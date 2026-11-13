import assert from 'node:assert/strict';
import test from 'node:test';
import { hasLatencyEvidence, snapshotByVersion } from './snapshots.ts';
import { timingSupplementV092 } from './timing-supplement-v092.ts';

test('the candidate supplement is bound to the frozen v0.9.2 evidence', () => {
  assert.equal(timingSupplementV092.schema, 'v092-timing-reconciliation/v1');
  assert.equal(
    timingSupplementV092.releaseCommit,
    '86092336d8f9ca32fe9e2c4042c2dced76c1feb1',
  );
  assert.equal(
    timingSupplementV092.frozenManifestSha256,
    '2d4a40a10c79813a4dad8e2b8f7340daa6259da0553762a92c5847ec5d91014c',
  );
  assert.equal(timingSupplementV092.publicationEligible, false);
  assert.equal(timingSupplementV092.totals.certifiedGroups, 0);
  assert.equal(timingSupplementV092.totals.blockedColdGroups, 63);
  assert.equal(timingSupplementV092.totals.identityDifferences, 0);
  assert.equal(timingSupplementV092.totals.outcomeChanges, 0);
  assert.equal(timingSupplementV092.coldSlices.length, 21);
});

test('case distributions preserve timed, untimed and outcome counts', () => {
  const totals = timingSupplementV092.totals;
  assert.equal(totals.reportRows, 1170);
  assert.equal(totals.timedRows, 1085);
  assert.equal(totals.untimedRows, 85);
  assert.equal(totals.outcomes.inconclusive, 338);
  assert.equal(totals.outcomes['not-reached'], 393);
  assert.equal(totals.outcomes.reached, 354);
  assert.equal(totals.outcomes.unsupported, 85);
  assert.equal(
    timingSupplementV092.coldSlices.reduce(
      (count, slice) => count + slice.reportRows,
      0,
    ),
    totals.reportRows,
  );
  assert.equal(
    timingSupplementV092.coldSlices.reduce(
      (count, slice) => count + slice.timed,
      0,
    ),
    totals.timedRows,
  );

  const unsupportedNative = timingSupplementV092.coldSlices.find(
    (slice) => slice.group === 'bifrost-java-native',
  );
  assert.ok(unsupportedNative);
  assert.equal(unsupportedNative.reportRows, 12);
  assert.equal(unsupportedNative.timed, 0);
  assert.equal(unsupportedNative.min, null);
  assert.equal(unsupportedNative.median, null);
  assert.equal(unsupportedNative.p90, null);
  assert.equal(unsupportedNative.max, null);

  const pythonModeling = timingSupplementV092.coldSlices.find(
    (slice) => slice.group === 'bifrost-python-modeling',
  );
  assert.ok(pythonModeling);
  assert.equal(pythonModeling.reportRows, 24);
  assert.equal(pythonModeling.timed, 8);
  assert.equal(pythonModeling.median, 608);
});

test('overhead ranges remain unqualified upper-bound estimates', () => {
  assert.deepEqual(
    timingSupplementV092.overhead.map(({ group, repeats_ms, range_ms }) => ({
      group,
      repeats_ms,
      range_ms,
    })),
    [
      {
        group: 'overhead-bifrost-python',
        repeats_ms: [805, 565, 562],
        range_ms: { high: 805, low: 562 },
      },
      {
        group: 'overhead-infer-c',
        repeats_ms: [245, 260, 260],
        range_ms: { high: 260, low: 245 },
      },
    ],
  );
  assert.ok(timingSupplementV092.overhead.every((entry) => entry.upper_bound_estimate));
  assert.ok(
    timingSupplementV092.overhead.every(
      (entry) => entry.qualification.certified === false,
    ),
  );
});

test('candidate timing never registers as certified snapshot latency', () => {
  const frozen = snapshotByVersion('v0.9.2');
  assert.equal(frozen.latencyEvidenceRelease, undefined);
  assert.equal(hasLatencyEvidence(frozen), false);
  assert.equal(timingSupplementV092.publicationEligible, false);
});
