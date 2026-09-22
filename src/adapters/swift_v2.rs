//! Rust integration boundary for the prospective Swift v2 additions.
//!
//! The Python runner owns compiler/analyzer execution, case budgets, and the
//! native evidence it retains. This module owns the benchmark boundary around
//! that runner: it requires the pinned `swift-synthetic-v2` population, checks
//! the runner's result metadata against the canonical case schema, derives the
//! new configuration set, and publishes one normalized report per model
//! profile. The two reports intentionally never mix `tool-native` modeling
//! cases with the benchmark-controlled `Result` extension cases.
//!
//! The runner contract is `reports/raw/{tool}-swift-v2-additions/run.json`:
//!
//! ```text
//! {
//!   "schema_version": 1,
//!   "population": "swift-synthetic-v2",
//!   "tool": "codeql" | "joern",
//!   "activation_scope": "swift-v2-additions",
//!   "executable_scope": "result-language-extension",
//!   "native_scope": "committed-capability-decisions-only",
//!   "tool_version": "...",
//!   "tool_build_identity": "...",
//!   "configuration_hash": "sha256...",
//!   "fixture_revision": "sha256:...",
//!   "started_at_unix_seconds": 0,
//!   "ended_at_unix_seconds": 0,
//!   "results": [{
//!     "case_id": "...",
//!     "model_profile": "tool-native" | "benchmark-controlled",
//!     "score_tier": "modeling" | "language-extension",
//!     "outcome": "reached" | "not-reached" | "inconclusive" |
//!       "unsupported" | "runner-error",
//!     "diagnostics": ["..."],
//!     "duration_ms": 0,
//!     "peak_memory_mb": null,
//!     "witness_checkpoints": ["..."],
//!     "raw_output": "reports/raw/codeql-swift-v2-additions/..."
//!   }]
//! }
//! ```
//!
//! The Python runner must write repository-relative raw paths. Rust copies
//! canonical source/sink anchors from the case files into the normalized
//! schema and never accepts anchors or outcomes invented by the runner's
//! metadata alone.

use crate::adapters::{ToolIdentity, normalized_report};
use crate::cases::{LoadedCases, case_paths, fixture_revision, validate_cases};
use crate::population;
use crate::report::{hash_paths, normalized_result, write_and_validate_report};
use anyhow::{Context, Result, bail};
use clap::ValueEnum;
use serde_json::Value;
use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::process::Command;
use std::time::Duration;

const RUNNER: &str = "scripts/run-swift-v2-additions.py";
const MODULE: &str = "src/adapters/swift_v2.rs";
const POPULATION: &str = "swift-synthetic-v2";
const RUN_METADATA: &str = "run.json";
const NATIVE_TEMPLATES: [&str; 6] = [
    "dfb-template-native-source-sink",
    "dfb-template-native-propagator",
    "dfb-template-native-sanitizer",
    "dfb-template-native-summary",
    "dfb-template-native-entrypoint",
    "dfb-template-native-persistence",
];
const RESULT_TEMPLATE: &str = "dfb-template-result-error-propagation";

/// The only analyzer choices supported by the Swift v2 runner.
#[derive(Clone, Copy, Debug, Eq, PartialEq, ValueEnum)]
pub(crate) enum SwiftV2Tool {
    Codeql,
    Joern,
}

impl SwiftV2Tool {
    pub(crate) fn key(self) -> &'static str {
        match self {
            Self::Codeql => "codeql",
            Self::Joern => "joern",
        }
    }

    fn raw_dir(self) -> PathBuf {
        PathBuf::from(format!("reports/raw/{}-swift-v2-additions", self.key()))
    }

    fn native_report(self) -> PathBuf {
        PathBuf::from(format!("reports/{}-swift-v2-native.json", self.key()))
    }

    fn result_report(self) -> PathBuf {
        PathBuf::from(format!("reports/{}-swift-v2-result.json", self.key()))
    }

    fn configuration_manifest(self) -> PathBuf {
        PathBuf::from(format!(
            "adapters/{}/swift-v2/configuration-files.json",
            self.key()
        ))
    }
}

