//! The OpenTaint adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/opentaint/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::semgrep::{SEMGREP_SINK_PLACEHOLDER, SEMGREP_SOURCE_PLACEHOLDER};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::{case_paths, fixture_revision, validate_cases, validate_kernel_population_with};
use crate::evidence::{AnchorDialect, benchmark_endpoint_names, callsite_anchored_outcome};
use crate::freeze::required_string;
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, OverheadTools, load_average_one_minute,
    overhead_workspace, trivial_fixture,
};
use crate::modeling::{
    ModelingCategory, modeling_case_scratch, modeling_category, modeling_partition_outcome,
    modeling_supported_templates, plan_modeling_run,
};
use crate::native::{
    native_configuration_hash, native_partition_outcome, native_supported_templates,
    plan_native_run,
};
use crate::report::{ADAPTER_VERSION, hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{
    case_timing_path, now_seconds, write_case_phase_timings, write_run_environment,
};
use crate::templates::expected_core_templates;
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command, time::Instant};

// ---------------------------------------------------------------------------
// OpenTaint kernel runners.
//
// OpenTaint (seqra/opentaint) is a JVM bytecode taint engine: it analyzes
// compiled classes, not source, so each case's fixtures are compiled in an
// isolated scratch workspace — `javac` for Java, `kotlinc` for Kotlin — and
// handed to the pinned analyzer jar through a synthesized `project.yaml`, the
// way the Joern Rust kernel synthesizes a Cargo manifest. The compile is a
// harness step and is deliberately untimed; the analyzer invocation is one
// indivisible subprocess and is timed as `total`, per the retained-phase-
// timing convention in docs/adapters.md.
// ---------------------------------------------------------------------------

/// The pinned OpenTaint release. The project publishes dated, content-
/// addressed analyzer releases (near-daily); this tag is the one this
/// adapter's evidence was produced under.
pub(crate) const OPENTAINT_RELEASE_TAG: &str = "analyzer/2026.08.27.17eb0fe";

/// SHA-256 of the pinned `opentaint-project-analyzer.jar` release asset. The
/// jar self-reports no version at all — no manifest attribute, no `--version`
/// flag, and a SARIF `version` of `"latest"` — so the witnessed artifact
/// digest *is* the identity, and the release tag above is only ever published
/// into a report after the digest of the jar actually invoked has been
/// measured and matched against this constant. A mismatch fails the run
/// before any case is analyzed rather than publishing an asserted identity,
/// per the identity-witnessing convention (#87).
pub(crate) const OPENTAINT_ANALYZER_JAR_SHA256: &str =
    "811bdb22786e539c9aabdce5bef91f0c6521cc099adbe2720e6a840c09badf54";

/// SHA-256 of the pinned `opentaint-models.tar.gz` release asset — the
/// analyzer's own shipped standard-library dataflow approximations and
/// pass-through models, versioned with the analyzer in the same release. They
/// are the tool's platform models, analogous to the standard-library steps
/// CodeQL's packs carry, and never declare a benchmark endpoint; the
/// benchmark-controlled sources and sinks come only from the committed rule
/// templates below.
pub(crate) const OPENTAINT_MODELS_ARCHIVE_SHA256: &str =
    "c2a8fb0bbc3b6d59ed6db0c62732ff9a6f0f491d515cc2247932f2dd78cbb9f5";

pub(crate) const OPENTAINT_RULES_DIR: &str = "adapters/opentaint/rules";

/// The rule id both committed kernel rule templates declare. The analyzer's
/// rule-load trace is checked for this id on every case, so a rule that fails
/// to load can never turn an unanalyzed fixture into a clean negative.
pub(crate) const OPENTAINT_RULE_ID: &str = "dfb-opentaint-kernel";

pub(crate) enum OpentaintKernel {
    Java {
        javac: PathBuf,
    },
    Kotlin {
        kotlinc: PathBuf,
        kotlin_stdlib: PathBuf,
    },
}

impl OpentaintKernel {
    pub(crate) fn language(&self) -> &'static str {
        match self {
            Self::Java { .. } => "java",
            Self::Kotlin { .. } => "kotlin",
        }
    }

    pub(crate) fn display_name(&self) -> &'static str {
        match self {
            Self::Java { .. } => "Java",
            Self::Kotlin { .. } => "Kotlin",
        }
    }

    pub(crate) fn rule(&self) -> String {
        format!("{OPENTAINT_RULES_DIR}/kernel-{}.yaml", self.language())
    }

    pub(crate) fn report(&self) -> String {
        format!("reports/opentaint-{}-kernel.json", self.language())
    }

    pub(crate) fn raw_dir(&self) -> String {
        format!("reports/raw/opentaint-{}-kernel", self.language())
    }

    /// Both kernels reconcile with the Java anchor dialect. The Kotlin
    /// fixtures satisfy its surface contract exactly as they do for the
    /// Semgrep Kotlin kernel: `fun name(params)` declarations, receiverless
    /// sink calls, `.` as the only member operator, `//` comments.
    pub(crate) fn dialect(&self) -> AnchorDialect {
        AnchorDialect::Java
    }

    pub(crate) fn label(&self) -> String {
        format!("OpenTaint {} kernel", self.display_name())
    }

    /// The scored template set, read from this language's rollout row like
    /// every other kernel's. OpenTaint's pinned documentation declares
    /// whole-program interprocedural JVM taint — across function boundaries,
    /// fields, aliases, and async code — and fences nothing off behind a paid
    /// tier or a documented capability boundary, so unlike Semgrep CE there is
    /// no documented partition to preregister `unsupported` cells from: the
    /// entire core denominator is scored, and every incapacity the engine
    /// actually has surfaces as a measured mismatch rather than being decided
    /// from observation, which the adapter contract forbids.
    pub(crate) fn templates(&self) -> Vec<&'static str> {
        expected_core_templates(self.language())
    }
}

