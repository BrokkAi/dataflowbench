//! The descriptive latency-characterization tier: warm-batch slopes and
//! invocation overhead. Auxiliary measurement only — nothing here is ever an
//! input to a correctness outcome. See docs/latency-tier.md.

use crate::adapters::ToolIdentity;
use crate::adapters::bifrost::overhead_run_bifrost;
use crate::adapters::codeql::{codeql_version_identity, overhead_run_codeql};
use crate::adapters::flowdroid::{overhead_run_flowdroid, witness_flowdroid_identity};
use crate::adapters::infer::{overhead_run_infer, witness_infer_identity};
use crate::adapters::joern::{
    JoernKernel, joern_version_identity, measure_joern_warm_batch, overhead_run_joern,
    select_joern_cases,
};
use crate::adapters::opentaint::{overhead_run_opentaint, witness_opentaint_identity};
use crate::adapters::pysa::{PysaTools, overhead_run_pysa, witness_pysa_identity};
use crate::adapters::semgrep::{
    SEMGREP_SINK_PLACEHOLDER, SEMGREP_SOURCE_PLACEHOLDER, SemgrepKernel,
    measure_semgrep_warm_batch, overhead_run_semgrep, select_semgrep_cases,
    semgrep_capability_exclusion, semgrep_version_identity,
};
use crate::cases::{fixture_revision, validate_cases};
use crate::evidence::benchmark_endpoint_names;
use crate::runtime::{command_output, now_seconds, write_run_environment};
use anyhow::{Context, Result, bail};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::{collections::BTreeMap, fs, path::Path, path::PathBuf, process::Command};

/// Every adapter in the benchmark. Unlike `WarmTool`, this enum is complete:
/// A24's estimate is attempted for all eight, and an adapter that cannot be
/// estimated here records a decline rather than being absent from the list.
#[derive(Clone, Copy, Debug, PartialEq, Eq, clap::ValueEnum)]
pub(crate) enum OverheadTool {
    Bifrost,
    Codeql,
    Flowdroid,
    Infer,
    Joern,
    Opentaint,
    Pysa,
    Semgrep,
}

impl OverheadTool {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::Bifrost => "bifrost",
            Self::Codeql => "codeql",
            Self::Flowdroid => "flowdroid",
            Self::Infer => "infer",
            Self::Joern => "joern",
            Self::Opentaint => "opentaint",
            Self::Pysa => "pysa",
            Self::Semgrep => "semgrep",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, clap::ValueEnum)]
pub(crate) enum OverheadLanguage {
    C,
    Java,
    Kotlin,
    Php,
    Python,
    Ruby,
}

impl OverheadLanguage {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::C => "c",
            Self::Java => "java",
            Self::Kotlin => "kotlin",
            Self::Php => "php",
            Self::Python => "python",
            Self::Ruby => "ruby",
        }
    }
}

/// The adapters whose released CLI exposes a warm, multi-case batch that does
/// the same per-case work the cold kernel runner does. The audit behind this
/// list — including the declines — is Amendment A15's observability table.
#[derive(Clone, Copy, Debug, PartialEq, Eq, clap::ValueEnum)]
pub(crate) enum WarmTool {
    Joern,
    Semgrep,
}

impl WarmTool {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::Joern => "joern",
            Self::Semgrep => "semgrep",
        }
    }
}

#[derive(Clone, Copy, Debug, PartialEq, Eq, clap::ValueEnum)]
pub(crate) enum WarmLanguage {
    Java,
}

impl WarmLanguage {
    pub(crate) fn as_str(self) -> &'static str {
        match self {
            Self::Java => "java",
        }
    }
}

// ---------------------------------------------------------------------------
// Warm-marginal latency measurement (Amendments A15 and A21,
// docs/latency-tier.md).
//
// A15 established the measurement and published it as a point estimate gated on
// an unstated agreement tolerance. A21 supersedes that: the figure is the range
// its retained repeats span, which needs no tolerance.
//
// The published latency rows are cold per-invocation wall-clock, and stay so:
// boot is not observable inside one invocation, so a benchmark that spawns one
// process per case honestly charges each case for the whole process. But a
// reader comparing a JVM adapter's cold median against a native adapter's is
// reading a start-up difference as a steady-state difference, and the two are
// not the same claim.
//
// This module measures the other quantity, separately and without estimating
// anything: run k cases through ONE tool process, for increasing k, and report
// the *slope* of batch wall-clock against k. The slope is the marginal cost of
// one more case in a process that has already paid its start-up, so start-up
// is amortized out by construction rather than subtracted.
//
// Three properties are load-bearing, and each is enforced here rather than
// asserted in prose:
//
//  1. **Timing only.** Nothing in this module writes a normalized report, and
//     no correctness outcome is derived from a warm run. Its artifacts live in
//     their own directory under `reports/raw/warm-latency/`, which the scoring
//     path, `validate-reports`, and the freeze manifest never read.
//  2. **The same work.** The batch reuses the same case selection, the same
//     endpoint resolution, the same workspace materialization, and the same
//     query logic as the cold kernel runner. What differs is only how many
//     cases share one process.
//  3. **One clock, at a subprocess boundary.** The only timestamps are the
//     runner's, around the whole batch subprocess — the same monotonic clock
//     and the same kind of boundary the cold sidecars use. Neither script nor
//     tool self-timestamping enters any number, so the tier's decomposition
//     rule is untouched.
//  4. **The figure is a range, not a point.** The whole series is measured
//     twice and both repeats are retained; what is published is the range they
//     span. A single slope over a handful of batches on a developer machine
//     has a precision, and the reader is entitled to see it rather than infer
//     it from a number stated to two significant figures.
// ---------------------------------------------------------------------------

