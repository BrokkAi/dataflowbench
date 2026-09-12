//! Population-aware comparison of normalized report sets.
//!
//! A diff never turns population growth into a score. Assertions are joined
//! by stable case ID after explicit identity inspection; only retained rows
//! contribute transitions, and coverage outcomes remain distinct from
//! affirmative `not-reached` evidence.

use crate::cases::cached_case_scan;
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::{BTreeMap, BTreeSet},
    fs,
    path::{Path, PathBuf},
};

const OUTCOMES: [&str; 5] = [
    "reached",
    "not-reached",
    "inconclusive",
    "unsupported",
    "runner-error",
];

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub(crate) struct ReportIdentity {
    schema_version: u64,
    tool: String,
    tool_version: String,
    tool_build_identity: String,
    adapter_version: String,
    configuration_hash: String,
    fixture_revision: String,
    cold_or_warm: String,
    languages: BTreeSet<String>,
}

#[derive(Clone, Debug)]
pub(crate) struct ReportInput {
    argument: String,
    aggregate_sha256: String,
    case_count: usize,
    reports: Vec<ReportProvenance>,
}

#[derive(Clone, Debug)]
pub(crate) struct ReportProvenance {
    path: String,
    sha256: String,
    case_count: usize,
}

#[derive(Clone, Debug)]
pub(crate) struct ReportSet {
    input: ReportInput,
    reports: BTreeMap<String, (ReportIdentity, BTreeMap<String, Value>)>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct CaseContext {
    language: Option<String>,
    polarity: Option<String>,
    template_id: Option<String>,
}

#[derive(Debug)]
pub(crate) struct Comparison {
    pub(crate) baseline: ReportInput,
    pub(crate) current: ReportInput,
    pub(crate) populations_equal: bool,
    pub(crate) groups: Vec<GroupComparison>,
}

#[derive(Debug)]
pub(crate) struct GroupComparison {
    pub(crate) tool: String,
    pub(crate) cold_or_warm: String,
    pub(crate) baseline_identity: ReportIdentity,
    pub(crate) current_identity: ReportIdentity,
    pub(crate) material_identity_differences: BTreeMap<String, Value>,
    pub(crate) retained: usize,
    pub(crate) added: usize,
    pub(crate) removed: usize,
    pub(crate) retained_transitions: Vec<CaseTransition>,
    pub(crate) added_cases: Vec<PartitionedCase>,
    pub(crate) removed_cases: Vec<PartitionedCase>,
    pub(crate) outcome_partitions: OutcomePartitions,
}

#[derive(Debug)]
pub(crate) struct CaseTransition {
    pub(crate) case_id: String,
    pub(crate) before: String,
    pub(crate) after: String,
    language: Option<String>,
    pub(crate) polarity: Option<String>,
    pub(crate) template_id: Option<String>,
}

#[derive(Debug)]
pub(crate) struct PartitionedCase {
    pub(crate) case_id: String,
    pub(crate) outcome: String,
    language: Option<String>,
    polarity: Option<String>,
    template_id: Option<String>,
}

#[derive(Debug, Default)]
pub(crate) struct OutcomePartitions {
    pub(crate) positive: PolarityComparison,
    pub(crate) negative: PolarityComparison,
    pub(crate) unclassified: PolarityComparison,
}

#[derive(Debug, Default)]
pub(crate) struct PolarityComparison {
    baseline_counts: BTreeMap<String, usize>,
    current_counts: BTreeMap<String, usize>,
    pub(crate) transitions: BTreeMap<String, usize>,
}

#[derive(Clone, Copy, Debug, Default)]
pub(crate) struct CompareOptions {
    pub(crate) allow_configuration_mismatch: bool,
}

fn required_string(report: &Value, field: &str, source: &Path) -> Result<String> {
    report[field]
        .as_str()
        .map(str::to_string)
        .with_context(|| format!("{}: read normalized-report field {field}", source.display()))
}

fn is_normalized_report(report: &Value) -> bool {
    report.get("schema_version") == Some(&json!(1))
        && report.get("tool").is_some_and(Value::is_string)
        && report.get("results").is_some_and(Value::is_array)
}

fn digest(bytes: &[u8]) -> String {
    format!("{:x}", Sha256::digest(bytes))
}

pub(crate) fn case_contexts() -> Result<BTreeMap<String, CaseContext>> {
    let mut case_scan = None;
    let loaded = cached_case_scan(&mut case_scan)?;
    Ok(loaded
        .iter()
        .map(|(_, case)| {
            (
                case["id"].as_str().unwrap_or_default().to_string(),
                CaseContext {
                    language: case["language"].as_str().map(str::to_string),
                    polarity: case["polarity"].as_str().map(str::to_string),
                    template_id: case["template_id"].as_str().map(str::to_string),
                },
            )
        })
        .collect())
}

fn language_for(case_id: &str, contexts: &BTreeMap<String, CaseContext>) -> Option<String> {
    contexts
        .get(case_id)
        .and_then(|context| context.language.clone())
}

fn context_for(case_id: &str, contexts: &BTreeMap<String, CaseContext>) -> CaseContext {
    contexts.get(case_id).cloned().unwrap_or(CaseContext {
        language: None,
        polarity: None,
        template_id: None,
    })
}

fn load_one_report(path: &Path, contexts: &BTreeMap<String, CaseContext>) -> Result<ReportSet> {
    let bytes = fs::read(path).with_context(|| format!("read {}", path.display()))?;
    let report: Value = serde_json::from_slice(&bytes)
        .with_context(|| format!("parse normalized report {}", path.display()))?;
    if !is_normalized_report(&report) {
        bail!("{} is not a normalized result report", path.display());
    }
    let report_path = vec![path.to_path_buf()];
    load_report_paths(&report_path, contexts)
}

fn load_report_directory(
    root: &Path,
    contexts: &BTreeMap<String, CaseContext>,
) -> Result<ReportSet> {
    let mut paths = Vec::new();
    for entry in walkdir::WalkDir::new(root).sort_by_file_name() {
        let entry = entry.with_context(|| format!("walk {}", root.display()))?;
        let path = entry.path();
        if path.is_file()
            && path
                .extension()
                .is_some_and(|extension| extension == "json")
        {
            paths.push(path.to_path_buf());
        }
    }
    load_report_paths(&paths, contexts)
}

fn load_report_paths(
    paths: &[PathBuf],
    contexts: &BTreeMap<String, CaseContext>,
) -> Result<ReportSet> {
    let mut reports = BTreeMap::new();
    let mut provenance = Vec::new();
    let mut aggregate = Sha256::new();
    let mut case_count = 0usize;
    for path in paths {
        let bytes = fs::read(path).with_context(|| format!("read {}", path.display()))?;
        aggregate.update(&bytes);
        let report: Value = serde_json::from_slice(&bytes)
            .with_context(|| format!("parse candidate report {}", path.display()))?;
        if !is_normalized_report(&report) {
            continue;
        }
        let identity = report_identity(&report, path, contexts)?;
        let mut results = BTreeMap::new();
        for result in report["results"].as_array().expect("array checked") {
            let case_id = result["case_id"]
                .as_str()
                .with_context(|| format!("{}: read case_id", path.display()))?;
            let outcome = result["outcome"]
                .as_str()
                .with_context(|| format!("{}: read outcome for {case_id}", path.display()))?;
            if !OUTCOMES.contains(&outcome) {
                bail!(
                    "{}: {case_id} has unknown outcome {outcome:?}",
                    path.display()
                );
            }
            if results
                .insert(case_id.to_string(), result.clone())
                .is_some()
            {
                bail!("{}: duplicate case ID {case_id}", path.display());
            }
        }
        case_count += results.len();
        provenance.push(ReportProvenance {
            path: path.to_string_lossy().replace('\\', "/"),
            sha256: digest(&bytes),
            case_count: results.len(),
        });
        if reports
            .insert(report_key(&identity), (identity, results))
            .is_some()
        {
            bail!(
                "{}: two reports share tool, configuration, and execution temperature",
                path.display()
            );
        }
    }
    if reports.is_empty() {
        bail!(
            "{} contains no normalized result reports",
            paths
                .first()
                .and_then(|path| path.parent())
                .unwrap_or(Path::new("."))
                .display()
        );
    }
    provenance.sort_by(|left, right| left.path.cmp(&right.path));
    Ok(ReportSet {
        input: ReportInput {
            argument: paths
                .first()
                .map(|path| path.to_string_lossy().replace('\\', "/"))
                .unwrap_or_default(),
            aggregate_sha256: format!("{:x}", aggregate.finalize()),
            case_count,
            reports: provenance,
        },
        reports,
    })
}

pub(crate) fn load_input(
    path: &Path,
    contexts: &BTreeMap<String, CaseContext>,
) -> Result<ReportSet> {
    if path.is_file() {
        load_one_report(path, contexts)
    } else if path.is_dir() {
        load_report_directory(path, contexts)
    } else {
        bail!("report input {} is not a file or directory", path.display())
    }
}

fn report_identity(
    report: &Value,
    path: &Path,
    contexts: &BTreeMap<String, CaseContext>,
) -> Result<ReportIdentity> {
    let mut languages = BTreeSet::new();
    for result in report["results"].as_array().expect("array checked") {
        let case_id = result["case_id"]
            .as_str()
            .with_context(|| format!("{}: read case_id", path.display()))?;
        languages.insert(language_for(case_id, contexts).unwrap_or_else(|| "unknown".into()));
    }
    Ok(ReportIdentity {
        schema_version: report["schema_version"]
            .as_u64()
            .with_context(|| format!("{}: read schema_version", path.display()))?,
        tool: required_string(report, "tool", path)?,
        tool_version: required_string(report, "tool_version", path)?,
        tool_build_identity: required_string(report, "tool_build_identity", path)?,
        adapter_version: required_string(report, "adapter_version", path)?,
        configuration_hash: required_string(report, "configuration_hash", path)?,
        fixture_revision: required_string(report, "fixture_revision", path)?,
        cold_or_warm: required_string(report, "cold_or_warm", path)?,
        languages,
    })
}

fn report_key(identity: &ReportIdentity) -> String {
    format!(
        "{}\u{1}\u{1}\u{1}{}\u{1}\u{1}\u{1}{}",
        identity.tool, identity.configuration_hash, identity.cold_or_warm
    )
}

fn identity_value(name: &str, baseline: &str, current: &str) -> (String, Value) {
    (
        name.to_string(),
        json!({
            "baseline": baseline,
            "current": current,
        }),
    )
}

fn identity_differences(
    baseline: &ReportIdentity,
    current: &ReportIdentity,
) -> BTreeMap<String, Value> {
    let fields = [
        (
            "tool_version",
            &baseline.tool_version,
            &current.tool_version,
        ),
        (
            "tool_build_identity",
            &baseline.tool_build_identity,
            &current.tool_build_identity,
        ),
        (
            "adapter_version",
            &baseline.adapter_version,
            &current.adapter_version,
        ),
        (
            "configuration_hash",
            &baseline.configuration_hash,
            &current.configuration_hash,
        ),
        (
            "fixture_revision",
            &baseline.fixture_revision,
            &current.fixture_revision,
        ),
    ];
    let mut differences: BTreeMap<String, Value> = fields
        .into_iter()
        .filter(|(_, before, after)| before != after)
        .map(|(name, before, after)| identity_value(name, before, after))
        .collect();
    if baseline.languages != current.languages {
        differences.insert(
            "languages".into(),
            json!({
                "baseline": baseline.languages,
                "current": current.languages,
            }),
        );
    }
    differences
}

fn outcome_partition(
    polarity: &str,
    rows: &[CaseTransition],
    added: &[PartitionedCase],
    removed: &[PartitionedCase],
) -> PolarityComparison {
    let mut comparison = PolarityComparison::default();
    for outcome in OUTCOMES {
        comparison.baseline_counts.insert(outcome.into(), 0);
        comparison.current_counts.insert(outcome.into(), 0);
    }
    for row in rows {
        let classified = match polarity {
            "unclassified" => row.polarity.is_none(),
            expected => row.polarity.as_deref() == Some(expected),
        };
        if !classified {
            continue;
        }
        *comparison
            .baseline_counts
            .entry(row.before.clone())
            .or_default() += 1;
        *comparison
            .current_counts
            .entry(row.after.clone())
            .or_default() += 1;
        *comparison
            .transitions
            .entry(format!("{} -> {}", row.before, row.after))
            .or_default() += 1;
    }
    for case in added {
        let classified = match polarity {
            "unclassified" => case.polarity.is_none(),
            expected => case.polarity.as_deref() == Some(expected),
        };
        if !classified {
            continue;
        }
        *comparison
            .current_counts
            .entry(case.outcome.clone())
            .or_default() += 1;
    }
    for case in removed {
        let classified = match polarity {
            "unclassified" => case.polarity.is_none(),
            expected => case.polarity.as_deref() == Some(expected),
        };
        if !classified {
            continue;
        }
        *comparison
            .baseline_counts
            .entry(case.outcome.clone())
            .or_default() += 1;
    }
    comparison
}

pub(crate) fn compare_sets(
    mut baseline: ReportSet,
    mut current: ReportSet,
    contexts: &BTreeMap<String, CaseContext>,
    options: CompareOptions,
) -> Result<Comparison> {
    if baseline.reports.len() == 1 && current.reports.len() == 1 {
        baseline.reports = baseline
            .reports
            .into_iter()
            .map(|(_, group)| ("diagnostic-pair".to_string(), group))
            .collect();
        current.reports = current
            .reports
            .into_iter()
            .map(|(_, group)| ("diagnostic-pair".to_string(), group))
            .collect();
    }
    let baseline_keys: BTreeSet<_> = baseline.reports.keys().collect();
    let current_keys: BTreeSet<_> = current.reports.keys().collect();
    if baseline_keys != current_keys {
        let missing: Vec<_> = baseline_keys.difference(&current_keys).collect();
        let unexpected: Vec<_> = current_keys.difference(&baseline_keys).collect();
        bail!(
            "report-set identities do not align: missing_current={missing:?}, extra_current={unexpected:?}"
        );
    }

    let mut groups = Vec::new();
    for (key, (baseline_identity, baseline_results)) in &baseline.reports {
        let (current_identity, current_results) = &current.reports[key];
        if baseline_identity.tool != current_identity.tool
            || baseline_identity.schema_version != current_identity.schema_version
            || baseline_identity.cold_or_warm != current_identity.cold_or_warm
        {
            bail!("incomparable report identity for {key}");
        }
        let differences = identity_differences(baseline_identity, current_identity);
        if differences.contains_key("configuration_hash") && !options.allow_configuration_mismatch {
            bail!(
                "configuration mismatch for {} baseline={} current={} (pass --allow-configuration-mismatch only for an explicitly labelled diagnostic comparison)",
                baseline_identity.tool,
                baseline_identity.configuration_hash,
                current_identity.configuration_hash
            );
        }

        let mut retained = 0usize;
        let mut retained_transitions = Vec::new();
        for (case_id, before) in baseline_results {
            let Some(after) = current_results.get(case_id) else {
                continue;
            };
            retained += 1;
            if before["outcome"] != after["outcome"] {
                let context = context_for(case_id, contexts);
                retained_transitions.push(CaseTransition {
                    case_id: case_id.clone(),
                    before: before["outcome"].as_str().expect("validated").into(),
                    after: after["outcome"].as_str().expect("validated").into(),
                    language: context.language,
                    polarity: context.polarity,
                    template_id: context.template_id,
                });
            }
        }
        let added_cases: Vec<_> = current_results
            .iter()
            .filter(|(case_id, _)| !baseline_results.contains_key(*case_id))
            .map(|(case_id, result)| {
                let context = context_for(case_id, contexts);
                PartitionedCase {
                    case_id: case_id.clone(),
                    outcome: result["outcome"].as_str().expect("validated").into(),
                    language: context.language,
                    polarity: context.polarity,
                    template_id: context.template_id,
                }
            })
            .collect();
        let removed_cases: Vec<_> = baseline_results
            .iter()
            .filter(|(case_id, _)| !current_results.contains_key(*case_id))
            .map(|(case_id, result)| {
                let context = context_for(case_id, contexts);
                PartitionedCase {
                    case_id: case_id.clone(),
                    outcome: result["outcome"].as_str().expect("validated").into(),
                    language: context.language,
                    polarity: context.polarity,
                    template_id: context.template_id,
                }
            })
            .collect();

        let mut outcome_partitions = OutcomePartitions::default();
        outcome_partitions.positive = outcome_partition(
            "positive",
            &retained_transitions,
            &added_cases,
            &removed_cases,
        );
        outcome_partitions.negative = outcome_partition(
            "negative",
            &retained_transitions,
            &added_cases,
            &removed_cases,
        );
        outcome_partitions.unclassified = outcome_partition(
            "unclassified",
            &retained_transitions,
            &added_cases,
            &removed_cases,
        );
        groups.push(GroupComparison {
            tool: baseline_identity.tool.clone(),
            cold_or_warm: baseline_identity.cold_or_warm.clone(),
            baseline_identity: baseline_identity.clone(),
            current_identity: current_identity.clone(),
            material_identity_differences: differences,
            retained,
            added: added_cases.len(),
            removed: removed_cases.len(),
            retained_transitions,
            added_cases,
            removed_cases,
            outcome_partitions,
        });
    }
    groups.sort_by(|left, right| {
        (&left.tool, &left.cold_or_warm).cmp(&(&right.tool, &right.cold_or_warm))
    });

    let populations_equal = groups
        .iter()
        .all(|group| group.added == 0 && group.removed == 0);
    Ok(Comparison {
        baseline: baseline.input,
        current: current.input,
        populations_equal,
        groups,
    })
}

fn identity_json(identity: &ReportIdentity) -> Value {
    json!({
        "schema_version": identity.schema_version,
        "tool": identity.tool,
        "tool_version": identity.tool_version,
        "tool_build_identity": identity.tool_build_identity,
        "adapter_version": identity.adapter_version,
        "configuration_hash": identity.configuration_hash,
        "fixture_revision": identity.fixture_revision,
        "cold_or_warm": identity.cold_or_warm,
        "languages": identity.languages,
    })
}

fn input_json(input: &ReportInput) -> Value {
    json!({
        "argument": input.argument,
        "aggregate_sha256": input.aggregate_sha256,
        "case_count": input.case_count,
        "reports": input.reports.iter().map(|report| json!({
            "path": report.path,
            "sha256": report.sha256,
            "case_count": report.case_count,
        })).collect::<Vec<_>>(),
    })
}

fn polarity_json(polarity: &PolarityComparison) -> Value {
    json!({
        "baseline_counts": polarity.baseline_counts,
        "current_counts": polarity.current_counts,
        "transitions": polarity.transitions,
    })
}

fn partition_json(cases: &[PartitionedCase]) -> Value {
    Value::Array(
        cases
            .iter()
            .map(|case| {
                json!({
                "case_id": case.case_id,
                "outcome": case.outcome,
                "language": case.language,
                "polarity": case.polarity,
                "template_id": case.template_id,
                })
            })
            .collect::<Vec<_>>(),
    )
}

pub(crate) fn comparison_json(comparison: &Comparison) -> Value {
    json!({
        "schema_version": 1,
        "baseline": input_json(&comparison.baseline),
        "current": input_json(&comparison.current),
        "populations_equal": comparison.populations_equal,
        "pooled_score": null,
        "pooled_score_policy": "Never emitted. Counts are partitioned by identity and stable case ID.",
        "groups": comparison.groups.iter().map(|group| json!({
            "tool": group.tool,
            "cold_or_warm": group.cold_or_warm,
            "baseline_identity": identity_json(&group.baseline_identity),
            "current_identity": identity_json(&group.current_identity),
            "material_identity_differences": group.material_identity_differences,
            "assertions": {
                "retained": group.retained,
                "added": group.added,
                "removed": group.removed,
            },
            "retained_transitions": group.retained_transitions.iter().map(|row| json!({
                "case_id": row.case_id,
                "before": row.before,
                "after": row.after,
                "language": row.language,
                "polarity": row.polarity,
                "template_id": row.template_id,
            })).collect::<Vec<_>>(),
            "added_cases": partition_json(&group.added_cases),
            "removed_cases": partition_json(&group.removed_cases),
            "outcome_partitions": {
                "positive": polarity_json(&group.outcome_partitions.positive),
                "negative": polarity_json(&group.outcome_partitions.negative),
                "unclassified": polarity_json(&group.outcome_partitions.unclassified),
            },
        })).collect::<Vec<_>>(),
    })
}

fn render_human(comparison: &Comparison) -> String {
    let mut lines = vec![
        format!(
            "Report diff: baseline={} ({}) current={} ({})",
            comparison.baseline.argument,
            comparison.baseline.aggregate_sha256,
            comparison.current.argument,
            comparison.current.aggregate_sha256,
        ),
        format!("populations_equal={}", comparison.populations_equal),
        "No pooled score or percentage is emitted.".to_string(),
    ];
    for group in &comparison.groups {
        lines.push(format!(
            "{}: retained={} added={} removed={}",
            group.tool, group.retained, group.added, group.removed
        ));
        for (field, difference) in &group.material_identity_differences {
            lines.push(format!(
                "  identity {field}: baseline={} current={}",
                difference["baseline"], difference["current"]
            ));
        }
        for row in &group.retained_transitions {
            lines.push(format!(
                "  transition {}: {} -> {} ({})",
                row.case_id,
                row.before,
                row.after,
                row.polarity.as_deref().unwrap_or("unclassified")
            ));
        }
    }
    lines.join("\n")
}

pub(crate) fn compare_reports(
    baseline_path: &Path,
    current_path: &Path,
    json_output: Option<&Path>,
    options: CompareOptions,
) -> Result<String> {
    let contexts = case_contexts()?;
    let baseline = load_input(baseline_path, &contexts)?;
    let current = load_input(current_path, &contexts)?;
    let comparison = compare_sets(baseline, current, &contexts, options)?;
    if let Some(output) = json_output {
        fs::write(
            output,
            serde_json::to_string_pretty(&comparison_json(&comparison))? + "\n",
        )
        .with_context(|| format!("write {}", output.display()))?;
    }
    Ok(render_human(&comparison))
}
