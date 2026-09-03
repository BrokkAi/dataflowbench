// Build-time derivation of the latency-characterization tier.
//
// Every number this module returns is read from a snapshot-selected archive of
// the repository's frozen evidence: the generated results model gates the case
// population, retained per-case timing sidecars supply wall-clock, and retained
// environment stamps supply the scope. Nothing here is hand-entered, and no
// correctness classification enters a latency calculation.
//
// The governing contract is `docs/latency-tier.md`, whose per-adapter
// granularity table (as amended by A12 for the four adapters added in v0.6.0)
// declares exactly which phases each adapter may be decomposed into. This
// module reports the phases the artifacts carry and labels the granularity
// per adapter; it never invents a phase split, never sums phases across
// adapters, and never presents a phase of one adapter beside a total of
// another.
import v060LatencyEvidence from './archive/v0-6-0-latency-evidence.json';
import {
  coreKernelPopulations,
  currentSnapshot,
  snapshotByVersion,
  type ResultsModel,
  type Snapshot,
} from './snapshots';
import {
  contractTiming,
  isComparableAnalyzerPhase,
  type TimingPhase,
} from './latency-contract';

export interface Distribution {
  /** Timed invocations behind the numbers. */
  n: number;
  min: number;
  p10: number;
  q1: number;
  median: number;
  q3: number;
  p90: number;
  max: number;
}

export interface PhaseDistribution extends Distribution {
  phase: string;
  /** Whether A20 permits this phase to enter the cross-adapter total. */
  includedInAnalyzerTotal: boolean;
}

export interface LatencySlice {
  /** The bound report this slice is: one adapter, one language, one population. */
  report: string;
  /** Adapter tool identifier, for the vendor colour identity map. */
  tool: string;
  toolVersion: string;
  language: string;
  scoreTier: string;
  modelProfile: string;
  subprocessesPerCase: number;
  /** Cases the freeze binds for this report. */
  cases: number;
  /** Of those, cases that actually invoked the analyzer and were timed. */
  timed: number;
  /** Comparable analyzer wall-clock selected by the phase contract. */
  whole: Distribution | null;
  /** Declared phases, in the adapter's own order. Empty when it exposes one. */
  phases: PhaseDistribution[];
}

export interface LatencyAdapter {
  tool: string;
  toolVersion: string;
  /** Distinct build identities witnessed for this tool across its runs. */
  buildIdentities: string[];
  subprocessesPerCase: string;
  /** `total`, or the adapter's declared phase names. */
  granularity: string[];
  timed: number;
  whole: Distribution;
  phases: PhaseDistribution[];
  slices: LatencySlice[];
}

export interface EnvironmentStamp {
  hardwareModel: string;
  os: string;
  osRelease: string;
  cpuCount: number;
  cpuArchitecture: string;
  /** Runs (report directories) stamped with exactly this environment. */
  runs: number;
}

export interface LatencyModel {
  /** Release this was derived from, read from the freeze manifest. */
  release: string;
  /** Freeze manifest digest, so the page states its own provenance. */
  manifestSha256: string;
  environments: EnvironmentStamp[];
  adapters: LatencyAdapter[];
  totalTimed: number;
  /** Bound cases with no timing, because they never invoked the analyzer. */
  totalUntimed: number;
  /** Outcomes those untimed cases carry — expected to be `unsupported` only. */
  untimedOutcomes: { outcome: string; cases: number }[];
}

interface ArchivedLatencyEvidence {
  schema_version: number;
  evidence_ref: string;
  release: string;
  benchmark_revision: string;
  manifest_sha256: string;
  timings: Record<string, { phases: TimingPhase[] }>;
  environments: Record<string, any | null>;
}

interface LatencySource {
  results: ResultsModel;
  evidence: ArchivedLatencyEvidence;
}

const latencyEvidenceByRelease: Record<string, ArchivedLatencyEvidence> = {
  'v0.6.0': v060LatencyEvidence as ArchivedLatencyEvidence,
};

function latencySource(snapshot: Snapshot): LatencySource {
  const release = snapshot.latencyEvidenceRelease;
  if (!release) throw new Error(`${snapshot.version} has no latency corpus`);
  const source = snapshotByVersion(release);
  const evidence = latencyEvidenceByRelease[release];
  if (!evidence) throw new Error(`${release} has no archived latency evidence`);
  if (
    evidence.release !== source.version ||
    evidence.evidence_ref !== source.evidenceRef ||
    evidence.manifest_sha256 !== source.results.manifest.sha256
  ) {
    throw new Error(
      `${release}: latency evidence does not match its frozen snapshot`,
    );
  }
  return { results: source.results, evidence };
}

