import assert from 'node:assert/strict';
import test from 'node:test';
import publication from '../../../reports/timing/v0.9.2/publication-20261123-01/summary.json' with { type: 'json' };
import caseRows from '../../../reports/timing/v0.9.2/publication-20261123-01/cases.json' with { type: 'json' };
import {
  formatAxisTick,
  formatTiming,
  timingOverviewAggregateRows,
  timingOverviewRows,
  timingOverviewV092,
  timingPosition,
} from './timing-overview-v092.ts';

type CaseRow = {
  case_id: string;
  group: string;
  outcome: string;
  wall_ms: number | null;
  invocation_cost_ms: number | null;
  invocation_cost_accepted: boolean;
  analysis_latency_eligible: false;
  partial: boolean;
  evidence_status: string;
  source_refs: unknown[];
};

type GroupRow = {
  group: string;
  analyzer_id: string;
  kernel: string;
  tier: string;
  evidence_status: string;
  report_rows: number;
  timed_rows: number;
  summary_ms: { min: number; median: number; p90: number; max: number } | null;
  outcomes: Record<string, number>;
  source_refs: unknown[];
};

const source = publication as unknown as {
  schema: string;
  publication_id: string;
  release_commit: string;
  version: string;
  publication_eligible: boolean;
  certified_timing: boolean;
  full_model_qualification: boolean;
  analyzer_families: unknown[];
  groups: GroupRow[];
  overhead_groups: unknown[];
  warm_families: unknown[];
  source_refs: unknown[];
};
const cases = caseRows as CaseRow[];

function quantile(values: readonly number[], probability: number): number | null {
  if (values.length === 0) return null;
  const sorted = [...values].sort((left, right) => left - right);
  const position = probability * (sorted.length - 1);
  const lowerIndex = Math.floor(position);
  const upperIndex = Math.ceil(position);
  if (lowerIndex === upperIndex) return sorted[lowerIndex] ?? null;
  const lower = sorted[lowerIndex];
  const upper = sorted[upperIndex];
  if (lower === undefined || upper === undefined) return null;
  const weight = position - lowerIndex;
  return lower * (1 - weight) + upper * weight;
}

function summarize(values: readonly number[]) {
  if (values.length === 0) return { min: null, median: null, p90: null, max: null };
  return {
    min: Math.min(...values),
    median: quantile(values, 0.5),
    p90: quantile(values, 0.9),
    max: Math.max(...values),
  };
}

const familyGroupCounts = {
  bifrost: 20,
  codeql: 18,
  joern: 13,
  semgrep: 17,
  opentaint: 4,
  infer: 5,
  flowdroid: 4,
  pysa: 3,
} as const;

test('overview is bound to the current eight-family diagnostic publication', () => {
  assert.equal(source.schema, 'v092-timing-diagnostic-publication/v1');
  assert.equal(source.publication_id, '20261123-v1');
  assert.equal(source.release_commit, '86092336d8f9ca32fe9e2c4042c2dced76c1feb1');
  assert.equal(source.version, '0.9.2');
  assert.equal(source.publication_eligible, false);
  assert.equal(source.certified_timing, false);
  assert.equal(source.full_model_qualification, false);
  assert.equal(source.analyzer_families.length, 8);
  assert.equal(source.groups.length, 84);
  assert.equal(timingOverviewV092.rows.length, 84);
  assert.equal(source.overhead_groups.length, 9);
  assert.equal(source.warm_families.length, 2);
  assert.ok(source.source_refs.length > 0);

  const observedGroupCounts = Object.fromEntries(
    Object.entries(familyGroupCounts).map(([family]) => [
      family,
      source.groups.filter((group) => group.analyzer_id === family).length,
    ]),
  );
  assert.deepEqual(observedGroupCounts, familyGroupCounts);
  assert.deepEqual(
    timingOverviewV092.summaryRows.map(({ analyzerId }) => analyzerId),
    ['bifrost', 'codeql', 'joern', 'semgrep', 'opentaint', 'infer', 'flowdroid', 'pysa'],
  );
  assert.deepEqual(
    timingOverviewV092.summaryRows.map(({ pin }) => pin),
    ['v0.15.1', '2.27.2', '4.0.660', '1.181.0', '0.4.6', 'v1.3.0', '2.15.1', '0.10.0'],
  );
});