#[derive(Debug)]
struct RunMetadata {
    identity: ToolIdentity,
    fixture_revision: String,
    started_at_unix_seconds: u64,
    results: BTreeMap<String, RunnerResult>,
}

#[derive(Debug)]
struct RunnerResult {
    model_profile: String,
    score_tier: String,
    outcome: String,
    diagnostics: Vec<String>,
    duration_ms: u64,
    peak_memory_mb: Value,
    witness_checkpoints: Vec<String>,
    raw_output: PathBuf,
}

/// Hash exactly the new Swift v2 configuration set for one tool.
///
/// `configuration-files.json` is deliberately an explicit array. Its own
/// bytes, this runner, and this module are always included automatically.
/// Old Swift adapter modules are rejected here so a v2 report cannot acquire
/// a hidden dependency on `src/adapters/{codeql,joern}/swift.rs`.
pub(crate) fn configuration_paths(tool: SwiftV2Tool) -> Result<BTreeSet<PathBuf>> {
    let manifest = tool.configuration_manifest();
    let value: Value = serde_json::from_str(&fs::read_to_string(&manifest).with_context(|| {
        format!(
            "read Swift v2 configuration manifest {}",
            manifest.display()
        )
    })?)
    .with_context(|| {
        format!(
            "parse Swift v2 configuration manifest {}",
            manifest.display()
        )
    })?;
    let entries = value
        .as_array()
        .context("Swift v2 configuration manifest must be an explicit array")?;
    if entries.is_empty() {
        bail!(
            "Swift v2 configuration manifest {} is empty",
            manifest.display()
        );
    }

    let mut paths = BTreeSet::from([
        manifest.clone(),
        PathBuf::from(RUNNER),
        PathBuf::from(MODULE),
    ]);
    for entry in entries {
        let text = entry
            .as_str()
            .context("Swift v2 configuration manifest entries must be strings")?;
        if text.is_empty() {
            bail!("Swift v2 configuration path must not be empty");
        }
        let path = PathBuf::from(text);
        if path.is_absolute()
            || path
                .components()
                .any(|component| matches!(component, Component::ParentDir | Component::CurDir))
        {
            bail!("Swift v2 configuration path must be repository-relative: {text:?}");
        }
        let mut normalized = PathBuf::new();
        for component in path.components() {
            match component {
                Component::Normal(name) => normalized.push(name),
                _ => bail!("Swift v2 configuration path must be a plain relative file: {text:?}"),
            }
        }
        if normalized.as_os_str() != path.as_os_str() {
            bail!("Swift v2 configuration path is not normalized: {text:?}");
        }
        if matches!(
            text,
            "src/adapters/codeql/swift.rs" | "src/adapters/joern/swift.rs"
        ) {
            bail!("Swift v2 configuration cannot include an old Swift adapter module: {text}");
        }
        if !paths.insert(path) {
            bail!("duplicate Swift v2 configuration path: {text}");
        }
    }
    let repository = fs::canonicalize(".").context("resolve repository root")?;
    for path in &paths {
        reject_symlink_components(path, "Swift v2 configuration")?;
        let canonical = fs::canonicalize(path).with_context(|| {
            format!(
                "Swift v2 configuration manifest names an unknown or missing file: {}",
                path.display()
            )
        })?;
        if !canonical.starts_with(&repository) || !canonical.is_file() {
            bail!(
                "Swift v2 configuration path escapes the repository or is not a file: {}",
                path.display()
            );
        }
    }
    Ok(paths)
}

