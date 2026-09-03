import { execFileSync } from 'node:child_process';
import crypto from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const docsRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const repoRoot = path.resolve(docsRoot, '..');
const ref = process.argv[2];
const output = process.argv[3];
if (!ref || !output) {
  throw new Error('usage: node scripts/archive-latency-evidence.mjs <git-ref> <output>');
}

const showText = (relative) =>
  execFileSync('git', ['show', `${ref}:${relative}`], {
    cwd: repoRoot,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
    stdio: ['ignore', 'pipe', 'ignore'],
  });
const showJson = (relative) => JSON.parse(showText(relative));

const manifestText = showText('reports/freeze.json');
const manifest = JSON.parse(manifestText);
const results = showJson('results/results.json');
const manifestSha256 = crypto
  .createHash('sha256')
  .update(manifestText)
  .digest('hex');
if (results.manifest.sha256 !== manifestSha256) {
  throw new Error(
    `${ref}: archived results name manifest ${results.manifest.sha256}, but the ref contains ${manifestSha256}`,
  );
}
const timings = {};
const environments = {};
for (const entry of manifest.reports) {
  const report = showJson(entry.path);
  for (const result of report.results) {
    if (!result.raw_output) continue;
    const directory = path.posix.dirname(result.raw_output);
    const timingPath = `${directory}/${result.case_id}-timing.json`;
    try {
      timings[timingPath] = showJson(timingPath);
    } catch {
      // Unsupported/declined cases have raw evidence but no analyzer timing.
    }
    if (!(directory in environments)) {
      try {
        environments[directory] = showJson(`${directory}/run-environment.json`);
      } catch {
        environments[directory] = null;
      }
    }
  }
}

const bundle = {
  schema_version: 1,
  evidence_ref: ref,
  release: manifest.benchmark.release,
  benchmark_revision: manifest.benchmark.revision,
  manifest_sha256: manifestSha256,
  timings,
  environments,
};
fs.writeFileSync(
  path.resolve(docsRoot, output),
  `${JSON.stringify(bundle, null, 2)}\n`,
);
