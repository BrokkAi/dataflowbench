//! Regression tests for `crate::runtime`.

use crate::adapters::ToolIdentity;
use crate::freeze::raw_special_outcome;
use crate::runtime::{
    case_timing_path, clear_stale_case_timing, witnessed_version_line, write_case_phase_timings,
    write_run_environment,
};
use crate::tests::support::unique_test_dir;
use serde_json::Value;
use std::{fs, time::Duration};

/// The sidecar retains what the runner witnessed and nothing an outcome
/// could ever read: even a timing document mistakenly consulted as raw
/// evidence declares no special outcome, and a re-run that skips the
/// analyzer clears the previous run's sidecar.
#[test]
pub(crate) fn timing_sidecar_is_additive_metadata_never_an_outcome_input() {
    let root = unique_test_dir("dataflowbench-timing-test");
    write_case_phase_timings(
        &root,
        "codeql",
        "dfb-taint-test",
        &[
            ("database-create", Duration::from_millis(2500)),
            ("database-analyze", Duration::from_millis(410)),
        ],
    )
    .unwrap();
    let path = case_timing_path(&root, "dfb-taint-test");
    let sidecar: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
    assert_eq!(sidecar["schema_version"], 1);
    assert_eq!(sidecar["adapter"], "codeql");
    assert_eq!(sidecar["case_id"], "dfb-taint-test");
    assert_eq!(sidecar["clock"], "monotonic");
    assert_eq!(sidecar["evidence_kind"], "retained-phase-timing");
    assert_eq!(sidecar["phases"][0]["phase"], "database-create");
    assert_eq!(sidecar["phases"][0]["wall_ms"], 2500);
    assert_eq!(sidecar["phases"][1]["phase"], "database-analyze");
    assert_eq!(sidecar["phases"][1]["wall_ms"], 410);
    // No timing value can ever be read as a correctness signal.
    assert_eq!(raw_special_outcome(&sidecar), None);
    clear_stale_case_timing(&root, "dfb-taint-test").unwrap();
    assert!(!path.exists());
    let _ = fs::remove_dir_all(&root);
}

/// The per-run environment stamp names the machine and the witnessed tool
/// identity, so per-case timings in the directory are attributable to one
/// environment without re-measurement.
#[test]
pub(crate) fn run_environment_stamp_pairs_machine_with_witnessed_identity() {
    let root = unique_test_dir("dataflowbench-environment-test");
    write_run_environment(
        &root,
        "bifrost",
        &ToolIdentity::new("0.10.8", "bifrost-build"),
    )
    .unwrap();
    let stamp: Value =
        serde_json::from_str(&fs::read_to_string(root.join("run-environment.json")).unwrap())
            .unwrap();
    assert_eq!(stamp["schema_version"], 1);
    assert_eq!(stamp["tool"], "bifrost");
    assert_eq!(stamp["witnessed_tool_version"], "0.10.8");
    assert!(stamp["witnessed_tool_version_banner"].is_null());
    assert_eq!(stamp["witnessed_tool_build_identity"], "bifrost-build");
    assert_eq!(stamp["os"], std::env::consts::OS);
    assert_eq!(stamp["evidence_kind"], "retained-run-environment");
    assert!(stamp["hardware_model"].is_string());
    assert!(stamp["cpu_count"].is_u64() || stamp["cpu_count"].is_null());
    let _ = fs::remove_dir_all(&root);
}

/// A `--version` banner that says more than the version (Bifrost 0.10.9 lists
/// its built-in policy packs beneath the version line) stamps the version line
/// alone as the witnessed version and retains the whole banner beside it, so
/// neither the report nor the environment loses what the binary said.
#[test]
pub(crate) fn multi_line_version_banner_is_split_into_line_and_retained_banner() {
    let banner = "bifrost 0.10.9\nbuiltin-policy-pack bifrost.code-smells@2.10.0 policies=16\nbuiltin-policy-catalog sha256=aea2ad0c\n";
    assert_eq!(witnessed_version_line(banner), "bifrost 0.10.9");
    assert_eq!(
        witnessed_version_line("  bifrost 0.10.8  "),
        "bifrost 0.10.8"
    );
    assert_eq!(witnessed_version_line(""), "");
    // The identity a report carries is called down to the version line only
    // after the banner has been stamped whole.
    assert_eq!(
        ToolIdentity::new(banner, "bifrost-build")
            .version_line_only()
            .version,
        "bifrost 0.10.9"
    );
    let root = unique_test_dir("dataflowbench-environment-banner-test");
    write_run_environment(
        &root,
        "bifrost",
        &ToolIdentity::new(banner, "bifrost-build"),
    )
    .unwrap();
    let stamp: Value =
        serde_json::from_str(&fs::read_to_string(root.join("run-environment.json")).unwrap())
            .unwrap();
    assert_eq!(stamp["witnessed_tool_version"], "bifrost 0.10.9");
    assert_eq!(stamp["witnessed_tool_version_banner"], banner.trim());
    let _ = fs::remove_dir_all(&root);
}