/// Run one tool's 14 additions and publish its two profile-pure reports.
pub(crate) fn run_swift_v2_additions(
    tool: SwiftV2Tool,
    codeql: &Path,
    packs: Option<&Path>,
    joern: &Path,
    java_home: Option<&Path>,
) -> Result<()> {
    validate_cases()?;
    let (native_cases, result_cases) = select_additions()?;
    let configuration_paths = configuration_paths(tool)?;
    let configuration_before = hash_paths(&configuration_paths)?;
    let expected_cases = native_cases
        .iter()
        .chain(result_cases.iter())
        .map(|(_, case)| case["id"].as_str().expect("validated case id").to_string())
        .collect::<BTreeSet<_>>();
    let raw_dir = tool.raw_dir();
    let native_report = tool.native_report();
    let result_report = tool.result_report();
    if native_report.exists() || result_report.exists() {
        bail!(
            "refusing to overwrite prior Swift v2 report(s): {} or {}",
            native_report.display(),
            result_report.display()
        );
    }
    if raw_dir.exists() {
        bail!(
            "refusing to overwrite prior Swift v2 evidence {}",
            raw_dir.display()
        );
    }

    let mut command = Command::new("python3");
    command
        .arg(RUNNER)
        .arg("--population")
        .arg(POPULATION)
        .arg("--tool")
        .arg(tool.key())
        .arg("--output")
        .arg(&raw_dir);
    match tool {
        SwiftV2Tool::Codeql => {
            let packs = packs.context("--packs is required for the Swift v2 CodeQL runner")?;
            command
                .arg("--codeql")
                .arg(codeql)
                .arg("--packs")
                .arg(packs);
        }
        SwiftV2Tool::Joern => {
            let java_home =
                java_home.context("--java-home is required for the Swift v2 Joern runner")?;
            command
                .arg("--joern")
                .arg(joern)
                .arg("--java-home")
                .arg(java_home);
        }
    }
    let status = command
        .status()
        .with_context(|| format!("run {RUNNER} for {}", tool.key()))?;
    if !status.success() {
        bail!("{RUNNER} failed for {} with status {status}", tool.key());
    }

    let metadata = read_run_metadata(tool, &raw_dir, &expected_cases, &configuration_before)?;
    let configuration_after = hash_paths(&configuration_paths)?;
    if configuration_after != configuration_before {
        bail!(
            "Swift v2 configuration changed while {} was running (before {configuration_before}, after {configuration_after})",
            tool.key()
        );
    }
    publish_report(
        tool,
        &native_report,
        &native_cases,
        &metadata,
        &configuration_after,
    )?;
    publish_report(
        tool,
        &result_report,
        &result_cases,
        &metadata,
        &configuration_after,
    )?;
    println!(
        "wrote {} and {}",
        native_report.display(),
        result_report.display()
    );
    Ok(())
}

fn select_additions() -> Result<(LoadedCases, LoadedCases)> {
    let active = population::active().context(
        "Swift v2 additions require --population swift-synthetic-v2; no active population was selected",
    )?;
    let paths = case_paths();
    if paths.len() != 104 {
        bail!(
            "Swift v2 additions require the 104-case swift-synthetic-v2 population; found {} cases",
            paths.len()
        );
    }
    let selected: LoadedCases = paths
        .into_iter()
        .map(|path| {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path)?)?;
            Ok((path, case))
        })
        .collect::<Result<LoadedCases>>()?
        .into_iter()
        .filter(|(_, case)| {
            case["language"] == "swift"
                && case["track"] == "taint"
                && (NATIVE_TEMPLATES.contains(&case["template_id"].as_str().unwrap_or(""))
                    || case["template_id"] == RESULT_TEMPLATE)
        })
        .collect();
    active.validate_members(&selected)?;

    let mut native = Vec::new();
    let mut result = Vec::new();
    for (path, case) in selected {
        match case["template_id"].as_str() {
            Some(template) if NATIVE_TEMPLATES.contains(&template) => native.push((path, case)),
            Some(RESULT_TEMPLATE) => result.push((path, case)),
            _ => unreachable!("selection predicate admitted an unknown Swift v2 template"),
        }
    }
    validate_balanced_additions(
        &native,
        "Swift v2 native additions",
        "tool-native",
        "modeling",
        12,
    )?;
    validate_balanced_additions(
        &result,
        "Swift v2 Result additions",
        "benchmark-controlled",
        "language-extension",
        2,
    )?;
    Ok((native, result))
}

