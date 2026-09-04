//! The Joern adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/joern/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::ToolIdentity;
use crate::adapters::codeql::write_rust_cargo_manifest;
use crate::adapters::normalized_report;
use crate::adapters::write_runner_error;
use crate::adapters::{KernelPopulation, select_kernel_cases};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::LoadedCases;
use crate::cases::{fixture_revision, validate_cases};
use crate::evidence::{
    AnchorDialect, EvidenceAnchorMatch, SinkAnchorLocation, benchmark_endpoint_names,
    evidence_path_matches_file, sink_anchor_locations,
};
use crate::freeze::required_string;
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, WarmBatch, WarmLanguage, load_average_one_minute,
    overhead_workspace, warm_batch_completed,
};
use crate::modeling::{
    ModelingCategory, ModelingRunPlan, materialize_modeling_workspace, modeling_anchor_dialect,
    modeling_case_scratch, modeling_category,
};
use crate::report::{hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{
    case_timing_path, now_seconds, write_case_phase_timings, write_run_environment,
};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command, time::Instant};

/// The single Joern query script. One script serves every Joern kernel:
/// the benchmark-controlled endpoints are passed in per case, so nothing in it
/// is language-, template-, or polarity-specific.
pub(crate) const JOERN_KERNEL_SCRIPT: &str = "adapters/joern/queries/kernel.sc";
pub(crate) const JOERN_JAVA_RAW_DIR: &str = "reports/raw/joern-java-kernel";
pub(crate) const JOERN_JAVA_REPORT: &str = "reports/joern-java-kernel.json";
pub(crate) const JOERN_JAVASCRIPT_RAW_DIR: &str = "reports/raw/joern-javascript-kernel";
pub(crate) const JOERN_JAVASCRIPT_REPORT: &str = "reports/joern-javascript-kernel.json";
pub(crate) const JOERN_PYTHON_RAW_DIR: &str = "reports/raw/joern-python-kernel";
pub(crate) const JOERN_PYTHON_REPORT: &str = "reports/joern-python-kernel.json";
pub(crate) const JOERN_RUBY_RAW_DIR: &str = "reports/raw/joern-ruby-kernel";
pub(crate) const JOERN_RUBY_REPORT: &str = "reports/joern-ruby-kernel.json";
pub(crate) const JOERN_PHP_RAW_DIR: &str = "reports/raw/joern-php-kernel";
pub(crate) const JOERN_PHP_REPORT: &str = "reports/joern-php-kernel.json";
pub(crate) const JOERN_RUST_RAW_DIR: &str = "reports/raw/joern-rust-kernel";
pub(crate) const JOERN_RUST_REPORT: &str = "reports/joern-rust-kernel.json";
/// Joern's modeling query script. Unlike the other three adapters, Joern's
/// declarations live in two files — one shared script and one per-language
/// flow-semantics file — so both are hash-bound into the report.
pub(crate) const JOERN_MODELING_SCRIPT: &str = "adapters/joern/queries/modeling.sc";

/// One Joern kernel: a single language, its own case selection, its own
/// frontend, its own normalized report, and its own retained-evidence root.
/// Joern shares one CPG query language and one data-flow engine across all of
/// them, exactly as CodeQL shares a standard library; the populations are kept
/// apart by the selector and the report paths, never by the engine.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum JoernKernel {
    Java,
    JavaScript,
    Python,
    Ruby,
    Php,
    Rust,
}

