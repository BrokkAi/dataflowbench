//! The normalized report: one result per selected case, the report envelope
//! every adapter writes, and the configuration-hash derivation that binds a
//! committed report to the adapter configuration it was produced under.
//!
//! `current_configuration_paths` is the single place that maps a report path
//! to the committed configuration it hashes. Its path set is what
//! `configuration_hash_state` compares a stamped hash against, so the set and
//! the order it is built in are part of the published contract.

use crate::adapters::bifrost::{BifrostRun, bifrost_policy_paths};
use crate::adapters::codeql::{
    CFamilyKernel, EcmaKernel, codeql_c_family_configuration_paths,
    codeql_csharp_configuration_paths, codeql_ecma_kernel_configuration_paths,
    codeql_go_configuration_paths, codeql_java_kernel_configuration_paths,
    codeql_kotlin_configuration_paths, codeql_python_kernel_configuration_paths,
    codeql_ruby_configuration_paths, codeql_rust_configuration_paths,
    codeql_swift_configuration_paths, codeql_v092_configuration_paths,
};
use crate::adapters::flowdroid::flowdroid_template_paths;
use crate::adapters::infer::infer_config_paths;
use crate::adapters::joern::{JOERN_KERNEL_SCRIPT, joern_swift_configuration_paths};
use crate::adapters::opentaint::opentaint_rule_paths;
use crate::adapters::pysa::pysa_configuration_paths;
use crate::adapters::semgrep::semgrep_rule_paths;
use crate::adapters::swift_v2::{SwiftV2Tool, configuration_paths as swift_v2_configuration_paths};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::{LoadedCases, all_case_paths, schema, validate_value};
use crate::freeze::required_string;
use crate::modeling::modeling_configuration_paths;
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf};

// Report sweeps validate all retained populations, independently of the active
// execution population. A Swift run must still derive historical Java policies.
fn cached_report_cases(scan: &mut Option<LoadedCases>) -> Result<&LoadedCases> {
    if scan.is_none() {
        *scan = Some(
            all_case_paths()
                .into_iter()
                .map(|path| {
                    let case = serde_json::from_str(&fs::read_to_string(&path)?)?;
                    Ok((path, case))
                })
                .collect::<Result<_>>()?,
        );
    }
    Ok(scan.as_ref().expect("filled above"))
}

pub(crate) const ADAPTER_VERSION: &str = env!("CARGO_PKG_VERSION");
pub(crate) fn validate_reports() -> Result<()> {
    validate_reports_in(Path::new("."), None)
}