/// Where warm-marginal artifacts live: a directory of their own, clearly apart
/// from the per-slice raw-evidence directories the reports bind.
pub(crate) const WARM_LATENCY_ROOT: &str = "reports/raw/warm-latency";

/// How many times the whole batch series is measured.
///
/// Not a trial count to be averaged, and not an acceptance test with a
/// threshold. A single slope over a handful of batches on a developer machine
/// is a point estimate with unstated precision, and the two ways to give it a
/// precision are both worse than this one: publishing one run and hiding the
/// spread understates it, and gating publication on an agreement tolerance
/// requires choosing that tolerance — which, chosen after the numbers exist,
/// is exactly the after-the-fact decision the tier's motivation refuses.
///
/// So every repeat is retained and the figure is published as the **range** the
/// repeats span. The width of the range is the precision statement, the reader
/// sees it directly, and there is no discretionary parameter anywhere in the
/// path from measurement to page.
pub(crate) const WARM_REPEATS: usize = 2;

/// Where superseded warm figures are retained, outside every directory the
/// runner sweeps.
///
/// `measure-warm-latency` clears its own output directory at the start of every
/// run, so a stale batch can never be read as part of a fresh measurement. That
/// is right for its own outputs and destructive for a *retired* figure parked
/// beside them — which is how the first attempt at retaining A15's superseded
/// artifact was lost, to the very next re-measurement. Retired evidence lives
/// here instead, in a tree the runner never writes to.
pub(crate) const WARM_SUPERSEDED_ROOT: &str = "reports/raw/warm-latency/superseded-a15";

/// One batch: k cases through one tool process, and the wall-clock of that
/// process.
#[derive(Clone, Debug)]
pub(crate) struct WarmBatch {
    pub(crate) k: usize,
    pub(crate) wall_ms: u64,
    pub(crate) case_ids: Vec<String>,
    /// The machine's one-minute load average, sampled immediately before the
    /// batch was spawned.
    ///
    /// The tier's measurement hygiene is the standing sequential-run
    /// discipline, and a run that shared the machine has unusable timing
    /// evidence. On a developer machine that discipline is a convention, not
    /// an enforcement, so the observed load rides on the artifact: a reader
    /// can see the conditions each batch was taken under instead of taking
    /// "quiet machine" on trust.
    pub(crate) load_before: Option<f64>,
}

/// The one-minute load average, best-effort. A number a reader can weigh is
/// worth having; failing a measurement over an unreadable one is not.
pub(crate) fn load_average_one_minute() -> Option<f64> {
    let uptime = command_output(&mut Command::new("uptime")).ok()?;
    let tail = uptime.rsplit_once("load averages:").or_else(|| {
        // Linux `uptime` spells it "load average:" and separates with commas.
        uptime.rsplit_once("load average:")
    })?;
    tail.1
        .trim()
        .split([' ', ','])
        .find(|field| !field.is_empty())
        .and_then(|field| field.parse::<f64>().ok())
}

/// The two slope estimators the amendment preregisters, plus the fitted
/// intercept.
///
/// Both are reported because they answer the same question two ways and a
/// reader is entitled to see them disagree: the endpoint estimator uses only
/// the smallest and largest batch and is the simplest thing that could work,
/// while the least-squares fit uses every point. Neither is corrected by the
/// other, and neither is ever subtracted from a cold number.
#[derive(Clone, Copy, Debug, PartialEq)]
pub(crate) struct WarmSlope {
    pub(crate) endpoint_ms: f64,
    pub(crate) least_squares_ms: f64,
    pub(crate) intercept_ms: f64,
}

