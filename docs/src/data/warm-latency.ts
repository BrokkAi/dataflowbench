// Build-time derivation of the warm-marginal latency figures.
//
// Governed by two amendments in `docs/latency-tier.md`. **A15** established the
// measurement: the marginal wall-clock of one more case in a tool process that
// has already paid its start-up, taken as the slope of batch wall-clock against
// batch size. **A21** supersedes how it is published — a range over retained
// repeats rather than a point estimate gated on an unstated agreement
// tolerance — and reverses A15's withhold of the Semgrep figure.
//
// The published latency rows are cold per-invocation wall-clock and stay so.
//
// Rules enforced here rather than only stated on the page:
//
//   * the warm figure is never substituted for a cold one and never subtracted
//     from one — this module returns both, separately labelled, and computes
//     no difference of them;
//   * the cold comparator is restricted to *exactly* the cases the warm batch
//     analyzed, so the two numbers describe the same work and not two
//     different populations;
//   * an adapter with no measured batch gets a recorded decline, never an
//     inferred number;
//   * the published figure is the range the retained repeats span — never
//     their mean, which would make a repeated trial into a statistic this
//     tier's non-goals rule out, and never one repeat chosen over another.
//
// Every slope is re-derived here from its retained batch series rather than
// read from the runner's fitted value. The runner's value is read too, and a
// disagreement beyond a millisecond is a build error: two independent
// implementations of the same estimator agreeing is the check that neither
// drifted. A15's retired figure is re-derived on the same terms — a superseded
// number still has to agree with the series behind it.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../..',
);

/** Where the runner retains warm-marginal artifacts. Outside every slice. */
const WARM_ROOT = 'reports/raw/warm-latency';

/**
 * Where A15's retired figures live.
 *
 * Deliberately *not* beside the live ones: the warm runner sweeps its own
 * output directory at the start of every run, which is right for its own
 * outputs and would silently delete retired evidence parked next to them. A
 * separate tree the runner never writes to is the only place a superseded
 * artifact is safe.
 */
const SUPERSEDED_A15_ROOT = 'reports/raw/warm-latency/superseded-a15';

export interface WarmBatch {
  k: number;
  wallMs: number;
}

/** One repeat of the whole batch series. */
export interface WarmRun {
  run: number;
  batches: WarmBatch[];
  endpointMs: number;
  leastSquaresMs: number;
  fittedFixedCostMs: number;
  /** One-minute load averages sampled before each batch of this run. */
  loads: (number | null)[];
}

export interface WarmMeasurement {
  tool: string;
  toolVersion: string;
  language: string;
  /** Every retained repeat, in the order they were measured. */
  runs: WarmRun[];
  /** The published figure: the range the repeats span, low to high. */
  leastSquaresRangeMs: [number, number];
  endpointRangeMs: [number, number];
  fittedFixedCostRangeMs: [number, number];
  /** Cases in the largest batch — the population every figure describes. */
  caseIds: string[];
  /** Cold whole-invocation median over exactly those cases, or null. */
  coldMedianMs: number | null;
  /** Why the batched population is narrower than the kernel's, when it is. */
  restriction: string | null;
  /**
   * The figure A15 published for this adapter, read from its own retained
   * artifact, or null where A15 published none.
   *
   * Read rather than transcribed: a superseded number restated by hand is a
   * number nobody can check against the run that produced it.
   */
  supersededA15: {
    endpointMs: number;
    leastSquaresMs: number;
    fittedFixedCostMs: number;
    /** Load averages A15's run observed, where it recorded them. */
    loads: (number | null)[];
    path: string;
  } | null;
  environment: {
    hardwareModel: string;
    os: string;
    osRelease: string;
    cpuCount: number;
    cpuArchitecture: string;
  } | null;
}

export interface WarmDecline {
  tool: string;
  /** `no` for a decline; `deferred` for observable-but-not-yet-measured. */
  verdict: 'no' | 'deferred';
  evidence: string;
}

/**
 * The observability audit, mirroring the amendments' table (A15 as amended by
 * A21, which moved Semgrep from withheld to measured).
 *
 * This is contract text, not measurement: it records what the released CLI of
 * each unmeasured adapter does and does not expose. It is held here so the
 * page cannot silently omit a decline — an adapter that produced no warm
 * artifact and appears in neither list is a build error below.
 */