/// Validate every retained report under `<root>/reports`.
///
/// When `own_report` is set, retained-raw-evidence existence checks are
/// limited to that report; the others are still schema-validated. Kernel
/// runners pass their own report here because a concurrently running kernel
/// removes and rewrites files under its own `reports/raw/<slice>/` directory
/// mid-run, so existence checks against another runner's evidence race and
/// fail spuriously.
pub(crate) fn validate_reports_in(root: &Path, own_report: Option<&Path>) -> Result<()> {
    let compiled = schema("schemas/result.schema.json")?;
    let own = own_report
        .map(fs::canonicalize)
        .transpose()
        .context("resolve the runner's own report")?;
    let mut paths: Vec<_> = fs::read_dir(root.join("reports"))
        .into_iter()
        .flatten()
        .filter_map(Result::ok)
        .map(|entry| entry.path())
        .filter(|path| path.is_file() && path.extension().is_some_and(|ext| ext == "json"))
        .collect();
    paths.sort();
    // Configuration-hash drift is derived from repository-relative paths, so
    // it is only checked when validating the working repository itself — the
    // one place every kernel runner and the CLI already stand. Isolated
    // fixture roots validate schemas and evidence exactly as before.
    let check_configuration = configuration_drift_checkable(root);
    let mut case_scan = None;
    let mut drifted = Vec::new();
    let mut checked = 0usize;
    let mut known_stale = 0usize;
    let mut validated = 0usize;
    for path in &paths {
        let report: Value = serde_json::from_str(&fs::read_to_string(path)?)?;
        // Freeze manifests live beside normalized reports but follow their
        // own contract; validate-freeze owns them.
        if report.get("benchmark").is_some() && report.get("claim").is_some() {
            continue;
        }
        validated += 1;
        validate_value(&compiled, &report, path)?;
        let check_raw = match &own {
            None => true,
            Some(own) => fs::canonicalize(path).is_ok_and(|path| &path == own),
        };
        if check_raw {
            validate_retained_raw(&report, path, root)?;
        }
        if check_configuration && let Some(stem) = path.file_stem().and_then(|stem| stem.to_str()) {
            let relative = path.to_string_lossy().replace('\\', "/");
            let stamped = required_string(&report, "configuration_hash", &relative)?;
            let tool_version = required_string(&report, "tool_version", &relative)?;
            match configuration_hash_state_for_report(
                stem,
                tool_version,
                required_string(&report, "adapter_version", &relative)?,
                stamped,
                &mut case_scan,
            )? {
                ConfigurationHashState::NotDerivable => {}
                ConfigurationHashState::Current => {
                    checked += 1;
                    if let Some(issue) = known_stale_issue(stem) {
                        println!(
                            "warning: {stem}: configuration hash is current again; remove it from KNOWN_STALE_CONFIGURATIONS (issue {issue})"
                        );
                    }
                }
                ConfigurationHashState::Drifted { current } => {
                    checked += 1;
                    if let Some(issue) = known_stale_issue(stem) {
                        known_stale += 1;
                        println!(
                            "warning: {stem}: outcomes predate the current adapter configuration (stamped {stamped}, current {current}); the owed re-run is tracked by issue {issue}"
                        );
                    } else {
                        drifted.push(format!(
                            "{relative}: stamped configuration hash {stamped} does not match the current adapter configuration ({current}); re-run the adapter, or record the debt in KNOWN_STALE_CONFIGURATIONS with its tracking issue"
                        ));
                    }
                }
            }
        }
    }
    if !drifted.is_empty() {
        bail!(
            "committed reports drifted from the current adapter configuration:\n{}",
            drifted.join("\n")
        );
    }
    println!("validated {validated} reports");
    if check_configuration {
        println!(
            "checked {checked} configuration hashes against the working tree ({known_stale} known-stale)"
        );
    }
    Ok(())
}

/// Populations whose committed outcomes are known to predate the current
/// adapter configuration. Each entry downgrades that report's hash mismatch
/// from an error to a warning so a recorded debt stays visible without
/// failing every validation run; the pull request that lands a population's
/// re-run removes its entry (a test fails once an entry stops drifting), and
/// every entry cites the issue tracking its owed re-run. A mismatch on any
/// report *not* listed here fails validation outright.
pub(crate) const KNOWN_STALE_CONFIGURATIONS: [(&str, &str); 1] = [
    // The Scala kernel gained scala-library dependency evidence for the v0.9.2
    // refresh; its group re-runs under a fresh attempt namespace.
    ("bifrost-scala-kernel", "#297"),
];

/// The issue tracking `stem`'s owed re-run, when its drift is a recorded debt.
pub(crate) fn known_stale_issue(stem: &str) -> Option<&'static str> {
    KNOWN_STALE_CONFIGURATIONS
        .iter()
        .find(|(known, _)| *known == stem)
        .map(|(_, issue)| *issue)
}

/// Whether `root` is the repository the current process is standing in.
/// Configuration-path derivation reuses the same repository-relative path
/// helpers every kernel runner uses, so the comparison is only meaningful
/// from the repository root itself.
pub(crate) fn configuration_drift_checkable(root: &Path) -> bool {
    fs::canonicalize(root)
        .and_then(|root| fs::canonicalize(".").map(|cwd| root == cwd))
        .unwrap_or(false)
}

/// One report's stamped configuration hash compared against the hash of the
/// same population's configuration files as they stand in the repository now.
#[derive(Debug, PartialEq, Eq)]
pub(crate) enum ConfigurationHashState {
    /// The population's configuration paths are not derivable from the
    /// repository alone (tool-native activations bind the witnessed binary
    /// identity), or the stem names no population this repository produces.
    NotDerivable,
    /// The stamped hash matches the current configuration.
    Current,
    /// The configuration changed after the report was produced: its outcomes
    /// predate the current adapter configuration.
    Drifted { current: String },
}