/**
 * Separator used only to group environment stamps by exact machine identity.
 */
const KEY_SEPARATOR = '\u0000';

/**
 * Linear-interpolation quantile, and the plain median. The contract headlines
 * medians and distributions and explicitly headlines no mean, because the
 * distributions are expected to be skewed by per-invocation fixed costs.
 */
function distribution(values: number[]): Distribution {
  const sorted = [...values].sort((left, right) => left - right);
  const n = sorted.length;
  const quantile = (p: number) => {
    if (n === 1) return sorted[0]!;
    const position = p * (n - 1);
    const low = Math.floor(position);
    const high = Math.min(low + 1, n - 1);
    return sorted[low]! + (sorted[high]! - sorted[low]!) * (position - low);
  };
  return {
    n,
    min: sorted[0]!,
    p10: quantile(0.1),
    q1: quantile(0.25),
    median: quantile(0.5),
    q3: quantile(0.75),
    p90: quantile(0.9),
    max: sorted[n - 1]!,
  };
}

/**
 * Timing records are read only from the archived bundle selected by the
 * snapshot's explicit latency release. The archived results model supplies
 * the exact freeze-bound report and case population.
 */
interface CaseTiming {
  phases: TimingPhase[];
  includedPhaseNames: Set<string>;
  /** Cross-adapter analyzer wall-clock selected by the phase contract. */
  whole: number;
}

/**
 * One case's timing sidecar, or `null` when the freeze does not bind the case
 * or the case never invoked an analyzer (and so has nothing to time).
 */
function readTiming(
  evidence: ArchivedLatencyEvidence,
  tool: string,
  scoreTier: string,
  caseId: string,
  rawEvidencePath: string | undefined,
): CaseTiming | null {
  if (!rawEvidencePath) return null;
  const separator = rawEvidencePath.lastIndexOf('/');
  const directory = rawEvidencePath.slice(0, separator);
  const sidecar = `${directory}/${caseId}-timing.json`;
  const timing = evidence.timings[sidecar];
  if (!timing) return null;
  const derived = contractTiming(tool, scoreTier, timing.phases);
  return {
    phases: derived.phases,
    includedPhaseNames: new Set(
      timing.phases
        .filter((phase) =>
          isComparableAnalyzerPhase(tool, scoreTier, phase.phase),
        )
        .map((phase) => phase.phase),
    ),
    whole: derived.analyzerWallMs,
  };
}

/**
 * The tier's freeze gate, made mechanical: a timing sidecar reaches a
 * published number only if the manifest binds that report *and* that case.
 * A sidecar left in the tree by an unbound run cannot be read.
 */
