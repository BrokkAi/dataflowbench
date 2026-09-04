//! The Pysa adapter: its pinned identity and configuration, its case
//! selection, its invocation, and the normalization of its own retained
//! evidence to the five benchmark outcomes.
//!
//! See adapters/pysa/README.md for the published capability record, and
//! docs/adding-an-adapter.md for the shape every adapter follows.

use crate::adapters::semgrep::{SEMGREP_SINK_PLACEHOLDER, SEMGREP_SOURCE_PLACEHOLDER};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::{case_paths, fixture_revision, validate_cases, validate_kernel_population_with};
use crate::evidence::{
    AnchorDialect, EvidenceAnchorMatch, SarifAnchorMatch, SinkAnchorLocation,
    benchmark_endpoint_names, evidence_path_matches_file, sink_anchor_locations,
};
use crate::freeze::required_string;
use crate::latency::{
    OverheadLanguage, OverheadRun, OverheadTool, OverheadTools, load_average_one_minute,
    overhead_workspace, trivial_fixture,
};
use crate::modeling::{
    ModelingCategory, ModelingRunPlan, materialize_modeling_workspace, modeling_anchor_dialect,
    modeling_case_scratch, modeling_category, modeling_partition_outcome,
    modeling_supported_templates, plan_modeling_run,
};
use crate::native::{
    NativeRunPlan, native_anchor_tally_outcome, native_case_scratch, native_partition_outcome,
    native_sink_anchor_locations, native_supported_templates, plan_native_run,
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

/// The mode annotations that make Pysa's propagator and summary declarations
/// load-bearing. Amendment A16 measured why they are mandatory: the pinned
/// pair resolves the matrix's reflective opaque body on its own (Pyrefly
/// narrows `getattr(_impl, name)` over the local string constant), so without
/// `@SkipAnalysis` (ignore the declared entity's body) and `@SkipObscure` (no
/// obscure taint-through fallback for it) the engine's own body reading — not
/// the declaration — would decide every category P and O cell.
pub(crate) const PYSA_MODELING_SKIP_MODES: [&str; 2] = ["@SkipAnalysis", "@SkipObscure"];

/// Enforce the load-bearing-model requirement on the Pysa modeling artifact:
/// every `TaintInTaintOut` declaration — the propagator and summary surface —
/// must sit under both skip modes. The artifact is cut into per-template
/// blocks by the runner, so the check walks the declarations rather than the
/// file: each `def` line carrying a `TaintInTaintOut` must be immediately
/// preceded by the two mode lines.
pub(crate) fn require_pysa_modeling_load_bearing(artifact: &str, path: &str) -> Result<()> {
    let lines: Vec<&str> = artifact.lines().collect();
    let mut saw_tito = false;
    for (index, line) in lines.iter().enumerate() {
        if !line.trim_start().starts_with("def ") || !line.contains("TaintInTaintOut") {
            continue;
        }
        saw_tito = true;
        let preceding: Vec<&str> = lines[..index]
            .iter()
            .rev()
            .take(PYSA_MODELING_SKIP_MODES.len())
            .map(|line| line.trim())
            .collect();
        for mode in PYSA_MODELING_SKIP_MODES {
            if !preceding.contains(&mode) {
                bail!(
                    "{path}: the declaration {:?} carries TaintInTaintOut without {mode}; docs/modeling-matrix.md#the-load-bearing-model-requirement and Amendment A16 require both skip modes on every declared propagator and summary entity, because the pinned pair follows the fixture bodies on its own",
                    line.trim()
                );
            }
        }
    }
    if !saw_tito {
        bail!(
            "{path} declares no TaintInTaintOut at all; the scored category P and O blocks are missing"
        );
    }
    Ok(())
}

/// Where the pinned pyre-check wheel puts its shipped taint model suite,
/// relative to the environment the pinned `pyre` client is installed in.
pub(crate) const PYSA_NATIVE_SUITE_RELATIVE: &str = "lib/pyre_check/taint";

/// The shipped sink model every Python native template sinks through
/// (`rce_sinks.pysa`, kind `RemoteCodeExecution`). The native invocation
/// carries `--no-verify` — the shipped suite does not verify over a
/// stdlib-only project — so the proof that the suite actually loaded moves
/// into the retained evidence: a run whose `taint-output.json` carries no
/// model for this callable never produced a coverage result, and is a
/// `runner-error` rather than a clean negative.
pub(crate) const PYSA_NATIVE_SINK_MODEL: &str = "os.system";

// ---------------------------------------------------------------------------
// Pysa kernel runner.
//
// Pysa is the taint analysis of Meta's pyre-check distribution: `.pysa` model
// files declare sources and sinks against real definitions, a `taint.config`
// declares the kinds and the rule, and `pyre analyze` runs the taint fixpoint
// and writes newline-delimited JSON evidence. The pinned 0.10.0 client no
// longer carries its own Python front end for this path: it drives the
// separately released Pyrefly binary for module and call-graph resolution, so
// the pin is a **pair** — pyre-check 0.10.0 plus pyrefly 1.2.0, its
// contemporaneous stable release — and both identities are witnessed per run.
// Two front-end behaviors verified in the field are load-bearing and are
// guarded below: without a `pyrefly.toml` naming the sources as the project,
// Pyrefly exports every call in the fixture as an unresolved
// `EmptyPyreflyCallTarget` and the analysis finds nothing while exiting
// cleanly; and a model naming a function the fixture does not define fails
// the run loudly (exit 10), so a mis-resolved endpoint can never read as a
// clean negative.
// ---------------------------------------------------------------------------

/// The pinned pyre-check release, self-reported by the client as
/// `Client version:`.
pub(crate) const PYSA_PINNED_PYRE_VERSION: &str = "0.10.0";

/// The pinned Pyrefly release the client drives — the stable release
/// contemporaneous with the pinned pyre-check (2026-08-01 beside 2026-08-06).
pub(crate) const PYSA_PINNED_PYREFLY_VERSION: &str = "1.2.0";

pub(crate) const PYSA_CONFIG_DIR: &str = "adapters/pysa";

/// The one rule code the committed `taint.config` declares. Only issues
/// carrying it are flow claims; the config declares no other rule, so any
/// other code in the evidence is a configuration drift and reads as such.
pub(crate) const PYSA_RULE_CODE: u64 = 9901;

pub(crate) const PYSA_SOURCE_MODULE_PLACEHOLDER: &str = "__DFB_SOURCE_MODULE__";
pub(crate) const PYSA_SINK_MODULE_PLACEHOLDER: &str = "__DFB_SINK_MODULE__";

pub(crate) struct PysaTools {
    pub(crate) pyre: PathBuf,
    pub(crate) pyre_binary: PathBuf,
    pub(crate) pyrefly: PathBuf,
}

pub(crate) fn pysa_taint_config_path() -> String {
    format!("{PYSA_CONFIG_DIR}/taint.config")
}

pub(crate) fn pysa_model_template_path() -> String {
    format!("{PYSA_CONFIG_DIR}/models/kernel-python.pysa")
}

/// Both committed Pysa configuration artifacts, so one configuration hash
/// binds the rule declaration and the model template together.
pub(crate) fn pysa_configuration_paths() -> BTreeSet<PathBuf> {
    BTreeSet::from([
        PathBuf::from(pysa_taint_config_path()),
        PathBuf::from(pysa_model_template_path()),
    ])
}

/// Witness the identity of the exact tool pair this run invokes: the
/// pyre-check client's self-reported version and the Pyrefly binary's, each
/// refused with both values in the error when it is not the pinned one, plus
/// the measured digests of the analysis and front-end binaries actually
/// handed to the client.
pub(crate) fn witness_pysa_identity(tools: &PysaTools) -> Result<(String, String)> {
    let pyre_output = Command::new(&tools.pyre)
        .arg("--version")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run {} --version", tools.pyre.display()))?;
    if !pyre_output.status.success() {
        bail!(
            "{} --version failed with status {}",
            tools.pyre.display(),
            pyre_output.status
        );
    }
    let pyre_stdout = String::from_utf8_lossy(&pyre_output.stdout);
    let pyre_version = pyre_stdout
        .lines()
        .find_map(|line| line.trim().strip_prefix("Client version:"))
        .map(str::trim)
        .filter(|version| !version.is_empty())
        .context("pyre did not report a client version")?
        .to_string();
    if pyre_version != PYSA_PINNED_PYRE_VERSION {
        bail!(
            "the pyre client at {} witnessed version {pyre_version}, but this adapter pins {PYSA_PINNED_PYRE_VERSION}; refusing to publish a pinned identity for a client that is not the pinned release",
            tools.pyre.display()
        );
    }
    let pyrefly_output = Command::new(&tools.pyrefly)
        .arg("--version")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run {} --version", tools.pyrefly.display()))?;
    if !pyrefly_output.status.success() {
        bail!(
            "{} --version failed with status {}",
            tools.pyrefly.display(),
            pyrefly_output.status
        );
    }
    let pyrefly_stdout = String::from_utf8_lossy(&pyrefly_output.stdout);
    let pyrefly_version = pyrefly_stdout
        .lines()
        .find_map(|line| line.trim().strip_prefix("pyrefly"))
        .map(str::trim)
        .filter(|version| !version.is_empty())
        .context("pyrefly did not report a version")?
        .to_string();
    if pyrefly_version != PYSA_PINNED_PYREFLY_VERSION {
        bail!(
            "the pyrefly binary at {} witnessed version {pyrefly_version}, but this adapter pins {PYSA_PINNED_PYREFLY_VERSION}; refusing to publish a pinned identity for a front end that is not the pinned release",
            tools.pyrefly.display()
        );
    }
    let pyre_binary_digest = format!(
        "{:x}",
        Sha256::digest(fs::read(&tools.pyre_binary).with_context(|| {
            format!(
                "read the pyre analysis binary {}",
                tools.pyre_binary.display()
            )
        })?)
    );
    let pyrefly_digest = format!(
        "{:x}",
        Sha256::digest(
            fs::read(&tools.pyrefly)
                .with_context(|| format!("read the pyrefly binary {}", tools.pyrefly.display()))?
        )
    );
    let build_identity = format!(
        "pyre-check:{pyre_version} pyre.bin-sha256:{pyre_binary_digest} pyrefly:{pyrefly_version} pyrefly-sha256:{pyrefly_digest}"
    );
    Ok((pyre_version, build_identity))
}

pub(crate) fn select_pysa_cases() -> Result<Vec<(PathBuf, Value)>> {
    let mut selected = Vec::new();
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
        if case["language"] == "python" && case["track"] == "taint" && case["score_tier"] == "core"
        {
            selected.push((path, case));
        }
    }
    validate_kernel_population_with(
        &selected,
        "Pysa Python kernel",
        &expected_core_templates("python"),
    )?;
    Ok(selected)
}