fn validate_balanced_additions(
    cases: &LoadedCases,
    label: &str,
    model_profile: &str,
    score_tier: &str,
    expected_count: usize,
) -> Result<()> {
    if cases.len() != expected_count {
        bail!(
            "{label} must select exactly {expected_count} cases; found {}",
            cases.len()
        );
    }
    let mut pairs = BTreeMap::<&str, (usize, usize)>::new();
    for (path, case) in cases {
        if case["model_profile"] != model_profile || case["score_tier"] != score_tier {
            bail!(
                "{label} mixes profile/tier at {} (expected {model_profile}/{score_tier})",
                path.display()
            );
        }
        let template = case["template_id"]
            .as_str()
            .with_context(|| format!("{} lacks template_id", path.display()))?;
        let counts = pairs.entry(template).or_default();
        match case["polarity"].as_str() {
            Some("positive") => counts.0 += 1,
            Some("negative") => counts.1 += 1,
            Some(other) => bail!("{} has unsupported polarity {other:?}", path.display()),
            None => bail!("{} lacks polarity", path.display()),
        }
    }
    if pairs
        .values()
        .any(|(positive, negative)| *positive != 1 || *negative != 1)
    {
        bail!("{label} requires one positive and one negative per template");
    }
    Ok(())
}

fn read_run_metadata(
    tool: SwiftV2Tool,
    raw_dir: &Path,
    expected_cases: &BTreeSet<String>,
    expected_configuration_hash: &str,
) -> Result<RunMetadata> {
    let metadata_path = raw_dir.join(RUN_METADATA);
    let value: Value =
        serde_json::from_str(&fs::read_to_string(&metadata_path).with_context(|| {
            format!("read Swift v2 runner metadata {}", metadata_path.display())
        })?)
        .with_context(|| format!("parse Swift v2 runner metadata {}", metadata_path.display()))?;
    if value["schema_version"] != 1
        || value["population"] != POPULATION
        || value["tool"] != tool.key()
        || value["activation_scope"] != "swift-v2-additions"
        || value["executable_scope"] != "result-language-extension"
        || value["native_scope"] != "committed-capability-decisions-only"
    {
        bail!(
            "Swift v2 runner metadata has the wrong schema, population, tool, or activation scope"
        );
    }
    if required_string(&value, "configuration_hash")? != expected_configuration_hash {
        bail!("Swift v2 runner configuration hash does not match Rust's path set and bytes");
    }
    let version = required_string(&value, "tool_version")?;
    let build_identity = required_string(&value, "tool_build_identity")?;
    if ["unknown", "n/a", "na"].contains(&version.to_ascii_lowercase().as_str())
        || ["unknown", "n/a", "na"].contains(&build_identity.to_ascii_lowercase().as_str())
    {
        bail!("Swift v2 runner metadata has an unwitnessed tool identity");
    }
    let fixture = required_string(&value, "fixture_revision")?.to_string();
    if fixture != fixture_revision()? {
        bail!("Swift v2 runner fixture revision does not match the active population");
    }
    let started = required_u64(&value, "started_at_unix_seconds")?;
    let ended = required_u64(&value, "ended_at_unix_seconds")?;
    if ended < started {
        bail!("Swift v2 runner ended before it started");
    }
    let entries = value["results"]
        .as_array()
        .context("Swift v2 runner metadata results must be an array")?;
    let mut results = BTreeMap::new();
    for entry in entries {
        let id = required_string(entry, "case_id")?.to_string();
        if !expected_cases.contains(&id) {
            bail!("Swift v2 runner returned an unexpected case {id}");
        }
        if results
            .insert(id.clone(), parse_runner_result(entry, raw_dir)?)
            .is_some()
        {
            bail!("Swift v2 runner returned duplicate case {id}");
        }
    }
    let actual = results.keys().cloned().collect::<BTreeSet<_>>();
    if actual != *expected_cases {
        bail!(
            "Swift v2 runner result set mismatch: missing={:?}, unexpected={:?}",
            expected_cases.difference(&actual).collect::<Vec<_>>(),
            actual.difference(expected_cases).collect::<Vec<_>>()
        );
    }
    Ok(RunMetadata {
        identity: ToolIdentity::new(version, build_identity),
        fixture_revision: fixture,
        started_at_unix_seconds: started,
        results,
    })
}

