//! Regression tests for `crate::batch`: the resumable execution contract.

use crate::batch::{
    BatchAnalyzer, BatchKernel, BatchState, MANIFEST_SCHEMA_VERSION, SliceState, run_batch,
};
use crate::cases::fixture_revision;
use crate::report::write_and_validate_report_in;
use crate::report::{current_configuration_paths, hash_paths};
use crate::tests::support::{ReportSweepFixture, unique_test_dir};
use anyhow::{Result, bail};
use serde_json::Value;
use std::{
    cell::RefCell,
    fs,
    os::unix::fs::PermissionsExt,
    path::{Path, PathBuf},
    process::Command,
};

const MANIFEST: &str = "batch-manifest.json";
const IDENTITY: TestIdentity = TestIdentity {
    version: "bifrost 1.0.0",
    build_identity: "test-build-1",
};

struct TestIdentity {
    version: &'static str,
    build_identity: &'static str,
}

fn fixture() -> ReportSweepFixture {
    let fixture = ReportSweepFixture::new();
    fs::write(
        fixture.root.join("bifrost"),
        b"#!/bin/sh\ncase \"$1\" in\n  --version) echo 'bifrost 1.0.0' ;;\n  --build-identity) echo 'test-build-1' ;;\nesac\n",
    )
    .unwrap();
    fs::set_permissions(
        fixture.root.join("bifrost"),
        fs::Permissions::from_mode(0o755),
    )
    .unwrap();
    let run = |args: &[&str]| {
        let status = Command::new("git")
            .args(args)
            .current_dir(&fixture.root)
            .status()
            .unwrap();
        assert!(status.success(), "git {args:?} failed");
    };
    run(&["init", "--quiet"]);
    run(&["config", "user.name", "DataFlowBench Tests"]);
    run(&["config", "user.email", "tests@dataflowbench.invalid"]);
    run(&["config", "commit.gpgsign", "false"]);
    run(&["add", "bifrost"]);
    run(&["commit", "--quiet", "-m", "batch fixture"]);
    fixture
}

fn measured_configuration_hash(kernel: BatchKernel) -> String {
    let mut case_scan = None;
    let paths = current_configuration_paths(
        &format!("bifrost-{}-kernel", kernel_key(kernel)),
        &mut case_scan,
    )
    .unwrap()
    .unwrap();
    hash_paths(&paths).unwrap()
}

fn fake_report(kernel: BatchKernel, outcome: &str) -> Value {
    let mut report = ReportSweepFixture::report("reports/raw/own-kernel/case.json");
    report["tool"] = Value::String("bifrost".to_string());
    report["tool_version"] = IDENTITY.version.into();
    report["tool_build_identity"] = IDENTITY.build_identity.into();
    report["adapter_version"] = env!("CARGO_PKG_VERSION").into();
    report["fixture_revision"] = fixture_revision().unwrap().into();
    report["configuration_hash"] = measured_configuration_hash(kernel).into();
    report["results"][0]["outcome"] = outcome.into();
    report
}

fn publish(root: &Path, kernel: BatchKernel, outcome: &str) -> Result<()> {
    let relative = kernel_report(kernel);
    let raw = root.join("reports/raw/own-kernel/case.json");
    fs::create_dir_all(raw.parent().unwrap())?;
    if !raw.exists() {
        fs::write(raw, b"{}\n")?;
    }
    write_and_validate_report_in(root, &relative, &fake_report(kernel, outcome))?;
    Ok(())
}

fn kernel_report(kernel: BatchKernel) -> PathBuf {
    PathBuf::from(format!(
        "reports/bifrost-{}-kernel.json",
        kernel_key(kernel)
    ))
}

fn kernel_key(kernel: BatchKernel) -> &'static str {
    match kernel {
        BatchKernel::Java => "java",
        BatchKernel::Javascript => "javascript",
        _ => unreachable!("tests use Java and JavaScript only"),
    }
}

#[test]
fn interrupted_report_publication_is_recovered_without_rerunning() {
    let root = fixture();
    publish(&root.root, BatchKernel::Java, "reached").unwrap();
    let manifest = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java],
        Path::new(MANIFEST),
        |_, _| bail!("executor must not run"),
    )
    .unwrap();
    assert_eq!(manifest.state, BatchState::Validated);
    assert_eq!(manifest.kernels["java"].state, SliceState::Completed);
    assert_eq!(manifest.kernels["java"].attempts, 0);
    let validated: Value =
        serde_json::from_str(&fs::read_to_string(root.root.join(MANIFEST)).unwrap()).unwrap();
    assert_eq!(validated["state"], "validated");
    assert_eq!(validated["validation"]["state"], "passed");
}

#[test]
fn failed_slices_retry_and_completed_reports_are_untouched() {
    let root = fixture();
    publish(&root.root, BatchKernel::Java, "reached").unwrap();
    let first = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java, BatchKernel::Javascript],
        Path::new(MANIFEST),
        |_, kernel| {
            assert_eq!(kernel, BatchKernel::Javascript);
            bail!("planned execution failure");
        },
    )
    .unwrap();
    assert_eq!(first.state, BatchState::Failed);
    assert_eq!(first.kernels["java"].state, SliceState::Completed);
    assert_eq!(first.kernels["javascript"].state, SliceState::Failed);

    let java_before = fs::read(root.root.join(kernel_report(BatchKernel::Java))).unwrap();
    let calls = RefCell::new(0);
    let second = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java, BatchKernel::Javascript],
        Path::new(MANIFEST),
        |_, kernel| {
            *calls.borrow_mut() += 1;
            publish(&root.root, kernel, "not-reached")
        },
    )
    .unwrap();
    assert_eq!(*calls.borrow(), 1);
    assert_eq!(second.state, BatchState::Validated);
    assert_eq!(second.kernels["javascript"].state, SliceState::Completed);
    assert_eq!(
        java_before,
        fs::read(root.root.join(kernel_report(BatchKernel::Java))).unwrap()
    );
}