/// Fit the marginal cost from the measured batches.
///
/// `endpoint_ms` is `(T_kmax − T_kmin) / (kmax − kmin)`. `least_squares_ms` is
/// the ordinary-least-squares slope of `wall_ms` on `k`, and `intercept_ms` is
/// that fit's intercept — a *descriptive* estimate of the fixed per-process
/// cost, published as such and never subtracted from any measured number.
pub(crate) fn warm_slope(batches: &[WarmBatch]) -> Result<WarmSlope> {
    if batches.len() < 2 {
        bail!("a warm-marginal fit needs at least two distinct batch sizes");
    }
    let first = batches.first().expect("length checked");
    let last = batches.last().expect("length checked");
    if last.k == first.k {
        bail!("a warm-marginal fit needs at least two distinct batch sizes");
    }
    let endpoint_ms =
        (last.wall_ms as f64 - first.wall_ms as f64) / (last.k as f64 - first.k as f64);

    let n = batches.len() as f64;
    let mean_k = batches.iter().map(|batch| batch.k as f64).sum::<f64>() / n;
    let mean_t = batches
        .iter()
        .map(|batch| batch.wall_ms as f64)
        .sum::<f64>()
        / n;
    let mut covariance = 0.0;
    let mut variance = 0.0;
    for batch in batches {
        let dk = batch.k as f64 - mean_k;
        covariance += dk * (batch.wall_ms as f64 - mean_t);
        variance += dk * dk;
    }
    if variance == 0.0 {
        bail!("a warm-marginal fit needs at least two distinct batch sizes");
    }
    let least_squares_ms = covariance / variance;
    Ok(WarmSlope {
        endpoint_ms,
        least_squares_ms,
        intercept_ms: mean_t - least_squares_ms * mean_k,
    })
}

/// Parse and check the requested batch sizes: strictly increasing, positive,
/// and at least two of them, so a slope is always defined.
pub(crate) fn warm_batch_sizes(spec: &str) -> Result<Vec<usize>> {
    let mut sizes = Vec::new();
    for field in spec.split(',') {
        let field = field.trim();
        if field.is_empty() {
            continue;
        }
        let size: usize = field
            .parse()
            .with_context(|| format!("batch size {field:?} is not a positive integer"))?;
        if size == 0 {
            bail!("batch size 0 measures nothing");
        }
        if sizes.last().is_some_and(|last| *last >= size) {
            bail!("batch sizes must be strictly increasing; got {spec:?}");
        }
        sizes.push(size);
    }
    if sizes.len() < 2 {
        bail!("at least two batch sizes are needed to fit a slope; got {spec:?}");
    }
    Ok(sizes)
}

/// The population one warm measurement batches, in a deterministic order.
///
/// Order is by case identifier, so the k-case batch is always the same prefix
/// of the same list and a larger batch is a strict superset of a smaller one.
/// That is what makes the difference between two batches attributable to the
/// cases that were added rather than to which cases were chosen.
pub(crate) struct WarmPopulation {
    pub(crate) cases: Vec<(PathBuf, Value)>,
    /// Why the batched population is narrower than the kernel's, when it is.
    pub(crate) restriction: Option<String>,
}

pub(crate) fn warm_population(tool: WarmTool, language: WarmLanguage) -> Result<WarmPopulation> {
    match (tool, language) {
        (WarmTool::Joern, WarmLanguage::Java) => {
            let mut cases = select_joern_cases(JoernKernel::Java)?;
            cases.sort_by(|left, right| left.1["id"].as_str().cmp(&right.1["id"].as_str()));
            Ok(WarmPopulation {
                cases,
                restriction: None,
            })
        }
        (WarmTool::Semgrep, WarmLanguage::Java) => {
            // Semgrep's kernel population is partitioned before invocation:
            // the cases its own CLI text declares out of scope are never
            // handed to it and are never timed cold either, so they cannot be
            // in a warm batch. And one `semgrep scan` carries one `--config`,
            // so a batch is only the same work as its k cold runs when all k
            // resolve to the identical rule text. Both restrictions narrow the
            // population; both are recorded on the artifact rather than
            // silently applied.
            let template = fs::read_to_string(SemgrepKernel::Java.rule())?;
            let mut keyed: Vec<(String, PathBuf, Value)> = Vec::new();
            for (path, case) in select_semgrep_cases(SemgrepKernel::Java)? {
                if semgrep_capability_exclusion(&case).is_some() {
                    continue;
                }
                let Ok(endpoints) =
                    benchmark_endpoint_names(&path, &case, SemgrepKernel::Java.dialect())
                else {
                    continue;
                };
                let rule = template
                    .replace(SEMGREP_SOURCE_PLACEHOLDER, &endpoints.source_function)
                    .replace(SEMGREP_SINK_PLACEHOLDER, &endpoints.sink_function);
                keyed.push((rule, path, case));
            }
            let mut counts: BTreeMap<String, usize> = BTreeMap::new();
            for (rule, _, _) in &keyed {
                *counts.entry(rule.clone()).or_default() += 1;
            }
            let (majority, majority_count) = counts
                .into_iter()
                .max_by_key(|(_, count)| *count)
                .context("the Semgrep Java kernel resolved no invocable case")?;
            let total = keyed.len();
            let mut cases: Vec<(PathBuf, Value)> = keyed
                .into_iter()
                .filter(|(rule, _, _)| *rule == majority)
                .map(|(_, path, case)| (path, case))
                .collect();
            cases.sort_by(|left, right| left.1["id"].as_str().cmp(&right.1["id"].as_str()));
            Ok(WarmPopulation {
                cases,
                restriction: Some(format!(
                    "one `semgrep scan` carries one --config, so a batch is restricted to cases \
                     resolving to identical rule text: {majority_count} of the \
                     {total} invocable Java kernel assertions"
                )),
            })
        }
    }
}

