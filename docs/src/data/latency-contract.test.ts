import assert from 'node:assert/strict';
import test from 'node:test';
import {
  comparableAnalyzerPhases,
  comparableAnalyzerWallMs,
  contractTiming,
} from './latency-contract.ts';

const flowdroidModeling = [
  { phase: 'compile', wall_ms: 855 },
  { phase: 'dex', wall_ms: 533 },
  { phase: 'analyze', wall_ms: 968 },
];

test('A20 excludes FlowDroid modeling materialization from the analyzer total', () => {
  const derived = contractTiming('flowdroid', 'modeling', flowdroidModeling);
  assert.equal(
    comparableAnalyzerWallMs('flowdroid', 'modeling', flowdroidModeling),
    968,
  );
  assert.deepEqual(
    comparableAnalyzerPhases('flowdroid', 'modeling', flowdroidModeling),
    [{ phase: 'analyze', wall_ms: 968 }],
  );
  // The selector does not mutate or discard the retained phase detail.
  assert.deepEqual(flowdroidModeling.map((phase) => phase.phase), [
    'compile',
    'dex',
    'analyze',
  ]);
  assert.equal(derived.analyzerWallMs, 968);
  assert.deepEqual(
    derived.phases.map((phase) => phase.phase),
    ['compile', 'dex', 'analyze'],
  );
});

test('ordinary decomposed adapters retain every analyzer phase', () => {
  const codeql = [
    { phase: 'database-create', wall_ms: 100 },
    { phase: 'database-analyze', wall_ms: 25 },
  ];
  assert.equal(comparableAnalyzerWallMs('codeql', 'core', codeql), 125);
  assert.deepEqual(comparableAnalyzerPhases('codeql', 'core', codeql), codeql);
});

test('A20 rejects an undeclared FlowDroid modeling phase shape', () => {
  assert.throws(
    () =>
      comparableAnalyzerWallMs('flowdroid', 'modeling', [
        { phase: 'compile', wall_ms: 10 },
        { phase: 'analyze', wall_ms: 20 },
      ]),
    /expected retained phases compile, dex, analyze/,
  );
});