impl JoernKernel {
    /// The `importCode` language identifier the script is invoked with, which
    /// selects `javasrc2cpg`, `jssrc2cpg`, `pysrc2cpg`, `rubysrc2cpg`,
    /// `php2cpg`, and `rust2cpg` respectively. Each kernel names exactly one
    /// source frontend; none of the six is analyzed through a bytecode or
    /// binary frontend.
    pub(crate) fn frontend(self) -> &'static str {
        match self {
            Self::Java => "JAVASRC",
            Self::JavaScript => "JSSRC",
            Self::Python => "PYTHONSRC",
            Self::Ruby => "RUBYSRC",
            Self::Php => "PHP",
            Self::Rust => "RUST",
        }
    }

    pub(crate) fn dialect(self) -> AnchorDialect {
        match self {
            Self::Java => AnchorDialect::Java,
            Self::JavaScript => AnchorDialect::Ecma,
            Self::Python => AnchorDialect::Python,
            Self::Ruby => AnchorDialect::Ruby,
            Self::Php => AnchorDialect::Php,
            Self::Rust => AnchorDialect::Rust,
        }
    }

    /// Whether a case of this language needs a synthesized build manifest in
    /// its workspace before the frontend can extract it. `rust2cpg` walks a
    /// Cargo crate, not a loose `.rs` file: given a bare fixture it produces an
    /// empty CPG. The manifest is generated per workspace and never written
    /// beside a fixture, so nothing under `cases/` moves.
    pub(crate) fn needs_cargo_manifest(self) -> bool {
        matches!(self, Self::Rust)
    }
}

/// Joern's populations over the shared contract. One engine and one query
/// language stand behind all six, exactly as CodeQL's standard library stands
/// behind its kernels; what keeps them apart is the selector and the dedicated
/// report and evidence roots below, never the engine.
impl KernelPopulation for JoernKernel {
    fn tool(&self) -> &'static str {
        "joern"
    }

    fn language(&self) -> &'static str {
        match self {
            Self::Java => "java",
            Self::JavaScript => "javascript",
            Self::Python => "python",
            Self::Ruby => "ruby",
            Self::Php => "php",
            Self::Rust => "rust",
        }
    }

    fn display_name(&self) -> &'static str {
        match self {
            Self::Java => "Java",
            Self::JavaScript => "JavaScript",
            Self::Python => "Python",
            Self::Ruby => "Ruby",
            Self::Php => "PHP",
            Self::Rust => "Rust",
        }
    }

    fn report(&self) -> String {
        (match self {
            Self::Java => JOERN_JAVA_REPORT,
            Self::JavaScript => JOERN_JAVASCRIPT_REPORT,
            Self::Python => JOERN_PYTHON_REPORT,
            Self::Ruby => JOERN_RUBY_REPORT,
            Self::Php => JOERN_PHP_REPORT,
            Self::Rust => JOERN_RUST_REPORT,
        })
        .to_string()
    }

    fn raw_dir(&self) -> String {
        (match self {
            Self::Java => JOERN_JAVA_RAW_DIR,
            Self::JavaScript => JOERN_JAVASCRIPT_RAW_DIR,
            Self::Python => JOERN_PYTHON_RAW_DIR,
            Self::Ruby => JOERN_RUBY_RAW_DIR,
            Self::Php => JOERN_PHP_RAW_DIR,
            Self::Rust => JOERN_RUST_RAW_DIR,
        })
        .to_string()
    }

    fn label(&self) -> String {
        format!("Joern {} kernel", self.display_name())
    }

    /// One committed script drives every Joern kernel, so one hash binds the
    /// whole set.
    fn configuration_paths(&self, _cases: &LoadedCases) -> Result<BTreeSet<PathBuf>> {
        Ok(BTreeSet::from([PathBuf::from(JOERN_KERNEL_SCRIPT)]))
    }
}

/// Select a Joern kernel population runner-side. The v0.3.0 freeze binds every
/// `case.json` byte, so no case declares a Joern model reference; the selection
/// is by language, track, and score tier alone, and the invocation is pinned
/// here the way the Kotlin Bifrost run pins its policy.
pub(crate) fn select_joern_cases(kernel: JoernKernel) -> Result<LoadedCases> {
    select_kernel_cases(&kernel)
}

