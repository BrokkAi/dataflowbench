import assert from 'node:assert/strict';
import fs from 'node:fs';
import { createHash } from 'node:crypto';
import test from 'node:test';
import { boundEvidence } from './evidence-binding.ts';

const historical = JSON.parse(fs.readFileSync(new URL('./archive/v0-6-0-latency-auxiliary-evidence.json', import.meta.url), 'utf8'));
const identity = (value: typeof historical) => ({ release: value.latency_release, revision: value.evidence_ref, schema: value.schema_version });
const registry = { 'v0.6.0': { evidenceRef: historical.evidence_ref, evidence: historical } };

test('registered historical bundle resolves without fallback for absent releases', () => {
  assert.equal(boundEvidence('v0.6.0', registry, identity), historical);
  assert.throws(() => boundEvidence('v0.7.1', registry, identity), /no registered evidence/);
});

test('each registered bundle uses its own immutable revision', () => {
  const cold = JSON.parse(fs.readFileSync(new URL('./archive/v0-6-0-latency-evidence.json', import.meta.url), 'utf8'));
  const coldRegistry = { 'v0.6.0': { evidenceRef: cold.evidence_ref, evidence: cold } };
  const coldIdentity = (value: typeof cold) => ({ release: value.release, revision: value.evidence_ref, schema: value.schema_version });
  assert.notEqual(cold.evidence_ref, historical.evidence_ref);
  assert.equal(boundEvidence('v0.6.0', coldRegistry, coldIdentity), cold);
  assert.throws(() => boundEvidence('v0.6.0', { 'v0.6.0': { evidenceRef: historical.evidence_ref, evidence: cold } }, coldIdentity), /immutable binding/);
});

test('release, revision and schema drift fail closed', () => {
  for (const changes of [{latency_release: 'v0.7.1'}, {evidence_ref: '0'.repeat(40)}, {schema_version: 2}]) {
    assert.throws(() => boundEvidence('v0.6.0', { 'v0.6.0': { ...registry['v0.6.0'], evidence: {...historical, ...changes} } }, identity), /immutable binding/);
  }
  assert.throws(() => boundEvidence('v0.6.0', { 'v0.6.0': { evidenceRef: 'main', evidence: {...historical, evidence_ref: 'main'} } }, identity), /immutable binding/);
});

test('v0.7.0 archive is byte-identical to the release tag', () => {
  const archived = fs.readFileSync(new URL('./archive/v0-7-0-results.json', import.meta.url));
  const digest = (bytes: Buffer) => createHash('sha256').update(bytes).digest('hex');
  // SHA-256 of git show 0a4d8b66c1e458b10e2c6196d0e4f9622f4c8ef5:results/results.json.
  // Keep this literal independent of the working tree and shallow CI history.
  assert.equal(digest(archived), '6d5933490d2ea7500a8b3ce0fd26f87074bd8db4ea1a6cb03a4c79172c8d444d');
});