export function latencyModel(
  snapshot: Snapshot = currentSnapshot,
): LatencyModel {
  const { results, evidence } = latencySource(snapshot);

  const rawDirectories = new Set<string>();
  const slices: LatencySlice[] = [];
  const untimed = new Map<string, number>();
  let totalTimed = 0;
  let totalUntimed = 0;

  for (const card of results.scorecards) {
    const reportPath = card.report.path;

    const phaseValues = new Map<string, number[]>();
    const phaseOrder: string[] = [];
    const includedPhases = new Set<string>();
    const wholeValues: number[] = [];
    let timed = 0;
    let cases = 0;

    for (const language of card.languages) {
      for (const tier of language.score_tiers) {
        for (const result of tier.cases) {
          cases += 1;
          const timing = readTiming(
            evidence,
            card.adapter.tool,
            tier.score_tier,
            result.case_id,
            result.raw_evidence?.path,
          );
          if (!timing) {
            totalUntimed += 1;
            untimed.set(result.outcome, (untimed.get(result.outcome) ?? 0) + 1);
            continue;
          }
          const rawPath = result.raw_evidence.path;
          rawDirectories.add(rawPath.slice(0, rawPath.lastIndexOf('/')));
          timed += 1;
          totalTimed += 1;
          for (const phase of timing.phases) {
            if (!phaseValues.has(phase.phase)) {
              phaseValues.set(phase.phase, []);
              phaseOrder.push(phase.phase);
            }
            phaseValues.get(phase.phase)!.push(phase.wall_ms);
            if (timing.includedPhaseNames.has(phase.phase)) {
              includedPhases.add(phase.phase);
            }
          }
          wholeValues.push(timing.whole);
        }
      }
    }

    const language = card.languages[0];
    slices.push({
      report: reportPath,
      tool: card.adapter.tool,
      toolVersion: card.adapter.tool_version,
      language:
        card.languages.length > 1
          ? `${card.languages.length} languages`
          : (language?.language ?? 'n/a'),
      scoreTier:
        card.languages.length === 1 && language.score_tiers.length === 1
          ? language.score_tiers[0].score_tier
          : language.score_tiers.map((tier: any) => tier.score_tier).join(', '),
      modelProfile: card.model_profile ?? card.adapter.model_profile,
      subprocessesPerCase: phaseOrder.length || (timed > 0 ? 1 : 0),
      cases,
      timed,
      whole: wholeValues.length > 0 ? distribution(wholeValues) : null,
      // A single-phase adapter's one phase is its analyzer total; listing it
      // twice would invent a decomposition it does not have.
      phases:
        phaseOrder.length > 1
          ? phaseOrder.map((phase) => ({
              phase,
              includedInAnalyzerTotal: includedPhases.has(phase),
              ...distribution(phaseValues.get(phase)!),
            }))
          : [],
    });
  }

  // Per-adapter aggregation across every slice the adapter owns.
  const byTool = new Map<string, LatencySlice[]>();
  for (const slice of slices) {
    byTool.set(slice.tool, [...(byTool.get(slice.tool) ?? []), slice]);
  }

  const buildIdentities = new Map<string, Set<string>>();
  for (const card of results.scorecards) {
    const tool = card.adapter.tool;
    if (!buildIdentities.has(tool)) buildIdentities.set(tool, new Set());
    // The build identity is extended for the native rows with the activated
    // ruleset; the binary identity is the part before the em dash.
    buildIdentities
      .get(tool)!
      .add(String(card.adapter.build_identity).split(' — ')[0]!);
  }

  const adapters: LatencyAdapter[] = [];
  for (const [tool, toolSlices] of byTool) {
    const wholeValues: number[] = [];
    const phaseValues = new Map<string, number[]>();
    const phaseOrder: string[] = [];
    const includedPhases = new Set<string>();
    let timed = 0;
    for (const slice of toolSlices) {
      timed += slice.timed;
    }
    if (timed === 0) continue;
    // Re-read at adapter granularity rather than pooling slice summaries: a
    // median of medians is not a median.
    for (const slice of toolSlices) {
      const card = results.scorecards.find(
        (candidate) => candidate.report.path === slice.report,
      )!;
      for (const language of card.languages) {
        for (const tier of language.score_tiers) {
          for (const result of tier.cases) {
            const timing = readTiming(
              evidence,
              card.adapter.tool,
              tier.score_tier,
              result.case_id,
              result.raw_evidence?.path,
            );
            if (!timing) continue;
            for (const phase of timing.phases) {
              if (!phaseValues.has(phase.phase)) {
                phaseValues.set(phase.phase, []);
                phaseOrder.push(phase.phase);
              }
              phaseValues.get(phase.phase)!.push(phase.wall_ms);
              if (timing.includedPhaseNames.has(phase.phase)) {
                includedPhases.add(phase.phase);
              }
            }
            wholeValues.push(timing.whole);
          }
        }
      }
    }
    const decomposed = phaseOrder.length > 1;
    adapters.push({
      tool,
      toolVersion: toolSlices[0]!.toolVersion,
      buildIdentities: [...(buildIdentities.get(tool) ?? [])].sort(),
      subprocessesPerCase: [
        ...new Set(toolSlices.map((slice) => slice.subprocessesPerCase)),
      ]
        .sort((left, right) => left - right)
        .join(' or '),
      granularity: decomposed ? phaseOrder : ['total'],
      timed,
      whole: distribution(wholeValues),
      phases: decomposed
        ? phaseOrder.map((phase) => ({
            phase,
            includedInAnalyzerTotal: includedPhases.has(phase),
            ...distribution(phaseValues.get(phase)!),
          }))
        : [],
      slices: toolSlices.sort(
        (left, right) =>
          left.language.localeCompare(right.language) ||
          left.report.localeCompare(right.report),
      ),
    });
  }

  // The environment stamp, read verbatim and grouped: if two runs disagree
  // the page shows both rather than averaging across machines.
  const environments = new Map<string, EnvironmentStamp>();
  for (const directory of [...rawDirectories].sort()) {
    const value = evidence.environments[directory];
    if (!value) continue;
    const key = [
      value.hardware_model,
      value.os,
      value.os_release,
      value.cpu_count,
      value.cpu_architecture,
    ].join(KEY_SEPARATOR);
    const existing = environments.get(key);
    if (existing) {
      existing.runs += 1;
      continue;
    }
    environments.set(key, {
      hardwareModel: value.hardware_model,
      os: value.os,
      osRelease: value.os_release,
      cpuCount: value.cpu_count,
      cpuArchitecture: value.cpu_architecture,
      runs: 1,
    });
  }

  return {
    release: evidence.release,
    manifestSha256: evidence.manifest_sha256,
    environments: [...environments.values()],
    adapters: adapters.sort((left, right) =>
      left.whole.median === right.whole.median
        ? left.tool.localeCompare(right.tool)
        : left.whole.median - right.whole.median,
    ),
    totalTimed,
    totalUntimed,
    untimedOutcomes: [...untimed.entries()]
      .map(([outcome, cases]) => ({ outcome, cases }))
      .sort((left, right) => right.cases - left.cases),
  };
}

