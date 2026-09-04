//! Regression tests for the pysa adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::pysa::{
    PYSA_PINNED_PYRE_VERSION, PYSA_PINNED_PYREFLY_VERSION, PYSA_RULE_CODE,
    PYSA_SINK_MODULE_PLACEHOLDER, PYSA_SOURCE_MODULE_PLACEHOLDER, PysaTools, parse_pysa_evidence,
    pysa_anchor_module, pysa_block_model_callables, pysa_configuration_paths,
    pysa_issue_anchor_match, pysa_model_activation_failure, pysa_model_template_path,
    pysa_modeling_block, pysa_taint_config_path, require_pysa_modeling_load_bearing,
    select_pysa_cases, witness_pysa_identity,
};
use crate::adapters::semgrep::{SEMGREP_SINK_PLACEHOLDER, SEMGREP_SOURCE_PLACEHOLDER};
use crate::adapters::{ModelingLanguage, ModelingTool, ToolIdentity};
use crate::evidence::{
    AnchorDialect, EvidenceAnchorMatch, SinkAnchorLocation, benchmark_endpoint_names,
};
use crate::modeling::{MODELING_TEMPLATE_IDS, modeling_supported_templates};
use crate::templates::expected_core_templates;
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::PathBuf};

/// The Pysa kernel is language-scoped, selects Python's whole expanded
/// core, resolves every case's endpoints and anchor modules, and loads
/// committed configuration whose shapes are load-bearing: the one
/// declared rule is what reconciliation keys on, and the model template
/// binds the sink's single `value` parameter — Pysa refuses a model whose
/// signature does not match the definition, so the uniform fixture shape
/// is pinned here before a drifted fixture could fail a population run.
#[test]
pub(crate) fn pysa_kernel_is_language_scoped_and_resolvable() {
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
pub(crate) fn pysa_identity_is_witnessed_against_the_pins() {
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
    let ToolIdentity {
        version,
        build_identity,
    } = witness_pysa_identity(&PysaTools {
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
pub(crate) fn pysa_evidence_guard_and_anchor_match_read_the_retained_document() {
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

/// The committed Pysa modeling artifact carries exactly the scored
/// templates' blocks — a block for a declined template would violate the
/// rule that an artifact never declares a category its partition marks
/// unsupported — and every block resolves the way the runner cuts it.
#[test]
pub(crate) fn pysa_modeling_artifact_blocks_cover_exactly_the_scored_templates() {
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
pub(crate) fn pysa_modeling_artifact_is_load_bearing() {
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