/// Witness the identity of the exact release assets this run invokes.
///
/// The analyzer jar reports no version, so the witness is the artifact
/// digest, measured from the bytes on disk before the population is walked.
/// The pinned release tag is published as `tool_version` only when both
/// witnessed digests match the pinned constants; anything else fails the run
/// with the measured values in the error, so a report can never carry an
/// identity that was asserted rather than measured.
pub(crate) fn witness_opentaint_identity(
    analyzer_jar: &Path,
    models_archive: &Path,
) -> Result<(String, String)> {
    let jar_digest = format!(
        "{:x}",
        Sha256::digest(fs::read(analyzer_jar).with_context(|| {
            format!("read the OpenTaint analyzer jar {}", analyzer_jar.display())
        })?)
    );
    let models_digest = format!(
        "{:x}",
        Sha256::digest(fs::read(models_archive).with_context(|| {
            format!(
                "read the OpenTaint models archive {}",
                models_archive.display()
            )
        })?)
    );
    if jar_digest != OPENTAINT_ANALYZER_JAR_SHA256 {
        bail!(
            "the analyzer jar at {} has witnessed sha256 {jar_digest}, but the pinned {OPENTAINT_RELEASE_TAG} asset is {OPENTAINT_ANALYZER_JAR_SHA256}; refusing to publish a pinned identity for an artifact that is not the pinned artifact",
            analyzer_jar.display()
        );
    }
    if models_digest != OPENTAINT_MODELS_ARCHIVE_SHA256 {
        bail!(
            "the models archive at {} has witnessed sha256 {models_digest}, but the pinned {OPENTAINT_RELEASE_TAG} asset is {OPENTAINT_MODELS_ARCHIVE_SHA256}; refusing to publish a pinned identity for an artifact that is not the pinned artifact",
            models_archive.display()
        );
    }
    Ok((
        OPENTAINT_RELEASE_TAG.to_string(),
        format!(
            "opentaint-project-analyzer.jar sha256:{jar_digest}; opentaint-models.tar.gz sha256:{models_digest}"
        ),
    ))
}

/// Both committed OpenTaint kernel rule templates, so one configuration hash
/// binds the whole rule set the way the Semgrep kernels' does.
pub(crate) fn opentaint_rule_paths() -> BTreeSet<PathBuf> {
    BTreeSet::from([
        PathBuf::from(format!("{OPENTAINT_RULES_DIR}/kernel-java.yaml")),
        PathBuf::from(format!("{OPENTAINT_RULES_DIR}/kernel-kotlin.yaml")),
    ])
}

/// Extract the pinned models archive into a per-run scratch directory and
/// resolve the three artifacts the pinned invocation names. The archive's
/// digest was verified before this runs; extraction failures and missing
/// members are run-fatal because the invocation the pin describes cannot be
/// assembled without them.
pub(crate) struct OpentaintModels {
    pub(crate) passthrough_yaml: PathBuf,
    pub(crate) passthrough_config_dir: PathBuf,
    /// The compiled approximation classes. The analyzer's
    /// `--java-dataflow-approximations` takes a class *directory* and rejects
    /// the jar the archive also carries.
    pub(crate) dataflow_approximations_classes: PathBuf,
}

pub(crate) fn extract_opentaint_models(models_archive: &Path) -> Result<OpentaintModels> {
    let root = std::env::temp_dir().join("dataflowbench-opentaint-models");
    if root.exists() {
        fs::remove_dir_all(&root).with_context(|| format!("clear {}", root.display()))?;
    }
    fs::create_dir_all(&root)?;
    let status = Command::new("tar")
        .arg("xzf")
        .arg(models_archive)
        .arg("-C")
        .arg(&root)
        .stdin(std::process::Stdio::null())
        .status()
        .with_context(|| format!("extract {}", models_archive.display()))?;
    if !status.success() {
        bail!(
            "tar failed with status {status} extracting {}",
            models_archive.display()
        );
    }
    let models = OpentaintModels {
        passthrough_yaml: root.join("java/accumulated-fields.yaml"),
        passthrough_config_dir: root.join("java/config"),
        dataflow_approximations_classes: root.join("java/dataflow/build/classes/java/main"),
    };
    for expected in [
        &models.passthrough_yaml,
        &models.passthrough_config_dir,
        &models.dataflow_approximations_classes,
    ] {
        if !expected.exists() {
            bail!(
                "the pinned models archive did not yield {}; the archive layout no longer matches the pin",
                expected.display()
            );
        }
    }
    Ok(models)
}

