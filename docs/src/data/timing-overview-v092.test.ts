import assert from 'node:assert/strict';
import test from 'node:test';
import { timingSupplementV092 } from './timing-supplement-v092.ts';
import {
  formatTiming,
  timingOverviewRows,
  timingOverviewV092,
  timingPosition,
} from './timing-overview-v092.ts';

test('overview rows preserve every source slice and its timing fields in order', () => {
  const source = timingSupplementV092.coldSlices;
  const overview = timingOverviewV092.rows;

  assert.equal(overview.length, 21);
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

  assert.equal(overview.reduce((count, row) => count + row.reportRows, 0), 1170);
  assert.equal(overview.reduce((count, row) => count + row.timed, 0), 1085);
  assert.equal(overview.reduce((count, row) => count + row.untimed, 0), 85);
  assert.equal(timingOverviewV092.totals, timingSupplementV092.totals);
  assert.equal(timingOverviewV092.pageUrl, timingSupplementV092.pageUrl);
  assert.equal(timingOverviewV092.overhead, timingSupplementV092.overhead);
});

test('native rows with no timings remain visible and keep null statistics', () => {
  const nativeRows = timingOverviewRows('all', 'native');

  assert.deepEqual(
    nativeRows.map((row) => row.group),
    [
      'bifrost-java-native',
      'bifrost-javascript-native',
      'bifrost-python-native',
    ],
  );
  assert.equal(nativeRows.length, 3);
  assert.ok(
    nativeRows.every(
      (row) =>
        row.reportRows > 0 &&
        row.timed === 0 &&
        row.untimed === row.reportRows &&
        row.min === null &&
        row.median === null &&
        row.p90 === null &&
        row.max === null,
    ),
  );
  assert.equal(timingOverviewRows('Bifrost', 'native').length, 3);
  assert.equal(timingOverviewRows('Infer', 'native').length, 0);
});

test('analyzer and tier filters preserve source order and full coverage', () => {
  const allRows = timingOverviewRows();

  assert.deepEqual(allRows, timingOverviewV092.rows);
  assert.equal(timingOverviewRows('Bifrost').length, 19);
  assert.equal(timingOverviewRows('Infer').length, 2);
  assert.equal(timingOverviewRows('Bifrost', 'modeling').length, 3);
  assert.deepEqual(
    timingOverviewRows('Infer', 'kernel').map((row) => row.group),
    ['infer-c-kernel', 'infer-cpp-kernel'],
  );
  assert.deepEqual(
    timingOverviewRows('all', 'smoke').map((row) => row.language),
    ['mixed languages'],
  );
  assert.equal(
    timingOverviewRows().filter((row) => row.tier === 'native' && row.timed === 0)
      .length,
    3,
  );
});

test('the shared log axis covers observed data and maps boundaries consistently', () => {
  const { axis, medianRange, observedMax } = timingOverviewV092;
  assert.deepEqual(axis.domainSeconds, [0.25, 10]);
  assert.deepEqual(axis.ticksSeconds, [0.25, 0.5, 1, 2, 4, 8]);

  const observedMinimum = Math.min(
    ...timingOverviewV092.rows.flatMap((row) =>
      row.min === null ? [] : [row.min],
    ),
  );
  assert.equal(observedMinimum, 254);
  assert.equal(observedMax, 8356);
  assert.ok(observedMinimum / 1000 >= axis.domainSeconds[0]);
  assert.ok(observedMax / 1000 <= axis.domainSeconds[1]);
  assert.equal(medianRange.min, 263);
  assert.equal(medianRange.max, 1462.5);

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