/// Run one warm measurement and retain its auxiliary timing artifact.
pub(crate) fn measure_warm_latency(
    tool: WarmTool,
    language: WarmLanguage,
    batch_sizes: &str,
    binary: &Path,
) -> Result<()> {
    validate_cases()?;
    let sizes = warm_batch_sizes(batch_sizes)?;
    let population = warm_population(tool, language)?;
    let available = population.cases.len();
    let largest = *sizes.last().expect("checked non-empty");
    if largest > available {
        bail!(
            "batch size {largest} exceeds the {available} cases the {} {} warm population holds",
            tool.as_str(),
            language.as_str()
        );
    }

    let raw_dir = PathBuf::from(WARM_LATENCY_ROOT).join(format!(
        "{}-{}-kernel",
        tool.as_str(),
        language.as_str()
    ));
    if raw_dir.exists() {
        fs::remove_dir_all(&raw_dir).with_context(|| format!("clear {}", raw_dir.display()))?;
    }
    fs::create_dir_all(&raw_dir)?;

    // Identity is witnessed from the binary and stamped exactly as every other
    // run stamps it, so a warm number is attributable to one machine and one
    // measured tool without re-measurement.
    let identity = match tool {
        WarmTool::Joern => joern_version_identity(binary)?,
        WarmTool::Semgrep => semgrep_version_identity(binary)?,
    };
    write_run_environment(&raw_dir, tool.as_str(), &identity)?;

    let started = now_seconds()?;
    // The whole series is measured `WARM_REPEATS` times, back to back, and
    // every repeat is retained. The repeats are not a trial to be averaged and
    // not an acceptance test to be passed: they are the figure's own precision,
    // published as the range they span.
    let mut runs: Vec<Vec<WarmBatch>> = Vec::new();
    for repeat in 1..=WARM_REPEATS {
        let mut batches = Vec::new();
        for &k in &sizes {
            let prefix = &population.cases[..k];
            println!(
                "measuring {} {} warm batch k={k} (run {repeat} of {WARM_REPEATS})",
                tool.as_str(),
                language.as_str()
            );
            let batch = match tool {
                WarmTool::Joern => {
                    measure_joern_warm_batch(binary, language, prefix, &raw_dir, k, repeat)?
                }
                WarmTool::Semgrep => {
                    measure_semgrep_warm_batch(binary, prefix, &raw_dir, k, repeat)?
                }
            };
            println!("  k={k} wall {} ms", batch.wall_ms);
            batches.push(batch);
        }
        runs.push(batches);
    }
    let slopes = runs
        .iter()
        .map(|batches| warm_slope(batches))
        .collect::<Result<Vec<_>>>()?;
    let range = |pick: fn(&WarmSlope) -> f64| {
        let values: Vec<f64> = slopes.iter().map(pick).collect();
        let low = values.iter().copied().fold(f64::INFINITY, f64::min);
        let high = values.iter().copied().fold(f64::NEG_INFINITY, f64::max);
        (low, high)
    };
    let (endpoint_low, endpoint_high) = range(|slope| slope.endpoint_ms);
    let (least_squares_low, least_squares_high) = range(|slope| slope.least_squares_ms);

    let document = json!({
        "schema_version": 1,
        "evidence_kind": "retained-warm-marginal-latency",
        // The amendment this artifact is published under. A15 established
        // the measurement; A21 supersedes how it is published.
        "amendment": "A21",
        "establishing_amendment": "A15",
        "adapter": tool.as_str(),
        "language": language.as_str(),
        "tool_version": identity.version,
        "tool_build_identity": identity.build_identity,
        "fixture_revision": fixture_revision()?,
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
        "clock": "monotonic",
        "measured_boundary": "one subprocess per batch, whole-invocation wall-clock",
        "population_available": available,
        "population_restriction": population.restriction,
        "repeats": WARM_REPEATS,
        "runs": runs.iter().zip(&slopes).enumerate().map(|(index, (batches, slope))| json!({
            "run": index + 1,
            "batches": batches.iter().map(|batch| json!({
                "k": batch.k,
                "wall_ms": batch.wall_ms,
                "case_ids": batch.case_ids,
                "load_average_1m_before": batch.load_before,
            })).collect::<Vec<_>>(),
            "marginal_ms_per_case": {
                "endpoint": slope.endpoint_ms,
                "least_squares": slope.least_squares_ms,
            },
            "fitted_fixed_cost_ms": slope.intercept_ms,
        })).collect::<Vec<_>>(),
        // The published figure: the range the repeats span, never their mean
        // and never one of them chosen over the others.
        "marginal_ms_per_case_range": {
            "endpoint": [endpoint_low, endpoint_high],
            "least_squares": [least_squares_low, least_squares_high],
        },
    });
    let path = raw_dir.join("warm-latency.json");
    fs::write(&path, serde_json::to_string_pretty(&document)? + "\n")?;
    println!(
        "wrote {} — marginal {:.0}-{:.0} ms/case (least squares over {WARM_REPEATS} runs), {:.0}-{:.0} ms/case (endpoint)",
        path.display(),
        least_squares_low,
        least_squares_high,
        endpoint_low,
        endpoint_high
    );
    Ok(())
}