pub(crate) fn configuration_hash_state(
    stem: &str,
    stamped: &str,
    case_scan: &mut Option<LoadedCases>,
) -> Result<ConfigurationHashState> {
    let Some(paths) = current_configuration_paths(stem, case_scan)? else {
        return Ok(ConfigurationHashState::NotDerivable);
    };
    let current = hash_paths(&paths)?;
    if current == stamped {
        Ok(ConfigurationHashState::Current)
    } else {
        Ok(ConfigurationHashState::Drifted { current })
    }
}

/// Compare a retained report against the configuration for the exact analyzer
/// version it records. Historical CodeQL 2.27.0 and 2.27.1 reports keep their
/// original configuration paths; the prospective 2.27.2 profile hashes
/// versioned configuration copies. Common Swift reports from other historical
/// versions remain `NotDerivable` when no version-specific closure is known.
pub(crate) fn configuration_hash_state_for_report(
    stem: &str,
    tool_version: &str,
    adapter_version: &str,
    stamped: &str,
    case_scan: &mut Option<LoadedCases>,
) -> Result<ConfigurationHashState> {
    if is_codeql_swift_normal_stem(stem) {
        let paths = match (tool_version, adapter_version) {
            ("2.27.0" | "2.27.1", _) => declared_configuration_paths(stem, case_scan)?,
            (crate::adapters::pins::CODEQL_VERSION, "swift-normal-v092") => {
                Some(swift_v092_configuration_paths("codeql")?)
            }
            (crate::adapters::pins::CODEQL_VERSION, adapter) => bail!(
                "CodeQL Swift 2.27.2 report {stem} has unrecognized adapter version {adapter:?}"
            ),
            // Historical common-Swift plans can bind run-specific runtime
            // trees outside the repository. Do not borrow another version's
            // paths or reject a valid freeze when that closure is unknown.
            _ => None,
        };
        return compare_configuration_paths(paths, stamped);
    }
    if is_joern_swift_normal_stem(stem) {
        let paths = match (tool_version, adapter_version) {
            ("4.0.628", _) => declared_configuration_paths(stem, case_scan)?,
            (crate::adapters::pins::JOERN_VERSION, "joern-normal-v092") => {
                Some(swift_v092_configuration_paths("joern")?)
            }
            (crate::adapters::pins::JOERN_VERSION, adapter) => bail!(
                "Joern Swift 4.0.660 report {stem} has unrecognized adapter version {adapter:?}"
            ),
            _ => None,
        };
        return compare_configuration_paths(paths, stamped);
    }
    if stem.starts_with("codeql-") {
        let paths = match tool_version {
            "2.27.0" | "2.27.1" => declared_configuration_paths(stem, case_scan)?,
            crate::adapters::pins::CODEQL_VERSION => current_configuration_paths(stem, case_scan)?,
            other => {
                let historical = declared_configuration_paths(stem, case_scan)?;
                if historical.is_some() {
                    bail!(
                        "cannot derive CodeQL configuration paths for report {stem} with unrecognized tool version {other:?}"
                    );
                }
                None
            }
        };
        return compare_configuration_paths(paths, stamped);
    }
    configuration_hash_state(stem, stamped, case_scan)
}

fn compare_configuration_paths(
    paths: Option<BTreeSet<PathBuf>>,
    stamped: &str,
) -> Result<ConfigurationHashState> {
    let Some(paths) = paths else {
        return Ok(ConfigurationHashState::NotDerivable);
    };
    let current = hash_paths(&paths)?;
    if current == stamped {
        Ok(ConfigurationHashState::Current)
    } else {
        Ok(ConfigurationHashState::Drifted { current })
    }
}

fn is_codeql_swift_normal_stem(stem: &str) -> bool {
    [
        "codeql-swift-kernel",
        "codeql-swift-core",
        "codeql-swift-modeling",
        "codeql-swift-calibration",
        "codeql-swift-native",
        "codeql-swift-language-extension",
    ]
    .contains(&stem)
}