/// The package a JVM fixture declares, so the fixture can be materialized on
/// its package path and named in the synthesized `project.yaml`. Every core
/// fixture declares one; a fixture that does not is a run-fatal contract
/// violation rather than a case outcome.
pub(crate) fn jvm_fixture_package(fixture: &str, body: &str) -> Result<String> {
    for line in body.lines() {
        let line = line.trim();
        if let Some(rest) = line.strip_prefix("package ") {
            let package = rest.trim_end_matches(';').trim();
            if package.is_empty() {
                break;
            }
            return Ok(package.to_string());
        }
    }
    bail!("fixture {fixture} declares no package")
}

pub(crate) fn select_opentaint_cases(kernel: &OpentaintKernel) -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if case["language"] == kernel.language()
            && case["track"] == "taint"
            && case["score_tier"] == "core"
        {
            selected.push((path, case));
        }
    }
    validate_kernel_population_with(&selected, &kernel.label(), &kernel.templates())?;
    Ok(selected)
}

pub(crate) fn run_opentaint_kernel(
    analyzer_jar: &Path,
    models_archive: &Path,
    java: &Path,
    kernel: OpentaintKernel,
) -> Result<()> {
    validate_cases()?;
    let selected = select_opentaint_cases(&kernel)?;
    let rule_path = kernel.rule();
    let template = fs::read_to_string(&rule_path)
        .with_context(|| format!("read the OpenTaint kernel rule {rule_path}"))?;
    for placeholder in [SEMGREP_SOURCE_PLACEHOLDER, SEMGREP_SINK_PLACEHOLDER] {
        if !template.contains(placeholder) {
            bail!("OpenTaint kernel rule {rule_path} does not carry {placeholder}");
        }
    }
    let raw_dir = PathBuf::from(kernel.raw_dir());
    fs::create_dir_all(&raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = witness_opentaint_identity(analyzer_jar, models_archive)?;
    write_run_environment(&raw_dir, "opentaint", &version, &build_identity)?;
    let models = extract_opentaint_models(models_archive)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = run_opentaint_case(
            analyzer_jar,
            java,
            &kernel,
            &models,
            &template,
            &path,
            &case,
            &raw_dir,
        )?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&opentaint_rule_paths())?;
    let report = json!({
        "schema_version": 1,
        "tool": "opentaint",
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": configuration_hash,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    let report_path = kernel.report();
    write_and_validate_report(Path::new(&report_path), &report)?;
    println!("wrote {report_path}");
    Ok(())
}

pub(crate) fn opentaint_case_scratch(kernel: &OpentaintKernel, id: &str) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!("dataflowbench-opentaint-{}", kernel.language()))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

pub(crate) fn write_opentaint_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let mut evidence = json!({
        "adapter": "opentaint",
        "case_id": id,
        "state": "runner-error",
        "stage": stage,
        "diagnostic": diagnostic,
        "evidence_kind": "retained-process-diagnostics"
    });
    if let Some(output) = output {
        evidence["status"] = json!(output.status.code());
        evidence["stdout"] = json!(String::from_utf8_lossy(&output.stdout).trim());
        evidence["stderr"] = json!(String::from_utf8_lossy(&output.stderr).trim());
    }
    fs::write(&error_path, serde_json::to_string_pretty(&evidence)? + "\n")?;
    Ok(error_path)
}

