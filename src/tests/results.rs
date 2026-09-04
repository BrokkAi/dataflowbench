//! Regression tests for `crate::results`.

use crate::results::{
    GeneratedCaseMeta, SCORE_TIER_ORDER, build_index_page, build_scorecard, generate_results_at,
    scorecard_identifier,
};
use crate::tests::support::FreezeFixture;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs};

#[test]
pub(crate) fn generate_results_writes_deterministic_artifacts() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let output = fixture.root.join("generated");
    generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();

    let results: Value =
        serde_json::from_slice(&fs::read(output.join("results.json")).unwrap()).unwrap();
    assert_eq!(results["schema_version"], 1);
    let manifest_bytes = fs::read(&fixture.manifest).unwrap();
    assert_eq!(
        results["manifest"]["sha256"],
        json!(format!("{:x}", Sha256::digest(&manifest_bytes)))
    );
    let scorecard = &results["scorecards"][0];
    assert_eq!(
        scorecard["id"],
        json!("test-taint-taint-benchmark-controlled")
    );
    let tier = &scorecard["languages"][0]["score_tiers"][0];
    assert_eq!(scorecard["languages"][0]["language"], json!("c"));
    assert_eq!(tier["score_tier"], json!("core"));
    assert_eq!(tier["outcome_coverage"]["reached"], json!(1));
    assert_eq!(tier["outcome_coverage"]["total"], json!(1));
    assert_eq!(tier["cases"][0]["classification"], json!("true-positive"));
    let dimension = &tier["semantic_dimensions"][0];
    assert_eq!(dimension["name"], json!("local-flow"));
    assert_eq!(dimension["true_positive_rate"]["numerator"], json!(1));
    assert_eq!(dimension["true_positive_rate"]["percent"], json!("100.0"));
    assert_eq!(dimension["false_positive_rate"], Value::Null);
    assert_eq!(
        dimension["template_macro"]["true_positive_rate_percent"],
        json!("100.0")
    );
    assert_eq!(
        tier["dimension_macro"]["false_positive_rate_percent"],
        Value::Null
    );

    let index = fs::read_to_string(output.join("index.md")).unwrap();
    assert!(index.contains("test-taint-taint-benchmark-controlled"));
    let page =
        fs::read_to_string(output.join("scorecards/test-taint-taint-benchmark-controlled.md"))
            .unwrap();
    assert!(page.contains("`dfb-taint-test`"));
    assert!(page.contains("true-positive"));
    assert!(page.contains("reports/raw/test.json"));

    // Repeated generation from identical evidence is byte-stable.
    let before = fs::read(output.join("results.json")).unwrap();
    generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
    assert_eq!(before, fs::read(output.join("results.json")).unwrap());
}

#[test]
pub(crate) fn generate_results_classifies_incomplete_outcomes_separately() {
    let fixture = FreezeFixture::new("inconclusive", json!({"state": "inconclusive"}));
    let output = fixture.root.join("generated");
    generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
    let results: Value =
        serde_json::from_slice(&fs::read(output.join("results.json")).unwrap()).unwrap();
    let tier = &results["scorecards"][0]["languages"][0]["score_tiers"][0];
    assert_eq!(tier["cases"][0]["classification"], json!("inconclusive"));
    let dimension = &tier["semantic_dimensions"][0];
    assert_eq!(dimension["counts"]["inconclusive"], json!(1));
    assert_eq!(dimension["counts"]["false_negatives"], json!(0));
    // No definitive positive result: the rate stays null, never zero.
    assert_eq!(dimension["true_positive_rate"], Value::Null);
    assert_eq!(
        dimension["template_macro"]["true_positive_rate_percent"],
        Value::Null
    );
}

#[test]
pub(crate) fn generate_results_check_detects_current_stale_missing_and_extra() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let output = fixture.root.join("generated");
    assert!(
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
            .unwrap_err()
            .to_string()
            .contains("missing artifact")
    );
    generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
    generate_results_at(&fixture.root, &fixture.manifest, &output, false, true).unwrap();

    fs::write(output.join("index.md"), "stale\n").unwrap();
    assert!(
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
            .unwrap_err()
            .to_string()
            .contains("stale artifact: index.md")
    );

    generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).unwrap();
    fs::write(output.join("extra.md"), "extra\n").unwrap();
    assert!(
        generate_results_at(&fixture.root, &fixture.manifest, &output, false, true)
            .unwrap_err()
            .to_string()
            .contains("unexpected artifact: extra.md")
    );
}

