//! Regression tests for `crate::modeling`.

use crate::adapters::bifrost::{
    BIFROST_JAVA_POLICY, BIFROST_MODELING_CALL_MODELING, require_bifrost_modeling_load_bearing,
    smoke_population_case,
};
use crate::adapters::codeql::modeling_codeql_language;
use crate::adapters::flowdroid::{
    FLOWDROID_MODELING_SUMMARIES_DIR, FLOWDROID_MODELING_SUMMARY_FILES,
    require_flowdroid_modeling_declarations,
};
use crate::adapters::joern::{
    JOERN_MODELING_SCRIPT, JoernEndpointRule, joern_flow_outcome, modeling_joern_frontend,
    modeling_joern_source_kind,
};
use crate::adapters::opentaint::OPENTAINT_MODEL_RULE_ID;
use crate::adapters::semgrep::{
    SEMGREP_MODELING_ASSUME_SAFE_OPTION, require_semgrep_modeling_load_bearing,
};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::evidence::AnchorDialect;
use crate::modeling::{
    MODELING_CASE_COUNT, MODELING_MODEL_PROFILE, MODELING_PARTITION, MODELING_TEMPLATE_IDS,
    MODELING_TEMPLATE_PREFIX, ModelingCategory, modeling_anchor_dialect, modeling_category,
    modeling_partition_outcome, modeling_partition_reason, modeling_supported_templates,
    modeling_unsupported_reason, select_modeling_cases, validate_modeling_cases,
    validate_modeling_population,
};
use crate::native::{native_activation, native_supported_templates};
use crate::tests::support::{WITNESSED_IDENTITY, unique_test_dir};
use serde_json::{Value, json};
use std::{collections::BTreeSet, fs, path::Path, path::PathBuf};

// -----------------------------------------------------------------------
/// The kernels' endpoint rule, used by every Joern kernel normalization test.
pub(crate) const KERNEL_ENDPOINTS: JoernEndpointRule = JoernEndpointRule::BothMustBeObserved;

// The benchmark-controlled taint-modeling matrix.
// -----------------------------------------------------------------------

/// One synthetic modeling case, carrying every field the modeling
/// validators read.
pub(crate) fn modeling_case_value(template: &str, polarity: &str, language: &str) -> Value {
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
pub(crate) fn modeling_population(language: &str) -> Vec<(PathBuf, Value)> {
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
pub(crate) fn modeling_templates_are_the_preregistered_twelve() {
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
pub(crate) fn every_modeling_template_belongs_to_exactly_one_category() {
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
pub(crate) fn the_modeling_partition_decides_every_tool_and_template() {
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
pub(crate) fn modeling_partition_scored_counts_match_the_preregistration() {
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
pub(crate) fn flowdroid_modeling_partition_matches_amendment_a18() {
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

/// OpenTaint's modeling row (Amendment A22), pinned exactly: categories S,
/// P, and Z are scored and O, E, and B are declined — a partition decided
/// by executing the pinned analyzer over the committed Java fixtures with
/// probe declarations, before any scored run, and retained under
/// reports/raw/opentaint-modeling-surface-probe/.
#[test]
pub(crate) fn opentaint_modeling_partition_scores_sources_propagators_and_sanitizers() {
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
pub(crate) fn opentaint_modeling_is_java_only() {
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
pub(crate) fn pysa_modeling_partition_scores_five_categories_python_only() {
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
pub(crate) fn bifrost_modeling_partition_scores_sources_and_sanitizers() {
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
pub(crate) fn semgrep_modeling_partition_scores_sources_sanitizers_and_entry_points() {
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
pub(crate) fn infer_modeling_partition_scores_sources_one_propagator_and_sanitizers() {
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

/// The partition is keyed by template identity alone. No `feature_tags`
/// choice a fixture makes — and no observed result — can move a cell
/// between the scored and `unsupported` partitions.
#[test]
pub(crate) fn the_modeling_partition_is_tag_proof() {
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
pub(crate) fn modeling_unsupported_reasons_are_retained_and_attributed() {
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
pub(crate) fn a_declined_modeling_cell_retains_evidence_without_invoking_the_tool() {
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
pub(crate) fn an_absent_modeling_population_validates_trivially() {
    validate_modeling_population(&[], "Java modeling population").unwrap();
    validate_modeling_cases(&[]).unwrap();
}

/// A whole balanced population over the preregistered twelve validates.
#[test]
pub(crate) fn a_balanced_modeling_population_validates() {
    let cases = modeling_population("java");
    assert_eq!(cases.len(), MODELING_CASE_COUNT);
    validate_modeling_population(&cases, "Java modeling population").unwrap();
    validate_modeling_cases(&cases).unwrap();
}

/// A partial fixture landing fails the build rather than silently reducing
/// a denominator, and an unbalanced pair fails too.
#[test]
pub(crate) fn an_incomplete_modeling_population_fails_validation() {
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
pub(crate) fn the_modeling_tier_and_the_modeling_prefix_imply_each_other() {
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
pub(crate) fn modeling_cases_must_be_benchmark_controlled() {
    let mut cases = modeling_population("java");
    cases[0].1["model_profile"] = json!("tool-native");
    let error = validate_modeling_cases(&cases).unwrap_err().to_string();
    assert!(error.contains("benchmark-controlled"), "{error}");
}

/// A modeling case is never swept into the frozen 118-case Bifrost smoke
/// population, whatever policy it names.
#[test]
pub(crate) fn a_modeling_case_is_never_smoke_selected() {
    let mut case = modeling_case_value("dfb-template-model-declared-source", "positive", "java");
    case["tool_model_references"] = json!({"bifrost": {"policy": BIFROST_JAVA_POLICY}});
    assert!(!smoke_population_case(&case));
    case["tool_model_references"] =
        json!({"bifrost": {"unsupported_reason": "no external catalog"}});
    assert!(!smoke_population_case(&case));
}

/// Wave M1's rows: Python, JavaScript, and Java each carry a balanced
/// twenty-four over exactly the preregistered twelve. With Java's landing
/// the wave is complete, so every `ModelingLanguage` now has a denominator
/// — and a language with none would still be a fail-fast rather than a
/// zero.
#[test]
pub(crate) fn the_modeling_populations_are_the_balanced_twenty_four() {
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
pub(crate) fn the_modeling_ecma_dialect_accepts_a_member_qualified_callsite() {
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
pub(crate) fn the_joern_modeling_source_kind_is_template_keyed() {
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
pub(crate) fn the_modeling_artifacts_declare_only_their_scored_categories() {
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
pub(crate) fn a_modeling_run_without_a_population_fails_fast() {
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

/// The model-artifact, report, and raw-evidence paths the language pull
/// requests populate: one per tool per language for the wave-M1 four,
/// plus the amendment-added adapters' single-language artifacts — their
/// other combinations have no denominator at all.
#[test]
pub(crate) fn modeling_artifact_and_report_paths_follow_the_convention() {
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
pub(crate) fn a_modeling_negative_may_legitimately_contain_no_declared_endpoint() {
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

/// The committed JavaScript artifacts pass the gates the runner applies
/// before it will touch an analyzer, so a load-bearing regression in one
/// of them fails the test suite rather than a run.
#[test]
pub(crate) fn the_javascript_modeling_artifacts_are_load_bearing() {
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
pub(crate) fn the_java_modeling_artifacts_are_load_bearing() {
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
pub(crate) fn java_modeling_reconciles_member_qualified_callsites() {
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
pub(crate) fn every_wave_m1_modeling_language_has_a_wired_execution_arm() {
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