pub(crate) fn run_joern_kernel(binary: &Path, kernel: JoernKernel) -> Result<()> {
    validate_cases()?;
    let selected = select_joern_cases(kernel)?;
    let script = Path::new(JOERN_KERNEL_SCRIPT);
    if !script.is_file() {
        bail!("Joern kernel script does not exist: {JOERN_KERNEL_SCRIPT}");
    }
    let script = fs::canonicalize(script).context("resolve the Joern kernel script")?;
    let raw_dir = kernel.raw_dir();
    let raw_dir = Path::new(&raw_dir);
    fs::create_dir_all(raw_dir)?;
    let raw_root = fs::canonicalize(raw_dir).context("resolve the Joern evidence directory")?;
    let configuration_paths = kernel.configuration_paths(&selected)?;
    let started = now_seconds()?;
    let identity = joern_version_identity(binary)?;
    write_run_environment(raw_dir, kernel.tool(), &identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) =
            run_joern_case(binary, &script, &path, &case, raw_dir, &raw_root, kernel)?;
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

/// The exact Joern version every normalized Joern report records. The pinned
/// distribution reports no separate build SHA, so the released version is the
/// build identity.
pub(crate) fn joern_version_identity(binary: &Path) -> Result<ToolIdentity> {
    let output = Command::new(binary)
        .arg("--version")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run {} --version", binary.display()))?;
    if !output.status.success() {
        bail!(
            "{} --version failed with status {}",
            binary.display(),
            output.status
        );
    }
    let stdout = String::from_utf8_lossy(&output.stdout);
    let version = stdout
        .lines()
        .find_map(|line| line.trim().strip_prefix("Version:"))
        .map(str::trim)
        .filter(|version| !version.is_empty())
        .context("Joern did not report a version")?
        .to_string();
    let build_identity = format!("joern-cli:{version}");
    Ok(ToolIdentity::new(version, build_identity))
}

pub(crate) fn run_joern_case(
    binary: &Path,
    script: &Path,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
    raw_root: &Path,
    kernel: JoernKernel,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [&raw_path, &error_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    // A case whose endpoints cannot be resolved from its own markers has no
    // usable anchor evidence. That is `inconclusive` with a retained reason; it
    // is never a clean negative.
    let endpoints = match benchmark_endpoint_names(case_path, case, kernel.dialect()) {
        Ok(endpoints) => endpoints,
        Err(reason) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled Joern endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "joern",
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

    let scratch = joern_case_scratch(kernel, id)?;
    let workspace = scratch.join("source");
    fs::create_dir_all(&workspace)?;
    let fixture_root = case_path.parent().expect("case path has parent");
    for fixture in case["fixture_files"].as_array().expect("schema validated") {
        let fixture = fixture.as_str().expect("schema validated");
        fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
    }
    if kernel.needs_cargo_manifest() {
        write_rust_cargo_manifest(&workspace, case)?;
    }
    let absolute_raw_path = raw_root.join(format!("{id}.json"));

    let result = (|| {
        let mut command = Command::new(binary);
        command
            // Joern materializes its console project under the working
            // directory; keeping that inside the per-case scratch root means no
            // case can observe another case's CPG.
            .current_dir(&scratch)
            .arg("--script")
            .arg(script)
            .arg("--param")
            .arg(format!("inputPath={}", workspace.display()))
            .arg("--param")
            .arg(format!("language={}", kernel.frontend()))
            .arg("--param")
            .arg(format!("sourceName={}", endpoints.source_function))
            .arg("--param")
            .arg(format!("sinkName={}", endpoints.sink_function))
            .arg("--param")
            .arg(format!("outputPath={}", absolute_raw_path.display()))
            .stdin(std::process::Stdio::null());
        // One subprocess imports and queries in the same JVM, so the boundary
        // the adapter observes is the whole invocation: `total`, per #89.
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the Joern {} kernel script with {}: {error}",
                    kernel.display_name(),
                    binary.display()
                );
                let path = write_joern_error(raw_dir, id, "script-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(raw_dir, "joern", id, &[("total", invoked.elapsed())])?;
        if !output.status.success() {
            let diagnostic = format!(
                "Joern {} kernel script failed with status {}",
                kernel.display_name(),
                output.status
            );
            let path =
                write_joern_error(raw_dir, id, "script-execution", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        if !raw_path.is_file() {
            let diagnostic = format!(
                "Joern {} kernel script produced no evidence document",
                kernel.display_name()
            );
            let path = write_joern_error(raw_dir, id, "script-output", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let text = match fs::read_to_string(&raw_path) {
            Ok(text) => text,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "read Joern evidence {}: {error}",
                        raw_path.display()
                    )],
                    raw_path.clone(),
                ));
            }
        };
        let raw: Value = match serde_json::from_str(&text) {
            Ok(raw) => raw,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "parse Joern evidence {}: {error}",
                        raw_path.display()
                    )],
                    raw_path.clone(),
                ));
            }
        };
        let (outcome, diagnostics) = joern_flow_outcome(
            case_path,
            case,
            &raw,
            kernel.dialect(),
            JoernEndpointRule::BothMustBeObserved,
        );
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Joern case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Joern case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

