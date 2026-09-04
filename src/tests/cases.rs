//! Regression tests for `crate::cases`.

use crate::cases::{php_core_case, validate_balanced_core_pairs, validate_cases, validate_markers};
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