/// Confirm a batch actually analyzed every case it was given, and retain the
/// per-case evidence it produced.
///
/// A warm number is only the marginal cost of *the benchmark's work* if the
/// batch really did that work. The retained evidence is what makes that
/// auditable after the fact: it is byte-comparable against the cold run's
/// retained evidence for the same cases, so a batch that quietly analyzed less
/// is visible rather than fast.
pub(crate) fn warm_batch_completed(
    completion_path: &Path,
    k: usize,
    repeat: usize,
    evidence: &Path,
    case_ids: &[String],
    raw_dir: &Path,
) -> Result<()> {
    let completion: Value = serde_json::from_str(
        &fs::read_to_string(completion_path).context("read the warm batch completion marker")?,
    )?;
    let analyzed = completion["analyzed"].as_u64().unwrap_or_default() as usize;
    if analyzed != k {
        bail!("the warm batch k={k} analyzed {analyzed} cases");
    }
    let retained = raw_dir.join(format!("run-{repeat}-batch-{k}-evidence"));
    fs::create_dir_all(&retained)?;
    for id in case_ids {
        let produced = evidence.join(format!("{id}.json"));
        if !produced.is_file() {
            bail!("the warm batch k={k} produced no evidence for {id}");
        }
        fs::copy(&produced, retained.join(format!("{id}.json")))?;
    }
    Ok(())
}

// ---------------------------------------------------------------------------
// Per-invocation overhead estimation (Amendment A24, docs/latency-tier.md).
//
// The warm-marginal figures (A15, as corrected by A21) measure the cost of one
// more case in a process already running, and decline to estimate one where the
// released CLI has no batch. That rule is untouched. This module measures a
// different quantity, which every adapter can supply: the wall-clock of ONE
// COMPLETE ADAPTER INVOCATION over a trivial no-flow fixture — same pipeline,
// same committed configuration path, same subprocess shape, a fixture with no
// flow to find.
//
// What the number is, stated where the code that produces it lives:
//
//   * it is fixed per-invocation overhead PLUS the trivial fixture's own
//     near-zero analysis, so it is an UPPER BOUND on start-up and warm-up and
//     is labelled an estimate everywhere it appears;
//   * it is a cold, single-shot execution — which is exactly what the cold
//     rows contain, and exactly what a steady-state deployment does not do;
//   * it is measured in one named language per adapter and is never presented
//     as language-free;
//   * it is never subtracted from a cold number, never substituted for one,
//     and never enters an ordering.
//
// Three properties are enforced here rather than asserted in prose:
//
//  1. **Timing only.** Nothing here writes a normalized report, derives an
//     outcome, or adds a case. The trivial fixtures are generated from the
//     templates below into scratch and retained beside the artifact; nothing
//     is written under `cases/` and no population changes.
//  2. **The same invocation.** Each arm builds the command from the same
//     committed policy, rule, query and flags the cold kernel runner uses.
//  3. **Range publication.** Every measurement is repeated a fixed number of
//     times — the count is this constant, not a per-run choice — every repeat
//     is retained, and the published figure is the **range the repeats span**.
//     Its width is the measurement's precision, stated rather than hidden.
//     There is no agreement threshold anywhere in this module: no tolerance
//     constant, no pass/fail on repeat agreement, no mean, and no "the retained
//     run is the nth". A repeat that disagrees widens the published range,
//     which is the honest consequence, instead of triggering a rule that must
//     itself be justified. This is the same convention the warm-marginal
//     figures use (Amendment A21), shared rather than re-derived.
// ---------------------------------------------------------------------------

/// Where per-invocation overhead artifacts live: their own directory, apart
/// from both the per-slice raw evidence and the warm-marginal artifacts.
pub(crate) const OVERHEAD_ROOT: &str = "reports/raw/invocation-overhead";

/// How many times each measurement is repeated. A source constant, so the
/// count is a property of the method rather than of any one run, and every
/// repeat is retained and published.
pub(crate) const OVERHEAD_REPEATS: usize = 3;

