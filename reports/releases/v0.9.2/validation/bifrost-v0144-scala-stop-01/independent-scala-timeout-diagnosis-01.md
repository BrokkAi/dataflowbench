# Independent diagnosis: Bifrost v0.14.4 Scala stop

**Reviewed:** 2026-11-01T16:43:06.366960+00:00  
**Scope:** Read-only evidence diagnosis. No benchmark retry, analyzer/build command, source edit, or threshold change.

## Verdict

The attempt hit its 1046-second deadline. The terminal receipt records exit 124, timed_out=true, elapsed 1053.306339459 seconds (7.306339459 seconds over budget), then labels its status recorder-error because the required aggregate JSON output root is absent. Keep both facts: the execution timed out; the recorder could not find the aggregate output. The recorder error is not the cause of the stop.

Seventeen groups completed before Scala. The read-only reconciliation found the target incomplete at 17 of 18 attempts; smoke and TypeScript were not started. There is no normalized Scala aggregate report, so this is not a completed benchmark result.

## What the retained raw evidence says

The Scala contract contains 70 cases (35 positive/negative pairs). The stopped attempt retains 60 case JSON artifacts: 59 Bifrost raw reports and one runner-error diagnostic. It has 59 per-case timing files. Ten cases have no raw output; recursive-heap-unwind-positive has raw output but no timing file. recursive-heap-unwind-negative has a retained runner-error payload saying it produced no JSON report after SIGTERM.

The raw Bifrost completion states are 34 complete, 25 inconclusive, and one runner-error. Positive raw reports contain 21 finding records: 17 complete cases with one finding each, and four inconclusive cases with one each. Negative raw reports contain no findings in the retained payloads, but 12 are inconclusive and one is the SIGTERM error. These are raw analyzer observations, not normalized outcomes or a score.

The 59 retained wall timings sum to 1044.765 seconds, 99.882% of the 1046-second group budget:

- 50 timings: 14.854–15.299 seconds (mean 15.123 seconds).
- 5 timings: 27.623–27.768 seconds (mean 27.692 seconds).
- 1 timing: 29.556 seconds.
- 3 timings: 40.172–40.277 seconds (mean 40.207 seconds).

The evidence points to cumulative per-case runtime consuming the budget. It does not isolate why those calls were slower.

## Configuration and causal limits

The frozen contract keeps the baseline case IDs, policy/report mapping, deadlines, and attempt budgets. Its allowed runtime projection changes the tool/report identity to Bifrost 0.14.4 and stages the pinned Scala 2.13.16 binary jar, sources jar, and POM into the Scala attempt home. The receipt records staging_started=false, 0.013183 seconds for the staging check, and a postcheck that verified all three artifacts. Source materialization took 2.468216 seconds. These setup costs do not explain the 1044.765 seconds of case timings.

Prior receipts record 70-case Scala runs at 311.801 seconds on Bifrost 0.13.1 and 412.487 seconds on 0.14.0, both under the same 1046-second deadline and fixture revision. The 0.14.4 attempt ended at 1053.306 seconds. This is a strong version-correlated slowdown signal, but it is not a controlled version-only comparison: source commits, contract hashes, and execution series differ, while runner identity evidence is not recorded consistently. The retained evidence does not prove the Bifrost version or Scala dependency staging caused the increase.

## Adapter/execution and repair assessment

No retained evidence establishes a wrong target pin, Scala dependency, or per-case policy mapping. The aggregate report is missing, and the persisted top-level status is recorder-error even though timeout is explicitly recorded; that is a reporting distinction to preserve, not a normalized analyzer outcome.

No analyzer change, pin change, timeout increase, or retry is justified by this incomplete run. Preserve the existing threshold and pinned behavior. A narrow receipt-classification improvement could make timeout the primary terminal status while keeping the absent aggregate root as a separate recorder error; it would improve reporting but would not repair or qualify the benchmark.

## Evidence anchors

- Attempt receipt: reports/releases/v0.9.2/attempts/bifrost-scala-kernel-attempt-03-series-03/completed.json (SHA-256 d1c090d100f5d7b9776fd2a43f62d4fa7f153e216c3bf773e60d2138ce837014).
- Frozen execution contract: reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/contract-02.json (SHA-256 1d2188df4e7bc7f5cc4e28cc0700a839a294b0cbecc484f4d9658bb5280164e4).
- Root stop reconciliation: reports/releases/v0.9.2/execution-v5/bifrost-v0144-01/scala-timeout-stop-reconciliation-01.json (SHA-256 d2ba9537b4ecb710b3bb27d2ecb4ac394def250c7ecdfc243d79c2478be878d9).
- Raw/timing directory: /Users/dave/.codex/worktrees/9f01/dataflowbench/execution-state/v092/groups/series-03/bifrost-scala-kernel/attempt-03/reports/raw/bifrost-scala-kernel; 120 files, inventory digest SHA-256 e3082e73699036b834f7b3d281c8a76713d1f143d9d6ae8aa72af47ae9bc7cc2.
- Prior series receipts and representative raw/timing artifacts are listed with hashes in the JSON.

**JSON artifact SHA-256:** 27b765a062d9f059e39d5c0a0ee06846ea75c52d822b6fd1897cce0e4c128d4e