fn parse_runner_result(value: &Value, raw_dir: &Path) -> Result<RunnerResult> {
    let diagnostics = value["diagnostics"]
        .as_array()
        .context("Swift v2 runner diagnostics must be an array")?
        .iter()
        .map(|diagnostic| {
            diagnostic
                .as_str()
                .map(str::to_string)
                .context("Swift v2 runner diagnostics must be strings")
        })
        .collect::<Result<Vec<_>>>()?;
    let witness_checkpoints = value["witness_checkpoints"]
        .as_array()
        .context("Swift v2 runner witness_checkpoints must be an array")?
        .iter()
        .map(|checkpoint| {
            checkpoint
                .as_str()
                .map(str::to_string)
                .context("Swift v2 runner witness_checkpoints must be strings")
        })
        .collect::<Result<Vec<_>>>()?;
    let outcome = required_string(value, "outcome")?;
    if ![
        "reached",
        "not-reached",
        "inconclusive",
        "unsupported",
        "runner-error",
    ]
    .contains(&outcome)
    {
        bail!("Swift v2 runner returned unsupported outcome {outcome:?}");
    }
    let raw_text = required_string(value, "raw_output")?;
    let raw_output = PathBuf::from(raw_text);
    let canonical_root = fs::canonicalize(raw_dir)
        .with_context(|| format!("resolve Swift v2 raw evidence root {}", raw_dir.display()))?;
    let canonical_output = fs::canonicalize(&raw_output)
        .with_context(|| format!("resolve Swift v2 raw evidence {}", raw_output.display()))?;
    if raw_output.is_absolute()
        || raw_output
            .components()
            .any(|component| matches!(component, Component::ParentDir | Component::CurDir))
        || raw_output.to_string_lossy() != raw_text
        || !raw_output.starts_with(raw_dir)
        || raw_output == raw_dir.join(RUN_METADATA)
        || !raw_output.is_file()
        || !canonical_output.starts_with(&canonical_root)
    {
        bail!(
            "Swift v2 runner raw_output must be an existing path below {}: {}",
            raw_dir.display(),
            raw_output.display()
        );
    }
    reject_symlink_components(&raw_output, "Swift v2 raw evidence")?;
    let peak_memory_mb = match &value["peak_memory_mb"] {
        Value::Null => Value::Null,
        Value::Number(number) if number.as_u64().is_some_and(|value| value > 0) => {
            Value::Number(number.clone())
        }
        _ => bail!("Swift v2 runner peak_memory_mb must be null or a positive integer"),
    };
    if raw_output.file_name().and_then(|name| name.to_str()) == Some("execution.json") {
        let execution: Value = serde_json::from_str(&fs::read_to_string(&raw_output)?)
            .with_context(|| {
                format!("parse Swift v2 execution evidence {}", raw_output.display())
            })?;
        let execution_outcome = required_string(&execution, "outcome")?;
        if execution_outcome != outcome {
            bail!(
                "Swift v2 runner outcome {outcome:?} disagrees with execution evidence {execution_outcome:?} at {}",
                raw_output.display()
            );
        }
    }
    Ok(RunnerResult {
        model_profile: required_string(value, "model_profile")?.to_string(),
        score_tier: required_string(value, "score_tier")?.to_string(),
        outcome: outcome.to_string(),
        diagnostics,
        duration_ms: required_u64(value, "duration_ms")?,
        peak_memory_mb,
        witness_checkpoints,
        raw_output,
    })
}

fn reject_symlink_components(path: &Path, label: &str) -> Result<()> {
    let mut current = PathBuf::new();
    for component in path.components() {
        if let Component::Normal(name) = component {
            current.push(name);
            if fs::symlink_metadata(&current)
                .with_context(|| format!("inspect {label} path component {}", current.display()))?
                .file_type()
                .is_symlink()
            {
                bail!("{label} path contains a symlink: {}", current.display());
            }
        }
    }
    Ok(())
}