/// The trivial no-flow fixture, per language.
///
/// Each declares the benchmark's own `dfb_source` / `dfb_sink` endpoint
/// contract — so the committed policy, rule or query resolves exactly as it
/// does on a real case — with a body that calls the sink on a constant and
/// never connects the two. There is no flow to find, so what the invocation
/// costs is very nearly all fixed cost.
///
/// The JVM fixtures declare the same packages the corpus fixtures do
/// (`dataflowbench.taint` for Java, `dataflowbench` for Kotlin), because the
/// OpenTaint and FlowDroid adapters resolve package directories and manifest
/// packages from them; a fixture in a package the adapter does not expect
/// would be a different invocation, not a trivial one. Each also declares a
/// single no-argument `run`, which is the entry shape FlowDroid's committed
/// wrapper template invokes.
///
/// These are NOT cases. They carry no `case.json`, no template identity, no
/// polarity and no score tier, they live outside `cases/`, and no population,
/// denominator or freeze sees them.
pub(crate) fn trivial_fixture(language: OverheadLanguage) -> (&'static str, &'static str) {
    match language {
        OverheadLanguage::Java => (
            "DfbTrivial.java",
            "package dataflowbench.taint;\n\
             \n\
             final class DfbTrivial {\n\
             \x20   static int dfb_source() { // DFB-SOURCE: trivial-overhead-input\n\
             \x20       return 1;\n\
             \x20   }\n\
             \n\
             \x20   static void dfb_sink(int value) { } // DFB-SINK: trivial-overhead-sink\n\
             \n\
             \x20   static void run() {\n\
             \x20       dfb_source();\n\
             \x20       dfb_sink(0);\n\
             \x20   }\n\
             }\n",
        ),
        OverheadLanguage::Kotlin => (
            "DfbTrivial.kt",
            "package dataflowbench\n\
             \n\
             object DfbTrivial {\n\
             \x20   fun dfb_source(): Int { // DFB-SOURCE: trivial-overhead-input\n\
             \x20       return 1\n\
             \x20   }\n\
             \n\
             \x20   fun dfb_sink(value: Int) {} // DFB-SINK: trivial-overhead-sink\n\
             \n\
             \x20   fun run() {\n\
             \x20       dfb_source()\n\
             \x20       dfb_sink(0)\n\
             \x20   }\n\
             }\n",
        ),
        OverheadLanguage::Python => (
            "dfb_trivial.py",
            "def dfb_source():  # DFB-SOURCE: trivial-overhead-input\n\
             \x20   return 1\n\
             \n\
             \n\
             def dfb_sink(value):  # DFB-SINK: trivial-overhead-sink\n\
             \x20   pass\n\
             \n\
             \n\
             def run():\n\
             \x20   dfb_source()\n\
             \x20   dfb_sink(0)\n",
        ),
        OverheadLanguage::Ruby => (
            "dfb_trivial.rb",
            "def dfb_source # DFB-SOURCE: trivial-overhead-input\n\
             \x20 1\n\
             end\n\
             \n\
             def dfb_sink(value) # DFB-SINK: trivial-overhead-sink\n\
             end\n\
             \n\
             def run\n\
             \x20 dfb_source\n\
             \x20 dfb_sink(0)\n\
             end\n",
        ),
        OverheadLanguage::Php => (
            "dfb_trivial.php",
            "<?php\n\
             function dfb_source(): string { // DFB-SOURCE: trivial-overhead-input\n\
             \x20   return \"tainted\";\n\
             }\n\
             \n\
             function dfb_sink(string $value): void {} // DFB-SINK: trivial-overhead-sink\n\
             \n\
             function run(): void {\n\
             \x20   dfb_source();\n\
             \x20   dfb_sink(\"clean\");\n\
             }\n",
        ),
        OverheadLanguage::C => (
            "dfb_trivial.c",
            "int dfb_source(void) { // DFB-SOURCE: trivial-overhead-input\n\
             \x20   return 1;\n\
             }\n\
             \n\
             void dfb_sink(int value) {} // DFB-SINK: trivial-overhead-sink\n\
             \n\
             void run(void) {\n\
             \x20   dfb_source();\n\
             \x20   dfb_sink(0);\n\
             }\n",
        ),
    }
}

/// One run of the estimator: the phases of one complete adapter invocation.
#[derive(Clone, Debug)]
pub(crate) struct OverheadRun {
    /// Adapter-observable phases, in invocation order. One entry for the
    /// single-subprocess adapters; CodeQL's two for CodeQL.
    pub(crate) phases: Vec<(String, u64)>,
    /// The whole invocation: the sum of the phases, exactly as the cold
    /// whole-invocation figure is derived.
    pub(crate) wall_ms: u64,
    /// The machine's one-minute load average, sampled immediately before the
    /// first subprocess of this run was spawned.
    pub(crate) load_before: Option<f64>,
}

