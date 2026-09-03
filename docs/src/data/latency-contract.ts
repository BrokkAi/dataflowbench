export interface TimingPhase {
  phase: string;
  wall_ms: number;
}

interface PhaseContract {
  tool: string;
  scoreTier: string;
  detailPhases: readonly string[];
  comparablePhases: readonly string[];
}

/** Explicit population-level amendments to the general analyzer-phase rule. */
const PHASE_CONTRACTS: readonly PhaseContract[] = [
  {
    tool: 'flowdroid',
    scoreTier: 'modeling',
    detailPhases: ['compile', 'dex', 'analyze'],
    comparablePhases: ['analyze'],
  },
];

/**
 * Contract-driven phase selection for the cross-adapter analyzer total.
 *
 * Most rows time only analyzer subprocesses, so every retained phase belongs
 * in the comparable total. Amendment A20 is the deliberate exception:
 * FlowDroid's modeling runner exposes APK materialization as `compile` and
 * `dex`, but only `analyze` is analyzer wall-clock.
 */
export function comparableAnalyzerPhases(
  tool: string,
  scoreTier: string,
  phases: TimingPhase[],
): TimingPhase[] {
  const contract = PHASE_CONTRACTS.find(
    (candidate) =>
      candidate.tool === tool && candidate.scoreTier === scoreTier,
  );
  if (contract) {
    assertDeclaredPhases(tool, scoreTier, phases, contract.detailPhases);
    return phases.filter((phase) =>
      contract.comparablePhases.includes(phase.phase),
    );
  }
  return phases;
}

export function isComparableAnalyzerPhase(
  tool: string,
  scoreTier: string,
  phaseName: string,
): boolean {
  const contract = PHASE_CONTRACTS.find(
    (candidate) =>
      candidate.tool === tool && candidate.scoreTier === scoreTier,
  );
  return !contract || contract.comparablePhases.includes(phaseName);
}

function assertDeclaredPhases(
  tool: string,
  scoreTier: string,
  phases: TimingPhase[],
  expected: readonly string[],
): void {
  const actual = phases.map((phase) => phase.phase);
  if (
    actual.length !== expected.length ||
    actual.some((phase, index) => phase !== expected[index])
  ) {
    throw new Error(
      `${tool}/${scoreTier}: expected retained phases ${expected.join(', ')}, got ${actual.join(', ')}`,
    );
  }
}

export function comparableAnalyzerWallMs(
  tool: string,
  scoreTier: string,
  phases: TimingPhase[],
): number {
  const comparable = comparableAnalyzerPhases(tool, scoreTier, phases);
  if (comparable.length === 0) {
    throw new Error(
      `${tool}/${scoreTier}: retained timing has no phase eligible for the comparable analyzer total`,
    );
  }
  return comparable.reduce((total, phase) => total + phase.wall_ms, 0);
}

export function contractTiming(
  tool: string,
  scoreTier: string,
  phases: TimingPhase[],
): { phases: TimingPhase[]; analyzerWallMs: number } {
  return {
    phases,
    analyzerWallMs: comparableAnalyzerWallMs(tool, scoreTier, phases),
  };
}
