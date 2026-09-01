// Build-time derivation of the per-invocation overhead estimates
// (Amendment A24).
//
// The published latency rows are cold per-invocation wall-clock and stay so.
// A15 measures the *warm marginal* for the one adapter whose released CLI
// exposes a batch, and refuses to estimate one for the seven that do not.
// This module carries the other quantity A24 preregisters, which every adapter
// can supply: the wall-clock of one complete adapter invocation over a trivial
// no-flow fixture — fixed overhead plus near-zero analysis, published as an
// **upper-bound estimate** and labelled an estimate everywhere it appears.
//
// Four rules from `docs/latency-tier.md#amendments` (A24) are enforced here
// rather than only stated on the page:
//
//   * the estimate is never subtracted from a cold number, never substituted
//     for one, and never used to order a row — this module computes no such
//     difference and exports no ordering;
//   * the published figure is the RANGE the repeats span — the same convention
//     the warm-marginal figures publish under, shared rather than re-derived.
//     It is never a mean, never a chosen repeat, and never gated on the
//     repeats agreeing: there is no tolerance in this module, because a repeat
//     that disagrees widens the range, which is the honest consequence. The
//     range is re-derived here from the retained repeats and a disagreement
//     with the runner's own value is a build error;
//   * every one of the eight adapters is accounted for — measured, or recorded
//     with the reason there is no figure — so a missing row can never read as
//     an omission;
//   * a chart mark is drawn only above the preregistered significance
//     threshold, applied to the range's LOWER bound so that no mark can appear
//     on the strength of a noisy high repeat, and computed against exactly the
//     cold median the chart itself draws for that adapter on that kernel.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { latencyModel, latencyRanking } from './latency';

const repoRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '../../..',
);

/** Where the runner retains overhead artifacts. Outside every slice. */
const OVERHEAD_ROOT = 'reports/raw/invocation-overhead';

/**
 * A24's significance threshold for a chart mark: an estimate is drawn only
 * when the **low end** of its range is at least this share of that adapter's
 * cold whole-invocation median in the fixture's own language.
 *
 * Relative rather than absolute because the chart's axis is logarithmic and
 * its rows span two orders of magnitude: a share of the row's own median is
 * the same visual claim on every row. Applied to the low end because a mark
 * must not appear on the strength of one slow repeat. Below it the figure is
 * still published — in the table, with every other value — it simply is not
 * drawn.
 */
export const SIGNIFICANCE_SHARE = 0.25;

export interface OverheadRepeat {
  repeat: number;
  wallMs: number;
  /** The adapter's declared phases; one entry for a single-subprocess tool. */
  phases: { phase: string; wallMs: number }[];
  /** One-minute load average sampled immediately before the repeat was spawned. */
  loadBefore: number | null;
}

export interface OverheadEstimate {
  tool: string;
  toolVersion: string;
  /** The language of the trivial fixture this estimate was measured on. */
  language: string;
  repeats: OverheadRepeat[];
  /** The published figure: the range every repeat spans. */
  lowMs: number;
  highMs: number;
  /** The range's width, which is the measurement's precision. */
  widthMs: number;
  /**
   * The one-minute load averages observed across the repeats, low to high.
   *
   * A21 requires observed machine conditions to be published beside the figure
   * rather than summarized as the word "quiet", so a reader can discount a
   * number taken on a busy machine instead of taking the conditions on trust.
   * `null` only when no repeat could read a load average at all.
   */
  loadRange: [number, number] | null;
  /** Cold whole-invocation median for this adapter on this kernel. */
  coldMedianMs: number | null;
  /** The range's low end as a share of that cold median, when both exist. */
  shareOfCold: number | null;
  /** Whether the chart draws a mark for this row. */
  significant: boolean;
  fixtureFile: string;
  fixtureSha256: string;
  environment: {
    hardwareModel: string;
    os: string;
    osRelease: string;
    cpuCount: number;
    cpuArchitecture: string;
  } | null;
}

export interface OverheadDecline {
  tool: string;
  language: string;
  /** `environment`: the pinned distribution is not installed where the
   *  estimator ran, so the invocation was never attempted. It is the only
   *  decline kind: the range convention has no withhold-on-disagreement. */
  verdict: 'environment';
  evidence: string;
}