/// The issues and models of one retained Pysa evidence document — the
/// newline-delimited JSON `taint-output.json` the analysis writes, parsed
/// whole so reconciliation and the activation guard read the same bytes the
/// run retained.
pub(crate) struct PysaEvidence {
    pub(crate) issues: Vec<Value>,
    pub(crate) model_callables: BTreeSet<String>,
}

pub(crate) fn parse_pysa_evidence(raw: &str) -> std::result::Result<PysaEvidence, String> {
    let mut issues = Vec::new();
    let mut model_callables = BTreeSet::new();
    for (index, line) in raw.lines().enumerate() {
        if line.trim().is_empty() {
            continue;
        }
        let entry: Value = serde_json::from_str(line)
            .map_err(|error| format!("line {} does not parse: {error}", index + 1))?;
        match entry["kind"].as_str() {
            Some("issue") => issues.push(entry["data"].clone()),
            Some("model") => {
                if let Some(callable) = entry["data"]["callable"].as_str() {
                    model_callables.insert(callable.to_string());
                }
            }
            _ => {}
        }
    }
    Ok(PysaEvidence {
        issues,
        model_callables,
    })
}

/// Why the retained evidence disqualifies this run's negative reading, if it
/// does. The benchmark endpoints are bound by the resolved `.pysa` models; a
/// model that failed to bind fails the run loudly in the pinned pair, but the
/// activation is still proven from the retained document itself — the same
/// discipline as the OpenTaint rule-load guard — so a clean `not-reached`
/// always carries the evidence that both endpoints were modeled.
pub(crate) fn pysa_model_activation_failure(
    evidence: &PysaEvidence,
    source_callable: &str,
    sink_callable: &str,
) -> Option<String> {
    for callable in [source_callable, sink_callable] {
        if !evidence.model_callables.contains(callable) {
            return Some(format!(
                "the retained evidence carries no model for {callable:?}, so the benchmark endpoints were never bound"
            ));
        }
    }
    None
}

