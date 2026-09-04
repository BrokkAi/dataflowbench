//! Byte-stable result generation from a validated freeze: the scorecards, the
//! index page, and the `--check` proof that published artifacts match the
//! frozen evidence. See docs/results.md.

use crate::freeze::{repository_root, required_string, validate_freeze_at};
use crate::report::{
    ConfigurationHashState, configuration_drift_checkable, configuration_hash_state,
};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::Path};
use walkdir::WalkDir;

pub(crate) const RESULT_OUTCOME_ORDER: [&str; 5] = [
    "reached",
    "not-reached",
    "inconclusive",
    "unsupported",
    "runner-error",
];
/// Result-page tier ordering. A tier absent from this list would be silently
/// dropped from every generated scorecard, so `modeling` is registered here
/// with the schema enums, ahead of the first modeling case, rather than left
/// to be discovered by an empty section later.
pub(crate) const SCORE_TIER_ORDER: [&str; 5] = [
    "calibration",
    "core",
    "language-extension",
    "modeling",
    "real-project",
];

/// Case metadata a result view needs beyond what the freeze manifest binds.
/// Language and semantic dimensions live in the case file, whose bytes the
/// freeze validator has already verified against the manifest digest.
pub(crate) struct GeneratedCaseMeta {
    pub(crate) language: String,
    pub(crate) semantic_dimensions: Vec<String>,
    pub(crate) template_id: String,
    pub(crate) polarity: String,
    pub(crate) score_tier: String,
}

pub(crate) fn generate_results(
    manifest: &Path,
    output_directory: &Path,
    check: bool,
) -> Result<()> {
    let root = repository_root()?;
    let manifest = if manifest.is_absolute() {
        manifest.to_path_buf()
    } else {
        root.join(manifest)
    };
    generate_results_at(&root, &manifest, output_directory, true, check)?;
    if check {
        println!(
            "result artifacts in {} are current",
            output_directory.display()
        );
    } else {
        println!("wrote result artifacts to {}", output_directory.display());
    }
    Ok(())
}

/// Generate (or, with `check`, verify) result artifacts from a freeze that
/// must first pass full validation. `check_git` mirrors `validate_freeze_at`:
/// only isolated test fixtures may skip the checkout comparison.
pub(crate) fn generate_results_at(
    root: &Path,
    manifest_path: &Path,
    output_directory: &Path,
    check_git: bool,
    check: bool,
) -> Result<()> {
    validate_freeze_at(root, manifest_path, check_git)?;
    let artifacts = build_result_artifacts(root, manifest_path)?;
    if check {
        check_result_artifacts(output_directory, &artifacts)
    } else {
        write_result_artifacts(output_directory, &artifacts)
    }
}