/**
 * Milliseconds as a human figure, without ever implying sub-millisecond
 * precision.
 *
 * The rounding is done on the integer millisecond count and only then scaled,
 * rather than dividing first and calling `toFixed`. `toFixed` rounds off the
 * IEEE-754 representation, so a value that is an exact half in decimal —
 * 4475 ms, which quartiles and even-n medians produce routinely — renders one
 * unit in the last place low, and does so unpredictably. Rounding the integer
 * makes the displayed figure a deterministic function of the measurement.
 */
// ---------------------------------------------------------------------------
// The ranked view: fastest to slowest, whole-corpus and per kernel.
//
// This is presentation of the *same* aggregation the contract preregisters —
// medians and quartiles of per-case wall-clock — ordered by median so the
// spread between adapters is legible. It adds no new statistic, no pooling
// with correctness, and no composite of any kind. An adapter that never
// invoked on a kernel is absent from that kernel's view rather than entered
// as a zero, because a decline is not a fast answer.
// ---------------------------------------------------------------------------

export interface RankedEntry {
  tool: string;
  toolVersion: string;
  /** Invocations behind this entry's distribution. */
  timed: number;
  /**
   * Assertions the analyzer covers in this view's population, so a median over
   * a partly-declined kernel can never be read as a median over all of it.
   * `null` in the whole-corpus view, whose denominator is not a population.
   */
  covered: number | null;
  whole: Distribution;
  /** Declared phases, empty for the adapters that expose one subprocess. */
  phases: PhaseDistribution[];
}

export interface RankingView {
  /** `all`, or the kernel's language. */
  id: string;
  label: string;
  /** Assertions in the kernel population; `null` for the whole-corpus view. */
  population: number | null;
  /** Fastest median first. */
  entries: RankedEntry[];
}

export interface AxisTick {
  value: number;
  label: string;
}

export interface LatencyRanking {
  views: RankingView[];
  /**
   * One shared logarithmic axis across every view, so switching kernels never
   * silently rescales the picture underneath the reader.
   */
  ticks: AxisTick[];
  axisMin: number;
  axisMax: number;
}

/** The 1–3–10 decade ladder, in milliseconds. */
function tickLadder(): number[] {
  const ladder: number[] = [];
  for (let decade = 0; decade <= 7; decade += 1) {
    ladder.push(10 ** decade, 3 * 10 ** decade);
  }
  return ladder.sort((left, right) => left - right);
}

function tickLabel(ms: number): string {
  return ms < 1000 ? `${ms} ms` : `${ms / 1000} s`;
}

function rankedEntry(
  tool: string,
  toolVersion: string,
  covered: number | null,
  timings: CaseTiming[],
): RankedEntry | null {
  if (timings.length === 0) return null;
  const phaseValues = new Map<string, number[]>();
  const phaseOrder: string[] = [];
  const includedPhases = new Set<string>();
  for (const timing of timings) {
    for (const phase of timing.phases) {
      if (!phaseValues.has(phase.phase)) {
        phaseValues.set(phase.phase, []);
        phaseOrder.push(phase.phase);
      }
      phaseValues.get(phase.phase)!.push(phase.wall_ms);
      if (timing.includedPhaseNames.has(phase.phase)) {
        includedPhases.add(phase.phase);
      }
    }
  }
  return {
    tool,
    toolVersion,
    timed: timings.length,
    covered,
    whole: distribution(timings.map((timing) => timing.whole)),
    // A single-phase adapter's one phase is its analyzer total; drawing it
    // twice would invent a decomposition the adapter does not expose.
    phases:
      phaseOrder.length > 1
        ? phaseOrder.map((phase) => ({
            phase,
            includedInAnalyzerTotal: includedPhases.has(phase),
            ...distribution(phaseValues.get(phase)!),
          }))
        : [],
  };
}