/// Why the analyzer's rule-load trace disqualifies this run's evidence, if it
/// does. The analyzer exits zero and writes a well-formed empty SARIF even
/// when the rule set failed to load, so an unchecked load failure would read
/// as a clean `not-reached`; this guard is what makes that impossible.
pub(crate) fn opentaint_rule_load_failure(trace: &Value, rule_id: &str) -> Option<String> {
    let mut registered = false;
    for file in trace["fileTraces"].as_array().into_iter().flatten() {
        for entry in file["entries"].as_array().into_iter().flatten() {
            if entry["type"] == "Error" {
                return Some(format!(
                    "rule loading reported an error: {}",
                    entry["message"].as_str().unwrap_or("without a message")
                ));
            }
        }
        for rule in file["ruleTraces"].as_array().into_iter().flatten() {
            for entry in rule["entries"].as_array().into_iter().flatten() {
                if entry["type"] == "Error" {
                    return Some(format!(
                        "rule {} reported a load error: {}",
                        rule["ruleIdInFile"].as_str().unwrap_or("(unnamed)"),
                        entry["message"].as_str().unwrap_or("without a message")
                    ));
                }
            }
            if rule["ruleIdInFile"] == rule_id {
                registered = true;
            }
        }
    }
    if !registered {
        return Some(format!(
            "rule {rule_id:?} was never registered by the analyzer"
        ));
    }
    None
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn run_opentaint_case(
    analyzer_jar: &Path,
    java: &Path,
    kernel: &OpentaintKernel,
    models: &OpentaintModels,
    template: &str,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let rule_path = raw_dir.join(format!("{id}-rule.yaml"));
    let trace_path = raw_dir.join(format!("{id}-load-trace.json"));
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [
        &raw_path,
        &error_path,
        &rule_path,
        &trace_path,
        &timing_path,
    ] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    // A case whose endpoints cannot be resolved from its own markers has no
    // usable anchor evidence: `inconclusive` with a retained reason, never a
    // clean negative.
    let endpoints = match benchmark_endpoint_names(case_path, case, kernel.dialect()) {
        Ok(endpoints) => endpoints,
        Err(reason) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled OpenTaint endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "opentaint",
                    "case_id": id,
                    "state": "inconclusive",
                    "stage": "endpoint-resolution",
                    "reason": diagnostic,
                    "evidence_kind": "retained-anchor-resolution"
                }))? + "\n",
            )?;
            return Ok(("inconclusive", vec![diagnostic], error_path));
        }
    };

    let rule = template
        .replace(SEMGREP_SOURCE_PLACEHOLDER, &endpoints.source_function)
        .replace(SEMGREP_SINK_PLACEHOLDER, &endpoints.sink_function);
    fs::write(&rule_path, &rule)?;

    let scratch = opentaint_case_scratch(kernel, id)?;
    let result = (|| {
        // Materialize the fixtures on their package paths, so the analyzer's
        // source resolution mirrors the layout the bytecode names.
        let source_root = scratch.join("source");
        let classes = scratch.join("classes");
        let output_dir = scratch.join("out");
        for directory in [&source_root, &classes, &output_dir] {
            fs::create_dir_all(directory)?;
        }
        let fixture_root = case_path.parent().expect("case path has parent");
        let mut packages = BTreeSet::new();
        let mut compile_inputs = Vec::new();
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            let body = fs::read_to_string(fixture_root.join(fixture))?;
            let package = jvm_fixture_package(fixture, &body)?;
            let package_dir = source_root.join(package.replace('.', "/"));
            fs::create_dir_all(&package_dir)?;
            let target = package_dir.join(fixture);
            fs::copy(fixture_root.join(fixture), &target)?;
            packages.insert(package);
            compile_inputs.push(target);
        }

        // The compile is a harness step — the fixture's bytecode is this
        // adapter's input encoding, like the Joern Rust kernel's synthesized
        // crate — so it is not timed, per docs/adapters.md.
        let mut compile = match kernel {
            OpentaintKernel::Java { javac } => Command::new(javac),
            OpentaintKernel::Kotlin { kotlinc, .. } => Command::new(kotlinc),
        };
        compile
            .arg("-nowarn")
            .arg("-d")
            .arg(&classes)
            .args(&compile_inputs)
            .stdin(std::process::Stdio::null());
        let compiled = match compile.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn the {} fixture compiler: {error}",
                    kernel.display_name()
                );
                let path =
                    write_opentaint_error(raw_dir, id, "fixture-compile", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        if !compiled.status.success() {
            let diagnostic = format!(
                "{} fixture compilation failed with status {}",
                kernel.display_name(),
                compiled.status
            );
            let path = write_opentaint_error(
                raw_dir,
                id,
                "fixture-compile",
                &diagnostic,
                Some(&compiled),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }

        let mut project = String::from("javaProjects:\n");
        project.push_str(&format!("  - sourceRoot: {}\n", source_root.display()));
        project.push_str("    modules:\n");
        project.push_str(&format!(
            "      - moduleSourceRoot: {}\n",
            source_root.display()
        ));
        project.push_str("        packages:\n");
        for package in &packages {
            project.push_str(&format!("          - {package}\n"));
        }
        project.push_str("        moduleClasses:\n");
        project.push_str(&format!("          - {}\n", classes.display()));
        if let OpentaintKernel::Kotlin { kotlin_stdlib, .. } = kernel {
            project.push_str("    dependencies:\n");
            project.push_str(&format!("      - {}\n", kotlin_stdlib.display()));
        }
        let project_path = scratch.join("project.yaml");
        fs::write(&project_path, project)?;

        let resolved_rule = fs::canonicalize(&rule_path).unwrap_or_else(|_| rule_path.clone());
        let scratch_trace = output_dir.join("load-trace.json");
        let mut command = Command::new(java);
        command
            .arg("-jar")
            .arg(analyzer_jar)
            .arg(format!("--project={}", project_path.display()))
            .arg("--project-kind=unknown")
            // The analyzer's entry-point discovery is Spring-shaped; the
            // benchmark fixtures declare no framework entry point, so the
            // documented all-methods selector is pinned as part of the
            // invocation. It changes which methods are analyzed, never what
            // the engine claims about a flow.
            .arg("--debug-run-analysis-on-selected-entry-points=*")
            .arg(format!("--semgrep-rule-set={}", resolved_rule.display()))
            .arg(format!(
                "--semgrep-rule-load-trace={}",
                scratch_trace.display()
            ))
            .arg(format!(
                "--passthrough-approximations={}",
                models.passthrough_yaml.display()
            ))
            .arg(format!(
                "--passthrough-approximations={}",
                models.passthrough_config_dir.display()
            ))
            .arg(format!(
                "--java-dataflow-approximations={}",
                models.dataflow_approximations_classes.display()
            ))
            .arg(format!("--output-dir={}", output_dir.display()))
            .stdin(std::process::Stdio::null());
        // One analyzer invocation is indivisible from the adapter's vantage:
        // `total`, per the timing convention. The fixture compile above is
        // harness work and is deliberately outside the timed boundary.
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the OpenTaint {} kernel analysis with {}: {error}",
                    kernel.display_name(),
                    java.display()
                );
                let path = write_opentaint_error(raw_dir, id, "analyzer-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(raw_dir, "opentaint", id, &[("total", invoked.elapsed())])?;
        if scratch_trace.exists() {
            fs::copy(&scratch_trace, &trace_path)?;
        }
        if !output.status.success() {
            let diagnostic = format!(
                "OpenTaint {} kernel analysis failed with status {}",
                kernel.display_name(),
                output.status
            );
            let path = write_opentaint_error(
                raw_dir,
                id,
                "analyzer-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        if !trace_path.exists() {
            let diagnostic =
                "the analyzer wrote no rule-load trace, so rule activation cannot be proven"
                    .to_string();
            let path = write_opentaint_error(raw_dir, id, "rule-load", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let trace: Value = serde_json::from_str(&fs::read_to_string(&trace_path)?)
            .with_context(|| format!("parse rule-load trace {}", trace_path.display()))?;
        if let Some(reason) = opentaint_rule_load_failure(&trace, OPENTAINT_RULE_ID) {
            let diagnostic = format!("the benchmark rule did not activate: {reason}");
            let path = write_opentaint_error(raw_dir, id, "rule-load", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let sarif_path = output_dir.join("report-ifds.sarif");
        if !sarif_path.exists() {
            let diagnostic = "the analyzer exited cleanly but wrote no SARIF report".to_string();
            let path =
                write_opentaint_error(raw_dir, id, "analyzer-output", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::copy(&sarif_path, &raw_path)?;
        let sarif: Value = match serde_json::from_str(&fs::read_to_string(&raw_path)?) {
            Ok(sarif) => sarif,
            Err(error) => {
                let diagnostic =
                    format!("parse OpenTaint evidence {}: {error}", raw_path.display());
                let path =
                    write_opentaint_error(raw_dir, id, "analyzer-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let (outcome, diagnostics) =
            callsite_anchored_outcome(case_path, case, &sarif, kernel.dialect());
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("OpenTaint case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "OpenTaint case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// The rule id the committed OpenTaint modeling artifact declares. Checked in
/// the retained rule-load trace on every scored cell, exactly as the kernel
/// checks its own id: a modeling rule that fails to load must never turn an
/// unanalyzed fixture into a clean negative.
pub(crate) const OPENTAINT_MODEL_RULE_ID: &str = "dfb-opentaint-model";

/// Run one *scored* Java modeling cell through the pinned OpenTaint analyzer,
/// under the committed modeling rule rather than the kernel template.
///
/// Nothing is templated: the endpoint identities *are* the model, so the
/// committed `adapters/opentaint/rules/model-java.yaml` states them literally
/// and the runner substitutes nothing — the same shape as the Semgrep
/// modeling arm. The execution plumbing mirrors the kernel's: fixtures are
/// materialized on their package paths and compiled (`javac`, a harness step
/// outside the timed boundary), a minimal `project.yaml` is synthesized, and
/// the one analyzer invocation is timed as `total`. Reconciliation uses the
/// modeling tier's `JavaMember` dialect, because a declared modeling entity
/// is reached through its declaring type (`Audit.record(v)`), which the
/// kernel's bare-call dialect deliberately does not count.
#[allow(clippy::too_many_arguments)]
pub(crate) fn run_opentaint_modeling_case(
    analyzer_jar: &Path,
    java: &Path,
    javac: &Path,
    models: &OpentaintModels,
    rule: &Path,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "modeling case")?;
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let trace_path = raw_dir.join(format!("{id}-load-trace.json"));
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [&raw_path, &error_path, &trace_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let scratch = modeling_case_scratch(ModelingTool::Opentaint, ModelingLanguage::Java, id)?;
    let result = (|| {
        let source_root = scratch.join("source");
        let classes = scratch.join("classes");
        let output_dir = scratch.join("out");
        for directory in [&source_root, &classes, &output_dir] {
            fs::create_dir_all(directory)?;
        }
        let fixture_root = case_path.parent().expect("case path has parent");
        let mut packages = BTreeSet::new();
        let mut compile_inputs = Vec::new();
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            let body = fs::read_to_string(fixture_root.join(fixture))?;
            let package = jvm_fixture_package(fixture, &body)?;
            let package_dir = source_root.join(package.replace('.', "/"));
            fs::create_dir_all(&package_dir)?;
            let target = package_dir.join(fixture);
            fs::copy(fixture_root.join(fixture), &target)?;
            packages.insert(package);
            compile_inputs.push(target);
        }

        // The compile is a harness step — the fixture's bytecode is this
        // adapter's input encoding — so it is not timed, per docs/adapters.md.
        let mut compile = Command::new(javac);
        compile
            .arg("-nowarn")
            .arg("-d")
            .arg(&classes)
            .args(&compile_inputs)
            .stdin(std::process::Stdio::null());
        let compiled = match compile.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!("failed to spawn the Java fixture compiler: {error}");
                let path =
                    write_opentaint_error(raw_dir, id, "fixture-compile", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        if !compiled.status.success() {
            let diagnostic = format!(
                "Java fixture compilation failed with status {}",
                compiled.status
            );
            let path = write_opentaint_error(
                raw_dir,
                id,
                "fixture-compile",
                &diagnostic,
                Some(&compiled),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }

        let mut project = String::from("javaProjects:\n");
        project.push_str(&format!("  - sourceRoot: {}\n", source_root.display()));
        project.push_str("    modules:\n");
        project.push_str(&format!(
            "      - moduleSourceRoot: {}\n",
            source_root.display()
        ));
        project.push_str("        packages:\n");
        for package in &packages {
            project.push_str(&format!("          - {package}\n"));
        }
        project.push_str("        moduleClasses:\n");
        project.push_str(&format!("          - {}\n", classes.display()));
        let project_path = scratch.join("project.yaml");
        fs::write(&project_path, project)?;

        let scratch_trace = output_dir.join("load-trace.json");
        let mut command = Command::new(java);
        command
            .arg("-jar")
            .arg(analyzer_jar)
            .arg(format!("--project={}", project_path.display()))
            .arg("--project-kind=unknown")
            // The same pinned all-methods entry-point selector the kernel
            // uses, for the same reason: the fixtures declare no framework
            // entry point, and without it Java's package-private statics are
            // never analyzed. It changes which methods are analyzed, never
            // what the engine claims about a flow — category E's roots are
            // decided by the partition, not by this flag.
            .arg("--debug-run-analysis-on-selected-entry-points=*")
            .arg(format!("--semgrep-rule-set={}", rule.display()))
            .arg(format!(
                "--semgrep-rule-load-trace={}",
                scratch_trace.display()
            ))
            .arg(format!(
                "--passthrough-approximations={}",
                models.passthrough_yaml.display()
            ))
            .arg(format!(
                "--passthrough-approximations={}",
                models.passthrough_config_dir.display()
            ))
            .arg(format!(
                "--java-dataflow-approximations={}",
                models.dataflow_approximations_classes.display()
            ))
            .arg(format!("--output-dir={}", output_dir.display()))
            .stdin(std::process::Stdio::null());
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the OpenTaint Java modeling analysis with {}: {error}",
                    java.display()
                );
                let path = write_opentaint_error(raw_dir, id, "analyzer-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(raw_dir, "opentaint", id, &[("total", invoked.elapsed())])?;
        if scratch_trace.exists() {
            fs::copy(&scratch_trace, &trace_path)?;
        }
        if !output.status.success() {
            let diagnostic = format!(
                "OpenTaint Java modeling analysis failed with status {}",
                output.status
            );
            let path = write_opentaint_error(
                raw_dir,
                id,
                "analyzer-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        if !trace_path.exists() {
            let diagnostic =
                "the analyzer wrote no rule-load trace, so rule activation cannot be proven"
                    .to_string();
            let path = write_opentaint_error(raw_dir, id, "rule-load", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let trace: Value = serde_json::from_str(&fs::read_to_string(&trace_path)?)
            .with_context(|| format!("parse rule-load trace {}", trace_path.display()))?;
        if let Some(reason) = opentaint_rule_load_failure(&trace, OPENTAINT_MODEL_RULE_ID) {
            let diagnostic = format!("the benchmark modeling rule did not activate: {reason}");
            let path = write_opentaint_error(raw_dir, id, "rule-load", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let sarif_path = output_dir.join("report-ifds.sarif");
        if !sarif_path.exists() {
            let diagnostic = "the analyzer exited cleanly but wrote no SARIF report".to_string();
            let path =
                write_opentaint_error(raw_dir, id, "analyzer-output", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::copy(&sarif_path, &raw_path)?;
        let sarif: Value = match serde_json::from_str(&fs::read_to_string(&raw_path)?) {
            Ok(sarif) => sarif,
            Err(error) => {
                let diagnostic =
                    format!("parse OpenTaint evidence {}: {error}", raw_path.display());
                let path =
                    write_opentaint_error(raw_dir, id, "analyzer-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let (outcome, diagnostics) =
            callsite_anchored_outcome(case_path, case, &sarif, AnchorDialect::JavaMember);
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("OpenTaint case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "OpenTaint case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// Run the OpenTaint benchmark-controlled modeling matrix for one language.
///
/// The house shape of `run_modeling`, with the one difference the adapter
/// forces: the run-level identity is the witnessed digest pair of the pinned
/// release assets (`witness_opentaint_identity`), not a binary's version
/// banner, because the analyzer jar self-reports no version at all. The
/// partition is consulted per case before the analyzer is touched — the
/// declined categories O, E, and B (Amendment A22) retain their rationales
/// without a fixture ever being handed to the tool — and a language other
/// than Java fails the plan on applicability: it has no OpenTaint modeling
/// denominator, which is different from a zero.
pub(crate) fn run_opentaint_modeling(
    analyzer_jar: &Path,
    models_archive: &Path,
    java: &Path,
    javac: &Path,
    language: ModelingLanguage,
) -> Result<()> {
    let plan = plan_modeling_run(ModelingTool::Opentaint, language)?;
    let rule = fs::canonicalize(
        plan.language
            .artifact(ModelingTool::Opentaint)
            .expect("the plan verified the artifact exists"),
    )
    .context("resolve the OpenTaint modeling rule")?;

    fs::create_dir_all(&plan.raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = witness_opentaint_identity(analyzer_jar, models_archive)?;
    write_run_environment(&plan.raw_dir, plan.tool.key(), &version, &build_identity)?;
    let models = extract_opentaint_models(models_archive)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(plan.cases.len());
    for (path, case) in &plan.cases {
        let id = required_string(case, "id", "modeling case")?;
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = if let Some((outcome, reason, raw_path)) =
            modeling_partition_outcome(plan.tool, case, &plan.raw_dir, &version)?
        {
            (outcome, vec![reason], raw_path)
        } else {
            run_opentaint_modeling_case(
                analyzer_jar,
                java,
                javac,
                &models,
                &rule,
                path,
                case,
                &plan.raw_dir,
            )?
        };
        results.push(normalized_result(
            case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }
    let report = json!({
        "schema_version": 1,
        "tool": plan.tool.key(),
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": hash_paths(&plan.configuration_paths)?,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(&plan.report, &report)?;
    let scored = modeling_supported_templates(plan.tool);
    let scored_assertions = plan
        .cases
        .iter()
        .filter(|(_, case)| {
            case["template_id"]
                .as_str()
                .is_some_and(|template| scored.contains(&template))
        })
        .count();
    let scored_categories: BTreeSet<ModelingCategory> = scored
        .iter()
        .filter_map(|template| modeling_category(template))
        .collect();
    println!(
        "wrote {} ({scored_assertions} scored, {} preregistered-unsupported, {} of six categories scored for {})",
        plan.report.display(),
        plan.cases.len() - scored_assertions,
        scored_categories.len(),
        plan.tool.pinned_identity()
    );
    Ok(())
}

/// Run the OpenTaint tool-native probe set for one language.
///
/// The partition declines all six templates (Amendment A23) — the pinned
/// release ships propagation models and no endpoint catalog — so no fixture
/// is ever handed to the analyzer. The run still witnesses the release
/// assets' digests once, per the run-level identity rule the native profile
/// states for exactly this 0 / 6 case: the twelve retained rationales are the
/// whole of the report's evidence, and they must name a measured identity
/// rather than an asserted one.
pub(crate) fn run_opentaint_native(
    analyzer_jar: &Path,
    models_archive: &Path,
    language: ModelingLanguage,
) -> Result<()> {
    let (version, build) = witness_opentaint_identity(analyzer_jar, models_archive)?;
    let plan = plan_native_run(ModelingTool::Opentaint, language, &version)?;
    let scored_templates = native_supported_templates(plan.tool, plan.language);

    fs::create_dir_all(&plan.raw_dir)?;
    let started = now_seconds()?;
    let build_identity = format!("{build} — {}", plan.activation.identity);
    write_run_environment(&plan.raw_dir, plan.tool.key(), &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(plan.cases.len());
    for (_path, case) in &plan.cases {
        let id = required_string(case, "id", "tool-native case")?;
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = if let Some((outcome, reason, raw_path)) =
            native_partition_outcome(
                plan.tool,
                plan.language,
                case,
                &plan.activation,
                &plan.raw_dir,
                &version,
            )? {
            (outcome, vec![reason], raw_path)
        } else {
            // Unreachable while the partition declines all six templates,
            // and a hard error rather than a synthesized outcome if a future
            // amendment promotes a cell without landing the arm that runs it.
            bail!(
                "the tool-native execution arm for {} × {} is not wired: {id} is a scored cell, and a cell promoted by a dated amendment lands its execution arm in the same pull request (docs/native-profile.md#partition-summary)",
                plan.tool.pinned_identity(),
                plan.language.display_name(),
            );
        };
        results.push(normalized_result(
            case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }
    let report = json!({
        "schema_version": 1,
        "tool": plan.tool.key(),
        "tool_version": version,
        "tool_build_identity": build_identity,
        "adapter_version": ADAPTER_VERSION,
        "configuration_hash": native_configuration_hash(&plan.activation)?,
        "fixture_revision": revision,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "cold_or_warm": "cold",
        "results": results
    });
    write_and_validate_report(&plan.report, &report)?;
    let scored_assertions = plan
        .cases
        .iter()
        .filter(|(_, case)| {
            case["template_id"]
                .as_str()
                .is_some_and(|template| scored_templates.contains(&template))
        })
        .count();
    println!(
        "wrote {} ({scored_assertions} scored, {} preregistered-unsupported, {} of six templates activated for {})",
        plan.report.display(),
        plan.cases.len() - scored_assertions,
        scored_templates.len(),
        plan.tool.pinned_identity()
    );
    Ok(())
}

/// OpenTaint: one analyzer-jar invocation over a synthesized `project.yaml`,
/// under the committed kernel rule set and the pinned model archive.
///
/// The fixture compile is harness materialization — this adapter's input
/// encoding is bytecode — and is outside the timed window, exactly as it is in
/// the cold kernel.
pub(crate) fn overhead_run_opentaint(
    tools: &OverheadTools,
    language: OverheadLanguage,
    run: usize,
    raw_dir: &Path,
) -> Result<OverheadRun> {
    let (rule_file, package, compiler) = match language {
        OverheadLanguage::Kotlin => (
            format!("{OPENTAINT_RULES_DIR}/kernel-kotlin.yaml"),
            "dataflowbench",
            &tools.kotlinc,
        ),
        OverheadLanguage::Java => (
            format!("{OPENTAINT_RULES_DIR}/kernel-java.yaml"),
            "dataflowbench.taint",
            &tools.javac,
        ),
        other => bail!("no OpenTaint overhead arm for {}", other.as_str()),
    };
    let rule = fs::read_to_string(&rule_file)?
        .replace(SEMGREP_SOURCE_PLACEHOLDER, "dfb_source")
        .replace(SEMGREP_SINK_PLACEHOLDER, "dfb_sink");
    let models = extract_opentaint_models(&tools.models_archive)?;

    let (scratch, _) = overhead_workspace(OverheadTool::Opentaint, language, run)?;
    let source_root = scratch.join("source");
    let classes = scratch.join("classes");
    let output_dir = scratch.join("out");
    for directory in [&source_root, &classes, &output_dir] {
        fs::create_dir_all(directory)?;
    }
    let (fixture_name, fixture_text) = trivial_fixture(language);
    let package_dir = source_root.join(package.replace('.', "/"));
    fs::create_dir_all(&package_dir)?;
    fs::write(package_dir.join(fixture_name), fixture_text)?;

    let compiled = Command::new(compiler)
        .arg("-nowarn")
        .arg("-d")
        .arg(&classes)
        .arg(package_dir.join(fixture_name))
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("compile the trivial fixture with {}", compiler.display()))?;
    if !compiled.status.success() {
        bail!(
            "the trivial {} fixture did not compile:\n{}",
            language.as_str(),
            String::from_utf8_lossy(&compiled.stderr)
        );
    }

    let mut project = String::from("javaProjects:\n");
    project.push_str(&format!("  - sourceRoot: {}\n", source_root.display()));
    project.push_str("    modules:\n");
    project.push_str(&format!(
        "      - moduleSourceRoot: {}\n",
        source_root.display()
    ));
    project.push_str("        packages:\n");
    project.push_str(&format!("          - {package}\n"));
    project.push_str("        moduleClasses:\n");
    project.push_str(&format!("          - {}\n", classes.display()));
    if matches!(language, OverheadLanguage::Kotlin) {
        project.push_str("    dependencies:\n");
        project.push_str(&format!("      - {}\n", tools.kotlin_stdlib.display()));
    }
    let project_path = scratch.join("project.yaml");
    fs::write(&project_path, project)?;
    let rule_path = scratch.join("rule.yaml");
    fs::write(&rule_path, &rule)?;
    fs::write(raw_dir.join("resolved-rule.yaml"), &rule)?;
    let resolved_rule = fs::canonicalize(&rule_path).unwrap_or_else(|_| rule_path.clone());

    let mut command = Command::new(&tools.java);
    command
        .arg("-jar")
        .arg(&tools.analyzer_jar)
        .arg(format!("--project={}", project_path.display()))
        .arg("--project-kind=unknown")
        .arg("--debug-run-analysis-on-selected-entry-points=*")
        .arg(format!("--semgrep-rule-set={}", resolved_rule.display()))
        .arg(format!(
            "--semgrep-rule-load-trace={}",
            output_dir.join("load-trace.json").display()
        ))
        .arg(format!(
            "--passthrough-approximations={}",
            models.passthrough_yaml.display()
        ))
        .arg(format!(
            "--passthrough-approximations={}",
            models.passthrough_config_dir.display()
        ))
        .arg(format!(
            "--java-dataflow-approximations={}",
            models.dataflow_approximations_classes.display()
        ))
        .arg(format!("--output-dir={}", output_dir.display()))
        .stdin(std::process::Stdio::null());
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run the OpenTaint analyzer with {}", tools.java.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !output.status.success() {
        bail!(
            "the OpenTaint overhead invocation failed with status {}:\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    fs::remove_dir_all(&scratch).ok();
    Ok(OverheadRun {
        phases: vec![("total".into(), wall_ms)],
        wall_ms,
        load_before,
    })
}
