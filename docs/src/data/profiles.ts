// Per-analyzer profiles: four independently-defined axes, derived at build
// time, for the small-multiple radars.
//
// This module is deliberately narrow about what it will and will not produce.
//
//   * **There is no composite.** Nothing here adds, averages, weights, or
//     otherwise combines two axes. Each axis is exported as its own number
//     with its own denominator, and the consumer draws four independent
//     readings that happen to share a centre. A radar's enclosed area is an
//     artifact of the axis order, not a quantity, and no code path computes
//     it.
//   * **Latency and correctness are never pooled.** `docs/latency-tier.md`
//     forbids a combined score, an efficiency-adjusted rate, and a leaderboard
//     that ranks a blend. A profile is none of those: it is four descriptive
//     figures placed side by side, each labelled with what it is over.
//   * **One population, stated.** Every axis — the latency one included — is
//     computed over the benchmark-controlled `core` kernel populations, the
//     same no-pooling filter the landing page reads. That is what makes the
//     four numbers describe the same exam rather than four different ones.
//   * **Coverage is never flattered.** Recall and precision are over each
//     tool's *own* covered slice, and the fourth axis states how big that
//     slice is, so a narrow footprint is visible on the same picture as the
//     rates it produced.
import type { Snapshot } from './snapshots';
import { coreKernelPopulations, currentSnapshot } from './snapshots';
import { kernelCorpusDistributions } from './latency';

export interface AnalyzerProfile {
  tool: string;
  /** Kernels this analyzer covers, of the snapshot's kernels. */
  kernels: number;
  /** Assertions in the kernels it covers. */
  covered: number;
  /** Positive-polarity assertions in those kernels: recall's denominator. */
  positives: number;
  truePositives: number;
  falsePositives: number;
  trueNegatives: number;
  falseNegatives: number;
  /** Non-answers on covered cases: inconclusive, unsupported, runner-error. */
  incomplete: number;
  /** Invocations behind the latency figure. */
  timed: number;
  /** Median analyzer-invocation wall-clock over the kernel populations, in ms. */
  medianMs: number | null;

  // ---- The four axes, each in [0, 1], each with its basis named. ----------
  /**
   * `truePositives ÷ positives`. Every positive-polarity assertion in the
   * kernels the analyzer covers is in the denominator, including the ones it
   * answered `inconclusive` or `unsupported`: a non-answer on a case it took
   * on is a miss, not an exemption.
   */
  recall: number | null;
  /**
   * `truePositives ÷ (truePositives + falsePositives)`. Only decided positives
   * are in the denominator; non-answers are absent from it entirely, which is
   * the opposite of how recall treats them and is the asymmetry a reader has
   * to be told about.
   */
  precision: number | null;
  /**
   * The median wall-clock, log-normalized and inverted so that faster reads as
   * larger. The scale is **absolute, not relative to this cohort**: 100 ms maps
   * to 1 and 100 s to 0, the same three decades the latency chart's axis
   * spans. Nothing here is normalized against the fastest analyzer present, so
   * adding or removing an analyzer cannot move anyone else's mark.
   */
  speed: number | null;
  /** `kernels ÷ the snapshot's kernels`. */
  coverage: number;
}

export interface ProfileModel {
  /** The snapshot's benchmark-controlled kernel count: coverage's denominator. */
  totalKernels: number;
  /** Milliseconds mapping to speed = 1 and speed = 0. */
  speedFastMs: number;
  speedSlowMs: number;
  profiles: AnalyzerProfile[];
}

const SPEED_FAST_MS = 100;
const SPEED_SLOW_MS = 100_000;

/**
 * The four axes for one snapshot. The snapshot is a parameter and not a
 * module-level constant because these radars are rendered on archived
 * snapshot pages as well as the current one: a page below `/snapshots/` shows
 * the figures its own freeze published, and re-deriving it from
 * `currentSnapshot` would rewrite every archived page on the next freeze.
 *
 * The latency axis follows the snapshot's `latencyEvidenceRelease` rather
 * than the snapshot itself, so freezes that bind the same timing corpus show
 * the same speed mark on different correctness figures — which is exactly the
 * mixed-run caveat the snapshot pages carry.
 */
export function analyzerProfiles(
  snapshot: Snapshot = currentSnapshot,
): ProfileModel {
  const populations = coreKernelPopulations(snapshot.results);
  const latency = kernelCorpusDistributions(snapshot);

  const accumulator = new Map<string, AnalyzerProfile>();
  for (const population of populations) {
    for (const [tool, coverage] of population.entries) {
      let profile = accumulator.get(tool);
      if (!profile) {
        profile = {
          tool,
          kernels: 0,
          covered: 0,
          positives: 0,
          truePositives: 0,
          falsePositives: 0,
          trueNegatives: 0,
          falseNegatives: 0,
          incomplete: 0,
          timed: 0,
          medianMs: null,
          recall: null,
          precision: null,
          speed: null,
          coverage: 0,
        };
        accumulator.set(tool, profile);
      }
      for (const result of coverage.tier.cases) {
        if (result.polarity === 'positive') profile.positives += 1;
        switch (result.classification) {
          case 'true-positive':
            profile.truePositives += 1;
            break;
          case 'false-positive':
            profile.falsePositives += 1;
            break;
          case 'true-negative':
            profile.trueNegatives += 1;
            break;
          case 'false-negative':
            profile.falseNegatives += 1;
            break;
          default:
            profile.incomplete += 1;
        }
      }
      profile.covered += population.cases;
      profile.kernels += 1;
    }
  }

  const totalKernels = populations.length;
  const logFast = Math.log10(SPEED_FAST_MS);
  const logSlow = Math.log10(SPEED_SLOW_MS);

  const profiles = [...accumulator.values()].map((profile) => {
    const distribution = latency.get(profile.tool) ?? null;
    const medianMs = distribution?.median ?? null;
    const decided = profile.truePositives + profile.falsePositives;
    return {
      ...profile,
      timed: distribution?.n ?? 0,
      medianMs,
      recall:
        profile.positives === 0
          ? null
          : profile.truePositives / profile.positives,
      precision: decided === 0 ? null : profile.truePositives / decided,
      speed:
        medianMs === null
          ? null
          : Math.min(
              1,
              Math.max(0, (logSlow - Math.log10(medianMs)) / (logSlow - logFast)),
            ),
      coverage: totalKernels === 0 ? 0 : profile.kernels / totalKernels,
    };
  });

  return {
    totalKernels,
    speedFastMs: SPEED_FAST_MS,
    speedSlowMs: SPEED_SLOW_MS,
    // Widest coverage first, then by name: an ordering that is explicitly not
    // by any axis value, so the grid cannot be read as a leaderboard.
    profiles: profiles.sort(
      (left, right) =>
        right.kernels - left.kernels || left.tool.localeCompare(right.tool),
    ),
  };
}