fn publish_report(
    tool: SwiftV2Tool,
    report_path: &Path,
    cases: &LoadedCases,
    metadata: &RunMetadata,
    configuration: &str,
) -> Result<()> {
    let expected_profile = if report_path == tool.native_report() {
        ("tool-native", "modeling")
    } else {
        ("benchmark-controlled", "language-extension")
    };
    let mut results = Vec::with_capacity(cases.len());
    for (_, case) in cases {
        let id = case["id"].as_str().context("Swift v2 case id")?;
        let record = metadata
            .results
            .get(id)
            .with_context(|| format!("Swift v2 runner omitted {id}"))?;
        if (record.model_profile.as_str(), record.score_tier.as_str()) != expected_profile {
            bail!(
                "Swift v2 report {} would mix profile/tier for {id}",
                report_path.display()
            );
        }
        if record.model_profile != case["model_profile"] || record.score_tier != case["score_tier"]
        {
            bail!("Swift v2 runner metadata disagrees with case schema for {id}");
        }
        if (expected_profile.0 == "tool-native" && record.outcome != "unsupported")
            || (expected_profile.0 == "benchmark-controlled" && record.outcome == "unsupported")
        {
            bail!("Swift v2 outcome contradicts the committed A40 partition for {id}");
        }
        let mut result = normalized_result(
            case,
            id,
            &record.outcome,
            record.diagnostics.clone(),
            Duration::from_millis(record.duration_ms),
            &record.raw_output,
        );
        result["peak_memory_mb"] = record.peak_memory_mb.clone();
        result["witness_checkpoints"] = Value::Array(
            record
                .witness_checkpoints
                .iter()
                .cloned()
                .map(Value::String)
                .collect(),
        );
        results.push(result);
    }
    let report = normalized_report(
        tool.key(),
        &metadata.identity,
        configuration,
        &metadata.fixture_revision,
        metadata.started_at_unix_seconds,
        results,
    )?;
    write_and_validate_report(report_path, &report)?;
    Ok(())
}

fn required_string<'a>(value: &'a Value, field: &str) -> Result<&'a str> {
    value[field]
        .as_str()
        .filter(|value| !value.is_empty())
        .with_context(|| format!("Swift v2 runner metadata lacks non-empty {field}"))
}

fn required_u64(value: &Value, field: &str) -> Result<u64> {
    value[field]
        .as_u64()
        .with_context(|| format!("Swift v2 runner metadata lacks non-negative integer {field}"))
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn report_paths_keep_profiles_disjoint() {
        assert_ne!(
            SwiftV2Tool::Codeql.native_report(),
            SwiftV2Tool::Codeql.result_report()
        );
        assert_ne!(
            SwiftV2Tool::Joern.native_report(),
            SwiftV2Tool::Joern.result_report()
        );
    }

    #[test]
    fn python_and_rust_hash_the_actual_configuration_identically() {
        let output = Command::new("python3")
            .args(["-c", "import sys,importlib.util;sys.path.insert(0,'scripts');s=importlib.util.spec_from_file_location('v','scripts/run-swift-v2-additions.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print(m.configuration_hash(m.configuration_paths('codeql')));print(m.configuration_hash(m.configuration_paths('joern')))"])
            .output().unwrap();
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        let actual = String::from_utf8(output.stdout).unwrap();
        let expected = [SwiftV2Tool::Codeql, SwiftV2Tool::Joern]
            .map(|tool| hash_paths(&configuration_paths(tool).unwrap()).unwrap());
        assert_eq!(
            actual.lines().collect::<Vec<_>>(),
            expected.iter().map(String::as_str).collect::<Vec<_>>()
        );
    }

    #[test]
    fn configuration_hash_binds_file_contents_not_only_paths() {
        let root = std::env::temp_dir().join(format!("dfb-v2-hash-{}", std::process::id()));
        fs::create_dir(&root).unwrap();
        let path = root.join("configuration.json");
        let paths = BTreeSet::from([path.clone()]);
        fs::write(&path, b"first").unwrap();
        let before = hash_paths(&paths).unwrap();
        fs::write(&path, b"second").unwrap();
        assert_ne!(before, hash_paths(&paths).unwrap());
        fs::remove_dir_all(root).unwrap();
    }
}
