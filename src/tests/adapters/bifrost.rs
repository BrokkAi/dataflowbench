//! Regression tests for the bifrost adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::bifrost::{
    BIFROST_DIRECT_POLICY, BIFROST_DIRECT_POSITIVE_POLICY, BIFROST_EXPLICIT_NEGATIVE_POLICY,
    BIFROST_JAVA_POLICY, BIFROST_JAVASCRIPT_POLICY, BIFROST_KOTLIN_POLICY,
    BIFROST_MODELING_CALL_MODELING, BIFROST_SCALA_POLICY, BifrostRun, bifrost_anchor_dialect,
    bifrost_policy_for, normalize_bifrost, require_bifrost_modeling_load_bearing,
    selected_bifrost_case,
};
use crate::adapters::codeql::rust_kernel_case;
use crate::cases::{case_paths, ruby_core_case, scala_core_case, validate_kernel_population_with};
use crate::evidence::AnchorDialect;
use crate::freeze::raw_special_outcome;
use crate::templates::{
    CHALLENGE_TEMPLATE_IDS, KERNEL_CASE_COUNT, KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH,
    KERNEL_TEMPLATE_IDS, expected_core_case_count, expected_core_templates,
};
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::{fs, path::Path, path::PathBuf};

/// The Bifrost mirror of the per-adapter sink-anchor tests: a finding on
/// the anchored sink's callsite is `reached`; a finding anywhere else in
/// the raw document, or one without a usable location, is `inconclusive`
/// on the same terms as CodeQL, Joern, and Semgrep evidence.
#[test]
pub(crate) fn bifrost_findings_require_the_sink_file_and_callsite() {
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
pub(crate) fn bifrost_anchor_dialects_cover_every_kernel_language() {
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
pub(crate) fn incomplete_or_unexpected_bifrost_status_never_becomes_clean_negative() {
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
pub(crate) fn empty_bifrost_endpoint_selection_is_inconclusive() {
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
pub(crate) fn python_kernel_selection_is_separate_from_direct_and_java() {
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
pub(crate) fn kotlin_kernel_selection_is_separate_from_java_and_every_other_language() {
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
pub(crate) fn scala_kernel_selection_is_separate_from_every_other_language() {
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
pub(crate) fn scala_bifrost_population_is_the_expanded_balanced_core() {
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
pub(crate) fn kotlin_kernel_population_rejects_an_unbalanced_or_foreign_template_set() {
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
pub(crate) fn typescript_bifrost_kernel_selection_excludes_other_languages() {
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
pub(crate) fn bifrost_csharp_kernel_selects_only_csharp_core_cases() {
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

#[test]
pub(crate) fn bifrost_c_and_cpp_kernels_select_disjoint_populations() {
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

#[test]
pub(crate) fn bifrost_go_kernel_selects_only_go_core_cases() {
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

/// PHP has no CodeQL support in the pinned CLI, so Bifrost and Joern are its
/// two analyzers. The Bifrost slice still may not overlap any other
/// language's kernel population.
#[test]
pub(crate) fn bifrost_php_kernel_selects_only_php_core_cases() {
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
pub(crate) fn bifrost_rust_kernel_selects_only_rust_cases() {
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

/// The Ruby kernel is its own Bifrost population. The tranche is gated on
/// Bifrost's Ruby indexing, so whatever this run produces is capability
/// evidence — but the selection itself must still be exactly the Ruby
/// expanded core assertions and nothing else.
#[test]
pub(crate) fn bifrost_ruby_kernel_selects_only_ruby_core_cases() {
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

#[test]
pub(crate) fn representative_bifrost_incomplete_evidence_stays_inconclusive() {
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
pub(crate) fn bifrost_runner_failures_are_not_clean_negatives() {
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

/// The smoke population must stay pinned to its frozen 118-case contract:
/// dedicated language-kernel policies never leak into it.
#[test]
pub(crate) fn smoke_selection_is_pinned_to_the_frozen_population() {
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
pub(crate) fn smoke_refuses_a_challenge_case_that_names_a_smoke_policy() {
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

/// The dedicated Java and JavaScript Bifrost kernels own their language's
/// whole core population. Java consumes each case's validated declared
/// policy; JavaScript pins its language-qualified policy throughout.
#[test]
pub(crate) fn java_and_javascript_bifrost_kernels_own_their_language_population() {
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
pub(crate) fn java_kernel_preserves_the_direct_pairs_compatible_policies() {
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

/// A failed Bifrost run is an execution error even under exit status 2;
/// this must match `raw_special_outcome` so a freeze can bind the report.
#[test]
pub(crate) fn failed_bifrost_completion_normalizes_to_runner_error_despite_status_2() {
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

/// A Bifrost modeling policy must make the model load-bearing: the kernel
/// policies' optimistic unmodeled-call default would decide a category P
/// or O cell without the declaration ever being read.
#[test]
pub(crate) fn a_bifrost_modeling_policy_must_require_the_model() {
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
