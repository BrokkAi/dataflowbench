//! Regression tests for `crate::report`.

use crate::adapters::ToolIdentity;
use crate::adapters::bifrost::normalize_bifrost;
use crate::evidence::AnchorDialect;
use crate::report::{
    ConfigurationHashState, KNOWN_STALE_CONFIGURATIONS, configuration_hash_state,
    current_configuration_paths, hash_paths, validate_reports, validate_reports_in,
    write_and_validate_report_in,
};
use crate::runtime::{write_case_phase_timings, write_run_environment};
use crate::tests::support::{ReportSweepFixture, unique_test_dir};
use anyhow::Result;
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, time::Duration};

#[test]
pub(crate) fn report_directory_validates() {
    validate_reports().unwrap();
}

#[test]
pub(crate) fn end_of_run_sweep_tolerates_a_concurrent_runner_rewriting_its_raw_evidence() {
    let fixture = ReportSweepFixture::new();
    let own_raw = "reports/raw/own-kernel/case.json";
    fixture.write_raw(own_raw);
    let own = fixture.write_report("own-kernel.json", &ReportSweepFixture::report(own_raw));
    // The other kernel's report is intact, but its raw evidence is mid
    // removal-and-rewrite: the retained file is momentarily absent.
    fixture.write_report(
        "other-kernel.json",
        &ReportSweepFixture::report("reports/raw/other-kernel/case.json"),
    );
    validate_reports_in(&fixture.root, Some(&own)).unwrap();
    let full = validate_reports_in(&fixture.root, None).unwrap_err();
    assert!(full.to_string().contains("is absent"), "{full}");
}

#[test]
pub(crate) fn end_of_run_sweep_still_checks_the_runners_own_raw_evidence() {
    let fixture = ReportSweepFixture::new();
    let own = fixture.write_report(
        "own-kernel.json",
        &ReportSweepFixture::report("reports/raw/own-kernel/case.json"),
    );
    let error = validate_reports_in(&fixture.root, Some(&own)).unwrap_err();
    assert!(error.to_string().contains("is absent"), "{error}");
}

#[test]
pub(crate) fn end_of_run_sweep_still_schema_checks_other_reports() {
    let fixture = ReportSweepFixture::new();
    let own_raw = "reports/raw/own-kernel/case.json";
    fixture.write_raw(own_raw);
    let own = fixture.write_report("own-kernel.json", &ReportSweepFixture::report(own_raw));
    let mut malformed = ReportSweepFixture::report("reports/raw/other-kernel/case.json");
    malformed.as_object_mut().unwrap().remove("tool");
    fixture.write_report("other-kernel.json", &malformed);
    let error = validate_reports_in(&fixture.root, Some(&own)).unwrap_err();
    assert!(error.to_string().contains("other-kernel.json"), "{error}");
}

#[test]
pub(crate) fn runner_never_publishes_a_report_it_did_not_validate() {
    let fixture = ReportSweepFixture::new();
    // Schema-invalid report: publishing must fail before anything lands.
    let mut invalid = ReportSweepFixture::report("reports/raw/own-kernel/case.json");
    invalid.as_object_mut().unwrap().remove("tool");
    let report_path = Path::new("reports/own-kernel.json");
    write_and_validate_report_in(&fixture.root, report_path, &invalid).unwrap_err();
    // Valid schema but absent raw evidence: same conservative refusal.
    let unbacked = ReportSweepFixture::report("reports/raw/own-kernel/case.json");
    write_and_validate_report_in(&fixture.root, report_path, &unbacked).unwrap_err();
    let leftovers: Vec<_> = fs::read_dir(fixture.root.join("reports"))
        .unwrap()
        .filter_map(Result::ok)
        .filter(|entry| entry.path().is_file())
        .collect();
    assert!(leftovers.is_empty(), "{leftovers:?}");
}

