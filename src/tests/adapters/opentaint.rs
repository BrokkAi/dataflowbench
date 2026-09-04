//! Regression tests for the opentaint adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::KernelPopulation;
use crate::adapters::opentaint::{
    OPENTAINT_ANALYZER_JAR_SHA256, OPENTAINT_MODELS_ARCHIVE_SHA256, OPENTAINT_RULE_ID,
    OpentaintKernel, jvm_fixture_package, opentaint_rule_load_failure, opentaint_rule_paths,
    select_opentaint_cases, witness_opentaint_identity,
};
use crate::adapters::semgrep::{SEMGREP_SINK_PLACEHOLDER, SEMGREP_SOURCE_PLACEHOLDER};
use crate::evidence::benchmark_endpoint_names;
use crate::templates::expected_core_templates;
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::{fs, path::PathBuf};

/// Both OpenTaint kernels select their language's whole expanded core and
/// resolve every endpoint pair, on dedicated per-language paths, from
/// committed rule templates that carry both placeholders and the pinned
/// rule id the load-trace guard checks for.
#[test]
pub(crate) fn opentaint_kernels_are_language_scoped_and_resolvable() {
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
pub(crate) fn opentaint_identity_is_witnessed_against_the_pin() {
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
pub(crate) fn opentaint_rule_load_guard_refuses_silent_failures() {
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
pub(crate) fn opentaint_fixture_packages_parse_both_jvm_spellings() {
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
