//! Regression tests for the joern adapter: population scoping, the pinned
//! identity, anchor reconciliation, dedicated report paths, and the guards that
//! keep a failed run from reading as a clean negative.

use crate::adapters::KernelPopulation;
use crate::adapters::codeql::{CODEQL_JAVASCRIPT_RAW_DIR, CODEQL_JAVASCRIPT_REPORT};
use crate::adapters::joern::{
    JOERN_KERNEL_SCRIPT, JoernKernel, joern_flow_outcome, select_joern_cases,
};
use crate::cases::case_paths;
use crate::evidence::{AnchorDialect, BenchmarkEndpoints, benchmark_endpoint_names};
use crate::freeze::raw_special_outcome;
use crate::templates::{
    KERNEL_CASE_COUNT, KERNEL_CASE_COUNT_WITHOUT_EXCEPTION_CATCH, challenge_rolled_out,
};
use crate::tests::modeling::KERNEL_ENDPOINTS;
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::{collections::BTreeMap, collections::BTreeSet, fs, path::Path, path::PathBuf};

/// Each Joern kernel is its own population: the balanced core assertions of
/// exactly one language — 32 where all sixteen templates apply, 30 for Rust,
/// whose exception-catch cell is inapplicable — with no case shared between
/// them and no case borrowed from a CodeQL or Bifrost selection. Rust's
/// `Result`/`?` `language-extension` pair is never pulled into the core
/// denominator.
#[test]
pub(crate) fn joern_kernel_selections_are_language_disjoint_and_balanced() {
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
pub(crate) fn joern_report_paths_are_dedicated() {
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
pub(crate) fn joern_endpoints_come_from_the_case_markers() {
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

/// A Joern flow is only `reached` when it lands on a callsite of the case's
/// own anchored sink function.
#[test]
pub(crate) fn joern_flow_evidence_requires_the_sink_callsite() {
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
pub(crate) fn joern_runner_failures_never_become_clean_negatives() {
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
