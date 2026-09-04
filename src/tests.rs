//! The regression suite.
//!
//! Every adapter is expected to carry, at minimum, a population-scoping test,
//! an identity-pin test, an evidence/anchor-reconciliation test, a
//! report-path-disjointness test, and an anti-vacuous-negative test. See
//! docs/adding-an-adapter.md.

use crate::adapters::bifrost::{
    BIFROST_DIRECT_POLICY, BIFROST_DIRECT_POSITIVE_POLICY, BIFROST_EXPLICIT_NEGATIVE_POLICY,
    BIFROST_JAVA_POLICY, BIFROST_JAVASCRIPT_POLICY, BIFROST_KOTLIN_POLICY,
    BIFROST_MODELING_CALL_MODELING, BIFROST_NATIVE_POLICY_PACK_FLAG, BIFROST_SCALA_POLICY,
    BifrostRun, bifrost_anchor_dialect, bifrost_policy_for, normalize_bifrost,
    require_bifrost_modeling_load_bearing, selected_bifrost_case, smoke_population_case,
};
use crate::adapters::codeql::{
    CFamilyKernel, CODEQL_C_ENDPOINT_PROBE, CODEQL_C_QUERY, CODEQL_C_RAW_DIR, CODEQL_C_REPORT,
    CODEQL_CPP_ENDPOINT_PROBE, CODEQL_CPP_QUERY, CODEQL_CPP_RAW_DIR, CODEQL_CPP_REPORT,
    CODEQL_CSHARP_ENDPOINT_PROBE, CODEQL_CSHARP_QUERY, CODEQL_CSHARP_RAW_DIR, CODEQL_CSHARP_REPORT,
    CODEQL_ENDPOINT_PROBE_RULE_SUFFIX, CODEQL_GO_ENDPOINT_PROBE, CODEQL_GO_QUERY,
    CODEQL_GO_RAW_DIR, CODEQL_GO_REPORT, CODEQL_JAVA_ENDPOINT_PROBE,
    CODEQL_JAVASCRIPT_ENDPOINT_PROBE, CODEQL_JAVASCRIPT_QUERY, CODEQL_JAVASCRIPT_RAW_DIR,
    CODEQL_JAVASCRIPT_REPORT, CODEQL_KOTLIN_ENDPOINT_PROBE, CODEQL_KOTLIN_QUERY,
    CODEQL_KOTLIN_RAW_DIR, CODEQL_KOTLIN_REPORT, CODEQL_NATIVE_QUERY_PACKS,
    CODEQL_NATIVE_SUITE_KIND, CODEQL_PYTHON_ENDPOINT_PROBE, CODEQL_PYTHON_QUERY,
    CODEQL_RUBY_ENDPOINT_PROBE, CODEQL_RUBY_QUERY, CODEQL_RUBY_RAW_DIR, CODEQL_RUBY_REPORT,
    CODEQL_RUST_ENDPOINT_PROBE, CODEQL_RUST_QUERY, CODEQL_RUST_RAW_DIR, CODEQL_RUST_REPORT,
    CODEQL_TYPESCRIPT_ENDPOINT_PROBE, CODEQL_TYPESCRIPT_QUERY, CODEQL_TYPESCRIPT_RAW_DIR,
    CODEQL_TYPESCRIPT_REPORT, CodeqlEndpointObservation, CodeqlLanguage, EcmaKernel,
    codeql_c_family_cases, codeql_csharp_cases, codeql_database_create_args,
    codeql_endpoint_probe_result, codeql_go_cases, codeql_kotlin_cases, codeql_missing_sarif_error,
    codeql_ruby_cases, codeql_rust_cases, ecma_core_case, ecma_sarif_outcome,
    modeling_codeql_language, normalize_anchored_codeql_sarif, rust_kernel_case,
    select_codeql_ecma_cases, selected_codeql_java_case, selected_codeql_python_case,
    split_codeql_endpoint_probe, unobserved_codeql_endpoint_outcome,
    validate_codeql_python_population, validate_rust_kernel_population, write_rust_cargo_manifest,
};
use crate::adapters::flowdroid::{
    FLOWDROID_ANDROID_PLATFORM_SHA256, FLOWDROID_CONFIG_DIR, FLOWDROID_ENTRY_CALL_PLACEHOLDER,
    FLOWDROID_JAR_SHA256, FLOWDROID_MODELING_SUMMARIES_DIR, FLOWDROID_MODELING_SUMMARY_FILES,
    FLOWDROID_NATIVE_CATALOG_ARGUMENT, FLOWDROID_PACKAGE_PLACEHOLDER, FLOWDROID_SINKS_PLACEHOLDER,
    FLOWDROID_SOURCES_PLACEHOLDER, FlowdroidKernel, flowdroid_completion_leaks,
    flowdroid_endpoint_signatures, flowdroid_entry_call, flowdroid_sink_definitions,
    flowdroid_template_paths, flowdroid_termination_state, parse_class_file,
    require_flowdroid_modeling_declarations, select_flowdroid_cases, witness_flowdroid_identity,
    write_stored_zip, xml_unescape, zip_crc32,
};
use crate::adapters::infer::{
    INFER_PINNED_VERSION, INFER_TAINT_RULE_ID, InferKernel, infer_config_paths,
    infer_taint_results_only, require_infer_modeling_load_bearing, select_infer_cases,
    witness_infer_identity,
};
use crate::adapters::joern::{
    JOERN_JAVA_RAW_DIR, JOERN_JAVA_REPORT, JOERN_KERNEL_SCRIPT, JOERN_MODELING_SCRIPT,
    JOERN_PHP_RAW_DIR, JOERN_WARM_BATCH_SCRIPT, JoernEndpointRule, JoernKernel, joern_flow_outcome,
    modeling_joern_frontend, modeling_joern_source_kind, select_joern_cases,
};
use crate::adapters::opentaint::{
    OPENTAINT_ANALYZER_JAR_SHA256, OPENTAINT_MODEL_RULE_ID, OPENTAINT_MODELS_ARCHIVE_SHA256,
    OPENTAINT_RULE_ID, OpentaintKernel, jvm_fixture_package, opentaint_rule_load_failure,
    opentaint_rule_paths, select_opentaint_cases, witness_opentaint_identity,
};
use crate::adapters::pysa::{
    PYSA_NATIVE_SINK_MODEL, PYSA_NATIVE_SUITE_RELATIVE, PYSA_PINNED_PYRE_VERSION,
    PYSA_PINNED_PYREFLY_VERSION, PYSA_RULE_CODE, PYSA_SINK_MODULE_PLACEHOLDER,
    PYSA_SOURCE_MODULE_PLACEHOLDER, PysaTools, parse_pysa_evidence, pysa_anchor_module,
    pysa_block_model_callables, pysa_configuration_paths, pysa_issue_anchor_match,
    pysa_model_activation_failure, pysa_model_template_path, pysa_modeling_block,
    pysa_taint_config_path, require_pysa_modeling_load_bearing, select_pysa_cases,
    witness_pysa_identity,
};
use crate::adapters::semgrep::{
    CHALLENGE_SEMGREP_PARTITION, SEMGREP_MODELING_ASSUME_SAFE_OPTION,
    SEMGREP_NATIVE_PROVENANCE_FILE, SEMGREP_NATIVE_UPSTREAM, SEMGREP_SINK_PLACEHOLDER,
    SEMGREP_SOURCE_PLACEHOLDER, SemgrepKernel, challenge_semgrep_exclusion, native_semgrep_outcome,
    require_semgrep_modeling_load_bearing, select_semgrep_cases, semgrep_capability_exclusion,
    semgrep_finding_outcome, semgrep_maturity_diagnostic, semgrep_native_rules_dir,
    semgrep_rule_paths,
};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::cases::{
    case_paths, core_templates_for_language, csharp_core_case, go_core_case, php_core_case,
    ruby_core_case, scala_core_case, validate_balanced_core_pairs, validate_cases,
    validate_kernel_population_with, validate_markers,
};
use crate::evidence::{
    AnchorDialect, BenchmarkEndpoints, EvidenceAnchorMatch, SarifAnchorMatch, SinkAnchorLocation,
    benchmark_endpoint_names, callsite_anchored_outcome, cpp_function_call,
    evidence_path_matches_file, parameter_list_function_call, parameter_list_function_name,
    rust_function_call, sarif_anchor_outcome, sarif_execution_errors, sarif_messages,
    sarif_result_count,
};
use crate::freeze::{
    build_freeze_manifest, compile_schema, fixture_revision_for_manifest_cases, git_output,
    parse_raw_evidence_documents, raw_special_outcome, validate_adapter_identities,
    validate_freeze_at, validate_freeze_git_state,
};
use crate::latency::{
    OVERHEAD_REPEATS, OVERHEAD_ROOT, OverheadLanguage, OverheadRun, WARM_LATENCY_ROOT,
    WARM_REPEATS, WARM_SUPERSEDED_ROOT, WarmBatch, WarmLanguage, WarmTool, overhead_range,
    trivial_fixture, warm_batch_sizes, warm_slope,
};
use crate::modeling::{
    MODELING_CASE_COUNT, MODELING_MODEL_PROFILE, MODELING_PARTITION, MODELING_TEMPLATE_IDS,
    MODELING_TEMPLATE_PREFIX, ModelingCategory, modeling_anchor_dialect, modeling_case,
    modeling_category, modeling_partition_outcome, modeling_partition_reason,
    modeling_supported_templates, modeling_unsupported_reason, select_modeling_cases,
    validate_modeling_cases, validate_modeling_population,
};
use crate::native::{
    NATIVE_CASE_COUNT, NATIVE_MODEL_PROFILE, NATIVE_PARTITION, NATIVE_PARTITION_AMENDMENTS,
    NATIVE_TEMPLATE_IDS, NATIVE_TEMPLATE_PREFIX, benchmark_model_artifacts, native_activation,
    native_anchor_tally_outcome, native_case, native_category, native_configuration_hash,
    native_partition_outcome, native_partition_reason, native_raw_dir, native_report_path,
    native_sarif_outcome, native_sink_anchor_locations, native_supported_templates,
    native_unsupported_reason, require_no_benchmark_models, select_native_cases,
    validate_native_cases, validate_native_population, validate_profile_disjoint_populations,
};
use crate::report::{
    ConfigurationHashState, KNOWN_STALE_CONFIGURATIONS, configuration_hash_state,
    current_configuration_paths, hash_paths, validate_reports, validate_reports_in,
    write_and_validate_report_in,
};
use crate::results::{
    GeneratedCaseMeta, SCORE_TIER_ORDER, build_index_page, build_scorecard, generate_results_at,
    scorecard_identifier,
};
use crate::runtime::{
    case_timing_path, clear_stale_case_timing, write_case_phase_timings, write_run_environment,
};
use crate::templates::{
    CHALLENGE_ROLLOUT, CHALLENGE_TEMPLATE_IDS, CHALLENGE_TEMPLATE_PREFIX, KERNEL_CASE_COUNT,
    KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH, KERNEL_TEMPLATE_IDS,
    KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH, challenge_rolled_out, challenge_rollout,
    challenge_template_case, expected_core_case_count, expected_core_templates,
};
use anyhow::Result;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{
    collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf, process::Command,
    time::Duration, time::SystemTime, time::UNIX_EPOCH,
};

/// A stand-in for the identity a run reads from the pinned binary.
///
/// A test has no binary to witness, so it passes this and then asserts the
/// retained rationale names *it*. That is the property under test: the
/// identity a report and its decisions carry is threaded in from a
/// measurement, and no constant inside the partition can supply one.
const WITNESSED_IDENTITY: &str = "witnessed-tool-identity-under-test";

/// Creates a fresh scratch directory under the system temp dir. Parallel
/// test threads share a pid and can observe the same nanosecond timestamp,
/// so a process-wide counter disambiguates, and `create_dir` (not
/// `create_dir_all`) atomically claims the path so a leftover directory
/// from a prior run is never silently reused.
fn unique_test_dir(prefix: &str) -> PathBuf {
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

struct FreezeFixture {
    root: PathBuf,
    manifest: PathBuf,
    report: PathBuf,
    raw: PathBuf,
}

impl FreezeFixture {
    fn new(outcome: &str, raw: Value) -> Self {
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

    fn read_manifest(&self) -> Value {
        serde_json::from_slice(&fs::read(&self.manifest).unwrap()).unwrap()
    }

    fn write_manifest(&self, manifest: &Value) {
        fs::write(&self.manifest, serde_json::to_vec_pretty(manifest).unwrap()).unwrap();
    }

    fn refresh_report_digest(&self, manifest: &mut Value) {
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
#[test]
fn checked_in_cases_validate() {
    validate_cases().unwrap();
}
#[test]
fn report_directory_validates() {
    validate_reports().unwrap();
}

/// A scratch benchmark root holding an "own" kernel report and a
/// concurrently running "other" kernel's report, for exercising the
/// end-of-run report sweep.
struct ReportSweepFixture {
    root: PathBuf,
}

impl ReportSweepFixture {
    fn new() -> Self {
        let root = unique_test_dir("dataflowbench-report-sweep-test");
        fs::create_dir_all(root.join("reports/raw/own-kernel")).unwrap();
        fs::create_dir_all(root.join("reports/raw/other-kernel")).unwrap();
        Self { root }
    }

    fn report(raw_relative: &str) -> Value {
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

    fn write_report(&self, name: &str, report: &Value) -> PathBuf {
        let path = self.root.join("reports").join(name);
        fs::write(&path, serde_json::to_vec_pretty(report).unwrap()).unwrap();
        path
    }

    fn write_raw(&self, raw_relative: &str) {
        fs::write(self.root.join(raw_relative), "{}\n").unwrap();
    }
}

impl Drop for ReportSweepFixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

#[test]
fn end_of_run_sweep_tolerates_a_concurrent_runner_rewriting_its_raw_evidence() {
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
fn end_of_run_sweep_still_checks_the_runners_own_raw_evidence() {
    let fixture = ReportSweepFixture::new();
    let own = fixture.write_report(
        "own-kernel.json",
        &ReportSweepFixture::report("reports/raw/own-kernel/case.json"),
    );
    let error = validate_reports_in(&fixture.root, Some(&own)).unwrap_err();
    assert!(error.to_string().contains("is absent"), "{error}");
}

#[test]
fn end_of_run_sweep_still_schema_checks_other_reports() {
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
fn runner_never_publishes_a_report_it_did_not_validate() {
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
fn runner_publishes_a_validated_report_atomically() {
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
fn validate_reports_accepts_raw_evidence_with_and_without_timing_metadata() {
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
    write_run_environment(&raw_dir, "test-tool", "1.0.0", "test-build-1").unwrap();
    validate_reports_in(&fixture.root, Some(&own)).unwrap();
    validate_reports_in(&fixture.root, None).unwrap();
}

/// Pre-existing frozen artifacts stay valid: a freeze manifest that binds
/// timing-free raw evidence keeps validating after timing sidecars and an
/// environment stamp appear beside that evidence, because neither is part
/// of the frozen surface.
#[test]
fn validate_freeze_accepts_timing_metadata_beside_frozen_raw_evidence() {
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
    write_run_environment(&raw_dir, "test-tool", "1.0.0", "test-build-1").unwrap();
    validate_freeze_at(&fixture.root, &fixture.manifest, false).unwrap();
}

/// The sidecar retains what the runner witnessed and nothing an outcome
/// could ever read: even a timing document mistakenly consulted as raw
/// evidence declares no special outcome, and a re-run that skips the
/// analyzer clears the previous run's sidecar.
#[test]
fn timing_sidecar_is_additive_metadata_never_an_outcome_input() {
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
fn run_environment_stamp_pairs_machine_with_witnessed_identity() {
    let root = unique_test_dir("dataflowbench-environment-test");
    write_run_environment(&root, "bifrost", "0.10.8", "bifrost-build").unwrap();
    let stamp: Value =
        serde_json::from_str(&fs::read_to_string(root.join("run-environment.json")).unwrap())
            .unwrap();
    assert_eq!(stamp["schema_version"], 1);
    assert_eq!(stamp["tool"], "bifrost");
    assert_eq!(stamp["witnessed_tool_version"], "0.10.8");
    assert_eq!(stamp["witnessed_tool_build_identity"], "bifrost-build");
    assert_eq!(stamp["os"], std::env::consts::OS);
    assert_eq!(stamp["evidence_kind"], "retained-run-environment");
    assert!(stamp["hardware_model"].is_string());
    assert!(stamp["cpu_count"].is_u64() || stamp["cpu_count"].is_null());
    let _ = fs::remove_dir_all(&root);
}

/// The eleven-line block that decides what a Joern case's evidence says —
/// the frontend dispatch, the two selectors, and the `reachableByFlows`
/// call — is character-for-character the same in the cold kernel script
/// and the warm batch script.
///
/// This is the mechanical form of Amendment A15's promise that the warm
/// measurement times the *same work* as the cold rows it stands beside. If
/// either script's query drifts, the warm marginal stops describing the
/// cold number's cost and this test fails rather than a page quietly
/// publishing an incomparable figure.
///
/// Exactly one substitution is allowed, and it is the reason the two files
/// are not one: the cold runner gives every case a fresh scratch directory
/// and so can reuse one project name, while the warm batch shares a
/// workspace across k cases and must name each project distinctly. Nothing
/// else may differ.
#[test]
fn joern_warm_batch_script_shares_the_kernel_query_block() {
    const BLOCK_START: &str = "if (language == \"RUBYSRC\") {";
    const BLOCK_END: &str = "val flows = sinkNodes.reachableByFlows(sourceNodes).l";

    fn block(source: &str) -> Vec<&str> {
        let lines: Vec<&str> = source.lines().collect();
        let start = lines
            .iter()
            .position(|line| line.contains(BLOCK_START))
            .expect("the query block starts at the frontend dispatch");
        let end = lines
            .iter()
            .position(|line| line.contains(BLOCK_END))
            .expect("the query block ends at reachableByFlows");
        assert!(start < end, "the block's anchors are out of order");
        lines[start..=end].to_vec()
    }

    let kernel = fs::read_to_string(JOERN_KERNEL_SCRIPT).unwrap();
    let warm = fs::read_to_string(JOERN_WARM_BATCH_SCRIPT).unwrap();
    let expected: Vec<String> = block(&kernel)
        .into_iter()
        .map(|line| {
            line.replace(
                "projectName = \"dataflowbench\"",
                "projectName = projectName",
            )
        })
        .collect();
    let measured: Vec<String> = block(&warm).into_iter().map(str::to_string).collect();
    assert_eq!(
        expected, measured,
        "the warm batch script's query block has drifted from the kernel script's"
    );
    // The block is substantive, not an accidental one-line match.
    assert!(expected.len() >= 8);

    // And the warm script never introduces a clock of its own: the tier's
    // decomposition rule admits only the runner's subprocess boundary, and
    // A13 does not relax it.
    for forbidden in ["nanoTime", "currentTimeMillis", "Instant.now"] {
        assert!(
            !warm.contains(forbidden),
            "the warm batch script must not timestamp itself ({forbidden})"
        );
    }
}

/// The slope estimators are the preregistered ones, and the fit is a
/// slope — not an average, which would still carry the fixed cost.
#[test]
fn warm_slope_recovers_the_marginal_cost_not_the_average() {
    // A process that pays 10 000 ms once and 500 ms per case.
    let batches: Vec<WarmBatch> = [1usize, 2, 4, 8, 16]
        .into_iter()
        .map(|k| WarmBatch {
            k,
            wall_ms: 10_000 + 500 * k as u64,
            case_ids: Vec::new(),
            load_before: None,
        })
        .collect();
    let slope = warm_slope(&batches).unwrap();
    assert!((slope.endpoint_ms - 500.0).abs() < 1e-6);
    assert!((slope.least_squares_ms - 500.0).abs() < 1e-6);
    assert!((slope.intercept_ms - 10_000.0).abs() < 1e-6);
    // The average per case at k=16 is 1125 ms — more than twice the
    // marginal cost. Reporting the average would smuggle the fixed cost
    // back into the number the slope exists to remove.
    assert!(slope.least_squares_ms < 10_000.0 / 16.0 + 500.0);

    // One point cannot define a slope, and neither can a repeated k.
    assert!(warm_slope(&batches[..1]).is_err());
    assert!(
        warm_slope(&[
            WarmBatch {
                k: 4,
                wall_ms: 1,
                case_ids: Vec::new(),
                load_before: None
            },
            WarmBatch {
                k: 4,
                wall_ms: 2,
                case_ids: Vec::new(),
                load_before: None
            },
        ])
        .is_err()
    );
}

/// Batch sizes must be strictly increasing and positive, so every larger
/// batch is a strict superset of every smaller one and a slope is defined.
#[test]
fn warm_batch_sizes_are_strictly_increasing() {
    assert_eq!(
        warm_batch_sizes("1,2,4,8,16").unwrap(),
        vec![1, 2, 4, 8, 16]
    );
    assert_eq!(warm_batch_sizes(" 1 , 3 ").unwrap(), vec![1, 3]);
    for rejected in ["1", "", "4,2", "2,2", "0,4", "1,x"] {
        assert!(
            warm_batch_sizes(rejected).is_err(),
            "{rejected:?} should be refused"
        );
    }
}

/// Warm-marginal artifacts are auxiliary: they live in their own directory
/// and carry an evidence kind no correctness reader recognizes, so nothing
/// in the scoring path can mistake one for a result.
#[test]
fn warm_latency_artifacts_are_auxiliary_and_never_an_outcome_input() {
    assert!(WARM_LATENCY_ROOT.starts_with("reports/raw/"));
    // Not inside any slice directory a normalized report binds.
    for report in [
        JOERN_JAVA_RAW_DIR.to_string(),
        SemgrepKernel::Java.raw_dir(),
    ] {
        assert!(!WARM_LATENCY_ROOT.starts_with(&report));
        assert!(!report.starts_with(WARM_LATENCY_ROOT));
    }
    // Retired figures must not live under a directory the runner sweeps:
    // `measure-warm-latency` removes its whole output directory before it
    // writes, so a superseded artifact parked there is destroyed by the
    // next re-measurement. That is not hypothetical — it happened once.
    for tool in [WarmTool::Joern, WarmTool::Semgrep] {
        let swept = format!(
            "{WARM_LATENCY_ROOT}/{}-{}-kernel",
            tool.as_str(),
            WarmLanguage::Java.as_str()
        );
        assert!(
            !WARM_SUPERSEDED_ROOT.starts_with(&swept),
            "retired warm evidence must not sit under the swept directory {swept}"
        );
    }
    let document = json!({
        "evidence_kind": "retained-warm-marginal-latency",
        "marginal_ms_per_case_range": {"endpoint": [500.0, 520.0]},
    });
    assert_eq!(raw_special_outcome(&document), None);
}

/// The figure is published as a range over retained repeats, and the
/// repeat count is fixed in the source rather than passed in.
///
/// Both properties exist to remove a discretionary parameter from the path
/// between a measurement and a page. A caller-chosen repeat count would let
/// a run be extended until its spread looked narrow; an agreement tolerance
/// would have to be picked, and any tolerance picked after the numbers
/// exist is the after-the-fact decision the tier's motivation refuses. The
/// range needs neither.
#[test]
fn warm_repeats_are_fixed_and_published_as_a_range() {
    assert!(WARM_REPEATS >= 2, "a range needs at least two repeats");
    let source = fs::read_to_string(file!()).unwrap();
    // No tolerance constant anywhere in the warm path: the range is the
    // precision statement, and nothing gates on how wide it is. The needles
    // are assembled at runtime so this assertion cannot trip on its own
    // literals.
    for suffix in ["AGREEMENT", "TOLERANCE", "THRESHOLD"] {
        let gate = format!("WARM_{suffix}");
        assert!(
            !source.contains(&gate),
            "the warm path must not gate publication on an agreement threshold ({gate})"
        );
    }
}

/// The same property for A24's estimates: an auxiliary directory of its
/// own, outside every slice a normalized report binds and outside the
/// warm directory, and a document the freeze validator's special-outcome
/// reader cannot mistake for evidence of an outcome.
#[test]
fn invocation_overhead_artifacts_are_auxiliary_and_never_an_outcome_input() {
    assert!(OVERHEAD_ROOT.starts_with("reports/raw/"));
    assert!(!OVERHEAD_ROOT.starts_with(WARM_LATENCY_ROOT));
    assert!(!WARM_LATENCY_ROOT.starts_with(OVERHEAD_ROOT));
    for report in [
        JOERN_JAVA_RAW_DIR.to_string(),
        JOERN_PHP_RAW_DIR.to_string(),
        CODEQL_RUBY_RAW_DIR.to_string(),
        SemgrepKernel::Kotlin.raw_dir(),
    ] {
        assert!(!OVERHEAD_ROOT.starts_with(&report));
        assert!(!report.starts_with(OVERHEAD_ROOT));
    }
    let document = json!({
        "evidence_kind": "retained-invocation-overhead-estimate",
        "estimated_overhead_ms": {"low": 2_900, "high": 3_100},
    });
    assert_eq!(raw_special_outcome(&document), None);
}

#[test]
fn normalizer_keeps_negative_and_unsupported_distinct() {
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
fn normalizer_does_not_synthesize_witness_checkpoints() {
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

/// The Bifrost mirror of the per-adapter sink-anchor tests: a finding on
/// the anchored sink's callsite is `reached`; a finding anywhere else in
/// the raw document, or one without a usable location, is `inconclusive`
/// on the same terms as CodeQL, Joern, and Semgrep evidence.
#[test]
fn bifrost_findings_require_the_sink_file_and_callsite() {
    let root = unique_test_dir("dataflowbench-bifrost-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("Fixture.java"),
        "    static void dfbSink(int value) { } // DFB-SINK: sink\n    static void other(int value) { }\n        other(input);\n        dfbSink(input);\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "Fixture.java",
            "line_hint": 1
        }]
    });
    let finding_report = |path: &str, line: u64| {
        json!({
            "runs": [{"completion": {"type": "complete"}, "findings": [{
                "primary": {"path": path, "region": {"start_line": line}}
            }]}]
        })
    };
    assert_eq!(
        normalize_bifrost(
            &case_path,
            &case,
            &finding_report("Fixture.java", 4),
            Some(0),
            AnchorDialect::Java,
        )
        .unwrap()
        .0,
        "reached"
    );
    let wrong_line = normalize_bifrost(
        &case_path,
        &case,
        &finding_report("Fixture.java", 3),
        Some(0),
        AnchorDialect::Java,
    )
    .unwrap();
    assert_eq!(wrong_line.0, "inconclusive");
    assert!(
        wrong_line
            .1
            .iter()
            .any(|diagnostic| diagnostic.contains("did not match the case sink anchor"))
    );
    assert_eq!(
        normalize_bifrost(
            &case_path,
            &case,
            &finding_report("Elsewhere.java", 4),
            Some(0),
            AnchorDialect::Java,
        )
        .unwrap()
        .0,
        "inconclusive"
    );
    let missing_location = normalize_bifrost(
        &case_path,
        &case,
        &json!({
            "runs": [{"completion": {"type": "complete"}, "findings": [{
                "message": "Controlled input reaches the benchmark sink"
            }]}]
        }),
        Some(0),
        AnchorDialect::Java,
    )
    .unwrap();
    assert_eq!(missing_location.0, "inconclusive");
    assert!(
        missing_location
            .1
            .iter()
            .any(|diagnostic| diagnostic.contains("ambiguous sink-anchor location"))
    );
    assert_eq!(
        normalize_bifrost(
            &case_path,
            &case,
            &json!({"runs": [{"completion": {"type": "complete"}, "findings": []}]}),
            Some(0),
            AnchorDialect::Java,
        )
        .unwrap()
        .0,
        "not-reached"
    );
    fs::remove_dir_all(root).unwrap();
}

/// Every Bifrost population maps its case language onto the sink-anchor
/// dialect its fixtures actually declare sinks in; an unmapped language is
/// a hard error rather than an unreconciled `reached`.
#[test]
fn bifrost_anchor_dialects_cover_every_kernel_language() {
    for (language, dialect) in [
        ("java", AnchorDialect::Java),
        ("kotlin", AnchorDialect::Java),
        ("scala", AnchorDialect::Java),
        ("javascript", AnchorDialect::Ecma),
        ("typescript", AnchorDialect::Ecma),
        ("python", AnchorDialect::Python),
        ("csharp", AnchorDialect::CSharp),
        ("go", AnchorDialect::Go),
        ("c", AnchorDialect::Cpp),
        ("cpp", AnchorDialect::Cpp),
        ("rust", AnchorDialect::Rust),
        ("ruby", AnchorDialect::Ruby),
        ("php", AnchorDialect::Php),
    ] {
        assert_eq!(bifrost_anchor_dialect(language).unwrap(), dialect);
    }
    assert!(bifrost_anchor_dialect("cobol").is_err());
}

#[test]
fn incomplete_or_unexpected_bifrost_status_never_becomes_clean_negative() {
    let negative = json!({"expected_flows": []});
    let incomplete = json!({
        "runs": [{
            "completion": {"type": "inconclusive", "reasons": ["partial_discovery"]},
            "findings": []
        }]
    });
    let case_path = Path::new("cases/never/case.json");
    assert_eq!(
        normalize_bifrost(
            case_path,
            &negative,
            &incomplete,
            Some(0),
            AnchorDialect::Java
        )
        .unwrap()
        .0,
        "inconclusive"
    );
    assert_eq!(
        normalize_bifrost(
            case_path,
            &negative,
            &json!({"runs": [{"completion": {"type": "complete"}, "findings": []}]}),
            Some(9),
            AnchorDialect::Java,
        )
        .unwrap()
        .0,
        "runner-error"
    );
    assert_eq!(
        normalize_bifrost(
            case_path,
            &negative,
            &json!({"findings": []}),
            Some(0),
            AnchorDialect::Java,
        )
        .unwrap()
        .0,
        "runner-error"
    );
}

#[test]
fn empty_bifrost_endpoint_selection_is_inconclusive() {
    let positive = json!({
        "expected_flows": [{"source": "DFB-SOURCE: input", "sink": "DFB-SINK: sink"}]
    });
    let report = json!({
        "runs": [{
            "completion": {"type": "complete"},
            "diagnostics": [{
                "code": {"type": "empty_selection"},
                "family": "empty_selection",
                "message": "the source selector matched no location"
            }],
            "findings": []
        }]
    });
    let normalized = normalize_bifrost(
        Path::new("cases/never/case.json"),
        &positive,
        &report,
        Some(0),
        AnchorDialect::Java,
    )
    .unwrap();
    assert_eq!(normalized.0, "inconclusive");
    assert!(
        normalized
            .1
            .iter()
            .any(|diagnostic| diagnostic.contains("matched no location"))
    );
}

#[test]
fn python_kernel_selection_is_separate_from_direct_and_java() {
    let python_kernel = json!({
        "language": "python",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"policy": "adapters/bifrost/policies/core-python-kernel.rqlp"}
        }
    });
    let python_direct = json!({
        "language": "python",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"policy": "adapters/bifrost/policies/core-direct.rqlp"}
        }
    });
    let java_kernel = json!({
        "language": "java",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"policy": "adapters/bifrost/policies/core-python-kernel.rqlp"}
        }
    });
    let python_unsupported = json!({
        "language": "python",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"unsupported_reason": "requires an external model catalog"}
        }
    });
    assert!(selected_bifrost_case(
        &python_kernel,
        BifrostRun::PythonKernel
    ));
    assert!(!selected_bifrost_case(
        &python_direct,
        BifrostRun::PythonKernel
    ));
    assert!(!selected_bifrost_case(
        &java_kernel,
        BifrostRun::PythonKernel
    ));
    assert!(selected_bifrost_case(
        &python_unsupported,
        BifrostRun::PythonKernel
    ));
    assert!(selected_bifrost_case(&python_direct, BifrostRun::Smoke));
}

#[test]
fn kotlin_kernel_selection_is_separate_from_java_and_every_other_language() {
    let kotlin_core = json!({
        "language": "kotlin",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"policy": BIFROST_KOTLIN_POLICY}
        }
    });
    // Frozen v0.2.0 breadth metadata: the Kotlin kernel still selects it.
    let kotlin_direct = json!({
        "language": "kotlin",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"policy": "adapters/bifrost/policies/core-direct.rqlp"}
        }
    });
    let java_core = json!({
        "language": "java",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {"bifrost": {"policy": BIFROST_KOTLIN_POLICY}}
    });
    let kotlin_calibration = json!({
        "language": "kotlin",
        "track": "taint",
        "score_tier": "calibration",
        "tool_model_references": {"bifrost": {"policy": BIFROST_KOTLIN_POLICY}}
    });
    assert!(selected_bifrost_case(
        &kotlin_core,
        BifrostRun::KotlinKernel
    ));
    assert!(selected_bifrost_case(
        &kotlin_direct,
        BifrostRun::KotlinKernel
    ));
    assert!(!selected_bifrost_case(&java_core, BifrostRun::KotlinKernel));
    assert!(!selected_bifrost_case(
        &kotlin_calibration,
        BifrostRun::KotlinKernel
    ));
    assert!(!selected_bifrost_case(
        &kotlin_core,
        BifrostRun::PythonKernel
    ));

    // Both kernel assertions are evaluated with the language-qualified
    // Kotlin policy, including the frozen direct pair.
    assert_eq!(
        bifrost_policy_for(&kotlin_direct, BifrostRun::KotlinKernel).unwrap(),
        BIFROST_KOTLIN_POLICY
    );
    assert_eq!(
        bifrost_policy_for(&kotlin_direct, BifrostRun::Smoke).unwrap(),
        "adapters/bifrost/policies/core-direct.rqlp"
    );
}

#[test]
fn scala_kernel_selection_is_separate_from_every_other_language() {
    let scala_core = json!({
        "language": "scala",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {"bifrost": {"policy": BIFROST_SCALA_POLICY}}
    });
    // Frozen v0.2.0 breadth metadata: the Scala kernel still selects it.
    let scala_direct = json!({
        "language": "scala",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"policy": "adapters/bifrost/policies/core-direct.rqlp"}
        }
    });
    let kotlin_core = json!({
        "language": "kotlin",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {"bifrost": {"policy": BIFROST_SCALA_POLICY}}
    });
    assert!(selected_bifrost_case(&scala_core, BifrostRun::ScalaKernel));
    assert!(selected_bifrost_case(
        &scala_direct,
        BifrostRun::ScalaKernel
    ));
    assert!(!selected_bifrost_case(
        &kotlin_core,
        BifrostRun::ScalaKernel
    ));
    assert!(!selected_bifrost_case(
        &scala_core,
        BifrostRun::KotlinKernel
    ));
    assert!(!selected_bifrost_case(&scala_core, BifrostRun::Smoke));

    // Every Scala assertion is evaluated with the language-qualified Scala
    // policy, including the frozen direct pair, while the frozen smoke
    // population keeps evaluating that pair through the breadth policy.
    assert_eq!(
        bifrost_policy_for(&scala_direct, BifrostRun::ScalaKernel).unwrap(),
        BIFROST_SCALA_POLICY
    );
    assert_eq!(
        bifrost_policy_for(&scala_direct, BifrostRun::Smoke).unwrap(),
        "adapters/bifrost/policies/core-direct.rqlp"
    );
}