pub(crate) fn build_result_artifacts(
    root: &Path,
    manifest_path: &Path,
) -> Result<BTreeMap<String, Vec<u8>>> {
    let manifest_bytes = fs::read(manifest_path)
        .with_context(|| format!("read freeze manifest {}", manifest_path.display()))?;
    let manifest_sha256 = format!("{:x}", Sha256::digest(&manifest_bytes));
    let manifest: Value = serde_json::from_slice(&manifest_bytes)
        .with_context(|| format!("parse freeze manifest {}", manifest_path.display()))?;
    let manifest_relative = manifest_display_path(root, manifest_path);

    let mut case_meta = BTreeMap::new();
    for selected in manifest["cases"].as_array().expect("freeze validated") {
        let id = required_string(selected, "id", "selected case")?;
        let relative_path = required_string(selected, "path", id)?;
        let case_bytes = fs::read(root.join(relative_path))
            .with_context(|| format!("read case {relative_path}"))?;
        let case: Value = serde_json::from_slice(&case_bytes)
            .with_context(|| format!("parse case {relative_path}"))?;
        let semantic_dimensions = case["semantic_dimensions"]
            .as_array()
            .expect("case schema validated")
            .iter()
            .map(|dimension| {
                dimension
                    .as_str()
                    .expect("case schema validated")
                    .to_string()
            })
            .collect();
        case_meta.insert(
            id.to_string(),
            GeneratedCaseMeta {
                language: required_string(&case, "language", id)?.to_string(),
                semantic_dimensions,
                template_id: required_string(selected, "template_id", id)?.to_string(),
                polarity: required_string(selected, "polarity", id)?.to_string(),
                score_tier: required_string(selected, "score_tier", id)?.to_string(),
            },
        );
    }

    let mut adapters = BTreeMap::new();
    for adapter in manifest["adapters"].as_array().expect("freeze validated") {
        adapters.insert(
            required_string(adapter, "id", "adapter")?.to_string(),
            adapter,
        );
    }

    let mut used_identifiers: BTreeMap<String, usize> = BTreeMap::new();
    let mut scorecard_values = Vec::new();
    let mut scorecard_pages = Vec::new();
    // The generator states configuration staleness itself, exactly like the
    // inconclusive-exclusion caveat: a frozen report whose stamped
    // configuration hash no longer matches the repository's current
    // configuration for that population gets a generator-emitted caveat,
    // never a hand-pasted one. Derivation stands on repository-relative
    // paths, so it runs only from the repository root; isolated fixture roots
    // generate exactly as before.
    let check_configuration = configuration_drift_checkable(root);
    let mut case_scan = None;
    let mut stale_configurations = Vec::new();
    for report in manifest["reports"].as_array().expect("freeze validated") {
        let adapter_id = required_string(report, "adapter", "frozen report")?;
        let adapter = adapters
            .get(adapter_id)
            .with_context(|| format!("frozen report binds unknown adapter {adapter_id}"))?;
        let identifier = scorecard_identifier(&mut used_identifiers, adapter_id, report)?;
        let current_configuration_hash = if check_configuration {
            let stem = Path::new(required_string(report, "path", "frozen report")?)
                .file_stem()
                .map(|stem| stem.to_string_lossy().into_owned())
                .with_context(|| format!("derive report stem for adapter {adapter_id}"))?;
            let stamped = required_string(adapter, "configuration_hash", "adapter")?;
            match configuration_hash_state(&stem, stamped, &mut case_scan)? {
                ConfigurationHashState::NotDerivable | ConfigurationHashState::Current => None,
                ConfigurationHashState::Drifted { current } => Some(current),
            }
        } else {
            None
        };
        if current_configuration_hash.is_some() {
            stale_configurations.push(identifier.clone());
        }
        let (value, page) = build_scorecard(
            &identifier,
            adapter,
            report,
            &case_meta,
            &manifest_relative,
            &manifest_sha256,
            current_configuration_hash.as_deref(),
        )?;
        scorecard_values.push(value);
        scorecard_pages.push((identifier, page));
    }

    let results = json!({
        "schema_version": 1,
        "manifest": {"path": manifest_relative, "sha256": manifest_sha256},
        "benchmark": manifest["benchmark"],
        "claim": manifest["claim"],
        "scorecards": scorecard_values,
    });
    let mut results_bytes = serde_json::to_vec_pretty(&results)?;
    results_bytes.push(b'\n');

    let mut artifacts = BTreeMap::new();
    artifacts.insert("results.json".to_string(), results_bytes);
    artifacts.insert(
        "index.md".to_string(),
        build_index_page(
            &manifest,
            &manifest_relative,
            &manifest_sha256,
            &scorecard_pages,
            &stale_configurations,
        )
        .into_bytes(),
    );
    for (identifier, page) in scorecard_pages {
        artifacts.insert(format!("scorecards/{identifier}.md"), page.into_bytes());
    }
    Ok(artifacts)
}

pub(crate) fn manifest_display_path(root: &Path, manifest_path: &Path) -> String {
    let canonical_root = fs::canonicalize(root).unwrap_or_else(|_| root.to_path_buf());
    let canonical_manifest =
        fs::canonicalize(manifest_path).unwrap_or_else(|_| manifest_path.to_path_buf());
    canonical_manifest
        .strip_prefix(&canonical_root)
        .unwrap_or(&canonical_manifest)
        .to_string_lossy()
        .replace('\\', "/")
}

