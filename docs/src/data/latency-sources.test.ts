import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { latencyEvidenceRelease } from './latency-sources.ts';

const dataRoot = fileURLToPath(new URL('.', import.meta.url));
const evidence = JSON.parse(
  fs.readFileSync(
    `${dataRoot}/archive/v0-6-0-latency-evidence.json`,
    'utf8',
  ),
);
const results = JSON.parse(
  fs.readFileSync(`${dataRoot}/archive/v0-6-0-results.json`, 'utf8'),
);

test('v0.6.0 and v0.6.1 bind the same immutable latency release', () => {
  assert.equal(latencyEvidenceRelease('v0.6.0'), 'v0.6.0');
  assert.equal(latencyEvidenceRelease('v0.6.1'), 'v0.6.0');
  assert.equal(evidence.release, 'v0.6.0');
  assert.equal(
    evidence.evidence_ref,
    'c0c42013a35a19107b65e652f55952669c4b9ffe',
  );
  assert.equal(evidence.manifest_sha256, results.manifest.sha256);
});

test('the archived corpus cannot absorb later FlowDroid modeling timings', () => {
  const flowdroidCards = results.scorecards.filter(
    (card: any) => card.adapter.tool === 'flowdroid',
  );
  const boundCases = flowdroidCards.flatMap((card: any) =>
    card.languages.flatMap((language: any) =>
      language.score_tiers.flatMap((tier: any) => tier.cases),
    ),
  );
  const flowdroidTimings = Object.keys(evidence.timings).filter((path) =>
    path.includes('/flowdroid-'),
  );
  assert.equal(boundCases.length, 116);
  assert.equal(flowdroidTimings.length, 116);
  assert.equal(
    flowdroidTimings.some((path) => path.includes('flowdroid-java-modeling')),
    false,
  );
  assert.equal(flowdroidCards[0].adapter.tool_version, '2.15.1');
  assert.equal(Object.keys(evidence.timings).length, 2657);
  assert.equal(
    results.scorecards.find((card: any) => card.adapter.tool === 'bifrost')
      .adapter.tool_version,
    'bifrost 0.10.7',
  );
});