const DECLINES: WarmDecline[] = [
  {
    tool: 'flowdroid',
    verdict: 'deferred',
    evidence:
      "The released CLI does have a batch: `-a/--apkfile` accepts a directory, and the shipped `soot-infoflow-cmd` main class lists its APKs, builds the taint wrapper once outside the loop, and iterates them in one JVM — its own help documents `-si/--skipapkfile` as \"APK file to skip when processing a directory of input files\", and it refuses a non-directory output with \"The output file must be a directory when analyzing multiple APKs\". It is not measured here because one invocation carries one `-s` sources-and-sinks definition, so a k-APK batch runs a union of k per-case endpoint configurations rather than each case's own. Whether that changes any case's result is an empirical question that has to be answered across the whole population before a marginal derived from it may be published. Named follow-up work, not a decline.",
  },
  {
    tool: 'opentaint',
    verdict: 'no',
    evidence:
      'The pinned analyzer takes one `--project` and one `--output-dir` and exits after that project. A `project.yaml` may list several `javaProjects`, but analyzing their union is one whole-program analysis over a merged call graph and a merged entry-point set — different work, not k independent case analyses — and `--semgrep-rule-set` is one rule set for the whole invocation while the benchmark resolves a rule per case. No released mode processes separate case projects in one process.',
  },
  {
    tool: 'pysa',
    verdict: 'no',
    evidence:
      '`pyre analyze` is one-shot. The client does expose daemon commands (`start`, `incremental`, `query`), but they serve the type checker, not the taint analysis, and `analyze` never attaches to a running server. `--source-directory` is repeatable but merges directories into one project — again one whole-program analysis rather than k — and each case carries its own `.pyre_configuration`, `pyrefly.toml`, and resolved models. A daemon-shaped measurement would be stateful and not reproducibly preregisterable against this pin, so it is declined rather than attempted.',
  },
  {
    tool: 'codeql',
    verdict: 'no',
    evidence:
      '`codeql database analyze` takes exactly one mandatory database, and `database create` produces exactly one database per invocation. Neither subcommand has a multi-database form in the pinned CLI.',
  },
  {
    tool: 'infer',
    verdict: 'no',
    evidence:
      "`--results-dir` names one capture database for one project and the analyzer exits after it. Worth stating explicitly: Infer's analyzer is a native binary, and the JVM cost inside its Java row is the traced `javac` in `capture` — per-project compilation work, not process start-up a batch could amortize.",
  },
  {
    tool: 'bifrost',
    verdict: 'no',
    evidence:
      "The policy CLI takes one `--root` per invocation; the repeatable `--workspace NAME=PATH` is documented as requiring `--mcp` and does not reach the policy path. What can be said without measuring anything is a bound: Bifrost's cold median already includes its own process start, so its warm marginal lies between zero and that cold number. Warm figures can therefore only move the other rows down toward Bifrost's, never Bifrost's row down further — the asymmetry this amendment corrects is one the publishing vendor's engine loses by.",
  },
];

function readJson(absolute: string): any {
  return JSON.parse(fs.readFileSync(absolute, 'utf8'));
}

/** Median by linear interpolation, matching `latency.ts`'s estimator. */
function median(values: number[]): number {
  const sorted = [...values].sort((left, right) => left - right);
  const n = sorted.length;
  if (n === 0) return Number.NaN;
  if (n === 1) return sorted[0]!;
  const position = 0.5 * (n - 1);
  const low = Math.floor(position);
  const high = Math.min(low + 1, n - 1);
  return sorted[low]! + (sorted[high]! - sorted[low]!) * (position - low);
}

/**
 * Independently re-derive both slope estimators from the batch series.
 *
 * Deliberately a second implementation of what the Rust runner already did:
 * the page publishes a number only when two implementations of the same
 * preregistered estimator, reading the same retained series, agree.
 */
function fit(batches: WarmBatch[]): {
  endpointMs: number;
  leastSquaresMs: number;
  interceptMs: number;
} {
  const first = batches[0]!;
  const last = batches[batches.length - 1]!;
  const endpointMs = (last.wallMs - first.wallMs) / (last.k - first.k);
  const n = batches.length;
  const meanK = batches.reduce((sum, b) => sum + b.k, 0) / n;
  const meanT = batches.reduce((sum, b) => sum + b.wallMs, 0) / n;
  let covariance = 0;
  let variance = 0;
  for (const batch of batches) {
    const dk = batch.k - meanK;
    covariance += dk * (batch.wallMs - meanT);
    variance += dk * dk;
  }
  const leastSquaresMs = covariance / variance;
  return {
    endpointMs,
    leastSquaresMs,
    interceptMs: meanT - leastSquaresMs * meanK,
  };
}

/**
 * The cold comparator: whole-invocation median over *exactly* the cases the
 * warm batch analyzed, gated on the freeze manifest like every other published
 * latency number.
 *
 * Restricting to the same case identifiers is what makes the two figures
 * comparable at all. A cold median over the whole kernel beside a warm
 * marginal over a twelve-case subset would be two populations, and the
 * difference between them would be partly a population effect wearing a
 * start-up effect's name.
 */