#[test]
fn identity_drift_fails_closed_without_touching_reports() {
    let root = fixture();
    publish(&root.root, BatchKernel::Java, "reached").unwrap();
    let manifest = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java],
        Path::new(MANIFEST),
        |_, _| Ok(()),
    )
    .unwrap();
    let path = root.root.join(MANIFEST);
    let mut stale: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
    stale["analyzer_identity"]["sha256"] = "drifted".into();
    fs::write(&path, serde_json::to_vec_pretty(&stale).unwrap()).unwrap();
    let before = fs::read(root.root.join(kernel_report(BatchKernel::Java))).unwrap();
    let error = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java],
        Path::new(MANIFEST),
        |_, _| bail!("must not execute after drift"),
    )
    .unwrap_err();
    assert!(error.to_string().contains("binary digest changed"));
    assert_eq!(
        before,
        fs::read(root.root.join(kernel_report(BatchKernel::Java))).unwrap()
    );
    let resumed: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
    assert_eq!(resumed, stale);
    assert_eq!(manifest.schema_version, MANIFEST_SCHEMA_VERSION);
}

#[test]
fn incomplete_and_validation_failures_are_typed() {
    let root = fixture();
    let first = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java],
        Path::new(MANIFEST),
        |_, kernel| publish(&root.root, kernel, "inconclusive"),
    )
    .unwrap();
    assert_eq!(first.state, BatchState::Validated);
    assert_eq!(first.kernels["java"].state, SliceState::Completed);
    assert_eq!(
        first.kernels["java"].outcomes.as_ref().unwrap()["inconclusive"],
        1
    );
    assert_eq!(first.kernels["java"].attempts, 1);

    // A completed-but-invalid report set records validation failure without
    // mistaking it for execution progress.
    let second = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java],
        Path::new(MANIFEST),
        |_, _| bail!("typed analyzer incompleteness must not rerun"),
    )
    .unwrap();
    assert_eq!(second.state, BatchState::Validated);
    assert_eq!(second.kernels["java"].attempts, 1);
    let mut malformed = ReportSweepFixture::report("reports/raw/own-kernel/case.json");
    malformed.as_object_mut().unwrap().remove("tool");
    fs::write(
        root.root.join("reports/broken.json"),
        serde_json::to_vec_pretty(&malformed).unwrap(),
    )
    .unwrap();
    let third = run_batch(
        &root.root,
        BatchAnalyzer::Bifrost,
        &root.root.join("bifrost"),
        &[BatchKernel::Java],
        Path::new(MANIFEST),
        |_, _| bail!("validation failure must not rerun"),
    )
    .unwrap();
    assert_eq!(third.state, BatchState::Failed);
    assert_eq!(third.validation.as_ref().unwrap().state, "failed");
    assert_eq!(third.kernels["java"].state, SliceState::Completed);
}

#[test]
fn atomic_manifest_writes_leave_no_staging_file() {
    let root = unique_test_dir("dataflowbench-batch-atomic");
    fs::create_dir_all(root.join("reports/raw/own-kernel")).unwrap();
    fs::write(root.join("reports/raw/own-kernel/case.json"), b"{}\n").unwrap();
    fs::write(
        root.join("bifrost"),
        b"#!/bin/sh\ncase \"$1\" in\n  --version) echo 'bifrost 1.0.0' ;;\n  --build-identity) echo 'test-build-1' ;;\nesac\n",
    )
    .unwrap();
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut permissions = fs::metadata(root.join("bifrost")).unwrap().permissions();
        permissions.set_mode(0o755);
        fs::set_permissions(root.join("bifrost"), permissions).unwrap();
    }
    fs::set_permissions(root.join("bifrost"), fs::Permissions::from_mode(0o755)).unwrap();
    let run = |args: &[&str]| {
        let status = Command::new("git")
            .args(args)
            .current_dir(&root)
            .status()
            .unwrap();
        assert!(status.success(), "git {args:?} failed");
    };
    run(&["init", "--quiet"]);
    run(&["config", "user.name", "DataFlowBench Tests"]);
    run(&["config", "user.email", "tests@dataflowbench.invalid"]);
    run(&["config", "commit.gpgsign", "false"]);
    run(&["add", "bifrost"]);
    run(&["commit", "--quiet", "-m", "batch fixture"]);
    let manifest = run_batch(
        &root,
        BatchAnalyzer::Bifrost,
        &root.join("bifrost"),
        &[BatchKernel::Java],
        Path::new(MANIFEST),
        |_, kernel| publish(&root, kernel, "reached"),
    )
    .unwrap();
    assert_eq!(manifest.state, BatchState::Validated);
    assert!(!root.join("reports/batch-test.json.tmp").exists());
}
