//! Regression tests for `crate::latency`.

use crate::adapters::KernelPopulation;
use crate::adapters::codeql::CODEQL_RUBY_RAW_DIR;
use crate::adapters::joern::{
    JOERN_JAVA_RAW_DIR, JOERN_KERNEL_SCRIPT, JOERN_PHP_RAW_DIR, JOERN_WARM_BATCH_SCRIPT,
};
use crate::adapters::semgrep::SemgrepKernel;
use crate::freeze::raw_special_outcome;
use crate::latency::{
    OVERHEAD_REPEATS, OVERHEAD_ROOT, OverheadLanguage, OverheadRun, WARM_LATENCY_ROOT,
    WARM_REPEATS, WARM_SUPERSEDED_ROOT, WarmBatch, WarmLanguage, WarmTool, overhead_range,
    trivial_fixture, warm_batch_sizes, warm_slope,
};
use serde_json::json;
use std::fs;
use walkdir::WalkDir;

/// The eleven-line block that decides what a Joern case's evidence says —
/// the frontend dispatch, the two selectors, and the `reachableByFlows`
/// call — is character-for-character the same in the cold kernel script
/// and the warm batch script.
///
/// This is the mechanical form of Amendment A15's promise that the warm
/// measurement times the *same work* as the cold rows it stands beside. If
/// either script's query drifts, the warm marginal stops describing the
/// cold number's cost and this test fails rather than a page quietly
/// publishing an incomparable figure.
///
/// Exactly one substitution is allowed, and it is the reason the two files
/// are not one: the cold runner gives every case a fresh scratch directory
/// and so can reuse one project name, while the warm batch shares a
/// workspace across k cases and must name each project distinctly. Nothing
/// else may differ.
#[test]
pub(crate) fn joern_warm_batch_script_shares_the_kernel_query_block() {
    const BLOCK_START: &str = "if (language == \"RUBYSRC\") {";
    const BLOCK_END: &str = "val flows = sinkNodes.reachableByFlows(sourceNodes).l";

    fn block(source: &str) -> Vec<&str> {
        let lines: Vec<&str> = source.lines().collect();
        let start = lines
            .iter()
            .position(|line| line.contains(BLOCK_START))
            .expect("the query block starts at the frontend dispatch");
        let end = lines
            .iter()
            .position(|line| line.contains(BLOCK_END))
            .expect("the query block ends at reachableByFlows");
        assert!(start < end, "the block's anchors are out of order");
        lines[start..=end].to_vec()
    }

    let kernel = fs::read_to_string(JOERN_KERNEL_SCRIPT).unwrap();
    let warm = fs::read_to_string(JOERN_WARM_BATCH_SCRIPT).unwrap();
    let expected: Vec<String> = block(&kernel)
        .into_iter()
        .map(|line| {
            line.replace(
                "projectName = \"dataflowbench\"",
                "projectName = projectName",
            )
        })
        .collect();
    let measured: Vec<String> = block(&warm).into_iter().map(str::to_string).collect();
    assert_eq!(
        expected, measured,
        "the warm batch script's query block has drifted from the kernel script's"
    );
    // The block is substantive, not an accidental one-line match.
    assert!(expected.len() >= 8);

    // And the warm script never introduces a clock of its own: the tier's
    // decomposition rule admits only the runner's subprocess boundary, and
    // A13 does not relax it.
    for forbidden in ["nanoTime", "currentTimeMillis", "Instant.now"] {
        assert!(
            !warm.contains(forbidden),
            "the warm batch script must not timestamp itself ({forbidden})"
        );
    }
}

/// The slope estimators are the preregistered ones, and the fit is a
/// slope — not an average, which would still carry the fixed cost.
#[test]
pub(crate) fn warm_slope_recovers_the_marginal_cost_not_the_average() {
    // A process that pays 10 000 ms once and 500 ms per case.
    let batches: Vec<WarmBatch> = [1usize, 2, 4, 8, 16]
        .into_iter()
        .map(|k| WarmBatch {
            k,
            wall_ms: 10_000 + 500 * k as u64,
            case_ids: Vec::new(),
            load_before: None,
        })
        .collect();
    let slope = warm_slope(&batches).unwrap();
    assert!((slope.endpoint_ms - 500.0).abs() < 1e-6);
    assert!((slope.least_squares_ms - 500.0).abs() < 1e-6);
    assert!((slope.intercept_ms - 10_000.0).abs() < 1e-6);
    // The average per case at k=16 is 1125 ms — more than twice the
    // marginal cost. Reporting the average would smuggle the fixed cost
    // back into the number the slope exists to remove.
    assert!(slope.least_squares_ms < 10_000.0 / 16.0 + 500.0);

    // One point cannot define a slope, and neither can a repeated k.
    assert!(warm_slope(&batches[..1]).is_err());
    assert!(
        warm_slope(&[
            WarmBatch {
                k: 4,
                wall_ms: 1,
                case_ids: Vec::new(),
                load_before: None
            },
            WarmBatch {
                k: 4,
                wall_ms: 2,
                case_ids: Vec::new(),
                load_before: None
            },
        ])
        .is_err()
    );
}

