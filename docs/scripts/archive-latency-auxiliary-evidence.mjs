import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const docsRoot = path.resolve(
  path.dirname(fileURLToPath(import.meta.url)),
  '..',
);
const repoRoot = path.resolve(docsRoot, '..');
const ref = process.argv[2];
const output = process.argv[3];
if (!ref || !output) {
  throw new Error(
    'usage: node scripts/archive-latency-auxiliary-evidence.mjs <git-ref> <output>',
  );
}

const roots = ['reports/raw/warm-latency', 'reports/raw/invocation-overhead'];
const names = execFileSync(
  'git',
  ['ls-tree', '-r', '--name-only', ref, '--', ...roots],
  { cwd: repoRoot, encoding: 'utf8' },
)
  .trim()
  .split('\n')
  .filter((name) =>
    /\/(warm-latency|invocation-overhead|run-environment)\.json$/.test(name),
  )
  .sort();

const artifacts = {};
for (const name of names) {
  artifacts[name] = JSON.parse(
    execFileSync('git', ['show', `${ref}:${name}`], {
      cwd: repoRoot,
      encoding: 'utf8',
    }),
  );
}

fs.writeFileSync(
  path.resolve(docsRoot, output),
  `${JSON.stringify(
    {
      schema_version: 1,
      evidence_ref: ref,
      latency_release: 'v0.6.0',
      artifacts,
    },
    null,
    2,
  )}\n`,
);