/// Scala has no CodeQL and no Joern population, so the only in-repo
/// guarantee that its assertions are complete and balanced is the Bifrost
/// run's own core denominator — now the expanded 29-template / 58-assertion
/// core, since Scala's challenge row is rolled out.
#[test]
fn scala_bifrost_population_is_the_expanded_balanced_core() {
    let selected = case_paths()
        .into_iter()
        .map(|path| {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            (path, case)
        })
        .filter(|(_, case)| scala_core_case(case))
        .collect::<Vec<_>>();
    let expected = expected_core_templates("scala");
    assert_eq!(
        selected.len(),
        BifrostRun::ScalaKernel.expected_core_cases().unwrap()
    );
    assert_eq!(selected.len(), 58);
    assert!(selected.len() > KERNEL_CASE_COUNT);
    assert!(
        selected
            .iter()
            .all(|(path, _)| path.starts_with("cases/taint/scala"))
    );
    validate_kernel_population_with(&selected, "Bifrost Scala kernel", &expected).unwrap();
    // The classic sixteen alone are no longer a complete Scala core.
    let classic = selected
        .iter()
        .filter(|(_, case)| KERNEL_TEMPLATE_IDS.contains(&case["template_id"].as_str().unwrap()))
        .cloned()
        .collect::<Vec<_>>();
    assert_eq!(classic.len(), KERNEL_CASE_COUNT);
    assert!(validate_kernel_population_with(&classic, "Bifrost Scala kernel", &expected).is_err());
    assert!(Path::new(BIFROST_SCALA_POLICY).is_file());
}

#[test]
fn kotlin_codeql_population_is_the_expanded_balanced_core() {
    let expected = expected_core_templates("kotlin");
    let selected = codeql_kotlin_cases().unwrap();
    assert_eq!(selected.len(), 2 * expected.len());
    // Kotlin's challenge row is rolled out, so the population is the
    // expanded 29-template / 58-assertion core, not the classic 32.
    assert_eq!(selected.len(), 58);
    assert!(selected.len() > KERNEL_CASE_COUNT);
    let templates = selected
        .iter()
        .map(|(_, case)| case["template_id"].as_str().unwrap())
        .collect::<BTreeSet<_>>();
    assert_eq!(templates, expected.iter().copied().collect::<BTreeSet<_>>());
    assert!(
        selected
            .iter()
            .all(|(path, _)| path.starts_with("cases/taint/kotlin"))
    );
}

#[test]
fn kotlin_kernel_population_rejects_an_unbalanced_or_foreign_template_set() {
    let case = |template: &str, polarity: &str| {
        (
            PathBuf::from(format!(
                "cases/taint/kotlin/{template}-{polarity}/case.json"
            )),
            json!({
                "template_id": template,
                "polarity": polarity,
                "model_profile": "benchmark-controlled"
            }),
        )
    };
    // The runner validates against Kotlin's own denominator, which the
    // rollout table now expands to the challenge templates as well.
    let expected = expected_core_templates("kotlin");
    let check = |cases: &[(PathBuf, Value)]| {
        validate_kernel_population_with(cases, "Kotlin CodeQL kernel", &expected)
    };
    let mut balanced = Vec::new();
    for template in &expected {
        balanced.push(case(template, "positive"));
        balanced.push(case(template, "negative"));
    }
    assert!(check(&balanced).is_ok());

    let mut unbalanced = balanced.clone();
    unbalanced[1] = case(expected[0], "positive");
    assert!(check(&unbalanced).is_err());

    let mut foreign = balanced.clone();
    foreign[0] = case("dfb-template-one-hop-relay", "positive");
    assert!(check(&foreign).is_err());

    // The classic sixteen alone are no longer a complete Kotlin core.
    let classic = balanced
        .iter()
        .filter(|(_, case)| KERNEL_TEMPLATE_IDS.contains(&case["template_id"].as_str().unwrap()))
        .cloned()
        .collect::<Vec<_>>();
    assert_eq!(classic.len(), KERNEL_CASE_COUNT);
    assert!(check(&classic).is_err());

    assert!(check(&balanced[..2]).is_err());
}

#[test]
fn kotlin_codeql_databases_trace_a_real_kotlin_compile() {
    let case = json!({"fixture_files": ["LocalChainPositive.kt"]});
    let args = codeql_database_create_args(
        Path::new("/tmp/db"),
        Path::new("/tmp/workspace"),
        &case,
        CodeqlLanguage::Kotlin {
            kotlinc: Path::new("kotlinc"),
        },
    )
    .unwrap();
    assert!(args.contains(&"--language=java".to_string()));
    assert!(
        args.iter()
            .any(|arg| arg == "--command=kotlinc -nowarn -d classes LocalChainPositive.kt")
    );
    // CodeQL 2.26.3 extracts no Kotlin under build-mode=none.
    assert!(!args.iter().any(|arg| arg.starts_with("--build-mode")));
}

#[test]
fn kotlin_codeql_report_paths_are_dedicated() {
    for path in [
        CODEQL_KOTLIN_REPORT,
        CODEQL_KOTLIN_RAW_DIR,
        BIFROST_KOTLIN_POLICY,
    ] {
        assert!(path.contains("kotlin"), "{path} is not Kotlin-scoped");
    }
    assert_ne!(CODEQL_KOTLIN_QUERY, "adapters/codeql/queries/JavaKernel.ql");
    assert!(Path::new(CODEQL_KOTLIN_QUERY).is_file());
    assert!(Path::new(BIFROST_KOTLIN_POLICY).is_file());
}

#[test]
fn typescript_bifrost_kernel_selection_excludes_other_languages() {
    let kernel = json!({
        "language": "typescript",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {
            "bifrost": {"policy": "adapters/bifrost/policies/core-typescript-kernel.rqlp"}
        }
    });
    assert!(selected_bifrost_case(&kernel, BifrostRun::TypescriptKernel));

    // The frozen direct-propagation pair keeps the language-agnostic
    // policy but is still a TypeScript kernel assertion.
    let mut direct = kernel.clone();
    direct["tool_model_references"]["bifrost"]["policy"] =
        json!("adapters/bifrost/policies/core-direct.rqlp");
    assert!(selected_bifrost_case(&direct, BifrostRun::TypescriptKernel));

    for language in ["javascript", "python", "java"] {
        let mut other = kernel.clone();
        other["language"] = json!(language);
        assert!(!selected_bifrost_case(&other, BifrostRun::TypescriptKernel));
    }
    let mut javascript_kernel = kernel.clone();
    javascript_kernel["language"] = json!("javascript");
    javascript_kernel["tool_model_references"]["bifrost"]["policy"] =
        json!("adapters/bifrost/policies/core-javascript-kernel.rqlp");
    assert!(!selected_bifrost_case(
        &javascript_kernel,
        BifrostRun::TypescriptKernel
    ));
    assert!(!selected_bifrost_case(&kernel, BifrostRun::PythonKernel));

    let mut calibration = kernel.clone();
    calibration["score_tier"] = json!("calibration");
    assert!(!selected_bifrost_case(
        &calibration,
        BifrostRun::TypescriptKernel
    ));
    let mut unsupported = kernel.clone();
    unsupported["tool_model_references"]["bifrost"] =
        json!({"unsupported_reason": "requires an external model catalog"});
    assert!(selected_bifrost_case(
        &unsupported,
        BifrostRun::TypescriptKernel
    ));
}

#[test]
fn ecma_codeql_selection_refuses_the_other_kernel_query() {
    assert_ne!(
        EcmaKernel::JavaScript.query(),
        EcmaKernel::TypeScript.query()
    );
    assert_ne!(
        EcmaKernel::JavaScript.raw_dir(),
        EcmaKernel::TypeScript.raw_dir()
    );
    assert_ne!(
        EcmaKernel::JavaScript.report(),
        EcmaKernel::TypeScript.report()
    );
    assert_eq!(
        EcmaKernel::TypeScript.query(),
        "adapters/codeql/typescript/queries/TypeScriptKernel.ql"
    );
    assert!(!EcmaKernel::JavaScript.allows_implicit_query_reference());

    // The committed populations must already agree with the selector.
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        let query = case["tool_model_references"]["codeql"]["query"].as_str();
        if ecma_core_case(&case, EcmaKernel::TypeScript) {
            assert!(query.is_none_or(|query| query == EcmaKernel::TypeScript.query()));
        }
        if ecma_core_case(&case, EcmaKernel::JavaScript) {
            assert_eq!(query, Some(EcmaKernel::JavaScript.query()));
        }
    }
    assert_eq!(
        select_codeql_ecma_cases(EcmaKernel::TypeScript)
            .unwrap()
            .len(),
        expected_core_case_count("typescript")
    );
    assert_eq!(
        select_codeql_ecma_cases(EcmaKernel::JavaScript)
            .unwrap()
            .len(),
        expected_core_case_count("javascript")
    );
}

#[test]
fn core_templates_require_one_positive_and_one_negative() {
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
fn marker_validation_rejects_stale_metadata() {
    let path = Path::new("cases/taint/java/direct-positive/case.json");
    let mut case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();

    case["source_anchors"][0]["line_hint"] = json!(1);
    assert!(validate_markers(path, &case).is_err());

    case["source_anchors"][0]["line_hint"] = json!(4);
    case["witness_checkpoints"] = json!(["DFB-WITNESS: absent"]);
    assert!(validate_markers(path, &case).is_err());
}

#[test]
fn sarif_normalization_counts_results_and_deduplicates_messages() {
    let sarif = json!({
        "runs": [
            {"results": [
                {"message": {"text": "flow found"}},
                {"message": {"text": "flow found"}}
            ]},
            {"results": []}
        ]
    });
    assert_eq!(sarif_result_count(&sarif), 2);
    assert_eq!(sarif_messages(&sarif), vec!["flow found"]);
}

#[test]
fn sarif_execution_errors_prevent_clean_negative_interpretation() {
    let sarif = json!({
        "runs": [{
            "results": [],
            "invocations": [{
                "executionSuccessful": false,
                "toolExecutionNotifications": [{
                    "level": "error",
                    "message": {"text": "query evaluation failed"}
                }]
            }]
        }]
    });
    assert_eq!(sarif_result_count(&sarif), 0);
    assert_eq!(
        sarif_execution_errors(&sarif),
        vec![
            "CodeQL SARIF reports unsuccessful execution",
            "query evaluation failed"
        ]
    );
}

fn probe_row(role: &str) -> Value {
    json!({
        "ruleId": format!("dataflowbench/javascript{CODEQL_ENDPOINT_PROBE_RULE_SUFFIX}"),
        "message": {"text": format!("Benchmark {role} endpoint observed.")},
        "locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "fixture.js"},
            "region": {"startLine": 3}
        }}]
    })
}

/// The probe's rows share the kernel's SARIF document, so they are counted
/// and then removed before any reconciler sees the result set: the kernel's
/// own finding count, and its retained messages, are unchanged by the
/// probe running alongside it.
#[test]
fn codeql_endpoint_probe_rows_are_split_from_kernel_findings() {
    let sarif = json!({
        "runs": [{
            "results": [
                {
                    "ruleId": "dataflowbench/javascript-propagation-kernel",
                    "message": {"text": "Controlled input reaches the benchmark sink."}
                },
                probe_row("source"),
                probe_row("source"),
                probe_row("sink")
            ]
        }]
    });
    let (kernel, observation) = split_codeql_endpoint_probe(&sarif);
    assert_eq!(
        observation,
        CodeqlEndpointObservation {
            sources: 2,
            sinks: 1
        }
    );
    assert_eq!(sarif_result_count(&kernel), 1);
    assert!(
        sarif_messages(&kernel)
            .iter()
            .all(|message| !message.contains("endpoint observed"))
    );
    // The retained document is untouched: the probe's rows stay raw
    // evidence on disk.
    assert_eq!(sarif_result_count(&sarif), 4);
    assert_eq!(unobserved_codeql_endpoint_outcome(observation), None);
}

/// CodeQL merges same-location `@kind problem` rows into one SARIF result
/// with a newline-joined message. The direct templates' `dfb_sink(dfb_source())`
/// resolves both endpoints to one expression, so the probe's two rows
/// arrive as a single result that must count as one source *and* one
/// sink — never as a source alone, which would withhold a real finding.
#[test]
fn a_merged_codeql_endpoint_probe_result_counts_every_observed_role() {
    let merged = json!({
        "runs": [{
            "results": [
                {
                    "ruleId": "dataflowbench/java-propagation-kernel",
                    "message": {"text": "Controlled input reaches the benchmark sink."}
                },
                {
                    "ruleId": "dataflowbench/java-kernel-endpoint-probe",
                    "message": {"text": "Benchmark source endpoint observed.\nBenchmark sink endpoint observed."}
                }
            ]
        }]
    });
    let (kernel, observation) = split_codeql_endpoint_probe(&merged);
    assert_eq!(
        observation,
        CodeqlEndpointObservation {
            sources: 1,
            sinks: 1
        }
    );
    assert_eq!(sarif_result_count(&kernel), 1);
    assert_eq!(unobserved_codeql_endpoint_outcome(observation), None);
}

/// The CodeQL kernels' anti-vacuity mirror of
/// `JoernEndpointRule::BothMustBeObserved`: a fixture always contains both
/// of its own endpoints by construction, so a zero-result SARIF whose
/// probe never observed one of them is an incomplete run, never a clean
/// `not-reached` negative — exactly the recoverable per-file extractor
/// parse error that drops the sink expression without failing the run.
#[test]
fn an_unobserved_codeql_endpoint_prevents_clean_negative_interpretation() {
    let case = json!({});
    let case_path = PathBuf::from("cases/never-read.json");
    let sink_dropped = json!({
        "runs": [{"results": [probe_row("source")]}]
    });
    let (kernel, observation) = split_codeql_endpoint_probe(&sink_dropped);
    assert_eq!(sarif_result_count(&kernel), 0);
    let (outcome, diagnostics) =
        unobserved_codeql_endpoint_outcome(observation).expect("the sink was unobserved");
    assert_eq!(outcome, "inconclusive");
    assert!(diagnostics.iter().any(|line| {
        line.contains("1 source endpoint(s) and 0 sink endpoint(s)")
            && line.contains("never observed both benchmark-controlled endpoints")
    }));
    // A probe that observed nothing at all — or that never ran, which is
    // indistinguishable in the document — withholds the negative too.
    let empty = json!({"runs": [{"results": []}]});
    let (_, observation) = split_codeql_endpoint_probe(&empty);
    assert!(unobserved_codeql_endpoint_outcome(observation).is_some());
    // Joern applies its endpoint rule before flow reconciliation, and the
    // CodeQL gate sits at the same place: a kernel finding in a run whose
    // probe contradicts it is inconsistent evidence, not `reached`.
    let contradictory = json!({
        "runs": [{"results": [
            {
                "ruleId": "dataflowbench/javascript-propagation-kernel",
                "message": {"text": "Controlled input reaches the benchmark sink."}
            },
            probe_row("source")
        ]}]
    });
    let (_, observation) = split_codeql_endpoint_probe(&contradictory);
    assert!(unobserved_codeql_endpoint_outcome(observation).is_some());
    // With both endpoints observed the gate opens and the zero-result
    // reconciliation is the clean negative it always was.
    let observed = json!({
        "runs": [{"results": [probe_row("source"), probe_row("sink")]}]
    });
    let (kernel, observation) = split_codeql_endpoint_probe(&observed);
    assert_eq!(unobserved_codeql_endpoint_outcome(observation), None);
    assert_eq!(
        ecma_sarif_outcome(&case_path, &case, &kernel).0,
        "not-reached"
    );
}

/// Every kernel population evaluates a companion endpoint-observation
/// probe beside its kernel query, and each probe is the load-bearing kind
/// the runner can split back out: a `problem` query under the shared
/// `dataflowbench/…-kernel-endpoint-probe` rule identity, observing the
/// benchmark's own `dfb_source`/`dfb_sink` contract.
#[test]
fn every_codeql_kernel_evaluates_an_endpoint_probe_beside_its_query() {
    let populations = [
        (
            "java",
            "adapters/codeql/queries/JavaKernel.ql",
            CODEQL_JAVA_ENDPOINT_PROBE,
        ),
        (
            "javascript",
            CODEQL_JAVASCRIPT_QUERY,
            CODEQL_JAVASCRIPT_ENDPOINT_PROBE,
        ),
        (
            "typescript",
            CODEQL_TYPESCRIPT_QUERY,
            CODEQL_TYPESCRIPT_ENDPOINT_PROBE,
        ),
        ("python", CODEQL_PYTHON_QUERY, CODEQL_PYTHON_ENDPOINT_PROBE),
        ("kotlin", CODEQL_KOTLIN_QUERY, CODEQL_KOTLIN_ENDPOINT_PROBE),
        ("csharp", CODEQL_CSHARP_QUERY, CODEQL_CSHARP_ENDPOINT_PROBE),
        ("go", CODEQL_GO_QUERY, CODEQL_GO_ENDPOINT_PROBE),
        ("c", CODEQL_C_QUERY, CODEQL_C_ENDPOINT_PROBE),
        ("cpp", CODEQL_CPP_QUERY, CODEQL_CPP_ENDPOINT_PROBE),
        ("rust", CODEQL_RUST_QUERY, CODEQL_RUST_ENDPOINT_PROBE),
        ("ruby", CODEQL_RUBY_QUERY, CODEQL_RUBY_ENDPOINT_PROBE),
    ];
    assert_eq!(populations.len(), 11);
    for (language, query, probe) in populations {
        let query_path = Path::new(query);
        let probe_path = Path::new(probe);
        assert!(query_path.is_file(), "{query}");
        assert!(probe_path.is_file(), "{probe}");
        assert_eq!(
            query_path.parent(),
            probe_path.parent(),
            "the {language} probe must live in the kernel query's own pack"
        );
        let body = fs::read_to_string(probe_path).unwrap();
        assert!(body.contains("@kind problem"), "{probe}");
        let rule_id = format!("@id dataflowbench/{language}{CODEQL_ENDPOINT_PROBE_RULE_SUFFIX}");
        assert!(body.contains(&rule_id), "{probe} must declare {rule_id}");
        assert!(body.contains("dfb_source"), "{probe}");
        assert!(body.contains("dfb_sink"), "{probe}");
        // A probe row is recognized by the same predicate the runner
        // splits with, so the two can never drift apart silently.
        let sarif_rule = format!("dataflowbench/{language}{CODEQL_ENDPOINT_PROBE_RULE_SUFFIX}");
        assert!(codeql_endpoint_probe_result(&json!({"ruleId": sarif_rule})));
    }
}

#[test]
fn ecma_core_selections_are_exactly_32_balanced_assertions() {
    for kernel in [EcmaKernel::JavaScript, EcmaKernel::TypeScript] {
        let mut selected = Vec::new();
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if ecma_core_case(&case, kernel) {
                selected.push(case);
            }
        }
        assert_eq!(selected.len(), expected_core_case_count(kernel.language()));
        let mut templates = BTreeMap::<String, (usize, usize)>::new();
        for case in selected {
            let counts = templates
                .entry(case["template_id"].as_str().unwrap().to_string())
                .or_default();
            if case["polarity"] == "positive" {
                counts.0 += 1;
            } else {
                counts.1 += 1;
            }
        }
        assert_eq!(
            templates.len(),
            expected_core_templates(kernel.language()).len()
        );
        assert!(
            templates
                .values()
                .all(|(positive, negative)| *positive == 1 && *negative == 1)
        );
    }
}

#[test]
fn java_javascript_and_typescript_codeql_selectors_are_language_disjoint() {
    let mut java = 0;
    let mut javascript = 0;
    let mut typescript = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_codeql_java_case(&case) {
            java += 1;
            assert_eq!(case["language"], "java");
        }
        if ecma_core_case(&case, EcmaKernel::JavaScript) {
            javascript += 1;
            assert_eq!(case["language"], "javascript");
            assert!(!ecma_core_case(&case, EcmaKernel::TypeScript));
        }
        if ecma_core_case(&case, EcmaKernel::TypeScript) {
            typescript += 1;
            assert_eq!(case["language"], "typescript");
            assert!(!ecma_core_case(&case, EcmaKernel::JavaScript));
        }
    }
    assert_eq!(java, expected_core_case_count("java"));
    assert_eq!(javascript, expected_core_case_count("javascript"));
    assert_eq!(typescript, expected_core_case_count("typescript"));
}

/// The JavaScript kernel selects `.js` fixtures and the TypeScript kernel
/// `.ts` fixtures; neither population may contain the other's extension.
#[test]
fn ecma_kernel_fixtures_carry_their_own_extension() {
    for (kernel, extension, other) in [
        (EcmaKernel::JavaScript, "js", "ts"),
        (EcmaKernel::TypeScript, "ts", "js"),
    ] {
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            if !ecma_core_case(&case, kernel) {
                continue;
            }
            for fixture in case["fixture_files"].as_array().unwrap() {
                let fixture = fixture.as_str().unwrap();
                assert!(fixture.ends_with(&format!(".{extension}")), "{fixture}");
                assert!(!fixture.ends_with(&format!(".{other}")), "{fixture}");
            }
        }
    }
}

#[test]
fn csharp_core_selection_is_the_expanded_balanced_population() {
    let expected_templates = expected_core_templates("csharp");
    let selected = codeql_csharp_cases().unwrap();
    assert_eq!(selected.len(), expected_core_case_count("csharp"));
    // C#'s challenge row is rolled out, so the population is the expanded
    // 29 templates / 58 assertions, not the classic 32.
    assert_eq!(selected.len(), 58);
    let mut templates = BTreeMap::<String, (usize, usize)>::new();
    for (_, case) in &selected {
        assert_eq!(case["language"], "csharp");
        assert_eq!(case["track"], "taint");
        assert_eq!(case["score_tier"], "core");
        let counts = templates
            .entry(case["template_id"].as_str().unwrap().to_string())
            .or_default();
        if case["polarity"] == "positive" {
            counts.0 += 1;
        } else {
            counts.1 += 1;
        }
    }
    assert_eq!(templates.len(), expected_templates.len());
    assert_eq!(templates.len(), 29);
    assert!(
        templates
            .values()
            .all(|(positive, negative)| *positive == 1 && *negative == 1)
    );
}

#[test]
fn csharp_core_selection_is_language_and_track_scoped() {
    let csharp = json!({
        "language": "csharp",
        "track": "taint",
        "score_tier": "core"
    });
    assert!(csharp_core_case(&csharp));
    for language in ["java", "javascript", "typescript", "python", "kotlin"] {
        let mut other = csharp.clone();
        other["language"] = json!(language);
        assert!(!csharp_core_case(&other));
    }
    let mut other = csharp.clone();
    other["track"] = json!("value-flow");
    assert!(!csharp_core_case(&other));
    other["track"] = json!("taint");
    other["score_tier"] = json!("calibration");
    assert!(!csharp_core_case(&other));
}

#[test]
fn bifrost_csharp_kernel_selects_only_csharp_core_cases() {
    let mut selected = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::CsharpKernel) {
            selected += 1;
            assert_eq!(case["language"], "csharp");
            assert_eq!(case["score_tier"], "core");
            for other in [
                BifrostRun::PythonKernel,
                BifrostRun::KotlinKernel,
                BifrostRun::TypescriptKernel,
            ] {
                assert!(!selected_bifrost_case(&case, other));
            }
        }
    }
    // The C# row is rolled out, so the kernel run covers the expanded core.
    assert_eq!(selected, expected_core_case_count("csharp"));
    assert!(selected > KERNEL_CASE_COUNT);
}

/// C and C++ are two populations with two denominators, both now rolled
/// out: C's core is the fifteen applicable classic templates plus its nine
/// applicable challenge templates — 24 templates and 48 assertions — and
/// the C++ core is all sixteen classic templates plus its twelve
/// applicable challenge templates — 28 templates and 56 assertions. The C
/// `language-extension` cases ride along in the C slice without changing
/// its core denominator.
#[test]
fn c_and_cpp_core_populations_keep_their_own_denominators() {
    let c = codeql_c_family_cases(CFamilyKernel::C).unwrap();
    let cpp = codeql_c_family_cases(CFamilyKernel::Cpp).unwrap();
    let core = |cases: &[(PathBuf, Value)]| {
        cases
            .iter()
            .filter(|(_, case)| case["score_tier"] == "core")
            .count()
    };
    assert_eq!(core(&c), expected_core_case_count("c"));
    assert_eq!(core(&c), 48);
    assert_eq!(core(&cpp), expected_core_case_count("cpp"));
    assert_eq!(core(&cpp), 56);
    assert_eq!(c.len() - core(&c), 2);
    assert_eq!(cpp.len(), core(&cpp));

    let c_templates = c
        .iter()
        .filter(|(_, case)| case["score_tier"] == "core")
        .map(|(_, case)| case["template_id"].as_str().unwrap().to_string())
        .collect::<BTreeSet<_>>();
    assert!(!c_templates.contains("dfb-template-exception-catch"));
    assert_eq!(c_templates.len(), expected_core_templates("c").len());
    assert_eq!(c_templates.len(), 24);
    for (_, case) in &c {
        assert_eq!(case["language"], "c");
        assert!(
            case["fixture_files"]
                .as_array()
                .unwrap()
                .iter()
                .all(|fixture| fixture.as_str().unwrap().ends_with(".c"))
        );
    }
    for (_, case) in &cpp {
        assert_eq!(case["language"], "cpp");
        assert_eq!(case["score_tier"], "core");
        assert!(
            case["fixture_files"]
                .as_array()
                .unwrap()
                .iter()
                .all(|fixture| fixture.as_str().unwrap().ends_with(".cpp"))
        );
    }
}

/// The C denominator is the sixteen scored templates minus the
/// inapplicable exception-catch cell, and nothing else.
#[test]
fn the_reduced_template_set_is_the_scored_set_without_exception_catch() {
    let scored = KERNEL_TEMPLATE_IDS.iter().copied().collect::<BTreeSet<_>>();
    let c = KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    assert_eq!(
        scored.difference(&c).copied().collect::<Vec<_>>(),
        vec!["dfb-template-exception-catch"]
    );
    assert!(c.difference(&scored).next().is_none());
}

/// A C population that lost an applicable template, or gained the
/// inapplicable one, is not a C kernel.
#[test]
fn c_kernel_population_rejects_a_foreign_or_short_template_set() {
    let case = |template: &str, polarity: &str| {
        (
            PathBuf::from(format!("cases/taint/c/{template}-{polarity}/case.json")),
            json!({
                "template_id": template,
                "polarity": polarity,
                "model_profile": "benchmark-controlled"
            }),
        )
    };
    let balanced = KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        .iter()
        .flat_map(|template| [case(template, "positive"), case(template, "negative")])
        .collect::<Vec<_>>();
    assert!(
        validate_kernel_population_with(
            &balanced,
            "C kernel",
            &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        )
        .is_ok()
    );
    assert!(validate_kernel_population_with(&balanced, "C kernel", &KERNEL_TEMPLATE_IDS).is_err());
    let mut with_exception_catch = balanced.clone();
    with_exception_catch.push(case("dfb-template-exception-catch", "positive"));
    with_exception_catch.push(case("dfb-template-exception-catch", "negative"));
    assert!(
        validate_kernel_population_with(
            &with_exception_catch,
            "C kernel",
            &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        )
        .is_err()
    );
    assert!(
        validate_kernel_population_with(
            &balanced[..2],
            "C kernel",
            &KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        )
        .is_err()
    );
}

#[test]
fn bifrost_c_and_cpp_kernels_select_disjoint_populations() {
    let mut c = 0;
    let mut c_core = 0;
    let mut cpp = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::CKernel) {
            c += 1;
            if case["score_tier"] == "core" {
                c_core += 1;
            }
            assert_eq!(case["language"], "c");
            assert!(!selected_bifrost_case(&case, BifrostRun::CppKernel));
        }
        if selected_bifrost_case(&case, BifrostRun::CppKernel) {
            cpp += 1;
            assert_eq!(case["language"], "cpp");
            assert_eq!(case["score_tier"], "core");
            for other in [
                BifrostRun::CKernel,
                BifrostRun::CsharpKernel,
                BifrostRun::KotlinKernel,
                BifrostRun::PythonKernel,
                BifrostRun::TypescriptKernel,
            ] {
                assert!(!selected_bifrost_case(&case, other));
            }
        }
    }
    // Both challenge rows are rolled out, but C excludes four challenge
    // templates and C++ one, so the two slices carry different
    // denominators from the same extractor.
    assert_eq!(c_core, expected_core_case_count("c"));
    assert_eq!(c_core, 48);
    assert_eq!(c - c_core, 2);
    assert_eq!(cpp, expected_core_case_count("cpp"));
    assert_eq!(cpp, 56);
}

/// The two C-family kernels share the `cpp` extractor and one pack, so
/// their reports, raw-evidence roots, and queries must stay distinct.
#[test]
fn c_family_codeql_report_paths_are_dedicated() {
    assert_ne!(CFamilyKernel::C.report(), CFamilyKernel::Cpp.report());
    assert_ne!(CFamilyKernel::C.raw_dir(), CFamilyKernel::Cpp.raw_dir());
    assert_ne!(CFamilyKernel::C.query(), CFamilyKernel::Cpp.query());
    assert_ne!(CFamilyKernel::C.policy(), CFamilyKernel::Cpp.policy());
    for kernel in [CFamilyKernel::C, CFamilyKernel::Cpp] {
        assert!(kernel.report().starts_with("reports/codeql-"));
        assert!(kernel.raw_dir().starts_with("reports/raw/codeql-"));
    }
    assert_eq!(CodeqlLanguage::CFamily.cli_name(), "cpp");
    assert!(!CodeqlLanguage::CFamily.traces_jvm_compile());
}

/// C and C++ reach members through `.`, `->`, and `::`; none of those is a
/// call of the free sink function the `DFB-SINK:` marker declares.
#[test]
fn cpp_sink_declarations_and_callsites_resolve_through_the_cpp_dialect() {
    assert_eq!(
        parameter_list_function_name(
            "void dfb_sink(int value) {} // DFB-SINK: sink",
            "DFB-SINK: sink"
        )
        .as_deref(),
        Some("dfb_sink")
    );
    assert_eq!(
        parameter_list_function_name(
            "const char *dfb_sink(const char *value) {} // DFB-SINK: sink",
            "DFB-SINK: sink"
        )
        .as_deref(),
        Some("dfb_sink")
    );
    assert!(cpp_function_call("    dfb_sink(holder.value);", "dfb_sink"));
    assert!(cpp_function_call("    dfb_sink(alias->value);", "dfb_sink"));
    assert!(!cpp_function_call(
        "    other->dfb_sink(value);",
        "dfb_sink"
    ));
    assert!(!cpp_function_call(
        "    Other::dfb_sink(value);",
        "dfb_sink"
    ));
    assert!(!cpp_function_call("    other.dfb_sink(value);", "dfb_sink"));
    assert!(!cpp_function_call("    my_dfb_sink(value);", "dfb_sink"));
    assert!(!cpp_function_call("    // dfb_sink(value);", "dfb_sink"));
}

#[test]
fn csharp_sarif_mapping_requires_the_sink_file_and_callsite() {
    let root = unique_test_dir("dataflowbench-csharp-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("Fixture.cs"),
        "    static void dfb_sink(int value) { } // DFB-SINK: sink\n    static void Other(int value) { }\n        Other(input);\n        dfb_sink(input);\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "Fixture.cs",
            "line_hint": 1
        }]
    });
    let matching = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "file:///tmp/work/Fixture.cs"},
            "region": {"startLine": 4}
        }}]}]}]
    });
    assert_eq!(
        sarif_anchor_outcome(&case_path, &case, &matching, AnchorDialect::CSharp).0,
        "reached"
    );
    let wrong_line = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "Fixture.cs"},
            "region": {"startLine": 3}
        }}]}]}]
    });
    assert_eq!(
        sarif_anchor_outcome(&case_path, &case, &wrong_line, AnchorDialect::CSharp).0,
        "inconclusive"
    );
    let missing_location = json!({
        "runs": [{"results": [{"message": {"text": "flow"}}]}]
    });
    assert_eq!(
        sarif_anchor_outcome(&case_path, &case, &missing_location, AnchorDialect::CSharp).0,
        "inconclusive"
    );
    let no_results = json!({"runs": [{"results": []}]});
    assert_eq!(
        sarif_anchor_outcome(&case_path, &case, &no_results, AnchorDialect::CSharp).0,
        "not-reached"
    );
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn go_core_selection_is_the_expanded_balanced_population() {
    let expected_templates = expected_core_templates("go");
    let selected = codeql_go_cases().unwrap();
    assert_eq!(selected.len(), expected_core_case_count("go"));
    // Go's challenge row is rolled out, so the population is the expanded
    // 29 templates / 58 assertions, not the classic 32.
    assert_eq!(selected.len(), 58);
    let mut templates = BTreeMap::<String, (usize, usize)>::new();
    for (_, case) in &selected {
        assert_eq!(case["language"], "go");
        assert_eq!(case["track"], "taint");
        assert_eq!(case["score_tier"], "core");
        let counts = templates
            .entry(case["template_id"].as_str().unwrap().to_string())
            .or_default();
        if case["polarity"] == "positive" {
            counts.0 += 1;
        } else {
            counts.1 += 1;
        }
    }
    assert_eq!(templates.len(), expected_templates.len());
    assert_eq!(templates.len(), 29);
    assert!(
        templates
            .values()
            .all(|(positive, negative)| *positive == 1 && *negative == 1)
    );
}

#[test]
fn go_core_selection_is_language_and_track_scoped() {
    let go = json!({
        "language": "go",
        "track": "taint",
        "score_tier": "core"
    });
    assert!(go_core_case(&go));
    for language in [
        "java",
        "javascript",
        "typescript",
        "python",
        "kotlin",
        "csharp",
    ] {
        let mut other = go.clone();
        other["language"] = json!(language);
        assert!(!go_core_case(&other));
    }
    let mut other = go.clone();
    other["track"] = json!("value-flow");
    assert!(!go_core_case(&other));
    other["track"] = json!("taint");
    other["score_tier"] = json!("calibration");
    assert!(!go_core_case(&other));
}

#[test]
fn bifrost_go_kernel_selects_only_go_core_cases() {
    let mut selected = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::GoKernel) {
            selected += 1;
            assert_eq!(case["language"], "go");
            assert_eq!(case["score_tier"], "core");
            for other in [
                BifrostRun::PythonKernel,
                BifrostRun::KotlinKernel,
                BifrostRun::TypescriptKernel,
                BifrostRun::CsharpKernel,
            ] {
                assert!(!selected_bifrost_case(&case, other));
            }
        }
    }
    // The Go row is rolled out, so the kernel run covers the expanded core.
    assert_eq!(selected, expected_core_case_count("go"));
    assert!(selected > KERNEL_CASE_COUNT);
}

