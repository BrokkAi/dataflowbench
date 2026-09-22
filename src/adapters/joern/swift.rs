//! The compiler-backed Swift Joern population.
//!
//! The Python recorder owns Swift compilation, native declaration resolution,
//! model/partition decisions, and the retained graph. This module owns the
//! run-level contract: activation ordering, immutable configuration binding,
//! tier selection, recorder-state validation, phase-budget normalization, and
//! report publication.

use crate::adapters::ToolIdentity;
use crate::adapters::normalized_report;
use crate::cases::{
    LoadedCases, case_paths, fixture_revision, validate_cases, validate_kernel_population_with,
};
use crate::modeling::SWIFT_MODELING_TEMPLATE_IDS;
use crate::report::{hash_paths, normalized_result, write_and_validate_report};
use crate::runtime::{now_seconds, write_case_phase_timings, write_run_environment};
use crate::templates::{SWIFT_CALIBRATION_TEMPLATE_IDS, expected_core_templates};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::{Duration, Instant};

const CASE_SCRIPT: &str = "scripts/run-joern-swift-case.py";
const VERIFY_SCRIPT: &str = "scripts/verify-joern-swift-activation.py";
const SWIFT_HELPER: &str = "scripts/joern_swift.py";
const QUERY: &str = "adapters/joern/swift/query.sc";
const ACTIVATION: &str = "adapters/joern/swift/activation.json";
const PARTITION: &str = "adapters/joern/swift/partition.json";
const MODELS: &str = "adapters/joern/swift/models.json";
const ADAPTER: &str = "src/adapters/joern/swift.rs";

pub(crate) const JOERN_SWIFT_KERNEL_REPORT: &str = "reports/joern-swift-kernel.json";
pub(crate) const JOERN_SWIFT_MODELING_REPORT: &str = "reports/joern-swift-modeling.json";
pub(crate) const JOERN_SWIFT_CALIBRATION_REPORT: &str = "reports/joern-swift-calibration.json";
pub(crate) const JOERN_SWIFT_KERNEL_RAW_DIR: &str = "reports/raw/joern-swift-kernel";
pub(crate) const JOERN_SWIFT_MODELING_RAW_DIR: &str = "reports/raw/joern-swift-modeling";
pub(crate) const JOERN_SWIFT_CALIBRATION_RAW_DIR: &str = "reports/raw/joern-swift-calibration";

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum SwiftTier {
    Core,
    Modeling,
    Calibration,
}

impl SwiftTier {
    fn parse(value: &str) -> Result<Self> {
        match value {
            "core" => Ok(Self::Core),
            "modeling" => Ok(Self::Modeling),
            "calibration" => Ok(Self::Calibration),
            other => {
                bail!("unknown Joern Swift tier {other:?}; expected core, modeling, or calibration")
            }
        }
    }

    fn key(self) -> &'static str {
        match self {
            Self::Core => "core",
            Self::Modeling => "modeling",
            Self::Calibration => "calibration",
        }
    }

    fn report(self) -> &'static str {
        match self {
            Self::Core => JOERN_SWIFT_KERNEL_REPORT,
            Self::Modeling => JOERN_SWIFT_MODELING_REPORT,
            Self::Calibration => JOERN_SWIFT_CALIBRATION_REPORT,
        }
    }

    fn raw_dir(self) -> &'static str {
        match self {
            Self::Core => JOERN_SWIFT_KERNEL_RAW_DIR,
            Self::Modeling => JOERN_SWIFT_MODELING_RAW_DIR,
            Self::Calibration => JOERN_SWIFT_CALIBRATION_RAW_DIR,
        }
    }

    fn templates(self) -> Vec<&'static str> {
        match self {
            Self::Core => expected_core_templates("swift"),
            Self::Modeling => SWIFT_MODELING_TEMPLATE_IDS.to_vec(),
            Self::Calibration => SWIFT_CALIBRATION_TEMPLATE_IDS.to_vec(),
        }
    }
}

/// Every file that defines the Swift Joern run contract is hash-bound. The
/// activation certificate and partition are inputs just like the query and
/// Python recorder; a report cannot silently outlive any of them.
pub(crate) fn joern_swift_configuration_paths() -> BTreeSet<PathBuf> {
    [
        CASE_SCRIPT,
        VERIFY_SCRIPT,
        SWIFT_HELPER,
        QUERY,
        ACTIVATION,
        PARTITION,
        MODELS,
        ADAPTER,
    ]
    .into_iter()
    .map(PathBuf::from)
    .collect()
}

