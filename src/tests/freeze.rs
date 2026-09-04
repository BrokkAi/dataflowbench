//! Regression tests for `crate::freeze`.

use crate::adapters::ToolIdentity;
use crate::cases::case_paths;
use crate::freeze::{
    build_freeze_manifest, compile_schema, fixture_revision_for_manifest_cases, git_output,
    parse_raw_evidence_documents, raw_special_outcome, validate_adapter_identities,
    validate_freeze_at, validate_freeze_git_state,
};
use crate::results::generate_results_at;
use crate::runtime::{write_case_phase_timings, write_run_environment};
use crate::tests::support::FreezeFixture;
use serde_json::{Value, json};
use std::{
    collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command,
    time::Duration,
};

/// Pre-existing frozen artifacts stay valid: a freeze manifest that binds
/// timing-free raw evidence keeps validating after timing sidecars and an
/// environment stamp appear beside that evidence, because neither is part
/// of the frozen surface.
#[test]
pub(crate) fn validate_freeze_accepts_timing_metadata_beside_frozen_raw_evidence() {
    let fixture = FreezeFixture::new("reached", json!({"findings": []}));
    validate_freeze_at(&fixture.root, &fixture.manifest, false).unwrap();
    let raw_dir = fixture.root.join("reports/raw");
    write_case_phase_timings(
        &raw_dir,
        "test-tool",
        "dfb-taint-test",
        &[("total", Duration::from_millis(75))],
    )
    .unwrap();
    write_run_environment(
        &raw_dir,
        "test-tool",
        &ToolIdentity::new("1.0.0", "test-build-1"),
    )
    .unwrap();
    validate_freeze_at(&fixture.root, &fixture.manifest, false).unwrap();
}

#[test]
pub(crate) fn freeze_schema_is_versioned_and_compiles() {
    let schema = compile_schema(Path::new("schemas/freeze.schema.json")).unwrap();
    let invalid = json!({"schema_version": 2});
    assert!(schema.validate(&invalid).is_err());
}

#[test]
pub(crate) fn freeze_fixture_revision_is_order_independent() {
    let paths = case_paths();
    let selected = paths
        .iter()
        .take(2)
        .map(|path| (path.to_string_lossy().to_string(), path.clone()))
        .collect::<Vec<_>>();
    let mut reversed = selected.clone();
    reversed.reverse();
    assert_eq!(
        fixture_revision_for_manifest_cases(Path::new("."), &selected).unwrap(),
        fixture_revision_for_manifest_cases(Path::new("."), &reversed).unwrap()
    );
}

/// Every checked-in normalized report must declare the fixture revision of
/// the freeze it is published under. Comparing against the freeze — rather
/// than against `fixture_revision()` over the working tree — is the
/// invariant `validate_freeze` and `create_freeze` actually enforce, and it
/// stays meaningful while a new language kernel is authored but not yet
/// re-run and re-frozen. Once a release freeze is assembled, `create_freeze`
/// still refuses reports that predate the selected case population, so a
/// grown benchmark cannot be published without re-running every adapter.
#[test]
pub(crate) fn checked_reports_match_the_frozen_fixture_revision() {
    let freeze: Value =
        serde_json::from_str(&fs::read_to_string("reports/freeze.json").unwrap()).unwrap();
    let frozen_revision = freeze["benchmark"]["fixture_revision"].as_str().unwrap();
    assert!(
        frozen_revision
            .strip_prefix("sha256:")
            .is_some_and(|digest| digest.len() == 64)
    );
    let frozen_reports = freeze["reports"]
        .as_array()
        .unwrap()
        .iter()
        .map(|report| report["path"].as_str().unwrap())
        .collect::<BTreeSet<_>>();
    assert!(!frozen_reports.is_empty());
    for path in frozen_reports {
        let report: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        assert_eq!(
            report["fixture_revision"].as_str(),
            Some(frozen_revision),
            "{path} does not declare the frozen fixture revision"
        );
    }
}