fn is_joern_swift_normal_stem(stem: &str) -> bool {
    [
        "joern-swift-kernel",
        "joern-swift-core",
        "joern-swift-modeling",
        "joern-swift-calibration",
        "joern-swift-native",
        "joern-swift-language-extension",
    ]
    .contains(&stem)
}

/// Read the exact v0.9.2 Swift execution plan's repository-local configuration
/// closure. Qualification descriptors (`plan.json`) are intentionally
/// ineligible; only the later execution plan with a recognized schema and
/// adapter identity can authorize hash derivation.
fn swift_v092_configuration_paths(engine: &str) -> Result<BTreeSet<PathBuf>> {
    let (relative, schema, version, adapter, key) = match engine {
        "codeql" => (
            "adapters/codeql/swift-common-v2/plan-v092-01/execution-plan.json",
            "swift-common-execution-plan/v092",
            crate::adapters::pins::CODEQL_VERSION,
            "swift-normal-v092",
            "patched-codeql",
        ),
        "joern" => (
            "adapters/joern/swift-common-v2/plan-v092-01/execution-plan.json",
            "joern-common-execution-plan/v092",
            crate::adapters::pins::JOERN_VERSION,
            "joern-normal-v092",
            "joern-current108",
        ),
        other => bail!("unknown Swift engine {other:?}"),
    };
    let plan_path = Path::new(relative);
    let plan: Value = serde_json::from_slice(
        &fs::read(plan_path)
            .with_context(|| format!("read the v0.9.2 Swift execution plan {relative}"))?,
    )
    .with_context(|| format!("parse the v0.9.2 Swift execution plan {relative}"))?;
    if plan["schema"] != schema
        || plan["profile"] != "v0.9.2"
        || plan["identity"]["tool_version"] != version
        || plan["identity"]["adapter_version"] != adapter
    {
        bail!(
            "v0.9.2 Swift execution plan has an unknown or mismatched schema/identity: {relative}"
        );
    }
    let references = plan["configurations"][key]
        .as_array()
        .with_context(|| format!("v0.9.2 Swift plan lacks configuration {key:?}"))?;
    let mut paths = BTreeSet::new();
    for reference in references {
        if reference.as_object().is_none_or(|object| {
            object.len() != 2 || !object.contains_key("path") || !object.contains_key("sha256")
        }) {
            bail!("v0.9.2 Swift configuration references must bind exactly path and sha256");
        }
        let path = required_string(reference, "path", "v0.9.2 Swift configuration")?;
        let relative_path = Path::new(path);
        if relative_path.is_absolute()
            || relative_path
                .components()
                .any(|part| part.as_os_str() == "..")
        {
            bail!("v0.9.2 Swift configuration path escapes the repository: {path}");
        }
        let expected = required_string(reference, "sha256", "v0.9.2 Swift configuration")?;
        let actual = format!(
            "{:x}",
            Sha256::digest(
                fs::read(relative_path)
                    .with_context(|| { format!("read v0.9.2 Swift configuration input {path}") })?
            )
        );
        if actual != expected {
            bail!("v0.9.2 Swift configuration input changed: {path}");
        }
        if !paths.insert(relative_path.to_path_buf()) {
            bail!("v0.9.2 Swift configuration path is duplicated: {path}");
        }
    }
    if paths.is_empty() {
        bail!("v0.9.2 Swift execution plan has an empty configuration closure");
    }
    Ok(paths)
}

/// The repository's *current* configuration-path set for the population a
/// normalized report's file stem names — the same set that population's
/// runner would hash into `configuration_hash` if it ran now — or `None`
/// where the hash is not derivable from the repository alone. Tool-native
/// reports return `None`: `native_configuration_hash` binds the witnessed
/// binary identity, which no repository file carries. Unknown stems (foreign
/// fixtures, future adapters) also return `None` rather than guessing.
///
/// Paths are repository-relative, exactly as the runners record them; callers
/// must stand at the repository root ([`configuration_drift_checkable`]).
pub(crate) fn current_configuration_paths(
    stem: &str,
    case_scan: &mut Option<LoadedCases>,
) -> Result<Option<BTreeSet<PathBuf>>> {
    let Some(paths) = declared_configuration_paths(stem, case_scan)? else {
        return Ok(None);
    };
    if stem.starts_with("codeql-") && !stem.contains("swift") {
        return Ok(Some(codeql_v092_configuration_paths(&paths)));
    }
    Ok(Some(paths))
}