#[test]
fn php_core_selection_is_language_and_track_scoped() {
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

/// PHP has no CodeQL support in the pinned CLI, so Bifrost and Joern are its
/// two analyzers. The Bifrost slice still may not overlap any other
/// language's kernel population.
#[test]
fn bifrost_php_kernel_selects_only_php_core_cases() {
    let mut selected = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::PhpKernel) {
            selected += 1;
            assert_eq!(case["language"], "php");
            assert_eq!(case["score_tier"], "core");
            for other in [
                BifrostRun::PythonKernel,
                BifrostRun::KotlinKernel,
                BifrostRun::TypescriptKernel,
                BifrostRun::CsharpKernel,
                BifrostRun::GoKernel,
                BifrostRun::CKernel,
                BifrostRun::CppKernel,
                BifrostRun::RustKernel,
                BifrostRun::RubyKernel,
            ] {
                assert!(!selected_bifrost_case(&case, other));
            }
        }
    }
    // PHP's challenge row is rolled out, so the slice covers the expanded
    // 29 templates / 58 assertions, not the classic 32.
    assert_eq!(selected, expected_core_case_count("php"));
    assert_eq!(selected, 58);
    assert_eq!(
        BifrostRun::PhpKernel.expected_core_cases(),
        Some(expected_core_case_count("php"))
    );
}

#[test]
fn go_sarif_mapping_requires_the_sink_file_and_callsite() {
    let root = unique_test_dir("dataflowbench-go-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("fixture.go"),
        "func dfb_sink(value int) {} // DFB-SINK: sink\nfunc other(value int) {}\n\tother(input)\n\tdfb_sink(input)\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "fixture.go",
            "line_hint": 1
        }]
    });
    let matching = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "file:///tmp/work/fixture.go"},
            "region": {"startLine": 4}
        }}]}]}]
    });
    assert_eq!(
        sarif_anchor_outcome(&case_path, &case, &matching, AnchorDialect::Go).0,
        "reached"
    );
    let wrong_line = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "fixture.go"},
            "region": {"startLine": 3}
        }}]}]}]
    });
    assert_eq!(
        sarif_anchor_outcome(&case_path, &case, &wrong_line, AnchorDialect::Go).0,
        "inconclusive"
    );
    let no_results = json!({"runs": [{"results": []}]});
    assert_eq!(
        sarif_anchor_outcome(&case_path, &case, &no_results, AnchorDialect::Go).0,
        "not-reached"
    );
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn go_sink_declarations_resolve_to_the_declared_function() {
    assert_eq!(
        parameter_list_function_name(
            "func dfb_sink(value int) {} // DFB-SINK: sink",
            "DFB-SINK: sink"
        )
        .as_deref(),
        Some("dfb_sink")
    );
    assert_eq!(
        parameter_list_function_name("\tvalue := 0 // DFB-SINK: sink", "DFB-SINK: sink"),
        None
    );
    assert!(parameter_list_function_call(
        "\tdfb_sink(values[0])",
        "dfb_sink"
    ));
    assert!(parameter_list_function_call(
        "\t\t\tdfb_sink(recovered.(int))",
        "dfb_sink"
    ));
    assert!(!parameter_list_function_call(
        "\tlog(`dfb_sink(value)`)",
        "dfb_sink"
    ));
    assert!(!parameter_list_function_call(
        "\tother.dfb_sink(0)",
        "dfb_sink"
    ));
}

/// The Rust kernel scores its expanded core: 27 templates and 54
/// assertions now that the challenge row is flipped (15 classic plus 12
/// challenge cells). The excluded exception-catch and reflective-invocation
/// cells stay excluded, and the `Result`/`?` extension pair rides in the
/// same slice without changing the denominator.
#[test]
fn rust_core_selection_is_the_expanded_balanced_population() {
    let expected_templates = expected_core_templates("rust");
    let selected = codeql_rust_cases().unwrap();
    let mut templates = BTreeMap::<String, (usize, usize)>::new();
    let mut extensions = 0;
    for (_, case) in &selected {
        assert_eq!(case["language"], "rust");
        assert_eq!(case["track"], "taint");
        if case["score_tier"] == "language-extension" {
            extensions += 1;
            continue;
        }
        assert_eq!(case["score_tier"], "core");
        let counts = templates
            .entry(case["template_id"].as_str().unwrap().to_string())
            .or_default();
        if case["polarity"] == "positive" {
            counts.0 += 1;
        } else {
            counts.1 += 1;
        }
    }
    assert_eq!(templates.len(), expected_templates.len());
    assert_eq!(templates.len(), 27);
    assert_eq!(
        templates.values().map(|(p, n)| p + n).sum::<usize>(),
        expected_core_case_count("rust")
    );
    assert_eq!(expected_core_case_count("rust"), 54);
    assert!(expected_core_case_count("rust") > KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
    assert!(
        templates
            .values()
            .all(|(positive, negative)| *positive == 1 && *negative == 1)
    );
    // The excluded templates stay excluded: they reduce only Rust's
    // denominator, and the language-extension pair replaces nothing.
    assert!(!templates.contains_key("dfb-template-exception-catch"));
    assert!(!templates.contains_key("dfb-template-chal-reflective-invocation"));
    assert_eq!(extensions, 2);
}

/// C and Rust exclude the same classic template for different reasons, so
/// they share one 15-template constant instead of two identical copies.
/// Both challenge rows are now flipped, so each language's corpus core is
/// that shared classic set plus its own challenge cells -- nine for C,
/// twelve for Rust. Their language-extension cases stay distinct and never
/// enter either core denominator.
#[test]
fn c_and_rust_share_the_scored_set_without_exception_catch() {
    let cases = case_paths()
        .into_iter()
        .map(|path| {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            (path, case)
        })
        .collect::<Vec<_>>();
    let classic = KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH
        .iter()
        .copied()
        .collect::<BTreeSet<_>>();
    for language in ["c", "rust"] {
        let core = core_templates_for_language(&cases, language);
        // Both languages start from the same 15-template classic
        // constant and both have since expanded past it, so the constant
        // is a subset of either core rather than equal to it, and the
        // shared exclusion is what the two still have in common.
        assert!(classic.is_subset(&core), "{language} classic set");
        assert!(!core.contains("dfb-template-exception-catch"));
        // Each language's corpus is exactly its rollout row.
        assert_eq!(
            core,
            expected_core_templates(language)
                .into_iter()
                .collect::<BTreeSet<_>>()
        );
        assert_eq!(
            challenge_rolled_out(language),
            core.len() > classic.len(),
            "{language} corpus does not match its rollout state"
        );
    }
    assert_eq!(core_templates_for_language(&cases, "rust").len(), 27);
    assert_eq!(core_templates_for_language(&cases, "c").len(), 24);
    assert!(
        !core_templates_for_language(&cases, "rust")
            .contains("dfb-template-result-error-propagation")
    );
    let extension = cases
        .iter()
        .filter(|(_, case)| {
            case["language"] == "rust" && case["score_tier"] == "language-extension"
        })
        .collect::<Vec<_>>();
    assert_eq!(extension.len(), 2);
    for (_, case) in extension {
        assert_eq!(case["template_id"], "dfb-template-result-error-propagation");
    }
}

/// A Rust population that reintroduced the excluded template, or that
/// smuggled a non-kernel tier into the slice, is not a Rust kernel.
#[test]
fn rust_kernel_population_rejects_the_excluded_or_a_foreign_template() {
    let base = json!({
        "language": "rust",
        "track": "taint",
        "score_tier": "core",
        "model_profile": "benchmark-controlled"
    });
    let mut cases = Vec::new();
    for template in expected_core_templates("rust") {
        for polarity in ["positive", "negative"] {
            let mut case = base.clone();
            case["template_id"] = json!(template);
            case["polarity"] = json!(polarity);
            cases.push((PathBuf::from(format!("{template}-{polarity}")), case));
        }
    }
    validate_rust_kernel_population(&cases, "test").unwrap();

    let mut with_exception = cases.clone();
    for polarity in ["positive", "negative"] {
        let mut case = base.clone();
        case["template_id"] = json!("dfb-template-exception-catch");
        case["polarity"] = json!(polarity);
        with_exception.push((PathBuf::from(polarity), case));
    }
    assert!(validate_rust_kernel_population(&with_exception, "test").is_err());

    // A language-extension assertion rides along without changing the
    // 54-assertion expanded core denominator.
    let mut with_extension = cases.clone();
    let mut extension = base.clone();
    extension["score_tier"] = json!("language-extension");
    extension["template_id"] = json!("dfb-template-result-error-propagation");
    extension["polarity"] = json!("positive");
    with_extension.push((PathBuf::from("extension"), extension));
    validate_rust_kernel_population(&with_extension, "test").unwrap();

    // A calibration case is not part of this population at all.
    let mut with_calibration = cases.clone();
    let mut calibration = base.clone();
    calibration["score_tier"] = json!("calibration");
    calibration["template_id"] = json!("dfb-template-one-hop-relay");
    calibration["polarity"] = json!("positive");
    with_calibration.push((PathBuf::from("calibration"), calibration));
    assert!(validate_rust_kernel_population(&with_calibration, "test").is_err());
}

#[test]
fn bifrost_rust_kernel_selects_only_rust_cases() {
    let mut core = 0;
    let mut extension = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::RustKernel) {
            assert!(rust_kernel_case(&case));
            if case["score_tier"] == "core" {
                core += 1;
            } else {
                assert_eq!(case["score_tier"], "language-extension");
                extension += 1;
            }
            for other in [
                BifrostRun::PythonKernel,
                BifrostRun::KotlinKernel,
                BifrostRun::TypescriptKernel,
                BifrostRun::CsharpKernel,
                BifrostRun::GoKernel,
                BifrostRun::CKernel,
                BifrostRun::CppKernel,
            ] {
                assert!(!selected_bifrost_case(&case, other));
            }
        }
    }
    // The Rust row is rolled out, so the kernel run covers the expanded
    // core: 27 templates and 54 assertions.
    assert_eq!(core, expected_core_case_count("rust"));
    assert!(core > KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
    assert_eq!(
        BifrostRun::RustKernel.expected_core_cases(),
        Some(expected_core_case_count("rust"))
    );
    assert_eq!(extension, 2);
}

#[test]
fn rust_codeql_report_paths_are_dedicated() {
    for other in [
        CODEQL_KOTLIN_REPORT,
        CODEQL_CSHARP_REPORT,
        CODEQL_JAVASCRIPT_REPORT,
        CODEQL_TYPESCRIPT_REPORT,
        CODEQL_GO_REPORT,
        CODEQL_C_REPORT,
        CODEQL_CPP_REPORT,
        "reports/codeql-python-kernel.json",
    ] {
        assert_ne!(CODEQL_RUST_REPORT, other);
    }
    for other in [
        CODEQL_KOTLIN_RAW_DIR,
        CODEQL_CSHARP_RAW_DIR,
        CODEQL_JAVASCRIPT_RAW_DIR,
        CODEQL_TYPESCRIPT_RAW_DIR,
        CODEQL_GO_RAW_DIR,
        CODEQL_C_RAW_DIR,
        CODEQL_CPP_RAW_DIR,
    ] {
        assert_ne!(CODEQL_RUST_RAW_DIR, other);
    }
    assert_ne!(CODEQL_RUST_QUERY, CODEQL_CSHARP_QUERY);
    assert_eq!(CodeqlLanguage::Rust.cli_name(), "rust");
    assert!(!CodeqlLanguage::Rust.traces_jvm_compile());
}

#[test]
fn rust_codeql_databases_carry_a_generated_cargo_manifest() {
    let case = json!({"id": "dfb-taint-rust-test", "fixture_files": ["direct_flow.rs"]});
    let args = codeql_database_create_args(
        Path::new("/tmp/rust-db"),
        Path::new("/tmp/rust-workspace"),
        &case,
        CodeqlLanguage::Rust,
    )
    .unwrap();
    assert!(args.iter().any(|arg| arg == "--language=rust"));
    assert!(args.iter().any(|arg| arg == "--build-mode=none"));
    assert!(!args.iter().any(|arg| arg.starts_with("--command=")));

    let workspace = unique_test_dir("dataflowbench-rust-manifest-test");
    write_rust_cargo_manifest(&workspace, &case).unwrap();
    let manifest = fs::read_to_string(workspace.join("Cargo.toml")).unwrap();
    // Without a manifest the extractor logs "semantic analyzer unavailable
    // (no manifest found)" and resolves no call targets, so the crate root
    // must point straight at the case's single fixture file.
    assert!(manifest.contains("path = \"direct_flow.rs\""), "{manifest}");
    assert!(manifest.contains("[workspace]"), "{manifest}");

    let two_fixtures = json!({"id": "x", "fixture_files": ["a.rs", "b.rs"]});
    assert!(write_rust_cargo_manifest(&workspace, &two_fixtures).is_err());
    fs::remove_dir_all(workspace).unwrap();
}

/// Rust declares a sink the way C#, Go, and C/C++ do, but reaches a member
/// through `.` and `::` only — it has no `->` operator to exclude.
#[test]
fn rust_sink_declarations_resolve_to_the_declared_function() {
    assert_eq!(
        parameter_list_function_name(
            "fn dfb_sink(value: i32) {} // DFB-SINK: sink",
            "DFB-SINK: sink"
        )
        .as_deref(),
        Some("dfb_sink")
    );
    assert_eq!(
        parameter_list_function_name("    let value = 0; // DFB-SINK: sink", "DFB-SINK: sink"),
        None
    );
    assert!(rust_function_call("    dfb_sink(input);", "dfb_sink"));
    assert!(rust_function_call(
        "    dfb_sink(holder.value);",
        "dfb_sink"
    ));
    assert!(!rust_function_call(
        "    other.dfb_sink(value);",
        "dfb_sink"
    ));
    assert!(!rust_function_call(
        "    other::dfb_sink(value);",
        "dfb_sink"
    ));
    assert!(!rust_function_call("    my_dfb_sink(value);", "dfb_sink"));
    assert!(!rust_function_call("    // dfb_sink(value);", "dfb_sink"));

    let root = unique_test_dir("dataflowbench-rust-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("fixture.rs"),
        "fn dfb_sink(value: i32) {} // DFB-SINK: sink\nfn other(value: i32) {}\n    other(input);\n    dfb_sink(input);\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "fixture.rs",
            "line_hint": 1
        }]
    });
    let outcome =
        |sarif: &Value| callsite_anchored_outcome(&case_path, &case, sarif, AnchorDialect::Rust).0;
    let matching = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "fixture.rs"},
            "region": {"startLine": 4}
        }}]}]}]
    });
    assert_eq!(outcome(&matching), "reached");
    let wrong_line = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "fixture.rs"},
            "region": {"startLine": 3}
        }}]}]}]
    });
    assert_eq!(outcome(&wrong_line), "inconclusive");
    let no_results = json!({"runs": [{"results": []}]});
    assert_eq!(outcome(&no_results), "not-reached");
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn csharp_sink_declarations_resolve_to_the_declared_method() {
    assert_eq!(
        parameter_list_function_name(
            "    static void dfb_sink(int value) { } // DFB-SINK: sink",
            "DFB-SINK: sink"
        )
        .as_deref(),
        Some("dfb_sink")
    );
    assert_eq!(
        parameter_list_function_name("        int value = 0; // DFB-SINK: sink", "DFB-SINK: sink"),
        None
    );
    assert!(parameter_list_function_call(
        "        dfb_sink(values[0]);",
        "dfb_sink"
    ));
    assert!(!parameter_list_function_call(
        "        Log(\"dfb_sink(value)\");",
        "dfb_sink"
    ));
    assert!(!parameter_list_function_call(
        "        other.dfb_sink(0);",
        "dfb_sink"
    ));
    assert!(!parameter_list_function_call(
        "        int dfb_sinkValue = 0;",
        "dfb_sink"
    ));
}

#[test]
fn ecma_core_selection_is_language_and_track_scoped() {
    for (kernel, language, others) in [
        (
            EcmaKernel::JavaScript,
            "javascript",
            ["typescript", "java", "python"],
        ),
        (
            EcmaKernel::TypeScript,
            "typescript",
            ["javascript", "java", "python"],
        ),
    ] {
        let selected = json!({
            "language": language,
            "track": "taint",
            "score_tier": "core"
        });
        assert!(ecma_core_case(&selected, kernel));
        for other_language in others {
            let mut other = selected.clone();
            other["language"] = json!(other_language);
            assert!(!ecma_core_case(&other, kernel));
        }
        let mut other = selected.clone();
        other["track"] = json!("value-flow");
        assert!(!ecma_core_case(&other, kernel));
        other["track"] = json!("taint");
        other["score_tier"] = json!("calibration");
        assert!(!ecma_core_case(&other, kernel));
    }
}

#[test]
fn javascript_sarif_mapping_requires_the_sink_file_and_line() {
    let root = unique_test_dir("dataflowbench-javascript-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("fixture.js"),
        "function sink(value) {} // DFB-SINK: sink\nfunction other(value) {}\nother(input);\nsink(input);\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "fixture.js",
            "line_hint": 1
        }]
    });
    let matching = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "file:///tmp/work/fixture.js"},
            "region": {"startLine": 4}
        }}]}]}]
    });
    assert_eq!(
        ecma_sarif_outcome(&case_path, &case, &matching).0,
        "reached"
    );
    let wrong_line = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "fixture.js"},
            "region": {"startLine": 3}
        }}]}]}]
    });
    assert_eq!(
        ecma_sarif_outcome(&case_path, &case, &wrong_line).0,
        "inconclusive"
    );
    let missing_location = json!({
        "runs": [{"results": [{"message": {"text": "flow"}}]}]
    });
    assert_eq!(
        ecma_sarif_outcome(&case_path, &case, &missing_location).0,
        "inconclusive"
    );
    let no_results = json!({"runs": [{"results": []}]});
    assert_eq!(
        ecma_sarif_outcome(&case_path, &case, &no_results).0,
        "not-reached"
    );
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn javascript_sarif_ambiguous_locations_stay_inconclusive() {
    let root = unique_test_dir("dataflowbench-javascript-ambiguous-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("fixture.js"),
        "// DFB-SINK: duplicate\n// DFB-SINK: duplicate\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{"marker": "DFB-SINK: duplicate", "file": "fixture.js"}]
    });
    let sarif = json!({
        "runs": [{"results": [{"locations": [{"physicalLocation": {
            "artifactLocation": {"uri": "fixture.js"},
            "region": {"startLine": 1}
        }}]}]}]
    });
    assert_eq!(
        ecma_sarif_outcome(&case_path, &case, &sarif).0,
        "inconclusive"
    );
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn javascript_codeql_report_paths_are_dedicated() {
    assert_eq!(CODEQL_JAVASCRIPT_RAW_DIR, "reports/raw/codeql-javascript");
    assert_eq!(
        CODEQL_JAVASCRIPT_REPORT,
        "reports/codeql-javascript-kernel.json"
    );
    assert_eq!(
        CODEQL_JAVASCRIPT_QUERY,
        "adapters/codeql/javascript/queries/JavaScriptKernel.ql"
    );
    assert_eq!(CODEQL_TYPESCRIPT_RAW_DIR, "reports/raw/codeql-typescript");
    assert_eq!(
        CODEQL_TYPESCRIPT_REPORT,
        "reports/codeql-typescript-kernel.json"
    );
    assert_eq!(
        CODEQL_TYPESCRIPT_QUERY,
        "adapters/codeql/typescript/queries/TypeScriptKernel.ql"
    );
}

#[test]
fn python_codeql_population_requires_the_expanded_core() {
    let expected = expected_core_templates("python");
    let mut cases = Vec::new();
    for index in 0..expected.len() {
        for polarity in ["positive", "negative"] {
            cases.push((
                PathBuf::from(format!("case-{index}-{polarity}.json")),
                json!({
                    "id": format!("dfb-taint-python-template-{index}-{polarity}"),
                    "template_id": expected[index],
                    "polarity": polarity,
                    "score_tier": "core",
                    "track": "taint",
                    "language": "python",
                    "model_profile": "benchmark-controlled",
                    "tool_model_references": {
                        "codeql": {"query": CODEQL_PYTHON_QUERY}
                    }
                }),
            ));
        }
    }
    // Population validation is metadata-only; the checked-in query path
    // is verified by the command-facing selection helper.
    assert_eq!(
        validate_codeql_python_population(&cases).unwrap(),
        PathBuf::from("adapters/codeql/python/queries/PythonKernel.ql")
    );
    let mut drifted = cases.clone();
    drifted[0].1["template_id"] = json!("dfb-template-unapproved-drift");
    assert!(validate_codeql_python_population(&drifted).is_err());
    cases.pop();
    assert!(validate_codeql_python_population(&cases).is_err());
}

#[test]
fn python_codeql_selection_requires_canonical_query() {
    let mut case = json!({
        "language": "python",
        "track": "taint",
        "score_tier": "core",
        "tool_model_references": {"codeql": {"query": CODEQL_PYTHON_QUERY}}
    });
    assert!(selected_codeql_python_case(&case));
    case["tool_model_references"]["codeql"]["query"] =
        json!("adapters/codeql/python/queries/OtherKernel.ql");
    assert!(!selected_codeql_python_case(&case));
}

#[test]
fn codeql_database_creation_uses_language_specific_build_modes() {
    let case = json!({"fixture_files": ["direct_flow.py"]});
    let python_args = codeql_database_create_args(
        Path::new("/tmp/python-db"),
        Path::new("/tmp/python-workspace"),
        &case,
        CodeqlLanguage::Python,
    )
    .unwrap();
    assert!(python_args.iter().any(|arg| arg == "--language=python"));
    assert!(python_args.iter().any(|arg| arg == "--build-mode=none"));
    assert!(!python_args.iter().any(|arg| arg.starts_with("--command=")));

    let java_args = codeql_database_create_args(
        Path::new("/tmp/java-db"),
        Path::new("/tmp/java-workspace"),
        &case,
        CodeqlLanguage::Java,
    )
    .unwrap();
    assert!(java_args.iter().any(|arg| arg == "--language=java"));
    assert!(
        java_args
            .iter()
            .any(|arg| arg == "--command=javac -d classes direct_flow.py")
    );
    assert!(!java_args.iter().any(|arg| arg == "--build-mode=none"));

    let csharp_args = codeql_database_create_args(
        Path::new("/tmp/csharp-db"),
        Path::new("/tmp/csharp-workspace"),
        &case,
        CodeqlLanguage::CSharp,
    )
    .unwrap();
    assert!(csharp_args.iter().any(|arg| arg == "--language=csharp"));
    assert!(csharp_args.iter().any(|arg| arg == "--build-mode=none"));
    assert!(!csharp_args.iter().any(|arg| arg.starts_with("--command=")));

    let go_args = codeql_database_create_args(
        Path::new("/tmp/go-db"),
        Path::new("/tmp/go-workspace"),
        &case,
        CodeqlLanguage::Go {
            go: Path::new("/usr/local/bin/go"),
        },
    )
    .unwrap();
    assert!(go_args.iter().any(|arg| arg == "--language=go"));
    assert!(go_args.iter().any(|arg| arg == "--build-mode=manual"));
    assert!(
        go_args
            .iter()
            .any(|arg| arg == "--command=/usr/local/bin/go build ./...")
    );
    assert!(!go_args.iter().any(|arg| arg == "--build-mode=none"));
}

#[test]
fn codeql_missing_sarif_keeps_runner_error_evidence() {
    let root = unique_test_dir("dataflowbench-codeql-missing-sarif-test");
    let raw_path = root.join("case.sarif.json");
    let read_error = fs::read_to_string(&raw_path).unwrap_err();
    let (outcome, diagnostics, evidence_path) =
        codeql_missing_sarif_error(&root, "case", &raw_path, &read_error).unwrap();

    assert_eq!(outcome, "runner-error");
    assert!(diagnostics[0].contains("read CodeQL SARIF"));
    assert_eq!(evidence_path, root.join("case-error.json"));
    let evidence: Value =
        serde_json::from_str(&fs::read_to_string(&evidence_path).unwrap()).unwrap();
    assert_eq!(evidence["state"], "runner-error");
    assert_eq!(evidence["stage"], "database-analyze");
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn python_codeql_sarif_requires_a_canonical_sink_anchor() {
    let case = json!({
        "sink_anchors": [{"file": "direct_flow.py", "line_hint": 5}]
    });
    let reached = json!({
        "runs": [{"results": [{
            "message": {"text": "flow"},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "file:///tmp/codeql/direct_flow.py"},
                "region": {"startLine": 11}
            }}]
        }]}]
    });
    assert_eq!(
        normalize_anchored_codeql_sarif(&case, &reached, "Python").0,
        "reached"
    );

    let wrong_file = json!({
        "runs": [{"results": [{
            "message": {"text": "unrelated finding"},
            "locations": [{"physicalLocation": {
                "artifactLocation": {"uri": "other_fixture.py"},
                "region": {"startLine": 4}
            }}]
        }]}]
    });
    assert_eq!(
        normalize_anchored_codeql_sarif(&case, &wrong_file, "Python").0,
        "inconclusive"
    );

    let clean = json!({"runs": [{"results": []}]});
    assert_eq!(
        normalize_anchored_codeql_sarif(&case, &clean, "Python").0,
        "not-reached"
    );

    let malformed = json!({"runs": [{"results": [{}]}]});
    assert_eq!(
        normalize_anchored_codeql_sarif(&case, &malformed, "Python").0,
        "inconclusive"
    );
    assert_eq!(
        normalize_anchored_codeql_sarif(&case, &json!({"runs": []}), "Python").0,
        "runner-error"
    );
}

/// Each Joern kernel is its own population: the balanced core assertions of
/// exactly one language — 32 where all sixteen templates apply, 30 for Rust,
/// whose exception-catch cell is inapplicable — with no case shared between
/// them and no case borrowed from a CodeQL or Bifrost selection. Rust's
/// `Result`/`?` `language-extension` pair is never pulled into the core
/// denominator.
#[test]
fn joern_kernel_selections_are_language_disjoint_and_balanced() {
    let mut populations = BTreeMap::new();
    for kernel in [
        JoernKernel::Java,
        JoernKernel::JavaScript,
        JoernKernel::Python,
        JoernKernel::Ruby,
        JoernKernel::Php,
        JoernKernel::Rust,
    ] {
        let selected = select_joern_cases(kernel).unwrap();
        assert_eq!(selected.len(), 2 * kernel.templates().len());
        if challenge_rolled_out(kernel.language()) {
            assert!(selected.len() > KERNEL_CASE_COUNT);
        } else if kernel == JoernKernel::Rust {
            assert_eq!(selected.len(), KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
        } else {
            assert_eq!(selected.len(), KERNEL_CASE_COUNT);
        }
        let mut templates = BTreeMap::<String, (usize, usize)>::new();
        for (_, case) in &selected {
            assert_eq!(case["language"], kernel.language());
            assert_eq!(case["track"], "taint");
            assert_eq!(case["score_tier"], "core");
            assert_eq!(case["model_profile"], "benchmark-controlled");
            let counts = templates
                .entry(case["template_id"].as_str().unwrap().to_string())
                .or_default();
            if case["polarity"] == "positive" {
                counts.0 += 1;
            } else {
                counts.1 += 1;
            }
        }
        assert_eq!(templates.len(), kernel.templates().len());
        assert!(templates.values().all(|counts| *counts == (1, 1)));
        assert!(
            templates
                .keys()
                .all(|id| kernel.templates().contains(&id.as_str()))
        );
        populations.insert(
            kernel.language(),
            selected
                .iter()
                .map(|(_, case)| case["id"].as_str().unwrap().to_string())
                .collect::<BTreeSet<_>>(),
        );
    }
    for left in populations.values() {
        for right in populations.values() {
            if left != right {
                assert!(left.is_disjoint(right));
            }
        }
    }
}

#[test]
fn joern_report_paths_are_dedicated() {
    let kernels = [
        JoernKernel::Java,
        JoernKernel::JavaScript,
        JoernKernel::Python,
        JoernKernel::Ruby,
        JoernKernel::Php,
        JoernKernel::Rust,
    ];
    let reports = kernels
        .iter()
        .map(|kernel| kernel.report())
        .collect::<BTreeSet<_>>();
    let raw_dirs = kernels
        .iter()
        .map(|kernel| kernel.raw_dir())
        .collect::<BTreeSet<_>>();
    let frontends = kernels
        .iter()
        .map(|kernel| kernel.frontend())
        .collect::<BTreeSet<_>>();
    assert_eq!(reports.len(), kernels.len());
    assert_eq!(raw_dirs.len(), kernels.len());
    assert_eq!(frontends.len(), kernels.len());
    for kernel in kernels {
        assert!(kernel.report().starts_with("reports/joern-"));
        assert!(kernel.raw_dir().starts_with("reports/raw/joern-"));
        // A Joern report must never land on a CodeQL or Bifrost path.
        assert_ne!(kernel.report(), CODEQL_JAVASCRIPT_REPORT);
        assert_ne!(kernel.raw_dir(), CODEQL_JAVASCRIPT_RAW_DIR);
    }
    assert!(Path::new(JOERN_KERNEL_SCRIPT).is_file());
}

/// The kernel query is parameterized by the endpoints the fixture itself
/// declares. Two frozen Java assertions predate the `dfb_source`/`dfb_sink`
/// convention, so an adapter that assumed those names would silently
/// analyze nothing; the runner reads both names off the marker lines.
#[test]
fn joern_endpoints_come_from_the_case_markers() {
    let resolve = |id: &str, dialect: AnchorDialect| {
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            if case["id"] == id {
                return benchmark_endpoint_names(&path, &case, dialect).unwrap();
            }
        }
        panic!("case {id} is absent");
    };
    assert_eq!(
        resolve(
            "dfb-taint-java-alias-propagation-positive",
            AnchorDialect::Java
        ),
        BenchmarkEndpoints {
            source_function: "dfb_source".to_string(),
            sink_function: "dfb_sink".to_string()
        }
    );
    assert_eq!(
        resolve("dfb-taint-java-direct-positive", AnchorDialect::Java),
        BenchmarkEndpoints {
            source_function: "directUntrustedInput".to_string(),
            sink_function: "recordDirect".to_string()
        }
    );
    assert_eq!(
        resolve(
            "dfb-taint-javascript-alias-propagation-positive",
            AnchorDialect::Ecma
        ),
        BenchmarkEndpoints {
            source_function: "dfb_source".to_string(),
            sink_function: "dfb_sink".to_string()
        }
    );
    assert_eq!(
        resolve(
            "dfb-taint-python-alias-propagation-positive",
            AnchorDialect::Python
        ),
        BenchmarkEndpoints {
            source_function: "dfb_source".to_string(),
            sink_function: "dfb_sink".to_string()
        }
    );
    // Ruby's source declaration carries no parameter list at all, so the
    // endpoint name has to come from the `def` keyword rather than from an
    // identifier before `(`.
    assert_eq!(
        resolve(
            "dfb-taint-ruby-alias-propagation-positive",
            AnchorDialect::Ruby
        ),
        BenchmarkEndpoints {
            source_function: "dfb_source".to_string(),
            sink_function: "dfb_sink".to_string()
        }
    );
    assert_eq!(
        resolve(
            "dfb-taint-php-alias-propagation-positive",
            AnchorDialect::Php
        ),
        BenchmarkEndpoints {
            source_function: "dfb_source".to_string(),
            sink_function: "dfb_sink".to_string()
        }
    );
}

/// Ruby is the one dialect whose endpoint declarations may carry no
/// parameter list: `def dfb_source # DFB-SOURCE: ...` is a method
/// declaration exactly as `def dfb_sink(value) # DFB-SINK: ...` is. It
/// reaches a method through `.` and a constant path through `::`, and opens
/// comments with `#`.
#[test]
fn ruby_endpoint_declarations_resolve_through_the_ruby_dialect() {
    assert_eq!(
        AnchorDialect::Ruby
            .declared_function_name("def dfb_sink(value) # DFB-SINK: sink", "DFB-SINK: sink")
            .as_deref(),
        Some("dfb_sink")
    );
    assert_eq!(
        AnchorDialect::Ruby
            .declared_function_name("def dfb_source # DFB-SOURCE: input", "DFB-SOURCE: input")
            .as_deref(),
        Some("dfb_source")
    );
    assert_eq!(
        AnchorDialect::Ruby
            .declared_function_name(
                "  def self.dfb_source # DFB-SOURCE: input",
                "DFB-SOURCE: input"
            )
            .as_deref(),
        Some("dfb_source")
    );
    // A marker that is not on a declaration resolves to nothing rather than
    // to a guess.
    assert_eq!(
        AnchorDialect::Ruby
            .declared_function_name("  value = 0 # DFB-SINK: sink", "DFB-SINK: sink"),
        None
    );
    assert_eq!(
        AnchorDialect::Ruby
            .declared_function_name("  undef dfb_sink # DFB-SINK: sink", "DFB-SINK: sink"),
        None
    );
    assert!(AnchorDialect::Ruby.is_call("  dfb_sink(aliased.value)", "dfb_sink"));
    assert!(!AnchorDialect::Ruby.is_call("  other.dfb_sink(value)", "dfb_sink"));
    assert!(!AnchorDialect::Ruby.is_call("  Other::dfb_sink(value)", "dfb_sink"));
    assert!(!AnchorDialect::Ruby.is_call("  my_dfb_sink(value)", "dfb_sink"));
    assert!(!AnchorDialect::Ruby.is_call("  # dfb_sink(value)", "dfb_sink"));
    assert!(!AnchorDialect::Ruby.is_call("  log(\"dfb_sink(value)\")", "dfb_sink"));
}

/// PHP declares a function name before its parameter list, reaches an
/// instance member through `->` and a static one through `::`, and opens a
/// line comment with either `//` or `#`. Its `.` is string concatenation,
/// not a member operator, so a concatenated call is still a callsite.
#[test]
fn php_sink_declarations_and_callsites_resolve_through_the_php_dialect() {
    assert_eq!(
        AnchorDialect::Php
            .declared_function_name(
                "function dfb_sink(string $value): void {} // DFB-SINK: sink",
                "DFB-SINK: sink"
            )
            .as_deref(),
        Some("dfb_sink")
    );
    assert_eq!(
        AnchorDialect::Php
            .declared_function_name(
                "function dfb_source(): string { # DFB-SOURCE: input",
                "DFB-SOURCE: input"
            )
            .as_deref(),
        Some("dfb_source")
    );
    assert!(AnchorDialect::Php.is_call("    dfb_sink($alias->value);", "dfb_sink"));
    assert!(!AnchorDialect::Php.is_call("    $other->dfb_sink($value);", "dfb_sink"));
    assert!(!AnchorDialect::Php.is_call("    Other::dfb_sink($value);", "dfb_sink"));
    assert!(!AnchorDialect::Php.is_call("    my_dfb_sink($value);", "dfb_sink"));
    assert!(!AnchorDialect::Php.is_call("    // dfb_sink($value);", "dfb_sink"));
    assert!(!AnchorDialect::Php.is_call("    # dfb_sink($value);", "dfb_sink"));
    assert!(!AnchorDialect::Php.is_call("    log(\"dfb_sink($value)\");", "dfb_sink"));
    // `.` concatenates in PHP; it never qualifies a member.
    assert!(AnchorDialect::Php.is_call("    $text = $prefix . dfb_sink($value);", "dfb_sink"));
}