/// Batch sizes must be strictly increasing and positive, so every larger
/// batch is a strict superset of every smaller one and a slope is defined.
#[test]
pub(crate) fn warm_batch_sizes_are_strictly_increasing() {
    assert_eq!(
        warm_batch_sizes("1,2,4,8,16").unwrap(),
        vec![1, 2, 4, 8, 16]
    );
    assert_eq!(warm_batch_sizes(" 1 , 3 ").unwrap(), vec![1, 3]);
    for rejected in ["1", "", "4,2", "2,2", "0,4", "1,x"] {
        assert!(
            warm_batch_sizes(rejected).is_err(),
            "{rejected:?} should be refused"
        );
    }
}

/// Warm-marginal artifacts are auxiliary: they live in their own directory
/// and carry an evidence kind no correctness reader recognizes, so nothing
/// in the scoring path can mistake one for a result.
#[test]
pub(crate) fn warm_latency_artifacts_are_auxiliary_and_never_an_outcome_input() {
    assert!(WARM_LATENCY_ROOT.starts_with("reports/raw/"));
    // Not inside any slice directory a normalized report binds.
    for report in [
        JOERN_JAVA_RAW_DIR.to_string(),
        SemgrepKernel::Java.raw_dir(),
    ] {
        assert!(!WARM_LATENCY_ROOT.starts_with(&report));
        assert!(!report.starts_with(WARM_LATENCY_ROOT));
    }
    // Retired figures must not live under a directory the runner sweeps:
    // `measure-warm-latency` removes its whole output directory before it
    // writes, so a superseded artifact parked there is destroyed by the
    // next re-measurement. That is not hypothetical — it happened once.
    for tool in [WarmTool::Joern, WarmTool::Semgrep] {
        let swept = format!(
            "{WARM_LATENCY_ROOT}/{}-{}-kernel",
            tool.as_str(),
            WarmLanguage::Java.as_str()
        );
        assert!(
            !WARM_SUPERSEDED_ROOT.starts_with(&swept),
            "retired warm evidence must not sit under the swept directory {swept}"
        );
    }
    let document = json!({
        "evidence_kind": "retained-warm-marginal-latency",
        "marginal_ms_per_case_range": {"endpoint": [500.0, 520.0]},
    });
    assert_eq!(raw_special_outcome(&document), None);
}

/// The figure is published as a range over retained repeats, and the
/// repeat count is fixed in the source rather than passed in.
///
/// Both properties exist to remove a discretionary parameter from the path
/// between a measurement and a page. A caller-chosen repeat count would let
/// a run be extended until its spread looked narrow; an agreement tolerance
/// would have to be picked, and any tolerance picked after the numbers
/// exist is the after-the-fact decision the tier's motivation refuses. The
/// range needs neither.
#[test]
pub(crate) fn warm_repeats_are_fixed_and_published_as_a_range() {
    assert!(WARM_REPEATS >= 2, "a range needs at least two repeats");
    let source = fs::read_to_string(file!()).unwrap();
    // No tolerance constant anywhere in the warm path: the range is the
    // precision statement, and nothing gates on how wide it is. The needles
    // are assembled at runtime so this assertion cannot trip on its own
    // literals.
    for suffix in ["AGREEMENT", "TOLERANCE", "THRESHOLD"] {
        let gate = format!("WARM_{suffix}");
        assert!(
            !source.contains(&gate),
            "the warm path must not gate publication on an agreement threshold ({gate})"
        );
    }
}

/// The same property for A24's estimates: an auxiliary directory of its
/// own, outside every slice a normalized report binds and outside the
/// warm directory, and a document the freeze validator's special-outcome
/// reader cannot mistake for evidence of an outcome.
#[test]
pub(crate) fn invocation_overhead_artifacts_are_auxiliary_and_never_an_outcome_input() {
    assert!(OVERHEAD_ROOT.starts_with("reports/raw/"));
    assert!(!OVERHEAD_ROOT.starts_with(WARM_LATENCY_ROOT));
    assert!(!WARM_LATENCY_ROOT.starts_with(OVERHEAD_ROOT));
    for report in [
        JOERN_JAVA_RAW_DIR.to_string(),
        JOERN_PHP_RAW_DIR.to_string(),
        CODEQL_RUBY_RAW_DIR.to_string(),
        SemgrepKernel::Kotlin.raw_dir(),
    ] {
        assert!(!OVERHEAD_ROOT.starts_with(&report));
        assert!(!report.starts_with(OVERHEAD_ROOT));
    }
    let document = json!({
        "evidence_kind": "retained-invocation-overhead-estimate",
        "estimated_overhead_ms": {"low": 2_900, "high": 3_100},
    });
    assert_eq!(raw_special_outcome(&document), None);
}