fn select_swift_cases(tier: SwiftTier) -> Result<LoadedCases> {
    let expected = tier.templates();
    let selected: LoadedCases = case_paths()
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
                && case["score_tier"] == tier.key()
                && case["model_profile"] == "benchmark-controlled"
        })
        .collect();
    validate_kernel_population_with(
        &selected,
        &format!("Joern Swift {} population", tier.key()),
        &expected,
    )?;
    Ok(selected)
}

fn verify_committed_configuration() -> Result<()> {
    let paths = joern_swift_configuration_paths();
    if !Command::new("git")
        .args(["ls-files", "--error-unmatch"])
        .args(&paths)
        .output()?
        .status
        .success()
        || !Command::new("git")
            .args(["diff", "--quiet", "HEAD", "--"])
            .args(&paths)
            .status()?
            .success()
    {
        bail!(
            "Joern Swift configuration and partition must be committed unchanged before execution"
        );
    }
    Ok(())
}

fn verify_partition(tier: SwiftTier, selected: &LoadedCases) -> Result<Value> {
    let partition: Value = serde_json::from_str(&fs::read_to_string(PARTITION)?)?;
    if partition["status"] != "resolved" {
        bail!("Joern Swift partition has not been resolved before scoring");
    }
    let templates = partition["templates"]
        .as_object()
        .context("Joern Swift partition templates")?;
    for (_, case) in selected {
        let template = case["template_id"].as_str().context("Swift template id")?;
        let entry = templates
            .get(template)
            .with_context(|| format!("Swift partition lacks template {template}"))?;
        if entry["tier"].as_str() != Some(tier.key())
            || entry["profile"].as_str() != Some("benchmark-controlled")
        {
            bail!(
                "Swift partition disagrees with {} for template {template}",
                tier.key()
            );
        }
        match entry["decision"].as_str() {
            Some("execute") => {}
            Some("unsupported") => {
                if entry["reason"].as_str().is_none_or(str::is_empty) {
                    bail!("Swift unsupported partition entry lacks a reason for {template}");
                }
            }
            Some(other) => bail!("unknown Swift partition decision {other:?} for {template}"),
            None => bail!("Swift partition decision is absent for {template}"),
        }
    }
    Ok(partition)
}

fn run_activation() -> Result<()> {
    let status = Command::new("python3")
        .arg(VERIFY_SCRIPT)
        .status()
        .with_context(|| format!("run {VERIFY_SCRIPT}"))?;
    if !status.success() {
        bail!("Joern Swift activation verifier failed with status {status}");
    }
    Ok(())
}

