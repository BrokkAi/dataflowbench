//! The Infer adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/infer/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::ModelingTool;
use crate::adapters::ToolIdentity;
use crate::adapters::normalized_report;
use crate::adapters::opentaint::jvm_fixture_package;
use crate::adapters::semgrep::{SEMGREP_SINK_PLACEHOLDER, SEMGREP_SOURCE_PLACEHOLDER};
use crate::adapters::write_runner_error;
use crate::adapters::{KernelPopulation, select_kernel_cases};
use crate::cases::LoadedCases;
use crate::cases::{fixture_revision, validate_cases};
use crate::evidence::{AnchorDialect, benchmark_endpoint_names, callsite_anchored_outcome};
use crate::freeze::required_string;
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, load_average_one_minute, overhead_workspace,
    trivial_fixture,
};
use crate::modeling::{ModelingRunPlan, modeling_anchor_dialect, modeling_case_scratch};
use crate::report::{hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{
    case_timing_path, now_seconds, write_case_phase_timings, write_run_environment,
};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command, time::Instant};

/// Enforce the pinned Infer release's silent-configuration hazards on its
/// modeling artifact, all three measured in the field
/// (`reports/raw/amendment-a13-infer-partition/`):
///
/// - a configuration that parses but declares no `pulse-taint-policies` loads
///   and reports nothing — the kernel adapter's own quirk, guarded here for
///   the same reason;
/// - a sanitizer whose kind is not named in a policy's `sanitizer_kinds` is
///   **silently inert**: the declaration is accepted, the flow it should
///   suppress is still reported, and every category-Z cell would then be
///   decided by the engine rather than the model;
/// - the plain `procedure` matcher is a substring match (`dfb_source` also
///   matches `dfb_source_extra`), so a modeling artifact — whose whole claim
///   is identity binding — may not use it.
pub(crate) fn require_infer_modeling_load_bearing(config: &str, path: &str) -> Result<()> {
    let parsed: Value = serde_json::from_str(config)
        .with_context(|| format!("parse the Infer modeling configuration {path}"))?;
    if parsed["pulse-taint-policies"]
        .as_array()
        .is_none_or(Vec::is_empty)
    {
        bail!(
            "{path} declares no pulse-taint-policies; the pinned binary loads such a configuration and asks no taint question at all, so every cell would read as a clean negative"
        );
    }
    let mut wired_sanitizer_kinds = BTreeSet::new();
    for policy in parsed["pulse-taint-policies"]
        .as_array()
        .into_iter()
        .flatten()
    {
        for flow in policy["taint_flows"].as_array().into_iter().flatten() {
            for kind in flow["sanitizer_kinds"].as_array().into_iter().flatten() {
                if let Some(kind) = kind.as_str() {
                    wired_sanitizer_kinds.insert(kind.to_string());
                }
            }
        }
    }
    for sanitizer in parsed["pulse-taint-sanitizers"]
        .as_array()
        .into_iter()
        .flatten()
    {
        let kinds = sanitizer["kinds"].as_array().cloned().unwrap_or_default();
        if kinds.is_empty() {
            bail!(
                "{path} declares a sanitizer with no `kinds`; on the pinned binary a sanitizer is credited only through a policy's `sanitizer_kinds`, and an unnamed kind cannot be wired into one"
            );
        }
        for kind in kinds {
            let Some(kind) = kind.as_str() else {
                bail!("{path} declares a non-string sanitizer kind");
            };
            if !wired_sanitizer_kinds.contains(kind) {
                bail!(
                    "{path} declares a sanitizer of kind {kind:?} that no policy's `sanitizer_kinds` names; measured on the pinned v1.3.0, such a sanitizer is silently inert and the category-Z cells would be decided by the engine rather than the model (docs/modeling-matrix.md#the-load-bearing-model-requirement)"
                );
            }
        }
    }
    for section in [
        "pulse-taint-sources",
        "pulse-taint-sinks",
        "pulse-taint-sanitizers",
        "pulse-taint-propagators",
    ] {
        for matcher in parsed[section].as_array().into_iter().flatten() {
            if matcher.get("procedure").is_some() {
                bail!(
                    "{path} uses a plain `procedure` matcher in {section}; the pinned binary matches it as a substring, which cannot carry the identity binding a modeling declaration claims — use `class_names` + `method_names` or an anchored `procedure_regex`"
                );
            }
        }
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Infer kernel runners.
//
// Infer (facebook/infer) analyzes code it watches being compiled: `infer
// capture` traces a real compile command — the distribution's own bundled
// clang for C and C++, a traced `javac` for Java — and `infer analyze` runs
// the Pulse engine over the captured intermediate representation. The pinned
// v1.3.0 release ships no Quandary checker at all (the historical taint
// checker is removed, not merely deprecated), so Pulse's taint configuration
// is the one operable taint surface and the one this adapter drives. Each
// case's compile command is materialized per case in an isolated scratch
// workspace, and the two subprocess boundaries the adapter genuinely
// observes — capture, then analyze — are the retained phases, exactly as the
// CodeQL kernels retain `database-create` and `database-analyze`.
// ---------------------------------------------------------------------------

/// The pinned Infer release this adapter's evidence was produced under. The
/// binary self-reports this version, and every run witnesses it from the
/// binary actually invoked, per the identity-witnessing convention (#87).
pub(crate) const INFER_PINNED_VERSION: &str = "v1.3.0";

pub(crate) const INFER_CONFIG_DIR: &str = "adapters/infer/config";

/// The one SARIF rule id the benchmark-controlled taint policy can produce.
/// `--pulse-only` disables every checker except Pulse, but Pulse itself also
/// reports memory-safety issues (null dereferences, leaks); those answer a
/// different question than the taint policy asks, so reconciliation reads
/// only `TAINT_ERROR` results as flow claims and retains anything else as a
/// diagnostic, the way the tool-native profile treats findings from queries
/// the benchmark did not ask.
pub(crate) const INFER_TAINT_RULE_ID: &str = "TAINT_ERROR";

pub(crate) enum InferKernel {
    C,
    Cpp,
    Java { javac: PathBuf },
}

impl InferKernel {
    pub(crate) fn config_template(&self) -> String {
        format!("{INFER_CONFIG_DIR}/kernel-{}.json", self.language())
    }

    /// C and C++ share the C-family anchor dialect the CodeQL and Bifrost
    /// kernels already reconcile with; Java uses the kernel Java dialect.
    pub(crate) fn dialect(&self) -> AnchorDialect {
        match self {
            Self::C | Self::Cpp => AnchorDialect::Cpp,
            Self::Java { .. } => AnchorDialect::Java,
        }
    }
}

/// Infer's populations over the shared contract.
///
/// The whole core denominator is scored. Infer's pinned distribution declares
/// whole-program interprocedural analysis, and its Pulse taint configuration
/// surface — sources, sinks, propagators, sanitizers, with field accesses
/// followed by default — fences no construct class behind a tier or a
/// documented capability boundary, so like the OpenTaint kernels there is no
/// documented partition to preregister `unsupported` cells from.
impl KernelPopulation for InferKernel {
    fn tool(&self) -> &'static str {
        "infer"
    }

    fn language(&self) -> &'static str {
        match self {
            Self::C => "c",
            Self::Cpp => "cpp",
            Self::Java { .. } => "java",
        }
    }

    fn display_name(&self) -> &'static str {
        match self {
            Self::C => "C",
            Self::Cpp => "C++",
            Self::Java { .. } => "Java",
        }
    }

    fn report(&self) -> String {
        format!("reports/infer-{}-kernel.json", self.language())
    }

    fn raw_dir(&self) -> String {
        format!("reports/raw/infer-{}-kernel", self.language())
    }

    fn label(&self) -> String {
        format!("Infer {} kernel", self.display_name())
    }

    /// All three committed taint-configuration templates, so one hash binds
    /// the whole set the way the Semgrep and OpenTaint kernels' does.
    fn configuration_paths(&self, _cases: &LoadedCases) -> Result<BTreeSet<PathBuf>> {
        Ok(infer_config_paths())
    }
}

