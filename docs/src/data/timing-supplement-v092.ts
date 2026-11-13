// A separately published diagnostic supplement. This model is deliberately
// independent of `snapshots.ts` and the certified latency sources: it reads
// only the retained reconciliation and never registers a latency corpus.
import reconciliation from '../../../reports/timing/v0.9.2/20261113-02/reconciliation-v1/summary.json' with { type: 'json' };
import caseRows from '../../../reports/timing/v0.9.2/20261113-02/reconciliation-v1/cases.json' with { type: 'json' };

interface TimingCase {
  case_id: string;
  group: string;
  outcome: string;
  wall_ms: number | null;
}

interface Qualification {
  certified: boolean;
  contention_observed: boolean;
  initial_quiet_gate_passed: boolean;
  observation_failures: number;
  settle_skipped_after_campaign_start: boolean;
}

interface ColdSummary {
  group: string;
  qualification: Qualification;
  descendant_containment: string;
}

interface OverheadSummary {
  group: string;
  qualification: Qualification;
  repeats_ms: number[];
  range_ms: { low: number; high: number };
  upper_bound_estimate: boolean;
}

interface Reconciliation {
  schema: string;
  release_commit: string;
  frozen_manifest: { sha256: string; path: string };
  publication_eligible: boolean;
  cold: ColdSummary[];
  overhead: OverheadSummary[];
  totals: {
    blocked_cold_groups: number;
    identity_differences: number;
    outcome_changes: number;
  };
}

const source = reconciliation as Reconciliation;
const cases = caseRows as TimingCase[];

if (source.schema !== 'v092-timing-reconciliation/v1') {
  throw new Error(`unexpected timing reconciliation schema: ${source.schema}`);
}

function quantile(values: number[], probability: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((left, right) => left - right);
  const position = probability * (sorted.length - 1);
  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);
  if (lowerIndex === upperIndex) return sorted[lowerIndex];
  const weight = position - lowerIndex;
  return sorted[lowerIndex] * (1 - weight) + sorted[upperIndex] * weight;
}

function outcomeCounts(rows: TimingCase[]): Record<string, number> {
  return rows.reduce<Record<string, number>>((counts, row) => {
    counts[row.outcome] = (counts[row.outcome] ?? 0) + 1;
    return counts;
  }, {});
}

const casesByGroup = new Map<string, TimingCase[]>();
for (const row of cases) {
  if (row.wall_ms !== null && !Number.isFinite(row.wall_ms)) {
    throw new Error(`non-finite timing for ${row.group}/${row.case_id}`);
  }
  const group = casesByGroup.get(row.group) ?? [];
  group.push(row);
  casesByGroup.set(row.group, group);
}

const coldGroupIds = new Set(source.cold.map((entry) => entry.group));
for (const group of casesByGroup.keys()) {
  if (!coldGroupIds.has(group)) {
    throw new Error(`case rows have no cold summary group: ${group}`);
  }
}

const coldSlices = source.cold.map((cold) => {
  const rows = casesByGroup.get(cold.group);
  if (!rows) throw new Error(`cold summary group has no case rows: ${cold.group}`);
  const timings = rows.flatMap((row) =>
    typeof row.wall_ms === 'number' ? [row.wall_ms] : [],
  );
  const min = timings.length === 0 ? null : Math.min(...timings);
  const max = timings.length === 0 ? null : Math.max(...timings);
  return {
    group: cold.group,
    reportRows: rows.length,
    timed: timings.length,
    min,
    median: quantile(timings, 0.5),
    p90: quantile(timings, 0.9),
    max,
    outcomes: outcomeCounts(rows),
    qualification: cold.qualification,
    descendantContainment: cold.descendant_containment,
  };
});

const allOutcomes = outcomeCounts(cases);
const timedRows = cases.filter((row) => typeof row.wall_ms === 'number').length;
const allQualificationRecords = [
  ...source.cold.map((entry) => entry.qualification),
  ...source.overhead.map((entry) => entry.qualification),
];

export const timingSupplementV092 = {
  schema: source.schema,
  releaseCommit: source.release_commit,
  frozenManifestSha256: source.frozen_manifest.sha256,
  frozenManifestPath: source.frozen_manifest.path,
  publicationEligible: source.publication_eligible,
  coldSlices,
  totals: {
    reportRows: cases.length,
    timedRows,
    untimedRows: cases.length - timedRows,
    outcomes: allOutcomes,
    completedColdGroups: source.cold.length,
    blockedColdGroups: source.totals.blocked_cold_groups,
    identityDifferences: source.totals.identity_differences,
    outcomeChanges: source.totals.outcome_changes,
    certifiedGroups: allQualificationRecords.filter((entry) => entry.certified)
      .length,
  },
  overhead: source.overhead,
  downloadBase: '/evidence/timing/v0-9-2/20261113-v1/',
  pageUrl: '/snapshots/v0-9-2/timing-20261113-v1/',
} as const;

export type TimingSupplementSlice = (typeof coldSlices)[number];