/**
 * The ranked views, derived from the already-computed adapter model (for the
 * whole-corpus view) and from the benchmark-controlled kernel populations —
 * the same no-pooling population filter the landing page reads — for the
 * per-kernel views.
 *
 * The two are deliberately different denominators, and the page says so: the
 * whole-corpus view is every timed invocation in the freeze, across every tier
 * and profile, while a kernel view is that kernel's core assertions only.
 */
export function latencyRanking(model: LatencyModel): LatencyRanking {
  const { results, evidence } = latencySource(snapshotByVersion(model.release));
  const views: RankingView[] = [
    {
      id: 'all',
      label: 'All timed invocations',
      population: null,
      entries: model.adapters
        .map((adapter) => ({
          tool: adapter.tool,
          toolVersion: adapter.toolVersion,
          timed: adapter.timed,
          covered: null,
          whole: adapter.whole,
          phases: adapter.phases,
        }))
        .sort((left, right) => left.whole.median - right.whole.median),
    },
  ];

  for (const population of coreKernelPopulations(results)) {
    const entries: RankedEntry[] = [];
    for (const [tool, coverage] of population.entries) {
      const timings: CaseTiming[] = [];
      for (const result of coverage.tier.cases) {
        const timing = readTiming(
          evidence,
          coverage.card.adapter.tool,
          coverage.tier.score_tier,
          result.case_id,
          result.raw_evidence?.path,
        );
        if (timing) timings.push(timing);
      }
      const entry = rankedEntry(
        tool,
        coverage.card.adapter.tool_version,
        population.cases,
        timings,
      );
      // No entry at all when the analyzer never invoked on this kernel: an
      // absent bar, never a zero-length one.
      if (entry) entries.push(entry);
    }
    views.push({
      id: population.language,
      label: population.language,
      population: population.cases,
      entries: entries.sort(
        (left, right) => left.whole.median - right.whole.median,
      ),
    });
  }

  // The axis spans every mark any view draws — whiskers and phase marks
  // included — so one ladder serves all of them.
  const marks: number[] = [];
  for (const view of views) {
    for (const entry of view.entries) {
      marks.push(entry.whole.p10, entry.whole.p90);
      for (const phase of entry.phases) marks.push(phase.p10, phase.p90);
    }
  }
  const ladder = tickLadder();
  const lowest = Math.min(...marks);
  const highest = Math.max(...marks);
  const axisMin = [...ladder].reverse().find((tick) => tick <= lowest) ?? 1;
  const axisMax = ladder.find((tick) => tick >= highest) ?? 10 ** 8;
  return {
    views,
    axisMin,
    axisMax,
    ticks: ladder
      .filter((tick) => tick >= axisMin && tick <= axisMax)
      .map((tick) => ({ value: tick, label: tickLabel(tick) })),
  };
}

/**
 * Per tool, the distribution of analyzer-invocation wall-clock over the
 * benchmark-controlled `core` kernel populations only — not over every timed
 * invocation in the freeze.
 *
 * It exists for the one consumer that needs latency and correctness figures to
 * share a denominator: a view that shows both must show them over the *same*
 * population, or the two numbers describe two different exams. Every value is
 * computed per case and then summarized, because a median of medians is not a
 * median.
 */
export function kernelCorpusDistributions(
  snapshot: Snapshot = currentSnapshot,
): Map<string, Distribution> {
  const { results, evidence } = latencySource(snapshot);
  const values = new Map<string, number[]>();
  for (const population of coreKernelPopulations(results)) {
    for (const [tool, coverage] of population.entries) {
      for (const result of coverage.tier.cases) {
        const timing = readTiming(
          evidence,
          coverage.card.adapter.tool,
          coverage.tier.score_tier,
          result.case_id,
          result.raw_evidence?.path,
        );
        if (!timing) continue;
        values.set(tool, [...(values.get(tool) ?? []), timing.whole]);
      }
    }
  }
  return new Map(
    [...values.entries()].map(([tool, list]) => [tool, distribution(list)]),
  );
}

export function formatMs(value: number): string {
  const ms = Math.round(value);
  if (ms < 1000) return `${ms} ms`;
  if (ms < 10_000) return `${(Math.round(ms / 10) / 100).toFixed(2)} s`;
  return `${(Math.round(ms / 100) / 10).toFixed(1)} s`;
}
