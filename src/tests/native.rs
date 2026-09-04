//! Regression tests for `crate::native`.

use crate::adapters::bifrost::{
    BIFROST_JAVA_POLICY, BIFROST_NATIVE_DEFAULT_PACKS_FLAG, smoke_population_case,
};
use crate::adapters::codeql::{CODEQL_NATIVE_QUERY_PACKS, CODEQL_NATIVE_SUITE_KIND};
use crate::adapters::flowdroid::{
    FLOWDROID_MODELING_SUMMARIES_DIR, FLOWDROID_NATIVE_CATALOG_ARGUMENT,
};
use crate::adapters::joern::JOERN_MODELING_SCRIPT;
use crate::adapters::pysa::{PYSA_NATIVE_SINK_MODEL, PYSA_NATIVE_SUITE_RELATIVE};
use crate::adapters::semgrep::SEMGREP_NATIVE_UPSTREAM;
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::evidence::SarifAnchorMatch;
use crate::modeling::{
    MODELING_MODEL_PROFILE, MODELING_TEMPLATE_IDS, MODELING_TEMPLATE_PREFIX, ModelingCategory,
    modeling_case, modeling_supported_templates, validate_modeling_cases,
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
use crate::tests::modeling::modeling_population;
use crate::tests::support::{WITNESSED_IDENTITY, unique_test_dir};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::PathBuf};

/// FlowDroid's Amendment-A19 native row: the activation contract is live —
/// the shipped catalog and default summary wrapper are the product — but
/// the catalog binds no identity any native template uses, so all six
/// cells are declined from shipped-model text, and the activation shape
/// names the jar-internal catalog rather than any repository path.
#[test]
pub(crate) fn flowdroid_native_partition_declines_all_six_on_catalog_evidence() {
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

/// Amendment A17's activation shape: the shipped suite with `--no-verify`,
/// no benchmark-authored model in the arguments, and the retained-evidence
/// guard keyed to the shipped `os.system` sink model.
#[test]
pub(crate) fn pysa_native_activation_is_the_shipped_suite() {
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

// -----------------------------------------------------------------------
// The tool-native model profile.
// -----------------------------------------------------------------------

/// One synthetic tool-native case, carrying every field the native
/// validators read.
pub(crate) fn native_case_value(template: &str, polarity: &str, language: &str) -> Value {
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
pub(crate) fn native_population(language: &str) -> Vec<(PathBuf, Value)> {
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
pub(crate) fn native_templates_are_the_preregistered_six() {
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
pub(crate) fn every_native_template_maps_to_one_category() {
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
pub(crate) fn the_native_partition_decides_every_tool_and_template() {
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
pub(crate) fn native_partition_scored_counts_match_the_preregistration() {
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
pub(crate) fn native_partition_amendments_name_preregistered_templates() {
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
pub(crate) fn the_native_partition_is_tag_proof() {
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
pub(crate) fn native_unsupported_reasons_are_retained_and_attributed() {
    let reason = native_unsupported_reason(
        ModelingTool::Bifrost,
        ModelingLanguage::Java,
        "dfb-template-native-sanitizer",
        WITNESSED_IDENTITY,
    )
    .unwrap()
    .expect("declined");
    // Amendment A10 replaced the withdrawn README citation; Amendment A32
    // then re-grounded the same decline on the catalog v0.10.9 actually ships.
    assert!(reason.contains("restated by Amendment A10"));
    assert!(reason.contains("re-grounded by Amendment A32"));
    assert!(reason.contains("declares no sanitizer"));
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
pub(crate) fn a_declined_native_cell_retains_evidence_without_invoking_the_tool() {
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
pub(crate) fn an_absent_native_population_validates_trivially() {
    validate_native_population(&[], "Java tool-native population").unwrap();
    validate_native_cases(&[]).unwrap();
    validate_profile_disjoint_populations(&[]).unwrap();
}

/// A whole balanced population of twelve validates, and the same population
/// passes the corpus-wide checks.
#[test]
pub(crate) fn a_balanced_native_population_validates() {
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
pub(crate) fn an_incomplete_native_population_fails_validation() {
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
pub(crate) fn the_native_family_and_the_tool_native_profile_imply_each_other() {
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
pub(crate) fn native_cases_stay_on_the_modeling_tier() {
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
pub(crate) fn the_two_model_profiles_never_cross_select() {
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
pub(crate) fn a_native_case_is_never_smoke_selected() {
    let mut case = native_case_value("dfb-template-native-source-sink", "positive", "java");
    case["tool_model_references"] = json!({"bifrost": {"policy": BIFROST_JAVA_POLICY}});
    assert!(!smoke_population_case(&case));
}

/// Report and raw-evidence paths follow the profile's convention, and are
/// disjoint from the benchmark-controlled matrix's.
#[test]
pub(crate) fn native_report_and_raw_paths_follow_the_convention() {
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
pub(crate) fn the_native_activation_shapes_are_pinned() {
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
    assert_eq!(bifrost.arguments, vec![BIFROST_NATIVE_DEFAULT_PACKS_FLAG]);
    assert!(
        !bifrost.arguments.iter().any(|a| matches!(
            a.as_str(),
            "--policy-file" | "--policy-pack" | "--policy-category" | "--policy-id"
        )),
        "a native Bifrost run may not name a policy file or narrow the shipped catalog"
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
pub(crate) fn the_no_benchmark_models_gate_refuses_a_spliced_model_artifact() {
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
pub(crate) fn the_activation_configuration_binds_the_report_hash() {
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
pub(crate) fn every_native_population_is_the_balanced_twelve() {
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
pub(crate) fn the_codeql_native_pins_are_query_packs() {
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

/// Native anchors sit on the platform callsite itself, because the profile
/// has no declared entity to hang a marker on. The reconciler must resolve
/// that line, and every landed native case must resolve under it — a case
/// whose sink marker drifted off the callsite would silently stop matching
/// any finding and read as coverage.
#[test]
pub(crate) fn native_sink_anchors_resolve_to_the_platform_callsite() {
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
pub(crate) fn a_shipped_suite_finding_away_from_the_native_anchor_is_not_a_flow() {
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
pub(crate) fn a_native_coverage_miss_is_not_reached_rather_than_inconclusive() {
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