/// The published figure: the range the repeats span.
///
/// Not a mean, not a chosen repeat, and not a figure gated on the repeats
/// agreeing. The width is the measurement's precision — a wide range says the
/// estimate is imprecise, which is a thing a reader is entitled to see rather
/// than a reason to publish nothing.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub(crate) struct OverheadRange {
    pub(crate) low_ms: u64,
    pub(crate) high_ms: u64,
}

pub(crate) fn overhead_range(runs: &[OverheadRun]) -> Result<OverheadRange> {
    let low_ms = runs
        .iter()
        .map(|run| run.wall_ms)
        .min()
        .context("a range needs at least one repeat")?;
    let high_ms = runs
        .iter()
        .map(|run| run.wall_ms)
        .max()
        .expect("non-empty, checked above");
    Ok(OverheadRange { low_ms, high_ms })
}

/// Run one adapter's estimator twice and retain the artifact.
/// Every distribution an overhead arm may need.
///
/// One struct rather than a per-tool argument list, because the command takes
/// them all and each arm reaches for the ones its own cold runner uses. The
/// paths are exactly the ones the kernel runners take, and every arm witnesses
/// the pinned identity through the same function its kernel does — so a wrong
/// jar, binary or venv refuses the measurement instead of producing a number
/// attributed to a distribution that did not make it.
pub(crate) struct OverheadTools {
    pub(crate) joern: PathBuf,
    pub(crate) semgrep: PathBuf,
    pub(crate) bifrost: PathBuf,
    pub(crate) codeql: PathBuf,
    pub(crate) codeql_packs: Option<PathBuf>,
    pub(crate) infer: PathBuf,
    pub(crate) analyzer_jar: PathBuf,
    pub(crate) models_archive: PathBuf,
    pub(crate) flowdroid_jar: PathBuf,
    pub(crate) android_platform: PathBuf,
    pub(crate) d8_jar: PathBuf,
    pub(crate) java: PathBuf,
    pub(crate) javac: PathBuf,
    pub(crate) kotlinc: PathBuf,
    pub(crate) kotlin_stdlib: PathBuf,
    pub(crate) pyre: PathBuf,
    pub(crate) pyre_binary: PathBuf,
    pub(crate) pyrefly: PathBuf,
}