#[test]
pub(crate) fn raw_evidence_may_be_one_document_or_json_lines_and_the_audit_reads_both() {
    let single = parse_raw_evidence_documents(br#"{"state": "unsupported"}"#).unwrap();
    assert_eq!(single.len(), 1);
    assert_eq!(
        single.iter().find_map(raw_special_outcome),
        Some("unsupported")
    );

    let lines = parse_raw_evidence_documents(
        b"{\"file_version\":3}\n{\"kind\":\"model\"}\n{\"state\":\"inconclusive\"}\n",
    )
    .unwrap();
    assert_eq!(lines.len(), 3);
    assert_eq!(
        lines.iter().find_map(raw_special_outcome),
        Some("inconclusive")
    );

    let clean =
        parse_raw_evidence_documents(b"{\"file_version\":3}\n{\"kind\":\"issue\"}\n").unwrap();
    assert_eq!(clean.iter().find_map(raw_special_outcome), None);

    assert!(parse_raw_evidence_documents(b"").is_err());
    assert!(parse_raw_evidence_documents(b"{\"a\":1}\nnot json\n").is_err());
}

#[test]
pub(crate) fn raw_special_outcomes_cannot_be_downgraded_to_clean_negatives() {
    assert_eq!(
        raw_special_outcome(&json!({"state": "unsupported"})),
        Some("unsupported")
    );
    assert_eq!(
        raw_special_outcome(&json!({"state": "runner-error"})),
        Some("runner-error")
    );
    assert_eq!(
        raw_special_outcome(&json!({"runs": [{"completion": {"type": "inconclusive"}}]})),
        Some("inconclusive")
    );
    assert_eq!(raw_special_outcome(&json!({"findings": []})), None);
}

#[test]
pub(crate) fn freeze_rejects_missing_raw_evidence() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    fs::remove_file(&fixture.raw).unwrap();
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
}

#[test]
pub(crate) fn freeze_rejects_altered_fixture_bytes() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
}

#[test]
pub(crate) fn freeze_rejects_mixed_fixture_revision() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let mut report: Value = serde_json::from_slice(&fs::read(&fixture.report).unwrap()).unwrap();
    report["fixture_revision"] =
        json!("sha256:ffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff");
    fs::write(&fixture.report, serde_json::to_vec_pretty(&report).unwrap()).unwrap();
    let mut manifest = fixture.read_manifest();
    fixture.refresh_report_digest(&mut manifest);
    fixture.write_manifest(&manifest);
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
}

#[test]
pub(crate) fn freeze_rejects_profile_or_track_pooling() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let mut manifest = fixture.read_manifest();
    manifest["adapters"][0]["model_profile"] = json!("tool-native");
    manifest["reports"][0]["model_profile"] = json!("tool-native");
    fixture.write_manifest(&manifest);
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());

    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let mut manifest = fixture.read_manifest();
    manifest["adapters"][0]["track"] = json!("value-flow");
    manifest["reports"][0]["track"] = json!("value-flow");
    fixture.write_manifest(&manifest);
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
}

#[test]
pub(crate) fn freeze_rejects_special_outcome_downgrade() {
    let fixture = FreezeFixture::new("unsupported", json!({"state": "unsupported"}));
    let mut report: Value = serde_json::from_slice(&fs::read(&fixture.report).unwrap()).unwrap();
    report["results"][0]["outcome"] = json!("not-reached");
    fs::write(&fixture.report, serde_json::to_vec_pretty(&report).unwrap()).unwrap();
    let mut manifest = fixture.read_manifest();
    manifest["reports"][0]["outcomes"][0]["outcome"] = json!("not-reached");
    fixture.refresh_report_digest(&mut manifest);
    fixture.write_manifest(&manifest);
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
}

#[test]
pub(crate) fn release_freeze_rejects_placeholder_analyzer_identity() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let manifest = fixture.read_manifest();
    let mut adapters = BTreeMap::new();
    adapters.insert("test".to_string(), &manifest["adapters"][0]);
    let mut release = manifest["adapters"][0].clone();
    release["tool_version"] = json!("unknown");
    let mut release_adapters = BTreeMap::new();
    release_adapters.insert("test".to_string(), &release);
    assert!(validate_adapter_identities("release", &release_adapters).is_err());
    assert!(validate_adapter_identities("development", &adapters).is_ok());
}

