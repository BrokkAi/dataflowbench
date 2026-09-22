//! Regression tests for `crate::cases`.

use crate::adapters::bifrost::bifrost_anchor_dialect;
use crate::cases::{
    php_core_case, validate_balanced_core_pairs, validate_cases, validate_markers,
    validate_swift_metadata,
};
use crate::cases::{schema, validate_value};
use serde_json::{Value, json};
use std::{fs, path::Path, path::PathBuf};

#[test]
pub(crate) fn checked_in_cases_validate() {
    validate_cases().unwrap();
}

#[test]
pub(crate) fn core_templates_require_one_positive_and_one_negative() {
    let case = |polarity| {
        json!({
            "track": "taint",
            "language": "java",
            "template_id": "dfb-template-direct-propagation",
            "model_profile": "benchmark-controlled",
            "score_tier": "core",
            "polarity": polarity
        })
    };
    let balanced = vec![
        (PathBuf::from("positive.json"), case("positive")),
        (PathBuf::from("negative.json"), case("negative")),
    ];
    assert!(validate_balanced_core_pairs(&balanced).is_ok());

    let unbalanced = vec![(PathBuf::from("positive.json"), case("positive"))];
    assert!(validate_balanced_core_pairs(&unbalanced).is_err());
}

#[test]
pub(crate) fn marker_validation_rejects_stale_metadata() {
    let path = Path::new("cases/taint/java/direct-positive/case.json");
    let mut case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();

    case["source_anchors"][0]["line_hint"] = json!(1);
    assert!(validate_markers(path, &case).is_err());

    case["source_anchors"][0]["line_hint"] = json!(4);
    case["witness_checkpoints"] = json!(["DFB-WITNESS: absent"]);
    assert!(validate_markers(path, &case).is_err());
}

#[test]
pub(crate) fn php_core_selection_is_language_and_track_scoped() {
    let php = json!({
        "language": "php",
        "track": "taint",
        "score_tier": "core"
    });
    assert!(php_core_case(&php));
    for language in ["java", "javascript", "typescript", "python", "ruby", "go"] {
        let mut other = php.clone();
        other["language"] = json!(language);
        assert!(!php_core_case(&other));
    }
    let mut other = php.clone();
    other["track"] = json!("value-flow");
    assert!(!php_core_case(&other));
    other["track"] = json!("taint");
    other["score_tier"] = json!("calibration");
    assert!(!php_core_case(&other));
}

#[test]
pub(crate) fn case_schema_accepts_swift_without_closing_future_language_keys() {
    let compiled = schema("schemas/case.schema.json").unwrap();
    let mut case = json!({
        "schema_version": 2,
        "id": "dfb-taint-swift-schema-positive",
        "template_id": "dfb-template-direct-propagation",
        "polarity": "positive",
        "score_tier": "core",
        "track": "taint",
        "language": "swift",
        "semantic_dimensions": ["local-flow"],
        "feature_tags": ["intraprocedural"],
        "model_profile": "benchmark-controlled",
        "fixture_files": ["main.swift"],
        "source_anchors": [{"marker": "DFB-SOURCE: input", "file": "main.swift"}],
        "sink_anchors": [{"marker": "DFB-SINK: sink", "file": "main.swift"}],
        "expected_flows": [{"source": "DFB-SOURCE: input", "sink": "DFB-SINK: sink"}],
        "expected_nonflows": [],
        "witness_checkpoints": [],
        "expected_analysis_capability": {"kind": "intraprocedural-taint"},
        "execution_budget": {"wall_clock_seconds": 1},
        "fixture_provenance": {
            "kind": "authored", "origin": "DataFlowBench", "revision": "test", "license": "MIT"
        },
        "tool_model_references": {}
    });
    validate_value(&compiled, &case, Path::new("swift-case.json")).unwrap();
    case["language"] = json!("future-language");
    validate_value(&compiled, &case, Path::new("future-case.json")).unwrap();
}

#[test]
pub(crate) fn swift_registry_rejects_incomplete_duplicate_and_excluded_templates() {
    let cases: Vec<_> = crate::cases::all_case_paths()
        .into_iter()
        .filter(|path| path.starts_with("cases/taint/swift"))
        .map(|path| {
            let value: Value = serde_json::from_slice(&fs::read(&path).unwrap()).unwrap();
            (path, value)
        })
        .collect();
    validate_swift_metadata(&cases).unwrap();
    for tier in ["core", "calibration", "modeling"] {
        let without_tier: Vec<_> = cases
            .iter()
            .filter(|(_, c)| c["score_tier"] != tier)
            .cloned()
            .collect();
        assert!(
            validate_swift_metadata(&without_tier).is_err(),
            "missing {tier}"
        );
    }
    let mut missing = cases.clone();
    missing.pop();
    assert!(validate_swift_metadata(&missing).is_err());
    let mut extra = cases.clone();
    extra.push(cases[0].clone());
    assert!(validate_swift_metadata(&extra).is_err());
    let mut duplicate = cases.clone();
    duplicate[1] = duplicate[0].clone();
    assert!(
        validate_swift_metadata(&duplicate)
            .unwrap_err()
            .to_string()
            .contains("duplicate")
    );
    for excluded in [
        "dfb-template-chal-reflective-invocation",
        "dfb-template-chal-anonymous-implementation",
        "dfb-template-model-opaque-propagator",
    ] {
        let mut changed = cases.clone();
        changed[0].1["template_id"] = json!(excluded);
        assert!(validate_swift_metadata(&changed).is_err());
    }
    for (field, value) in [
        ("score_tier", "language-extension"),
        ("track", "value-flow"),
        ("model_profile", "tool-native"),
    ] {
        let mut changed = cases.clone();
        changed[0].1[field] = json!(value);
        assert!(validate_swift_metadata(&changed).is_err());
    }
    let mut polarity = cases.clone();
    polarity[0].1["polarity"] = json!(if polarity[0].1["polarity"] == "positive" {
        "negative"
    } else {
        "positive"
    });
    assert!(validate_swift_metadata(&polarity).is_err());
}

#[test]
pub(crate) fn swift_anchor_validation_rejects_duplicate_and_missing_locations() {
    let path = Path::new("cases/taint/swift/direct-positive/case.json");
    let case: Value = serde_json::from_slice(&fs::read(path).unwrap()).unwrap();
    crate::cases::validate_swift_anchors(path, &case).unwrap();
    let mut missing = case.clone();
    missing["source_anchors"][0]
        .as_object_mut()
        .unwrap()
        .remove("line_hint");
    assert!(crate::cases::validate_swift_anchors(path, &missing).is_err());
    let mut stale = case.clone();
    stale["source_anchors"][0]["line_hint"] = json!(1);
    assert!(crate::cases::validate_swift_anchors(path, &stale).is_err());
    let mut duplicate = case.clone();
    duplicate["source_anchors"]
        .as_array_mut()
        .unwrap()
        .push(case["source_anchors"][0].clone());
    assert!(crate::cases::validate_swift_anchors(path, &duplicate).is_err());
}

#[test]
pub(crate) fn swift_is_not_added_to_bifrost_language_inventory() {
    assert!(bifrost_anchor_dialect("swift").is_err());
}