test('all group rows retain their source dispositions and exclude unaccepted costs', () => {
  assert.deepEqual(
    timingOverviewV092.rows.map(({ group }) => group),
    source.groups.map(({ group }) => group),
  );
  assert.equal(timingOverviewV092.totals.acceptedGroups, 82);
  assert.equal(timingOverviewV092.totals.blockedGroups, 1);
  assert.equal(timingOverviewV092.totals.quarantinedGroups, 1);
  assert.equal(timingOverviewV092.totals.rawQuarantinedTimedRows, 62);
  assert.equal(timingOverviewV092.totals.certifiedGroups, 0);
  assert.equal(timingOverviewV092.totals.publicationEligible, false);

  const blocked = timingOverviewV092.rows.filter((row) => row.status === 'blocked');
  assert.equal(blocked.length, 1);
  assert.equal(blocked[0]?.analyzerId, 'codeql');
  assert.match(blocked[0]?.blocker ?? '', /Swift extractor/);

  const quarantined = timingOverviewV092.rows.filter((row) => row.status === 'quarantined');
  assert.equal(quarantined.length, 1);
  assert.equal(quarantined[0]?.analyzerId, 'joern');
  assert.match(quarantined[0]?.language ?? '', /Rust/i);
  assert.equal(quarantined[0]?.timed, 0);
  assert.equal(quarantined[0]?.min, null);
  assert.equal(quarantined[0]?.median, null);
  assert.equal(quarantined[0]?.p90, null);
  assert.equal(quarantined[0]?.max, null);

  const accepted = cases.filter((row) => row.invocation_cost_accepted);
  assert.equal(timingOverviewV092.totals.timedRows, accepted.length);
  assert.equal(
    accepted.reduce((sum, row) => sum + (row.invocation_cost_ms ?? 0), 0),
    cases.reduce((sum, row) => sum + (row.invocation_cost_accepted ? row.invocation_cost_ms ?? 0 : 0), 0),
  );
  assert.ok(cases.every((row) => row.analysis_latency_eligible === false));
  assert.ok(cases.every((row) => row.source_refs.length > 0));
});

test('the accepted Swift invocation-cost supplement stays separate from analysis latency', () => {
  const costs = timingOverviewV092.diagnosticInvocationCosts;
  assert.equal(costs.acceptedRows, 96);
  assert.equal(costs.successfulAnalysisLatencyRows, 0);
  assert.equal(costs.fullPhaseRows, 92);
  assert.equal(costs.partialRows, 4);
  assert.equal(costs.unsupportedNoInvocationRows, 12);
  assert.equal(costs.inconclusiveRows, 96);
  assert.ok(costs.sourceRefs.length > 0);

  const swiftGroup = source.groups.find(
    (group) => group.analyzer_id === 'joern' && group.kernel.toLowerCase().includes('swift'),
  );
  assert.ok(swiftGroup);
  const swiftRows = cases.filter((row) => row.group === swiftGroup.group);
  assert.equal(swiftRows.length, 108);
  assert.equal(swiftRows.filter((row) => row.invocation_cost_accepted).length, 96);
  assert.equal(swiftRows.filter((row) => row.partial && row.invocation_cost_accepted).length, 4);
  assert.equal(swiftRows.filter((row) => row.outcome === 'unsupported' && row.invocation_cost_ms === null).length, 12);
  assert.ok(swiftRows.every((row) => row.analysis_latency_eligible === false));
  assert.ok(swiftRows.filter((row) => row.invocation_cost_accepted).every((row) => row.outcome === 'inconclusive'));

  const joern = timingOverviewV092.summaryRows.find((row) => row.analyzerId === 'joern');
  assert.ok(joern);
  assert.equal(joern.partialTimedRows, 4);
});

