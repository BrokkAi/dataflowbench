//! Regression tests for `crate::report`.

use crate::adapters::ToolIdentity;
use crate::adapters::bifrost::normalize_bifrost as normalize_bifrost_report;
use crate::evidence::AnchorDialect;
use crate::report::{
    ConfigurationHashState, KNOWN_STALE_CONFIGURATIONS, configuration_hash_state,
    configuration_hash_state_for_report, current_configuration_paths, hash_paths,
    known_stale_issue, validate_reports, validate_reports_in, write_and_validate_report_in,
};
use crate::runtime::{write_case_phase_timings, write_run_environment};
use crate::tests::support::{ReportSweepFixture, unique_test_dir};
use anyhow::Result;
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, time::Duration};

/// Keep legacy normalization fixtures explicitly on Bifrost schema 4 while
/// production report parsing requires a witnessed report schema.
fn normalize_bifrost(
    case_path: &Path,
    case: &Value,
    report: &Value,
    status: Option<i32>,
    dialect: AnchorDialect,
) -> Result<(&'static str, Vec<String>, Vec<Value>)> {
    let mut report = report.clone();
    if report.get("schema_version").is_none() {
        report["schema_version"] = json!(4);
    }
    normalize_bifrost_report(case_path, case, &report, status, dialect)
}

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

#[test]
pub(crate) fn codeql_configuration_hashes_follow_the_reported_tool_version() {
    let mut case_scan = None;
    let historical: Value =
        serde_json::from_str(&fs::read_to_string("reports/codeql-java-kernel.json").unwrap())
            .unwrap();
    let stamped = historical["configuration_hash"].as_str().unwrap();
    assert_eq!(historical["tool_version"], "2.27.0");
    assert_eq!(
        configuration_hash_state_for_report(
            "codeql-java-kernel",
            "2.27.0",
            historical["adapter_version"].as_str().unwrap(),
            stamped,
            &mut case_scan,
        )
        .unwrap(),
        ConfigurationHashState::Current,
        "the frozen CLI profile must retain its original configuration bytes"
    );

    let prospective = current_configuration_paths("codeql-java-kernel", &mut case_scan)
        .unwrap()
        .expect("the current CodeQL kernel profile is derivable");
    assert!(prospective.contains(Path::new("adapters/codeql/v0.9.2/profile.json")));
    assert_ne!(hash_paths(&prospective).unwrap(), stamped);
    let prospective_hash = hash_paths(&prospective).unwrap();
    assert_eq!(
        configuration_hash_state_for_report(
            "codeql-java-kernel",
            crate::adapters::pins::CODEQL_VERSION,
            historical["adapter_version"].as_str().unwrap(),
            &prospective_hash,
            &mut case_scan,
        )
        .unwrap(),
        ConfigurationHashState::Current
    );
    let baseline: Value =
        serde_json::from_slice(&fs::read("reports/freeze.json").unwrap()).unwrap();
    let baseline_java = baseline["adapters"]
        .as_array()
        .unwrap()
        .iter()
        .find(|adapter| adapter["id"] == "codeql-java-kernel")
        .expect("the checked-in baseline freeze includes CodeQL Java");
    assert_eq!(baseline_java["tool_version"], "2.27.1");
    assert_eq!(
        configuration_hash_state_for_report(
            "codeql-java-kernel",
            baseline_java["tool_version"].as_str().unwrap(),
            baseline_java["adapter_version"].as_str().unwrap(),
            baseline_java["configuration_hash"].as_str().unwrap(),
            &mut case_scan,
        )
        .unwrap(),
        ConfigurationHashState::Current,
        "the v0.9.0/v0.9.1 baseline freeze keeps its witnessed 2.27.1 path closure"
    );
    assert!(
        configuration_hash_state_for_report(
            "codeql-java-kernel",
            "2.27.9",
            historical["adapter_version"].as_str().unwrap(),
            stamped,
            &mut case_scan,
        )
        .is_err(),
        "unknown CodeQL versions must not inherit another version's profile"
    );
    assert!(
        configuration_hash_state_for_report(
            "codeql-swift-kernel",
            crate::adapters::pins::CODEQL_VERSION,
            "not-the-v092-adapter",
            stamped,
            &mut case_scan,
        )
        .is_err(),
        "Swift 2.27.2 reports must bind the new adapter identity"
    );
    assert_eq!(
        configuration_hash_state_for_report(
            "codeql-swift-kernel",
            "2.27.9",
            "unknown-historical-adapter",
            stamped,
            &mut case_scan,
        )
        .unwrap(),
        ConfigurationHashState::NotDerivable,
        "unregistered historical common-Swift closures stay honestly non-derivable"
    );
}

