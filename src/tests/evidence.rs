//! Regression tests for `crate::evidence`.

use crate::evidence::{
    AnchorDialect, callsite_anchored_outcome, cpp_function_call, evidence_path_matches_file,
    parameter_list_function_call, parameter_list_function_name, rust_function_call,
    sarif_execution_errors, sarif_messages, sarif_result_count,
};
use crate::tests::support::unique_test_dir;
use serde_json::{Value, json};
use std::fs;

#[test]
pub(crate) fn sarif_normalization_counts_results_and_deduplicates_messages() {
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
pub(crate) fn sarif_execution_errors_prevent_clean_negative_interpretation() {
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

#[test]
pub(crate) fn codeql_successful_invocation_with_failed_extraction_fails_closed() {
    let sarif = json!({
        "runs": [{
            "results": [],
            "invocations": [{
                "executionSuccessful": true,
                "toolExecutionNotifications": [{
                    "level": "note",
                    "descriptor": {"id": "cpp/bmn/extraction-information"},
                    "properties": {"attributes": {
                        "extraction_status": {
                            "#errors": 1,
                            "#partial": 0,
                            "#success": 0,
                            "#total": 1,
                            "all_counts": {"Signalled": 1}
                        },
                        "extraction_errors": [{
                            "failure_reason": "Signalled",
                            "error_args": ["clang", "-c", "fixture.c"]
                        }]
                    }}
                }, {
                    "level": "note",
                    "descriptor": {"id": "cpp/extractor/summary"},
                    "properties": {"attributes": {
                        "extractor-failures": 0,
                        "extractor-successes": 0
                    }}
                }]
            }]
        }]
    });
    assert_eq!(
        sarif_execution_errors(&sarif),
        vec![
            "CodeQL extraction failure: Signalled",
            "CodeQL extraction status: 1 error(s), 0 partial extraction(s)"
        ]
    );
}

#[test]
pub(crate) fn codeql_partial_extraction_and_extractor_summary_failures_fail_closed() {
    let sarif = json!({
        "runs": [{
            "results": [],
            "invocations": [{
                "executionSuccessful": true,
                "toolExecutionNotifications": [{
                    "level": "note",
                    "descriptor": {"id": "cpp/bmn/extraction-information"},
                    "properties": {"attributes": {
                        "extraction_status": {
                            "#errors": 0,
                            "#partial": 1,
                            "#success": 1,
                            "#total": 2,
                            "all_counts": {"ExitCode: 0": 2}
                        }
                    }}
                }, {
                    "level": "note",
                    "descriptor": {"id": "cpp/extractor/summary"},
                    "properties": {"attributes": {
                        "extractor-failures": 1,
                        "extractor-successes": 1
                    }}
                }]
            }]
        }]
    });
    assert_eq!(
        sarif_execution_errors(&sarif),
        vec![
            "CodeQL extraction status: 0 error(s), 1 partial extraction(s)",
            "CodeQL extractor summary reports 1 failure(s)"
        ]
    );
}

#[test]
pub(crate) fn codeql_unrelated_extraction_note_attributes_remain_non_errors() {
    let sarif = json!({
        "runs": [{
            "results": [],
            "invocations": [{
                "executionSuccessful": true,
                "toolExecutionNotifications": [{
                    "level": "note",
                    "descriptor": {"id": "cpp/bmn/extraction-information"},
                    "properties": {"attributes": {
                        "error_count": 1,
                        "partial_count": 1,
                        "extraction_errors_text": "Signalled"
                    }}
                }, {
                    "level": "note",
                    "descriptor": {"id": "cpp/extractor/summary"},
                    "properties": {"attributes": {"extractor_failure_count": 1}}
                }]
            }]
        }]
    });
    assert!(sarif_execution_errors(&sarif).is_empty());
}

#[test]
pub(crate) fn codeql_successful_extraction_remains_clean() {
    let sarif = json!({
        "runs": [{
            "results": [],
            "invocations": [{
                "executionSuccessful": true,
                "toolExecutionNotifications": [{
                    "level": "note",
                    "descriptor": {"id": "cpp/bmn/extraction-information"},
                    "properties": {"attributes": {
                        "extraction_status": {
                            "#errors": 0,
                            "#partial": 0,
                            "#success": 1,
                            "#total": 1,
                            "all_counts": {"ExitCode: 0": 1}
                        },
                        "extraction_errors": []
                    }}
                }, {
                    "level": "note",
                    "descriptor": {"id": "cpp/extractor/summary"},
                    "properties": {"attributes": {
                        "extractor-failures": 0,
                        "extractor-successes": 1
                    }}
                }]
            }]
        }]
    });
    assert!(sarif_execution_errors(&sarif).is_empty());
}

#[test]
fn codeql_213_retained_extraction_controls_and_frozen_failures() {
    use crate::adapters::codeql::{
        split_codeql_endpoint_probe, unobserved_codeql_endpoint_outcome,
    };

    for (path, failed) in [
        (
            "reports/issues/213/cpp-partial-attempt/dfb-taint-cpp-closure-capture-positive.sarif.json",
            true,
        ),
        ("reports/issues/213/sdk-control/partial-sdk15.sarif", false),
    ] {
        let sarif: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
        assert_eq!(!sarif_execution_errors(&sarif).is_empty(), failed, "{path}");
    }

    for language in ["c", "cpp"] {
        for access in ["sandbox", "host"] {
            let path = format!("reports/issues/213/reproduction/{language}-{access}.sarif");
            let sarif: Value = serde_json::from_str(&fs::read_to_string(path).unwrap()).unwrap();
            let errors = sarif_execution_errors(&sarif);
            let (_, observed) = split_codeql_endpoint_probe(&sarif);
            if access == "host" {
                assert!(errors.is_empty(), "{language}: {errors:?}");
                assert!(observed.sources > 0 && observed.sinks > 0);
                assert!(unobserved_codeql_endpoint_outcome(observed).is_none());
            } else {
                assert!(
                    !errors.is_empty(),
                    "{language}: failed extraction was accepted"
                );
                assert_eq!((observed.sources, observed.sinks), (0, 0));
                assert_eq!(
                    unobserved_codeql_endpoint_outcome(observed).unwrap().0,
                    "inconclusive"
                );
            }
        }

        // Bind to the immutable release attempt, not whichever report a
        // subsequent correction makes current.
        let root =
            format!("reports/releases/v0.8.0/attempts/codeql-{language}-kernel-attempt-01/outputs");
        let report: Value = serde_json::from_str(
            &fs::read_to_string(format!("{root}/reports/codeql-{language}-kernel.json")).unwrap(),
        )
        .unwrap();
        let results = report["results"].as_array().unwrap();
        assert_eq!(results.len(), if language == "c" { 58 } else { 68 });
        for result in results {
            let raw = result["raw_output"].as_str().unwrap();
            let sarif: Value =
                serde_json::from_str(&fs::read_to_string(format!("{root}/{raw}")).unwrap())
                    .unwrap();
            assert!(!sarif_execution_errors(&sarif).is_empty(), "{raw}");
        }
    }
}

#[test]
fn codeql_213_rerun_evidence_reconciles_with_the_corrected_decoder() {
    use crate::adapters::codeql::{
        CFamilyKernel, codeql_c_family_cases, split_codeql_endpoint_probe,
        unobserved_codeql_endpoint_outcome,
    };

    let root = "reports/issues/213/rerun";
    for (language, kernel) in [("c", CFamilyKernel::C), ("cpp", CFamilyKernel::Cpp)] {
        let report: Value = serde_json::from_str(
            &fs::read_to_string(format!("{root}/reports/codeql-{language}-kernel.json")).unwrap(),
        )
        .unwrap();
        let results = report["results"].as_array().unwrap();
        let cases = codeql_c_family_cases(kernel).unwrap();
        assert_eq!(results.len(), cases.len());
        for (path, case) in cases {
            let matching: Vec<_> = results
                .iter()
                .filter(|result| result["case_id"] == case["id"])
                .collect();
            assert_eq!(matching.len(), 1, "{}", case["id"]);
            let result = matching[0];
            let raw = result["raw_output"].as_str().unwrap();
            let sarif: Value =
                serde_json::from_str(&fs::read_to_string(format!("{root}/{raw}")).unwrap())
                    .unwrap();
            assert!(!sarif["runs"].as_array().unwrap().is_empty());
            assert!(sarif_execution_errors(&sarif).is_empty(), "{raw}");
            let (findings, observed) = split_codeql_endpoint_probe(&sarif);
            let (outcome, _) = unobserved_codeql_endpoint_outcome(observed).unwrap_or_else(|| {
                callsite_anchored_outcome(&path, &case, &findings, AnchorDialect::Cpp)
            });
            assert_eq!(result["outcome"], outcome, "{raw}");
        }
    }
}

/// C and C++ reach members through `.`, `->`, and `::`; none of those is a
/// call of the free sink function the `DFB-SINK:` marker declares.
#[test]
pub(crate) fn cpp_sink_declarations_and_callsites_resolve_through_the_cpp_dialect() {
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
pub(crate) fn go_sink_declarations_resolve_to_the_declared_function() {
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

/// Rust declares a sink the way C#, Go, and C/C++ do, but reaches a member
/// through `.` and `::` only — it has no `->` operator to exclude.
#[test]
pub(crate) fn rust_sink_declarations_resolve_to_the_declared_function() {
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
pub(crate) fn csharp_sink_declarations_resolve_to_the_declared_method() {
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

/// Ruby is the one dialect whose endpoint declarations may carry no
/// parameter list: `def dfb_source # DFB-SOURCE: ...` is a method
/// declaration exactly as `def dfb_sink(value) # DFB-SINK: ...` is. It
/// reaches a method through `.` and a constant path through `::`, and opens
/// comments with `#`.
#[test]
pub(crate) fn ruby_endpoint_declarations_resolve_through_the_ruby_dialect() {
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
pub(crate) fn php_sink_declarations_and_callsites_resolve_through_the_php_dialect() {
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

/// Java declares a sink as an identifier before a parameter list and calls
/// it unqualified; Python does the same but opens its comments with `#`.
#[test]
pub(crate) fn java_and_python_sink_declarations_resolve_through_their_dialects() {
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

/// Infer spells a workspace-relative SARIF artifact with a bare `file:`
/// scheme and no slashes; the shared path matcher must resolve it against
/// the case's anchor file, without loosening any other spelling.
#[test]
pub(crate) fn evidence_path_matcher_strips_the_bare_file_scheme() {
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