/// A stable page identifier per frozen report. Reports that share an adapter,
/// track, dimension, and profile are distinct result populations, so later
/// occurrences receive an ordinal suffix in manifest order.
pub(crate) fn scorecard_identifier(
    used: &mut BTreeMap<String, usize>,
    adapter_id: &str,
    report: &Value,
) -> Result<String> {
    let mut base = String::new();
    for part in [
        adapter_id,
        required_string(report, "track", "frozen report")?,
        required_string(report, "dimension", "frozen report")?,
        required_string(report, "model_profile", "frozen report")?,
    ] {
        if !base.is_empty() {
            base.push('-');
        }
        for character in part.chars() {
            base.push(match character.to_ascii_lowercase() {
                lower @ ('a'..='z' | '0'..='9') => lower,
                _ => '-',
            });
        }
    }
    let ordinal = used.entry(base.clone()).or_insert(0);
    *ordinal += 1;
    if *ordinal == 1 {
        Ok(base)
    } else {
        Ok(format!("{base}-{ordinal}"))
    }
}

pub(crate) fn classify_outcome(polarity: &str, outcome: &str) -> &'static str {
    match (polarity, outcome) {
        ("positive", "reached") => "true-positive",
        ("positive", "not-reached") => "false-negative",
        ("negative", "reached") => "false-positive",
        ("negative", "not-reached") => "true-negative",
        (_, "inconclusive") => "inconclusive",
        (_, "unsupported") => "unsupported",
        _ => "runner-error",
    }
}

pub(crate) fn rate_fraction(numerator: usize, denominator: usize) -> Value {
    if denominator == 0 {
        Value::Null
    } else {
        json!({
            "numerator": numerator,
            "denominator": denominator,
            "percent": percent_string(numerator as f64 / denominator as f64),
        })
    }
}

pub(crate) fn percent_string(rate: f64) -> String {
    format!("{:.1}", rate * 100.0)
}

pub(crate) fn mean_percent(rates: &[f64]) -> Option<String> {
    if rates.is_empty() {
        None
    } else {
        Some(percent_string(
            rates.iter().sum::<f64>() / rates.len() as f64,
        ))
    }
}

