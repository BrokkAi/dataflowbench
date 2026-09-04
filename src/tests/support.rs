//! Fixtures shared by more than one test module.

use crate::freeze::fixture_revision_for_manifest_cases;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{fs, path::Path, path::PathBuf, time::SystemTime, time::UNIX_EPOCH};

/// A stand-in for the identity a run reads from the pinned binary.
///
/// A test has no binary to witness, so it passes this and then asserts the
/// retained rationale names *it*. That is the property under test: the
/// identity a report and its decisions carry is threaded in from a
/// measurement, and no constant inside the partition can supply one.
pub(crate) const WITNESSED_IDENTITY: &str = "witnessed-tool-identity-under-test";

/// Creates a fresh scratch directory under the system temp dir. Parallel
/// test threads share a pid and can observe the same nanosecond timestamp,
/// so a process-wide counter disambiguates, and `create_dir` (not
/// `create_dir_all`) atomically claims the path so a leftover directory
/// from a prior run is never silently reused.
pub(crate) fn unique_test_dir(prefix: &str) -> PathBuf {
    use std::sync::atomic::{AtomicU64, Ordering};
    static COUNTER: AtomicU64 = AtomicU64::new(0);
    loop {
        let unique = format!(
            "{prefix}-{}-{}-{}",
            std::process::id(),
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .unwrap()
                .as_nanos(),
            COUNTER.fetch_add(1, Ordering::Relaxed),
        );
        let root = std::env::temp_dir().join(unique);
        match fs::create_dir(&root) {
            Ok(()) => return root,
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(error) => panic!("creating scratch dir {}: {error}", root.display()),
        }
    }
}

pub(crate) struct FreezeFixture {
    pub(crate) root: PathBuf,
    pub(crate) manifest: PathBuf,
    pub(crate) report: PathBuf,
    pub(crate) raw: PathBuf,
}

impl FreezeFixture {
    pub(crate) fn new(outcome: &str, raw: Value) -> Self {
        let root = unique_test_dir("dataflowbench-freeze-test");
        fs::create_dir_all(root.join("schemas")).unwrap();
        fs::create_dir_all(root.join("cases/taint/test")).unwrap();
        fs::create_dir_all(root.join("reports/raw")).unwrap();
        for schema in [
            "case.schema.json",
            "result.schema.json",
            "freeze.schema.json",
        ] {
            fs::copy(
                Path::new("schemas").join(schema),
                root.join("schemas").join(schema),
            )
            .unwrap();
        }

        let case_relative = "cases/taint/test/case.json";
        let fixture_relative = "cases/taint/test/flow.c";
        let case_path = root.join(case_relative);
        fs::write(
            &case_path,
            serde_json::to_vec_pretty(&json!({
                "schema_version": 2,
                "id": "dfb-taint-test",
                "template_id": "dfb-template-test",
                "polarity": "positive",
                "score_tier": "core",
                "track": "taint",
                "language": "c",
                "semantic_dimensions": ["local-flow"],
                "feature_tags": ["intraprocedural"],
                "model_profile": "benchmark-controlled",
                "fixture_files": ["flow.c"],
                "source_anchors": [{"marker": "DFB-SOURCE: input", "file": "flow.c"}],
                "sink_anchors": [{"marker": "DFB-SINK: sink", "file": "flow.c"}],
                "expected_flows": [{"source": "DFB-SOURCE: input", "sink": "DFB-SINK: sink"}],
                "expected_nonflows": [],
                "expected_analysis_capability": {"kind": "intraprocedural-taint"},
                "execution_budget": {"wall_clock_seconds": 1},
                "fixture_provenance": {
                    "kind": "authored", "origin": "test", "revision": "test", "license": "MIT"
                },
                "tool_model_references": {}
            }))
            .unwrap(),
        )
        .unwrap();
        fs::write(
            root.join(fixture_relative),
            "/* DFB-SOURCE: input DFB-SINK: sink */\n",
        )
        .unwrap();

        let selected_case = (case_relative.to_string(), case_path.clone());
        let fixture_revision =
            fixture_revision_for_manifest_cases(&root, std::slice::from_ref(&selected_case))
                .unwrap();
        let raw_relative = "reports/raw/test.json";
        let raw_path = root.join(raw_relative);
        fs::write(&raw_path, serde_json::to_vec_pretty(&raw).unwrap()).unwrap();
        let report_relative = "reports/test.json";
        let report_path = root.join(report_relative);
        let report = json!({
            "schema_version": 1,
            "tool": "test-tool",
            "tool_version": "1.0.0",
            "tool_build_identity": "test-build-1",
            "adapter_version": "1.0.0",
            "configuration_hash": "0000000000000000000000000000000000000000000000000000000000000000",
            "fixture_revision": fixture_revision,
            "started_at_unix_seconds": 1,
            "ended_at_unix_seconds": 2,
            "cold_or_warm": "cold",
            "results": [{
                "case_id": "dfb-taint-test",
                "outcome": outcome,
                "source_anchors": ["DFB-SOURCE: input"],
                "sink_anchors": ["DFB-SINK: sink"],
                "witness_checkpoints": [],
                "diagnostics": [],
                "duration_ms": 1,
                "peak_memory_mb": null,
                "raw_output": raw_relative
            }]
        });
        fs::write(&report_path, serde_json::to_vec_pretty(&report).unwrap()).unwrap();

        let case_bytes = fs::read(&case_path).unwrap();
        let fixture_bytes = fs::read(root.join(fixture_relative)).unwrap();
        let report_bytes = fs::read(&report_path).unwrap();
        let raw_bytes = fs::read(&raw_path).unwrap();
        let digest = |bytes: &[u8]| format!("{:x}", Sha256::digest(bytes));
        let manifest = json!({
            "schema_version": 1,
            "benchmark": {
                "revision": "a".repeat(40),
                "release": "development",
                "case_schema_version": 2,
                "result_schema_version": 1,
                "fixture_revision": fixture_revision,
                "dirty": false
            },
            "claim": {
                "scope": "development",
                "tracks": ["taint"],
                "dimensions": ["taint"],
                "exclusions": [],
                "score_tiers": ["core"],
                "model_profiles": ["benchmark-controlled"]
            },
            "cases": [{
                "id": "dfb-taint-test", "path": case_relative, "sha256": digest(&case_bytes),
                "fixture_digests": [{"path": fixture_relative, "sha256": digest(&fixture_bytes)}],
                "track": "taint", "score_tier": "core", "model_profile": "benchmark-controlled",
                "template_id": "dfb-template-test", "polarity": "positive"
            }],
            "adapters": [{
                "id": "test", "tool": "test-tool", "tool_version": "1.0.0",
                "build_identity": "test-build-1", "adapter_version": "1.0.0",
                "configuration_hash": "0000000000000000000000000000000000000000000000000000000000000000",
                "track": "taint", "dimension": "taint", "model_profile": "benchmark-controlled"
            }],
            "reports": [{
                "path": report_relative, "sha256": digest(&report_bytes),
                "normalized_report_sha256": digest(&report_bytes), "adapter": "test",
                "track": "taint", "dimension": "taint", "model_profile": "benchmark-controlled",
                "case_ids": ["dfb-taint-test"], "outcomes": [{"case_id": "dfb-taint-test", "outcome": outcome}],
                "raw_evidence": [{"case_id": "dfb-taint-test", "path": raw_relative, "sha256": digest(&raw_bytes)}]
            }]
        });
        let manifest_path = root.join("reports/freeze.json");
        fs::write(
            &manifest_path,
            serde_json::to_vec_pretty(&manifest).unwrap(),
        )
        .unwrap();
        Self {
            root,
            manifest: manifest_path,
            report: report_path,
            raw: raw_path,
        }
    }