/// Does one Pysa issue's location evidence sit on a callsite of the anchored
/// sink? The issue's own position is where the flow is reported; each
/// backward-trace root adds the sink-reach positions the engine's own path
/// evidence names, exactly as the Infer reconciliation reads its final
/// `codeFlows` step. All positions name lines in the issue's own file.
pub(crate) fn pysa_issue_anchor_match(
    issue: &Value,
    sink_locations: &[SinkAnchorLocation],
) -> EvidenceAnchorMatch {
    let Some(file) = issue["filename"].as_str() else {
        return EvidenceAnchorMatch::Ambiguous;
    };
    let mut lines = BTreeSet::new();
    if let Some(line) = issue["line"].as_u64() {
        lines.insert(line);
    }
    for trace in issue["traces"].as_array().into_iter().flatten() {
        if trace["name"] != "backward" {
            continue;
        }
        for root in trace["roots"].as_array().into_iter().flatten() {
            if let Some(line) = root["origin"]["line"].as_u64() {
                lines.insert(line);
            }
            if let Some(line) = root["call_site"]
                .as_str()
                .and_then(|span| span.split(':').next())
                .and_then(|line| line.parse::<u64>().ok())
            {
                lines.insert(line);
            }
        }
    }
    lines.remove(&0);
    if lines.is_empty() {
        return EvidenceAnchorMatch::Ambiguous;
    }
    let mut matches = BTreeSet::new();
    for line in &lines {
        for (index, anchor) in sink_locations.iter().enumerate() {
            if evidence_path_matches_file(file, &anchor.file)
                && anchor.callsite_lines.contains(line)
            {
                matches.insert(index);
            }
        }
    }
    if matches.len() > 1 {
        EvidenceAnchorMatch::Ambiguous
    } else if matches.len() == 1 {
        EvidenceAnchorMatch::Matched
    } else {
        EvidenceAnchorMatch::Unmatched
    }
}

/// Decide one Pysa cell from where the declared rule's issues landed,
/// relative to the case's sink anchors. Shared by the kernel and the
/// benchmark-controlled modeling runner, so the two populations cannot drift
/// into two readings of the same evidence shape.
pub(crate) fn pysa_rule_outcome(
    case_path: &Path,
    case: &Value,
    evidence: &PysaEvidence,
    dialect: AnchorDialect,
) -> (&'static str, Vec<String>) {
    let mut diagnostics = Vec::new();
    let mut flow_claims = Vec::new();
    for issue in &evidence.issues {
        if issue["code"].as_u64() == Some(PYSA_RULE_CODE) {
            flow_claims.push(issue);
            if let Some(message) = issue["message"].as_str() {
                diagnostics.push(message.to_string());
            }
        } else {
            diagnostics.push(format!(
                "issue with undeclared rule code {} retained as a diagnostic, not flow evidence",
                issue["code"]
            ));
        }
    }
    if flow_claims.is_empty() {
        diagnostics.sort();
        diagnostics.dedup();
        return ("not-reached", diagnostics);
    }
    let sink_locations = match sink_anchor_locations(case_path, case, dialect) {
        Ok(locations) => locations,
        Err(reason) => {
            return (
                "inconclusive",
                vec![format!(
                    "cannot prove a Pysa issue against the sink anchor: {reason}"
                )],
            );
        }
    };
    let mut matched = 0;
    let mut unmatched = 0;
    let mut ambiguous = 0;
    for issue in flow_claims {
        match pysa_issue_anchor_match(issue, &sink_locations) {
            EvidenceAnchorMatch::Matched => matched += 1,
            EvidenceAnchorMatch::Unmatched => unmatched += 1,
            EvidenceAnchorMatch::Ambiguous => ambiguous += 1,
        }
    }
    diagnostics.sort();
    diagnostics.dedup();
    if ambiguous > 0 {
        diagnostics.push(format!(
            "{ambiguous} Pysa issue(s) carry no usable or an ambiguous sink-anchor location"
        ));
        return ("inconclusive", diagnostics);
    }
    if matched > 0 {
        return ("reached", diagnostics);
    }
    diagnostics.push(format!(
        "{unmatched} Pysa issue(s) did not match the case sink anchor"
    ));
    ("inconclusive", diagnostics)
}