/// Build one scorecard's JSON value and Markdown page.
///
/// `current_configuration_hash` is `Some` when the repository's current
/// configuration for this population no longer hashes to the value the frozen
/// report was stamped with; the scorecard then carries a generator-emitted
/// staleness caveat, on the same terms as the inconclusive-exclusion caveat.
pub(crate) fn build_scorecard(
    identifier: &str,
    adapter: &Value,
    report: &Value,
    case_meta: &BTreeMap<String, GeneratedCaseMeta>,
    manifest_relative: &str,
    manifest_sha256: &str,
    current_configuration_hash: Option<&str>,
) -> Result<(Value, String)> {
    let mut outcomes = BTreeMap::new();
    for record in report["outcomes"].as_array().expect("freeze validated") {
        outcomes.insert(
            required_string(record, "case_id", "outcome record")?,
            required_string(record, "outcome", "outcome record")?,
        );
    }
    let mut raw_evidence = BTreeMap::new();
    for evidence in report["raw_evidence"].as_array().expect("freeze validated") {
        raw_evidence.insert(
            required_string(evidence, "case_id", "raw evidence")?,
            (
                required_string(evidence, "path", "raw evidence")?,
                required_string(evidence, "sha256", "raw evidence")?,
            ),
        );
    }

    // language -> score tier -> case IDs, in deterministic order.
    let mut populations: BTreeMap<&str, BTreeMap<&str, Vec<&str>>> = BTreeMap::new();
    for case_id in report["case_ids"].as_array().expect("freeze validated") {
        let case_id = case_id.as_str().expect("freeze validated");
        let meta = case_meta
            .get(case_id)
            .with_context(|| format!("frozen report selects unknown case {case_id}"))?;
        populations
            .entry(meta.language.as_str())
            .or_default()
            .entry(meta.score_tier.as_str())
            .or_default()
            .push(case_id);
    }

    let track = required_string(report, "track", "frozen report")?;
    let dimension = required_string(report, "dimension", "frozen report")?;
    let model_profile = required_string(report, "model_profile", "frozen report")?;
    let report_path = required_string(report, "path", "frozen report")?;
    let report_sha256 = required_string(report, "sha256", "frozen report")?;
    let normalized_sha256 = required_string(report, "normalized_report_sha256", "frozen report")?;

    let mut page = String::new();
    page.push_str(&format!("# Scorecard `{identifier}`\n\n"));
    page.push_str(&format!(
        "Adapter `{}`: `{}` `{}` (build `{}`, adapter version `{}`, configuration `{}`).\n\n",
        required_string(adapter, "id", "adapter")?,
        required_string(adapter, "tool", "adapter")?,
        required_string(adapter, "tool_version", "adapter")?,
        required_string(adapter, "build_identity", "adapter")?,
        required_string(adapter, "adapter_version", "adapter")?,
        required_string(adapter, "configuration_hash", "adapter")?,
    ));
    page.push_str(&format!(
        "Track `{track}`, score dimension `{dimension}`, model profile `{model_profile}`. \
         This scorecard is a single result population; it is never pooled with \
         other tracks, dimensions, or model profiles.\n\n"
    ));
    page.push_str(&format!(
        "Normalized report: `{report_path}` (`sha256:{report_sha256}`, normalized \
         `sha256:{normalized_sha256}`). Generated from freeze manifest \
         `{manifest_relative}` (`sha256:{manifest_sha256}`).\n"
    ));
    if let Some(current) = current_configuration_hash {
        page.push_str(&format!(
            "\nCaveat: these outcomes predate the current adapter configuration. \
             The frozen report was produced under configuration hash `{}`, but \
             this population's committed configuration currently hashes to \
             `{current}`. The numbers stand as frozen evidence for the \
             configuration they were measured under; they do not describe the \
             current configuration until the population is re-run.\n",
            required_string(adapter, "configuration_hash", "adapter")?,
        ));
    }

    let mut language_values = Vec::new();
    for (language, tiers) in &populations {
        let mut tier_values = Vec::new();
        for tier in SCORE_TIER_ORDER {
            let Some(case_ids) = tiers.get(tier) else {
                continue;
            };
            let scored = tier != "calibration";
            page.push_str(&format!("\n## Language `{language}`, tier `{tier}`\n\n"));

            let mut coverage: BTreeMap<&str, usize> = BTreeMap::new();
            for case_id in case_ids {
                *coverage.entry(outcomes[case_id]).or_default() += 1;
            }
            let coverage_value: Value = RESULT_OUTCOME_ORDER
                .iter()
                .map(|outcome| {
                    (
                        outcome.to_string(),
                        json!(coverage.get(outcome).copied().unwrap_or(0)),
                    )
                })
                .chain([("total".to_string(), json!(case_ids.len()))])
                .collect::<serde_json::Map<_, _>>()
                .into();
            page.push_str("Outcome coverage: ");
            for outcome in RESULT_OUTCOME_ORDER {
                page.push_str(&format!(
                    "`{outcome}` {}, ",
                    coverage.get(outcome).copied().unwrap_or(0)
                ));
            }
            page.push_str(&format!(
                "total {}. `inconclusive`, `unsupported`, and `runner-error` are \
                 capability and execution coverage; they are never counted as \
                 clean negatives.\n",
                case_ids.len()
            ));
            if !scored {
                page.push_str(
                    "\nCalibration cases exercise schemas and adapters; they do not \
                     contribute to a correctness score.\n",
                );
            }

            // semantic dimension -> template -> case IDs.
            let mut by_dimension: BTreeMap<&str, BTreeMap<&str, Vec<&str>>> = BTreeMap::new();
            for case_id in case_ids {
                let meta = &case_meta[*case_id];
                for semantic_dimension in &meta.semantic_dimensions {
                    by_dimension
                        .entry(semantic_dimension.as_str())
                        .or_default()
                        .entry(meta.template_id.as_str())
                        .or_default()
                        .push(case_id);
                }
            }

            let mut dimension_values = Vec::new();
            let mut dimension_tprs = Vec::new();
            let mut dimension_fprs = Vec::new();
            if scored {
                page.push_str("\n### Semantic dimension rates\n\n");
                page.push_str(
                    "| Semantic dimension | TP | FN | FP | TN | Inconclusive | \
                     Unsupported | Runner error | TPR (template macro) | \
                     FPR (template macro) |\n",
                );
                page.push_str("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |\n");
            }
            for (semantic_dimension, templates) in &by_dimension {
                let mut counts: BTreeMap<&str, usize> = BTreeMap::new();
                let mut template_tprs = Vec::new();
                let mut template_fprs = Vec::new();
                for template_cases in templates.values() {
                    let mut template_counts: BTreeMap<&str, usize> = BTreeMap::new();
                    for case_id in template_cases {
                        let classification =
                            classify_outcome(&case_meta[*case_id].polarity, outcomes[case_id]);
                        *template_counts.entry(classification).or_default() += 1;
                        *counts.entry(classification).or_default() += 1;
                    }
                    let true_positives = template_counts.get("true-positive").copied().unwrap_or(0);
                    let false_negatives =
                        template_counts.get("false-negative").copied().unwrap_or(0);
                    let false_positives =
                        template_counts.get("false-positive").copied().unwrap_or(0);
                    let true_negatives = template_counts.get("true-negative").copied().unwrap_or(0);
                    if true_positives + false_negatives > 0 {
                        template_tprs.push(
                            true_positives as f64 / (true_positives + false_negatives) as f64,
                        );
                    }
                    if false_positives + true_negatives > 0 {
                        template_fprs.push(
                            false_positives as f64 / (false_positives + true_negatives) as f64,
                        );
                    }
                }
                let count = |classification: &str| counts.get(classification).copied().unwrap_or(0);
                let tpr = mean_percent(&template_tprs);
                let fpr = mean_percent(&template_fprs);
                if scored {
                    page.push_str(&format!(
                        "| `{semantic_dimension}` | {} | {} | {} | {} | {} | {} | {} | {} | {} |\n",
                        count("true-positive"),
                        count("false-negative"),
                        count("false-positive"),
                        count("true-negative"),
                        count("inconclusive"),
                        count("unsupported"),
                        count("runner-error"),
                        percent_cell(&tpr),
                        percent_cell(&fpr),
                    ));
                }
                if let Some(tpr) = &tpr {
                    dimension_tprs.push(tpr.parse::<f64>().expect("formatted percent") / 100.0);
                }
                if let Some(fpr) = &fpr {
                    dimension_fprs.push(fpr.parse::<f64>().expect("formatted percent") / 100.0);
                }
                dimension_values.push(json!({
                    "name": semantic_dimension,
                    "counts": {
                        "true_positives": count("true-positive"),
                        "false_negatives": count("false-negative"),
                        "false_positives": count("false-positive"),
                        "true_negatives": count("true-negative"),
                        "inconclusive": count("inconclusive"),
                        "unsupported": count("unsupported"),
                        "runner_errors": count("runner-error"),
                    },
                    "true_positive_rate": rate_fraction(
                        count("true-positive"),
                        count("true-positive") + count("false-negative"),
                    ),
                    "false_positive_rate": rate_fraction(
                        count("false-positive"),
                        count("false-positive") + count("true-negative"),
                    ),
                    "template_macro": {
                        "true_positive_rate_percent": tpr,
                        "false_positive_rate_percent": fpr,
                        "scored_positive_templates": template_tprs.len(),
                        "scored_negative_templates": template_fprs.len(),
                    },
                }));
            }
            let macro_tpr = mean_percent(&dimension_tprs);
            let macro_fpr = mean_percent(&dimension_fprs);
            if scored {
                page.push_str(&format!(
                    "\nMacro-average over semantic dimensions: TPR {}, FPR {}. \
                     Macro-averages pool templates first, then semantic dimensions; \
                     raw case counts are shown for audit only.\n",
                    percent_cell(&macro_tpr),
                    percent_cell(&macro_fpr),
                ));
                let inconclusive = coverage.get("inconclusive").copied().unwrap_or(0);
                page.push_str(&format!(
                    "\nCaveat: `inconclusive` outcomes are excluded from every TPR \
                     and FPR denominator above, so the rates cover only the \
                     conclusive subset of this population. This population records \
                     {inconclusive} `inconclusive` outcome(s){}. Compare rate \
                     columns across adapters with that exclusion in mind: an \
                     adapter that self-reports uncertainty is not penalized in its \
                     rates for the cases it declined to decide.\n",
                    if inconclusive > 0 {
                        format!(
                            ", produced by `{}`",
                            adapter["tool"].as_str().unwrap_or("unknown"),
                        )
                    } else {
                        String::new()
                    },
                ));
            }

            page.push_str("\n### Cases\n\n");
            page.push_str(
                "| Template | Case | Polarity | Outcome | Classification | \
                 Raw evidence | Raw SHA-256 |\n",
            );
            page.push_str("| --- | --- | --- | --- | --- | --- | --- |\n");
            let mut case_values = Vec::new();
            let mut ordered_cases: Vec<&&str> = case_ids.iter().collect();
            ordered_cases
                .sort_by_key(|case_id| (case_meta[**case_id].template_id.as_str(), **case_id));
            for case_id in ordered_cases {
                let meta = &case_meta[*case_id];
                let outcome = outcomes[case_id];
                let classification = classify_outcome(&meta.polarity, outcome);
                let (raw_path, raw_sha256) = raw_evidence[case_id];
                page.push_str(&format!(
                    "| `{}` | `{case_id}` | {} | `{outcome}` | {classification} | \
                     `{raw_path}` | `{raw_sha256}` |\n",
                    meta.template_id, meta.polarity,
                ));
                case_values.push(json!({
                    "case_id": case_id,
                    "template_id": meta.template_id,
                    "polarity": meta.polarity,
                    "semantic_dimensions": meta.semantic_dimensions,
                    "outcome": outcome,
                    "classification": classification,
                    "raw_evidence": {"path": raw_path, "sha256": raw_sha256},
                }));
            }

            tier_values.push(json!({
                "score_tier": tier,
                "scored": scored,
                "outcome_coverage": coverage_value,
                "semantic_dimensions": dimension_values,
                "dimension_macro": {
                    "true_positive_rate_percent": macro_tpr,
                    "false_positive_rate_percent": macro_fpr,
                },
                "cases": case_values,
            }));
        }
        language_values.push(json!({
            "language": language,
            "score_tiers": tier_values,
        }));
    }

    let mut value = json!({
        "id": identifier,
        "adapter": adapter,
        "track": track,
        "dimension": dimension,
        "model_profile": model_profile,
        "report": {
            "path": report_path,
            "sha256": report_sha256,
            "normalized_report_sha256": normalized_sha256,
        },
        "languages": language_values,
    });
    if let Some(current) = current_configuration_hash {
        value["stale_configuration"] = json!({
            "stamped_configuration_hash": required_string(adapter, "configuration_hash", "adapter")?,
            "current_configuration_hash": current,
        });
    }
    Ok((value, page))
}