#[test]
pub(crate) fn runner_publishes_a_validated_report_atomically() {
    let fixture = ReportSweepFixture::new();
    let own_raw = "reports/raw/own-kernel/case.json";
    fixture.write_raw(own_raw);
    // A concurrent kernel's evidence is mid-rewrite; publishing must
    // still succeed.
    fixture.write_report(
        "other-kernel.json",
        &ReportSweepFixture::report("reports/raw/other-kernel/case.json"),
    );
    let report_path = Path::new("reports/own-kernel.json");
    write_and_validate_report_in(
        &fixture.root,
        report_path,
        &ReportSweepFixture::report(own_raw),
    )
    .unwrap();
    let published: Value =
        serde_json::from_str(&fs::read_to_string(fixture.root.join(report_path)).unwrap()).unwrap();
    assert_eq!(published["tool"], "test-tool");
    assert!(!fixture.root.join("reports/own-kernel.json.tmp").exists());
}

/// Timing fields are additive metadata (#90): validate-reports must accept
/// retained raw evidence both with and without the timing sidecar and the
/// run-environment stamp beside it.
#[test]
pub(crate) fn validate_reports_accepts_raw_evidence_with_and_without_timing_metadata() {
    let fixture = ReportSweepFixture::new();
    let own_raw = "reports/raw/own-kernel/case.json";
    fixture.write_raw(own_raw);
    let own = fixture.write_report("own-kernel.json", &ReportSweepFixture::report(own_raw));
    // Without any timing metadata: the pre-existing shape stays valid.
    validate_reports_in(&fixture.root, Some(&own)).unwrap();
    // With the per-case sidecar and the per-run environment stamp: still
    // valid, and validation never requires either.
    let raw_dir = fixture.root.join("reports/raw/own-kernel");
    write_case_phase_timings(
        &raw_dir,
        "test-tool",
        "case",
        &[
            ("database-create", Duration::from_millis(1200)),
            ("database-analyze", Duration::from_millis(340)),
        ],
    )
    .unwrap();
    write_run_environment(
        &raw_dir,
        "test-tool",
        &ToolIdentity::new("1.0.0", "test-build-1"),
    )
    .unwrap();
    validate_reports_in(&fixture.root, Some(&own)).unwrap();
    validate_reports_in(&fixture.root, None).unwrap();
}

#[test]
pub(crate) fn normalizer_keeps_negative_and_unsupported_distinct() {
    let case_path = Path::new("cases/never/case.json");
    let negative = json!({"expected_flows": []});
    assert_eq!(
        normalize_bifrost(
            case_path,
            &negative,
            &json!({
                "runs": [{"completion": {"type": "complete"}, "findings": []}]
            }),
            Some(0),
            AnchorDialect::Java,
        )
        .unwrap()
        .0,
        "not-reached"
    );
    // A finding the case's sink anchor cannot vouch for is downgraded to
    // `inconclusive`, exactly as every external adapter's evidence is.
    let unproven = normalize_bifrost(
        case_path,
        &negative,
        &json!({
            "runs": [{"completion": {"type": "complete"}, "findings": [{}]}]
        }),
        Some(0),
        AnchorDialect::Java,
    )
    .unwrap();
    assert_eq!(unproven.0, "inconclusive");
    assert!(unproven.1.iter().any(|diagnostic| {
        diagnostic.contains("cannot prove a Bifrost finding against the sink anchor")
    }));
    assert_eq!(
        normalize_bifrost(
            case_path,
            &negative,
            &json!({}),
            Some(2),
            AnchorDialect::Java
        )
        .unwrap()
        .0,
        "inconclusive"
    );
    assert!(normalize_bifrost(
        case_path,
        &negative,
        &json!({"runs": [{"completion": {"type": "inconclusive", "reasons": ["partial_discovery"]}}]}),
        Some(2),
        AnchorDialect::Java,
    )
    .unwrap()
    .1
        .contains(&"Bifrost reported incomplete analysis: partial_discovery".to_string()));
}