pub(crate) fn joern_case_scratch(kernel: JoernKernel, id: &str) -> Result<PathBuf> {
    let scratch = std::env::temp_dir()
        .join(format!("dataflowbench-joern-{}", kernel.language()))
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    Ok(scratch)
}

pub(crate) fn write_joern_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    write_runner_error("joern", raw_dir, id, stage, diagnostic, output)
}

/// What an absent endpoint means in a Joern evidence document.
///
/// The two populations differ here, and the difference is not a convenience.
/// A **kernel** case is parameterized by its *own* markers, so both endpoints
/// are present in every fixture by construction and their absence can only mean
/// the frontend failed to see them — which is execution coverage, never a
/// negative. A **modeling** case is parameterized by the benchmark's
/// *declarations*, and a declared endpoint being absent from a fixture is
/// frequently the whole content of the assertion: template 2's negative calls
/// `Audit.discard`, so the declared sink `Audit.record` is not there, and that
/// is exactly the answer the cell is asking for. Applying the kernel's rule
/// there would turn every correct category-S negative into `inconclusive`.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) enum JoernEndpointRule {
    /// Kernels: a fixture always contains both of its own endpoints, so an
    /// absent one is an incomplete run.
    BothMustBeObserved,
    /// The modeling matrix: an absent *declared* endpoint is the assertion.
    /// Only an empty extraction is incomplete.
    AbsenceIsTheAssertion,
}

