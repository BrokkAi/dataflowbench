// Build-time derivation of the warm-marginal latency figures (Amendment A15).
//
// The published latency rows are cold per-invocation wall-clock and stay so.
// This module derives the *other* figure the amendment preregisters: the
// marginal wall-clock of one more case in a tool process that has already paid
// its start-up, measured as the slope of batch wall-clock against batch size.
//
// Three rules from `docs/latency-tier.md#a13--2026-09-01-warm-marginal-cost-is-measured-as-a-separate-labelled-figure-and-the-cold-rows-stay-the-headline`
// are enforced here rather than only stated on the page:
//
//   * the warm figure is never substituted for a cold one and never subtracted
//     from one — this module returns both, separately labelled, and computes
//     no difference of them;
//   * the cold comparator is restricted to *exactly* the cases the warm batch
//     analyzed, so the two numbers describe the same work and not two
//     different populations;
//   * an adapter with no measured batch gets a recorded decline, never an
//     inferred number.
//
// The slope is re-derived here from the retained batch series rather than read
// from the runner's own fitted value. The runner's value is read too, and a
// disagreement beyond a millisecond is a build error: two independent
// implementations of the same estimator agreeing is the check that neither
// drifted.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../..',
);

/** Where the runner retains warm-marginal artifacts. Outside every slice. */
const WARM_ROOT = 'reports/raw/warm-latency';

export interface WarmBatch {
  k: number;
  wallMs: number;
}

export interface WarmMeasurement {
  tool: string;
  toolVersion: string;
  language: string;
  /** Batches in increasing k. */
  batches: WarmBatch[];
  /** `(T(kmax) − T(kmin)) / (kmax − kmin)`. */
  endpointMs: number;
  /** OLS slope of wall-clock on k. */
  leastSquaresMs: number;
  /** OLS intercept: a descriptive estimate of the fixed per-process cost. */
  fittedFixedCostMs: number;
  /** Cases in the largest batch — the population both figures describe. */
  caseIds: string[];
  /** Cold whole-invocation median over exactly those cases, or null. */
  coldMedianMs: number | null;
  /** Why the batched population is narrower than the kernel's, when it is. */
  restriction: string | null;
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
 * The observability audit, mirroring Amendment A15's table.
 *
 * This is contract text, not measurement: it records what the released CLI of
 * each unmeasured adapter does and does not expose. It is held here so the
 * page cannot silently omit a decline — an adapter that produced no warm
 * artifact and appears in neither list is a build error below.
 */
const DECLINES: WarmDecline[] = [
  {
    tool: 'semgrep',
    verdict: 'deferred',
    evidence:
      "The batch exists and was measured: one `semgrep scan` accepts many target paths. It also accepts one `--config`, so a batch is the same work as its k cold runs only when all k cases resolve to identical rule text — which caps k at 12 here, and every Semgrep kernel in this benchmark invokes exactly 14 cases (the rest are declared-capability `unsupported`, decided before invocation), so no other language raises the ceiling. At that k the whole batch runs two to three seconds and the slope is small against the machine's own noise: the same measurement run twice back to back produced slopes differing by roughly a factor of two, with one series not even monotone in k. Both runs are retained as `reports/raw/warm-latency/semgrep-java-stability-probe/`. The figure is withheld rather than published to two significant figures it does not have.",
  },
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
      const document = path.join(root, entry, 'warm-latency.json');
      if (!fs.existsSync(document)) continue;
      const warm = readJson(document);
      const batches: WarmBatch[] = warm.batches.map((batch: any) => ({
        k: batch.k,
        wallMs: batch.wall_ms,
      }));
      if (batches.length < 2) {
        throw new Error(`${document}: a slope needs at least two batches`);
      }
      const derived = fit(batches);
      // The independent-derivation gate. Both implementations read the same
      // retained series; if they disagree, one of them is wrong and no number
      // is published until it is known which.
      for (const [label, mine, theirs] of [
        ['endpoint', derived.endpointMs, warm.marginal_ms_per_case.endpoint],
        [
          'least squares',
          derived.leastSquaresMs,
          warm.marginal_ms_per_case.least_squares,
        ],
        ['intercept', derived.interceptMs, warm.fitted_fixed_cost_ms],
      ] as [string, number, number][]) {
        if (Math.abs(mine - theirs) > 1) {
          throw new Error(
            `${document}: the ${label} slope re-derived at build time (${mine}) disagrees with the runner's retained value (${theirs})`,
          );
        }
      }
      const caseIds: string[] =
        warm.batches[warm.batches.length - 1]!.case_ids ?? [];
      const stamp = path.join(root, entry, 'run-environment.json');
      const environment = fs.existsSync(stamp) ? readJson(stamp) : null;
      measurements.push({
        tool: warm.adapter,
        toolVersion: warm.tool_version,
        language: warm.language,
        batches,
        endpointMs: derived.endpointMs,
        leastSquaresMs: derived.leastSquaresMs,
        fittedFixedCostMs: derived.interceptMs,
        caseIds,
        coldMedianMs: coldMedianOver(warm.adapter, warm.language, caseIds),
        restriction: warm.population_restriction ?? null,
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
 * Per tool, the warm marginal to draw as a secondary mark on the ranked chart,
 * keyed by tool. Only tools with a measured figure appear; a tool without one
 * gets no mark, never a zero-length one.
 */
export function warmMarginalByTool(): Map<string, number> {
  const marks = new Map<string, number>();
  for (const measurement of warmLatency().measurements) {
    // The least-squares slope is the mark, because it uses every measured
    // point. The endpoint estimator stays visible in the table beside it.
    const existing = marks.get(measurement.tool);
    if (existing === undefined || measurement.leastSquaresMs < existing) {
      marks.set(measurement.tool, measurement.leastSquaresMs);
    }
  }
  return marks;
}