pub(crate) fn percent_cell(percent: &Option<String>) -> String {
    match percent {
        Some(percent) => format!("{percent}%"),
        None => "n/a".to_string(),
    }
}

pub(crate) fn build_index_page(
    manifest: &Value,
    manifest_relative: &str,
    manifest_sha256: &str,
    scorecard_pages: &[(String, String)],
    stale_configurations: &[String],
) -> String {
    let benchmark = &manifest["benchmark"];
    let claim = &manifest["claim"];
    let mut page = String::new();
    page.push_str("# DataFlowBench frozen results\n\n");
    page.push_str(&format!(
        "Generated from freeze manifest `{manifest_relative}` \
         (`sha256:{manifest_sha256}`), benchmark release `{}` at revision \
         `{}`, fixture revision `{}`.\n\n",
        benchmark["release"].as_str().unwrap_or_default(),
        benchmark["revision"].as_str().unwrap_or_default(),
        benchmark["fixture_revision"].as_str().unwrap_or_default(),
    ));
    page.push_str(&format!(
        "Claim scope `{}`. Every number on these pages is derived from the \
         immutable freeze evidence above; none are maintained by hand. Tracks, \
         score dimensions, score tiers, and model profiles are separate result \
         populations and are never combined into one leaderboard.\n\n",
        claim["scope"].as_str().unwrap_or_default(),
    ));
    let mut inconclusive_by_adapter: BTreeMap<&str, usize> = BTreeMap::new();
    for report in manifest["reports"].as_array().into_iter().flatten() {
        let inconclusive = report["outcomes"]
            .as_array()
            .into_iter()
            .flatten()
            .filter(|record| record["outcome"] == "inconclusive")
            .count();
        if inconclusive > 0 {
            *inconclusive_by_adapter
                .entry(report["adapter"].as_str().unwrap_or("unknown"))
                .or_default() += inconclusive;
        }
    }
    if !inconclusive_by_adapter.is_empty() {
        let producers = inconclusive_by_adapter
            .iter()
            .map(|(adapter, count)| format!("`{adapter}` ({count})"))
            .collect::<Vec<_>>()
            .join(", ");
        page.push_str(&format!(
            "Caveat: `inconclusive` outcomes are excluded from every TPR and FPR \
             denominator on these pages, so rate columns cover only each \
             population's conclusive subset. In this freeze every `inconclusive` \
             outcome is produced by: {producers}. Compare rate columns across \
             adapters with that exclusion in mind.\n\n",
        ));
    }
    if !stale_configurations.is_empty() {
        let populations = stale_configurations
            .iter()
            .map(|identifier| format!("`{identifier}`"))
            .collect::<Vec<_>>()
            .join(", ");
        page.push_str(&format!(
            "Caveat: the following result populations were frozen under an \
             adapter configuration that has since changed in this repository: \
             {populations}. Their outcomes predate the current adapter \
             configuration; they stand as frozen evidence for the configuration \
             they were measured under until each population is re-run.\n\n",
        ));
    }
    for (label, field) in [
        ("Tracks", "tracks"),
        ("Score dimensions", "dimensions"),
        ("Score tiers", "score_tiers"),
        ("Model profiles", "model_profiles"),
    ] {
        let names = claim[field]
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(Value::as_str)
            .map(|name| format!("`{name}`"))
            .collect::<Vec<_>>()
            .join(", ");
        page.push_str(&format!("- {label}: {names}\n"));
    }

    page.push_str("\n## Exclusions\n\n");
    let exclusions = claim["exclusions"].as_array().cloned().unwrap_or_default();
    if exclusions.is_empty() {
        page.push_str("None.\n");
    } else {
        page.push_str("| Case | Reason |\n| --- | --- |\n");
        for exclusion in &exclusions {
            page.push_str(&format!(
                "| `{}` | {} |\n",
                exclusion["id"].as_str().unwrap_or_default(),
                exclusion["reason"].as_str().unwrap_or_default(),
            ));
        }
    }

    page.push_str("\n## Scorecards\n\n");
    for (identifier, _) in scorecard_pages {
        page.push_str(&format!("- [`{identifier}`](scorecards/{identifier}.md)\n"));
    }
    page
}