pub(crate) fn run_pysa_python_kernel(tools: &PysaTools) -> Result<()> {
    validate_cases()?;
    let selected = select_pysa_cases()?;
    let taint_config_path = pysa_taint_config_path();
    let taint_config = fs::read_to_string(&taint_config_path)
        .with_context(|| format!("read the Pysa taint configuration {taint_config_path}"))?;
    let taint_config_json: Value = serde_json::from_str(&taint_config)
        .with_context(|| format!("parse the Pysa taint configuration {taint_config_path}"))?;
    if taint_config_json["rules"]
        .as_array()
        .is_none_or(Vec::is_empty)
    {
        bail!("Pysa taint configuration {taint_config_path} declares no rules");
    }
    let template_path = pysa_model_template_path();
    let template = fs::read_to_string(&template_path)
        .with_context(|| format!("read the Pysa model template {template_path}"))?;
    for placeholder in [
        SEMGREP_SOURCE_PLACEHOLDER,
        SEMGREP_SINK_PLACEHOLDER,
        PYSA_SOURCE_MODULE_PLACEHOLDER,
        PYSA_SINK_MODULE_PLACEHOLDER,
    ] {
        if !template.contains(placeholder) {
            bail!("Pysa model template {template_path} does not carry {placeholder}");
        }
    }
    let raw_dir = PathBuf::from("reports/raw/pysa-python-kernel");
    fs::create_dir_all(&raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = witness_pysa_identity(tools)?;
    write_run_environment(&raw_dir, "pysa", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(selected.len());

    for (path, case) in selected {
        let id = case["id"].as_str().expect("schema validated");
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) =
            run_pysa_case(tools, &taint_config, &template, &path, &case, &raw_dir)?;
        results.push(normalized_result(
            &case,
            id,
            outcome,
            diagnostics,
            start.elapsed(),
            &raw_path,
        ));
    }

    let configuration_hash = hash_paths(&pysa_configuration_paths())?;
    let report = json!({
        "schema_version": 1,
        "tool": "pysa",
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
    let report_path = "reports/pysa-python-kernel.json";
    write_and_validate_report(Path::new(report_path), &report)?;
    println!("wrote {report_path}");
    Ok(())
}

pub(crate) fn write_pysa_error(
    raw_dir: &Path,
    id: &str,
    stage: &str,
    diagnostic: &str,
    output: Option<&std::process::Output>,
) -> Result<PathBuf> {
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let mut evidence = json!({
        "adapter": "pysa",
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

/// The module Pysa knows an anchored fixture file as: its stem, because the
/// runner materializes every fixture flat in the workspace's one source root.
pub(crate) fn pysa_anchor_module(file: &str) -> std::result::Result<String, String> {
    file.strip_suffix(".py")
        .filter(|stem| !stem.is_empty())
        .map(str::to_string)
        .ok_or_else(|| format!("anchor file {file:?} is not a .py module"))
}

pub(crate) fn run_pysa_case(
    tools: &PysaTools,
    taint_config: &str,
    template: &str,
    case_path: &Path,
    case: &Value,
    raw_dir: &Path,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = case["id"].as_str().expect("schema validated");
    let raw_path = raw_dir.join(format!("{id}.json"));
    let error_path = raw_dir.join(format!("{id}-error.json"));
    let models_path = raw_dir.join(format!("{id}-models.pysa"));
    let timing_path = case_timing_path(raw_dir, id);
    for stale in [&raw_path, &error_path, &models_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    // A case whose endpoints cannot be resolved from its own markers has no
    // usable anchor evidence: `inconclusive` with a retained reason, never a
    // clean negative.
    let endpoints = match benchmark_endpoint_names(case_path, case, AnchorDialect::Python) {
        Ok(endpoints) => endpoints,
        Err(reason) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled Pysa endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "pysa",
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
    let source_anchor_file = case["source_anchors"][0]["file"]
        .as_str()
        .expect("schema validated");
    let sink_anchor_file = case["sink_anchors"][0]["file"]
        .as_str()
        .expect("schema validated");
    let (source_module, sink_module) = match (
        pysa_anchor_module(source_anchor_file),
        pysa_anchor_module(sink_anchor_file),
    ) {
        (Ok(source), Ok(sink)) => (source, sink),
        (Err(reason), _) | (_, Err(reason)) => {
            let diagnostic =
                format!("cannot derive the benchmark-controlled Pysa endpoints: {reason}");
            fs::write(
                &error_path,
                serde_json::to_string_pretty(&json!({
                    "adapter": "pysa",
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
    let source_callable = format!("{source_module}.{}", endpoints.source_function);
    let sink_callable = format!("{sink_module}.{}", endpoints.sink_function);

    let models = template
        .replace(PYSA_SOURCE_MODULE_PLACEHOLDER, &source_module)
        .replace(PYSA_SINK_MODULE_PLACEHOLDER, &sink_module)
        .replace(SEMGREP_SOURCE_PLACEHOLDER, &endpoints.source_function)
        .replace(SEMGREP_SINK_PLACEHOLDER, &endpoints.sink_function);
    fs::write(&models_path, &models)?;

    let scratch = std::env::temp_dir()
        .join("dataflowbench-pysa-python")
        .join(id);
    if scratch.exists() {
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()))?;
    }
    fs::create_dir_all(&scratch)?;
    let result = (|| {
        let source_root = scratch.join("src");
        let models_dir = scratch.join("models");
        let output_dir = scratch.join("out");
        for directory in [&source_root, &models_dir, &output_dir] {
            fs::create_dir_all(directory)?;
        }
        let fixture_root = case_path.parent().expect("case path has parent");
        for fixture in case["fixture_files"].as_array().expect("schema validated") {
            let fixture = fixture.as_str().expect("schema validated");
            fs::copy(fixture_root.join(fixture), source_root.join(fixture))?;
        }
        fs::write(models_dir.join("taint.config"), taint_config)?;
        fs::write(models_dir.join("dfb.pysa"), &models)?;
        // Without this project declaration, the pinned Pyrefly exports every
        // call in the fixture as an unresolved `EmptyPyreflyCallTarget` and
        // the analysis finds nothing while exiting cleanly — verified in the
        // field, and the reason this file is part of the pinned invocation.
        fs::write(
            scratch.join("pyrefly.toml"),
            "project-includes = [\"src/**/*.py\"]\n",
        )?;
        fs::write(
            scratch.join(".pyre_configuration"),
            serde_json::to_string_pretty(&json!({
                "source_directories": ["src"],
                "taint_models_path": ["models"]
            }))? + "\n",
        )?;

        let pyrefly_dir = tools
            .pyrefly
            .parent()
            .map(Path::to_path_buf)
            .unwrap_or_else(|| PathBuf::from("."));
        let mut search_path = pyrefly_dir.into_os_string();
        if let Some(existing) = std::env::var_os("PATH") {
            search_path.push(":");
            search_path.push(existing);
        }
        let mut command = Command::new(&tools.pyre);
        command
            .arg("-n")
            .arg("--binary")
            .arg(&tools.pyre_binary)
            .arg("analyze")
            .arg("--save-results-to")
            .arg(&output_dir)
            .env("PATH", &search_path)
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        // The client orchestrates the Pyrefly front end and the analysis
        // binary inside one invocation; that boundary is not
        // adapter-observable as separate subprocesses, so the phase is
        // `total`, like Joern's and Semgrep's.
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn the Pysa analysis with {}: {error}",
                    tools.pyre.display()
                );
                let path = write_pysa_error(raw_dir, id, "analyzer-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(raw_dir, "pysa", id, &[("total", invoked.elapsed())])?;
        if !output.status.success() {
            let diagnostic = format!("the Pysa analysis failed with status {}", output.status);
            let path = write_pysa_error(
                raw_dir,
                id,
                "analyzer-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let taint_output = output_dir.join("taint-output.json");
        if !taint_output.exists() {
            let diagnostic =
                "the Pysa analysis exited cleanly but wrote no taint-output.json".to_string();
            let path =
                write_pysa_error(raw_dir, id, "analyzer-output", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::copy(&taint_output, &raw_path)?;
        let evidence = match parse_pysa_evidence(&fs::read_to_string(&raw_path)?) {
            Ok(evidence) => evidence,
            Err(reason) => {
                let diagnostic = format!("parse Pysa evidence {}: {reason}", raw_path.display());
                let path = write_pysa_error(raw_dir, id, "analyzer-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        if let Some(reason) =
            pysa_model_activation_failure(&evidence, &source_callable, &sink_callable)
        {
            let diagnostic = format!("the benchmark models did not activate: {reason}");
            let path =
                write_pysa_error(raw_dir, id, "model-activation", &diagnostic, Some(&output))?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let (outcome, diagnostics) =
            pysa_rule_outcome(case_path, case, &evidence, AnchorDialect::Python);
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Pysa case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Pysa case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// Cut one template's declarations out of the committed Pysa modeling
/// artifact. The artifact is one hash-bound file with `# template:` markers;
/// the cut is mechanical, never an edit, and it exists because the pinned
/// pair refuses a model that names a definition the case's sources do not
/// carry — a whole-matrix model file would fail verification on every case.
pub(crate) fn pysa_modeling_block(artifact: &str, template: &str, path: &str) -> Result<String> {
    let marker = format!("# template: {template}\n");
    let start = artifact.find(&marker).with_context(|| {
        format!(
            "{path} carries no `# template: {template}` block; docs/modeling-matrix.md makes a missing model a benchmark defect that fails the build, never an outcome"
        )
    })? + marker.len();
    let rest = &artifact[start..];
    let end = rest.find("# template: ").unwrap_or(rest.len());
    Ok(rest[..end].trim().to_string())
}

/// The callables a resolved modeling block binds as the source and sink
/// models. The activation guard requires each to appear as a bound model in
/// the retained evidence — the same discipline as the kernel's guard, read
/// from the block itself so the guard follows the declarations rather than
/// restating them.
pub(crate) fn pysa_block_model_callables(block: &str) -> Vec<String> {
    block
        .lines()
        .filter(|line| line.contains("TaintSource[") || line.contains("TaintSink["))
        .filter_map(|line| {
            line.trim()
                .strip_prefix("def ")
                .and_then(|rest| rest.split('(').next())
                .map(str::to_string)
        })
        .collect()
}

/// Run one *scored* modeling cell through Pysa's `.pysa` model surface.
///
/// The kernel's per-case machinery is mirrored — the same isolated workspace,
/// the same load-bearing `pyrefly.toml`, the same loud model-verification
/// failure mode, the same activation guard read from the retained evidence —
/// and the reconciliation *is* the kernel's, through `pysa_rule_outcome`.
/// What differs is where the models come from: the committed modeling
/// artifact's per-template block, materialized verbatim, with no endpoint
/// placeholders to resolve, because here the endpoint identities *are* the
/// model.
pub(crate) fn run_pysa_modeling_case(
    tools: &PysaTools,
    taint_config: &str,
    artifact: &str,
    case_path: &Path,
    case: &Value,
    plan: &ModelingRunPlan,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "modeling case")?;
    let template = required_string(case, "template_id", id)?;
    let raw_path = plan.raw_dir.join(format!("{id}.json"));
    let error_path = plan.raw_dir.join(format!("{id}-error.json"));
    let models_path = plan.raw_dir.join(format!("{id}-models.pysa"));
    let timing_path = case_timing_path(&plan.raw_dir, id);
    for stale in [&raw_path, &error_path, &models_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let artifact_path = plan
        .language
        .artifact(ModelingTool::Pysa)
        .expect("the plan resolved the artifact");
    let models = pysa_modeling_block(artifact, template, artifact_path)?;
    fs::write(&models_path, format!("{models}\n"))?;
    let model_callables = pysa_block_model_callables(&models);

    let scratch = modeling_case_scratch(ModelingTool::Pysa, plan.language, id)?;
    let result = (|| {
        let source_root = scratch.join("src");
        let models_dir = scratch.join("models");
        let output_dir = scratch.join("out");
        for directory in [&source_root, &models_dir, &output_dir] {
            fs::create_dir_all(directory)?;
        }
        materialize_modeling_workspace(case_path, case, &source_root)?;
        fs::write(models_dir.join("taint.config"), taint_config)?;
        fs::write(models_dir.join("dfb.pysa"), format!("{models}\n"))?;
        // Load-bearing for the front end, exactly as in the kernel: without
        // this project declaration Pyrefly exports every call as unresolved
        // and the analysis finds nothing while exiting cleanly.
        fs::write(
            scratch.join("pyrefly.toml"),
            "project-includes = [\"src/**/*.py\"]\n",
        )?;
        fs::write(
            scratch.join(".pyre_configuration"),
            serde_json::to_string_pretty(&json!({
                "source_directories": ["src"],
                "taint_models_path": ["models"]
            }))? + "\n",
        )?;

        let pyrefly_dir = tools
            .pyrefly
            .parent()
            .map(Path::to_path_buf)
            .unwrap_or_else(|| PathBuf::from("."));
        let mut search_path = pyrefly_dir.into_os_string();
        if let Some(existing) = std::env::var_os("PATH") {
            search_path.push(":");
            search_path.push(existing);
        }
        let mut command = Command::new(&tools.pyre);
        command
            .arg("-n")
            .arg("--binary")
            .arg(&tools.pyre_binary)
            .arg("analyze")
            .arg("--save-results-to")
            .arg(&output_dir)
            .env("PATH", &search_path)
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn the Pysa analysis with {}: {error}",
                    tools.pyre.display()
                );
                let path =
                    write_pysa_error(&plan.raw_dir, id, "analyzer-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(&plan.raw_dir, "pysa", id, &[("total", invoked.elapsed())])?;
        if !output.status.success() {
            let diagnostic = format!("the Pysa analysis failed with status {}", output.status);
            let path = write_pysa_error(
                &plan.raw_dir,
                id,
                "analyzer-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let taint_output = output_dir.join("taint-output.json");
        if !taint_output.exists() {
            let diagnostic =
                "the Pysa analysis exited cleanly but wrote no taint-output.json".to_string();
            let path = write_pysa_error(
                &plan.raw_dir,
                id,
                "analyzer-output",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::copy(&taint_output, &raw_path)?;
        let evidence = match parse_pysa_evidence(&fs::read_to_string(&raw_path)?) {
            Ok(evidence) => evidence,
            Err(reason) => {
                let diagnostic = format!("parse Pysa evidence {}: {reason}", raw_path.display());
                let path =
                    write_pysa_error(&plan.raw_dir, id, "analyzer-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        for callable in &model_callables {
            if !evidence.model_callables.contains(callable) {
                let diagnostic = format!(
                    "the benchmark models did not activate: the retained evidence carries no model for {callable:?}"
                );
                let path = write_pysa_error(
                    &plan.raw_dir,
                    id,
                    "model-activation",
                    &diagnostic,
                    Some(&output),
                )?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        }
        let (outcome, diagnostics) = pysa_rule_outcome(
            case_path,
            case,
            &evidence,
            modeling_anchor_dialect(plan.language)?,
        );
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Pysa case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Pysa case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// Run Pysa's benchmark-controlled modeling matrix for one language — Python,
/// the engine's only one; any other language fails the plan's coverage gate.
///
/// The shape is `run_modeling`'s, stated separately because the identity is a
/// witnessed *pair* rather than a single binary: partition first, scored arm
/// second, one report, the scored/declined split printed from the partition.
pub(crate) fn run_pysa_modeling(tools: &PysaTools, language: ModelingLanguage) -> Result<()> {
    let plan = plan_modeling_run(ModelingTool::Pysa, language)?;
    let artifact_path = plan
        .language
        .artifact(ModelingTool::Pysa)
        .expect("the plan resolved the artifact");
    let artifact = fs::read_to_string(artifact_path)
        .with_context(|| format!("read the Pysa modeling artifact {artifact_path}"))?;
    let taint_config_path = pysa_taint_config_path();
    let taint_config = fs::read_to_string(&taint_config_path)
        .with_context(|| format!("read the Pysa taint configuration {taint_config_path}"))?;

    fs::create_dir_all(&plan.raw_dir)?;
    let started = now_seconds()?;
    let (version, build_identity) = witness_pysa_identity(tools)?;
    // The identity the retained partition rationales name: the witnessed
    // pair, not a constant — witness_pysa_identity refuses either component
    // off its pin, so both versions here were measured.
    let witnessed_pair =
        format!("Pysa (pyre-check {version} + Pyrefly {PYSA_PINNED_PYREFLY_VERSION})");
    write_run_environment(&plan.raw_dir, "pysa", &version, &build_identity)?;
    let revision = fixture_revision()?;
    let mut results = Vec::with_capacity(plan.cases.len());
    for (path, case) in &plan.cases {
        let id = required_string(case, "id", "modeling case")?;
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = if let Some((outcome, reason, raw_path)) =
            modeling_partition_outcome(ModelingTool::Pysa, case, &plan.raw_dir, &witnessed_pair)?
        {
            (outcome, vec![reason], raw_path)
        } else {
            run_pysa_modeling_case(tools, &taint_config, &artifact, path, case, &plan)?
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
        "tool": "pysa",
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
    let scored = modeling_supported_templates(ModelingTool::Pysa);
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
        ModelingTool::Pysa.pinned_identity()
    );
    Ok(())
}
/// The shipped taint model suite beside the pinned pyre client:
/// `<environment>/bin/pyre` → `<environment>/lib/pyre_check/taint`. Resolved
/// from the binary the run was handed, never from a hard-coded machine path,
/// and required to exist before any case runs.
pub(crate) fn pysa_native_suite_dir(tools: &PysaTools) -> Result<PathBuf> {
    let environment = tools
        .pyre
        .parent()
        .and_then(Path::parent)
        .with_context(|| {
            format!(
                "cannot resolve the environment root above {}",
                tools.pyre.display()
            )
        })?;
    let suite = environment.join(PYSA_NATIVE_SUITE_RELATIVE);
    if !suite.is_dir() {
        bail!(
            "the pinned pyre-check environment carries no shipped taint model suite at {}; docs/native-profile.md makes a missing activation artifact a benchmark defect that fails the build, never a result",
            suite.display()
        );
    }
    Ok(suite)
}

/// A content digest over the shipped suite the run activates: every file,
/// sorted by relative path, hashed as path plus bytes. The suite lives inside
/// the installed wheel rather than in this repository, so this digest is what
/// binds the report's configuration hash to one suite instead of one machine.
pub(crate) fn pysa_native_suite_digest(suite: &Path) -> Result<String> {
    fn walk(root: &Path, directory: &Path, files: &mut Vec<PathBuf>) -> Result<()> {
        let mut entries: Vec<PathBuf> = fs::read_dir(directory)
            .with_context(|| format!("read {}", directory.display()))?
            .map(|entry| entry.map(|entry| entry.path()))
            .collect::<std::io::Result<_>>()?;
        entries.sort();
        for entry in entries {
            if entry.is_dir() {
                walk(root, &entry, files)?;
            } else {
                files.push(entry);
            }
        }
        Ok(())
    }
    let mut files = Vec::new();
    walk(suite, suite, &mut files)?;
    let mut hasher = Sha256::new();
    for file in files {
        let relative = file.strip_prefix(suite).expect("walked under the suite");
        hasher.update(relative.to_string_lossy().as_bytes());
        hasher.update(fs::read(&file).with_context(|| format!("read {}", file.display()))?);
    }
    Ok(format!("{:x}", hasher.finalize()))
}

/// Run one *scored* native cell through the shipped Pysa suite.
///
/// Two deliberate differences from the benchmark-controlled Pysa runners,
/// both preregistered in docs/native-profile.md (Amendment A17): the
/// workspace's `taint_models_path` names the shipped suite and nothing else,
/// and the invocation carries `--no-verify`, because the shipped suite does
/// not verify over a stdlib-only project. The activation proof moves into the
/// retained evidence — a run whose output carries no shipped model for
/// `os.system` is a `runner-error`, never a coverage result — and the outcome
/// is decided by `native_anchor_tally_outcome`, the same rule the CodeQL and
/// Semgrep arms reach.
pub(crate) fn run_pysa_native_case(
    tools: &PysaTools,
    suite: &Path,
    case_path: &Path,
    case: &Value,
    plan: &NativeRunPlan,
) -> Result<(&'static str, Vec<String>, PathBuf)> {
    let id = required_string(case, "id", "tool-native case")?;
    let raw_path = plan.raw_dir.join(format!("{id}.json"));
    let error_path = plan.raw_dir.join(format!("{id}-error.json"));
    let timing_path = case_timing_path(&plan.raw_dir, id);
    for stale in [&raw_path, &error_path, &timing_path] {
        if stale.exists() {
            fs::remove_file(stale).with_context(|| format!("clear {}", stale.display()))?;
        }
    }

    let scratch = native_case_scratch(ModelingTool::Pysa, plan.language, id)?;
    let result = (|| {
        let source_root = scratch.join("src");
        let output_dir = scratch.join("out");
        for directory in [&source_root, &output_dir] {
            fs::create_dir_all(directory)?;
        }
        materialize_modeling_workspace(case_path, case, &source_root)?;
        fs::write(
            scratch.join("pyrefly.toml"),
            "project-includes = [\"src/**/*.py\"]\n",
        )?;
        fs::write(
            scratch.join(".pyre_configuration"),
            serde_json::to_string_pretty(&json!({
                "source_directories": ["src"],
                "taint_models_path": [suite.to_string_lossy()]
            }))? + "\n",
        )?;

        let pyrefly_dir = tools
            .pyrefly
            .parent()
            .map(Path::to_path_buf)
            .unwrap_or_else(|| PathBuf::from("."));
        let mut search_path = pyrefly_dir.into_os_string();
        if let Some(existing) = std::env::var_os("PATH") {
            search_path.push(":");
            search_path.push(existing);
        }
        let mut command = Command::new(&tools.pyre);
        command
            .arg("-n")
            .arg("--binary")
            .arg(&tools.pyre_binary)
            .arg("analyze")
            .arg("--no-verify")
            .arg("--save-results-to")
            .arg(&output_dir)
            .env("PATH", &search_path)
            .current_dir(&scratch)
            .stdin(std::process::Stdio::null());
        let invoked = Instant::now();
        let output = match command.output() {
            Ok(output) => output,
            Err(error) => {
                let diagnostic = format!(
                    "failed to spawn the Pysa tool-native analysis with {}: {error}",
                    tools.pyre.display()
                );
                let path =
                    write_pysa_error(&plan.raw_dir, id, "analyzer-spawn", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        write_case_phase_timings(&plan.raw_dir, "pysa", id, &[("total", invoked.elapsed())])?;
        if !output.status.success() {
            let diagnostic = format!(
                "the Pysa tool-native analysis failed with status {}",
                output.status
            );
            let path = write_pysa_error(
                &plan.raw_dir,
                id,
                "analyzer-execution",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let taint_output = output_dir.join("taint-output.json");
        if !taint_output.exists() {
            let diagnostic =
                "the Pysa tool-native analysis exited cleanly but wrote no taint-output.json"
                    .to_string();
            let path = write_pysa_error(
                &plan.raw_dir,
                id,
                "analyzer-output",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        fs::copy(&taint_output, &raw_path)?;
        let evidence = match parse_pysa_evidence(&fs::read_to_string(&raw_path)?) {
            Ok(evidence) => evidence,
            Err(reason) => {
                let diagnostic = format!("parse Pysa evidence {}: {reason}", raw_path.display());
                let path =
                    write_pysa_error(&plan.raw_dir, id, "analyzer-output", &diagnostic, None)?;
                return Ok(("runner-error", vec![diagnostic], path));
            }
        };
        // The --no-verify activation guard: the shipped suite demonstrably
        // loaded, or nothing below is a coverage result.
        if !evidence.model_callables.contains(PYSA_NATIVE_SINK_MODEL) {
            let diagnostic = format!(
                "the shipped suite did not activate: the retained evidence carries no model for {PYSA_NATIVE_SINK_MODEL:?}"
            );
            let path = write_pysa_error(
                &plan.raw_dir,
                id,
                "shipped-suite-activation",
                &diagnostic,
                Some(&output),
            )?;
            return Ok(("runner-error", vec![diagnostic], path));
        }
        let mut diagnostics: Vec<String> = evidence
            .issues
            .iter()
            .filter_map(|issue| issue["message"].as_str().map(str::to_string))
            .collect();
        diagnostics.sort();
        diagnostics.dedup();
        if evidence.issues.is_empty() {
            return Ok(("not-reached", diagnostics, raw_path.clone()));
        }
        let sink_locations = match native_sink_anchor_locations(case_path, case) {
            Ok(locations) => locations,
            Err(reason) => {
                return Ok((
                    "inconclusive",
                    vec![format!(
                        "cannot prove a Pysa issue against the native sink anchor: {reason}"
                    )],
                    raw_path.clone(),
                ));
            }
        };
        // Every issue the shipped rules produce is classified against the
        // platform-sink anchor and tallied by the profile's one rule: a
        // finding on the anchor is `reached` whatever rule produced it, a
        // finding away from it is not evidence about this assertion.
        let (outcome, tally_diagnostics) = native_anchor_tally_outcome(
            evidence.issues.iter().map(|issue| {
                match pysa_issue_anchor_match(issue, &sink_locations) {
                    EvidenceAnchorMatch::Matched => SarifAnchorMatch::Matched,
                    EvidenceAnchorMatch::Unmatched => SarifAnchorMatch::Unmatched,
                    EvidenceAnchorMatch::Ambiguous => SarifAnchorMatch::Ambiguous,
                }
            }),
            "Pysa",
        );
        diagnostics.extend(tally_diagnostics);
        diagnostics.sort();
        diagnostics.dedup();
        Ok((outcome, diagnostics, raw_path.clone()))
    })();

    let cleanup =
        fs::remove_dir_all(&scratch).with_context(|| format!("clear {}", scratch.display()));
    match (result, cleanup) {
        (Ok(normalized), Ok(())) => Ok(normalized),
        (Ok((_, mut diagnostics, path)), Err(error)) => {
            diagnostics.push(format!("Pysa case artifact cleanup failed: {error}"));
            diagnostics.sort();
            diagnostics.dedup();
            Ok(("runner-error", diagnostics, path))
        }
        (Err(error), Ok(())) => Err(error),
        (Err(error), Err(cleanup_error)) => Err(error.context(format!(
            "Pysa case artifact cleanup also failed: {cleanup_error}"
        ))),
    }
}

/// Run Pysa's tool-native probe set for one language — Python, the engine's
/// only one; any other language fails the plan's coverage gate.
///
/// The shape is `run_native`'s, stated separately because the identity is a
/// witnessed pair and the activation artifact lives inside the installed
/// wheel rather than in this repository: the suite is resolved beside the
/// pinned client, its bytes are digested into the run identity and the
/// configuration hash, and the no-benchmark-models gate covers the invocation
/// shape exactly as it covers the other four.
pub(crate) fn run_pysa_native(tools: &PysaTools, language: ModelingLanguage) -> Result<()> {
    let (version, build) = witness_pysa_identity(tools)?;
    let witnessed_pair =
        format!("Pysa (pyre-check {version} + Pyrefly {PYSA_PINNED_PYREFLY_VERSION})");
    let plan = plan_native_run(ModelingTool::Pysa, language, &witnessed_pair)?;
    let suite = pysa_native_suite_dir(tools)?;
    let suite_digest = pysa_native_suite_digest(&suite)?;
    let scored_templates = native_supported_templates(plan.tool, plan.language);

    fs::create_dir_all(&plan.raw_dir)?;
    let started = now_seconds()?;
    let build_identity = format!(
        "{build} — {} (suite-sha256:{suite_digest})",
        plan.activation.identity
    );
    write_run_environment(&plan.raw_dir, "pysa", &version, &build_identity)?;
    let revision = fixture_revision()?;
    // The activation hash binds the shape *and* the shipped bytes: identity,
    // arguments, and the suite digest, so two runs over two different wheel
    // contents can never share a configuration hash.
    let configuration_hash = {
        let mut hasher = Sha256::new();
        hasher.update(plan.activation.identity.as_bytes());
        for argument in &plan.activation.arguments {
            hasher.update(argument.as_bytes());
        }
        hasher.update(suite_digest.as_bytes());
        format!("{:x}", hasher.finalize())
    };
    let mut results = Vec::with_capacity(plan.cases.len());
    for (path, case) in &plan.cases {
        let id = required_string(case, "id", "tool-native case")?;
        let start = Instant::now();
        let (outcome, diagnostics, raw_path) = if let Some((outcome, reason, raw_path)) =
            native_partition_outcome(
                plan.tool,
                plan.language,
                case,
                &plan.activation,
                &plan.raw_dir,
                &witnessed_pair,
            )? {
            (outcome, vec![reason], raw_path)
        } else {
            run_pysa_native_case(tools, &suite, path, case, &plan)?
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
        "tool": "pysa",
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
        ModelingTool::Pysa.pinned_identity()
    );
    Ok(())
}

/// Pysa: one `pyre analyze`, under the committed taint configuration and the
/// committed model template resolved against the trivial fixture's module.
///
/// The scratch project carries the same `.pyre_configuration` and
/// `pyrefly.toml` the cold runner writes — without the latter the pinned
/// Pyrefly resolves no call target and the analysis finds nothing while
/// exiting cleanly, which would be a different invocation, not a faster one.
pub(crate) fn overhead_run_pysa(
    tools: &OverheadTools,
    language: OverheadLanguage,
    run: usize,
    raw_dir: &Path,
) -> Result<OverheadRun> {
    let OverheadLanguage::Python = language else {
        bail!("no Pysa overhead arm for {}", language.as_str());
    };
    let (fixture_name, _) = trivial_fixture(language);
    let module = Path::new(fixture_name)
        .file_stem()
        .and_then(|stem| stem.to_str())
        .context("the trivial Python fixture has no module name")?;
    let taint_config = fs::read_to_string(format!("{PYSA_CONFIG_DIR}/taint.config"))?;
    let models = fs::read_to_string(format!("{PYSA_CONFIG_DIR}/models/kernel-python.pysa"))?
        .replace(PYSA_SOURCE_MODULE_PLACEHOLDER, module)
        .replace(PYSA_SINK_MODULE_PLACEHOLDER, module)
        .replace(SEMGREP_SOURCE_PLACEHOLDER, "dfb_source")
        .replace(SEMGREP_SINK_PLACEHOLDER, "dfb_sink");
    fs::write(raw_dir.join("resolved-models.pysa"), &models)?;

    let (scratch, _) = overhead_workspace(OverheadTool::Pysa, language, run)?;
    let source_root = scratch.join("src");
    let models_dir = scratch.join("models");
    let output_dir = scratch.join("out");
    for directory in [&source_root, &models_dir, &output_dir] {
        fs::create_dir_all(directory)?;
    }
    let (_, fixture_text) = trivial_fixture(language);
    fs::write(source_root.join(fixture_name), fixture_text)?;
    fs::write(models_dir.join("taint.config"), &taint_config)?;
    fs::write(models_dir.join("dfb.pysa"), &models)?;
    fs::write(
        scratch.join("pyrefly.toml"),
        "project-includes = [\"src/**/*.py\"]\n",
    )?;
    fs::write(
        scratch.join(".pyre_configuration"),
        serde_json::to_string_pretty(&json!({
            "source_directories": ["src"],
            "taint_models_path": ["models"]
        }))? + "\n",
    )?;

    let pyrefly_dir = tools
        .pyrefly
        .parent()
        .map(Path::to_path_buf)
        .unwrap_or_else(|| PathBuf::from("."));
    let mut search_path = pyrefly_dir.into_os_string();
    if let Some(existing) = std::env::var_os("PATH") {
        search_path.push(":");
        search_path.push(existing);
    }
    let mut command = Command::new(&tools.pyre);
    command
        .arg("-n")
        .arg("--binary")
        .arg(&tools.pyre_binary)
        .arg("analyze")
        .arg("--save-results-to")
        .arg(&output_dir)
        .env("PATH", &search_path)
        .current_dir(&scratch)
        .stdin(std::process::Stdio::null());
    let load_before = load_average_one_minute();
    let invoked = Instant::now();
    let output = command
        .output()
        .with_context(|| format!("run the Pysa analysis with {}", tools.pyre.display()))?;
    let wall_ms = invoked.elapsed().as_millis() as u64;
    if !output.status.success() {
        bail!(
            "the Pysa overhead invocation failed with status {}:\n{}",
            output.status,
            String::from_utf8_lossy(&output.stderr)
        );
    }
    if !output_dir.join("taint-output.json").exists() {
        bail!("the Pysa overhead invocation exited cleanly but wrote no taint-output.json");
    }
    fs::remove_dir_all(&scratch).ok();
    Ok(OverheadRun {
        phases: vec![("total".into(), wall_ms)],
        wall_ms,
        load_before,
    })
}