/// Configuration paths spelled by the original adapter declarations. These
/// remain the source of the frozen CodeQL 2.27.0 profile while
/// `current_configuration_paths` maps new non-Swift CodeQL runs to their
/// prospective versioned copies.
fn declared_configuration_paths(
    stem: &str,
    case_scan: &mut Option<LoadedCases>,
) -> Result<Option<BTreeSet<PathBuf>>> {
    if [
        "codeql-swift-kernel",
        "codeql-swift-modeling",
        "codeql-swift-calibration",
    ]
    .contains(&stem)
    {
        return Ok(Some(codeql_swift_configuration_paths()));
    }
    if [
        "joern-swift-kernel",
        "joern-swift-modeling",
        "joern-swift-calibration",
    ]
    .contains(&stem)
    {
        return Ok(Some(joern_swift_configuration_paths()));
    }
    if ["codeql-swift-v2-native", "codeql-swift-v2-result"].contains(&stem) {
        return Ok(Some(swift_v2_configuration_paths(SwiftV2Tool::Codeql)?));
    }
    if ["joern-swift-v2-native", "joern-swift-v2-result"].contains(&stem) {
        return Ok(Some(swift_v2_configuration_paths(SwiftV2Tool::Joern)?));
    }
    if stem == "bifrost-smoke" {
        return Ok(Some(bifrost_policy_paths(
            BifrostRun::Smoke,
            cached_report_cases(case_scan)?,
        )?));
    }
    let Some((tool, rest)) = stem.split_once('-') else {
        return Ok(None);
    };
    let Some((language, population)) = rest.rsplit_once('-') else {
        return Ok(None);
    };
    if population == "modeling" {
        let (Some(modeling_tool), Some(modeling_language)) = (
            ModelingTool::ALL
                .iter()
                .copied()
                .find(|candidate| candidate.key() == tool),
            ModelingLanguage::from_key(language),
        ) else {
            return Ok(None);
        };
        return modeling_configuration_paths(modeling_tool, modeling_language);
    }
    if population != "kernel" {
        return Ok(None);
    }
    Ok(match tool {
        "bifrost" => {
            let run = match language {
                "java" => BifrostRun::JavaKernel,
                "javascript" => BifrostRun::JavascriptKernel,
                "python" => BifrostRun::PythonKernel,
                "kotlin" => BifrostRun::KotlinKernel,
                "scala" => BifrostRun::ScalaKernel,
                "typescript" => BifrostRun::TypescriptKernel,
                "csharp" => BifrostRun::CsharpKernel,
                "go" => BifrostRun::GoKernel,
                "c" => BifrostRun::CKernel,
                "cpp" => BifrostRun::CppKernel,
                "rust" => BifrostRun::RustKernel,
                "ruby" => BifrostRun::RubyKernel,
                "php" => BifrostRun::PhpKernel,
                _ => return Ok(None),
            };
            Some(bifrost_policy_paths(run, cached_report_cases(case_scan)?)?)
        }
        "codeql" => match language {
            "java" => Some(codeql_java_kernel_configuration_paths(
                cached_report_cases(case_scan)?,
            )?),
            "javascript" => Some(codeql_ecma_kernel_configuration_paths(
                EcmaKernel::JavaScript,
                cached_report_cases(case_scan)?,
            )),
            "typescript" => Some(codeql_ecma_kernel_configuration_paths(
                EcmaKernel::TypeScript,
                cached_report_cases(case_scan)?,
            )),
            "python" => Some(codeql_python_kernel_configuration_paths(
                cached_report_cases(case_scan)?,
            )?),
            "kotlin" => Some(codeql_kotlin_configuration_paths()),
            "csharp" => Some(codeql_csharp_configuration_paths()),
            "go" => Some(codeql_go_configuration_paths()),
            "c" => Some(codeql_c_family_configuration_paths(CFamilyKernel::C)),
            "cpp" => Some(codeql_c_family_configuration_paths(CFamilyKernel::Cpp)),
            "rust" => Some(codeql_rust_configuration_paths()),
            "ruby" => Some(codeql_ruby_configuration_paths()),
            "swift" => Some(codeql_swift_configuration_paths()),
            _ => None,
        },
        "joern" => Some(BTreeSet::from([PathBuf::from(JOERN_KERNEL_SCRIPT)])),
        "semgrep" => Some(semgrep_rule_paths()?),
        "opentaint" => Some(opentaint_rule_paths()),
        "infer" => Some(infer_config_paths()),
        "flowdroid" => Some(flowdroid_template_paths()),
        "pysa" => Some(pysa_configuration_paths()),
        _ => None,
    })
}