#[test]
pub(crate) fn scorecard_identifiers_disambiguate_repeated_populations() {
    let mut used = BTreeMap::new();
    let report = json!({
        "track": "taint",
        "dimension": "taint",
        "model_profile": "benchmark-controlled"
    });
    assert_eq!(
        scorecard_identifier(&mut used, "Test.Adapter", &report).unwrap(),
        "test-adapter-taint-taint-benchmark-controlled"
    );
    assert_eq!(
        scorecard_identifier(&mut used, "Test.Adapter", &report).unwrap(),
        "test-adapter-taint-taint-benchmark-controlled-2"
    );
}

/// The generator, never a hand edit, states configuration staleness: a
/// scorecard built with a current-configuration mismatch carries the
/// caveat and the machine-readable hash pair, and one built without the
/// mismatch carries neither.
#[test]
pub(crate) fn scorecard_staleness_caveat_is_generator_emitted() {
    let adapter = json!({
        "id": "test",
        "tool": "test-tool",
        "tool_version": "1.0.0",
        "build_identity": "test-build",
        "adapter_version": "0.1.0",
        "configuration_hash": "aaaa",
        "track": "taint",
        "dimension": "taint",
        "model_profile": "benchmark-controlled",
    });
    let report = json!({
        "path": "reports/test.json",
        "sha256": "cafe",
        "normalized_report_sha256": "cafe",
        "adapter": "test",
        "track": "taint",
        "dimension": "taint",
        "model_profile": "benchmark-controlled",
        "case_ids": ["dfb-taint-test"],
        "outcomes": [{"case_id": "dfb-taint-test", "outcome": "reached"}],
        "raw_evidence": [
            {"case_id": "dfb-taint-test", "path": "reports/raw/test.json", "sha256": "feed"}
        ],
    });
    let mut case_meta = BTreeMap::new();
    case_meta.insert(
        "dfb-taint-test".to_string(),
        GeneratedCaseMeta {
            language: "c".to_string(),
            semantic_dimensions: vec!["local-flow".to_string()],
            template_id: "dfb-t1".to_string(),
            polarity: "positive".to_string(),
            score_tier: "core".to_string(),
        },
    );
    let (value, page) = build_scorecard(
        "test-taint-taint-benchmark-controlled",
        &adapter,
        &report,
        &case_meta,
        "reports/freeze.json",
        "beef",
        Some("bbbb"),
    )
    .unwrap();
    assert!(page.contains("predate the current adapter configuration"));
    assert!(page.contains("`aaaa`"));
    assert!(page.contains("`bbbb`"));
    assert_eq!(
        value["stale_configuration"],
        json!({
            "stamped_configuration_hash": "aaaa",
            "current_configuration_hash": "bbbb",
        })
    );

    let (value, page) = build_scorecard(
        "test-taint-taint-benchmark-controlled",
        &adapter,
        &report,
        &case_meta,
        "reports/freeze.json",
        "beef",
        None,
    )
    .unwrap();
    assert!(!page.contains("predate the current adapter configuration"));
    assert!(value.get("stale_configuration").is_none());

    // The index page names each stale population once, and only when one
    // exists.
    let manifest = json!({"benchmark": {}, "claim": {}, "reports": []});
    let stale = ["stale-population".to_string()];
    let index = build_index_page(&manifest, "reports/freeze.json", "beef", &[], &stale);
    assert!(index.contains("`stale-population`"));
    assert!(index.contains("predate the current adapter configuration"));
    let index = build_index_page(&manifest, "reports/freeze.json", "beef", &[], &[]);
    assert!(!index.contains("predate the current adapter configuration"));
}

/// The generated scorecards order `modeling` alongside the existing tiers.
/// A tier absent from this list would be silently dropped.
#[test]
pub(crate) fn the_result_tier_order_carries_modeling() {
    assert!(SCORE_TIER_ORDER.contains(&"modeling"));
}
