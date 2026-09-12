//! Focused tests for population-aware normalized report comparison (#204).

use crate::report_diff::{CompareOptions, case_contexts, compare_sets, load_input};
use serde_json::{Value, json};
use std::path::Path;

fn report(case_outcomes: &[(&str, &str)], configuration: &str, fixture: &str) -> Value {
    json!({
        "schema_version": 1,
        "tool": "test-tool",
        "tool_version": "1.0",
        "tool_build_identity": "build-1",
        "adapter_version": "0.1",
        "configuration_hash": configuration,
        "fixture_revision": fixture,
        "started_at_unix_seconds": 1,
        "ended_at_unix_seconds": 2,
        "cold_or_warm": "cold",
        "results": case_outcomes.iter().map(|(case_id, outcome)| json!({
            "case_id": case_id,
            "outcome": outcome,
            "source_anchors": [],
            "sink_anchors": [],
            "witness_checkpoints": [],
            "diagnostics": [],
            "duration_ms": 1,
            "peak_memory_mb": null,
            "raw_output": "reports/raw/test.json",
        })).collect::<Vec<_>>(),
    })
}

fn loaded(root: &Path, name: &str, value: &Value) -> crate::report_diff::ReportSet {
    let path = root.join(name);
    std::fs::write(&path, serde_json::to_vec_pretty(value).unwrap()).unwrap();
    let contexts = case_contexts().unwrap();
    load_input(&path, &contexts).unwrap()
}