#[test]
pub(crate) fn v092_common_swift_partition_hashes_follow_the_registered_plan_without_rederiving_old_native_freezes()
 {
    let mut case_scan = None;
    let current_partitions = [
        (
            "codeql-swift-kernel",
            crate::adapters::pins::CODEQL_VERSION,
            "swift-normal-v092",
        ),
        (
            "codeql-swift-core",
            crate::adapters::pins::CODEQL_VERSION,
            "swift-normal-v092",
        ),
        (
            "codeql-swift-modeling",
            crate::adapters::pins::CODEQL_VERSION,
            "swift-normal-v092",
        ),
        (
            "codeql-swift-calibration",
            crate::adapters::pins::CODEQL_VERSION,
            "swift-normal-v092",
        ),
        (
            "codeql-swift-native",
            crate::adapters::pins::CODEQL_VERSION,
            "swift-normal-v092",
        ),
        (
            "codeql-swift-language-extension",
            crate::adapters::pins::CODEQL_VERSION,
            "swift-normal-v092",
        ),
        (
            "joern-swift-kernel",
            crate::adapters::pins::JOERN_VERSION,
            "joern-normal-v092",
        ),
        (
            "joern-swift-core",
            crate::adapters::pins::JOERN_VERSION,
            "joern-normal-v092",
        ),
        (
            "joern-swift-modeling",
            crate::adapters::pins::JOERN_VERSION,
            "joern-normal-v092",
        ),
        (
            "joern-swift-calibration",
            crate::adapters::pins::JOERN_VERSION,
            "joern-normal-v092",
        ),
        (
            "joern-swift-native",
            crate::adapters::pins::JOERN_VERSION,
            "joern-normal-v092",
        ),
        (
            "joern-swift-language-extension",
            crate::adapters::pins::JOERN_VERSION,
            "joern-normal-v092",
        ),
    ];

    for (stem, tool_version, adapter_version) in current_partitions {
        let stamped = "0".repeat(64);
        let current = match configuration_hash_state_for_report(
            stem,
            tool_version,
            adapter_version,
            &stamped,
            &mut case_scan,
        )
        .unwrap()
        {
            ConfigurationHashState::Drifted { current } => current,
            state => panic!("{stem} must resolve the v0.9.2 plan closure, got {state:?}"),
        };
        assert_eq!(
            configuration_hash_state_for_report(
                stem,
                tool_version,
                adapter_version,
                &current,
                &mut case_scan,
            )
            .unwrap(),
            ConfigurationHashState::Current,
            "{stem} must compare against its registered v0.9.2 configuration closure"
        );
    }
}

#[test]
pub(crate) fn historical_common_swift_core_native_and_extension_freezes_remain_not_derivable() {
    let mut case_scan = None;
    let freeze: Value = serde_json::from_slice(&fs::read("reports/freeze.json").unwrap()).unwrap();
    let historical_native_partitions = [
        ("codeql-swift-core", "codeql-swift-core"),
        ("codeql-swift-native", "codeql-swift-native"),
        (
            "codeql-swift-language-extension",
            "codeql-swift-language-extension",
        ),
        ("joern-swift-core", "joern-swift-core"),
        ("joern-swift-native", "joern-swift-native"),
        (
            "joern-swift-language-extension",
            "joern-swift-language-extension",
        ),
    ];
    for (stem, adapter_id) in historical_native_partitions {
        let frozen = freeze["adapters"]
            .as_array()
            .unwrap()
            .iter()
            .find(|adapter| adapter["id"] == adapter_id)
            .unwrap_or_else(|| panic!("the historical freeze must retain {adapter_id}"));
        assert_eq!(
            configuration_hash_state_for_report(
                stem,
                frozen["tool_version"].as_str().unwrap(),
                frozen["adapter_version"].as_str().unwrap(),
                frozen["configuration_hash"].as_str().unwrap(),
                &mut case_scan,
            )
            .unwrap(),
            ConfigurationHashState::NotDerivable,
            "{adapter_id} has no original repository-local closure and stays honestly non-derivable"
        );
    }
}

/// Every committed report whose configuration hash is derivable in-repo
/// still matches the current configuration — except the populations
/// `KNOWN_STALE_CONFIGURATIONS` records against their tracking issues, each of which
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
        let state = configuration_hash_state_for_report(
            &stem,
            report["tool_version"].as_str().unwrap(),
            report["adapter_version"].as_str().unwrap(),
            stamped,
            &mut case_scan,
        )
        .unwrap();
        if let Some(issue) = known_stale_issue(&stem) {
            seen_stale.insert(stem.clone());
            assert!(
                matches!(state, ConfigurationHashState::Drifted { .. }),
                "{stem} no longer drifts; remove it from KNOWN_STALE_CONFIGURATIONS (issue {issue})"
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
            .map(|(stem, _)| stem.to_string())
            .collect::<BTreeSet<_>>(),
        "every KNOWN_STALE_CONFIGURATIONS entry must name a committed report"
    );
}