/// Normalize one retained Joern evidence document.
///
/// A flow counts as `reached` only when one of its elements sits on a callsite
/// of the case's own anchored sink function, in the anchored file — the same
/// reconciliation the CodeQL C#, Go, C, C++, and Rust kernels apply to SARIF.
/// Every other state is preserved distinctly: a script, frontend, or engine
/// failure is `runner-error`; a run that produced flows with no usable
/// location, or that `endpoints` says did not observe what it had to, is
/// `inconclusive`. Only a complete run that produced no flow is `not-reached`.
pub(crate) fn joern_flow_outcome(
    case_path: &Path,
    case: &Value,
    raw: &Value,
    dialect: AnchorDialect,
    endpoints: JoernEndpointRule,
) -> (&'static str, Vec<String>) {
    match raw["state"].as_str() {
        Some("analyzed") => {}
        Some("runner-error") => {
            return (
                "runner-error",
                vec![
                    raw["diagnostic"]
                        .as_str()
                        .unwrap_or("Joern reported a runner error without a diagnostic")
                        .to_string(),
                ],
            );
        }
        Some(other) => {
            return (
                "runner-error",
                vec![format!(
                    "Joern evidence declares unexpected state {other:?}"
                )],
            );
        }
        None => {
            return (
                "runner-error",
                vec!["Joern evidence declares no state".to_string()],
            );
        }
    }
    let Some(flows) = raw["flows"].as_array() else {
        return (
            "runner-error",
            vec!["Joern evidence lacks its flows array".to_string()],
        );
    };
    let (Some(sources), Some(sinks)) = (
        raw["source_node_count"].as_u64(),
        raw["sink_node_count"].as_u64(),
    ) else {
        return (
            "runner-error",
            vec!["Joern evidence lacks its endpoint node counts".to_string()],
        );
    };
    match endpoints {
        JoernEndpointRule::BothMustBeObserved if sources == 0 || sinks == 0 => {
            return (
                "inconclusive",
                vec![format!(
                    "Joern resolved {sources} source node(s) and {sinks} sink node(s); the run never observed both benchmark-controlled endpoints"
                )],
            );
        }
        JoernEndpointRule::AbsenceIsTheAssertion
            if raw["method_count"].as_u64().is_none_or(|count| count == 0) =>
        {
            return (
                "inconclusive",
                vec![
                    "Joern extracted no method from the fixture; the run produced nothing to analyze".to_string(),
                ],
            );
        }
        _ => {}
    }
    if flows.is_empty() {
        let mut diagnostics = Vec::new();
        if endpoints == JoernEndpointRule::AbsenceIsTheAssertion && (sources == 0 || sinks == 0) {
            // Retained, not converted: which declared endpoints the fixture
            // even contains is exactly what several modeling negatives are
            // about, and a reader should be able to see it without opening the
            // raw evidence.
            diagnostics.push(format!(
                "Joern resolved {sources} declared source node(s) and {sinks} declared sink node(s) in this fixture"
            ));
        }
        return ("not-reached", diagnostics);
    }
    let sink_locations = match sink_anchor_locations(case_path, case, dialect) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove a Joern flow against the sink anchor: {reason}"
                )],
            );
        }
    };
    let mut matched = 0;
    let mut unmatched = 0;
    let mut ambiguous = 0;
    for flow in flows {
        match joern_flow_anchor_match(flow, &sink_locations) {
            EvidenceAnchorMatch::Matched => matched += 1,
            EvidenceAnchorMatch::Unmatched => unmatched += 1,
            EvidenceAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    if ambiguous > 0 {
        return (
            "inconclusive",
            vec![format!(
                "{ambiguous} Joern flow(s) carry no usable or an ambiguous sink-anchor location"
            )],
        );
    }
    if matched > 0 {
        return ("reached", Vec::new());
    }
    (
        "inconclusive",
        vec![format!(
            "{unmatched} Joern flow(s) did not match the case sink anchor"
        )],
    )
}

pub(crate) fn joern_flow_anchor_match(
    flow: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> EvidenceAnchorMatch {
    let Some(elements) = flow["elements"].as_array() else {
        return EvidenceAnchorMatch::Ambiguous;
    };
    if elements.is_empty() {
        return EvidenceAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    let mut usable = false;
    for element in elements {
        let (Some(file), Some(line)) = (element["file"].as_str(), element["line"].as_u64()) else {
            continue;
        };
        if line == 0 {
            continue;
        }
        usable = true;
        for (index, anchor) in sink_locations.iter().enumerate() {
            if evidence_path_matches_file(file, &anchor.file)
                && anchor.callsite_lines.contains(&line)
            {
                matches.insert(index);
            }
        }
    }
    if !usable || matches.len() > 1 {
        EvidenceAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        EvidenceAnchorMatch::Matched
    } else {
        EvidenceAnchorMatch::Unmatched
    }
}

/// The Joern source-selector shape a template needs, decided from the template
/// identity alone and never from an observed result.
///
/// Category E is the one category whose source is not a call: its handler is
/// never called from the fixture, which is the whole point, so there is no call
/// site to select and the analysis root is the handler's own parameter node.
/// Every other category's source is a call whose returned value is tainted.
pub(crate) fn modeling_joern_source_kind(template: &str) -> Result<&'static str> {
    let category = modeling_category(template).with_context(|| {
        format!("{template:?} is not one of the twelve preregistered modeling templates")
    })?;
    Ok(match category {
        ModelingCategory::EntryPoints => "method-parameter",
        _ => "call-return",
    })
}

pub(crate) fn modeling_joern_frontend(language: ModelingLanguage) -> Result<&'static str> {
    match language {
        ModelingLanguage::Python => Ok("PYTHONSRC"),
        ModelingLanguage::Javascript => Ok("JSSRC"),
        ModelingLanguage::Java => Ok("JAVASRC"),
    }
}

/// Run one scored modeling cell through Joern's flow-semantics surface.
///
/// The kernel's per-case machinery is reused unchanged — workspace
/// materialization, endpoint resolution from the fixture's own marker lines,
/// and `joern_flow_outcome`'s anchor reconciliation. What differs is the script
/// (`modeling.sc`, so `kernel.sc` stays untouched), the semantics file it
/// loads, and the source-selector shape category E needs.
pub(crate) fn run_joern_modeling_case(
    binary: &Path,
    script: &Path,
    semantics: &Path,
    case_path: &Path,
    case: &Value,
    plan: &ModelingRunPlan,
    raw_root: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "modeling case")?;
    let template = required_string(case, "template_id", id)?;
    let dialect = modeling_anchor_dialect(plan.language)?;
    let raw_path = plan.raw_dir.join(format!("{id}.json"));
    let error_path = plan.raw_dir.join(format!("{id}-error.json"));
    let timing_path = case_timing_path(&plan.raw_dir, id);
    for stale in [&raw_path, &error_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let endpoints = match benchmark_endpoint_names(case_path, case, dialect) {
        Ok(endpoints) => endpoints,
        Err(reason) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled Joern endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "joern",
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

    let scratch = modeling_case_scratch(ModelingTool::Joern, plan.language, id)?;
    let workspace = scratch.join("source");
    materialize_modeling_workspace(case_path, case, &workspace)?;
    let absolute_raw_path = raw_root.join(format!("{id}.json"));

    let result = (|| {
        let mut command = Command::new(binary);
        command
            .current_dir(&scratch)
            .arg("--script")
            .arg(script)
            .arg("--param")
            .arg(format!("inputPath={}", workspace.display()))
            .arg("--param")
            .arg(format!(
                "language={}",
                modeling_joern_frontend(plan.language)?
            ))
            .arg("--param")
            .arg(format!("sourceName={}", endpoints.source_function))
            .arg("--param")
            .arg(format!("sinkName={}", endpoints.sink_function))
            .arg("--param")
            .arg(format!(
                "sourceKind={}",
                modeling_joern_source_kind(template)?
            ))
            .arg("--param")
            .arg(format!("semanticsPath={}", semantics.display()))
            .arg("--param")
            .arg(format!("outputPath={}", absolute_raw_path.display()))
            .stdin(std::process::Stdio::null());
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to run the Joern modeling script with {}: {error}",
                    binary.display()
                );
                let path = write_joern_error(&plan.raw_dir, id, "script-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(&plan.raw_dir, "joern", id, &[("total", invoked.elapsed())])?;
        if !output.status.success() {
            let diagnostic = format!("Joern modeling script failed with status {}", output.status);
            let path = write_joern_error(
                &plan.raw_dir,
                id,
                "script-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        if !raw_path.is_file() {
            let diagnostic = "Joern modeling script produced no evidence document".to_string();
            let path = write_joern_error(
                &plan.raw_dir,
                id,
                "script-output",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let text = match fs::read_to_string(&raw_path) {
            Ok(text) => text,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "read Joern evidence {}: {error}",
                        raw_path.display()
                    )],
                    raw_path.clone(),
                ));
            }
        };
        let raw: Value = match serde_json::from_str(&text) {
            Ok(raw) => raw,
            Err(error) => {
                return Ok((
                    "runner-error",
                    vec![format!(
                        "parse Joern evidence {}: {error}",
                        raw_path.display()
                    )],
                    raw_path.clone(),
                ));
            }
        };
        // A modeling negative may legitimately contain no *declared* endpoint —
        // template 2's negative calls `Audit.discard`, so the declared sink
        // `Audit.record` is absent from the fixture by construction. That
        // absence is the assertion, not an incomplete run; only an empty
        // extraction is incomplete.
        let (outcome, diagnostics) = joern_flow_outcome(
            case_path,
            case,
            &raw,
            dialect,
            JoernEndpointRule::AbsenceIsTheAssertion,
        );
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Joern case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Joern case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// The Joern batch script. `kernel.sc` is unchanged and remains the only
/// script any normalized Joern report hashes into its `configuration_hash`.
pub(crate) const JOERN_WARM_BATCH_SCRIPT: &str = "adapters/joern/queries/warm-batch.sc";

/// One Joern batch: k cases imported and queried inside one JVM.
///
/// Workspace materialization is the cold runner's, case by case, and is done
/// **before** the JVM is spawned — fixture materialization is outside every
/// timed window by the tier's exclusion list, warm and cold alike.
pub(crate) fn measure_joern_warm_batch(
    binary: &Path,
    language: WarmLanguage,
    cases: &[(PathBuf, Value)],
    raw_dir: &Path,
    k: usize,
    repeat: usize,
) -> Result<WarmBatch> {
    let WarmLanguage::Java = language;
    let kernel = JoernKernel::Java;
    let script = fs::canonicalize(Path::new(JOERN_WARM_BATCH_SCRIPT))
        .context("resolve the Joern warm-batch script")?;
    let scratch = std::env::temp_dir().join(format!("dataflowbench-warm-joern-{repeat}-{k}"));
    if scratch.exists() {
        fs::remove_dir_all(&scratch)?;
    }
    fs::create_dir_all(&scratch)?;
    let evidence = scratch.join("evidence");
    fs::create_dir_all(&evidence)?;

    let mut manifest = String::new();
    let mut case_ids = Vec::new();
    for (index, (case_path, case)) in cases.iter().enumerate() {
        let id = case["id"].as_str().expect("schema validated");
        let endpoints =
            benchmark_endpoint_names(case_path, case, kernel.dialect()).map_err(|reason| {
                anyhow::anyhow!("{id}: cannot derive the Joern endpoints: {reason}")
            })?;
        let workspace = scratch.join(format!("source-{index}"));
        fs::create_dir_all(&workspace)?;
        let fixture_root = case_path.parent().expect("case path has parent");
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            fs::copy(fixture_root.join(fixture), workspace.join(fixture))?;
        }
        if kernel.needs_cargo_manifest() {
            write_rust_cargo_manifest(&workspace, case)?;
        }
        manifest.push_str(&format!(
            "{id}\t{}\t{}\t{}\t{}\t{}\n",
            workspace.display(),
            kernel.frontend(),
            endpoints.source_function,
            endpoints.sink_function,
            evidence.join(format!("{id}.json")).display(),
        ));
        case_ids.push(id.to_string());
    }
    let manifest_path = scratch.join("batch-manifest.tsv");
    fs::write(&manifest_path, &manifest)?;
    let completion_path = scratch.join("completion.json");

    let mut command = Command::new(binary);
    command
        .current_dir(&scratch)
        .arg("--script")
        .arg(&script)
        .arg("--param")
        .arg(format!("manifestPath={}", manifest_path.display()))
        .arg("--param")
        .arg(format!("completionPath={}", completion_path.display()))
        .stdin(std::process::Stdio::null());
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run the Joern warm batch with {}", binary.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !output.status.success() {
        bail!(
            "the Joern warm batch k={k} failed with status {}:\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    warm_batch_completed(&completion_path, k, repeat, &evidence, &case_ids, raw_dir)?;
    fs::remove_dir_all(&scratch).ok();
    Ok(WarmBatch {
        k,
        wall_ms,
        case_ids,
        load_before,
    })
}

/// Joern: the committed `kernel.sc`, the kernel's own frontend, and the same
/// five parameters the cold runner passes. One JVM, one number.
pub(crate) fn overhead_run_joern(
    binary: &Path,
    language: OverheadLanguage,
    run: usize,
) -> Result<OverheadRun> {
    let kernel = match language {
        OverheadLanguage::Java => JoernKernel::Java,
        OverheadLanguage::Php => JoernKernel::Php,
        other => bail!("no Joern overhead arm for {}", other.as_str()),
    };
    let script = fs::canonicalize(Path::new(JOERN_KERNEL_SCRIPT))
        .context("resolve the Joern kernel script")?;
    let (scratch, workspace) = overhead_workspace(OverheadTool::Joern, language, run)?;
    let evidence = scratch.join("evidence.json");

    let mut command = Command::new(binary);
    command
        .current_dir(&scratch)
        .arg("--script")
        .arg(&script)
        .arg("--param")
        .arg(format!("inputPath={}", workspace.display()))
        .arg("--param")
        .arg(format!("language={}", kernel.frontend()))
        .arg("--param")
        .arg("sourceName=dfb_source")
        .arg("--param")
        .arg("sinkName=dfb_sink")
        .arg("--param")
        .arg(format!("outputPath={}", evidence.display()))
        .stdin(std::process::Stdio::null());
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run the Joern kernel script with {}", binary.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !output.status.success() {
        bail!(
            "the Joern overhead invocation failed with status {}:\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    if !evidence.is_file() {
        bail!("the Joern overhead invocation produced no evidence document");
    }
    fs::remove_dir_all(&scratch).ok();
    Ok(OverheadRun {
        phases: vec![("total".into(), wall_ms)],
        wall_ms,
        load_before,
    })
}