pub(crate) fn write_result_artifacts(
    output_directory: &Path,
    artifacts: &BTreeMap<String, Vec<u8>>,
) -> Result<()> {
    for (relative, bytes) in artifacts {
        let path = output_directory.join(relative);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent)
                .with_context(|| format!("create output directory {}", parent.display()))?;
        }
        fs::write(&path, bytes)
            .with_context(|| format!("write result artifact {}", path.display()))?;
    }
    Ok(())
}

/// Prove the checked-in artifacts are byte-identical to a fresh generation.
/// Missing, stale, and unexpected files each fail the check so a stale page
/// cannot survive behind a regenerated sibling.
pub(crate) fn check_result_artifacts(
    output_directory: &Path,
    artifacts: &BTreeMap<String, Vec<u8>>,
) -> Result<()> {
    let mut problems = Vec::new();
    for (relative, expected) in artifacts {
        let path = output_directory.join(relative);
        match fs::read(&path) {
            Ok(actual) if &actual == expected => {}
            Ok(_) => problems.push(format!("stale artifact: {relative}")),
            Err(_) => problems.push(format!("missing artifact: {relative}")),
        }
    }
    if output_directory.is_dir() {
        for entry in WalkDir::new(output_directory) {
            let entry = entry.context("walk output directory")?;
            if !entry.file_type().is_file() {
                continue;
            }
            let relative = entry
                .path()
                .strip_prefix(output_directory)
                .expect("walked under output directory")
                .to_string_lossy()
                .replace('\\', "/");
            if !artifacts.contains_key(&relative) {
                problems.push(format!("unexpected artifact: {relative}"));
            }
        }
    }
    if !problems.is_empty() {
        bail!("result artifacts are not current:\n{}", problems.join("\n"));
    }
    Ok(())
}