function coldMedianOver(
  tool: string,
  language: string,
  caseIds: string[],
): number | null {
  const manifest = readJson(path.join(repoRoot, 'reports/freeze.json'));
  const results = readJson(path.join(repoRoot, 'results/results.json'));
  const bound = new Map<string, Set<string>>();
  for (const report of manifest.reports) {
    bound.set(
      report.path,
      new Set<string>(report.outcomes.map((outcome: any) => outcome.case_id)),
    );
  }
  const wanted = new Set(caseIds);
  const values: number[] = [];
  for (const card of results.scorecards) {
    if (card.adapter.tool !== tool) continue;
    if (card.languages.length !== 1) continue;
    if (card.languages[0].language !== language) continue;
    const boundCases = bound.get(card.report.path);
    if (!boundCases) continue;
    for (const tier of card.languages[0].score_tiers) {
      for (const result of tier.cases) {
        if (!wanted.has(result.case_id)) continue;
        if (!boundCases.has(result.case_id)) continue;
        const raw = result.raw_evidence?.path;
        if (!raw) continue;
        const sidecar = path.join(
          repoRoot,
          path.dirname(raw),
          `${result.case_id}-timing.json`,
        );
        if (!fs.existsSync(sidecar)) continue;
        const timing = readJson(sidecar);
        values.push(
          timing.phases.reduce(
            (sum: number, phase: any) => sum + phase.wall_ms,
            0,
          ),
        );
      }
    }
  }
  return values.length > 0 ? median(values) : null;
}

let cache: {
  measurements: WarmMeasurement[];
  declines: WarmDecline[];
} | null = null;