#[test]
pub(crate) fn freeze_rejects_dirty_checkout_state() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    assert!(
        Command::new("git")
            .args(["init", "-q"])
            .current_dir(&fixture.root)
            .status()
            .unwrap()
            .success()
    );
    assert!(
        Command::new("git")
            .args(["add", "."])
            .current_dir(&fixture.root)
            .status()
            .unwrap()
            .success()
    );
    assert!(
        Command::new("git")
            .args([
                "-c",
                "user.email=dataflowbench-test@example.invalid",
                "-c",
                "user.name=DataFlowBench Test",
                "-c",
                "commit.gpgsign=false",
                "commit",
                "-qm",
                "fixture"
            ])
            .current_dir(&fixture.root)
            .status()
            .unwrap()
            .success()
    );
    let revision = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();
    assert!(
        validate_freeze_git_state(&fixture.root, &revision, "development", "development").is_ok()
    );
    fs::write(fixture.root.join("dirty.txt"), "dirty\n").unwrap();
    assert!(
        validate_freeze_git_state(&fixture.root, &revision, "development", "development").is_err()
    );
}

#[test]
pub(crate) fn create_freeze_manifest_matches_validated_fixture() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let manifest = build_freeze_manifest(
        &fixture.root,
        &[PathBuf::from("reports/test.json")],
        "development",
        "development",
        &"a".repeat(40),
    )
    .unwrap();
    // The assembler reconstructs the hand-built fixture manifest exactly.
    assert_eq!(manifest, fixture.read_manifest());
    let assembled = fixture.root.join("reports/assembled.json");
    fs::write(&assembled, serde_json::to_vec_pretty(&manifest).unwrap()).unwrap();
    validate_freeze_at(&fixture.root, &assembled, false).unwrap();
}

#[test]
pub(crate) fn create_freeze_rejects_stale_fixture_bytes() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
    let error = build_freeze_manifest(
        &fixture.root,
        &[PathBuf::from("reports/test.json")],
        "development",
        "development",
        &"a".repeat(40),
    )
    .unwrap_err()
    .to_string();
    assert!(error.contains("re-run the adapters"), "{error}");
}

#[test]
pub(crate) fn freeze_git_state_accepts_ancestor_revisions_and_containing_tags() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    let run_git = |args: &[&str]| {
        assert!(
            Command::new("git")
                .args([
                    "-c",
                    "user.email=dataflowbench-test@example.invalid",
                    "-c",
                    "user.name=DataFlowBench Test",
                    "-c",
                    "commit.gpgsign=false",
                    "-c",
                    "tag.gpgsign=false",
                ])
                .args(args)
                .current_dir(&fixture.root)
                .status()
                .unwrap()
                .success()
        );
    };
    run_git(&["init", "-q"]);
    run_git(&["add", "."]);
    run_git(&["commit", "-qm", "evidence"]);
    let evidence = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();
    fs::write(fixture.root.join("later.txt"), "later\n").unwrap();
    run_git(&["add", "."]);
    run_git(&["commit", "-qm", "manifest"]);
    let head = git_output(&fixture.root, ["rev-parse", "HEAD"]).unwrap();

    // The evidence commit validates as an ancestor of HEAD.
    validate_freeze_git_state(&fixture.root, &evidence, "development", "development").unwrap();
    assert!(
        validate_freeze_git_state(&fixture.root, &"b".repeat(40), "development", "development")
            .is_err()
    );

    // A release tag must contain the frozen evidence revision.
    run_git(&["tag", "v0.1.0"]);
    validate_freeze_git_state(&fixture.root, &evidence, "v0.1.0", "release").unwrap();
    run_git(&["tag", "v0.0.1", &evidence]);
    assert!(validate_freeze_git_state(&fixture.root, &head, "v0.0.1", "release").is_err());
}

#[test]
pub(crate) fn generate_results_requires_a_valid_freeze() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
    let output = fixture.root.join("generated");
    assert!(generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).is_err());
    assert!(!output.exists());
}