/// The Ruby kernel is its own Bifrost population. The tranche is gated on
/// Bifrost's Ruby indexing, so whatever this run produces is capability
/// evidence — but the selection itself must still be exactly the Ruby
/// expanded core assertions and nothing else.
#[test]
fn bifrost_ruby_kernel_selects_only_ruby_core_cases() {
    let mut core = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::RubyKernel) {
            assert!(ruby_core_case(&case));
            core += 1;
            for other in [
                BifrostRun::PythonKernel,
                BifrostRun::KotlinKernel,
                BifrostRun::TypescriptKernel,
                BifrostRun::CsharpKernel,
                BifrostRun::GoKernel,
                BifrostRun::CKernel,
                BifrostRun::CppKernel,
                BifrostRun::RustKernel,
                BifrostRun::PhpKernel,
            ] {
                assert!(!selected_bifrost_case(&case, other));
            }
        } else {
            assert!(!ruby_core_case(&case));
        }
    }
    // The Ruby row is rolled out, so the kernel run covers the expanded
    // core: 29 templates / 58 assertions, not the classic 32.
    assert_eq!(core, expected_core_case_count("ruby"));
    assert_eq!(core, 58);
    assert!(core > KERNEL_CASE_COUNT);
    assert_eq!(
        BifrostRun::RubyKernel.expected_core_cases(),
        Some(expected_core_case_count("ruby"))
    );
}

/// The Ruby CodeQL slice owns its own pack, query, report, and evidence
/// root, and is never pooled with another language's population.
#[test]
fn ruby_codeql_report_paths_are_dedicated() {
    for other in [
        CODEQL_KOTLIN_REPORT,
        CODEQL_CSHARP_REPORT,
        CODEQL_JAVASCRIPT_REPORT,
        CODEQL_TYPESCRIPT_REPORT,
        CODEQL_GO_REPORT,
        CODEQL_C_REPORT,
        CODEQL_CPP_REPORT,
        CODEQL_RUST_REPORT,
        "reports/codeql-python-kernel.json",
    ] {
        assert_ne!(CODEQL_RUBY_REPORT, other);
    }
    for other in [
        CODEQL_KOTLIN_RAW_DIR,
        CODEQL_CSHARP_RAW_DIR,
        CODEQL_JAVASCRIPT_RAW_DIR,
        CODEQL_TYPESCRIPT_RAW_DIR,
        CODEQL_GO_RAW_DIR,
        CODEQL_C_RAW_DIR,
        CODEQL_CPP_RAW_DIR,
        CODEQL_RUST_RAW_DIR,
    ] {
        assert_ne!(CODEQL_RUBY_RAW_DIR, other);
    }
    assert_ne!(CODEQL_RUBY_QUERY, CODEQL_PYTHON_QUERY);
    assert_eq!(CodeqlLanguage::Ruby.cli_name(), "ruby");
    assert!(!CodeqlLanguage::Ruby.traces_jvm_compile());

    // Ruby is buildless: no traced compile, no generated manifest.
    let case = json!({"id": "dfb-taint-ruby-test", "fixture_files": ["direct_flow.rb"]});
    let args = codeql_database_create_args(
        Path::new("/tmp/ruby-db"),
        Path::new("/tmp/ruby-workspace"),
        &case,
        CodeqlLanguage::Ruby,
    )
    .unwrap();
    assert!(args.iter().any(|arg| arg == "--language=ruby"));
    assert!(args.iter().any(|arg| arg == "--build-mode=none"));
    assert!(!args.iter().any(|arg| arg.starts_with("--command=")));

    let selected = codeql_ruby_cases().unwrap();
    // The Ruby row is rolled out, so the CodeQL population is the expanded
    // 29 templates / 58 assertions.
    assert_eq!(selected.len(), expected_core_case_count("ruby"));
    assert_eq!(selected.len(), 58);
    for (_, case) in &selected {
        assert_eq!(case["language"], "ruby");
        assert_eq!(case["score_tier"], "core");
    }
}

/// Java declares a sink as an identifier before a parameter list and calls
/// it unqualified; Python does the same but opens its comments with `#`.
#[test]
fn java_and_python_sink_declarations_resolve_through_their_dialects() {
    assert_eq!(
        AnchorDialect::Java
            .declared_function_name(
                "    static void dfb_sink(int value) { } // DFB-SINK: sink",
                "DFB-SINK: sink"
            )
            .as_deref(),
        Some("dfb_sink")
    );
    assert_eq!(
        AnchorDialect::Python
            .declared_function_name("def dfb_sink(value):  # DFB-SINK: sink", "DFB-SINK: sink")
            .as_deref(),
        Some("dfb_sink")
    );
    assert!(AnchorDialect::Java.is_call("        dfb_sink(alias.value);", "dfb_sink"));
    assert!(!AnchorDialect::Java.is_call("        other.dfb_sink(value);", "dfb_sink"));
    assert!(!AnchorDialect::Java.is_call("        my_dfb_sink(value);", "dfb_sink"));
    assert!(!AnchorDialect::Java.is_call("        // dfb_sink(value);", "dfb_sink"));
    assert!(AnchorDialect::Python.is_call("    dfb_sink(alias.value)", "dfb_sink"));
    assert!(!AnchorDialect::Python.is_call("    other.dfb_sink(value)", "dfb_sink"));
    // A Python comment must not be read as a callsite, even though it is
    // not a `//` comment.
    assert!(!AnchorDialect::Python.is_call("    # dfb_sink(value)", "dfb_sink"));
    assert!(!AnchorDialect::Python.is_call("    log(\"dfb_sink(value)\")", "dfb_sink"));
}

/// A Joern flow is only `reached` when it lands on a callsite of the case's
/// own anchored sink function.
#[test]
fn joern_flow_evidence_requires_the_sink_callsite() {
    let root = unique_test_dir("dataflowbench-joern-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("fixture.py"),
        "def dfb_sink(value):  # DFB-SINK: sink\n    pass\n\n\ndef run():\n    other(value)\n    dfb_sink(value)\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "fixture.py",
            "line_hint": 1
        }]
    });
    let analyzed = |flows: Value| {
        json!({
            "state": "analyzed",
            "source_node_count": 1,
            "sink_node_count": 1,
            "method_count": 3,
            "flows": flows
        })
    };
    let matching = analyzed(json!([{"elements": [
        {"file": "/tmp/work/fixture.py", "line": 7, "code": "value"}
    ]}]));
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &matching,
            AnchorDialect::Python,
            KERNEL_ENDPOINTS
        )
        .0,
        "reached"
    );
    let wrong_line = analyzed(json!([{"elements": [
        {"file": "fixture.py", "line": 6, "code": "value"}
    ]}]));
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &wrong_line,
            AnchorDialect::Python,
            KERNEL_ENDPOINTS
        )
        .0,
        "inconclusive"
    );
    let no_location = analyzed(json!([{"elements": [{"code": "value"}]}]));
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &no_location,
            AnchorDialect::Python,
            KERNEL_ENDPOINTS
        )
        .0,
        "inconclusive"
    );
    let empty_flow = analyzed(json!([{"elements": []}]));
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &empty_flow,
            AnchorDialect::Python,
            KERNEL_ENDPOINTS
        )
        .0,
        "inconclusive"
    );
    let clean = analyzed(json!([]));
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &clean,
            AnchorDialect::Python,
            KERNEL_ENDPOINTS
        )
        .0,
        "not-reached"
    );
    fs::remove_dir_all(root).unwrap();
}

/// A Joern script, frontend, or engine failure — and a run that never
/// observed one of the two benchmark-controlled endpoints — must never be
/// normalized to a clean negative.
#[test]
fn joern_runner_failures_never_become_clean_negatives() {
    let case_path = PathBuf::from("cases/taint/python/direct-positive/case.json");
    let case = json!({"sink_anchors": []});
    let failed = json!({
        "state": "runner-error",
        "stage": "joern-script",
        "diagnostic": "java.lang.RuntimeException: frontend failed"
    });
    let (outcome, diagnostics) = joern_flow_outcome(
        &case_path,
        &case,
        &failed,
        AnchorDialect::Python,
        KERNEL_ENDPOINTS,
    );
    assert_eq!(outcome, "runner-error");
    assert!(
        diagnostics
            .iter()
            .any(|line| line.contains("frontend failed"))
    );
    // The same document must also be refused as a downgraded negative by
    // the freeze's raw-evidence guard.
    assert_eq!(raw_special_outcome(&failed), Some("runner-error"));

    for broken in [
        json!({"state": "analyzed", "source_node_count": 1, "sink_node_count": 1}),
        json!({"state": "analyzed", "flows": []}),
        json!({"state": "surprise", "flows": []}),
        json!({"flows": []}),
    ] {
        assert_eq!(
            joern_flow_outcome(
                &case_path,
                &case,
                &broken,
                AnchorDialect::Python,
                KERNEL_ENDPOINTS
            )
            .0,
            "runner-error"
        );
    }

    for unobserved in [
        json!({"state": "analyzed", "source_node_count": 0, "sink_node_count": 1, "flows": []}),
        json!({"state": "analyzed", "source_node_count": 1, "sink_node_count": 0, "flows": []}),
    ] {
        assert_eq!(
            joern_flow_outcome(
                &case_path,
                &case,
                &unobserved,
                AnchorDialect::Python,
                KERNEL_ENDPOINTS
            )
            .0,
            "inconclusive"
        );
    }

    // An unresolvable sink anchor keeps a produced flow inconclusive rather
    // than crediting or discrediting it.
    let flows = json!({
        "state": "analyzed",
        "source_node_count": 1,
        "sink_node_count": 1,
        "flows": [{"elements": [{"file": "direct_flow.py", "line": 10}]}]
    });
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &flows,
            AnchorDialect::Python,
            KERNEL_ENDPOINTS
        )
        .0,
        "inconclusive"
    );
}

const SEMGREP_KERNELS: [SemgrepKernel; 11] = [
    SemgrepKernel::Java,
    SemgrepKernel::JavaScript,
    SemgrepKernel::TypeScript,
    SemgrepKernel::Python,
    SemgrepKernel::Go,
    SemgrepKernel::Ruby,
    SemgrepKernel::Php,
    SemgrepKernel::Kotlin,
    SemgrepKernel::Rust,
    SemgrepKernel::C,
    SemgrepKernel::Cpp,
];

/// Each Semgrep kernel is its own population: the balanced core assertions
/// of exactly one language, with no case shared between the eleven and no
/// case borrowed from a CodeQL, Joern, or Bifrost selection. The bounded
/// profile narrows what is *scored*, never what is selected — the balance
/// check still sees the whole kernel. C and Rust carry a fifteen-template
/// core because docs/applicability-matrix.md classifies their
/// exception-catch cell as inapplicable; an inapplicable cell reduces only
/// its own language's denominator.
#[test]
fn semgrep_kernel_selections_are_language_disjoint_and_balanced() {
    let mut populations = BTreeMap::new();
    for kernel in SEMGREP_KERNELS {
        let selected = select_semgrep_cases(kernel).unwrap();
        let expected_templates = kernel.templates();
        assert_eq!(selected.len(), 2 * expected_templates.len());
        if challenge_rolled_out(kernel.language()) {
            assert!(selected.len() > KERNEL_CASE_COUNT);
        } else {
            match kernel {
                SemgrepKernel::C | SemgrepKernel::Rust => {
                    assert_eq!(selected.len(), KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH);
                }
                _ => assert_eq!(selected.len(), KERNEL_CASE_COUNT),
            }
        }
        let mut templates = BTreeMap::<String, (usize, usize)>::new();
        for (_, case) in &selected {
            assert_eq!(case["language"], kernel.language());
            assert_eq!(case["track"], "taint");
            assert_eq!(case["score_tier"], "core");
            assert_eq!(case["model_profile"], "benchmark-controlled");
            let counts = templates
                .entry(case["template_id"].as_str().unwrap().to_string())
                .or_default();
            if case["polarity"] == "positive" {
                counts.0 += 1;
            } else {
                counts.1 += 1;
            }
        }
        assert_eq!(
            templates
                .keys()
                .map(String::as_str)
                .collect::<BTreeSet<_>>(),
            expected_templates.iter().copied().collect::<BTreeSet<_>>()
        );
        assert!(templates.values().all(|counts| *counts == (1, 1)));
        populations.insert(
            kernel.language(),
            selected
                .iter()
                .map(|(_, case)| case["id"].as_str().unwrap().to_string())
                .collect::<BTreeSet<_>>(),
        );
    }
    for left in populations.values() {
        for right in populations.values() {
            if left != right {
                assert!(left.is_disjoint(right));
            }
        }
    }
    // The `language-extension` tier is what C's error-code-return and
    // goto-cleanup cases and Rust's `Result`/`?` pair are scored on. None
    // of them is a core template, and none may be selected into a core
    // Semgrep run, where they would silently inflate the denominator.
    for extension in [
        "dfb-taint-c-error-code-return-positive",
        "dfb-taint-c-goto-cleanup-positive",
        "dfb-taint-rust-result-error-propagation-positive",
        "dfb-taint-rust-result-error-propagation-negative",
    ] {
        for population in populations.values() {
            assert!(
                !population.contains(extension),
                "{extension} is a language-extension case and must never enter a core Semgrep population"
            );
        }
    }
}

/// The maturity label is read off the pinned distribution's own
/// machine-readable language table and retained verbatim. Kotlin is
/// recorded `beta`; Rust, C, and C++ are recorded `alpha`; the seven
/// kernels that landed first are all `ga`. The label is retained evidence
/// about the front end, and it never appears in the partition decision:
/// `semgrep_capability_exclusion` reads only the case metadata.
#[test]
fn semgrep_language_maturity_is_recorded_and_never_scored_on() {
    assert_eq!(SemgrepKernel::Kotlin.documented_maturity(), "beta");
    for kernel in [SemgrepKernel::Rust, SemgrepKernel::C, SemgrepKernel::Cpp] {
        assert_eq!(kernel.documented_maturity(), "alpha");
    }
    for kernel in [
        SemgrepKernel::Java,
        SemgrepKernel::JavaScript,
        SemgrepKernel::TypeScript,
        SemgrepKernel::Python,
        SemgrepKernel::Go,
        SemgrepKernel::Ruby,
        SemgrepKernel::Php,
    ] {
        assert_eq!(kernel.documented_maturity(), "ga");
    }
    for kernel in SEMGREP_KERNELS {
        let diagnostic = semgrep_maturity_diagnostic(kernel);
        assert!(diagnostic.contains(kernel.display_name()));
        assert!(diagnostic.contains(kernel.documented_maturity()));
        assert!(diagnostic.contains("lang.json"));
    }
    // Two cases identical but for language: the exclusion decision cannot
    // see a maturity label, so it cannot differ between them.
    let case = |language: &str| {
        json!({
            "language": language,
            "feature_tags": ["heap-access-path"],
            "expected_analysis_capability": {"kind": "heap-alias-sensitive-taint"}
        })
    };
    assert_eq!(
        semgrep_capability_exclusion(&case("rust")),
        semgrep_capability_exclusion(&case("java"))
    );
}

/// The dialect a kernel picks has to be verified against that language's
/// real fixtures, not assumed from family resemblance. Kotlin adds no
/// `AnchorDialect` of its own: its markers sit on `fun name(params)`
/// declarations, its fixtures call the sink receiverlessly, `.` is the only
/// member operator that could precede the name, and `//` opens a comment —
/// which is the Java arm's contract exactly. This resolves every scored
/// case of all four newly covered kernels through its chosen dialect and
/// fails if any one of them cannot name its own endpoints.
#[test]
fn semgrep_new_kernels_resolve_every_scored_endpoint() {
    for kernel in [
        SemgrepKernel::Kotlin,
        SemgrepKernel::Rust,
        SemgrepKernel::C,
        SemgrepKernel::Cpp,
    ] {
        let mut scored = 0usize;
        for (path, case) in select_semgrep_cases(kernel).unwrap() {
            if semgrep_capability_exclusion(&case).is_some() {
                continue;
            }
            scored += 1;
            let endpoints = benchmark_endpoint_names(&path, &case, kernel.dialect())
                .unwrap_or_else(|reason| {
                    panic!("{} endpoints: {reason}", case["id"]);
                });
            assert_eq!(endpoints.source_function, "dfb_source", "{}", case["id"]);
            assert_eq!(endpoints.sink_function, "dfb_sink", "{}", case["id"]);
        }
        assert_eq!(scored, 14, "{} scored partition", kernel.label());
    }
    // The Kotlin surface rules the Java arm is being reused for, stated
    // directly rather than only exercised through the fixtures.
    assert_eq!(
        AnchorDialect::Java.declared_function_name(
            "    fun dfb_sink(value: String) {} // DFB-SINK: direct-sink",
            "DFB-SINK: direct-sink"
        ),
        Some("dfb_sink".to_string())
    );
    assert_eq!(
        AnchorDialect::Java.declared_function_name(
            "    fun dfb_source(): String { // DFB-SOURCE: direct-input",
            "DFB-SOURCE: direct-input"
        ),
        Some("dfb_source".to_string())
    );
    assert!(AnchorDialect::Java.is_call("        dfb_sink(alias.value)", "dfb_sink"));
    assert!(!AnchorDialect::Java.is_call("        other.dfb_sink(value)", "dfb_sink"));
    assert!(!AnchorDialect::Java.is_call("        // dfb_sink(value)", "dfb_sink"));
}

#[test]
fn semgrep_report_paths_and_rules_are_dedicated() {
    let reports = SEMGREP_KERNELS
        .iter()
        .map(|kernel| kernel.report())
        .collect::<BTreeSet<_>>();
    let raw_dirs = SEMGREP_KERNELS
        .iter()
        .map(|kernel| kernel.raw_dir())
        .collect::<BTreeSet<_>>();
    let rules = SEMGREP_KERNELS
        .iter()
        .map(|kernel| kernel.rule())
        .collect::<BTreeSet<_>>();
    assert_eq!(reports.len(), SEMGREP_KERNELS.len());
    assert_eq!(raw_dirs.len(), SEMGREP_KERNELS.len());
    assert_eq!(rules.len(), SEMGREP_KERNELS.len());
    for kernel in SEMGREP_KERNELS {
        assert!(kernel.report().starts_with("reports/semgrep-"));
        assert!(kernel.raw_dir().starts_with("reports/raw/semgrep-"));
        // A Semgrep report must never land on another adapter's path.
        assert_ne!(kernel.report().as_str(), CODEQL_JAVASCRIPT_REPORT);
        assert_ne!(kernel.report().as_str(), JOERN_JAVA_REPORT);
        assert_ne!(kernel.raw_dir().as_str(), JOERN_JAVA_RAW_DIR);
        // Every kernel's rule is committed, carries both placeholders, and
        // is written for that kernel's own Semgrep language.
        let rule = fs::read_to_string(kernel.rule()).unwrap();
        assert!(rule.contains(SEMGREP_SOURCE_PLACEHOLDER));
        assert!(rule.contains(SEMGREP_SINK_PLACEHOLDER));
        assert!(rule.contains("mode: taint"));
    }
    // The configuration hash binds every committed rule, so a change to any
    // one of them invalidates every retained Semgrep report.
    let hashed = semgrep_rule_paths().unwrap();
    for kernel in SEMGREP_KERNELS {
        assert!(hashed.contains(&PathBuf::from(kernel.rule())));
    }
}

/// Both OpenTaint kernels select their language's whole expanded core and
/// resolve every endpoint pair, on dedicated per-language paths, from
/// committed rule templates that carry both placeholders and the pinned
/// rule id the load-trace guard checks for.
#[test]
fn opentaint_kernels_are_language_scoped_and_resolvable() {
    let kernels = [
        OpentaintKernel::Java {
            javac: PathBuf::from("javac"),
        },
        OpentaintKernel::Kotlin {
            kotlinc: PathBuf::from("kotlinc"),
            kotlin_stdlib: PathBuf::from("kotlin-stdlib.jar"),
        },
    ];
    let hashed = opentaint_rule_paths();
    for kernel in &kernels {
        let language = kernel.language();
        assert_eq!(
            kernel.report(),
            format!("reports/opentaint-{language}-kernel.json")
        );
        assert_eq!(
            kernel.raw_dir(),
            format!("reports/raw/opentaint-{language}-kernel")
        );
        let rule = fs::read_to_string(kernel.rule()).unwrap();
        assert!(rule.contains(SEMGREP_SOURCE_PLACEHOLDER));
        assert!(rule.contains(SEMGREP_SINK_PLACEHOLDER));
        assert!(rule.contains("mode: taint"));
        assert!(rule.contains(&format!("id: {OPENTAINT_RULE_ID}")));
        // The engine keys its JVM rule front end on `java` for Kotlin
        // bytecode too; a `languages: [kotlin]` rule loads but matches
        // nothing, so this line is load-bearing in both templates.
        assert!(rule.contains("- java"));
        assert!(hashed.contains(&PathBuf::from(kernel.rule())));
        // The whole expanded core is selected and balanced, and every
        // case's endpoints resolve from its own markers, so no case can
        // fall out of the population silently.
        let selected = select_opentaint_cases(kernel).unwrap();
        assert_eq!(selected.len(), 2 * expected_core_templates(language).len());
        for (path, case) in &selected {
            benchmark_endpoint_names(path, case, kernel.dialect()).unwrap_or_else(|reason| {
                panic!("{} endpoints do not resolve: {reason}", path.display())
            });
        }
    }
}

/// The pinned identity is witnessed, never asserted: the constants are
/// well-formed digests, and an artifact whose measured digest is not the
/// pinned one is refused with both values in the error.
#[test]
fn opentaint_identity_is_witnessed_against_the_pin() {
    for constant in [
        OPENTAINT_ANALYZER_JAR_SHA256,
        OPENTAINT_MODELS_ARCHIVE_SHA256,
    ] {
        assert_eq!(constant.len(), 64);
        assert!(constant.chars().all(|c| c.is_ascii_hexdigit()));
    }
    let root = unique_test_dir("dataflowbench-opentaint-identity-test");
    let jar = root.join("not-the-pinned.jar");
    let models = root.join("not-the-pinned.tar.gz");
    fs::write(&jar, b"not the pinned analyzer").unwrap();
    fs::write(&models, b"not the pinned models").unwrap();
    let error = witness_opentaint_identity(&jar, &models)
        .unwrap_err()
        .to_string();
    assert!(error.contains("witnessed sha256"));
    assert!(error.contains(OPENTAINT_ANALYZER_JAR_SHA256));
    fs::remove_dir_all(&root).unwrap();
}

/// The rule-load guard is what keeps an unloaded rule from reading as a
/// clean negative: a load error disqualifies the evidence, and so does a
/// trace that never registered the benchmark rule.
#[test]
fn opentaint_rule_load_guard_refuses_silent_failures() {
    let loaded: Value = json!({"fileTraces": [{"path": "", "ruleTraces": [
        {"ruleId": ":dfb-opentaint-kernel", "ruleIdInFile": "dfb-opentaint-kernel",
         "entries": [{"type": "Info", "message": "Generate 4 rules"}]}
    ], "entries": [{"type": "Info", "message": "Register 1 rules"}]}]});
    assert!(opentaint_rule_load_failure(&loaded, OPENTAINT_RULE_ID).is_none());
    let errored: Value = json!({"fileTraces": [{"path": "", "entries": [
        {"type": "Error", "message": "Failed to load rule set", "severity": "BLOCKING"}
    ]}]});
    assert!(
        opentaint_rule_load_failure(&errored, OPENTAINT_RULE_ID)
            .unwrap()
            .contains("Failed to load rule set")
    );
    let unregistered: Value = json!({"fileTraces": [{"path": "", "entries": []}]});
    assert!(
        opentaint_rule_load_failure(&unregistered, OPENTAINT_RULE_ID)
            .unwrap()
            .contains("never registered")
    );
}

/// The package parser feeds the synthesized `project.yaml`; both JVM
/// spellings parse, and a packageless fixture is a contract violation
/// rather than a guess.
#[test]
fn opentaint_fixture_packages_parse_both_jvm_spellings() {
    assert_eq!(
        jvm_fixture_package("A.java", "package dataflowbench.taint;\nclass A {}").unwrap(),
        "dataflowbench.taint"
    );
    assert_eq!(
        jvm_fixture_package("A.kt", "package dataflowbench\n\nobject A {}").unwrap(),
        "dataflowbench"
    );
    assert!(jvm_fixture_package("A.java", "class A {}").is_err());
}

/// The Pysa kernel is language-scoped, selects Python's whole expanded
/// core, resolves every case's endpoints and anchor modules, and loads
/// committed configuration whose shapes are load-bearing: the one
/// declared rule is what reconciliation keys on, and the model template
/// binds the sink's single `value` parameter — Pysa refuses a model whose
/// signature does not match the definition, so the uniform fixture shape
/// is pinned here before a drifted fixture could fail a population run.
#[test]
fn pysa_kernel_is_language_scoped_and_resolvable() {
    let hashed = pysa_configuration_paths();
    assert!(hashed.contains(&PathBuf::from(pysa_taint_config_path())));
    assert!(hashed.contains(&PathBuf::from(pysa_model_template_path())));
    let taint_config: Value =
        serde_json::from_str(&fs::read_to_string(pysa_taint_config_path()).unwrap()).unwrap();
    let rules = taint_config["rules"].as_array().unwrap();
    assert_eq!(rules.len(), 1);
    assert_eq!(rules[0]["code"].as_u64(), Some(PYSA_RULE_CODE));
    assert_eq!(rules[0]["sources"], json!(["DfbSource"]));
    assert_eq!(rules[0]["sinks"], json!(["DfbSink"]));
    let template = fs::read_to_string(pysa_model_template_path()).unwrap();
    for placeholder in [
        SEMGREP_SOURCE_PLACEHOLDER,
        SEMGREP_SINK_PLACEHOLDER,
        PYSA_SOURCE_MODULE_PLACEHOLDER,
        PYSA_SINK_MODULE_PLACEHOLDER,
    ] {
        assert!(template.contains(placeholder));
    }
    let selected = select_pysa_cases().unwrap();
    assert_eq!(selected.len(), 2 * expected_core_templates("python").len());
    for (path, case) in &selected {
        let endpoints =
            benchmark_endpoint_names(path, case, AnchorDialect::Python).unwrap_or_else(|reason| {
                panic!("{} endpoints do not resolve: {reason}", path.display())
            });
        // The committed model template hardcodes the sink's one parameter
        // as `value`, and Pysa refuses a model whose signature does not
        // match the definition — loudly, as a runner error. This pins the
        // uniform shape so a drifted fixture is caught here first.
        let fixture_root = path.parent().unwrap();
        let sink_anchor = &case["sink_anchors"][0];
        let body =
            fs::read_to_string(fixture_root.join(sink_anchor["file"].as_str().unwrap())).unwrap();
        let declaration = body
            .lines()
            .find(|line| line.contains(sink_anchor["marker"].as_str().unwrap()))
            .unwrap();
        assert!(
            declaration.contains(&format!("def {}(value)", endpoints.sink_function)),
            "{} sink declaration {declaration:?} is not the single-`value` shape the committed model template binds",
            path.display()
        );
        pysa_anchor_module(sink_anchor["file"].as_str().unwrap()).unwrap();
        pysa_anchor_module(case["source_anchors"][0]["file"].as_str().unwrap()).unwrap();
    }
}

/// Both pinned versions are witnessed, never asserted: a client or front
/// end reporting any other version is refused with both values in the
/// error, and the accepted identity carries the measured digests of both
/// binaries.
#[test]
#[cfg(unix)]
fn pysa_identity_is_witnessed_against_the_pins() {
    use std::os::unix::fs::PermissionsExt;
    let root = unique_test_dir("dataflowbench-pysa-identity-test");
    let write_fake = |name: &str, line: &str| {
        let path = root.join(name);
        fs::write(&path, format!("#!/bin/sh\necho \"{line}\"\n")).unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o755)).unwrap();
        path
    };
    let pinned_pyre = write_fake(
        "pyre",
        &format!("Client version: {PYSA_PINNED_PYRE_VERSION}"),
    );
    let pinned_pyrefly = write_fake("pyrefly", &format!("pyrefly {PYSA_PINNED_PYREFLY_VERSION}"));
    let binary = root.join("pyre.bin");
    fs::write(&binary, b"analysis binary bytes").unwrap();
    let wrong_pyre = write_fake("pyre-wrong", "Client version: 0.0.1");
    let error = witness_pysa_identity(&PysaTools {
        pyre: wrong_pyre,
        pyre_binary: binary.clone(),
        pyrefly: pinned_pyrefly.clone(),
    })
    .unwrap_err()
    .to_string();
    assert!(error.contains("0.0.1"));
    assert!(error.contains(PYSA_PINNED_PYRE_VERSION));
    let wrong_pyrefly = write_fake("pyrefly-wrong", "pyrefly 0.0.1");
    let error = witness_pysa_identity(&PysaTools {
        pyre: pinned_pyre.clone(),
        pyre_binary: binary.clone(),
        pyrefly: wrong_pyrefly,
    })
    .unwrap_err()
    .to_string();
    assert!(error.contains("0.0.1"));
    assert!(error.contains(PYSA_PINNED_PYREFLY_VERSION));
    let (version, build_identity) = witness_pysa_identity(&PysaTools {
        pyre: pinned_pyre,
        pyre_binary: binary,
        pyrefly: pinned_pyrefly,
    })
    .unwrap();
    assert_eq!(version, PYSA_PINNED_PYRE_VERSION);
    assert!(build_identity.contains("pyre.bin-sha256:"));
    assert!(build_identity.contains("pyrefly-sha256:"));
    fs::remove_dir_all(&root).unwrap();
}

/// The activation guard proves from the retained evidence itself that
/// both benchmark endpoints were bound, so a clean `not-reached` can
/// never come from a run whose models silently failed to attach; and
/// reconciliation reads only the declared rule's issues on anchored sink
/// callsites.
#[test]
fn pysa_evidence_guard_and_anchor_match_read_the_retained_document() {
    let raw = concat!(
        "{\"file_version\":3}\n",
        "{\"kind\":\"model\",\"data\":{\"callable\":\"direct_flow.dfb_source\",\"sources\":[{}]}}\n",
        "{\"kind\":\"model\",\"data\":{\"callable\":\"direct_flow.dfb_sink\",\"sinks\":[{}]}}\n",
        "{\"kind\":\"issue\",\"data\":{\"code\":9901,\"filename\":\"src/direct_flow.py\",\"line\":10,\"traces\":[{\"name\":\"backward\",\"roots\":[{\"origin\":{\"line\":10},\"call_site\":\"10:4-10:26\"}]}]}}\n",
    );
    let evidence = parse_pysa_evidence(raw).unwrap();
    assert_eq!(evidence.issues.len(), 1);
    assert!(
        pysa_model_activation_failure(&evidence, "direct_flow.dfb_source", "direct_flow.dfb_sink")
            .is_none()
    );
    assert!(
        pysa_model_activation_failure(
            &evidence,
            "direct_flow.dfb_source",
            "direct_flow.other_sink"
        )
        .unwrap()
        .contains("other_sink")
    );
    let anchors = vec![SinkAnchorLocation {
        file: "direct_flow.py".to_string(),
        marker_line: 5,
        function_name: "dfb_sink".to_string(),
        callsite_lines: BTreeSet::from([10]),
    }];
    assert_eq!(
        pysa_issue_anchor_match(&evidence.issues[0], &anchors),
        EvidenceAnchorMatch::Matched
    );
    let elsewhere = vec![SinkAnchorLocation {
        file: "direct_flow.py".to_string(),
        marker_line: 5,
        function_name: "dfb_sink".to_string(),
        callsite_lines: BTreeSet::from([99]),
    }];
    assert_eq!(
        pysa_issue_anchor_match(&evidence.issues[0], &elsewhere),
        EvidenceAnchorMatch::Unmatched
    );
    let no_location: Value = json!({"code": 9901, "traces": []});
    assert_eq!(
        pysa_issue_anchor_match(&no_location, &anchors),
        EvidenceAnchorMatch::Ambiguous
    );
}

/// Each Infer kernel is language-scoped, selects its whole expanded core,
/// resolves every case's endpoints under its own dialect, and loads a
/// committed taint-configuration template whose matcher shapes are
/// load-bearing: the pinned binary's plain `procedure` matcher is a
/// substring match (verified in the field — `dfb_source` matches
/// `dfb_source_extra`), so the C and C++ templates must carry the
/// anchored `^…$` regex form and the Java template the `\.…(`
/// signature-bounded form, or an endpoint name that prefixes another
/// identifier would silently widen the taint question.
#[test]
fn infer_kernels_are_language_scoped_and_resolvable() {
    let kernels = [
        InferKernel::C,
        InferKernel::Cpp,
        InferKernel::Java {
            javac: PathBuf::from("javac"),
        },
    ];
    let hashed = infer_config_paths();
    for kernel in &kernels {
        let language = kernel.language();
        assert_eq!(
            kernel.report(),
            format!("reports/infer-{language}-kernel.json")
        );
        assert_eq!(
            kernel.raw_dir(),
            format!("reports/raw/infer-{language}-kernel")
        );
        let template_path = kernel.config_template();
        let template = fs::read_to_string(&template_path).unwrap();
        assert!(template.contains(SEMGREP_SOURCE_PLACEHOLDER));
        assert!(template.contains(SEMGREP_SINK_PLACEHOLDER));
        let expected_source_regex = match kernel {
            InferKernel::Java { .. } => "\\.__DFB_SOURCE__(".to_string(),
            _ => "^__DFB_SOURCE__$".to_string(),
        };
        let parsed: Value = serde_json::from_str(&template).unwrap();
        assert_eq!(
            parsed["pulse-taint-sources"][0]["procedure_regex"]
                .as_str()
                .unwrap(),
            expected_source_regex,
            "{template_path} does not pin the exact-match regex shape"
        );
        assert!(
            !parsed["pulse-taint-policies"]
                .as_array()
                .unwrap()
                .is_empty(),
            "{template_path} declares no policy, so no flow could ever be reported"
        );
        // The resolved configuration must stay valid JSON once the
        // placeholders become real identifiers.
        let resolved = template
            .replace(SEMGREP_SOURCE_PLACEHOLDER, "dfb_source")
            .replace(SEMGREP_SINK_PLACEHOLDER, "dfb_sink");
        serde_json::from_str::<Value>(&resolved).unwrap();
        assert!(hashed.contains(&PathBuf::from(&template_path)));
        let selected = select_infer_cases(kernel).unwrap();
        assert_eq!(selected.len(), 2 * expected_core_templates(language).len());
        for (path, case) in &selected {
            benchmark_endpoint_names(path, case, kernel.dialect()).unwrap_or_else(|reason| {
                panic!("{} endpoints do not resolve: {reason}", path.display())
            });
        }
    }
}

