//! Regression tests for the semgrep adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::KernelPopulation;
use crate::adapters::codeql::CODEQL_JAVASCRIPT_REPORT;
use crate::adapters::joern::{JOERN_JAVA_RAW_DIR, JOERN_JAVA_REPORT};
use crate::adapters::semgrep::{
    CHALLENGE_SEMGREP_PARTITION, SEMGREP_MODELING_ASSUME_SAFE_OPTION,
    SEMGREP_NATIVE_PROVENANCE_FILE, SEMGREP_NATIVE_UPSTREAM, SEMGREP_SINK_PLACEHOLDER,
    SEMGREP_SOURCE_PLACEHOLDER, SemgrepKernel, challenge_semgrep_exclusion, native_semgrep_outcome,
    require_semgrep_modeling_load_bearing, select_semgrep_cases, semgrep_capability_exclusion,
    semgrep_finding_outcome, semgrep_maturity_diagnostic, semgrep_native_rules_dir,
    semgrep_rule_paths,
};
use crate::adapters::{ModelingLanguage, ModelingTool};
use crate::evidence::{AnchorDialect, benchmark_endpoint_names};
use crate::freeze::raw_special_outcome;
use crate::native::native_sink_anchor_locations;
use crate::report::hash_paths;
use crate::templates::{
    CHALLENGE_TEMPLATE_IDS, KERNEL_CASE_COUNT, KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH,
    challenge_rolled_out,
};
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::{collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf};

pub(crate) const SEMGREP_KERNELS: [SemgrepKernel; 11] = [
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
pub(crate) fn semgrep_kernel_selections_are_language_disjoint_and_balanced() {
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
pub(crate) fn semgrep_language_maturity_is_recorded_and_never_scored_on() {
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
pub(crate) fn semgrep_new_kernels_resolve_every_scored_endpoint() {
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
pub(crate) fn semgrep_report_paths_and_rules_are_dedicated() {
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

/// The bounded profile is a declared-capability decision taken from the
/// case's own metadata *before* Semgrep is invoked. This test reads only
/// `case.json` files — no Semgrep binary is required or consulted — so an
/// out-of-profile case can never be run and then counted as a miss.
#[test]
pub(crate) fn semgrep_unsupported_partition_is_metadata_driven() {
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
pub(crate) fn semgrep_finding_evidence_requires_the_sink_callsite() {
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
pub(crate) fn semgrep_runner_failures_never_become_clean_negatives() {
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

/// The Semgrep CE partition for the challenge tier is preregistered by
/// template ID and decided from the pinned distribution's documentation. It
/// must cover all thirteen templates, and no fixture's `feature_tags` may
/// move a challenge case into the scored partition after the fact.
#[test]
pub(crate) fn the_challenge_semgrep_partition_is_preregistered_and_tag_proof() {
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

/// A Semgrep modeling rule must disable the engine's default pass-through,
/// which the preregistration verified against the pinned CE binary.
#[test]
pub(crate) fn a_semgrep_modeling_rule_must_assume_safe_functions() {
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

/// A Semgrep **modeling** rule lives beside the kernel rules but is not
/// part of the kernel configuration. Every published Semgrep kernel report
/// cites a hash over the eleven kernel rules, and committing a twelfth file
/// for a different population must not silently invalidate all eleven.
#[test]
pub(crate) fn a_semgrep_modeling_rule_is_outside_the_kernel_configuration_hash() {
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

/// The Semgrep vendoring convention: one directory per language under the
/// adapter, disjoint from the benchmark-controlled rules directory, and a
/// provenance document that the runner requires before it will run.
#[test]
pub(crate) fn the_semgrep_native_vendoring_convention_is_pinned() {
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

/// The same ruling, reached through the Semgrep arm's own evidence shape:
/// a scan that completed and found nothing at the anchor is `not-reached`,
/// and a finding with no readable location is the one incomplete case.
#[test]
pub(crate) fn the_semgrep_native_arm_reaches_the_same_outcome_rule() {
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