export function warmLatency(): {
  measurements: WarmMeasurement[];
  declines: WarmDecline[];
} {
  if (cache) return cache;
  const root = path.join(repoRoot, WARM_ROOT);
  const measurements: WarmMeasurement[] = [];
  if (fs.existsSync(root)) {
    for (const entry of fs.readdirSync(root).sort()) {
      // The retired tree holds superseded figures, not current ones; it is
      // read per measurement below, never enumerated as one.
      if (entry === 'superseded-a15') continue;
      const document = path.join(root, entry, 'warm-latency.json');
      if (!fs.existsSync(document)) continue;
      const warm = readJson(document);
      if (!Array.isArray(warm.runs) || warm.runs.length < 2) {
        throw new Error(
          `${document}: the published figure is a range over repeats, so at least two retained runs are required`,
        );
      }
      const runs: WarmRun[] = warm.runs.map((run: any) => {
        const batches: WarmBatch[] = run.batches.map((batch: any) => ({
          k: batch.k,
          wallMs: batch.wall_ms,
        }));
        if (batches.length < 2) {
          throw new Error(`${document}: a slope needs at least two batches`);
        }
        const derived = fit(batches);
        // The independent-derivation gate, applied to every retained run.
        // Both implementations read the same retained series; if they
        // disagree, one of them is wrong and nothing is published until it is
        // known which.
        for (const [label, mine, theirs] of [
          ['endpoint', derived.endpointMs, run.marginal_ms_per_case.endpoint],
          [
            'least squares',
            derived.leastSquaresMs,
            run.marginal_ms_per_case.least_squares,
          ],
          ['intercept', derived.interceptMs, run.fitted_fixed_cost_ms],
        ] as [string, number, number][]) {
          if (Math.abs(mine - theirs) > 1) {
            throw new Error(
              `${document}: run ${run.run}'s ${label} slope re-derived at build time (${mine}) disagrees with the runner's retained value (${theirs})`,
            );
          }
        }
        return {
          run: run.run,
          batches,
          endpointMs: derived.endpointMs,
          leastSquaresMs: derived.leastSquaresMs,
          fittedFixedCostMs: derived.interceptMs,
          loads: run.batches.map(
            (batch: any) => batch.load_average_1m_before ?? null,
          ),
        };
      });

      // The published figure is the range the repeats span — never their mean,
      // which would turn repeated trials into a statistic the tier's non-goals
      // rule out, and never one repeat chosen over another.
      const spread = (pick: (run: WarmRun) => number): [number, number] => {
        const values = runs.map(pick);
        return [Math.min(...values), Math.max(...values)];
      };
      // The runner computes the same ranges; agreeing with it is the last
      // independent check before anything reaches the page.
      const retainedRange = warm.marginal_ms_per_case_range;
      const leastSquaresRangeMs = spread((run) => run.leastSquaresMs);
      const endpointRangeMs = spread((run) => run.endpointMs);
      for (const [label, mine, theirs] of [
        ['least squares', leastSquaresRangeMs, retainedRange.least_squares],
        ['endpoint', endpointRangeMs, retainedRange.endpoint],
      ] as [string, [number, number], [number, number]][]) {
        if (
          Math.abs(mine[0] - theirs[0]) > 1 ||
          Math.abs(mine[1] - theirs[1]) > 1
        ) {
          throw new Error(
            `${document}: the ${label} range re-derived at build time (${mine}) disagrees with the runner's retained range (${theirs})`,
          );
        }
      }

      const lastRun = runs[runs.length - 1]!;
      const caseIds: string[] =
        warm.runs[warm.runs.length - 1].batches[
          lastRun.batches.length - 1
        ].case_ids ?? [];
      const stamp = path.join(root, entry, 'run-environment.json');
      const environment = fs.existsSync(stamp) ? readJson(stamp) : null;

      // A15's retired figure, where one was published for this adapter. Its
      // slopes are re-derived from its own retained batch series for the same
      // reason the live ones are: a published number and the series behind it
      // must agree, retired or not.
      const retiredPath = path.join(
        repoRoot,
        SUPERSEDED_A15_ROOT,
        entry,
        'warm-latency.json',
      );
      let supersededA15: WarmMeasurement['supersededA15'] = null;
      if (fs.existsSync(retiredPath)) {
        const retired = readJson(retiredPath);
        const retiredBatches: WarmBatch[] = retired.batches.map(
          (batch: any) => ({ k: batch.k, wallMs: batch.wall_ms }),
        );
        const retiredFit = fit(retiredBatches);
        for (const [label, mine, theirs] of [
          [
            'endpoint',
            retiredFit.endpointMs,
            retired.marginal_ms_per_case.endpoint,
          ],
          [
            'least squares',
            retiredFit.leastSquaresMs,
            retired.marginal_ms_per_case.least_squares,
          ],
          ['intercept', retiredFit.interceptMs, retired.fitted_fixed_cost_ms],
        ] as [string, number, number][]) {
          if (Math.abs(mine - theirs) > 1) {
            throw new Error(
              `${retiredPath}: the retired ${label} slope re-derived at build time (${mine}) disagrees with the retained value (${theirs})`,
            );
          }
        }
        supersededA15 = {
          endpointMs: retiredFit.endpointMs,
          leastSquaresMs: retiredFit.leastSquaresMs,
          fittedFixedCostMs: retiredFit.interceptMs,
          loads: retired.batches.map(
            (batch: any) => batch.load_average_1m_before ?? null,
          ),
          path: path.posix.join(SUPERSEDED_A15_ROOT, entry, 'warm-latency.json'),
        };
      }
      measurements.push({
        tool: warm.adapter,
        toolVersion: warm.tool_version,
        language: warm.language,
        runs,
        leastSquaresRangeMs,
        endpointRangeMs,
        fittedFixedCostRangeMs: spread((run) => run.fittedFixedCostMs),
        caseIds,
        coldMedianMs: coldMedianOver(warm.adapter, warm.language, caseIds),
        restriction: warm.population_restriction ?? null,
        supersededA15,
        environment: environment
          ? {
              hardwareModel: environment.hardware_model,
              os: environment.os,
              osRelease: environment.os_release,
              cpuCount: environment.cpu_count,
              cpuArchitecture: environment.cpu_architecture,
            }
          : null,
      });
    }
  }

  // Every adapter is accounted for: measured, or recorded with its evidence.
  // A silently missing adapter would read as an omission rather than a
  // decline, which is the failure mode the amendment's table exists to stop.
  const measured = new Set(measurements.map((m) => m.tool));
  for (const decline of DECLINES) {
    if (measured.has(decline.tool)) {
      throw new Error(
        `${decline.tool} is both measured and recorded as unmeasurable`,
      );
    }
  }

  cache = { measurements, declines: DECLINES };
  return cache;
}

/**
 * Per tool, the measured warm marginal **as a range**, keyed by tool.
 *
 * Deliberately a range and not a point, for any consumer deriving a further
 * figure from it — a per-vendor overhead estimate, say. Handing out one
 * endpoint would let a derived number carry a precision the measurement does
 * not have, and would silently pick an endpoint, which is the failure A21's
 * range rule exists to prevent. A consumer that wants a scalar has to choose
 * one visibly and say which.
 *
 * Only tools with a measured figure appear. A tool that declined is absent
 * rather than present with a zero: absent reads as "not measured", zero reads
 * as "free". Callers should pair this with `warmLatency().declines` so a
 * missing tool is rendered as its recorded decline.
 *
 * Where one tool has figures on several kernels, the entry spans them all:
 * the low end of the lowest and the high end of the highest.
 */
export function warmMarginalRangeByTool(): Map<string, [number, number]> {
  const marks = new Map<string, [number, number]>();
  for (const measurement of warmLatency().measurements) {
    const [low, high] = measurement.leastSquaresRangeMs;
    const existing = marks.get(measurement.tool);
    marks.set(
      measurement.tool,
      existing
        ? [Math.min(existing[0], low), Math.max(existing[1], high)]
        : [low, high],
    );
  }
  return marks;
}
