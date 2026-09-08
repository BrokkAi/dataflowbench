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

test('v0.7.0 archive binds the published release rather than its development tag tree', () => {
  const archived = fs.readFileSync(new URL('./archive/v0-7-0-results.json', import.meta.url));
  const results = JSON.parse(archived.toString('utf8'));
  assert.equal(results.benchmark.release, 'v0.7.0');
  assert.equal(results.claim.scope, 'release');
  assert.equal(results.benchmark.revision, '0a4d8b66c1e458b10e2c6196d0e4f9622f4c8ef5');
  assert.equal(results.benchmark.dirty, false);
  assert.equal(results.manifest.path, 'reports/freeze.json');
  assert.equal(results.manifest.sha256, 'c543ae4ebd11ed6f3495f4461b5b4bd7c84d0874997f1b62044e9df62817b28b');
  // SHA-256 of git show 61300f47de7affa651fbd4a125ca6b894b29ce71:results/results.json.
  // The tag predates this manifest commit and still contains development results.
  // Keep the expected digest independent of the working tree and shallow CI history.
  assert.equal(createHash('sha256').update(archived).digest('hex'), '2de0ea1726072d98e134e9b48bc3fdcd07184c286d3259cfe6ea8f2b4b82075b');
});


test('the final freeze uses current release validation rather than historical transition', () => {
  const workflow = fs.readFileSync(new URL('../../../.github/workflows/ci.yml', import.meta.url), 'utf8');
  assert.equal(workflow.includes('TEMPORARY v0.7.1 evidence transition'), false);
  assert.ok(workflow.includes('scripts/check-release-results.py'));
});

test('v0.7.1 fresh latency binds its own manifest and actual warm batch sizes', () => {
  const read = (path: string) => JSON.parse(fs.readFileSync(new URL(path, import.meta.url), 'utf8'));
  const cold = read('./archive/v0-7-1-latency-evidence.json');
  const aux = read('./archive/v0-7-1-latency-auxiliary-evidence.json');
  const manifest = fs.readFileSync(new URL('../../../reports/freeze.json', import.meta.url));
  assert.equal(cold.manifest_sha256, createHash('sha256').update(manifest).digest('hex'));
  assert.equal(cold.release, 'v0.7.1');
  assert.equal(cold.evidence_ref, '2007f15d687e0081c948e55bba39c952d248ee0f');
  assert.equal(aux.evidence_ref, cold.evidence_ref);
  assert.equal(Object.keys(cold.timings).length, 2725);
  assert.equal(Object.keys(cold.environments).length, 82);
  assert.equal(Object.keys(aux.artifacts).length, 22);
  const warm = aux.artifacts['reports/raw/warm-latency/semgrep-java-kernel/warm-latency.json'];
  assert.equal(warm.runs.length, 2);
  for (const run of warm.runs) assert.deepEqual(run.batches.map((b: any) => b.k), [1, 2, 4, 8, 12]);
  assert.equal(Object.keys(aux.artifacts).some((p) => p.includes('superseded')), false);
});
