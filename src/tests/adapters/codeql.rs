//! Regression tests for the codeql adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::KernelPopulation;
use crate::adapters::bifrost::BIFROST_KOTLIN_POLICY;
use crate::adapters::codeql::{
    CFamilyKernel, CODEQL_C_ENDPOINT_PROBE, CODEQL_C_QUERY, CODEQL_C_RAW_DIR, CODEQL_C_REPORT,
    CODEQL_CPP_ENDPOINT_PROBE, CODEQL_CPP_QUERY, CODEQL_CPP_RAW_DIR, CODEQL_CPP_REPORT,
    CODEQL_CSHARP_ENDPOINT_PROBE, CODEQL_CSHARP_QUERY, CODEQL_CSHARP_RAW_DIR, CODEQL_CSHARP_REPORT,
    CODEQL_ENDPOINT_PROBE_RULE_SUFFIX, CODEQL_GO_ENDPOINT_PROBE, CODEQL_GO_QUERY,
    CODEQL_GO_RAW_DIR, CODEQL_GO_REPORT, CODEQL_JAVA_ENDPOINT_PROBE,
    CODEQL_JAVASCRIPT_ENDPOINT_PROBE, CODEQL_JAVASCRIPT_QUERY, CODEQL_JAVASCRIPT_RAW_DIR,
    CODEQL_JAVASCRIPT_REPORT, CODEQL_KOTLIN_ENDPOINT_PROBE, CODEQL_KOTLIN_QUERY,
    CODEQL_KOTLIN_RAW_DIR, CODEQL_KOTLIN_REPORT, CODEQL_PYTHON_ENDPOINT_PROBE, CODEQL_PYTHON_QUERY,
    CODEQL_RUBY_ENDPOINT_PROBE, CODEQL_RUBY_QUERY, CODEQL_RUBY_RAW_DIR, CODEQL_RUBY_REPORT,
    CODEQL_RUST_ENDPOINT_PROBE, CODEQL_RUST_QUERY, CODEQL_RUST_RAW_DIR, CODEQL_RUST_REPORT,
    CODEQL_TYPESCRIPT_ENDPOINT_PROBE, CODEQL_TYPESCRIPT_QUERY, CODEQL_TYPESCRIPT_RAW_DIR,
    CODEQL_TYPESCRIPT_REPORT, CodeqlEndpointObservation, CodeqlLanguage, EcmaKernel,
    codeql_c_family_cases, codeql_csharp_cases, codeql_database_create_args,
    codeql_endpoint_probe_result, codeql_go_cases, codeql_kotlin_cases, codeql_missing_sarif_error,
    codeql_ruby_cases, codeql_rust_cases, ecma_sarif_outcome, normalize_anchored_codeql_sarif,
    select_codeql_ecma_cases, selected_codeql_java_case, selected_codeql_python_case,
    split_codeql_endpoint_probe, unobserved_codeql_endpoint_outcome,
    validate_codeql_python_population, validate_rust_kernel_population, write_rust_cargo_manifest,
};
use crate::cases::{case_paths, csharp_core_case, go_core_case, validate_kernel_population_with};
use crate::evidence::{AnchorDialect, sarif_anchor_outcome, sarif_messages, sarif_result_count};
use crate::templates::{
    KERNEL_CASE_COUNT, KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH, KERNEL_TEMPLATE_IDS,
    KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH, expected_core_case_count, expected_core_templates,
};
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::{collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf};