#[test]
pub(crate) fn normalizer_does_not_synthesize_witness_checkpoints() {
    let root = unique_test_dir("dataflowbench-bifrost-witness-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("Fixture.java"),
        "    static void dfbSink(int value) { } // DFB-SINK: sink\n        dfbSink(input);\n",
    )
    .unwrap();
    let case = json!({
        "expected_flows": [{"source": "DFB-SOURCE: input", "sink": "DFB-SINK: sink"}],
        "witness_checkpoints": ["DFB-WITNESS: relay"],
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "Fixture.java",
            "line_hint": 1
        }]
    });
    let normalized = normalize_bifrost(
        &case_path,
        &case,
        &json!({
            "runs": [{"completion": {"type": "complete"}, "findings": [{
                "primary": {"path": "Fixture.java", "region": {"start_line": 2}}
            }]}]
        }),
        Some(0),
        AnchorDialect::Java,
    )
    .unwrap();
    assert_eq!(normalized.0, "reached");
    assert!(normalized.2.is_empty());
    fs::remove_dir_all(root).unwrap();
}

/// A report stamped with the hash the current configuration derives to is
/// current; the same report stamped with any other value has drifted; a
/// population whose hash is not derivable in-repo (tool-native
/// activations, foreign stems) is never compared at all.
#[test]
pub(crate) fn configuration_hash_comparison_distinguishes_current_from_drifted() {
    let mut case_scan = None;
    let paths = current_configuration_paths("joern-java-kernel", &mut case_scan)
        .unwrap()
        .expect("the Joern kernel hash derives from the committed kernel script");
    let current = hash_paths(&paths).unwrap();
    assert_eq!(
        configuration_hash_state("joern-java-kernel", &current, &mut case_scan).unwrap(),
        ConfigurationHashState::Current
    );
    let drifted = "0".repeat(64);
    assert_eq!(
        configuration_hash_state("joern-java-kernel", &drifted, &mut case_scan).unwrap(),
        ConfigurationHashState::Drifted { current }
    );
    // Tool-native hashes bind the witnessed binary identity, and unknown
    // stems name no population this repository produces.
    for underivable in ["bifrost-java-native", "own-kernel", "freeze"] {
        assert_eq!(
            configuration_hash_state(underivable, &drifted, &mut case_scan).unwrap(),
            ConfigurationHashState::NotDerivable,
            "{underivable} must not be compared"
        );
    }
}

/// Every committed report whose configuration hash is derivable in-repo
/// still matches the current configuration — except the populations
/// `KNOWN_STALE_CONFIGURATIONS` records against issue #138, each of which
/// must actually drift. The half that fails when a re-run lands is the
/// machine-readable reminder to delete that population's allowlist entry
/// in the same pull request.
#[test]
pub(crate) fn committed_reports_match_current_configuration_except_known_stale() {
    let mut case_scan = None;
    let mut seen_stale = BTreeSet::new();
    for entry in fs::read_dir("reports").unwrap().filter_map(Result::ok) {
        let path = entry.path();
        if !path.is_file() || path.extension().is_none_or(|ext| ext != "json") {
            continue;
        }
        let report: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        if report.get("benchmark").is_some() && report.get("claim").is_some() {
            continue;
        }
        let stem = path.file_stem().unwrap().to_str().unwrap().to_string();
        let stamped = report["configuration_hash"].as_str().unwrap();
        let state = configuration_hash_state(&stem, stamped, &mut case_scan).unwrap();
        if KNOWN_STALE_CONFIGURATIONS.contains(&stem.as_str()) {
            seen_stale.insert(stem.clone());
            assert!(
                matches!(state, ConfigurationHashState::Drifted { .. }),
                "{stem} no longer drifts; remove it from KNOWN_STALE_CONFIGURATIONS (issue #138)"
            );
        } else {
            assert!(
                !matches!(state, ConfigurationHashState::Drifted { .. }),
                "{stem} drifted from the current adapter configuration: {state:?}"
            );
        }
    }
    assert_eq!(
        seen_stale,
        KNOWN_STALE_CONFIGURATIONS
            .iter()
            .map(ToString::to_string)
            .collect::<BTreeSet<_>>(),
        "every KNOWN_STALE_CONFIGURATIONS entry must name a committed report"
    );
}