/**
 * A24's per-adapter fixture language, mirroring the amendment's table.
 *
 * This is contract text, not measurement: it records which language each
 * adapter's estimate is measured in — the language of its cheapest kernel arm
 * — and it is held here so the page cannot silently omit an adapter. An
 * adapter that produced no artifact becomes an `environment` decline below
 * rather than disappearing.
 */
const FIXTURE_LANGUAGE: { tool: string; language: string; why: string }[] = [
  { tool: 'bifrost', language: 'python', why: 'its cheapest kernel arm' },
  { tool: 'codeql', language: 'ruby', why: 'its cheapest kernel arm' },
  { tool: 'flowdroid', language: 'java', why: 'its cheapest kernel arm' },
  { tool: 'infer', language: 'c', why: 'its cheapest kernel arm' },
  { tool: 'joern', language: 'php', why: 'its cheapest kernel arm' },
  { tool: 'opentaint', language: 'kotlin', why: 'its cheapest kernel arm' },
  { tool: 'pysa', language: 'python', why: 'its only kernel arm' },
  { tool: 'semgrep', language: 'kotlin', why: 'its cheapest kernel arm' },
];

/**
 * The one deliberate addition to the cheapest-arm rule, recorded rather than
 * quietly taken: Joern is also estimated on Java, because A15's measured warm
 * marginal and its fitted fixed cost are both Java figures and a three-way
 * comparison across two languages would be a cross-population claim.
 */
const ADDITIONAL: { tool: string; language: string; why: string }[] = [
  {
    tool: 'joern',
    language: 'java',
    why: "not its cheapest arm — measured so that A15's Java warm figures have a same-language estimate to be compared against",
  },
];

export function fixtureLanguages(): { tool: string; language: string; why: string }[] {
  return [...FIXTURE_LANGUAGE, ...ADDITIONAL];
}

function readJson(absolute: string): any {
  return JSON.parse(fs.readFileSync(absolute, 'utf8'));
}

/**
 * The cold comparator: exactly the whole-invocation median the ranked chart
 * itself draws for this adapter on this kernel, so the threshold is a share of
 * the number the reader is looking at rather than of a differently-scoped one.
 */
let coldByKernel: Map<string, number> | null = null;
function coldMedianFor(tool: string, language: string): number | null {
  if (!coldByKernel) {
    coldByKernel = new Map();
    for (const view of latencyRanking(latencyModel()).views) {
      if (view.id === 'all') continue;
      for (const entry of view.entries) {
        coldByKernel.set(`${entry.tool}/${view.id}`, entry.whole.median);
      }
    }
  }
  return coldByKernel.get(`${tool}/${language}`) ?? null;
}

let cache: {
  estimates: OverheadEstimate[];
  declines: OverheadDecline[];
} | null = null;