#[test]
fn identical_populations_have_no_transitions() {
    let root = crate::tests::support::unique_test_dir("report-diff-identical");
    let report = report(&[("dfb-taint-test", "reached")], "config-1", "fixture-1");
    let baseline = loaded(&root, "baseline.json", &report);
    let current = loaded(&root, "current.json", &report);
    let result = compare_sets(
        baseline,
        current,
        &case_contexts().unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    assert!(result.populations_equal);
    assert_eq!(result.groups[0].retained, 1);
    assert_eq!(result.groups[0].added, 0);
    assert_eq!(result.groups[0].removed, 0);
    assert!(result.groups[0].retained_transitions.is_empty());
}

#[test]
fn expansion_and_removal_are_partitioned_not_pooled() {
    let root = crate::tests::support::unique_test_dir("report-diff-populations");
    let baseline = loaded(
        &root,
        "baseline.json",
        &report(
            &[
                ("dfb-taint-test", "reached"),
                ("dfb-taint-removed", "not-reached"),
            ],
            "config-1",
            "fixture-1",
        ),
    );
    let current = loaded(
        &root,
        "current.json",
        &report(
            &[
                ("dfb-taint-test", "reached"),
                ("dfb-taint-added", "inconclusive"),
            ],
            "config-1",
            "fixture-2",
        ),
    );
    let result = compare_sets(
        baseline,
        current,
        &case_contexts().unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    assert!(!result.populations_equal);
    assert_eq!(result.groups[0].retained, 1);
    assert_eq!(result.groups[0].added_cases[0].case_id, "dfb-taint-added");
    assert_eq!(result.groups[0].added_cases[0].outcome, "inconclusive");
    assert_eq!(
        result.groups[0].removed_cases[0].case_id,
        "dfb-taint-removed"
    );
    assert_eq!(
        result.groups[0].material_identity_differences["fixture_revision"]["current"],
        "fixture-2"
    );
}

#[test]
fn configuration_mismatch_fails_closed_but_is_explicitly_allowed() {
    let root = crate::tests::support::unique_test_dir("report-diff-configuration");
    let baseline = loaded(
        &root,
        "baseline.json",
        &report(
            &[("dfb-taint-test", "inconclusive")],
            "config-1",
            "fixture-1",
        ),
    );
    let current = loaded(
        &root,
        "current.json",
        &report(&[("dfb-taint-test", "reached")], "config-2", "fixture-1"),
    );
    let contexts = case_contexts().unwrap();
    let error = compare_sets(
        baseline.clone(),
        current.clone(),
        &contexts,
        CompareOptions::default(),
    )
    .unwrap_err();
    assert!(
        error.to_string().contains("configuration mismatch"),
        "{error}"
    );
    let allowed = compare_sets(
        baseline,
        current,
        &contexts,
        CompareOptions {
            allow_configuration_mismatch: true,
        },
    )
    .unwrap();
    assert_eq!(
        allowed.groups[0].material_identity_differences["configuration_hash"]["current"],
        "config-2"
    );
    assert_eq!(
        allowed.groups[0].retained_transitions[0].before,
        "inconclusive"
    );
    assert_eq!(allowed.groups[0].retained_transitions[0].after, "reached");
}

#[test]
fn all_five_outcomes_stay_distinct() {
    let root = crate::tests::support::unique_test_dir("report-diff-outcomes");
    let before = [
        ("a", "reached"),
        ("b", "not-reached"),
        ("c", "inconclusive"),
        ("d", "unsupported"),
        ("e", "runner-error"),
    ];
    let after = [
        ("a", "not-reached"),
        ("b", "reached"),
        ("c", "unsupported"),
        ("d", "runner-error"),
        ("e", "inconclusive"),
    ];
    let baseline = loaded(
        &root,
        "baseline.json",
        &report(&before, "config-1", "fixture-1"),
    );
    let current = loaded(
        &root,
        "current.json",
        &report(&after, "config-1", "fixture-1"),
    );
    let result = compare_sets(
        baseline,
        current,
        &case_contexts().unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    let transitions = &result.groups[0].outcome_partitions.unclassified.transitions;
    assert_eq!(transitions.len(), 5);
    assert_eq!(transitions["inconclusive -> unsupported"], 1);
    assert_eq!(transitions["runner-error -> inconclusive"], 1);
    assert_eq!(
        result.groups[0]
            .retained_transitions
            .iter()
            .find(|row| row.case_id == "c")
            .map(|row| row.after.as_str()),
        Some("unsupported")
    );
}

#[test]
fn positive_and_negative_cases_are_summarized_separately() {
    let root = crate::tests::support::unique_test_dir("report-diff-polarity");
    let positive = "dfb-taint-c-direct-positive";
    let negative = "dfb-taint-c-direct-negative";
    let baseline = loaded(
        &root,
        "baseline.json",
        &report(
            &[(positive, "reached"), (negative, "reached")],
            "config-1",
            "fixture-1",
        ),
    );
    let current = loaded(
        &root,
        "current.json",
        &report(
            &[(positive, "inconclusive"), (negative, "not-reached")],
            "config-1",
            "fixture-1",
        ),
    );
    let result = compare_sets(
        baseline,
        current,
        &case_contexts().unwrap(),
        CompareOptions::default(),
    )
    .unwrap();
    let partitions = &result.groups[0].outcome_partitions;
    assert_eq!(
        partitions.positive.transitions["reached -> inconclusive"],
        1
    );
    assert_eq!(partitions.negative.transitions["reached -> not-reached"], 1);
    assert!(
        partitions
            .positive
            .transitions
            .get("reached -> not-reached")
            .is_none()
    );
    assert!(
        partitions
            .negative
            .transitions
            .get("reached -> inconclusive")
            .is_none()
    );
    let row = result.groups[0]
        .retained_transitions
        .iter()
        .find(|row| row.case_id == positive)
        .unwrap();
    assert_eq!(row.polarity.as_deref(), Some("positive"));
    assert!(row.template_id.is_some());
}

#[test]
fn json_output_is_deterministic() {
    let root = crate::tests::support::unique_test_dir("report-diff-json");
    let report = report(&[("dfb-taint-test", "reached")], "config-1", "fixture-1");
    let baseline = loaded(&root, "baseline.json", &report);
    let current = loaded(&root, "current.json", &report.clone());
    let contexts = case_contexts().unwrap();
    let first = compare_sets(
        baseline.clone(),
        current.clone(),
        &contexts,
        CompareOptions::default(),
    )
    .unwrap();
    let second = compare_sets(baseline, current, &contexts, CompareOptions::default()).unwrap();
    let json = |comparison: &crate::report_diff::Comparison| {
        serde_json::to_string(&crate::report_diff::comparison_json(comparison)).unwrap()
    };
    assert_eq!(json(&first), json(&second));
}

#[test]
fn distinct_configurations_in_a_directory_do_not_collide() {
    let root = crate::tests::support::unique_test_dir("report-diff-directory-groups");
    let baseline_dir = root.join("baseline");
    let current_dir = root.join("current");
    std::fs::create_dir(&baseline_dir).unwrap();
    std::fs::create_dir(&current_dir).unwrap();
    for name in ["kernel-a", "kernel-b"] {
        let value = report(&[("dfb-taint-test", "reached")], name, "fixture-1");
        let baseline = baseline_dir.join(format!("{name}.json"));
        let current = current_dir.join(format!("{name}.json"));
        std::fs::write(baseline, serde_json::to_vec_pretty(&value).unwrap()).unwrap();
        std::fs::write(current, serde_json::to_vec_pretty(&value).unwrap()).unwrap();
    }
    let contexts = case_contexts().unwrap();
    let baseline = load_input(&baseline_dir, &contexts).unwrap();
    let current = load_input(&current_dir, &contexts).unwrap();
    let result = compare_sets(baseline, current, &contexts, CompareOptions::default()).unwrap();
    assert_eq!(result.groups.len(), 2);
}