fn joern_swift_identity(
    joern: &Path,
    java_home: &Path,
) -> Result<(ToolIdentity, std::process::Output)> {
    let output = Command::new(joern)
        .env("JAVA_HOME", java_home)
        .arg("--nocolors")
        .stdin(std::process::Stdio::null())
        .output()
        .with_context(|| format!("run {} --nocolors", joern.display()))?;
    if !output.status.success() {
        bail!(
            "{} --nocolors failed with status {}",
            joern.display(),
            output.status
        );
    }
    let banner = format!(
        "{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    let version = banner
        .lines()
        .find_map(|line| line.trim().strip_prefix("Version:").map(str::trim))
        .filter(|version| !version.is_empty())
        .context("Joern did not report a version")?
        .to_string();
    if version != "4.0.628" {
        bail!("Swift requires pinned Joern 4.0.628");
    }
    Ok((
        ToolIdentity::new(version.clone(), format!("joern-cli:{version}")),
        output,
    ))
}

#[derive(Debug)]
struct RecorderResult {
    outcome: &'static str,
    diagnostics: Vec<String>,
    total: Duration,
    raw_name: &'static str,
}

fn recorder_result(
    execution: &Value,
    case_output: &Path,
    budget_seconds: u64,
) -> Result<RecorderResult> {
    let original = execution["outcome"]
        .as_str()
        .context("Swift recorder outcome")?;
    let mut outcome = match original {
        "reached" => "reached",
        "not-reached" => "not-reached",
        "inconclusive" => "inconclusive",
        "runner-error" => "runner-error",
        "unsupported" => "unsupported",
        other => bail!("unknown Swift recorder outcome {other:?}"),
    };
    let mut diagnostics = execution["diagnostics"]
        .as_array()
        .context("Swift recorder diagnostics")?
        .iter()
        .map(|value| {
            value
                .as_str()
                .map(str::to_string)
                .context("Swift diagnostic must be a string")
        })
        .collect::<Result<Vec<_>>>()?;
    if !execution["peak_memory_mb"].is_null() {
        bail!(
            "Swift recorder peak_memory_mb must remain null: process-tree memory is not certified"
        );
    }
    let seconds = execution["phases"]["total"]
        .as_f64()
        .filter(|seconds| seconds.is_finite() && *seconds >= 0.0)
        .context("Swift recorder phases.total must be a finite non-negative number")?;
    let total = Duration::try_from_secs_f64(seconds).context("Swift recorder phase duration")?;
    let native_evidence = &execution["native_evidence"];
    let native_name = match native_evidence {
        Value::Null => None,
        Value::String(value) if value == "graph.json" => {
            if !case_output.join(value).is_file() {
                bail!("Swift recorder declares graph.json but native evidence is absent");
            }
            Some("graph.json")
        }
        Value::String(value) => bail!("unknown Swift native evidence {value:?}"),
        _ => bail!("Swift native_evidence must be graph.json or null"),
    };
    if matches!(original, "reached" | "not-reached") && native_name != Some("graph.json") {
        bail!("{original} Swift result lacks authoritative graph.json evidence");
    }
    if seconds > budget_seconds as f64 && matches!(outcome, "reached" | "not-reached") {
        outcome = "inconclusive";
        diagnostics.push(format!(
            "total Swift phase duration exceeded the case wall-clock budget: {seconds:.3}s > {budget_seconds}s"
        ));
        return Ok(RecorderResult {
            outcome,
            diagnostics,
            total,
            raw_name: "execution.json",
        });
    }
    if matches!(outcome, "reached" | "not-reached") {
        outcome = "inconclusive";
        diagnostics.push("aggregate process-tree memory compliance is not certified".into());
    }
    Ok(RecorderResult {
        outcome,
        diagnostics,
        total,
        raw_name: if matches!(outcome, "reached" | "not-reached") {
            "graph.json"
        } else {
            "execution.json"
        },
    })
}

pub(crate) fn run_joern_swift_kernel(joern: &Path, java_home: &Path, tier: &str) -> Result<()> {
    validate_cases()?;
    let tier = SwiftTier::parse(tier)?;
    let selected = select_swift_cases(tier)?;
    let _partition = verify_partition(tier, &selected)?;
    verify_committed_configuration()?;

    let report_path = Path::new(tier.report());
    let raw_dir = Path::new(tier.raw_dir());
    if report_path.exists() {
        bail!(
            "refusing to overwrite prior Swift Joern report {}",
            report_path.display()
        );
    }
    if raw_dir.exists() {
        bail!(
            "refusing to overwrite prior Swift Joern evidence {}",
            raw_dir.display()
        );
    }
    // The verifier is a run-level prerequisite. Run it before creating any
    // scored evidence destination, so an activation failure leaves no empty
    // directory that could make a later qualified retry look like overwrite.
    run_activation()?;
    fs::create_dir_all("reports/raw")?;
    fs::create_dir(raw_dir)?;

    let (identity, version_output) = joern_swift_identity(joern, java_home)?;
    fs::write(raw_dir.join("version-stdout.txt"), &version_output.stdout)?;
    fs::write(raw_dir.join("version-stderr.txt"), &version_output.stderr)?;
    fs::write(
        raw_dir.join("version-command.json"),
        serde_json::to_vec_pretty(&json!({
            "argv": [joern.to_string_lossy().to_string(), "--nocolors".to_string()], "JAVA_HOME": java_home,
            "exit_status": version_output.status.code()
        }))?,
    )?;
    write_run_environment(raw_dir, "joern", &identity)?;
    let configuration = hash_paths(&joern_swift_configuration_paths())?;
    let revision = fixture_revision()?;
    let started = now_seconds()?;
    let mut results = Vec::with_capacity(selected.len());

    for (case_path, case) in selected {
        let id = case["id"].as_str().context("Swift case id")?;
        let case_output = raw_dir.join(id);
        let start = Instant::now();
        let status = Command::new("python3")
            .arg(CASE_SCRIPT)
            .arg("--joern")
            .arg(joern)
            .arg("--java-home")
            .arg(java_home)
            .arg("--case")
            .arg(&case_path)
            .arg("--output")
            .arg(&case_output)
            .status()
            .with_context(|| format!("run {CASE_SCRIPT} for {id}"))?;
        if !status.success() {
            bail!("Swift recorder failed for {id} with status {status}");
        }
        let execution_path = case_output.join("execution.json");
        let execution: Value = serde_json::from_str(
            &fs::read_to_string(&execution_path)
                .with_context(|| format!("read {}", execution_path.display()))?,
        )?;
        let recorder = recorder_result(
            &execution,
            &case_output,
            case["execution_budget"]["wall_clock_seconds"]
                .as_u64()
                .context("Swift case wall-clock budget")?,
        )?;
        write_case_phase_timings(raw_dir, "joern", id, &[("total", recorder.total)])?;
        let raw_path = case_output.join(recorder.raw_name);
        if !raw_path.is_file() {
            bail!(
                "Swift recorder raw evidence is absent for {id}: {}",
                raw_path.display()
            );
        }
        results.push(normalized_result(
            &case,
            id,
            recorder.outcome,
            recorder.diagnostics,
            start.elapsed(),
            &raw_path,
        ));
        println!("{id}: {}", recorder.outcome);
    }

    let report = normalized_report(
        "joern",
        &identity,
        &configuration,
        &revision,
        started,
        results,
    )?;
    write_and_validate_report(report_path, &report)?;
    println!("wrote {}", report_path.display());
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    fn execution(outcome: &str, native: Value, total: f64) -> Value {
        json!({
            "outcome": outcome,
            "diagnostics": [],
            "peak_memory_mb": null,
            "phases": {"total": total},
            "native_evidence": native
        })
    }

    #[test]
    fn swift_tiers_keep_the_preregistered_denominators() {
        assert_eq!(SwiftTier::Core.templates().len(), 33);
        assert_eq!(SwiftTier::Modeling.templates().len(), 10);
        assert_eq!(SwiftTier::Calibration.templates().len(), 2);
    }

    #[test]
    fn determinate_recorder_states_require_graph_evidence() {
        let error = recorder_result(
            &execution("reached", Value::Null, 1.0),
            Path::new("/absent"),
            60,
        )
        .unwrap_err();
        assert!(error.to_string().contains("authoritative graph.json"));
        let error = recorder_result(
            &execution("not-reached", json!("other.json"), 1.0),
            Path::new("/absent"),
            60,
        )
        .unwrap_err();
        assert!(error.to_string().contains("unknown Swift native evidence"));
    }

    #[test]
    fn unknown_recorder_states_fail_closed() {
        let error = recorder_result(
            &execution("analyzed", Value::Null, 1.0),
            Path::new("/absent"),
            60,
        )
        .unwrap_err();
        assert!(error.to_string().contains("unknown Swift recorder outcome"));
    }

    #[test]
    fn total_budget_overrun_cannot_remain_determinate() {
        let root =
            std::env::temp_dir().join(format!("dataflowbench-swift-test-{}", std::process::id()));
        fs::create_dir_all(&root).unwrap();
        fs::write(root.join("graph.json"), "{}\n").unwrap();
        let result =
            recorder_result(&execution("reached", json!("graph.json"), 61.0), &root, 60).unwrap();
        assert_eq!(result.outcome, "inconclusive");
        assert_eq!(result.raw_name, "execution.json");
        assert!(
            result
                .diagnostics
                .iter()
                .any(|value| value.contains("exceeded"))
        );
        let _ = fs::remove_dir_all(root);
    }

    #[test]
    fn missing_memory_certification_cannot_remain_determinate() {
        let root =
            std::env::temp_dir().join(format!("dfb-swift-memory-test-{}", std::process::id()));
        fs::create_dir_all(&root).unwrap();
        fs::write(root.join("graph.json"), "{}\n").unwrap();
        for outcome in ["reached", "not-reached"] {
            let result =
                recorder_result(&execution(outcome, json!("graph.json"), 1.0), &root, 60).unwrap();
            assert_eq!(result.outcome, "inconclusive");
            assert!(result.diagnostics.iter().any(|d| d.contains("memory")));
        }
        fs::remove_dir_all(root).unwrap();
    }

    #[test]
    fn swift_report_and_raw_paths_are_disjoint_per_tier() {
        let reports = [
            SwiftTier::Core.report(),
            SwiftTier::Modeling.report(),
            SwiftTier::Calibration.report(),
        ]
        .into_iter()
        .collect::<BTreeSet<_>>();
        let raw = [
            SwiftTier::Core.raw_dir(),
            SwiftTier::Modeling.raw_dir(),
            SwiftTier::Calibration.raw_dir(),
        ]
        .into_iter()
        .collect::<BTreeSet<_>>();
        assert_eq!(reports.len(), 3);
        assert_eq!(raw.len(), 3);
    }
}