test('family distributions are calculated from accepted invocation costs, not raw quarantined durations', () => {
  for (const row of timingOverviewV092.summaryRows) {
    const groupIds = new Set(
      source.groups.filter((group) => group.analyzer_id === row.analyzerId).map((group) => group.group),
    );
    const sourceRows = cases.filter((entry) => groupIds.has(entry.group));
    const accepted = sourceRows.filter((entry) => entry.invocation_cost_accepted);
    const values = accepted.map((entry) => entry.invocation_cost_ms as number);
    assert.equal(row.reportRows, sourceRows.length);
    assert.equal(row.timed, values.length);
    assert.deepEqual(
      { min: row.min, median: row.median, p90: row.p90, max: row.max },
      summarize(values),
    );
  }

  const quarantinedGroupIds = new Set(
    source.groups.filter((group) => group.evidence_status === 'quarantined').map((group) => group.group),
  );
  const rust = cases.filter((row) => quarantinedGroupIds.has(row.group) && row.wall_ms !== null);
  assert.equal(rust.length, 62);
  assert.ok(rust.every((row) => !row.invocation_cost_accepted));
  assert.ok(rust.every((row) => typeof row.invocation_cost_ms === 'number'));
  const acceptedMax = Math.max(...cases.filter((row) => row.invocation_cost_accepted).map((row) => row.invocation_cost_ms as number));
  assert.equal(timingOverviewV092.observedMax, acceptedMax);
});

test('dynamic log axis covers every accepted cost and stays readable on narrow screens', () => {
  const acceptedValues = cases
    .filter((row) => row.invocation_cost_accepted)
    .map((row) => row.invocation_cost_ms as number);
  const [minimum, maximum] = timingOverviewV092.axis.domainSeconds;
  assert.ok(minimum > 0);
  assert.ok(minimum * 1000 <= Math.min(...acceptedValues));
  assert.ok(maximum * 1000 >= Math.max(...acceptedValues));
  assert.ok(timingOverviewV092.axis.ticksSeconds.length <= 6);
  assert.ok(timingOverviewV092.axis.ticksSeconds.length > 0);
  assert.deepEqual(
    timingOverviewV092.axis.ticksSeconds,
    [...timingOverviewV092.axis.ticksSeconds].sort((left, right) => left - right),
  );
  assert.equal(timingPosition(minimum * 1000), 0);
  assert.equal(timingPosition(maximum * 1000), 100);
  assert.ok(acceptedValues.every((value) => timingPosition(value) >= 0 && timingPosition(value) <= 100));
  assert.ok(new Set(timingOverviewV092.axis.ticksSeconds.map(formatAxisTick)).size > 1);
  assert.throws(() => timingPosition(minimum * 100), RangeError);
  assert.throws(() => timingPosition(maximum * 10_000), RangeError);
});

test('analyzer and tier filters retain mixed Swift coverage and empty planned tiers', () => {
  assert.deepEqual(
    timingOverviewAggregateRows().map((row) => row.analyzerId),
    timingOverviewV092.summaryRows.map((row) => row.analyzerId),
  );
  assert.equal(timingOverviewAggregateRows('all', 'mixed').length, 8);
  assert.equal(timingOverviewRows().length, 84);
  assert.equal(timingOverviewRows('joern', 'mixed').length, 1);
  const common108 = timingOverviewRows('joern', 'mixed')[0];
  assert.ok(common108);
  assert.match(common108.label, /Swift.*mixed/);
  assert.equal(timingOverviewAggregateRows('codeql')[0]?.blockedGroups, 1);
  assert.equal(timingOverviewAggregateRows('joern')[0]?.quarantinedGroups, 1);

  const unplanned = timingOverviewV092.aggregateRows.filter((row) => row.plannedGroups === 0);
  assert.ok(unplanned.length > 0);
  assert.ok(unplanned.every((row) => row.status === 'not-planned' && row.median === null));
});

test('overhead and warm evidence remains separate from cold invocation-cost distributions', () => {
  assert.equal(timingOverviewV092.overhead.length, 9);
  assert.equal(timingOverviewV092.warm.length, 2);
  assert.ok(timingOverviewV092.overhead.every((entry) => entry.label.length > 0));
  assert.ok(timingOverviewV092.overhead.every((entry) => entry.sourceRefs.length > 0));
});

test('timing labels preserve sub-millisecond costs and missing values', () => {
  assert.equal(formatTiming(null), '—');
  assert.equal(formatTiming(0.4), '<1 ms');
  assert.equal(formatTiming(1.4), '1 ms');
  assert.equal(formatTiming(254), '254 ms');
  assert.equal(formatTiming(999.9), '1 s');
  assert.equal(formatTiming(1000), '1 s');
  assert.equal(formatTiming(1462.5), '1.46 s');
  assert.equal(formatAxisTick(0.0005), '0.5 ms');
  assert.equal(formatAxisTick(1), '1 s');
  for (const invalid of [Number.NaN, Number.POSITIVE_INFINITY, -1]) {
    assert.throws(() => formatTiming(invalid), RangeError);
  }
});
