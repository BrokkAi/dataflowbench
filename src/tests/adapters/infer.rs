//! Regression tests for the infer adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::KernelPopulation;
use crate::adapters::infer::{
    INFER_PINNED_VERSION, INFER_TAINT_RULE_ID, InferKernel, infer_config_paths,
    infer_taint_results_only, require_infer_modeling_load_bearing, select_infer_cases,
    witness_infer_identity,
};
use crate::adapters::semgrep::{SEMGREP_SINK_PLACEHOLDER, SEMGREP_SOURCE_PLACEHOLDER};
use crate::adapters::{ModelingLanguage, ModelingTool, ToolIdentity};
use crate::evidence::{benchmark_endpoint_names, sarif_result_count};
use crate::templates::expected_core_templates;
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::{fs, path::PathBuf};

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
pub(crate) fn infer_kernels_are_language_scoped_and_resolvable() {
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
pub(crate) fn infer_identity_is_witnessed_against_the_pin() {
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
    let ToolIdentity {
        version,
        build_identity,
    } = witness_infer_identity(&pinned).unwrap();
    assert_eq!(version, INFER_PINNED_VERSION);
    assert!(build_identity.contains("bin-sha256:"));
    fs::remove_dir_all(&root).unwrap();
}

/// Reconciliation reads only the benchmark taint policy's own rule id as
/// flow evidence. Pulse reports memory-safety issues under `--pulse-only`
/// too, and one of those landing on a sink callsite must never read as
/// `reached` — it is retained as a diagnostic instead.
#[test]
pub(crate) fn infer_reconciliation_reads_only_the_taint_policy() {
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

/// The three silent-failure shapes of the pinned Infer configuration
/// surface, each measured in the field, each refused by the gate: a
/// policy-less configuration asks no taint question, an unwired sanitizer
/// is silently inert, and the plain `procedure` matcher is a substring
/// match that cannot carry identity binding.
#[test]
pub(crate) fn an_infer_modeling_configuration_must_be_load_bearing() {
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
pub(crate) fn the_infer_modeling_artifact_is_load_bearing_and_scoped_to_its_partition() {
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