export function invocationOverhead(): {
  estimates: OverheadEstimate[];
  declines: OverheadDecline[];
} {
  if (cache) return cache;
  const root = path.join(repoRoot, OVERHEAD_ROOT);
  const estimates: OverheadEstimate[] = [];
  const declines: OverheadDecline[] = [];

  if (fs.existsSync(root)) {
    for (const entry of fs.readdirSync(root).sort()) {
      const document = path.join(root, entry, 'invocation-overhead.json');
      if (!fs.existsSync(document)) continue;
      const raw = readJson(document);
      const repeats: OverheadRepeat[] = raw.runs.map((run: any) => {
        const phases = run.phases.map((phase: any) => ({
          phase: phase.phase,
          wallMs: phase.wall_ms,
        }));
        // The whole invocation is the sum of the adapter's declared phases,
        // exactly as the cold figure is derived. Re-derived here so a
        // two-subprocess adapter's estimate cannot silently become one phase.
        const summed = phases.reduce(
          (total: number, phase: any) => total + phase.wallMs,
          0,
        );
        if (summed !== run.wall_ms) {
          throw new Error(
            `${document}: repeat ${run.repeat}'s phases sum to ${summed} ms, but the retained whole invocation is ${run.wall_ms} ms`,
          );
        }
        return {
          repeat: run.repeat,
          wallMs: run.wall_ms,
          phases,
          loadBefore: run.load_average_1m_before ?? null,
        };
      });
      if (repeats.length !== raw.repeats || repeats.length < 2) {
        throw new Error(
          `${document}: the artifact declares ${raw.repeats} repeats and retains ${repeats.length}`,
        );
      }

      // The independent-derivation gate: the published range is recomputed
      // from the retained repeats, and any disagreement with the runner's own
      // value fails the build rather than publishing either.
      const walls = repeats.map((repeat) => repeat.wallMs);
      const lowMs = Math.min(...walls);
      const highMs = Math.max(...walls);
      for (const [label, mine, theirs] of [
        ['low end', lowMs, raw.estimated_overhead_ms?.low],
        ['high end', highMs, raw.estimated_overhead_ms?.high],
      ] as [string, number, number][]) {
        if (mine !== theirs) {
          throw new Error(
            `${document}: the range's ${label} re-derived at build time (${mine} ms) disagrees with the runner's retained value (${theirs} ms)`,
          );
        }
      }

      const stamp = path.join(root, entry, 'run-environment.json');
      const environment = fs.existsSync(stamp) ? readJson(stamp) : null;
      const coldMedianMs = coldMedianFor(raw.adapter, raw.language);
      // The threshold reads the range's LOW end, so a mark can never appear on
      // the strength of one slow repeat.
      const shareOfCold =
        coldMedianMs !== null && coldMedianMs > 0 ? lowMs / coldMedianMs : null;
      estimates.push({
        tool: raw.adapter,
        toolVersion: raw.tool_version,
        language: raw.language,
        repeats,
        lowMs,
        highMs,
        widthMs: highMs - lowMs,
        loadRange: (() => {
          const loads = repeats
            .map((repeat) => repeat.loadBefore)
            .filter((load): load is number => load !== null);
          return loads.length > 0
            ? [Math.min(...loads), Math.max(...loads)]
            : null;
        })(),
        coldMedianMs,
        shareOfCold,
        significant: shareOfCold !== null && shareOfCold >= SIGNIFICANCE_SHARE,
        fixtureFile: raw.fixture_file,
        fixtureSha256: raw.fixture_sha256,
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

  // Every adapter is accounted for: measured, or recorded with the reason
  // there is no figure. A silently missing adapter would read as an omission.
  for (const wanted of FIXTURE_LANGUAGE) {
    const measured = estimates.some(
      (estimate) =>
        estimate.tool === wanted.tool && estimate.language === wanted.language,
    );
    if (measured) continue;
    declines.push({
      tool: wanted.tool,
      language: wanted.language,
      verdict: 'environment',
      evidence: `The pinned distribution is not installed in the environment the estimator ran in, so the invocation could not be attempted. This is a fact about that machine and says nothing about the adapter's released CLI — it is not a capability decline of the warm marginal's kind, and it is resolved by re-running \`estimate-invocation-overhead --tool ${wanted.tool} --language ${wanted.language}\` where the pinned distribution is installed.`,
    });
  }

  declines.sort(
    (left, right) =>
      left.tool.localeCompare(right.tool) ||
      left.language.localeCompare(right.language),
  );
  cache = { estimates, declines };
  return cache;
}

export interface OverheadMark {
  /** The span the chart draws: the range the repeats spanned. */
  lowMs: number;
  highMs: number;
  language: string;
}

/**
 * Per tool and language, the estimate range the ranked chart may draw.
 *
 * Only estimates whose range clears A24's significance threshold at its low
 * end appear. An estimate below the threshold gets no mark — the table carries
 * every value either way, and the caption says so, because a mark that means
 * "a mark was drawn" is clutter rather than information.
 */
export function overheadMarks(): Map<string, OverheadMark> {
  const marks = new Map<string, OverheadMark>();
  for (const estimate of invocationOverhead().estimates) {
    if (!estimate.significant) continue;
    marks.set(`${estimate.tool}/${estimate.language}`, {
      lowMs: estimate.lowMs,
      highMs: estimate.highMs,
      language: estimate.language,
    });
  }
  return marks;
}

/**
 * The mark for a row in a given view.
 *
 * In a per-kernel view, which holds language fixed, only an estimate measured
 * on that same language may be drawn. In the whole-corpus view, whose rows
 * already mix languages and say so, the adapter's cheapest-arm estimate is
 * drawn and its language is named on the row.
 */
export function overheadMarkFor(
  viewId: string,
  tool: string,
): OverheadMark | null {
  const marks = overheadMarks();
  if (viewId !== 'all') return marks.get(`${tool}/${viewId}`) ?? null;
  const cheapest = FIXTURE_LANGUAGE.find((entry) => entry.tool === tool);
  if (!cheapest) return null;
  return marks.get(`${tool}/${cheapest.language}`) ?? null;
}