/// The published figure is the range the repeats span, and nothing else:
/// not a mean, not a chosen repeat, and not a figure conditioned on the
/// repeats agreeing.
#[test]
pub(crate) fn invocation_overhead_publishes_the_range_over_every_repeat() {
    let run = |wall_ms: u64| OverheadRun {
        phases: vec![("total".into(), wall_ms)],
        wall_ms,
        load_before: None,
    };
    let range = overhead_range(&[run(4200), run(3900), run(4600)]).unwrap();
    assert_eq!(range.low_ms, 3900);
    assert_eq!(range.high_ms, 4600);

    // Order cannot change the figure: a range has no notion of a first or
    // a last repeat, which is the point of publishing one.
    assert_eq!(
        overhead_range(&[run(4600), run(3900), run(4200)]).unwrap(),
        range
    );

    // A wide disagreement widens the range; it never withholds it. The
    // width is the precision, and stating it is the publication.
    let wide = overhead_range(&[run(1000), run(9000), run(2000)]).unwrap();
    assert_eq!((wide.low_ms, wide.high_ms), (1000, 9000));

    // Repeats that agree exactly collapse to a point range rather than to
    // a special case.
    let tight = overhead_range(&[run(500), run(500), run(500)]).unwrap();
    assert_eq!((tight.low_ms, tight.high_ms), (500, 500));
}

/// No agreement threshold exists anywhere in the overhead estimator.
///
/// The range convention replaced a withhold-on-disagreement rule, and a
/// tolerance constant creeping back would quietly restore it — so the
/// absence is asserted against the source itself rather than trusted to
/// review. The same property is asserted for the warm-marginal figures.
#[test]
pub(crate) fn no_agreement_threshold_constant_governs_the_overhead_estimate() {
    // Read every module in the crate, not one file: the estimator's own
    // helpers live beside each adapter, and a threshold constant reintroduced
    // in any of them must fail this test.
    let mut source = String::new();
    for entry in WalkDir::new("src")
        .into_iter()
        .filter_map(std::result::Result::ok)
    {
        if entry
            .path()
            .extension()
            .is_some_and(|extension| extension == "rs")
        {
            source.push_str(&fs::read_to_string(entry.path()).unwrap());
        }
    }
    // The needles are assembled rather than written out, so this test's
    // own text cannot satisfy the search it performs.
    for forbidden in [
        format!("OVERHEAD_{}", "TOLERANCE"),
        format!("OVERHEAD_{}", "AGREEMENT"),
        format!("fn overhead_{}", "stability"),
    ] {
        assert!(
            !source.contains(&forbidden),
            "the overhead estimate must not be gated on its repeats agreeing, \
                 but the source defines {forbidden}"
        );
    }
    // And the repeat count is a source constant, not a per-run argument.
    assert!(OVERHEAD_REPEATS >= 2);
}

/// The estimator's fixture must be a *no-flow* fixture, or the number it
/// produces is not an overhead estimate but a small analysis.
///
/// Each template is checked for the property that makes it one: both
/// endpoints are declared with the benchmark's own names — so the
/// committed policy, rule and query resolve exactly as they do on a real
/// case — and the sink is called on a literal, never on the source's
/// result.
#[test]
pub(crate) fn trivial_fixtures_declare_both_endpoints_and_carry_no_flow() {
    for language in [
        OverheadLanguage::C,
        OverheadLanguage::Java,
        OverheadLanguage::Kotlin,
        OverheadLanguage::Php,
        OverheadLanguage::Python,
        OverheadLanguage::Ruby,
    ] {
        let (name, text) = trivial_fixture(language);
        assert!(
            !name.is_empty() && text.contains("dfb_source") && text.contains("dfb_sink"),
            "{}: both endpoints must be declared",
            language.as_str()
        );
        assert!(
            text.contains("// DFB-SOURCE:") || text.contains("# DFB-SOURCE:"),
            "{}: the source marker must be present",
            language.as_str()
        );
        assert!(
            text.contains("// DFB-SINK:") || text.contains("# DFB-SINK:"),
            "{}: the sink marker must be present",
            language.as_str()
        );
        // No line may pass the source's value into the sink, directly or
        // through a name: the sink's argument is a literal on every one.
        for line in text.lines() {
            let call = line.trim();
            if !call.starts_with("dfb_sink(") {
                continue;
            }
            assert!(
                call.starts_with("dfb_sink(0)") || call.starts_with("dfb_sink(\"clean\")"),
                "{}: the sink must be called on a literal, found {call:?}",
                language.as_str()
            );
        }
        // And the fixture is never a case: nothing about it may claim a
        // template, a polarity or a score tier.
        for forbidden in ["dfb-template-", "score_tier", "expected_outcome"] {
            assert!(
                !text.contains(forbidden),
                "{}: a trivial fixture is not a case and must not carry {forbidden}",
                language.as_str()
            );
        }
    }
}
