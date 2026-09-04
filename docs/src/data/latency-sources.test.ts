import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';
import { fileURLToPath } from 'node:url';
import { latencyEvidenceRelease } from './latency-sources.ts';

const dataRoot = fileURLToPath(new URL('.', import.meta.url));
const evidence = JSON.parse(
  fs.readFileSync(`${dataRoot}/archive/v0-6-0-latency-evidence.json`, 'utf8'),
);
const results = JSON.parse(
  fs.readFileSync(`${dataRoot}/archive/v0-6-0-results.json`, 'utf8'),
);
const auxiliary = JSON.parse(
  fs.readFileSync(
    `${dataRoot}/archive/v0-6-0-latency-auxiliary-evidence.json`,
    'utf8',
  ),
);

test('v0.6.0, v0.6.1 and v0.7.0 bind the same immutable latency release', () => {
  assert.equal(latencyEvidenceRelease('v0.6.0'), 'v0.6.0');
  assert.equal(latencyEvidenceRelease('v0.6.1'), 'v0.6.0');
  assert.equal(latencyEvidenceRelease('v0.7.0'), 'v0.6.0');
  assert.equal(evidence.release, 'v0.6.0');
  assert.equal(
    evidence.evidence_ref,
    'c0c42013a35a19107b65e652f55952669c4b9ffe',
  );
  assert.equal(evidence.manifest_sha256, results.manifest.sha256);
});

test('warm and overhead panels bind immutable v0.6.0 amendment evidence', () => {
  assert.equal(auxiliary.latency_release, 'v0.6.0');
  assert.equal(
    auxiliary.evidence_ref,
    'ccbcd788aabec2abe60200573f38bc42128d00f0',
  );
  assert.equal(Object.keys(auxiliary.artifacts).length, 25);
  const names = Object.keys(auxiliary.artifacts);
  assert.equal(
    names.filter((name) => name.endsWith('/warm-latency.json')).length,
    3,
  );
  assert.equal(
    names.filter((name) => name.endsWith('/invocation-overhead.json')).length,
    9,
  );
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

test('the archived corpus keeps naming the pins that produced it', () => {
  // v0.7.0 re-pinned Bifrost, Semgrep CE, Joern and OpenTaint and re-ran their
  // correctness slices. It did not re-measure latency, so the corpus these
  // three snapshots render still witnesses the *older* pins — the assertion
  // that would fail if a future release ever relabelled it onto its own.
  const versions = new Map<string, string>();
  for (const card of results.scorecards as any[]) {
    versions.set(card.adapter.tool, card.adapter.tool_version);
  }
  assert.equal(versions.get('bifrost'), 'bifrost 0.10.7');
  assert.equal(versions.get('semgrep'), '1.175.0');
  assert.equal(versions.get('joern'), '4.0.614');
  assert.equal(versions.get('opentaint'), 'analyzer/2026.08.27.17eb0fe');
});