/// Witness the identity of the exact Infer binary this run invokes: the
/// version the binary self-reports, plus the measured digest of its bytes.
/// The pinned version is published only when the witnessed version matches
/// it; a mismatch fails the run with both values in the error, so a report
/// can never carry an asserted identity.
pub(crate) fn witness_infer_identity(infer: &Path) -> Result<ToolIdentity> {
    let output = Command::new(infer)
        .arg("--version")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run {} --version", infer.display()))?;
    if !output.status.success() {
        bail!(
            "{} --version failed with status {}",
            infer.display(),
            output.status
        );
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let version = stdout
        .lines()
        .find_map(|line| line.trim().strip_prefix("Infer version "))
        .map(str::trim)
        .filter(|version| !version.is_empty())
        .context("Infer did not report a version")?
        .to_string();
    if version != INFER_PINNED_VERSION {
        bail!(
            "the Infer binary at {} witnessed version {version}, but this adapter pins {INFER_PINNED_VERSION}; refusing to publish a pinned identity for a binary that is not the pinned release",
            infer.display()
        );
    }
    let digest = format!(
        "{:x}",
        Sha256::digest(
            fs::read(infer)
                .with_context(|| format!("read the Infer binary {}", infer.display()))?
        )
    );
    let build_identity = format!("infer:{version} bin-sha256:{digest}");
    Ok(ToolIdentity::new(version, build_identity))
}

/// All three committed Infer taint-configuration templates, so one
/// configuration hash binds the whole set the way the Semgrep and OpenTaint
/// kernels' do.
pub(crate) fn infer_config_paths() -> BTreeSet<PathBuf> {
    BTreeSet::from([
        PathBuf::from(format!("{INFER_CONFIG_DIR}/kernel-c.json")),
        PathBuf::from(format!("{INFER_CONFIG_DIR}/kernel-cpp.json")),
        PathBuf::from(format!("{INFER_CONFIG_DIR}/kernel-java.json")),
    ])
}

pub(crate) fn select_infer_cases(kernel: &InferKernel) -> Result<LoadedCases> {
    select_kernel_cases(kernel)
}

/// Split an Infer SARIF document into the taint results the benchmark policy
/// asked for and diagnostics for everything else Pulse reported alongside
/// them. The returned document is what reconciliation reads; the retained raw
/// evidence stays the verbatim SARIF.
pub(crate) fn infer_taint_results_only(sarif: &Value) -> (Value, Vec<String>) {
    let mut filtered = sarif.clone();
    let mut diagnostics = Vec::new();
    for run in filtered["runs"].as_array_mut().into_iter().flatten() {
        if let Some(results) = run["results"].as_array_mut() {
            results.retain(|result| {
                if result["ruleId"] == INFER_TAINT_RULE_ID {
                    return true;
                }
                diagnostics.push(format!(
                    "non-taint Pulse finding {} retained as a diagnostic, not flow evidence",
                    result["ruleId"].as_str().unwrap_or("(unnamed)")
                ));
                false
            });
            for result in results {
                if let Some(sink_step) = infer_taint_sink_step_location(result)
                    && let Some(locations) = result["locations"].as_array_mut()
                {
                    locations.push(sink_step);
                }
            }
        }
    }
    diagnostics.sort();
    diagnostics.dedup();
    (filtered, diagnostics)
}

/// The final `codeFlows` step of an Infer taint result — the sink reach the
/// engine's own path evidence names.
///
/// Infer's top-level `locations` entry sits at the reporting point, which for
/// a flow through a function pointer or interface is the *indirect* callsite
/// (`selected(dfb_source())`) rather than a textual callsite of the anchored
/// sink. The retained SARIF's own `codeFlows` end on the sink callsite —
/// "flows to this sink" — so that location is appended to the reconciliation
/// view's `locations`, the way the CodeQL kernels' "query path evidence
/// identifies the source-to-sink flow". The verbatim raw evidence is
/// untouched, and a result with no code flow gains nothing.
pub(crate) fn infer_taint_sink_step_location(result: &Value) -> Option<Value> {
    let step = result["codeFlows"].as_array()?.first()?["threadFlows"]
        .as_array()?
        .first()?["locations"]
        .as_array()?
        .last()?;
    let location = &step["location"];
    location["physicalLocation"]["artifactLocation"]["uri"].as_str()?;
    location["physicalLocation"]["region"]["startLine"].as_u64()?;
    Some(location.clone())
}

pub(crate) fn run_infer_kernel(infer: &Path, kernel: InferKernel) -> Result<()> {
    validate_cases()?;
    let selected = select_infer_cases(&kernel)?;
    let configuration_paths = kernel.configuration_paths(&selected)?;
    let template_path = kernel.config_template();
    let template = fs::read_to_string(&template_path)
        .with_context(|| format!("read the Infer taint-configuration template {template_path}"))?;
    for placeholder in [SEMGREP_SOURCE_PLACEHOLDER, SEMGREP_SINK_PLACEHOLDER] {
        if !template.contains(placeholder) {
            bail!(
                "Infer taint-configuration template {template_path} does not carry {placeholder}"
            );
        }
    }
    // The template must itself be well-formed JSON that names a policy: the
    // pinned binary silently analyzes with no taint question at all when its
    // taint configuration cannot be read, so a malformed template must fail
    // here rather than surface as a population of clean negatives.
    let template_json: Value = serde_json::from_str(&template)
        .with_context(|| format!("parse the Infer taint-configuration template {template_path}"))?;
    if template_json["pulse-taint-policies"]
        .as_array()
        .is_none_or(Vec::is_empty)
    {
        bail!(
            "Infer taint-configuration template {template_path} declares no pulse-taint-policies"
        );
    }
    let raw_dir = PathBuf::from(kernel.raw_dir());
    fs::create_dir_all(&raw_dir)?;
    let started = now_seconds()?;
    let identity = witness_infer_identity(infer)?;
    write_run_environment(&raw_dir, "infer", &identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) =
            run_infer_case(infer, &kernel, &template, &path, &case, &raw_dir)?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&configuration_paths)?;
    let report = normalized_report(
        kernel.tool(),
        &identity,
        &configuration_hash,
        &revision,
        started,
        results,
    )?;
    let report_path = kernel.report();
    write_and_validate_report(Path::new(&report_path), &report)?;
    println!("wrote {report_path}");
    Ok(())
}

