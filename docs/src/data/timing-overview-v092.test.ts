import assert from 'node:assert/strict';
import test from 'node:test';
import caseRows from '../../../reports/timing/v0.9.2/20261113-02/reconciliation-v1/cases.json' with { type: 'json' };
import { timingSupplementV092 } from './timing-supplement-v092.ts';
import {
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

test('default aggregate contains the eight pinned analyzers in frozen order', () => {
  const rows = timingOverviewV092.summaryRows;
  assert.deepEqual(
    rows.map(({ analyzerId }) => analyzerId),
    ['bifrost', 'codeql', 'joern', 'semgrep', 'opentaint', 'infer', 'flowdroid', 'pysa'],
  );
  assert.deepEqual(
    rows.map(({ pin }) => pin),
    ['v0.15.1', '2.27.2', '4.0.660', '1.181.0', '0.4.6', 'v1.3.0', '2.15.1', '0.10.0'],
  );
  assert.equal(rows[3]?.auxiliaryPin, 'rules 17e31e11ebac99fb7dfe1cd288f7a32151b6f3f9');
  assert.equal(rows[4]?.auxiliaryPin, 'analyzer 2026.09.04.c51dc3e');
  assert.equal(rows[7]?.auxiliaryPin, 'Pyrefly 1.4.0');
  assert.equal(rows.length, 8);
});

test('aggregate distributions use every retained per-case wall-time observation', () => {
  const rows = timingOverviewV092.summaryRows;
  const bifrost = rows[0];
  const infer = rows[5];
  assert.ok(bifrost);
  assert.ok(infer);

  const directSummary = (analyzerId: string) => {
    const values = cases
      .filter((row) => row.group.startsWith(`${analyzerId}-`))
      .flatMap((row) => (typeof row.wall_ms === 'number' ? [row.wall_ms] : []));
    return {
      reportRows: cases.filter((row) => row.group.startsWith(`${analyzerId}-`)).length,
      timed: values.length,
      min: Math.min(...values),
      median: quantile(values, 0.5),
      p90: quantile(values, 0.9),
      max: Math.max(...values),
    };
  };

  assert.deepEqual(
    {
      reportRows: bifrost.reportRows,
      timed: bifrost.timed,
      min: bifrost.min,
      median: bifrost.median,
      p90: bifrost.p90,
      max: bifrost.max,
    },
    directSummary('bifrost'),
  );
  assert.deepEqual(
    {
      reportRows: infer.reportRows,
      timed: infer.timed,
      min: infer.min,
      median: infer.median,
      p90: infer.p90,
      max: infer.max,
    },
    directSummary('infer'),
  );

  const groupMedians = timingSupplementV092.coldSlices
    .filter((slice) => slice.group.startsWith('bifrost-') && slice.median !== null)
    .map((slice) => slice.median as number);
  assert.notEqual(bifrost.median, quantile(groupMedians, 0.5));
  assert.equal(bifrost.reportRows, 1046);
  assert.equal(bifrost.timed, 961);
  assert.equal(bifrost.min, 559);
  assert.equal(bifrost.median, 620);
  assert.equal(bifrost.p90, 1400);
  assert.equal(bifrost.max, 8356);
  assert.equal(infer.reportRows, 124);
  assert.equal(infer.timed, 124);
  assert.equal(infer.min, 254);
  assert.equal(infer.median, 267);
  assert.ok(Math.abs((infer.p90 ?? 0) - 1472.9) < 1e-9);
  assert.equal(infer.max, 1821);
});

test('missing analyzer coverage stays explicit and has no fabricated statistics', () => {
  const rows = timingOverviewV092.summaryRows;
  const missing = rows.filter((row) => row.status === 'not-measured');

  assert.deepEqual(
    missing.map((row) => row.analyzerId),
    ['codeql', 'joern', 'semgrep', 'opentaint', 'flowdroid', 'pysa'],
  );
  assert.deepEqual(
    missing.map((row) => row.plannedGroups),
    [18, 13, 17, 4, 4, 3],
  );
  assert.ok(
    missing.every(
      (row) =>
        row.reportRows === 0 &&
        row.timed === 0 &&
        row.measuredGroups === 0 &&
        row.min === null &&
        row.median === null &&
        row.p90 === null &&
        row.max === null &&
        row.blocker !== null,
    ),
  );
  assert.match(missing.find((row) => row.analyzerId === 'codeql')?.blocker ?? '', /runtime closure/);
  assert.match(missing.find((row) => row.analyzerId === 'flowdroid')?.blocker ?? '', /java or javac digest differs/);
  assert.equal(
    rows.find((row) => row.analyzerId === 'bifrost')?.blocker,
    'Pinned Scala Maven materialization must be restored and verified.',
  );
  assert.match(rows.find((row) => row.analyzerId === 'infer')?.blocker ?? '', /java or javac digest differs/);
});

test('aggregate counts keep captured and planned cases and groups distinct', () => {
  assert.deepEqual(
    {
      reportRows: timingOverviewV092.totals.reportRows,
      timedRows: timingOverviewV092.totals.timedRows,
      untimedRows: timingOverviewV092.totals.untimedRows,
      capturedGroups: timingOverviewV092.totals.capturedGroups,
      plannedGroups: timingOverviewV092.totals.plannedGroups,
    },
    {
      reportRows: 1170,
      timedRows: 1085,
      untimedRows: 85,
      capturedGroups: 21,
      plannedGroups: 84,
    },
  );
  assert.equal(timingOverviewV092.totals.publicationEligible, false);
  assert.equal(timingOverviewV092.totals.certifiedGroups, 0);
  assert.deepEqual(timingOverviewV092.totals.observedContentionGroups, [
    'bifrost-c-kernel',
    'bifrost-java-kernel',
  ]);
  assert.deepEqual(timingOverviewV092.totals.quietGatePassedGroups, ['bifrost-c-kernel']);
  assert.equal(timingOverviewV092.totals.cpuObservationFailures, 0);

  const overhead = timingOverviewV092.overhead;
  assert.equal(overhead.length, 2);
  assert.deepEqual(
    overhead.map((row) => [row.group, row.range_ms.low, row.range_ms.high, row.qualification.contention_observed]),
    [
      ['overhead-bifrost-python', 562, 805, true],
      ['overhead-infer-c', 245, 260, false],
    ],
  );
  assert.ok(overhead.every((row) => row.qualification.observation_failures === 0));
});

test('analyzer and tier filters work for both aggregate and slice detail', () => {
  assert.deepEqual(
    timingOverviewAggregateRows().map((row) => row.analyzerId),
    timingOverviewV092.summaryRows.map((row) => row.analyzerId),
  );
  assert.equal(timingOverviewAggregateRows('bifrost').length, 1);
  assert.equal(timingOverviewAggregateRows('all', 'modeling').length, 8);
  assert.equal(timingOverviewAggregateRows('bifrost', 'modeling')[0]?.plannedGroups, 3);
  assert.equal(timingOverviewAggregateRows('codeql', 'modeling')[0]?.plannedGroups, 3);

  assert.equal(timingOverviewRows().length, 21);
  assert.equal(timingOverviewRows('bifrost').length, 19);
  assert.equal(timingOverviewRows('infer').length, 2);
  assert.equal(timingOverviewRows('bifrost', 'modeling').length, 3);
  assert.deepEqual(
    timingOverviewRows('infer', 'kernel').map((row) => row.group),
    ['infer-c-kernel', 'infer-cpp-kernel'],
  );
  assert.equal(timingOverviewRows('all', 'native').length, 3);
});

test('an untimed captured tier and an unplanned tier are distinct from missing runtime coverage', () => {
  const native = timingOverviewAggregateRows('bifrost', 'native')[0];
  assert.equal(native?.status, 'untimed');
  assert.equal(native?.measuredGroups, 3);
  assert.equal(native?.reportRows, 36);
  assert.equal(native?.timed, 0);
  assert.equal(native?.blocker, null);
  const unplanned = timingOverviewV092.aggregateRows.filter(row => row.plannedGroups === 0);
  assert.ok(unplanned.length > 0);
  assert.ok(unplanned.every(row => row.status === 'not-planned' && row.median === null));
});

test('slice detail preserves every retained source row and qualification flag', () => {
  const source = timingSupplementV092.coldSlices;
  const overview = timingOverviewV092.rows;

  assert.deepEqual(
    overview.map((row) => row.group),
    source.map((slice) => slice.group),
  );

  for (const [index, row] of overview.entries()) {
    const slice = source[index];
    assert.ok(slice);
    assert.equal(row.reportRows, slice.reportRows);
    assert.equal(row.timed, slice.timed);
    assert.equal(row.untimed, slice.reportRows - slice.timed);
    assert.equal(row.min, slice.min);
    assert.equal(row.median, slice.median);
    assert.equal(row.p90, slice.p90);
    assert.equal(row.max, slice.max);
    assert.deepEqual(row.outcomes, slice.outcomes);
    assert.deepEqual(row.qualification, slice.qualification);
    assert.ok(row.label.length > 0);
  }
});

test('the shared log axis covers observed case data and maps boundaries consistently', () => {
  const { axis, medianRange, observedMax } = timingOverviewV092;
  assert.deepEqual(axis.domainSeconds, [0.25, 10]);
  assert.deepEqual(axis.ticksSeconds, [0.25, 0.5, 1, 2, 4, 8]);
  assert.equal(medianRange.min, 267);
  assert.equal(medianRange.max, 620);
  assert.equal(observedMax, 8356);

  assert.equal(timingPosition(axis.domainSeconds[0] * 1000), 0);
  assert.equal(timingPosition(axis.domainSeconds[1] * 1000), 100);
  assert.ok(Math.abs(timingPosition(Math.sqrt(2.5) * 1000) - 50) < 1e-10);

  const atOneSecond = timingPosition(1000);
  const atTwoSeconds = timingPosition(2000);
  const atFourSeconds = timingPosition(4000);
  assert.ok(Math.abs(atTwoSeconds - atOneSecond - (atFourSeconds - atTwoSeconds)) < 1e-10);
});

test('timing positions reject non-finite, non-positive and out-of-domain values', () => {
  for (const invalid of [Number.NaN, Number.POSITIVE_INFINITY, 0, -1, 249, 10_001]) {
    assert.throws(() => timingPosition(invalid), RangeError);
  }
});

test('timing labels use milliseconds, seconds and an em dash consistently', () => {
  assert.equal(formatTiming(null), '—');
  assert.equal(formatTiming(254), '254 ms');
  assert.equal(formatTiming(263.4), '263 ms');
  assert.equal(formatTiming(999.9), '1 s');
  assert.equal(formatTiming(1000), '1 s');
  assert.equal(formatTiming(1462.5), '1.46 s');
  assert.equal(formatTiming(8356), '8.36 s');
});

test('timed observations retain inconclusive and unsupported outcome context', () => {
  assert.equal(timingOverviewV092.totals.timedGroups, 18);
  assert.equal(timingOverviewV092.totals.timedInconclusiveRows, 338);
  assert.equal(timingOverviewV092.totals.unsupportedUntimedRows, 85);
});