#[test]
pub(crate) fn kotlin_codeql_population_is_the_expanded_balanced_core() {
    let expected = expected_core_templates("kotlin");
    let selected = codeql_kotlin_cases().unwrap();
    assert_eq!(selected.len(), 2 * expected.len());
    // Kotlin's challenge row is rolled out, so the population is the
    // expanded 30-template / 60-assertion core, not the classic 32.
    assert_eq!(selected.len(), 60);
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
pub(crate) fn kotlin_codeql_databases_trace_a_real_kotlin_compile() {
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
pub(crate) fn kotlin_codeql_report_paths_are_dedicated() {
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
pub(crate) fn ecma_codeql_selection_refuses_the_other_kernel_query() {
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
        if EcmaKernel::TypeScript.selects(&case) {
            assert!(query.is_none_or(|query| query == EcmaKernel::TypeScript.query()));
        }
        if EcmaKernel::JavaScript.selects(&case) {
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

pub(crate) fn probe_row(role: &str) -> Value {
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
pub(crate) fn codeql_endpoint_probe_rows_are_split_from_kernel_findings() {
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
pub(crate) fn a_merged_codeql_endpoint_probe_result_counts_every_observed_role() {
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
pub(crate) fn an_unobserved_codeql_endpoint_prevents_clean_negative_interpretation() {
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
pub(crate) fn every_codeql_kernel_evaluates_an_endpoint_probe_beside_its_query() {
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
pub(crate) fn ecma_core_selections_are_exactly_32_balanced_assertions() {
    for kernel in [EcmaKernel::JavaScript, EcmaKernel::TypeScript] {
        let mut selected = Vec::new();
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            if kernel.selects(&case) {
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
pub(crate) fn java_javascript_and_typescript_codeql_selectors_are_language_disjoint() {
    let mut java = 0;
    let mut javascript = 0;
    let mut typescript = 0;
    for path in case_paths() {
        let case: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        if selected_codeql_java_case(&case) {
            java += 1;
            assert_eq!(case["language"], "java");
        }
        if EcmaKernel::JavaScript.selects(&case) {
            javascript += 1;
            assert_eq!(case["language"], "javascript");
            assert!(!EcmaKernel::TypeScript.selects(&case));
        }
        if EcmaKernel::TypeScript.selects(&case) {
            typescript += 1;
            assert_eq!(case["language"], "typescript");
            assert!(!EcmaKernel::JavaScript.selects(&case));
        }
    }
    assert_eq!(java, expected_core_case_count("java"));
    assert_eq!(javascript, expected_core_case_count("javascript"));
    assert_eq!(typescript, expected_core_case_count("typescript"));
}

/// The JavaScript kernel selects `.js` fixtures and the TypeScript kernel
/// `.ts` fixtures; neither population may contain the other's extension.
#[test]
pub(crate) fn ecma_kernel_fixtures_carry_their_own_extension() {
    for (kernel, extension, other) in [
        (EcmaKernel::JavaScript, "js", "ts"),
        (EcmaKernel::TypeScript, "ts", "js"),
    ] {
        for path in case_paths() {
            let case: Value = serde_json::from_str(&fs::read_to_string(&path).unwrap()).unwrap();
            if !kernel.selects(&case) {
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
pub(crate) fn csharp_core_selection_is_the_expanded_balanced_population() {
    let expected_templates = expected_core_templates("csharp");
    let selected = codeql_csharp_cases().unwrap();
    assert_eq!(selected.len(), expected_core_case_count("csharp"));
    // C#'s challenge row is rolled out, so the population is the expanded
    // 30 templates / 60 assertions, not the classic 32.
    assert_eq!(selected.len(), 60);
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
    assert_eq!(templates.len(), 30);
    assert!(
        templates
            .values()
            .all(|(positive, negative)| *positive == 1 && *negative == 1)
    );
}

#[test]
pub(crate) fn csharp_core_selection_is_language_and_track_scoped() {
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

/// C and C++ are two populations with two denominators, both now rolled
/// out: C's core is the fifteen applicable classic templates plus its nine
/// applicable challenge templates — 24 templates and 48 assertions — and
/// the C++ core is all sixteen classic templates plus its twelve
/// applicable challenge templates — 29 templates and 58 assertions. The C
/// `language-extension` cases ride along in the C slice without changing
/// its core denominator.
#[test]
pub(crate) fn c_and_cpp_core_populations_keep_their_own_denominators() {
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
    assert_eq!(core(&cpp), 58);
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

/// A C population that lost an applicable template, or gained the
/// inapplicable one, is not a C kernel.
#[test]
pub(crate) fn c_kernel_population_rejects_a_foreign_or_short_template_set() {
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

/// The two C-family kernels share the `cpp` extractor and one pack, so
/// their reports, raw-evidence roots, and queries must stay distinct.
#[test]
pub(crate) fn c_family_codeql_report_paths_are_dedicated() {
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

#[test]
pub(crate) fn csharp_sarif_mapping_requires_the_sink_file_and_callsite() {
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
pub(crate) fn go_core_selection_is_the_expanded_balanced_population() {
    let expected_templates = expected_core_templates("go");
    let selected = codeql_go_cases().unwrap();
    assert_eq!(selected.len(), expected_core_case_count("go"));
    // Go's challenge row is rolled out, so the population is the expanded
    // 30 templates / 60 assertions, not the classic 32.
    assert_eq!(selected.len(), 60);
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
    assert_eq!(templates.len(), 30);
    assert!(
        templates
            .values()
            .all(|(positive, negative)| *positive == 1 && *negative == 1)
    );
}

#[test]
pub(crate) fn go_core_selection_is_language_and_track_scoped() {
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
pub(crate) fn go_sarif_mapping_requires_the_sink_file_and_callsite() {
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

/// The Rust kernel scores its expanded core: 27 templates and 54
/// assertions now that the challenge row is flipped (15 classic plus 12
/// challenge cells). The excluded exception-catch and reflective-invocation
/// cells stay excluded, and the `Result`/`?` extension pair rides in the
/// same slice without changing the denominator.
#[test]
pub(crate) fn rust_core_selection_is_the_expanded_balanced_population() {
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

/// A Rust population that reintroduced the excluded template, or that
/// smuggled a non-kernel tier into the slice, is not a Rust kernel.
#[test]
pub(crate) fn rust_kernel_population_rejects_the_excluded_or_a_foreign_template() {
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
pub(crate) fn rust_codeql_report_paths_are_dedicated() {
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
pub(crate) fn rust_codeql_databases_carry_a_generated_cargo_manifest() {
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

#[test]
pub(crate) fn ecma_core_selection_is_language_and_track_scoped() {
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
        assert!(kernel.selects(&selected));
        for other_language in others {
            let mut other = selected.clone();
            other["language"] = json!(other_language);
            assert!(!kernel.selects(&other));
        }
        let mut other = selected.clone();
        other["track"] = json!("value-flow");
        assert!(!kernel.selects(&other));
        other["track"] = json!("taint");
        other["score_tier"] = json!("calibration");
        assert!(!kernel.selects(&other));
    }
}

#[test]
pub(crate) fn javascript_sarif_mapping_requires_the_sink_file_and_line() {
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
pub(crate) fn javascript_sarif_ambiguous_locations_stay_inconclusive() {
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
pub(crate) fn javascript_codeql_report_paths_are_dedicated() {
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
pub(crate) fn python_codeql_population_requires_the_expanded_core() {
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
pub(crate) fn python_codeql_selection_requires_canonical_query() {
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
pub(crate) fn codeql_database_creation_uses_language_specific_build_modes() {
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
pub(crate) fn codeql_missing_sarif_keeps_runner_error_evidence() {
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
pub(crate) fn python_codeql_sarif_requires_a_canonical_sink_anchor() {
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

/// The Ruby CodeQL slice owns its own pack, query, report, and evidence
/// root, and is never pooled with another language's population.
#[test]
pub(crate) fn ruby_codeql_report_paths_are_dedicated() {
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
    // 30 templates / 60 assertions.
    assert_eq!(selected.len(), expected_core_case_count("ruby"));
    assert_eq!(selected.len(), 60);
    for (_, case) in &selected {
        assert_eq!(case["language"], "ruby");
        assert_eq!(case["score_tier"], "core");
    }
}