/// The pinned Infer version is witnessed, never asserted: a binary
/// reporting any other version is refused with both values in the error,
/// and the accepted identity carries the measured digest of the binary's
/// bytes.
#[test]
#[cfg(unix)]
fn infer_identity_is_witnessed_against_the_pin() {
    use std::os::unix::fs::PermissionsExt;
    let root = unique_test_dir("dataflowbench-infer-identity-test");
    let write_fake = |name: &str, version: &str| {
        let path = root.join(name);
        fs::write(
            &path,
            format!("#!/bin/sh\necho \"Infer version {version}\"\n"),
        )
        .unwrap();
        fs::set_permissions(&path, fs::Permissions::from_mode(0o755)).unwrap();
        path
    };
    let wrong = write_fake("wrong-version", "v0.0.1");
    let error = witness_infer_identity(&wrong).unwrap_err().to_string();
    assert!(error.contains("v0.0.1"));
    assert!(error.contains(INFER_PINNED_VERSION));
    let pinned = write_fake("pinned-version", INFER_PINNED_VERSION);
    let (version, build_identity) = witness_infer_identity(&pinned).unwrap();
    assert_eq!(version, INFER_PINNED_VERSION);
    assert!(build_identity.contains("bin-sha256:"));
    fs::remove_dir_all(&root).unwrap();
}

/// Reconciliation reads only the benchmark taint policy's own rule id as
/// flow evidence. Pulse reports memory-safety issues under `--pulse-only`
/// too, and one of those landing on a sink callsite must never read as
/// `reached` — it is retained as a diagnostic instead.
#[test]
fn infer_reconciliation_reads_only_the_taint_policy() {
    let location = |line: u64| {
        json!({"physicalLocation": {
            "artifactLocation": {"uri": "file:dispatch_table.c"},
            "region": {"startLine": line}
        }})
    };
    let sarif = json!({"runs": [{"results": [
        {"ruleId": "TAINT_ERROR", "message": {"text": "taint"},
         "locations": [location(31)],
         "codeFlows": [{"threadFlows": [{"locations": [
             {"location": location(8)},
             {"location": location(15)}
         ]}]}]},
        {"ruleId": "NULLPTR_DEREFERENCE", "message": {"text": "null"}}
    ]}]});
    let (filtered, diagnostics) = infer_taint_results_only(&sarif);
    assert_eq!(sarif_result_count(&filtered), 1);
    let result = &filtered["runs"][0]["results"][0];
    assert_eq!(result["ruleId"], INFER_TAINT_RULE_ID);
    // The final code-flow step — the engine's own sink reach — is part of
    // the reconciliation view, because the top-level location sits at the
    // reporting point, which for a flow through a function pointer is the
    // indirect callsite rather than the anchored sink's own.
    let lines = result["locations"]
        .as_array()
        .unwrap()
        .iter()
        .map(|l| {
            l["physicalLocation"]["region"]["startLine"]
                .as_u64()
                .unwrap()
        })
        .collect::<Vec<_>>();
    assert_eq!(lines, vec![31, 15]);
    assert_eq!(diagnostics.len(), 1);
    assert!(diagnostics[0].contains("NULLPTR_DEREFERENCE"));
    // The verbatim evidence is untouched.
    assert_eq!(sarif_result_count(&sarif), 2);
    assert_eq!(
        sarif["runs"][0]["results"][0]["locations"]
            .as_array()
            .unwrap()
            .len(),
        1
    );
}

/// Each FlowDroid kernel is language-scoped, selects its whole expanded
/// core, resolves every case's endpoints under its own dialect, and
/// loads committed materialization artifacts: a binary (AXML) manifest
/// blob, a wrapper template carrying both placeholders, and the endpoint
/// template carrying both signature placeholders — all bound into one
/// configuration hash.
#[test]
fn flowdroid_kernels_are_language_scoped_and_resolvable() {
    let kernels = [
        FlowdroidKernel::Java {
            javac: PathBuf::from("javac"),
        },
        FlowdroidKernel::Kotlin {
            kotlinc: PathBuf::from("kotlinc"),
            kotlin_stdlib: PathBuf::from("kotlin-stdlib.jar"),
        },
    ];
    let hashed = flowdroid_template_paths();
    let endpoint_template =
        fs::read_to_string(format!("{FLOWDROID_CONFIG_DIR}/sources-sinks.txt")).unwrap();
    assert!(endpoint_template.contains(FLOWDROID_SOURCES_PLACEHOLDER));
    assert!(endpoint_template.contains(FLOWDROID_SINKS_PLACEHOLDER));
    assert!(hashed.contains(&PathBuf::from(format!(
        "{FLOWDROID_CONFIG_DIR}/sources-sinks.txt"
    ))));
    for kernel in &kernels {
        let language = kernel.language();
        assert_eq!(
            kernel.report(),
            format!("reports/flowdroid-{language}-kernel.json")
        );
        assert_eq!(
            kernel.raw_dir(),
            format!("reports/raw/flowdroid-{language}-kernel")
        );
        let wrapper = fs::read_to_string(kernel.wrapper_template()).unwrap();
        assert!(wrapper.contains(FLOWDROID_PACKAGE_PLACEHOLDER));
        assert!(wrapper.contains(FLOWDROID_ENTRY_CALL_PLACEHOLDER));
        assert!(hashed.contains(&PathBuf::from(kernel.wrapper_template())));
        // The committed manifest is binary Android XML — FlowDroid's
        // manifest parser reads AXML, not text — and its first bytes are
        // the AXML document header.
        let manifest = fs::read(kernel.manifest()).unwrap();
        assert_eq!(&manifest[..4], &[0x03, 0x00, 0x08, 0x00]);
        assert!(hashed.contains(&PathBuf::from(kernel.manifest())));
        // The whole expanded core is selected and balanced, and every
        // case's endpoints resolve from its own markers, so no case can
        // fall out of the population silently.
        let selected = select_flowdroid_cases(kernel).unwrap();
        assert_eq!(selected.len(), 2 * expected_core_templates(language).len());
        for (path, case) in &selected {
            benchmark_endpoint_names(path, case, kernel.dialect()).unwrap_or_else(|reason| {
                panic!("{} endpoints do not resolve: {reason}", path.display())
            });
        }
    }
}

/// The pinned identity is witnessed, never asserted: the constants are
/// well-formed digests, and an artifact whose measured digest is not the
/// pinned one is refused with both values in the error.
#[test]
fn flowdroid_identity_is_witnessed_against_the_pin() {
    for constant in [FLOWDROID_JAR_SHA256, FLOWDROID_ANDROID_PLATFORM_SHA256] {
        assert_eq!(constant.len(), 64);
        assert!(constant.chars().all(|c| c.is_ascii_hexdigit()));
    }
    let root = unique_test_dir("dataflowbench-flowdroid-identity-test");
    let jar = root.join("not-the-pinned.jar");
    let platform = root.join("not-the-pinned-platform.jar");
    fs::write(&jar, b"not the pinned analyzer").unwrap();
    fs::write(&platform, b"not the pinned platform").unwrap();
    let error = witness_flowdroid_identity(&jar, &platform)
        .unwrap_err()
        .to_string();
    assert!(error.contains("witnessed sha256"));
    assert!(error.contains(FLOWDROID_JAR_SHA256));
    fs::remove_dir_all(&root).unwrap();
}

/// A minimal class file for the parser tests: one class, the given
/// methods, an empty attribute set everywhere.
fn flowdroid_test_class(binary_name: &str, methods: &[(&str, &str, u16)]) -> Vec<u8> {
    let internal = binary_name.replace('.', "/");
    let mut pool: Vec<Vec<u8>> = Vec::new();
    let mut utf8 = |value: &str| -> u16 {
        let mut entry = vec![1u8];
        entry.extend_from_slice(&(value.len() as u16).to_be_bytes());
        entry.extend_from_slice(value.as_bytes());
        pool.push(entry);
        pool.len() as u16
    };
    let name_index = utf8(&internal);
    let mut method_indices = Vec::new();
    for (name, descriptor, flags) in methods {
        method_indices.push((utf8(name), utf8(descriptor), *flags));
    }
    let class_index = {
        let mut entry = vec![7u8];
        entry.extend_from_slice(&name_index.to_be_bytes());
        pool.push(entry);
        pool.len() as u16
    };
    let mut bytes = 0xCAFE_BABEu32.to_be_bytes().to_vec();
    bytes.extend_from_slice(&0u16.to_be_bytes()); // minor
    bytes.extend_from_slice(&52u16.to_be_bytes()); // major
    bytes.extend_from_slice(&((pool.len() + 1) as u16).to_be_bytes());
    for entry in &pool {
        bytes.extend_from_slice(entry);
    }
    bytes.extend_from_slice(&0x0020u16.to_be_bytes()); // access flags
    bytes.extend_from_slice(&class_index.to_be_bytes());
    bytes.extend_from_slice(&0u16.to_be_bytes()); // super
    bytes.extend_from_slice(&0u16.to_be_bytes()); // interfaces
    bytes.extend_from_slice(&0u16.to_be_bytes()); // fields
    bytes.extend_from_slice(&(method_indices.len() as u16).to_be_bytes());
    for (name_index, descriptor_index, flags) in method_indices {
        bytes.extend_from_slice(&flags.to_be_bytes());
        bytes.extend_from_slice(&name_index.to_be_bytes());
        bytes.extend_from_slice(&descriptor_index.to_be_bytes());
        bytes.extend_from_slice(&0u16.to_be_bytes()); // attributes
    }
    bytes
}

/// The endpoint signatures FlowDroid is given are witnessed from the
/// compiled bytecode: the class parser reads names and descriptors, the
/// descriptor conversion spells the Java types Soot signatures use, and
/// compiler-synthesized members are invisible.
#[test]
fn flowdroid_signatures_are_witnessed_from_bytecode() {
    let class = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.DirectPositive",
        &[
            ("directUntrustedInput", "()I", 0x0008),
            ("recordDirect", "(I)V", 0x0008),
            ("fancy", "([Ljava/lang/String;J)[[D", 0x0008),
            ("recordDirect", "(Ljava/lang/Object;)V", 0x1008), // synthetic
        ],
    ))
    .unwrap();
    assert_eq!(class.binary_name, "dataflowbench.taint.DirectPositive");
    let classes = vec![class];
    assert_eq!(
        flowdroid_endpoint_signatures(&classes, "directUntrustedInput")
            .unwrap()
            .into_iter()
            .collect::<Vec<_>>(),
        vec!["<dataflowbench.taint.DirectPositive: int directUntrustedInput()>".to_string()]
    );
    // The synthetic overload never widens the endpoint set.
    assert_eq!(
        flowdroid_endpoint_signatures(&classes, "recordDirect")
            .unwrap()
            .into_iter()
            .collect::<Vec<_>>(),
        vec!["<dataflowbench.taint.DirectPositive: void recordDirect(int)>".to_string()]
    );
    assert_eq!(
        flowdroid_endpoint_signatures(&classes, "fancy")
            .unwrap()
            .into_iter()
            .collect::<Vec<_>>(),
        vec![
            "<dataflowbench.taint.DirectPositive: double[][] fancy(java.lang.String[],long)>"
                .to_string()
        ]
    );
    assert!(
        flowdroid_endpoint_signatures(&classes, "absent")
            .unwrap_err()
            .contains("no compiled fixture class")
    );
}

/// The harness entry call is witnessed from the compiled classes and
/// supports exactly the two shapes the core fixtures declare; the
/// boolean shape's argument is derived from the activity bundle so it
/// stays statically unknown. Anything else is unresolvable, never a
/// synthesized outcome.
#[test]
fn flowdroid_entry_call_supports_the_two_fixture_shapes() {
    let plain = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.DirectPositive",
        &[("run", "()V", 0x0008)],
    ))
    .unwrap();
    assert_eq!(
        flowdroid_entry_call(&[plain]).unwrap(),
        "DirectPositive.run()"
    );
    let boolean = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.BranchJoinPositive",
        &[("run", "(Z)V", 0x0008)],
    ))
    .unwrap();
    assert_eq!(
        flowdroid_entry_call(&[boolean]).unwrap(),
        "BranchJoinPositive.run(savedInstanceState == null)"
    );
    let none = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.Helper",
        &[("helper", "()V", 0x0008)],
    ))
    .unwrap();
    assert!(
        flowdroid_entry_call(&[none])
            .unwrap_err()
            .contains("found 0")
    );
    let extra = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.Extra",
        &[("run", "()V", 0x0008), ("run", "(I)V", 0x0008)],
    ))
    .unwrap();
    assert!(
        flowdroid_entry_call(&[extra])
            .unwrap_err()
            .contains("found 2")
    );
    let unsupported = parse_class_file(&flowdroid_test_class(
        "dataflowbench.taint.Odd",
        &[("run", "(I)V", 0x0008)],
    ))
    .unwrap();
    assert!(
        flowdroid_entry_call(&[unsupported])
            .unwrap_err()
            .contains("unsupported descriptor")
    );
}

/// Reconciliation reads FlowDroid's own results document: the
/// self-reported `TerminationState` and each result's echoed sink
/// definition, with the writer's XML entities unescaped.
#[test]
fn flowdroid_results_xml_reading_is_exact() {
    let xml = r#"<?xml version="1.0" encoding="UTF-8"?><DataFlowResults FileFormatVersion="102" TerminationState="Success"><Results><Result><Sink Statement="staticinvoke &lt;a.B: void dfb_sink(int)&gt;($i0)" Method="&lt;a.B: void run()&gt;" MethodSourceSinkDefinition="&lt;a.B: void dfb_sink(int)&gt;"></Sink></Result></Results></DataFlowResults>"#;
    assert_eq!(flowdroid_termination_state(xml).as_deref(), Some("Success"));
    assert_eq!(
        flowdroid_sink_definitions(xml),
        vec!["<a.B: void dfb_sink(int)>".to_string()]
    );
    let timed_out = xml.replace("Success", "DataFlowTimeout");
    assert_eq!(
        flowdroid_termination_state(&timed_out).as_deref(),
        Some("DataFlowTimeout")
    );
    assert_eq!(flowdroid_termination_state("<NotResults/>"), None);
    assert_eq!(xml_unescape("&lt;x&gt; &quot;&apos;&amp;"), "<x> \"'&");
}

/// The completion guard is what keeps the pinned CLI's zero-exit failure
/// modes from reading as clean negatives: the failure banner
/// disqualifies the run, a log with no completion line proves nothing,
/// and only the analyzer's own "Found N leaks" line reports a count.
#[test]
fn flowdroid_completion_guard_refuses_silent_failures() {
    assert_eq!(
        flowdroid_completion_leaks("[main] INFO SetupApplication - Found 0 leaks from 0 sources"),
        Ok(0)
    );
    assert_eq!(
        flowdroid_completion_leaks("[main] INFO SetupApplication - Found 3 leaks from 2 sources"),
        Ok(3)
    );
    assert!(
        flowdroid_completion_leaks(
            "The data flow analysis has failed. Error message: Parse app resource failed"
        )
        .unwrap_err()
        .contains("reported failure")
    );
    // A crash after the completion line would still print the banner
    // somewhere in the log; the banner wins over the count.
    assert!(
        flowdroid_completion_leaks(
            "Found 0 leaks from 0 sources\nThe data flow analysis has failed"
        )
        .is_err()
    );
    assert!(
        flowdroid_completion_leaks("Initializing Soot...")
            .unwrap_err()
            .contains("no completion line")
    );
}

/// The stored-zip writer produces a structurally whole archive — the CRC
/// is the standard zip polynomial and the end-of-central-directory
/// record counts every entry — since a malformed APK would surface as an
/// analyzer parse failure attributed to the tool.
#[test]
fn flowdroid_apk_zip_writer_is_structurally_whole() {
    assert_eq!(zip_crc32(b"123456789"), 0xCBF4_3926);
    let root = unique_test_dir("dataflowbench-flowdroid-zip-test");
    let path = root.join("case.apk");
    write_stored_zip(
        &path,
        &[
            ("AndroidManifest.xml", b"manifest".as_slice()),
            ("classes.dex", b"dex-bytes".as_slice()),
        ],
    )
    .unwrap();
    let bytes = fs::read(&path).unwrap();
    assert_eq!(&bytes[..4], &0x0403_4B50u32.to_le_bytes());
    let eocd = bytes.len() - 22;
    assert_eq!(&bytes[eocd..eocd + 4], &0x0605_4B50u32.to_le_bytes());
    assert_eq!(
        u16::from_le_bytes([bytes[eocd + 10], bytes[eocd + 11]]),
        2,
        "the central directory must count both entries"
    );
    fs::remove_dir_all(&root).unwrap();
}

/// Infer spells a workspace-relative SARIF artifact with a bare `file:`
/// scheme and no slashes; the shared path matcher must resolve it against
/// the case's anchor file, without loosening any other spelling.
#[test]
fn evidence_path_matcher_strips_the_bare_file_scheme() {
    assert!(evidence_path_matches_file(
        "file:direct_flow.c",
        "direct_flow.c"
    ));
    assert!(evidence_path_matches_file(
        "file:dataflowbench/taint/DirectPositive.java",
        "DirectPositive.java"
    ));
    assert!(evidence_path_matches_file(
        "file:///workspace/direct_flow.c",
        "direct_flow.c"
    ));
    assert!(!evidence_path_matches_file(
        "file:other_flow.c",
        "direct_flow.c"
    ));
}

/// The bounded profile is a declared-capability decision taken from the
/// case's own metadata *before* Semgrep is invoked. This test reads only
/// `case.json` files — no Semgrep binary is required or consulted — so an
/// out-of-profile case can never be run and then counted as a miss.
#[test]
fn semgrep_unsupported_partition_is_metadata_driven() {
    for kernel in SEMGREP_KERNELS {
        let selected = select_semgrep_cases(kernel).unwrap();
        let mut scored = 0usize;
        let mut excluded = 0usize;
        for (_, case) in &selected {
            let tags: BTreeSet<&str> = case["feature_tags"]
                .as_array()
                .unwrap()
                .iter()
                .filter_map(Value::as_str)
                .collect();
            match semgrep_capability_exclusion(case) {
                None => {
                    assert!(
                        tags.contains("intraprocedural"),
                        "{} is scored but is not tagged intraprocedural",
                        case["id"]
                    );
                    scored += 1;
                }
                Some(reason) => {
                    assert!(
                        !tags.contains("intraprocedural"),
                        "{} is tagged intraprocedural but was excluded",
                        case["id"]
                    );
                    assert!(reason.contains("outside the bounded Semgrep CE profile"));
                    excluded += 1;
                }
            }
        }
        // Seven templates are intraprocedural in every language, and the
        // partition keeps each one's positive/negative pair together, so
        // the scored subset is 14 assertions everywhere. Only the
        // `unsupported` remainder differs: C and Rust have no
        // exception-catch pair to exclude, so theirs is 16 rather than 18,
        // and a language whose challenge row is rolled out carries the
        // whole challenge tier in the remainder — every challenge template
        // is outside the CE profile, so none of them moves the scored
        // subset off 14.
        assert_eq!(scored, 14, "{} scored partition", kernel.label());
        let expected_excluded = 2 * kernel.templates().len() - 14;
        assert_eq!(
            excluded,
            expected_excluded,
            "{} unsupported partition",
            kernel.label()
        );
        if challenge_rolled_out(kernel.language()) {
            assert!(expected_excluded > 18);
        } else {
            match kernel {
                SemgrepKernel::C | SemgrepKernel::Rust => assert_eq!(expected_excluded, 16),
                _ => assert_eq!(expected_excluded, 18),
            }
        }
    }
    // Every interprocedural and heap relay is excluded by tag, whatever the
    // language, and the retained reason names the documented boundary.
    let interprocedural = json!({
        "feature_tags": ["interprocedural-one-hop"],
        "expected_analysis_capability": {"kind": "context-sensitive-interprocedural-taint"}
    });
    let reason = semgrep_capability_exclusion(&interprocedural).unwrap();
    assert!(reason.contains("--pro-intrafile"));
    let heap = json!({
        "feature_tags": ["heap-access-path"],
        "expected_analysis_capability": {"kind": "heap-alias-sensitive-taint"}
    });
    assert!(
        semgrep_capability_exclusion(&heap)
            .unwrap()
            .contains("field-sensitive")
    );
    assert_eq!(
        semgrep_capability_exclusion(&json!({
            "feature_tags": ["intraprocedural"],
            "expected_analysis_capability": {"kind": "intraprocedural-taint"}
        })),
        None
    );
}

/// A Semgrep finding is only `reached` when it lands on a callsite of the
/// case's own anchored sink function.
#[test]
fn semgrep_finding_evidence_requires_the_sink_callsite() {
    let root = unique_test_dir("dataflowbench-semgrep-anchor-test");
    let case_path = root.join("case.json");
    fs::write(
        root.join("fixture.py"),
        "def dfb_sink(value):  # DFB-SINK: sink\n    pass\n\n\ndef run():\n    other(value)\n    dfb_sink(value)\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{
            "marker": "DFB-SINK: sink",
            "file": "fixture.py",
            "line_hint": 1
        }]
    });
    let scanned = |results: Value| {
        json!({
            "version": "1.174.0",
            "results": results,
            "errors": [],
            "skipped_rules": [],
            "paths": {"scanned": ["/tmp/work/fixture.py"]}
        })
    };
    let finding = |file: &str, line: u64| {
        json!({
            "check_id": "dfb-taint-endpoint-contract",
            "path": file,
            "start": {"line": line, "col": 5},
            "extra": {"engine_kind": "OSS"}
        })
    };
    assert_eq!(
        semgrep_finding_outcome(
            &case_path,
            &case,
            &scanned(json!([finding("/tmp/work/fixture.py", 7)])),
            AnchorDialect::Python
        )
        .0,
        "reached"
    );
    assert_eq!(
        semgrep_finding_outcome(
            &case_path,
            &case,
            &scanned(json!([finding("fixture.py", 6)])),
            AnchorDialect::Python
        )
        .0,
        "inconclusive"
    );
    assert_eq!(
        semgrep_finding_outcome(
            &case_path,
            &case,
            &scanned(json!([{"path": "fixture.py", "extra": {"engine_kind": "OSS"}}])),
            AnchorDialect::Python
        )
        .0,
        "inconclusive"
    );
    assert_eq!(
        semgrep_finding_outcome(
            &case_path,
            &case,
            &scanned(json!([])),
            AnchorDialect::Python
        )
        .0,
        "not-reached"
    );
    fs::remove_dir_all(root).unwrap();
}

/// A Semgrep engine, rule, or parse failure — and a scan that never opened
/// the fixture — must never be normalized to a clean negative, whatever the
/// finding list says.
#[test]
fn semgrep_runner_failures_never_become_clean_negatives() {
    let case_path = PathBuf::from("cases/taint/python/direct-positive/case.json");
    let case = json!({"sink_anchors": []});
    let failed = json!({
        "results": [],
        "errors": [{"type": "SyntaxError", "long_msg": "Syntax error at line fixture.py:3"}],
        "skipped_rules": [],
        "paths": {"scanned": []}
    });
    let (outcome, diagnostics) =
        semgrep_finding_outcome(&case_path, &case, &failed, AnchorDialect::Python);
    assert_eq!(outcome, "runner-error");
    assert!(diagnostics.iter().any(|line| line.contains("Syntax error")));
    // The same document must also be refused as a downgraded negative by
    // the freeze's raw-evidence guard.
    assert_eq!(raw_special_outcome(&failed), Some("runner-error"));

    // A rule Semgrep declined to run explains its empty finding list, so
    // that list is not evidence about the program.
    let skipped = json!({
        "results": [],
        "errors": [],
        "skipped_rules": [{"rule_id": "dfb-taint-endpoint-contract"}],
        "paths": {"scanned": ["/tmp/work/fixture.py"]}
    });
    assert_eq!(
        semgrep_finding_outcome(&case_path, &case, &skipped, AnchorDialect::Python).0,
        "runner-error"
    );

    // A finding from any engine other than the pinned CE engine breaks the
    // pinning; that is an execution failure, not a data point.
    let wrong_engine = json!({
        "results": [{"path": "fixture.py", "start": {"line": 7}, "extra": {"engine_kind": "PRO"}}],
        "errors": [],
        "skipped_rules": [],
        "paths": {"scanned": ["/tmp/work/fixture.py"]}
    });
    assert_eq!(
        semgrep_finding_outcome(&case_path, &case, &wrong_engine, AnchorDialect::Python).0,
        "runner-error"
    );

    for malformed in [
        json!({"errors": [], "paths": {"scanned": []}}),
        json!({"results": [], "paths": {"scanned": []}}),
    ] {
        assert_eq!(
            semgrep_finding_outcome(&case_path, &case, &malformed, AnchorDialect::Python).0,
            "runner-error"
        );
    }

    // A clean run that never opened a target proves nothing either way.
    let untargeted = json!({
        "results": [],
        "errors": [],
        "skipped_rules": [],
        "paths": {"scanned": []}
    });
    assert_eq!(
        semgrep_finding_outcome(&case_path, &case, &untargeted, AnchorDialect::Python).0,
        "inconclusive"
    );
}

#[test]
fn freeze_schema_is_versioned_and_compiles() {
    let schema = compile_schema(Path::new("schemas/freeze.schema.json")).unwrap();
    let invalid = json!({"schema_version": 2});
    assert!(schema.validate(&invalid).is_err());
}