/// Every `raw_output` a report retains must exist under `root`.
pub(crate) fn validate_retained_raw(report: &Value, path: &Path, root: &Path) -> Result<()> {
    for result in report["results"].as_array().expect("schema validated") {
        let raw = result["raw_output"].as_str().expect("schema validated");
        if !root.join(raw).is_file() {
            bail!("{}: retained raw output {raw:?} is absent", path.display());
        }
    }
    Ok(())
}

/// Publish a runner's report at the end of a run, then sweep the report
/// directory.
///
/// The report is validated against the result schema, and its retained raw
/// evidence confirmed on disk, before anything is written: a runner never
/// publishes a report it did not validate. The report then lands through a
/// same-directory temp file and an atomic rename so a concurrent runner's
/// end-of-run sweep can never parse a half-written report. The closing sweep
/// schema-checks every retained report but scopes raw-evidence checks to this
/// report only, because concurrent runners rewrite their own
/// `reports/raw/<slice>/` evidence mid-run.
pub(crate) fn write_and_validate_report(report_path: &Path, report: &Value) -> Result<()> {
    write_and_validate_report_in(Path::new("."), report_path, report)
}

pub(crate) fn write_and_validate_report_in(
    root: &Path,
    report_path: &Path,
    report: &Value,
) -> Result<()> {
    let report_path = root.join(report_path);
    let compiled = schema("schemas/result.schema.json")?;
    validate_value(&compiled, report, &report_path)?;
    validate_retained_raw(report, &report_path, root)?;
    let staged = report_path.with_extension("json.tmp");
    fs::write(&staged, serde_json::to_string_pretty(report)? + "\n")
        .with_context(|| format!("stage report {}", staged.display()))?;
    fs::rename(&staged, &report_path)
        .with_context(|| format!("publish report {}", report_path.display()))?;
    validate_reports_in(root, Some(&report_path))
}

/// Shape one entry of `schemas/result.schema.json`. This is pure result-schema
/// serialization shared by every anchored adapter; the tool-specific decisions
/// are all made before the outcome reaches it.
pub(crate) fn normalized_result(
    case: &Value,
    id: &str,
    outcome: &str,
    diagnostics: Vec<String>,
    duration: std::time::Duration,
    raw_path: &Path,
) -> Value {
    json!({
        "case_id": id,
        "outcome": outcome,
        "source_anchors": case["source_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "sink_anchors": case["sink_anchors"].as_array().unwrap().iter().map(|v| v["marker"].clone()).collect::<Vec<_>>(),
        "witness_checkpoints": [],
        "diagnostics": diagnostics,
        "duration_ms": duration.as_millis() as u64,
        "peak_memory_mb": Value::Null,
        "raw_output": raw_path.to_string_lossy()
    })
}

pub(crate) fn hash_paths(paths: &BTreeSet<PathBuf>) -> Result<String> {
    let mut hasher = Sha256::new();
    for path in paths {
        hasher.update(path.to_string_lossy().as_bytes());
        hasher.update(fs::read(path).with_context(|| format!("read {}", path.display()))?);
    }
    Ok(format!("{:x}", hasher.finalize()))
}