pub(crate) fn infer_case_scratch(kernel: &InferKernel, id: &str) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!("dataflowbench-infer-{}", kernel.language()))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

pub(crate) fn write_infer_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    write_runner_error("infer", raw_dir, id, stage, diagnostic, output)
}

pub(crate) fn run_infer_case(
    infer: &Path,
    kernel: &InferKernel,
    template: &str,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let config_path = raw_dir.join(format!("{id}-taint-config.json"));
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [&raw_path, &error_path, &config_path, &timing_path] {
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
                format!("cannot derive the benchmark-controlled Infer endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "infer",
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

    let config = template
        .replace(SEMGREP_SOURCE_PLACEHOLDER, &endpoints.source_function)
        .replace(SEMGREP_SINK_PLACEHOLDER, &endpoints.sink_function);
    fs::write(&config_path, &config)?;

    let scratch = infer_case_scratch(kernel, id)?;
    let result = (|| {
        let fixture_root = case_path.parent().expect("case path has parent");
        let mut compile_inputs = Vec::new();
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            // Java fixtures are materialized on their declared package paths,
            // the way the OpenTaint kernels materialize them; C and C++
            // fixtures sit flat in the workspace root.
            let target = match kernel {
                InferKernel::Java { .. } => {
                    let body = fs::read_to_string(fixture_root.join(fixture))?;
                    let package = jvm_fixture_package(fixture, &body)?;
                    let package_dir = PathBuf::from(package.replace('.', "/"));
                    fs::create_dir_all(scratch.join(&package_dir))?;
                    package_dir.join(fixture)
                }
                InferKernel::C | InferKernel::Cpp => PathBuf::from(fixture),
            };
            fs::copy(fixture_root.join(fixture), scratch.join(&target))?;
            compile_inputs.push(target);
        }

        // The materialized per-case compile command: Infer analyzes code it
        // watches being compiled, so this command is the case's build
        // context, like the compile-command materialization the CodeQL
        // C-family kernel performs. The `clang`/`clang++` spelling selects
        // the language mode of the distribution's own bundled front end;
        // Java's traced compiler is the harness-supplied `javac`.
        let results_dir = scratch.join("infer-out");
        let mut capture = Command::new(infer);
        capture
            .arg("capture")
            .arg("--results-dir")
            .arg(&results_dir)
            .arg("--")
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        match kernel {
            InferKernel::C => capture.arg("clang").arg("-c"),
            InferKernel::Cpp => capture.arg("clang++").arg("-c"),
            InferKernel::Java { javac } => capture.arg(javac),
        };
        capture.args(&compile_inputs);
        let capture_started = Instant::now();
        let captured = match capture.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn infer capture with {}: {error}",
                    infer.display()
                );
                let path = write_infer_error(raw_dir, id, "capture", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let capture_elapsed = capture_started.elapsed();
        if !captured.status.success() {
            let diagnostic = format!(
                "infer capture of the {} fixture compile failed with status {}",
                kernel.display_name(),
                captured.status
            );
            let path = write_infer_error(raw_dir, id, "capture", &diagnostic, Some(&captured))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }

        // The pinned binary silently analyzes with no taint question at all
        // when the file its `--pulse-taint-config` names does not exist —
        // exit status zero, an empty report — so the resolved configuration's
        // presence is proven before the analyzer runs, for the same reason
        // the OpenTaint kernels prove their rule-load trace.
        let resolved_config =
            fs::canonicalize(&config_path).unwrap_or_else(|_| config_path.clone());
        if !resolved_config.is_file() {
            let diagnostic = format!(
                "the resolved taint configuration {} vanished before analysis; the pinned binary would silently analyze without a taint question",
                resolved_config.display()
            );
            let path = write_infer_error(raw_dir, id, "taint-config", &diagnostic, None)?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let mut analyze = Command::new(infer);
        analyze
            .arg("analyze")
            .arg("--results-dir")
            .arg(&results_dir)
            .arg("--pulse-only")
            .arg("--sarif")
            .arg("--pulse-taint-config")
            .arg(&resolved_config)
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        let analyze_started = Instant::now();
        let analyzed = match analyze.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn infer analyze with {}: {error}",
                    infer.display()
                );
                let path = write_infer_error(raw_dir, id, "analyze", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(
            raw_dir,
            "infer",
            id,
            &[
                ("capture", capture_elapsed),
                ("analyze", analyze_started.elapsed()),
            ],
        )?;
        if !analyzed.status.success() {
            let diagnostic = format!(
                "infer analyze of the {} kernel case failed with status {}",
                kernel.display_name(),
                analyzed.status
            );
            let path = write_infer_error(raw_dir, id, "analyze", &diagnostic, Some(&analyzed))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let sarif_path = results_dir.join("report.sarif");
        if !sarif_path.exists() {
            let diagnostic = "infer analyze exited cleanly but wrote no SARIF report".to_string();
            let path =
                write_infer_error(raw_dir, id, "analyzer-output", &diagnostic, Some(&analyzed))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::copy(&sarif_path, &raw_path)?;
        let sarif: Value = match serde_json::from_str(&fs::read_to_string(&raw_path)?) {
            Ok(sarif) => sarif,
            Err(error) => {
                let diagnostic = format!("parse Infer evidence {}: {error}", raw_path.display());
                let path = write_infer_error(raw_dir, id, "analyzer-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let (taint_only, mut diagnostics) = infer_taint_results_only(&sarif);
        let (outcome, anchor_diagnostics) =
            callsite_anchored_outcome(case_path, case, &taint_only, kernel.dialect());
        diagnostics.extend(anchor_diagnostics);
        diagnostics.sort();
        diagnostics.dedup();
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Infer case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Infer case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// Run one scored modeling cell through the pinned Infer release's Pulse
/// taint analysis.
///
/// The kernel runner's per-case shape is reused deliberately — materialize on
/// package paths, `infer capture` around a traced `javac`, `infer analyze
/// --pulse-only --sarif --pulse-taint-config`, the two phase timings, the
/// silent-missing-config guard — with two modeling differences: nothing is
/// templated (the committed `model-java.json` states the declared identities
/// literally, the way the Semgrep modeling rule does), and reconciliation uses
/// the member-qualified Java dialect, because a declared modeling entity is
/// reached through its declaring type (`Audit.record(v)`), which the kernel
/// dialect deliberately refuses.
pub(crate) fn run_infer_modeling_case(
    binary: &Path,
    javac: &Path,
    config: &Path,
    case_path: &Path,
    case: &Value,
    plan: &ModelingRunPlan,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "modeling case")?;
    let dialect = modeling_anchor_dialect(plan.language)?;
    let raw_path = plan.raw_dir.join(format!("{id}.json"));
    let error_path = plan.raw_dir.join(format!("{id}-error.json"));
    let timing_path = case_timing_path(&plan.raw_dir, id);
    for stale in [&raw_path, &error_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let scratch = modeling_case_scratch(ModelingTool::Infer, plan.language, id)?;
    let result = (|| {
        let fixture_root = case_path.parent().expect("case path has parent");
        let mut compile_inputs = Vec::new();
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            let body = fs::read_to_string(fixture_root.join(fixture))?;
            let package = jvm_fixture_package(fixture, &body)?;
            let package_dir = PathBuf::from(package.replace('.', "/"));
            fs::create_dir_all(scratch.join(&package_dir))?;
            let target = package_dir.join(fixture);
            fs::copy(fixture_root.join(fixture), scratch.join(&target))?;
            compile_inputs.push(target);
        }

        let results_dir = scratch.join("infer-out");
        let mut capture = Command::new(binary);
        capture
            .arg("capture")
            .arg("--results-dir")
            .arg(&results_dir)
            .arg("--")
            .arg(javac)
            .args(&compile_inputs)
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        let capture_started = Instant::now();
        let captured = match capture.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn infer capture with {}: {error}",
                    binary.display()
                );
                let path = write_infer_error(&plan.raw_dir, id, "capture", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let capture_elapsed = capture_started.elapsed();
        if !captured.status.success() {
            let diagnostic = format!(
                "infer capture of the Java modeling fixture compile failed with status {}",
                captured.status
            );
            let path =
                write_infer_error(&plan.raw_dir, id, "capture", &diagnostic, Some(&captured))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }

        // The pinned binary silently analyzes with no taint question at all
        // when the file its `--pulse-taint-config` names does not exist —
        // exit status zero, an empty report — so the committed artifact's
        // presence is proven immediately before the analyzer runs, exactly as
        // the kernel runner proves its resolved configuration's.
        if !config.is_file() {
            let diagnostic = format!(
                "the committed modeling configuration {} vanished before analysis; the pinned binary would silently analyze without a taint question",
                config.display()
            );
            let path = write_infer_error(&plan.raw_dir, id, "taint-config", &diagnostic, None)?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let mut analyze = Command::new(binary);
        analyze
            .arg("analyze")
            .arg("--results-dir")
            .arg(&results_dir)
            .arg("--pulse-only")
            .arg("--sarif")
            .arg("--pulse-taint-config")
            .arg(config)
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        let analyze_started = Instant::now();
        let analyzed = match analyze.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn infer analyze with {}: {error}",
                    binary.display()
                );
                let path = write_infer_error(&plan.raw_dir, id, "analyze", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(
            &plan.raw_dir,
            "infer",
            id,
            &[
                ("capture", capture_elapsed),
                ("analyze", analyze_started.elapsed()),
            ],
        )?;
        if !analyzed.status.success() {
            let diagnostic = format!(
                "infer analyze of the Java modeling case failed with status {}",
                analyzed.status
            );
            let path =
                write_infer_error(&plan.raw_dir, id, "analyze", &diagnostic, Some(&analyzed))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let sarif_path = results_dir.join("report.sarif");
        if !sarif_path.exists() {
            let diagnostic = "infer analyze exited cleanly but wrote no SARIF report".to_string();
            let path = write_infer_error(
                &plan.raw_dir,
                id,
                "analyzer-output",
                &diagnostic,
                Some(&analyzed),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::copy(&sarif_path, &raw_path)?;
        let sarif: Value = match serde_json::from_str(&fs::read_to_string(&raw_path)?) {
            Ok(sarif) => sarif,
            Err(error) => {
                let diagnostic = format!("parse Infer evidence {}: {error}", raw_path.display());
                let path =
                    write_infer_error(&plan.raw_dir, id, "analyzer-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        let (taint_only, mut diagnostics) = infer_taint_results_only(&sarif);
        let (outcome, anchor_diagnostics) =
            callsite_anchored_outcome(case_path, case, &taint_only, dialect);
        diagnostics.extend(anchor_diagnostics);
        diagnostics.sort();
        diagnostics.dedup();
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Infer case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Infer case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// Infer: both declared subprocesses — `infer capture` around the traced
/// compile, then `infer analyze` under the committed taint configuration —
/// timed separately and summed, as its cold whole-invocation figure is.
pub(crate) fn overhead_run_infer(
    infer: &Path,
    language: OverheadLanguage,
    run: usize,
) -> Result<OverheadRun> {
    let config_template = match language {
        OverheadLanguage::C => format!("{INFER_CONFIG_DIR}/kernel-c.json"),
        other => bail!("no Infer overhead arm for {}", other.as_str()),
    };
    let config = fs::read_to_string(&config_template)?
        .replace(SEMGREP_SOURCE_PLACEHOLDER, "dfb_source")
        .replace(SEMGREP_SINK_PLACEHOLDER, "dfb_sink");
    let (scratch, workspace) = overhead_workspace(OverheadTool::Infer, language, run)?;
    let config_path = scratch.join("taint-config.json");
    fs::write(&config_path, &config)?;
    let results_dir = scratch.join("infer-out");
    let (fixture_name, _) = trivial_fixture(language);

    let load_before = load_average_one_minute();
    let mut capture = Command::new(infer);
    capture
        .arg("capture")
        .arg("--results-dir")
        .arg(&results_dir)
        .arg("--")
        .arg("clang")
        .arg("-c")
        .arg(fixture_name)
        .current_dir(&workspace)
        .stdin(std::process::Stdio::null());
    let capture_started = Instant::now();
    let captured = capture
        .output()
        .with_context(|| format!("run infer capture with {}", infer.display()))?;
    let capture_ms = capture_started.elapsed().as_millis() as u64;
    if !captured.status.success() {
        bail!(
            "the Infer overhead capture failed with status {}:\n{}",
            captured.status,
            String::from_utf8_lossy(&captured.stderr)
        );
    }

    // The pinned binary silently analyzes with no taint question at all when
    // the file `--pulse-taint-config` names does not exist, so its presence is
    // proven before the analyzer runs — the same guard the kernel keeps.
    let resolved_config = fs::canonicalize(&config_path).unwrap_or_else(|_| config_path.clone());
    if !resolved_config.is_file() {
        bail!("the resolved Infer taint configuration vanished before analysis");
    }
    let mut analyze = Command::new(infer);
    analyze
        .arg("analyze")
        .arg("--results-dir")
        .arg(&results_dir)
        .arg("--pulse-only")
        .arg("--sarif")
        .arg("--pulse-taint-config")
        .arg(&resolved_config)
        .current_dir(&workspace)
        .stdin(std::process::Stdio::null());
    let analyze_started = Instant::now();
    let analyzed = analyze
        .output()
        .with_context(|| format!("run infer analyze with {}", infer.display()))?;
    let analyze_ms = analyze_started.elapsed().as_millis() as u64;
    if !analyzed.status.success() {
        bail!(
            "the Infer overhead analyze failed with status {}:\n{}",
            analyzed.status,
            String::from_utf8_lossy(&analyzed.stderr)
        );
    }
    fs::remove_dir_all(&scratch).ok();
    Ok(OverheadRun {
        phases: vec![
            ("capture".into(), capture_ms),
            ("analyze".into(), analyze_ms),
        ],
        wall_ms: capture_ms + analyze_ms,
        load_before,
    })
}