    pub(crate) fn read_manifest(&self) -> Value {
        serde_json::from_slice(&fs::read(&self.manifest).unwrap()).unwrap()
    }

    pub(crate) fn write_manifest(&self, manifest: &Value) {
        fs::write(&self.manifest, serde_json::to_vec_pretty(manifest).unwrap()).unwrap();
    }

    pub(crate) fn refresh_report_digest(&self, manifest: &mut Value) {
        let digest = format!("{:x}", Sha256::digest(fs::read(&self.report).unwrap()));
        manifest["reports"][0]["sha256"] = json!(digest);
        manifest["reports"][0]["normalized_report_sha256"] = json!(digest);
    }
}

impl Drop for FreezeFixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

/// A scratch benchmark root holding an "own" kernel report and a
/// concurrently running "other" kernel's report, for exercising the
/// end-of-run report sweep.
pub(crate) struct ReportSweepFixture {
    pub(crate) root: PathBuf,
}

impl ReportSweepFixture {
    pub(crate) fn new() -> Self {
        let root = unique_test_dir("dataflowbench-report-sweep-test");
        fs::create_dir_all(root.join("reports/raw/own-kernel")).unwrap();
        fs::create_dir_all(root.join("reports/raw/other-kernel")).unwrap();
        Self { root }
    }

    pub(crate) fn report(raw_relative: &str) -> Value {
        json!({
            "schema_version": 1,
            "tool": "test-tool",
            "tool_version": "1.0.0",
            "tool_build_identity": "test-build-1",
            "adapter_version": "1.0.0",
            "configuration_hash": "0".repeat(64),
            "fixture_revision": "test",
            "started_at_unix_seconds": 1,
            "ended_at_unix_seconds": 2,
            "cold_or_warm": "cold",
            "results": [{
                "case_id": "dfb-taint-test",
                "outcome": "reached",
                "source_anchors": ["DFB-SOURCE: input"],
                "sink_anchors": ["DFB-SINK: sink"],
                "witness_checkpoints": [],
                "diagnostics": [],
                "duration_ms": 1,
                "peak_memory_mb": null,
                "raw_output": raw_relative
            }]
        })
    }

    pub(crate) fn write_report(&self, name: &str, report: &Value) -> PathBuf {
        let path = self.root.join("reports").join(name);
        fs::write(&path, serde_json::to_vec_pretty(report).unwrap()).unwrap();
        path
    }

    pub(crate) fn write_raw(&self, raw_relative: &str) {
        fs::write(self.root.join(raw_relative), "{}\n").unwrap();
    }
}

impl Drop for ReportSweepFixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}