#[test]
fn freeze_fixture_revision_is_order_independent() {
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
fn checked_reports_match_the_frozen_fixture_revision() {
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
fn raw_evidence_may_be_one_document_or_json_lines_and_the_audit_reads_both() {
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
fn raw_special_outcomes_cannot_be_downgraded_to_clean_negatives() {
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
fn representative_bifrost_incomplete_evidence_stays_inconclusive() {
    let raw = json!({
        "schema_version": 4,
        "execution": {
            "termination": null,
            "terminal_stage": null,
            "pending_policy_ids": ["dataflowbench.taint.core-direct"]
        },
        "runs": [{
            "policy_id": "dataflowbench.taint.core-direct",
            "completion": {
                "type": "inconclusive",
                "reasons": ["partial_discovery", "budget_exhausted"]
            },
            "findings": []
        }]
    });
    assert_eq!(raw_special_outcome(&raw), Some("inconclusive"));
}

#[test]
fn bifrost_runner_failures_are_not_clean_negatives() {
    let case = json!({"expected_flows": []});
    let raw = json!({
        "execution": {"termination": {"type": "error"}},
        "runs": []
    });
    assert_eq!(
        normalize_bifrost(
            Path::new("cases/never/case.json"),
            &case,
            &raw,
            Some(0),
            AnchorDialect::Java,
        )
        .unwrap()
        .0,
        "runner-error"
    );
    assert_eq!(raw_special_outcome(&raw), Some("runner-error"));
    assert_eq!(
        raw_special_outcome(&json!({
            "_dataflowbench_runner": {"outcome": "runner-error", "exit_status": 127}
        })),
        Some("runner-error")
    );
}

#[test]
fn freeze_rejects_missing_raw_evidence() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    fs::remove_file(&fixture.raw).unwrap();
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
}

#[test]
fn freeze_rejects_altered_fixture_bytes() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
    assert!(validate_freeze_at(&fixture.root, &fixture.manifest, false).is_err());
}

#[test]
fn freeze_rejects_mixed_fixture_revision() {
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
fn freeze_rejects_profile_or_track_pooling() {
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
fn freeze_rejects_special_outcome_downgrade() {
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
fn release_freeze_rejects_placeholder_analyzer_identity() {
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
fn freeze_rejects_dirty_checkout_state() {
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
fn create_freeze_manifest_matches_validated_fixture() {
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
fn create_freeze_rejects_stale_fixture_bytes() {
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
fn freeze_git_state_accepts_ancestor_revisions_and_containing_tags() {
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
fn generate_results_writes_deterministic_artifacts() {
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
fn generate_results_classifies_incomplete_outcomes_separately() {
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
fn generate_results_check_detects_current_stale_missing_and_extra() {
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
fn generate_results_requires_a_valid_freeze() {
    let fixture = FreezeFixture::new("reached", json!({"state": "complete"}));
    fs::write(fixture.root.join("cases/taint/test/flow.c"), "altered\n").unwrap();
    let output = fixture.root.join("generated");
    assert!(generate_results_at(&fixture.root, &fixture.manifest, &output, false, false).is_err());
    assert!(!output.exists());
}

#[test]
fn scorecard_identifiers_disambiguate_repeated_populations() {
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

/// A report stamped with the hash the current configuration derives to is
/// current; the same report stamped with any other value has drifted; a
/// population whose hash is not derivable in-repo (tool-native
/// activations, foreign stems) is never compared at all.
#[test]
fn configuration_hash_comparison_distinguishes_current_from_drifted() {
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
fn committed_reports_match_current_configuration_except_known_stale() {
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

/// The generator, never a hand edit, states configuration staleness: a
/// scorecard built with a current-configuration mismatch carries the
/// caveat and the machine-readable hash pair, and one built without the
/// mismatch carries neither.
#[test]
fn scorecard_staleness_caveat_is_generator_emitted() {
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
/// Every challenge case that exists in the corpus belongs to a language
/// whose row is rolled out, and lands in that language's core population
/// with a preregistered template ID.
#[test]
fn challenge_cases_exist_only_for_rolled_out_languages() {
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        if !challenge_template_case(&case) {
            continue;
        }
        let template = case["template_id"].as_str().unwrap();
        assert!(
            CHALLENGE_TEMPLATE_IDS.contains(&template),
            "{} carries an unpreregistered challenge template",
            path.display()
        );
        let language = case["language"].as_str().unwrap();
        assert!(
            challenge_rolled_out(language),
            "{} carries a challenge template while {language} is not rolled out",
            path.display()
        );
        assert_eq!(case["score_tier"], "core", "{}", path.display());
        assert!(
            expected_core_templates(language).contains(&template),
            "{} is not in {language}'s expanded core",
            path.display()
        );
    }
}

/// The smoke population must stay pinned to its frozen 118-case contract:
/// dedicated language-kernel policies never leak into it.
#[test]
fn smoke_selection_is_pinned_to_the_frozen_population() {
    let mut selected = 0usize;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::Smoke) {
            selected += 1;
            let policy = case["tool_model_references"]["bifrost"]["policy"].as_str();
            if let Some(policy) = policy {
                assert!(
                    !policy.contains("kotlin")
                        && !policy.contains("typescript")
                        && !policy.contains("csharp")
                        && !policy.contains("go")
                        && !policy.contains("rust")
                        && !policy.contains("core-c-kernel")
                        && !policy.contains("core-cpp-kernel"),
                    "smoke selected a dedicated-kernel policy: {policy}"
                );
            }
        }
    }
    assert_eq!(selected, 118, "the smoke population is frozen at 118 cases");
}

/// A challenge case is refused by the smoke selector on template identity
/// alone. The Java, JavaScript, and Python challenge fixtures will name the
/// *same* kernel policies their classic siblings name, so pinning by policy
/// could not have kept them out; without this exclusion the frozen 118
/// would have silently become a different population.
#[test]
fn smoke_refuses_a_challenge_case_that_names_a_smoke_policy() {
    for policy in [
        BIFROST_JAVA_POLICY,
        BIFROST_JAVASCRIPT_POLICY,
        "adapters/bifrost/policies/core-python-kernel.rqlp",
        BIFROST_DIRECT_POLICY,
        BIFROST_DIRECT_POSITIVE_POLICY,
        BIFROST_EXPLICIT_NEGATIVE_POLICY,
    ] {
        let classic = json!({
            "template_id": "dfb-template-direct-propagation",
            "tool_model_references": {"bifrost": {"policy": policy}}
        });
        assert!(
            selected_bifrost_case(&classic, BifrostRun::Smoke),
            "the frozen smoke population still selects {policy}"
        );
        for template in CHALLENGE_TEMPLATE_IDS {
            let challenge = json!({
                "template_id": template,
                "tool_model_references": {"bifrost": {"policy": policy}}
            });
            assert!(
                !selected_bifrost_case(&challenge, BifrostRun::Smoke),
                "smoke selected challenge template {template} through {policy}"
            );
        }
    }
    // Not even a declared capability exclusion re-admits one: the smoke
    // selector short-circuits on `unsupported_reason`, and the challenge
    // refusal is checked first.
    let unsupported = json!({
        "template_id": "dfb-template-chal-deep-relay-chain",
        "tool_model_references": {"bifrost": {"unsupported_reason": "declared out of scope"}}
    });
    assert!(!selected_bifrost_case(&unsupported, BifrostRun::Smoke));
}

/// The rollout table is the one authoritative statement of each language's
/// denominator, and it must reproduce docs/challenge-tier.md's expanded
/// core table exactly.
#[test]
fn the_rollout_table_matches_the_preregistered_denominators() {
    let expanded: BTreeMap<&str, (usize, usize)> = BTreeMap::from([
        // language => (classic templates, applicable challenge templates)
        ("java", (16, 13)),
        ("javascript", (16, 13)),
        ("python", (16, 13)),
        ("typescript", (16, 13)),
        ("kotlin", (16, 13)),
        ("scala", (16, 13)),
        ("csharp", (16, 13)),
        ("go", (16, 13)),
        ("php", (16, 13)),
        ("ruby", (16, 13)),
        ("cpp", (16, 12)),
        ("c", (15, 9)),
        ("rust", (15, 12)),
    ]);
    assert_eq!(CHALLENGE_ROLLOUT.len(), expanded.len());
    for row in &CHALLENGE_ROLLOUT {
        let (classic, challenge) = expanded[row.language];
        assert_eq!(row.classic.len(), classic, "{} classic", row.language);
        assert_eq!(row.challenge.len(), challenge, "{} challenge", row.language);
        // Every challenge cell is one of the thirteen preregistered
        // templates; a language can narrow the set, never invent one.
        for template in row.challenge {
            assert!(
                CHALLENGE_TEMPLATE_IDS.contains(template),
                "{} claims unpreregistered template {template}",
                row.language
            );
            assert!(template.starts_with(CHALLENGE_TEMPLATE_PREFIX));
        }
        // The rollout is complete: Ruby was the last wave, so every one of
        // the thirteen rows is flipped and no language validates against
        // its classic set alone any more. This is the assertion that would
        // catch a row being silently un-flipped.
        assert!(row.rolled_out, "{} rollout state", row.language);
        assert!(
            challenge_rolled_out(row.language),
            "{} rollout state",
            row.language
        );
        // Every language's denominator is therefore its expanded core:
        // the classic templates plus its applicable challenge templates.
        let expected = classic + challenge;
        assert_eq!(row.expected_templates().len(), expected);
        assert_eq!(expected_core_case_count(row.language), 2 * expected);
    }
    // The exclusions docs/challenge-tier.md states, by name.
    let cpp = challenge_rollout("cpp").unwrap().challenge;
    let rust = challenge_rollout("rust").unwrap().challenge;
    let c = challenge_rollout("c").unwrap().challenge;
    for set in [cpp, rust, c] {
        assert!(!set.contains(&"dfb-template-chal-reflective-invocation"));
    }
    for excluded in [
        "dfb-template-chal-computed-property",
        "dfb-template-chal-closure-capture",
        "dfb-template-chal-anonymous-implementation",
    ] {
        assert!(!c.contains(&excluded), "C must exclude {excluded}");
    }
}

/// The dedicated Java and JavaScript Bifrost kernels own their language's
/// whole core population. Java consumes each case's validated declared
/// policy; JavaScript pins its language-qualified policy throughout.
#[test]
fn java_and_javascript_bifrost_kernels_own_their_language_population() {
    let mut java = 0usize;
    let mut javascript = 0usize;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
        if selected_bifrost_case(&case, BifrostRun::JavaKernel) {
            java += 1;
            assert_eq!(case["language"], "java");
            assert_eq!(case["score_tier"], "core");
            let declared_policy = case["tool_model_references"]["bifrost"]["policy"]
                .as_str()
                .unwrap();
            assert_eq!(
                bifrost_policy_for(&case, BifrostRun::JavaKernel).unwrap(),
                declared_policy
            );
            assert!(!selected_bifrost_case(&case, BifrostRun::JavascriptKernel));
        }
        if selected_bifrost_case(&case, BifrostRun::JavascriptKernel) {
            javascript += 1;
            assert_eq!(case["language"], "javascript");
            assert_eq!(case["score_tier"], "core");
            assert_eq!(
                bifrost_policy_for(&case, BifrostRun::JavascriptKernel).unwrap(),
                BIFROST_JAVASCRIPT_POLICY
            );
            assert!(!selected_bifrost_case(&case, BifrostRun::JavaKernel));
        }
    }
    assert_eq!(java, expected_core_case_count("java"));
    assert_eq!(javascript, expected_core_case_count("javascript"));
    // Both rows are rolled out, so both kernels are the expanded 58.
    assert_eq!(java, 58);
    assert_eq!(javascript, 58);
    assert_eq!(
        BifrostRun::JavaKernel.expected_core_cases(),
        Some(expected_core_case_count("java"))
    );
    assert_eq!(
        BifrostRun::JavascriptKernel.expected_core_cases(),
        Some(expected_core_case_count("javascript"))
    );
    // A challenge case joins its language kernel as soon as it exists, and
    // the run's expected count follows the rollout row rather than a
    // hard-coded 32.
    let challenge = json!({
        "language": "javascript",
        "track": "taint",
        "score_tier": "core",
        "template_id": "dfb-template-chal-dispatch-table",
        "tool_model_references": {"bifrost": {"policy": BIFROST_JAVASCRIPT_POLICY}}
    });
    assert!(selected_bifrost_case(
        &challenge,
        BifrostRun::JavascriptKernel
    ));
    assert!(!selected_bifrost_case(&challenge, BifrostRun::Smoke));
}

#[test]
fn java_kernel_preserves_the_direct_pairs_compatible_policies() {
    for policy in [
        BIFROST_DIRECT_POSITIVE_POLICY,
        BIFROST_EXPLICIT_NEGATIVE_POLICY,
    ] {
        let direct_case = json!({
            "language": "java",
            "track": "taint",
            "score_tier": "core",
            "template_id": "dfb-template-direct-propagation",
            "tool_model_references": {"bifrost": {"policy": policy}}
        });
        assert_eq!(
            bifrost_policy_for(&direct_case, BifrostRun::Smoke).unwrap(),
            policy
        );
        assert_eq!(
            bifrost_policy_for(&direct_case, BifrostRun::JavaKernel).unwrap(),
            policy,
            "the Java kernel must not replace compatible legacy selectors"
        );
    }
}

/// The Semgrep CE partition for the challenge tier is preregistered by
/// template ID and decided from the pinned distribution's documentation. It
/// must cover all thirteen templates, and no fixture's `feature_tags` may
/// move a challenge case into the scored partition after the fact.
#[test]
fn the_challenge_semgrep_partition_is_preregistered_and_tag_proof() {
    assert_eq!(
        CHALLENGE_SEMGREP_PARTITION.len(),
        CHALLENGE_TEMPLATE_IDS.len()
    );
    for template in CHALLENGE_TEMPLATE_IDS {
        let reason = challenge_semgrep_exclusion(template)
            .unwrap_or_else(|| panic!("{template} has no preregistered CE decision"));
        assert!(!reason.is_empty());
        // Even tagged as a purely local flow, the case stays outside the
        // scored partition: the decision is the document's, not the
        // fixture's.
        let case = json!({
            "template_id": template,
            "feature_tags": ["intraprocedural"],
            "expected_analysis_capability": {"kind": "recursive-carry-taint"}
        });
        let exclusion = semgrep_capability_exclusion(&case)
            .unwrap_or_else(|| panic!("{template} was scored by the CE partition"));
        assert!(exclusion.contains("outside the bounded Semgrep CE profile"));
        assert!(exclusion.contains(reason));
    }
    // The classic partition is untouched: the seven intraprocedural
    // templates stay scored and the heap and interprocedural ones stay
    // excluded.
    let classic_scored = json!({
        "template_id": "dfb-template-direct-propagation",
        "feature_tags": ["intraprocedural"],
        "expected_analysis_capability": {"kind": "intraprocedural-taint"}
    });
    assert!(semgrep_capability_exclusion(&classic_scored).is_none());
    let classic_excluded = json!({
        "template_id": "dfb-template-same-object-field-separation",
        "feature_tags": ["heap-access-path"],
        "expected_analysis_capability": {"kind": "heap-field-sensitive-taint"}
    });
    assert!(semgrep_capability_exclusion(&classic_excluded).is_some());
}
/// A failed Bifrost run is an execution error even under exit status 2;
/// this must match `raw_special_outcome` so a freeze can bind the report.
#[test]
fn failed_bifrost_completion_normalizes_to_runner_error_despite_status_2() {
    let case = json!({"expected_flows": []});
    let raw = json!({
        "runs": [{
            "completion": {"type": "failed", "reasons": ["internal_invariant"]},
            "diagnostics": []
        }]
    });
    let (outcome, _, _) = normalize_bifrost(
        Path::new("cases/never/case.json"),
        &case,
        &raw,
        Some(2),
        AnchorDialect::Java,
    )
    .unwrap();
    assert_eq!(outcome, "runner-error");
    assert_eq!(raw_special_outcome(&raw), Some("runner-error"));

    let inconclusive = json!({
        "runs": [
            {"completion": {"type": "inconclusive"}, "diagnostics": []},
            {"completion": {"type": "failed"}, "diagnostics": []}
        ]
    });
    let (outcome, _, _) = normalize_bifrost(
        Path::new("cases/never/case.json"),
        &case,
        &inconclusive,
        Some(2),
        AnchorDialect::Java,
    )
    .unwrap();
    assert_eq!(outcome, "inconclusive");
    assert_eq!(raw_special_outcome(&inconclusive), Some("inconclusive"));
}

// -----------------------------------------------------------------------
/// The kernels' endpoint rule, used by every Joern kernel normalization test.
const KERNEL_ENDPOINTS: JoernEndpointRule = JoernEndpointRule::BothMustBeObserved;

// The benchmark-controlled taint-modeling matrix.
// -----------------------------------------------------------------------

/// One synthetic modeling case, carrying every field the modeling
/// validators read.
fn modeling_case_value(template: &str, polarity: &str, language: &str) -> Value {
    let short = template
        .strip_prefix(MODELING_TEMPLATE_PREFIX)
        .expect("a modeling template");
    json!({
        "id": format!("dfb-taint-{language}-model-{short}-{polarity}"),
        "template_id": template,
        "polarity": polarity,
        "score_tier": "modeling",
        "track": "taint",
        "language": language,
        "model_profile": MODELING_MODEL_PROFILE,
        "feature_tags": ["modeled-external", "intraprocedural"],
        "expected_analysis_capability": {"kind": "declared-source-activation"}
    })
}

/// A whole balanced modeling population for one language: 24 assertions
/// over the preregistered twelve.
fn modeling_population(language: &str) -> Vec<(PathBuf, Value)> {
    let mut cases = Vec::new();
    for template in MODELING_TEMPLATE_IDS {
        for polarity in ["positive", "negative"] {
            cases.push((
                PathBuf::from(format!(
                    "cases/taint/{language}/{template}-{polarity}/case.json"
                )),
                modeling_case_value(template, polarity, language),
            ));
        }
    }
    cases
}

/// The twelve template IDs are the document's, unique, and all carry the
/// tier's structural prefix.
#[test]
fn modeling_templates_are_the_preregistered_twelve() {
    assert_eq!(MODELING_TEMPLATE_IDS.len(), 12);
    assert_eq!(MODELING_CASE_COUNT, 24);
    let unique: BTreeSet<&str> = MODELING_TEMPLATE_IDS.into_iter().collect();
    assert_eq!(unique.len(), 12);
    for template in MODELING_TEMPLATE_IDS {
        assert!(
            template.starts_with(MODELING_TEMPLATE_PREFIX),
            "{template} lacks the modeling prefix"
        );
    }
    assert_eq!(
        MODELING_TEMPLATE_IDS[0],
        "dfb-template-model-declared-source"
    );
    assert_eq!(
        MODELING_TEMPLATE_IDS[11],
        "dfb-template-model-store-separation"
    );
}

/// Six categories of two, partitioning the twelve exactly.
#[test]
fn every_modeling_template_belongs_to_exactly_one_category() {
    let mut seen: BTreeSet<&str> = BTreeSet::new();
    for category in ModelingCategory::ALL {
        for template in category.templates() {
            assert!(seen.insert(template), "{template} is in two categories");
            assert_eq!(modeling_category(template), Some(category));
        }
    }
    assert_eq!(seen, MODELING_TEMPLATE_IDS.into_iter().collect());
    assert_eq!(modeling_category("dfb-template-direct-propagation"), None);
    assert_eq!(
        ModelingCategory::ALL.map(ModelingCategory::key),
        ["S", "P", "Z", "O", "E", "B"]
    );
}

/// Every tool × template cell is decided. There is no scored default: an
/// undecided cell is an error, not a silent `supported`.
#[test]
fn the_modeling_partition_decides_every_tool_and_template() {
    for tool in ModelingTool::ALL.iter().copied() {
        for template in MODELING_TEMPLATE_IDS {
            modeling_partition_reason(tool, template)
                .unwrap_or_else(|_| panic!("{} × {template} is undecided", tool.key()));
        }
    }
    // One cell per tool per category, for every tool in `ALL`: the
    // preregistered four plus each amendment-added adapter's six. The
    // count is derived, not a literal, so a new adapter's six cells
    // cannot collide with another's in this assertion.
    assert_eq!(
        MODELING_PARTITION.len(),
        ModelingTool::ALL.len() * ModelingCategory::ALL.len()
    );
    assert!(
        modeling_partition_reason(ModelingTool::Codeql, "dfb-template-chal-dispatch-table")
            .is_err()
    );
}

/// The scored-template counts are the document's partition summary as
/// amended, expressed in templates rather than categories: Bifrost 2 of
/// 12, Semgrep 5 of 12 (Amendment A3), Joern 8 of 12 (Amendment A2), and
/// CodeQL 12 of 12.
#[test]
fn modeling_partition_scored_counts_match_the_preregistration() {
    // Amendment A9 promoted Bifrost's category Z: the two sanitizer
    // templates join the two category-S ones.
    assert_eq!(modeling_supported_templates(ModelingTool::Bifrost).len(), 4);
    // Amendment A3 moved sanitizer-selectivity out of Semgrep's scored set.
    assert_eq!(modeling_supported_templates(ModelingTool::Semgrep).len(), 5);
    assert_eq!(modeling_supported_templates(ModelingTool::Codeql).len(), 12);
    // Amendment A2 moved Joern's propagator and summary categories to
    // unsupported: FlowSemantic is additive on the pinned 4.0.610.
    assert_eq!(modeling_supported_templates(ModelingTool::Joern).len(), 8);
    // Amendment A13: Infer joins with S, P (template 3 alone — template 4
    // is overridden out on the measured absence of an input-position
    // vocabulary), and Z.
    assert_eq!(modeling_supported_templates(ModelingTool::Infer).len(), 5);
    // Amendment A18: FlowDroid joins with S, P, Z, and O, minus the
    // sanitizer-selectivity template its class-exclusive summary
    // resolution makes undecidable — seven templates, four categories.
    assert_eq!(
        modeling_supported_templates(ModelingTool::Flowdroid).len(),
        7
    );
}

/// FlowDroid's Amendment-A18 row, template by template: categories S, P,
/// and O whole, category Z's kill template alone, and categories E and B
/// declined with retained rationales that cite the probe evidence.
#[test]
fn flowdroid_modeling_partition_matches_amendment_a18() {
    let mut expected = ModelingCategory::SourcesAndSinks.templates().to_vec();
    expected.extend(ModelingCategory::Propagators.templates());
    expected.extend(ModelingCategory::Sanitizers.templates());
    expected.extend(ModelingCategory::Summaries.templates());
    expected.retain(|template| *template != "dfb-template-model-sanitizer-selectivity");
    expected.sort_unstable();
    let mut scored = modeling_supported_templates(ModelingTool::Flowdroid);
    scored.sort_unstable();
    assert_eq!(scored, expected);
    for category in [ModelingCategory::EntryPoints, ModelingCategory::Persistence] {
        for template in category.templates() {
            assert!(
                modeling_partition_reason(ModelingTool::Flowdroid, template)
                    .unwrap()
                    .is_some(),
                "{template} must be unsupported for FlowDroid"
            );
        }
    }
    // The template-level override is what splits category Z, exactly as
    // Amendment A3 split it for Semgrep and A13 split category P for
    // Infer.
    assert!(
        modeling_partition_reason(
            ModelingTool::Flowdroid,
            "dfb-template-model-sanitizer-selectivity"
        )
        .unwrap()
        .unwrap()
        .contains("Amendment A18")
    );
}

/// FlowDroid's Amendment-A19 native row: the activation contract is live —
/// the shipped catalog and default summary wrapper are the product — but
/// the catalog binds no identity any native template uses, so all six
/// cells are declined from shipped-model text, and the activation shape
/// names the jar-internal catalog rather than any repository path.
#[test]
fn flowdroid_native_partition_declines_all_six_on_catalog_evidence() {
    assert!(native_supported_templates(ModelingTool::Flowdroid, ModelingLanguage::Java).is_empty());
    for template in NATIVE_TEMPLATE_IDS {
        let reason =
            native_partition_reason(ModelingTool::Flowdroid, ModelingLanguage::Java, template)
                .unwrap()
                .expect("every FlowDroid native cell is declined");
        assert!(reason.contains("Amendment A19"), "{template}: {reason}");
    }
    let activation =
        native_activation(ModelingTool::Flowdroid, ModelingLanguage::Java, "2.15.1").unwrap();
    assert_eq!(
        activation.arguments,
        vec![
            "-s".to_string(),
            FLOWDROID_NATIVE_CATALOG_ARGUMENT.to_string()
        ]
    );
    require_no_benchmark_models(ModelingTool::Flowdroid, &activation.arguments).unwrap();
    assert!(activation.configuration_paths.is_empty());
    // Amendment A22 preregistered OpenTaint's Java row: S, P, and Z.
    assert_eq!(
        modeling_supported_templates(ModelingTool::Opentaint).len(),
        6
    );
}

/// OpenTaint's modeling row (Amendment A22), pinned exactly: categories S,
/// P, and Z are scored and O, E, and B are declined — a partition decided
/// by executing the pinned analyzer over the committed Java fixtures with
/// probe declarations, before any scored run, and retained under
/// reports/raw/opentaint-modeling-surface-probe/.
#[test]
fn opentaint_modeling_partition_scores_sources_propagators_and_sanitizers() {
    let mut expected = ModelingCategory::SourcesAndSinks.templates().to_vec();
    expected.extend(ModelingCategory::Propagators.templates());
    expected.extend(ModelingCategory::Sanitizers.templates());
    expected.sort_unstable();
    let mut scored = modeling_supported_templates(ModelingTool::Opentaint);
    scored.sort_unstable();
    assert_eq!(scored, expected);
    for category in [
        ModelingCategory::Summaries,
        ModelingCategory::EntryPoints,
        ModelingCategory::Persistence,
    ] {
        for template in category.templates() {
            let reason = modeling_partition_reason(ModelingTool::Opentaint, template)
                .unwrap()
                .unwrap_or_else(|| panic!("{template} must be unsupported for OpenTaint"));
            assert!(reason.contains("Amendment A22"), "{reason}");
        }
    }
}

/// OpenTaint's modeling denominator is Java alone: the other two wave-M1
/// languages have no artifact and `plan_modeling_run` refuses them on
/// applicability rather than reporting anything.
#[test]
fn opentaint_modeling_is_java_only() {
    assert_eq!(
        ModelingLanguage::Java.artifact(ModelingTool::Opentaint),
        Some("adapters/opentaint/rules/model-java.yaml")
    );
    assert_eq!(
        ModelingLanguage::Javascript.artifact(ModelingTool::Opentaint),
        None
    );
    assert_eq!(
        ModelingLanguage::Python.artifact(ModelingTool::Opentaint),
        None
    );
    // The committed modeling rule declares exactly its scored categories:
    // the load-trace-checked id, the propagators category P entitles it
    // to, the sanitizer category Z entitles it to — and none of the
    // declined categories' entities.
    let rule = fs::read_to_string(
        ModelingLanguage::Java
            .artifact(ModelingTool::Opentaint)
            .unwrap(),
    )
    .unwrap();
    assert!(rule.contains(&format!("id: {OPENTAINT_MODEL_RULE_ID}")));
    assert!(rule.contains("pattern-propagators"));
    assert!(rule.contains("pattern-sanitizers"));
    for declined_entity in ["Bridge.", "Handler.", "onRequest", "onDeclared", "Store."] {
        assert!(
            !rule.contains(declined_entity),
            "the OpenTaint modeling rule declares {declined_entity}, whose category its partition marks unsupported"
        );
    }
}

/// Amendment A16's partition row, cell by cell: five categories scored,
/// persistence declined on the DSL's absent store vocabulary, and the
/// whole row Python-scoped by the artifact map and the native activation
/// — a no-denominator pair has no artifact and is refused before any run.
#[test]
fn pysa_modeling_partition_scores_five_categories_python_only() {
    let mut expected = Vec::new();
    for category in [
        ModelingCategory::SourcesAndSinks,
        ModelingCategory::Propagators,
        ModelingCategory::Sanitizers,
        ModelingCategory::Summaries,
        ModelingCategory::EntryPoints,
    ] {
        expected.extend(category.templates());
    }
    expected.sort_unstable();
    let mut scored = modeling_supported_templates(ModelingTool::Pysa);
    scored.sort_unstable();
    assert_eq!(scored, expected);
    for template in ModelingCategory::Persistence.templates() {
        let reason = modeling_partition_reason(ModelingTool::Pysa, template)
            .unwrap()
            .expect("category B is declined for Pysa");
        assert!(reason.contains("no store identity"));
        assert!(reason.contains("Amendment A16"));
    }
    assert!(
        ModelingLanguage::Python
            .artifact(ModelingTool::Pysa)
            .is_some()
    );
    assert!(
        ModelingLanguage::Java
            .artifact(ModelingTool::Pysa)
            .is_none()
    );
    assert!(
        ModelingLanguage::Javascript
            .artifact(ModelingTool::Pysa)
            .is_none()
    );
    let error = native_activation(
        ModelingTool::Pysa,
        ModelingLanguage::Javascript,
        WITNESSED_IDENTITY,
    )
    .err()
    .expect("a no-denominator pair must be refused")
    .to_string();
    assert!(error.contains("no JavaScript tool-native denominator"));
    // Amendment A17: the native row scores all six templates for Python.
    assert_eq!(
        native_supported_templates(ModelingTool::Pysa, ModelingLanguage::Python).len(),
        6
    );
}

/// The committed Pysa modeling artifact carries exactly the scored
/// templates' blocks — a block for a declined template would violate the
/// rule that an artifact never declares a category its partition marks
/// unsupported — and every block resolves the way the runner cuts it.
#[test]
fn pysa_modeling_artifact_blocks_cover_exactly_the_scored_templates() {
    let path = ModelingLanguage::Python
        .artifact(ModelingTool::Pysa)
        .expect("Pysa's Python artifact is declared");
    let artifact = fs::read_to_string(path).unwrap();
    let scored = modeling_supported_templates(ModelingTool::Pysa);
    for template in MODELING_TEMPLATE_IDS {
        let block = pysa_modeling_block(&artifact, template, path);
        if scored.contains(&template) {
            let block = block.unwrap_or_else(|_| panic!("{template} block is missing"));
            assert!(
                !block.is_empty() && !pysa_block_model_callables(&block).is_empty(),
                "{template} block declares no source or sink model"
            );
        } else {
            block.expect_err("a declined template must have no block");
        }
    }
    // The endpoint extraction the activation guard relies on.
    let block = pysa_modeling_block(&artifact, "dfb-template-model-declared-source", path).unwrap();
    assert_eq!(
        pysa_block_model_callables(&block),
        vec![
            "config.fetch_remote".to_string(),
            "config.dfb_sink".to_string()
        ]
    );
}

/// The load-bearing gate on the Pysa artifact: the committed file passes,
/// and a counterfactual whose propagator loses a skip mode fails, because
/// Amendment A16 measured the pinned pair following the fixture bodies on
/// its own.
#[test]
fn pysa_modeling_artifact_is_load_bearing() {
    let path = ModelingLanguage::Python
        .artifact(ModelingTool::Pysa)
        .expect("Pysa's Python artifact is declared");
    let artifact = fs::read_to_string(path).unwrap();
    require_pysa_modeling_load_bearing(&artifact, path).unwrap();
    let stripped = artifact.replace("@SkipObscure\n", "");
    let error = require_pysa_modeling_load_bearing(&stripped, path)
        .unwrap_err()
        .to_string();
    assert!(error.contains("@SkipObscure"));
    assert!(error.contains("the-load-bearing-model-requirement"));
    let empty = "def config.dfb_sink(value: TaintSink[DfbSink]): ...\n";
    let error = require_pysa_modeling_load_bearing(empty, path)
        .unwrap_err()
        .to_string();
    assert!(error.contains("no TaintInTaintOut"));
}

/// Amendment A17's activation shape: the shipped suite with `--no-verify`,
/// no benchmark-authored model in the arguments, and the retained-evidence
/// guard keyed to the shipped `os.system` sink model.
#[test]
fn pysa_native_activation_is_the_shipped_suite() {
    let activation = native_activation(
        ModelingTool::Pysa,
        ModelingLanguage::Python,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert!(activation.identity.contains(PYSA_NATIVE_SUITE_RELATIVE));
    assert!(activation.arguments.contains(&"--no-verify".to_string()));
    require_no_benchmark_models(ModelingTool::Pysa, &activation.arguments).unwrap();
    assert_eq!(PYSA_NATIVE_SINK_MODEL, "os.system");
}

/// Bifrost entered with category S alone — the honest starting position the
/// preregistration states for a standalone policy CLI whose modeling
/// surface lives in an embedding — and holds S and Z after Amendment A9
/// measured the sanitizer stanza as accepted, load-bearing, and selective.
///
/// The four cells that stay declined are asserted here as well, because a
/// promotion is only as honest as the cells it leaves alone: P and O have
/// adjacent sections the grammar accepts but no demonstration that either
/// lowers, and E and B have no section at all.
#[test]
fn bifrost_modeling_partition_scores_sources_and_sanitizers() {
    let mut expected = ModelingCategory::SourcesAndSinks.templates().to_vec();
    expected.extend(ModelingCategory::Sanitizers.templates());
    expected.sort_unstable();
    let mut scored = modeling_supported_templates(ModelingTool::Bifrost);
    scored.sort_unstable();
    assert_eq!(scored, expected);
    for category in [
        ModelingCategory::Propagators,
        ModelingCategory::Summaries,
        ModelingCategory::EntryPoints,
        ModelingCategory::Persistence,
    ] {
        for template in category.templates() {
            assert!(
                modeling_partition_reason(ModelingTool::Bifrost, template)
                    .unwrap()
                    .is_some(),
                "{template} must be unsupported for Bifrost"
            );
        }
    }
}

/// Semgrep CE enters with S, Z, and E — three of six, and a larger share
/// of this matrix than Bifrost, which is the whole reason the tier exists.
#[test]
fn semgrep_modeling_partition_scores_sources_sanitizers_and_entry_points() {
    let mut expected = Vec::new();
    for category in [
        ModelingCategory::SourcesAndSinks,
        ModelingCategory::Sanitizers,
        ModelingCategory::EntryPoints,
    ] {
        expected.extend(category.templates());
    }
    // Amendment A3: sanitizer-selectivity is template-overridden out of
    // Semgrep's scored set — the safe-function assumption and selectivity
    // cannot coexist in one CE invocation.
    expected.retain(|template| *template != "dfb-template-model-sanitizer-selectivity");
    expected.sort_unstable();
    let mut scored = modeling_supported_templates(ModelingTool::Semgrep);
    scored.sort_unstable();
    assert_eq!(scored, expected);
}

/// Infer joins by Amendment A13 with S, P, and Z — and P by template 3
/// alone: the field evaluation measured the declared `select` propagator
/// carrying taint from the undeclared position exactly as from the
/// declared one, so template 4 is overridden out of the scored set the
/// way Amendment A3 overrode Semgrep's template 6.
#[test]
fn infer_modeling_partition_scores_sources_one_propagator_and_sanitizers() {
    let mut expected = ModelingCategory::SourcesAndSinks.templates().to_vec();
    expected.extend(ModelingCategory::Propagators.templates());
    expected.extend(ModelingCategory::Sanitizers.templates());
    expected.retain(|template| *template != "dfb-template-model-propagator-position");
    expected.sort_unstable();
    let mut scored = modeling_supported_templates(ModelingTool::Infer);
    scored.sort_unstable();
    assert_eq!(scored, expected);
    let position = modeling_partition_reason(
        ModelingTool::Infer,
        "dfb-template-model-propagator-position",
    )
    .unwrap()
    .expect("template 4 is overridden out of Infer's scored set");
    assert!(position.contains("Amendment A13"), "{position}");
    assert!(position.contains("input position"), "{position}");
    for (category, fragment) in [
        (ModelingCategory::Summaries, "decided by body analysis"),
        (ModelingCategory::EntryPoints, "synthesizes no root"),
        (
            ModelingCategory::Persistence,
            "no store-write/store-read vocabulary",
        ),
    ] {
        for template in category.templates() {
            let reason = modeling_partition_reason(ModelingTool::Infer, template)
                .unwrap()
                .unwrap_or_else(|| panic!("{template} must be unsupported for Infer"));
            assert!(reason.contains(fragment), "{template}: {reason}");
        }
    }
}

/// The three silent-failure shapes of the pinned Infer configuration
/// surface, each measured in the field, each refused by the gate: a
/// policy-less configuration asks no taint question, an unwired sanitizer
/// is silently inert, and the plain `procedure` matcher is a substring
/// match that cannot carry identity binding.
#[test]
fn an_infer_modeling_configuration_must_be_load_bearing() {
    let no_policy = r#"{"pulse-taint-sources": [], "pulse-taint-policies": []}"#;
    let error = require_infer_modeling_load_bearing(no_policy, "adapters/infer/config/x.json")
        .unwrap_err()
        .to_string();
    assert!(error.contains("no pulse-taint-policies"), "{error}");

    let unwired = r#"{
            "pulse-taint-sanitizers": [{"class_names": ["C"], "method_names": ["scrub"], "kinds": ["K"]}],
            "pulse-taint-policies": [{"taint_flows": [{"source_kinds": ["S"], "sink_kinds": ["T"]}]}]
        }"#;
    let error = require_infer_modeling_load_bearing(unwired, "adapters/infer/config/x.json")
        .unwrap_err()
        .to_string();
    assert!(error.contains("silently inert"), "{error}");

    let substring = r#"{
            "pulse-taint-sources": [{"procedure": "dfb_source"}],
            "pulse-taint-policies": [{"taint_flows": [{"source_kinds": ["S"], "sink_kinds": ["T"]}]}]
        }"#;
    let error = require_infer_modeling_load_bearing(substring, "adapters/infer/config/x.json")
        .unwrap_err()
        .to_string();
    assert!(error.contains("substring"), "{error}");

    let wired = r#"{
            "pulse-taint-sanitizers": [{"class_names": ["C"], "method_names": ["scrub"], "kinds": ["K"]}],
            "pulse-taint-policies": [{"taint_flows": [{"source_kinds": ["S"], "sanitizer_kinds": ["K"], "sink_kinds": ["T"]}]}]
        }"#;
    require_infer_modeling_load_bearing(wired, "adapters/infer/config/x.json").unwrap();
}

/// The committed Infer artifact passes the runner's gate and declares
/// exactly its scored categories: the `carry` propagator but not the
/// position-bound `select` (template 4 is overridden out), and nothing for
/// the declined `Bridge`, `Handler`, or `Store` entities.
#[test]
fn the_infer_modeling_artifact_is_load_bearing_and_scoped_to_its_partition() {
    let path = ModelingLanguage::Java
        .artifact(ModelingTool::Infer)
        .unwrap();
    let config = fs::read_to_string(path).unwrap();
    require_infer_modeling_load_bearing(&config, path).unwrap();
    assert!(config.contains("\"carry\""));
    for declined in ["\"select\"", "Bridge", "Handler", "Store", "deposit"] {
        assert!(
            !config.contains(declined),
            "the Infer modeling configuration declares {declined}, which its partition marks unsupported"
        );
    }
}

/// The partition is keyed by template identity alone. No `feature_tags`
/// choice a fixture makes — and no observed result — can move a cell
/// between the scored and `unsupported` partitions.
#[test]
fn the_modeling_partition_is_tag_proof() {
    let template = "dfb-template-model-opaque-propagator";
    let baseline =
        modeling_unsupported_reason(ModelingTool::Semgrep, template, WITNESSED_IDENTITY).unwrap();
    assert!(baseline.is_some());
    for tags in [
        json!(["intraprocedural"]),
        json!(["interprocedural-deep", "heap-access-path"]),
        json!([]),
    ] {
        let mut case = modeling_case_value(template, "positive", "java");
        case["feature_tags"] = tags;
        case["expected_analysis_capability"]["kind"] = json!("local-taint");
        assert_eq!(
            modeling_unsupported_reason(
                ModelingTool::Semgrep,
                case["template_id"].as_str().unwrap(),
                WITNESSED_IDENTITY
            )
            .unwrap(),
            baseline,
            "a fixture's tags must not move a partition cell"
        );
    }
    // And the converse: a scored cell stays scored whatever it is tagged.
    let scored = "dfb-template-model-declared-source";
    assert!(
        modeling_unsupported_reason(ModelingTool::Semgrep, scored, WITNESSED_IDENTITY)
            .unwrap()
            .is_none()
    );
}

/// Every declined cell retains a reason that names the category and the
/// **witnessed** tool identity and carries the document's rationale
/// verbatim.
///
/// The identity is asserted to be the one the caller measured, and asserted
/// again *not* to be a version literal: a rationale that hardcoded a
/// version would keep naming a build the run never invoked, which is how a
/// stale pin survives a re-pin unnoticed.
#[test]
fn modeling_unsupported_reasons_are_retained_and_attributed() {
    let reason = modeling_unsupported_reason(
        ModelingTool::Bifrost,
        "dfb-template-model-summary-through",
        WITNESSED_IDENTITY,
    )
    .unwrap()
    .expect("category O is unsupported for Bifrost");
    assert!(reason.starts_with("category O — opaque procedure summaries —"));
    assert!(reason.contains(WITNESSED_IDENTITY));
    assert!(reason.contains("External semantic-model activation requires an embedding"));
    assert!(reason.contains("docs/modeling-matrix.md"));
    for tool in ModelingTool::ALL.iter().copied() {
        for template in MODELING_TEMPLATE_IDS {
            if let Some(reason) =
                modeling_unsupported_reason(tool, template, WITNESSED_IDENTITY).unwrap()
            {
                assert!(reason.len() > 80, "a retained reason must say why");
                assert!(
                    reason.contains(WITNESSED_IDENTITY),
                    "a retained reason names the identity the run witnessed"
                );
            }
        }
    }
}

/// A declined cell writes its retained capability decision and returns
/// `unsupported` without the analyzer ever being invoked.
#[test]
fn a_declined_modeling_cell_retains_evidence_without_invoking_the_tool() {
    let root = unique_test_dir("dataflowbench-modeling-partition-test");
    let case = modeling_case_value("dfb-template-model-store-roundtrip", "positive", "python");
    let (outcome, reason, raw_path) =
        modeling_partition_outcome(ModelingTool::Semgrep, &case, &root, WITNESSED_IDENTITY)
            .unwrap()
            .expect("category B is unsupported for Semgrep CE");
    assert_eq!(outcome, "unsupported");
    let retained: Value = serde_json::from_slice(&fs::read(&raw_path).unwrap()).unwrap();
    assert_eq!(retained["state"], "unsupported");
    assert_eq!(retained["stage"], "preregistered-modeling-partition");
    assert_eq!(retained["modeling_category"], "B");
    assert_eq!(retained["adapter"], "semgrep");
    assert_eq!(retained["reason"], json!(reason));
    assert_eq!(retained["witnessed_tool_identity"], WITNESSED_IDENTITY);
    assert_eq!(retained["evidence_kind"], "retained-capability-decision");

    // A scored cell produces no decision and no evidence at all.
    let scored = modeling_case_value("dfb-template-model-declared-sink", "positive", "python");
    assert!(
        modeling_partition_outcome(ModelingTool::Semgrep, &scored, &root, WITNESSED_IDENTITY)
            .unwrap()
            .is_none()
    );
    fs::remove_dir_all(&root).unwrap();
}

/// A language with no modeling cases has no modeling denominator, which is
/// different from having a zero. It validates trivially.
#[test]
fn an_absent_modeling_population_validates_trivially() {
    validate_modeling_population(&[], "Java modeling population").unwrap();
    validate_modeling_cases(&[]).unwrap();
}

/// A whole balanced population over the preregistered twelve validates.
#[test]
fn a_balanced_modeling_population_validates() {
    let cases = modeling_population("java");
    assert_eq!(cases.len(), MODELING_CASE_COUNT);
    validate_modeling_population(&cases, "Java modeling population").unwrap();
    validate_modeling_cases(&cases).unwrap();
}

/// A partial fixture landing fails the build rather than silently reducing
/// a denominator, and an unbalanced pair fails too.
#[test]
fn an_incomplete_modeling_population_fails_validation() {
    let mut short = modeling_population("javascript");
    short.truncate(22);
    let error = validate_modeling_population(&short, "JavaScript modeling population")
        .unwrap_err()
        .to_string();
    assert!(
        error.contains("must select exactly 24 assertions"),
        "{error}"
    );

    let mut unbalanced = modeling_population("javascript");
    unbalanced[1].1["polarity"] = json!("positive");
    let error = validate_modeling_population(&unbalanced, "JavaScript modeling population")
        .unwrap_err()
        .to_string();
    assert!(
        error.contains("one positive and one negative per template"),
        "{error}"
    );

    let mut renamed = modeling_population("javascript");
    renamed[0].1["template_id"] = json!("dfb-template-model-invented");
    renamed[1].1["template_id"] = json!("dfb-template-model-invented");
    let error = validate_modeling_population(&renamed, "JavaScript modeling population")
        .unwrap_err()
        .to_string();
    assert!(error.contains("template set mismatch"), "{error}");
}

/// Tier isolation is structural: the modeling template prefix and the
/// `modeling` score tier imply each other, so a modeling case can never be
/// selected into a core, calibration, extension, or real-project
/// population, and a kernel template can never claim the modeling tier.
#[test]
fn the_modeling_tier_and_the_modeling_prefix_imply_each_other() {
    let mut retiered = modeling_population("python");
    retiered[0].1["score_tier"] = json!("core");
    let error = validate_modeling_cases(&retiered).unwrap_err().to_string();
    assert!(error.contains("disagree"), "{error}");

    let smuggled = vec![(
        PathBuf::from("cases/taint/python/smuggled/case.json"),
        json!({
            "id": "dfb-taint-python-smuggled",
            "template_id": "dfb-template-direct-propagation",
            "score_tier": "modeling",
            "polarity": "positive",
            "track": "taint",
            "language": "python",
            "model_profile": MODELING_MODEL_PROFILE
        }),
    )];
    let error = validate_modeling_cases(&smuggled).unwrap_err().to_string();
    assert!(error.contains("disagree"), "{error}");

    let invented = vec![(
        PathBuf::from("cases/taint/python/invented/case.json"),
        json!({
            "id": "dfb-taint-python-invented",
            "template_id": "dfb-template-model-invented",
            "score_tier": "modeling",
            "polarity": "positive",
            "track": "taint",
            "language": "python",
            "model_profile": MODELING_MODEL_PROFILE
        }),
    )];
    let error = validate_modeling_cases(&invented).unwrap_err().to_string();
    assert!(
        error.contains("not one of the twelve preregistered modeling templates"),
        "{error}"
    );
}

/// Every modeling case is `benchmark-controlled`. The tool-native profile
/// supplies no models and is never pooled with this matrix.
#[test]
fn modeling_cases_must_be_benchmark_controlled() {
    let mut cases = modeling_population("java");
    cases[0].1["model_profile"] = json!("tool-native");
    let error = validate_modeling_cases(&cases).unwrap_err().to_string();
    assert!(error.contains("benchmark-controlled"), "{error}");
}

/// A modeling case is never swept into the frozen 118-case Bifrost smoke
/// population, whatever policy it names.
#[test]
fn a_modeling_case_is_never_smoke_selected() {
    let mut case = modeling_case_value("dfb-template-model-declared-source", "positive", "java");
    case["tool_model_references"] = json!({"bifrost": {"policy": BIFROST_JAVA_POLICY}});
    assert!(!smoke_population_case(&case));
    case["tool_model_references"] =
        json!({"bifrost": {"unsupported_reason": "no external catalog"}});
    assert!(!smoke_population_case(&case));
}

/// The generated scorecards order `modeling` alongside the existing tiers.
/// A tier absent from this list would be silently dropped.
#[test]
fn the_result_tier_order_carries_modeling() {
    assert!(SCORE_TIER_ORDER.contains(&"modeling"));
}

/// Wave M1's rows: Python, JavaScript, and Java each carry a balanced
/// twenty-four over exactly the preregistered twelve. With Java's landing
/// the wave is complete, so every `ModelingLanguage` now has a denominator
/// — and a language with none would still be a fail-fast rather than a
/// zero.
#[test]
fn the_modeling_populations_are_the_balanced_twenty_four() {
    for (language, revision) in [
        (ModelingLanguage::Python, "m3-modeling-python"),
        (ModelingLanguage::Javascript, "m3-modeling-javascript"),
        (ModelingLanguage::Java, "m3-modeling-java"),
    ] {
        let population = select_modeling_cases(language).unwrap();
        assert_eq!(population.len(), MODELING_CASE_COUNT);
        let templates: BTreeSet<&str> = population
            .iter()
            .filter_map(|(_, case)| case["template_id"].as_str())
            .collect();
        assert_eq!(templates, MODELING_TEMPLATE_IDS.into_iter().collect());
        for (path, case) in &population {
            assert_eq!(case["score_tier"], "modeling", "{}", path.display());
            assert_eq!(case["model_profile"], MODELING_MODEL_PROFILE);
            assert_eq!(
                case["fixture_provenance"]["revision"],
                revision,
                "{}",
                path.display()
            );
            assert!(!smoke_population_case(case), "{}", path.display());
            assert!(
                case["feature_tags"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .any(|tag| tag == "modeled-external"),
                "{} lacks the modeled-external tag every case in this matrix carries",
                path.display()
            );
        }
    }
}

/// A modeling sink is reached through its receiver, so the modeling ECMA
/// dialect counts `Audit.record(v)` as a callsite of `record` where the
/// kernel dialect deliberately does not. Nothing else about the two
/// differs, and no kernel uses the member-qualified variant.
#[test]
fn the_modeling_ecma_dialect_accepts_a_member_qualified_callsite() {
    assert!(AnchorDialect::EcmaMember.is_call("  Audit.record(dfb_source());", "record"));
    assert!(!AnchorDialect::Ecma.is_call("  Audit.record(dfb_source());", "record"));
    for dialect in [AnchorDialect::Ecma, AnchorDialect::EcmaMember] {
        assert!(dialect.is_call("  dfb_sink(value);", "dfb_sink"));
        // A declaration is never a callsite, and a longer identifier that
        // merely ends with the member name is never one either.
        assert!(!dialect.is_call("  record: function record(value) {},", "record"));
        assert!(!dialect.is_call("  preRecord(value);", "record"));
        assert_eq!(
            dialect.declared_function_name(
                "  record: function record(value) {}, // DFB-SINK: m",
                "DFB-SINK: m"
            ),
            Some("record".to_string())
        );
    }
    assert_eq!(
        modeling_anchor_dialect(ModelingLanguage::Javascript).unwrap(),
        AnchorDialect::EcmaMember
    );
    assert_eq!(
        modeling_anchor_dialect(ModelingLanguage::Python).unwrap(),
        AnchorDialect::Python
    );
}

/// The Joern source-selector shape is decided from the template identity,
/// never from a fixture's tags and never from an observed result. Category
/// E is the one category whose analysis root is a parameter of a method the
/// fixture never calls; every other category's source is a call.
#[test]
fn the_joern_modeling_source_kind_is_template_keyed() {
    for template in MODELING_TEMPLATE_IDS {
        let expected = if modeling_category(template) == Some(ModelingCategory::EntryPoints) {
            "method-parameter"
        } else {
            "call-return"
        };
        assert_eq!(modeling_joern_source_kind(template).unwrap(), expected);
    }
    assert_eq!(
        modeling_joern_source_kind("dfb-template-model-entrypoint-parameter").unwrap(),
        "method-parameter"
    );
    assert_eq!(
        modeling_joern_source_kind("dfb-template-model-opaque-propagator").unwrap(),
        "call-return"
    );
    assert!(modeling_joern_source_kind("dfb-template-direct-propagation").is_err());
}

/// The equivalence contract's other half: an artifact must not declare a
/// category the tool's partition marks `unsupported`, because the partition
/// — not the artifact — is what decides those cells. Every language's
/// Bifrost policy therefore carries source and sink endpoint sets and
/// nothing else, its Semgrep rule carries sources, sinks, and sanitizers and
/// no propagator or store vocabulary, and its Joern semantics declares
/// nothing behind Amendment A2's declined categories P and O.
#[test]
fn the_modeling_artifacts_declare_only_their_scored_categories() {
    for (language, policy_name, rule_name, declined_joern_files) in [
        (
            ModelingLanguage::Python,
            "model-python.rqlp",
            "model-python.yaml",
            ["opaque.py", "bridge.py"],
        ),
        (
            ModelingLanguage::Javascript,
            "model-javascript.rqlp",
            "model-javascript.yaml",
            ["Opaque.js", "Bridge.js"],
        ),
        // Java's Joern identities are fully qualified method full names
        // rather than file-scoped ones, so the declined categories are
        // named by their declaring type: `Opaque` carries category P's
        // entities and `Bridge` carries category O's.
        (
            ModelingLanguage::Java,
            "model-java.rqlp",
            "model-java.yaml",
            ["dataflowbench.taint.Opaque", "dataflowbench.taint.Bridge"],
        ),
    ] {
        let policy = fs::read_to_string(language.artifact(ModelingTool::Bifrost).unwrap()).unwrap();
        require_bifrost_modeling_load_bearing(&policy, policy_name).unwrap();
        // Amendment A9 promoted category Z, so the sanitizer section is now
        // required rather than forbidden: the invariant is that an artifact
        // declares exactly its scored categories — a declined category is
        // absent from it, and a scored one may not be missing from it.
        assert!(
            policy.contains(":sanitizers"),
            "the Bifrost {policy_name} modeling policy declares no sanitizer, which its partition scores (Amendment A9)"
        );
        for declined in [
            ":transforms",
            ":external-models",
            ":external_models",
            ":entry-points",
        ] {
            assert!(
                !policy.contains(declined),
                "the Bifrost {policy_name} modeling policy declares {declined}, which its partition marks unsupported"
            );
        }

        let rule = fs::read_to_string(language.artifact(ModelingTool::Semgrep).unwrap()).unwrap();
        require_semgrep_modeling_load_bearing(&rule, rule_name).unwrap();
        assert!(rule.contains("pattern-sanitizers"));
        assert!(
            !rule.contains("pattern-propagators"),
            "the Semgrep {rule_name} modeling rule declares a propagator, which its partition marks unsupported"
        );

        // Amendment A2 declines Joern's categories P and O, so the semantics
        // file must not declare their entities: the cells are decided by the
        // partition, and a declaration behind them would be a claim the
        // partition does not make.
        let semantics =
            fs::read_to_string(language.artifact(ModelingTool::Joern).unwrap()).unwrap();
        for declined in declined_joern_files {
            assert!(
                !semantics.contains(&format!("\"{declined}")),
                "the Joern {} semantics declares {declined}, whose categories Amendment A2 marks unsupported",
                language.display_name()
            );
        }

        // Joern's semantics file fails silently on a blank line or a `//`
        // comment: both parse to an empty model with no error, and every
        // scored cell would then be decided by the absence of a
        // declaration. The rule is verified here rather than left to a run.
        for (number, line) in semantics.lines().enumerate() {
            assert!(
                !line.trim().is_empty(),
                "line {} of the Joern {} semantics is blank; the pinned parser drops every declaration",
                number + 1,
                language.display_name()
            );
            assert!(
                !line.trim_start().starts_with("//"),
                "line {} of the Joern {} semantics uses a `//` comment, which the pinned parser does not recognize",
                number + 1,
                language.display_name()
            );
        }
    }
}

/// With no population, a run fails with a clear error naming the language
/// and never writes a report.
///
/// Wave M1 is complete, so no `ModelingLanguage` variant reaches that arm
/// any more — this test used to drive it through Java, which had no
/// fixtures. What it asserts now is the arm's *precondition*: every
/// enumerated language carries the full balanced population, which is
/// exactly what makes the empty-population bail unreachable. The bail
/// itself stays, for the state the next language enters the enum in.
#[test]
fn a_modeling_run_without_a_population_fails_fast() {
    for language in [
        ModelingLanguage::Python,
        ModelingLanguage::Javascript,
        ModelingLanguage::Java,
    ] {
        assert_eq!(
            select_modeling_cases(language).unwrap().len(),
            MODELING_CASE_COUNT,
            "{} has no modeling population",
            language.display_name()
        );
    }
}

/// A Bifrost modeling policy must make the model load-bearing: the kernel
/// policies' optimistic unmodeled-call default would decide a category P
/// or O cell without the declaration ever being read.
#[test]
fn a_bifrost_modeling_policy_must_require_the_model() {
    let optimistic =
        "(analysis :type taint :mode may :call-modeling (call-modeling :unmodeled optimistic))";
    let error =
        require_bifrost_modeling_load_bearing(optimistic, "adapters/bifrost/policies/x.rqlp")
            .unwrap_err()
            .to_string();
    assert!(error.contains("require-model"), "{error}");

    let silent = "(analysis :type taint :mode may)";
    assert!(
        require_bifrost_modeling_load_bearing(silent, "adapters/bifrost/policies/x.rqlp").is_err()
    );

    let load_bearing =
        "(analysis :type taint :mode may :call-modeling (call-modeling :unmodeled require-model))";
    require_bifrost_modeling_load_bearing(load_bearing, "adapters/bifrost/policies/x.rqlp")
        .unwrap();
    assert_eq!(BIFROST_MODELING_CALL_MODELING, "require-model");
}

/// A Semgrep modeling rule must disable the engine's default pass-through,
/// which the preregistration verified against the pinned CE binary.
#[test]
fn a_semgrep_modeling_rule_must_assume_safe_functions() {
    let permissive = "rules:\n  - id: dfb-model\n    mode: taint\n";
    let error = require_semgrep_modeling_load_bearing(permissive, "adapters/semgrep/rules/x.yaml")
        .unwrap_err()
        .to_string();
    assert!(
        error.contains("taint_assume_safe_functions: true"),
        "{error}"
    );

    let load_bearing = "rules:\n  - id: dfb-model\n    mode: taint\n    options:\n      taint_assume_safe_functions: true\n";
    require_semgrep_modeling_load_bearing(load_bearing, "adapters/semgrep/rules/x.yaml").unwrap();
    assert_eq!(
        SEMGREP_MODELING_ASSUME_SAFE_OPTION,
        "taint_assume_safe_functions: true"
    );
}

/// The model-artifact, report, and raw-evidence paths the language pull
/// requests populate: one per tool per language for the wave-M1 four,
/// plus the amendment-added adapters' single-language artifacts — their
/// other combinations have no denominator at all.
#[test]
fn modeling_artifact_and_report_paths_follow_the_convention() {
    let mut artifacts = BTreeSet::new();
    for tool in ModelingTool::ALL.iter().copied() {
        for language in [
            ModelingLanguage::Java,
            ModelingLanguage::Javascript,
            ModelingLanguage::Python,
        ] {
            if let Some(artifact) = language.artifact(tool) {
                assert!(artifacts.insert(artifact));
            } else {
                match tool {
                    ModelingTool::Infer | ModelingTool::Flowdroid | ModelingTool::Opentaint => {
                        assert_ne!(language, ModelingLanguage::Java)
                    }
                    ModelingTool::Pysa => assert_ne!(language, ModelingLanguage::Python),
                    other => panic!("{} × {} lost its artifact", other.key(), language.key()),
                }
            }
            assert_eq!(
                language.report(tool),
                PathBuf::from(format!(
                    "reports/{}-{}-modeling.json",
                    tool.key(),
                    language.key()
                ))
            );
            assert_eq!(
                language.raw_dir(tool),
                PathBuf::from(format!(
                    "reports/raw/{}-{}-modeling",
                    tool.key(),
                    language.key()
                ))
            );
        }
    }
    // Wave M1's twelve, Infer's, Pysa's, and OpenTaint's
    // single-language artifacts (A13, A16, A22), and FlowDroid's
    // Java-only summaries directory (A18). Uniqueness is the content of
    // the `insert` assertions above, and membership of the
    // amendment-added artifacts is pinned below — no total is pinned as
    // a literal, so a new adapter's artifact cannot race another's in
    // this assertion.
    assert!(artifacts.contains("adapters/opentaint/rules/model-java.yaml"));
    assert_eq!(
        ModelingLanguage::Python.artifact(ModelingTool::Pysa),
        Some("adapters/pysa/models/modeling-python.pysa")
    );
    assert_eq!(
        ModelingLanguage::Java.artifact(ModelingTool::Bifrost),
        Some("adapters/bifrost/policies/model-java.rqlp")
    );
    assert_eq!(
        ModelingLanguage::Python.artifact(ModelingTool::Semgrep),
        Some("adapters/semgrep/rules/model-python.yaml")
    );
    assert_eq!(
        ModelingLanguage::Javascript.artifact(ModelingTool::Joern),
        Some("adapters/joern/semantics/model-javascript.semantics")
    );
    assert_eq!(
        ModelingLanguage::Javascript.artifact(ModelingTool::Codeql),
        Some("adapters/codeql/javascript/queries/JavaScriptModeling.ql")
    );
    // Java's CodeQL query is the one that stays on the preregistration's
    // schematic path, because the Java pack *is* the adapter root.
    assert_eq!(
        ModelingLanguage::Java.artifact(ModelingTool::Codeql),
        Some("adapters/codeql/queries/JavaModeling.ql")
    );
    assert_eq!(
        ModelingLanguage::Java.artifact(ModelingTool::Infer),
        Some("adapters/infer/config/model-java.json")
    );
    assert_eq!(ModelingLanguage::Python.artifact(ModelingTool::Infer), None);
    assert_eq!(
        ModelingLanguage::Javascript.artifact(ModelingTool::Infer),
        None
    );
    assert_eq!(
        ModelingLanguage::Java.artifact(ModelingTool::Flowdroid),
        Some(FLOWDROID_MODELING_SUMMARIES_DIR)
    );
    assert_eq!(
        ModelingLanguage::Python.artifact(ModelingTool::Flowdroid),
        None
    );
    assert_eq!(
        ModelingLanguage::Javascript.artifact(ModelingTool::Flowdroid),
        None
    );
    // Each artifact arrives with the pull request that authors its
    // declarations. Wave M1 is complete; Infer's, FlowDroid's, and
    // OpenTaint's Java rows landed with Amendments A13, A18, and A22,
    // and Pysa's Python row with Amendment A16. FlowDroid's artifact is
    // a directory of three committed summary files, checked individually
    // because a directory has no bytes for the configuration hash to
    // bind.
    for tool in ModelingTool::ALL.iter().copied() {
        for language in [
            ModelingLanguage::Python,
            ModelingLanguage::Javascript,
            ModelingLanguage::Java,
        ] {
            if let Some(artifact) = language.artifact(tool) {
                if tool == ModelingTool::Flowdroid {
                    assert!(Path::new(artifact).is_dir(), "{artifact} is missing");
                } else {
                    assert!(Path::new(artifact).is_file(), "{artifact} is missing");
                }
            }
        }
    }
    for summary in FLOWDROID_MODELING_SUMMARY_FILES {
        assert!(
            Path::new(summary).is_file(),
            "{summary} is missing from the committed FlowDroid modeling summaries"
        );
        assert!(summary.starts_with(FLOWDROID_MODELING_SUMMARIES_DIR));
    }
    require_flowdroid_modeling_declarations().unwrap();
    assert!(Path::new(JOERN_MODELING_SCRIPT).is_file());
    // A CodeQL modeling query must sit inside a resolvable pack, which is
    // what makes its `codeql/<lang>-all` dependency resolvable at all.
    for language in [
        ModelingLanguage::Python,
        ModelingLanguage::Javascript,
        ModelingLanguage::Java,
    ] {
        let query = PathBuf::from(language.artifact(ModelingTool::Codeql).unwrap());
        let pack = query
            .parent()
            .and_then(Path::parent)
            .expect("a modeling query lives under <pack>/queries/")
            .join("qlpack.yml");
        assert!(
            pack.is_file(),
            "{} resolves no qlpack at {}",
            query.display(),
            pack.display()
        );
    }
}

/// An absent *declared* endpoint is the content of several modeling
/// negatives — template 2's negative calls `Audit.discard`, so the declared
/// sink `Audit.record` is not in the fixture at all. Under the kernels'
/// rule that would be `inconclusive`; under the modeling rule it is the
/// clean negative it is, with the endpoint counts retained rather than
/// converted. Only an empty extraction is incomplete.
#[test]
fn a_modeling_negative_may_legitimately_contain_no_declared_endpoint() {
    let root = unique_test_dir("dataflowbench-joern-modeling-endpoints");
    let case_path = root.join("case.json");
    fs::write(
        root.join("fixture.js"),
        "function dfb_sink(v) {} // DFB-SINK: s\ndfb_sink(1);\n",
    )
    .unwrap();
    let case = json!({
        "sink_anchors": [{"marker": "DFB-SINK: s", "file": "fixture.js", "line_hint": 1}]
    });
    let absent = json!({
        "state": "analyzed",
        "source_node_count": 1,
        "sink_node_count": 0,
        "method_count": 4,
        "flows": []
    });
    let (outcome, diagnostics) = joern_flow_outcome(
        &case_path,
        &case,
        &absent,
        AnchorDialect::EcmaMember,
        JoernEndpointRule::AbsenceIsTheAssertion,
    );
    assert_eq!(outcome, "not-reached");
    assert!(
        diagnostics
            .iter()
            .any(|line| line.contains("0 declared sink node(s)"))
    );
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &absent,
            AnchorDialect::EcmaMember,
            JoernEndpointRule::BothMustBeObserved
        )
        .0,
        "inconclusive"
    );
    // An empty extraction is still incomplete under the modeling rule.
    let mut empty = absent.clone();
    empty["method_count"] = json!(0);
    assert_eq!(
        joern_flow_outcome(
            &case_path,
            &case,
            &empty,
            AnchorDialect::EcmaMember,
            JoernEndpointRule::AbsenceIsTheAssertion
        )
        .0,
        "inconclusive"
    );
    fs::remove_dir_all(&root).unwrap();
}

/// A Semgrep **modeling** rule lives beside the kernel rules but is not
/// part of the kernel configuration. Every published Semgrep kernel report
/// cites a hash over the eleven kernel rules, and committing a twelfth file
/// for a different population must not silently invalidate all eleven.
#[test]
fn a_semgrep_modeling_rule_is_outside_the_kernel_configuration_hash() {
    let kernel_rules = semgrep_rule_paths().unwrap();
    assert_eq!(kernel_rules.len(), 11);
    let modeling = PathBuf::from(
        ModelingLanguage::Javascript
            .artifact(ModelingTool::Semgrep)
            .unwrap(),
    );
    assert!(modeling.is_file());
    assert!(!kernel_rules.contains(&modeling));
    // The v0.4.0 freeze binds this hash; it is reproduced here rather than
    // recomputed, so a rule-set change fails the suite instead of a run.
    assert_eq!(
        hash_paths(&kernel_rules).unwrap(),
        "865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100"
    );
}

/// The committed JavaScript artifacts pass the gates the runner applies
/// before it will touch an analyzer, so a load-bearing regression in one
/// of them fails the test suite rather than a run.
#[test]
fn the_javascript_modeling_artifacts_are_load_bearing() {
    let policy_path = ModelingLanguage::Javascript
        .artifact(ModelingTool::Bifrost)
        .unwrap();
    require_bifrost_modeling_load_bearing(&fs::read_to_string(policy_path).unwrap(), policy_path)
        .unwrap();
    let rule_path = ModelingLanguage::Javascript
        .artifact(ModelingTool::Semgrep)
        .unwrap();
    require_semgrep_modeling_load_bearing(&fs::read_to_string(rule_path).unwrap(), rule_path)
        .unwrap();
}

/// The same two gates on Java's artifacts. `require-model` is the one the
/// preregistration marked *to be verified*: it recorded that no committed
/// policy sets it and that the pinned CLI's acceptance of it was unshown.
/// [Amendment A5](../docs/modeling-matrix.md#amendments) records the
/// verification; this test is what keeps it true.
#[test]
fn the_java_modeling_artifacts_are_load_bearing() {
    let policy_path = ModelingLanguage::Java
        .artifact(ModelingTool::Bifrost)
        .unwrap();
    let policy = fs::read_to_string(policy_path).unwrap();
    require_bifrost_modeling_load_bearing(&policy, policy_path).unwrap();
    assert!(policy.contains(BIFROST_MODELING_CALL_MODELING));
    let rule_path = ModelingLanguage::Java
        .artifact(ModelingTool::Semgrep)
        .unwrap();
    let rule = fs::read_to_string(rule_path).unwrap();
    require_semgrep_modeling_load_bearing(&rule, rule_path).unwrap();
    assert!(rule.contains(SEMGREP_MODELING_ASSUME_SAFE_OPTION));
}

/// Java's modeling fixtures reconcile under the member-qualified variant,
/// not the kernel dialect. Java has no free functions, so every declared
/// modeling entity is reached through its declaring type; the kernel
/// dialect refuses exactly that spelling, which is right for a kernel whose
/// `dfb_sink` is called bare.
#[test]
fn java_modeling_reconciles_member_qualified_callsites() {
    assert_eq!(
        modeling_anchor_dialect(ModelingLanguage::Java).unwrap(),
        AnchorDialect::JavaMember
    );
    // The declared-entity spelling every Java modeling fixture uses.
    assert!(AnchorDialect::JavaMember.is_call("        Audit.record(value);", "record"));
    assert!(
        AnchorDialect::JavaMember.is_call("        dfb_sink(Config.fetchLocal());", "fetchLocal")
    );
    assert!(AnchorDialect::JavaMember.is_call("        beta.get(\"k\");", "get"));
    // …which the kernel dialect deliberately refuses.
    assert!(!AnchorDialect::Java.is_call("        Audit.record(value);", "record"));
    // Neither variant mistakes a longer identifier, a comment, or a bare
    // member access with no argument list for a callsite.
    assert!(!AnchorDialect::JavaMember.is_call("        myRecord(value);", "record"));
    assert!(!AnchorDialect::JavaMember.is_call("        // Audit.record(value);", "record"));
    assert!(!AnchorDialect::JavaMember.is_call("        dfb_sink(box.payload);", "payload"));
    assert!(!AnchorDialect::JavaMember.is_call("        Audit::record;", "record"));
    // The declaration side is the kernel rule unchanged: the marker sits on
    // the identifier before the parameter list either way.
    assert_eq!(
        AnchorDialect::JavaMember
            .declared_function_name(
                "    static void record(String value) { }  // DFB-SINK: m",
                "DFB-SINK: m"
            )
            .unwrap(),
        "record"
    );
}

/// Every wave-M1 modeling language is wired end to end: an extractor, a
/// Joern frontend, and an anchor dialect, none of which may bail.
#[test]
fn every_wave_m1_modeling_language_has_a_wired_execution_arm() {
    for language in [
        ModelingLanguage::Python,
        ModelingLanguage::Javascript,
        ModelingLanguage::Java,
    ] {
        modeling_codeql_language(language).unwrap();
        modeling_joern_frontend(language).unwrap();
        modeling_anchor_dialect(language).unwrap();
    }
    assert_eq!(
        modeling_joern_frontend(ModelingLanguage::Java).unwrap(),
        "JAVASRC"
    );
}

// -----------------------------------------------------------------------
// The tool-native model profile.
// -----------------------------------------------------------------------

/// One synthetic tool-native case, carrying every field the native
/// validators read.
fn native_case_value(template: &str, polarity: &str, language: &str) -> Value {
    let short = template
        .strip_prefix(NATIVE_TEMPLATE_PREFIX)
        .expect("a tool-native template");
    json!({
        "id": format!("dfb-taint-{language}-native-{short}-{polarity}"),
        "template_id": template,
        "polarity": polarity,
        "score_tier": "modeling",
        "track": "taint",
        "language": language,
        "model_profile": NATIVE_MODEL_PROFILE,
        "feature_tags": ["modeled-external", "intraprocedural"],
        "expected_analysis_capability": {"kind": "native-source-sink-coverage"}
    })
}

/// A whole balanced tool-native population for one language: 12 assertions
/// over the preregistered six.
fn native_population(language: &str) -> Vec<(PathBuf, Value)> {
    let mut cases = Vec::new();
    for template in NATIVE_TEMPLATE_IDS {
        for polarity in ["positive", "negative"] {
            cases.push((
                PathBuf::from(format!(
                    "cases/taint/{language}/{template}-{polarity}/case.json"
                )),
                native_case_value(template, polarity, language),
            ));
        }
    }
    cases
}

/// The six template IDs are the document's, unique, and all carry the
/// profile's structural prefix.
#[test]
fn native_templates_are_the_preregistered_six() {
    assert_eq!(NATIVE_TEMPLATE_IDS.len(), 6);
    assert_eq!(NATIVE_CASE_COUNT, 12);
    let unique: BTreeSet<&str> = NATIVE_TEMPLATE_IDS.into_iter().collect();
    assert_eq!(unique.len(), 6);
    for template in NATIVE_TEMPLATE_IDS {
        assert!(
            template.starts_with(NATIVE_TEMPLATE_PREFIX),
            "{template} lacks the tool-native prefix"
        );
        assert!(
            !template.starts_with(MODELING_TEMPLATE_PREFIX),
            "{template} collides with the benchmark-controlled family"
        );
    }
}

/// Each native template reports under exactly one modeling category, and
/// the six cover all six — which is what lets a native scorecard be read
/// beside a benchmark-controlled one category for category.
#[test]
fn every_native_template_maps_to_one_category() {
    let categories: BTreeSet<ModelingCategory> = NATIVE_TEMPLATE_IDS
        .into_iter()
        .map(|template| native_category(template).expect("a category"))
        .collect();
    assert_eq!(categories.len(), 6);
    assert_eq!(
        native_category("dfb-template-native-source-sink"),
        Some(ModelingCategory::SourcesAndSinks)
    );
    assert_eq!(
        native_category("dfb-template-native-persistence"),
        Some(ModelingCategory::Persistence)
    );
    assert_eq!(native_category("dfb-template-model-declared-source"), None);
    assert_eq!(native_category("dfb-template-direct-propagation"), None);
}

/// Every tool × template cell is preregistered, and a template outside the
/// six is an error rather than a silent scored default.
#[test]
fn the_native_partition_decides_every_tool_and_template() {
    // One cell per tool per template, for every tool in `ALL` — derived,
    // not a literal, for the same reason as the modeling count above.
    assert_eq!(
        NATIVE_PARTITION.len(),
        ModelingTool::ALL.len() * NATIVE_TEMPLATE_IDS.len()
    );
    for tool in ModelingTool::ALL.iter().copied() {
        for template in NATIVE_TEMPLATE_IDS {
            for language in [
                ModelingLanguage::Java,
                ModelingLanguage::Javascript,
                ModelingLanguage::Python,
            ] {
                native_partition_reason(tool, language, template).unwrap_or_else(|_| {
                    panic!(
                        "no cell for {} × {} × {template}",
                        tool.key(),
                        language.key()
                    )
                });
            }
        }
    }
    assert!(
        native_partition_reason(
            ModelingTool::Codeql,
            ModelingLanguage::Java,
            "dfb-template-model-declared-source"
        )
        .is_err()
    );
    assert!(
        native_partition_reason(
            ModelingTool::Codeql,
            ModelingLanguage::Java,
            "dfb-template-chal-dispatch-table"
        )
        .is_err()
    );
}

/// The scored counts are the preregistration's partition summary as
/// amended. CodeQL entered with six of six and the other three with
/// nothing, which is a statement about product packaging rather than about
/// an engine — Joern scores four of six *categories* on the
/// benchmark-controlled matrix with the same engine. Amendment A8
/// promotes Semgrep CE's six Python cells on the evidence of the vendored
/// snapshot, and touches no other language.
#[test]
fn native_partition_scored_counts_match_the_preregistration() {
    for language in [
        ModelingLanguage::Java,
        ModelingLanguage::Javascript,
        ModelingLanguage::Python,
    ] {
        assert_eq!(
            native_supported_templates(ModelingTool::Codeql, language),
            NATIVE_TEMPLATE_IDS.to_vec()
        );
        assert!(native_supported_templates(ModelingTool::Bifrost, language).is_empty());
        assert!(native_supported_templates(ModelingTool::Joern, language).is_empty());
        // Amendment A14: Infer declines all six on a measured silence. The
        // partition decides every language's cells, but only Java has an
        // Infer native denominator — `native_activation` refuses the other
        // two before a run can be shaped.
        assert!(native_supported_templates(ModelingTool::Infer, language).is_empty());
        // Amendment A23: the pinned OpenTaint release ships propagation
        // models and no endpoint catalog, so nothing activates. (The row
        // itself is Java-only; the partition cells exist for every
        // language, and the activation shape is what refuses the others.)
        assert!(native_supported_templates(ModelingTool::Opentaint, language).is_empty());
    }
    // Amendment A8: Python only.
    assert_eq!(
        native_supported_templates(ModelingTool::Semgrep, ModelingLanguage::Python),
        NATIVE_TEMPLATE_IDS.to_vec()
    );
    assert!(native_supported_templates(ModelingTool::Semgrep, ModelingLanguage::Java).is_empty());
    assert!(
        native_supported_templates(ModelingTool::Semgrep, ModelingLanguage::Javascript).is_empty()
    );
}

/// Every amendment row names one of the six preregistered templates, so a
/// typo cannot silently create a seventh cell that decides nothing.
#[test]
fn native_partition_amendments_name_preregistered_templates() {
    for (tool, language, template, _) in NATIVE_PARTITION_AMENDMENTS {
        assert!(
            NATIVE_TEMPLATE_IDS.contains(&template),
            "{} × {} amends {template}, which is not a preregistered template",
            tool.key(),
            language.key()
        );
    }
}

/// The partition is decided by template identity, never by a fixture's
/// tags: rewriting `feature_tags` cannot move a cell between the scored and
/// `unsupported` partitions.
#[test]
fn the_native_partition_is_tag_proof() {
    let template = "dfb-template-native-summary";
    let baseline = native_unsupported_reason(
        ModelingTool::Joern,
        ModelingLanguage::Java,
        template,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert!(baseline.is_some());
    for tags in [
        json!([]),
        json!(["modeled-external"]),
        json!(["summary-required", "heap-access-path"]),
    ] {
        let mut case = native_case_value(template, "positive", "java");
        case["feature_tags"] = tags;
        assert_eq!(
            native_unsupported_reason(
                ModelingTool::Joern,
                ModelingLanguage::Java,
                case["template_id"].as_str().unwrap(),
                WITNESSED_IDENTITY
            )
            .unwrap(),
            baseline
        );
    }
    let scored = "dfb-template-native-summary";
    assert!(
        native_unsupported_reason(
            ModelingTool::Codeql,
            ModelingLanguage::Java,
            scored,
            WITNESSED_IDENTITY
        )
        .unwrap()
        .is_none()
    );
}

/// A declined cell's reason is retained verbatim and attributed to the
/// **witnessed** tool identity and the document that decided it.
///
/// The Bifrost row is the one that makes the witnessing matter: it declines
/// all six templates and hands the analyzer nothing, so these twelve
/// rationales are the whole of its evidence and the identity they name has
/// to be one the run actually read.
#[test]
fn native_unsupported_reasons_are_retained_and_attributed() {
    let reason = native_unsupported_reason(
        ModelingTool::Bifrost,
        ModelingLanguage::Java,
        "dfb-template-native-sanitizer",
        WITNESSED_IDENTITY,
    )
    .unwrap()
    .expect("declined");
    // Amendment A10 replaced the withdrawn README citation with the
    // endpoint-catalog grounds; the cell's decision is unchanged.
    assert!(reason.contains("restated by Amendment A10"));
    assert!(reason.contains("BrokkAi/bifrost-dev #2620"));
    assert!(reason.contains(WITNESSED_IDENTITY));
    assert!(reason.contains("docs/native-profile.md"));
    for tool in ModelingTool::ALL.iter().copied() {
        for template in NATIVE_TEMPLATE_IDS {
            if let Some(reason) = native_unsupported_reason(
                tool,
                ModelingLanguage::Java,
                template,
                WITNESSED_IDENTITY,
            )
            .unwrap()
            {
                assert!(reason.contains(WITNESSED_IDENTITY));
                assert!(reason.contains(template));
            }
        }
    }
}

/// A declined cell writes its retained decision beside the report without
/// the analyzer being invoked, and carries the pinned activation
/// configuration with it.
#[test]
fn a_declined_native_cell_retains_evidence_without_invoking_the_tool() {
    let root = unique_test_dir("dataflowbench-native-partition-test");
    let activation = native_activation(
        ModelingTool::Joern,
        ModelingLanguage::Python,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    let case = native_case_value("dfb-template-native-persistence", "positive", "python");
    let (outcome, reason, raw_path) = native_partition_outcome(
        ModelingTool::Joern,
        ModelingLanguage::Python,
        &case,
        &activation,
        &root,
        WITNESSED_IDENTITY,
    )
    .unwrap()
    .expect("declined");
    assert_eq!(outcome, "unsupported");
    let retained: Value = serde_json::from_str(&fs::read_to_string(&raw_path).unwrap()).unwrap();
    assert_eq!(retained["state"], "unsupported");
    assert_eq!(
        retained["stage"],
        "preregistered-native-activation-partition"
    );
    assert_eq!(retained["model_profile"], NATIVE_MODEL_PROFILE);
    assert_eq!(retained["modeling_category"], "B");
    assert_eq!(retained["reason"], reason);
    assert_eq!(retained["activation_identity"], activation.identity);
    assert_eq!(retained["witnessed_tool_identity"], WITNESSED_IDENTITY);
    assert_eq!(retained["evidence_kind"], "retained-capability-decision");

    let scored = native_case_value("dfb-template-native-source-sink", "positive", "python");
    let activation = native_activation(
        ModelingTool::Codeql,
        ModelingLanguage::Python,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert!(
        native_partition_outcome(
            ModelingTool::Codeql,
            ModelingLanguage::Python,
            &scored,
            &activation,
            &root,
            WITNESSED_IDENTITY
        )
        .unwrap()
        .is_none()
    );
    fs::remove_dir_all(&root).unwrap();
}

/// A language with no native cases has no native denominator, which is
/// different from having a zero.
#[test]
fn an_absent_native_population_validates_trivially() {
    validate_native_population(&[], "Java tool-native population").unwrap();
    validate_native_cases(&[]).unwrap();
    validate_profile_disjoint_populations(&[]).unwrap();
}

/// A whole balanced population of twelve validates, and the same population
/// passes the corpus-wide checks.
#[test]
fn a_balanced_native_population_validates() {
    let cases = native_population("java");
    assert_eq!(cases.len(), NATIVE_CASE_COUNT);
    validate_native_population(&cases, "Java tool-native population").unwrap();
    validate_native_cases(&cases).unwrap();
    validate_profile_disjoint_populations(&cases).unwrap();
    // And it is invisible to the benchmark-controlled validator, which is
    // the whole point of the shared tier plus disjoint profile.
    validate_modeling_cases(&cases).unwrap();
}

/// A partial, unbalanced, or renamed population fails the build rather than
/// silently reducing a denominator.
#[test]
fn an_incomplete_native_population_fails_validation() {
    let mut short = native_population("javascript");
    short.pop();
    let error = validate_native_population(&short, "JavaScript tool-native population")
        .unwrap_err()
        .to_string();
    assert!(error.contains("exactly 12 assertions"), "{error}");

    let mut unbalanced = native_population("javascript");
    unbalanced[1].1["polarity"] = json!("positive");
    let error = validate_native_population(&unbalanced, "JavaScript tool-native population")
        .unwrap_err()
        .to_string();
    assert!(error.contains("one positive and one negative"), "{error}");

    let mut renamed = native_population("javascript");
    renamed[0].1["template_id"] = json!("dfb-template-native-invented");
    let error = validate_native_population(&renamed, "JavaScript tool-native population")
        .unwrap_err()
        .to_string();
    assert!(error.contains("template set mismatch"), "{error}");
}

/// The template family and the profile imply each other, so a native case
/// cannot hide inside the benchmark-controlled population and a
/// benchmark-controlled case cannot claim the native profile.
#[test]
fn the_native_family_and_the_tool_native_profile_imply_each_other() {
    let mut reprofiled = native_population("python");
    reprofiled[0].1["model_profile"] = json!(MODELING_MODEL_PROFILE);
    let error = validate_native_cases(&reprofiled).unwrap_err().to_string();
    assert!(error.contains("disagree"), "{error}");

    let smuggled = vec![(
        PathBuf::from("cases/taint/python/smuggled/case.json"),
        json!({
            "id": "dfb-taint-python-smuggled",
            "template_id": "dfb-template-direct-propagation",
            "polarity": "positive",
            "score_tier": "core",
            "track": "taint",
            "language": "python",
            "model_profile": NATIVE_MODEL_PROFILE
        }),
    )];
    let error = validate_native_cases(&smuggled).unwrap_err().to_string();
    assert!(error.contains("disagree"), "{error}");

    let invented = vec![(
        PathBuf::from("cases/taint/python/invented/case.json"),
        json!({
            "id": "dfb-taint-python-native-invented-positive",
            "template_id": "dfb-template-native-invented",
            "polarity": "positive",
            "score_tier": "modeling",
            "track": "taint",
            "language": "python",
            "model_profile": NATIVE_MODEL_PROFILE
        }),
    )];
    let error = validate_native_cases(&invented).unwrap_err().to_string();
    assert!(
        error.contains("not one of the six preregistered tool-native templates"),
        "{error}"
    );
}

/// A native case shares the `modeling` tier; claiming another one fails.
#[test]
fn native_cases_stay_on_the_modeling_tier() {
    let mut cases = native_population("java");
    cases[0].1["score_tier"] = json!("core");
    let error = validate_native_cases(&cases).unwrap_err().to_string();
    assert!(error.contains("share the `modeling` score tier"), "{error}");
}

/// The two modeling-tier profiles never cross-select, in either direction,
/// for any language. This is the invariant a selector could break by
/// omission — filtering on the tier and forgetting the profile — so it is
/// asserted against the selectors themselves.
#[test]
fn the_two_model_profiles_never_cross_select() {
    for language in [
        ModelingLanguage::Java,
        ModelingLanguage::Javascript,
        ModelingLanguage::Python,
    ] {
        for (_, case) in native_population(language.key()) {
            assert!(native_case(&case, language), "{case}");
            assert!(
                !modeling_case(&case, language),
                "a tool-native case entered the benchmark-controlled {} selection",
                language.display_name()
            );
        }
        for (_, case) in modeling_population(language.key()) {
            assert!(modeling_case(&case, language), "{case}");
            assert!(
                !native_case(&case, language),
                "a benchmark-controlled case entered the tool-native {} selection",
                language.display_name()
            );
        }
    }
    // And a case that somehow claimed both is rejected corpus-wide.
    let mut hybrid = native_population("java");
    hybrid[0].1["template_id"] = json!(MODELING_TEMPLATE_IDS[0]);
    let error = validate_profile_disjoint_populations(&hybrid)
        .unwrap_err()
        .to_string();
    assert!(error.contains("benchmark-controlled template"), "{error}");
}

/// A tool-native case is never swept into the frozen 118-case Bifrost smoke
/// population, the same way a modeling or challenge case is not.
#[test]
fn a_native_case_is_never_smoke_selected() {
    let mut case = native_case_value("dfb-template-native-source-sink", "positive", "java");
    case["tool_model_references"] = json!({"bifrost": {"policy": BIFROST_JAVA_POLICY}});
    assert!(!smoke_population_case(&case));
}

/// Report and raw-evidence paths follow the profile's convention, and are
/// disjoint from the benchmark-controlled matrix's.
#[test]
fn native_report_and_raw_paths_follow_the_convention() {
    for tool in ModelingTool::ALL.iter().copied() {
        for language in [
            ModelingLanguage::Java,
            ModelingLanguage::Javascript,
            ModelingLanguage::Python,
        ] {
            let report = native_report_path(tool, language);
            assert_eq!(
                report,
                PathBuf::from(format!(
                    "reports/{}-{}-native.json",
                    tool.key(),
                    language.key()
                ))
            );
            assert_eq!(
                native_raw_dir(tool, language),
                PathBuf::from(format!(
                    "reports/raw/{}-{}-native",
                    tool.key(),
                    language.key()
                ))
            );
            assert_ne!(report, language.report(tool));
            assert_ne!(native_raw_dir(tool, language), language.raw_dir(tool));
        }
    }
}

/// The pinned activation shapes. These are the invocation surfaces the
/// no-benchmark-models gate runs against, so they are pinned literally:
/// a change to any of them is a change to what the published number means.
#[test]
fn the_native_activation_shapes_are_pinned() {
    let codeql = native_activation(
        ModelingTool::Codeql,
        ModelingLanguage::Java,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert_eq!(
        codeql.arguments,
        vec![
            "--threat-model=local".to_string(),
            "codeql/java-queries@1.11.9:codeql-suites/java-security-extended.qls".to_string(),
        ]
    );
    assert!(codeql.configuration_paths.is_empty());
    assert_eq!(
        native_activation(
            ModelingTool::Codeql,
            ModelingLanguage::Javascript,
            WITNESSED_IDENTITY
        )
        .unwrap()
        .arguments[1],
        "codeql/javascript-queries@2.4.4:codeql-suites/javascript-security-extended.qls"
    );
    assert_eq!(
        native_activation(
            ModelingTool::Codeql,
            ModelingLanguage::Python,
            WITNESSED_IDENTITY
        )
        .unwrap()
        .arguments[1],
        "codeql/python-queries@1.8.9:codeql-suites/python-security-extended.qls"
    );

    let semgrep = native_activation(
        ModelingTool::Semgrep,
        ModelingLanguage::Python,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert_eq!(
        semgrep.arguments,
        vec![
            "--oss-only".to_string(),
            "--config=adapters/semgrep/native/python".to_string(),
        ]
    );
    assert_eq!(
        semgrep.configuration_paths,
        BTreeSet::from([PathBuf::from(
            "adapters/semgrep/native/python/provenance.json"
        )])
    );
    assert!(semgrep.identity.contains(SEMGREP_NATIVE_UPSTREAM));

    let bifrost = native_activation(
        ModelingTool::Bifrost,
        ModelingLanguage::Java,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert_eq!(bifrost.arguments[0], BIFROST_NATIVE_POLICY_PACK_FLAG);
    assert!(
        !bifrost.arguments.iter().any(|a| a == "--policy-file"),
        "a native Bifrost run may not name a policy file"
    );

    let joern = native_activation(
        ModelingTool::Joern,
        ModelingLanguage::Java,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert!(joern.arguments.is_empty());
    assert!(joern.identity.contains("DefaultSemantics"));

    // OpenTaint (Amendment A23): the shipped models archive loads, and no
    // rule set of any kind is named — the rule set is where every
    // endpoint lives, and the pinned release ships none. Java only; the
    // other languages have no native denominator.
    let opentaint = native_activation(
        ModelingTool::Opentaint,
        ModelingLanguage::Java,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert!(opentaint.identity.contains("shipped models archive"));
    assert!(
        opentaint
            .arguments
            .iter()
            .all(|argument| !argument.contains("--semgrep-rule-set"))
    );
    assert!(
        opentaint
            .arguments
            .iter()
            .any(|argument| argument.contains("--passthrough-approximations"))
    );
    assert!(
        opentaint
            .arguments
            .iter()
            .any(|argument| argument.contains("--java-dataflow-approximations"))
    );
    require_no_benchmark_models(ModelingTool::Opentaint, &opentaint.arguments).unwrap();
    for language in [ModelingLanguage::Javascript, ModelingLanguage::Python] {
        let error = match native_activation(ModelingTool::Opentaint, language, WITNESSED_IDENTITY) {
            Ok(_) => panic!(
                "{} must have no OpenTaint native denominator",
                language.key()
            ),
            Err(error) => error.to_string(),
        };
        assert!(error.contains("no"), "{error}");
        assert!(error.contains("denominator"), "{error}");
    }
}

/// The activation rule, enforced: every pinned shape passes the gate, and
/// splicing any benchmark-authored model artifact into any of them fails
/// it. The artifact set is derived from the benchmark-controlled matrix's
/// own constants, so a new modeling artifact is covered the moment it is
/// declared.
#[test]
fn the_no_benchmark_models_gate_refuses_a_spliced_model_artifact() {
    for tool in ModelingTool::ALL.iter().copied() {
        for language in [
            ModelingLanguage::Java,
            ModelingLanguage::Javascript,
            ModelingLanguage::Python,
        ] {
            // Infer's and OpenTaint's native denominators are Java alone
            // (Amendments A14 and A19) and Pysa's is Python alone
            // (Amendment A17): the other languages have no activation
            // shape at all, and asking for one is an applicability
            // error, not a gate result.
            let covered = match tool {
                ModelingTool::Infer | ModelingTool::Flowdroid | ModelingTool::Opentaint => {
                    language == ModelingLanguage::Java
                }
                ModelingTool::Pysa => language == ModelingLanguage::Python,
                _ => true,
            };
            if !covered {
                let Err(error) = native_activation(tool, language, WITNESSED_IDENTITY) else {
                    panic!(
                        "{} × {} must have no native denominator",
                        tool.key(),
                        language.key()
                    );
                };
                assert!(
                    error
                        .to_string()
                        .contains("No denominator is different from a zero"),
                    "{error}"
                );
                continue;
            }
            let activation = native_activation(tool, language, WITNESSED_IDENTITY).unwrap();
            require_no_benchmark_models(tool, &activation.arguments).unwrap();
        }
    }
    let artifacts = benchmark_model_artifacts();
    // Wave M1's twelve, the shared Joern script, Infer's, Pysa's, and
    // OpenTaint's single-language artifacts, and FlowDroid's Java
    // summaries directory. Membership, not a pinned total: a new
    // adapter's artifact joins the derived set the moment it is declared,
    // with no literal here to race another pull request for.
    assert!(artifacts.contains("adapters/opentaint/rules/model-java.yaml"));
    assert!(artifacts.contains(JOERN_MODELING_SCRIPT));
    assert!(artifacts.contains(FLOWDROID_MODELING_SUMMARIES_DIR));
    assert!(artifacts.contains("adapters/pysa/models/modeling-python.pysa"));
    for artifact in &artifacts {
        let spliced = vec![format!("--config={artifact}")];
        let error = require_no_benchmark_models(ModelingTool::Semgrep, &spliced)
            .unwrap_err()
            .to_string();
        assert!(error.contains(artifact), "{error}");
        assert!(error.contains("only models the vendor ships"), "{error}");
    }
}

/// The pinned activation configuration binds the report's
/// `configuration_hash`, so provenance is a property of the artifact rather
/// than of a README: two different activations cannot produce one hash.
#[test]
fn the_activation_configuration_binds_the_report_hash() {
    let java = native_activation(
        ModelingTool::Codeql,
        ModelingLanguage::Java,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    let python = native_activation(
        ModelingTool::Codeql,
        ModelingLanguage::Python,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    assert_ne!(
        native_configuration_hash(&java).unwrap(),
        native_configuration_hash(&python).unwrap()
    );
    let mut retuned = native_activation(
        ModelingTool::Codeql,
        ModelingLanguage::Java,
        WITNESSED_IDENTITY,
    )
    .unwrap();
    retuned.arguments[0] = "--threat-model=remote".to_string();
    assert_ne!(
        native_configuration_hash(&java).unwrap(),
        native_configuration_hash(&retuned).unwrap()
    );
}

/// Wave N1 is complete: every native language carries a balanced twelve
/// over exactly the six preregistered templates, on the shared `modeling`
/// tier and the `tool-native` profile, supplying no models of our own.
///
/// A population is absent or complete and never partial. Wave N1 landed one
/// language per pull request, so the *absent* state was real while the wave
/// was open; with Python's row this closes issue #16 and all three are
/// complete. The fail-fast gate on an empty population stays in
/// `plan_native_run` — a partial or emptied population must never publish a
/// coverage rate against a denominator nobody declared.
#[test]
fn every_native_population_is_the_balanced_twelve() {
    for (language, revision) in [
        (ModelingLanguage::Java, "n1-native-java"),
        (ModelingLanguage::Javascript, "n1-native-javascript"),
        (ModelingLanguage::Python, "n1-native-python"),
    ] {
        let population = select_native_cases(language).unwrap();
        assert_eq!(
            population.len(),
            NATIVE_CASE_COUNT,
            "wave N1 landed the {} tool-native probe set",
            language.display_name()
        );
        let templates: BTreeSet<&str> = population
            .iter()
            .filter_map(|(_, case)| case["template_id"].as_str())
            .collect();
        assert_eq!(templates, NATIVE_TEMPLATE_IDS.into_iter().collect());
        for (path, case) in &population {
            assert_eq!(case["score_tier"], "modeling", "{}", path.display());
            assert_eq!(case["model_profile"], NATIVE_MODEL_PROFILE);
            assert_eq!(
                case["fixture_provenance"]["revision"],
                revision,
                "{}",
                path.display()
            );
            // The activation rule reaches the corpus too: a native case
            // names no model artifact of ours, because there are none.
            assert_eq!(
                case["tool_model_references"],
                json!({}),
                "{} references a benchmark-authored model",
                path.display()
            );
            // Every sink anchor resolves to the real API's own callsite
            // line, which is the line a shipped-suite finding must land on.
            let locations = native_sink_anchor_locations(path, case).unwrap();
            assert_eq!(locations.len(), 1, "{}", path.display());
            assert_eq!(
                locations[0].callsite_lines,
                BTreeSet::from([locations[0].marker_line]),
                "{}",
                path.display()
            );
        }
    }
}

/// The CodeQL native pins are *query* packs, and every one of them differs
/// from the library pack the benchmark-controlled adapter pins for that
/// language. The two profiles run on different library resolutions by
/// construction, which is one more reason they are never pooled.
#[test]
fn the_codeql_native_pins_are_query_packs() {
    assert_eq!(CODEQL_NATIVE_QUERY_PACKS.len(), 3);
    for (pack, version) in CODEQL_NATIVE_QUERY_PACKS {
        assert!(pack.ends_with("-queries"), "{pack} is not a query pack");
        assert!(!version.is_empty());
    }
    for language in [
        ModelingLanguage::Java,
        ModelingLanguage::Javascript,
        ModelingLanguage::Python,
    ] {
        let suite = native_activation(ModelingTool::Codeql, language, WITNESSED_IDENTITY)
            .unwrap()
            .arguments[1]
            .clone();
        assert!(
            suite.contains(&format!(
                "{}-{CODEQL_NATIVE_SUITE_KIND}.qls",
                language.key()
            )),
            "{suite}"
        );
        assert!(
            !suite.contains("adapters/"),
            "a native suite is never an adapter query: {suite}"
        );
    }
}

/// The Semgrep vendoring convention: one directory per language under the
/// adapter, disjoint from the benchmark-controlled rules directory, and a
/// provenance document that the runner requires before it will run.
#[test]
fn the_semgrep_native_vendoring_convention_is_pinned() {
    for language in [
        ModelingLanguage::Java,
        ModelingLanguage::Javascript,
        ModelingLanguage::Python,
    ] {
        let dir = semgrep_native_rules_dir(language);
        assert_eq!(
            dir,
            PathBuf::from(format!("adapters/semgrep/native/{}", language.key()))
        );
        let modeling_rule = PathBuf::from(language.artifact(ModelingTool::Semgrep).unwrap());
        assert!(!modeling_rule.starts_with(&dir));
        // A vendored snapshot exists only for a language whose wave-N1 pull
        // request has landed, and when it does it carries its provenance:
        // docs/native-profile.md#provenance-for-vendored-activation-artifacts
        // makes a snapshot with no recorded source commit not a snapshot,
        // and the runner refuses a run over one.
        //
        // The document requires *facts*, not a key layout, and the two
        // waves recorded them differently: JavaScript flat
        // (`upstream_commit`), Java nested (`upstream.commit`). Both are
        // read here so the required facts are checked for every landed
        // snapshot; harmonizing the two layouts would rewrite a vendored
        // file that the Semgrep configuration hash already covers, so it is
        // left to its own change.
        if dir.exists() {
            let provenance: Value = serde_json::from_str(
                &fs::read_to_string(dir.join(SEMGREP_NATIVE_PROVENANCE_FILE)).unwrap(),
            )
            .unwrap();
            let fact = |flat: &str, nested: &str| {
                let value = &provenance[flat];
                if value.is_null() {
                    provenance["upstream"][nested].clone()
                } else {
                    value.clone()
                }
            };
            assert_eq!(provenance["kind"], "derived");
            assert_eq!(
                fact("upstream_repository", "repository"),
                SEMGREP_NATIVE_UPSTREAM,
                "{} records its upstream repository",
                language.display_name()
            );
            assert_eq!(
                fact("upstream_commit", "commit")
                    .as_str()
                    .expect("a snapshot records its source commit")
                    .len(),
                40,
                "{} records a full upstream commit",
                language.display_name()
            );
            assert!(fact("upstream_license", "license").is_string());
            assert!(dir.join("rules").is_dir());
        }
    }
    assert_eq!(SEMGREP_NATIVE_PROVENANCE_FILE, "provenance.json");
    // Wave N1 is complete, so every native language has vendored its
    // snapshot. Python's uses the nested layout, so the `fact()` reader
    // above covers all three without any of them being rewritten.
    for landed in [
        ModelingLanguage::Javascript,
        ModelingLanguage::Java,
        ModelingLanguage::Python,
    ] {
        assert!(
            semgrep_native_rules_dir(landed).exists(),
            "wave N1 vendored the {} snapshot",
            landed.display_name()
        );
    }
}

/// Native anchors sit on the platform callsite itself, because the profile
/// has no declared entity to hang a marker on. The reconciler must resolve
/// that line, and every landed native case must resolve under it — a case
/// whose sink marker drifted off the callsite would silently stop matching
/// any finding and read as coverage.
#[test]
fn native_sink_anchors_resolve_to_the_platform_callsite() {
    // One assertion per landed language, against that language's own
    // platform command API: the marker must sit on the line that calls it.
    for (language, callsite) in [
        (ModelingLanguage::Javascript, "execSync("),
        (ModelingLanguage::Java, "Runtime.getRuntime().exec("),
        (ModelingLanguage::Python, "os.system("),
    ] {
        let population = select_native_cases(language).unwrap();
        assert_eq!(population.len(), NATIVE_CASE_COUNT);
        for (path, case) in &population {
            let locations = native_sink_anchor_locations(path, case)
                .unwrap_or_else(|error| panic!("{}: {error}", path.display()));
            assert_eq!(locations.len(), 1, "{}", path.display());
            let location = &locations[0];
            assert_eq!(
                location.callsite_lines,
                BTreeSet::from([location.marker_line])
            );
            let body = fs::read_to_string(path.parent().unwrap().join(&location.file)).unwrap();
            let line = body
                .lines()
                .nth(location.marker_line as usize - 1)
                .expect("marker line is inside the fixture");
            assert!(
                line.contains(callsite),
                "{}: the sink marker must sit on the real platform callsite, found {line:?}",
                path.display()
            );
        }
    }
}

/// A shipped suite answers many questions at once, so a finding that lands
/// away from this assertion's sink is a different query's answer, retained
/// as a diagnostic and never counted as a flow. Ambiguity is still
/// `inconclusive`, and a finding on the anchor is still `reached`. One
/// reconciler serves every language, so the shape is asserted on both
/// landed rows.
#[test]
fn a_shipped_suite_finding_away_from_the_native_anchor_is_not_a_flow() {
    for (language, fixture) in [
        (ModelingLanguage::Javascript, "probe.js"),
        (ModelingLanguage::Java, "NativeSourceSinkPositive.java"),
    ] {
        let wanted = format!("dfb-taint-{}-native-source-sink-positive", language.key());
        let (path, case) = select_native_cases(language)
            .unwrap()
            .into_iter()
            .find(|(_, case)| case["id"] == wanted.as_str())
            .expect("the source-sink positive is in the population");
        let sink_line = case["sink_anchors"][0]["line_hint"].as_u64().unwrap();
        let finding = |line: u64, message: &str| {
            json!({
                "runs": [{"results": [{
                    "message": {"text": message},
                    "locations": [{"physicalLocation": {
                        "artifactLocation": {"uri": fixture},
                        "region": {"startLine": line}
                    }}]
                }]}]
            })
        };

        let (outcome, diagnostics) =
            native_sarif_outcome(&path, &case, &finding(sink_line, "command injection"));
        assert_eq!(outcome, "reached");
        assert!(diagnostics.iter().any(|d| d.contains("command injection")));

        let (outcome, diagnostics) =
            native_sarif_outcome(&path, &case, &finding(1, "weak hashing somewhere else"));
        assert_eq!(outcome, "not-reached");
        assert!(
            diagnostics
                .iter()
                .any(|d| d.contains("landed away from this case's platform sink anchor")),
            "{diagnostics:?}"
        );

        let (outcome, _) = native_sarif_outcome(
            &path,
            &case,
            &json!({"runs": [{"results": [{"message": {"text": "no location"}}]}]}),
        );
        assert_eq!(outcome, "inconclusive");

        let (outcome, diagnostics) =
            native_sarif_outcome(&path, &case, &json!({"runs": [{"results": []}]}));
        assert_eq!(outcome, "not-reached");
        assert!(diagnostics.is_empty());
    }
}

/// The native outcome vocabulary, applied literally from
/// docs/native-profile.md#outcome-honesty: a coverage miss by an activated
/// model set is a plain `not-reached`, never `inconclusive`, because
/// `inconclusive` would remove the cell from the vendor's denominator. Only
/// evidence this runner genuinely cannot read is incomplete.
///
/// Both execution arms tally through this one function, so the ruling is
/// pinned once for CodeQL and Semgrep alike rather than per adapter.
#[test]
fn a_native_coverage_miss_is_not_reached_rather_than_inconclusive() {
    let outcome = |matches: &[SarifAnchorMatch]| {
        native_anchor_tally_outcome(matches.iter().copied(), "SARIF").0
    };
    // (a) No finding anywhere.
    assert_eq!(outcome(&[]), "not-reached");
    // (b) Findings, but only away from the anchor. This is the cell the
    //     document calls "a coverage miss by an activated model set", and
    //     it is a false negative on a positive cell, not an absence of
    //     evidence.
    assert_eq!(outcome(&[SarifAnchorMatch::Unmatched]), "not-reached");
    assert_eq!(
        outcome(&[SarifAnchorMatch::Unmatched, SarifAnchorMatch::Unmatched]),
        "not-reached"
    );
    // A finding on the anchored callsite is `reached` on the cell it lands
    // in, negatives included: polarity is about the flow.
    assert_eq!(outcome(&[SarifAnchorMatch::Matched]), "reached");
    assert_eq!(
        outcome(&[SarifAnchorMatch::Matched, SarifAnchorMatch::Unmatched]),
        "reached"
    );
    // (c) Only unreadable or genuinely ambiguous evidence is incomplete.
    assert_eq!(outcome(&[SarifAnchorMatch::Ambiguous]), "inconclusive");
    assert_eq!(
        outcome(&[SarifAnchorMatch::Matched, SarifAnchorMatch::Ambiguous]),
        "inconclusive"
    );
}

/// The same ruling, reached through the Semgrep arm's own evidence shape:
/// a scan that completed and found nothing at the anchor is `not-reached`,
/// and a finding with no readable location is the one incomplete case.
#[test]
fn the_semgrep_native_arm_reaches_the_same_outcome_rule() {
    let case_path = Path::new("cases/taint/python/native-source-sink-positive/case.json");
    let case: Value = serde_json::from_str(&fs::read_to_string(case_path).unwrap()).unwrap();
    let locations = native_sink_anchor_locations(case_path, &case).unwrap();
    assert_eq!(locations.len(), 1);
    let anchor = &locations[0];
    assert_eq!(anchor.file, "env_command.py");
    let body = fs::read_to_string(case_path.parent().unwrap().join(&anchor.file)).unwrap();
    assert!(
        body.lines()
            .nth(anchor.marker_line as usize - 1)
            .expect("the anchored line")
            .contains("os.system("),
    );

    let scan = |results: Value| {
        native_semgrep_outcome(
            case_path,
            &case,
            &json!({
                "results": results,
                "errors": [],
                "paths": {"scanned": ["env_command.py"]}
            }),
        )
        .0
    };
    let finding = |path: &str, line: u64| json!({"path": path, "start": {"line": line}});

    assert_eq!(scan(json!([])), "not-reached");
    assert_eq!(
        scan(json!([finding("env_command.py", anchor.marker_line)])),
        "reached"
    );
    assert_eq!(
        scan(json!([finding("env_command.py", anchor.marker_line - 1)])),
        "not-reached"
    );
    assert_eq!(
        scan(json!([finding("other.py", anchor.marker_line)])),
        "not-reached"
    );
    assert_eq!(
        scan(json!([json!({"path": "env_command.py"})])),
        "inconclusive"
    );
}

/// The published figure is the range the repeats span, and nothing else:
/// not a mean, not a chosen repeat, and not a figure conditioned on the
/// repeats agreeing.
#[test]
fn invocation_overhead_publishes_the_range_over_every_repeat() {
    let run = |wall_ms: u64| OverheadRun {
        phases: vec![("total".into(), wall_ms)],
        wall_ms,
        load_before: None,
    };
    let range = overhead_range(&[run(4200), run(3900), run(4600)]).unwrap();
    assert_eq!(range.low_ms, 3900);
    assert_eq!(range.high_ms, 4600);

    // Order cannot change the figure: a range has no notion of a first or
    // a last repeat, which is the point of publishing one.
    assert_eq!(
        overhead_range(&[run(4600), run(3900), run(4200)]).unwrap(),
        range
    );

    // A wide disagreement widens the range; it never withholds it. The
    // width is the precision, and stating it is the publication.
    let wide = overhead_range(&[run(1000), run(9000), run(2000)]).unwrap();
    assert_eq!((wide.low_ms, wide.high_ms), (1000, 9000));

    // Repeats that agree exactly collapse to a point range rather than to
    // a special case.
    let tight = overhead_range(&[run(500), run(500), run(500)]).unwrap();
    assert_eq!((tight.low_ms, tight.high_ms), (500, 500));
}

/// No agreement threshold exists anywhere in the overhead estimator.
///
/// The range convention replaced a withhold-on-disagreement rule, and a
/// tolerance constant creeping back would quietly restore it — so the
/// absence is asserted against the source itself rather than trusted to
/// review. The same property is asserted for the warm-marginal figures.
#[test]
fn no_agreement_threshold_constant_governs_the_overhead_estimate() {
    let source = include_str!("main.rs");
    // The needles are assembled rather than written out, so this test's
    // own text cannot satisfy the search it performs.
    for forbidden in [
        format!("OVERHEAD_{}", "TOLERANCE"),
        format!("OVERHEAD_{}", "AGREEMENT"),
        format!("fn overhead_{}", "stability"),
    ] {
        assert!(
            !source.contains(&forbidden),
            "the overhead estimate must not be gated on its repeats agreeing, \
                 but the source defines {forbidden}"
        );
    }
    // And the repeat count is a source constant, not a per-run argument.
    assert!(OVERHEAD_REPEATS >= 2);
}

/// The estimator's fixture must be a *no-flow* fixture, or the number it
/// produces is not an overhead estimate but a small analysis.
///
/// Each template is checked for the property that makes it one: both
/// endpoints are declared with the benchmark's own names — so the
/// committed policy, rule and query resolve exactly as they do on a real
/// case — and the sink is called on a literal, never on the source's
/// result.
#[test]
fn trivial_fixtures_declare_both_endpoints_and_carry_no_flow() {
    for language in [
        OverheadLanguage::C,
        OverheadLanguage::Java,
        OverheadLanguage::Kotlin,
        OverheadLanguage::Php,
        OverheadLanguage::Python,
        OverheadLanguage::Ruby,
    ] {
        let (name, text) = trivial_fixture(language);
        assert!(
            !name.is_empty() && text.contains("dfb_source") && text.contains("dfb_sink"),
            "{}: both endpoints must be declared",
            language.as_str()
        );
        assert!(
            text.contains("// DFB-SOURCE:") || text.contains("# DFB-SOURCE:"),
            "{}: the source marker must be present",
            language.as_str()
        );
        assert!(
            text.contains("// DFB-SINK:") || text.contains("# DFB-SINK:"),
            "{}: the sink marker must be present",
            language.as_str()
        );
        // No line may pass the source's value into the sink, directly or
        // through a name: the sink's argument is a literal on every one.
        for line in text.lines() {
            let call = line.trim();
            if !call.starts_with("dfb_sink(") {
                continue;
            }
            assert!(
                call.starts_with("dfb_sink(0)") || call.starts_with("dfb_sink(\"clean\")"),
                "{}: the sink must be called on a literal, found {call:?}",
                language.as_str()
            );
        }
        // And the fixture is never a case: nothing about it may claim a
        // template, a polarity or a score tier.
        for forbidden in ["dfb-template-", "score_tier", "expected_outcome"] {
            assert!(
                !text.contains(forbidden),
                "{}: a trivial fixture is not a case and must not carry {forbidden}",
                language.as_str()
            );
        }
    }
}