pub(crate) fn estimate_invocation_overhead(
    tool: OverheadTool,
    language: OverheadLanguage,
    tools: &OverheadTools,
) -> Result<()> {
    let binary: &Path = match tool {
        OverheadTool::Joern => &tools.joern,
        OverheadTool::Semgrep => &tools.semgrep,
        OverheadTool::Bifrost => &tools.bifrost,
        OverheadTool::Codeql => &tools.codeql,
        OverheadTool::Infer => &tools.infer,
        OverheadTool::Opentaint => &tools.analyzer_jar,
        OverheadTool::Flowdroid => &tools.flowdroid_jar,
        OverheadTool::Pysa => &tools.pyre,
    };
    let codeql_packs = tools.codeql_packs.as_deref();
    let raw_dir =
        PathBuf::from(OVERHEAD_ROOT).join(format!("{}-{}", tool.as_str(), language.as_str()));
    if raw_dir.exists() {
        fs::remove_dir_all(&raw_dir).with_context(|| format!("clear {}", raw_dir.display()))?;
    }
    fs::create_dir_all(&raw_dir)?;

    // Identity is witnessed from the binary and stamped exactly as every other
    // run stamps it.
    let identity = match tool {
        OverheadTool::Joern => joern_version_identity(binary)?,
        OverheadTool::Semgrep => semgrep_version_identity(binary)?,
        OverheadTool::Codeql => codeql_version_identity(binary)?,
        OverheadTool::Bifrost => ToolIdentity::new(
            command_output(Command::new(binary).arg("--version"))
                .unwrap_or_else(|_| "unknown".into()),
            command_output(Command::new(binary).arg("--build-identity"))
                .unwrap_or_else(|_| "unknown".into()),
        ),
        // The four JVM-and-Python distributions witness their identity exactly
        // as their kernels do — Infer against its pinned version and binary
        // digest, OpenTaint and FlowDroid against their jar digests, Pysa
        // against the pinned client, analysis binary and Pyrefly build. A
        // measurement can therefore never be attributed to a distribution the
        // runner did not verify.
        OverheadTool::Infer => witness_infer_identity(binary)?,
        OverheadTool::Opentaint => witness_opentaint_identity(binary, &tools.models_archive)?,
        OverheadTool::Flowdroid => witness_flowdroid_identity(binary, &tools.android_platform)?,
        OverheadTool::Pysa => witness_pysa_identity(&PysaTools {
            pyre: tools.pyre.clone(),
            pyre_binary: tools.pyre_binary.clone(),
            pyrefly: tools.pyrefly.clone(),
        })?,
    };
    write_run_environment(&raw_dir, tool.as_str(), &identity)?;

    // The fixture is retained beside the artifact so a reader can see exactly
    // what was analyzed, and is written before any subprocess is spawned:
    // fixture materialization is outside every timed window, warm and cold
    // alike, by this tier's own exclusion list.
    let (fixture_name, fixture_text) = trivial_fixture(language);
    let retained_fixture = raw_dir.join("fixture");
    fs::create_dir_all(&retained_fixture)?;
    fs::write(retained_fixture.join(fixture_name), fixture_text)?;

    let started = now_seconds()?;
    let mut runs = Vec::new();
    for run in 1..=OVERHEAD_REPEATS {
        println!(
            "estimating {} {} per-invocation overhead, repeat {run} of {OVERHEAD_REPEATS}",
            tool.as_str(),
            language.as_str()
        );
        let measured = match tool {
            OverheadTool::Joern => overhead_run_joern(binary, language, run)?,
            OverheadTool::Semgrep => overhead_run_semgrep(binary, language, run, &raw_dir)?,
            OverheadTool::Bifrost => overhead_run_bifrost(binary, language, run)?,
            OverheadTool::Codeql => overhead_run_codeql(binary, codeql_packs, language, run)?,
            OverheadTool::Infer => overhead_run_infer(binary, language, run)?,
            OverheadTool::Opentaint => overhead_run_opentaint(tools, language, run, &raw_dir)?,
            OverheadTool::Flowdroid => overhead_run_flowdroid(tools, language, run, &raw_dir)?,
            OverheadTool::Pysa => overhead_run_pysa(tools, language, run, &raw_dir)?,
        };
        println!("  repeat {run}: {} ms", measured.wall_ms);
        runs.push(measured);
    }

    // The published figure. Every repeat is retained above it, and the width
    // of the range is the precision the measurement actually has.
    let range = overhead_range(&runs)?;

    let document = json!({
        "schema_version": 1,
        "evidence_kind": "retained-invocation-overhead-estimate",
        "amendment": "A24",
        "adapter": tool.as_str(),
        "language": language.as_str(),
        "tool_version": identity.version,
        "tool_build_identity": identity.build_identity,
        "estimator": "one complete adapter invocation over a trivial no-flow fixture",
        "estimate_bias": "upper bound on start-up and warm-up: it contains the trivial fixture's \
                          own near-zero analysis, and it is a cold single-shot execution — the \
                          same posture the cold rows are measured in, and not a steady-state one",
        "clock": "monotonic",
        "measured_boundary": "the adapter's own subprocess boundaries; the estimate is the sum of \
                              its declared phases, as the cold whole-invocation figure is",
        "fixture_file": format!("fixture/{fixture_name}"),
        "fixture_sha256": format!("{:x}", Sha256::digest(fixture_text.as_bytes())),
        "publication": "range over every repeat; never a mean, never a chosen repeat, and never \
                        gated on the repeats agreeing — the width is the precision",
        "repeats": OVERHEAD_REPEATS,
        "runs": runs.iter().enumerate().map(|(index, run)| json!({
            "repeat": index + 1,
            "wall_ms": run.wall_ms,
            "phases": run.phases.iter().map(|(phase, wall_ms)| json!({
                "phase": phase,
                "wall_ms": wall_ms,
            })).collect::<Vec<_>>(),
            "load_average_1m_before": run.load_before,
        })).collect::<Vec<_>>(),
        "estimated_overhead_ms": {
            "low": range.low_ms,
            "high": range.high_ms,
        },
        "started_at_unix_seconds": started,
        "ended_at_unix_seconds": now_seconds()?,
    });
    let path = raw_dir.join("invocation-overhead.json");
    fs::write(&path, serde_json::to_string_pretty(&document)? + "\n")?;
    println!(
        "wrote {} — estimated per-invocation overhead {} to {} ms over {OVERHEAD_REPEATS} repeats",
        path.display(),
        range.low_ms,
        range.high_ms
    );
    Ok(())
}

/// A scratch root for one overhead run, holding the trivial fixture.
pub(crate) fn overhead_workspace(
    tool: OverheadTool,
    language: OverheadLanguage,
    run: usize,
) -> Result<(PathBuf, PathBuf)> {
    let scratch = std::env::temp_dir().join(format!(
        "dataflowbench-overhead-{}-{}-{run}",
        tool.as_str(),
        language.as_str()
    ));
    if scratch.exists() {
        fs::remove_dir_all(&scratch)?;
    }
    fs::create_dir_all(&scratch)?;
    let workspace = scratch.join("source");
    fs::create_dir_all(&workspace)?;
    let (name, text) = trivial_fixture(language);
    fs::write(workspace.join(name), text)?;
    Ok((scratch, workspace))
}
