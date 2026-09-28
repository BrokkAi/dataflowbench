# Joern current108 integration and bounded evidence

The versioned `adapters/joern/swift-normal-v1` runner prepares all 108 current
Swift IDs and a Joern-specific normal result/v1 export route. The current
partition is **unresolved**; no full-population report, score, freeze or
publication has been produced. Historical v1/v2 reports and their 60-second
contracts are unchanged. This lane prospectively uses one 75-second total per
case across typecheck, import, query, decode and identity validation.

## What ran

The first registration accidentally resolved the `swiftc` launcher symlink to
`swift-frontend`. Six retained arms reported zero compiler type-map entries,
and an interrupted seventh arm retains its actual output without a fabricated
raw result. The correction preserves the driver spelling and stops on any
incomplete baseline. Original evidence remains immutable.

Corrected plan `3ca3c36fd4194db148b30fac9d65cd6d581ad6e7828e7e506df9253594c6e2c5`
ran twelve serial arms after its registration commit `c4765e3a` with
47,162,884,096 free bytes. All commands completed below their remaining budget;
total arm wall time was 70.532 seconds combined, with a 6.779-second maximum arm.
The output tree retained approximately 238.3 MiB and the observed free-space
change was 251,355,136 bytes; these are diagnostic measurements, not isolated
peak accounting or aggregate containment certification.

| Controls | Off | On | Interpretation |
|---|---|---|---|
| Direct positive | reached | reached | Endpoint baseline passed |
| Direct negative | not-reached | not-reached | Bounded baseline passed; no completeness claim |
| Four opaque/position cases | inconclusive | inconclusive | Native endpoint identity missing before model activation |

The 512 MiB JVM request is not aggregate process-tree memory enforcement. The
40 GiB reserve stayed intact. No fixture executable ran. The twelve-arm matrix
and its exact native output hashes replay with
`python3 -O scripts/check-joern-normal-controls-v1.py`.

## Exact structural boundary

One separately registered query inspected a clone of the opaque-positive CPG;
its first attempt failed to compile because generic Expression nodes lack
`typeFullName`. The corrected query omitted that field, retained typed method
parameters/returns and native argument/callee edges, and succeeded. Both
attempts and before/after original-CPG hashes are retained.

In that exact CPG, the local source declaration is
`main.swift:<global>.dfb_source:()->Swift.String`. The anchored source call targets
an **external** `DataFlowBenchTaintSwift.dfb_source:()->Swift.String` stub instead.
The local sink declaration has a Swift.String parameter and an ANY return,
while the anchored sink call likewise targets a separate external stub. The
wrapper declarations are owned by the Opaque TYPE_DECL, with receiver index 0,
Swift.String argument indices 1/2 and Swift.String returns; the carry call joins
its internal declaration correctly.

These are distinct native identities, not merely spellings that the adapter may
substitute. Changing a name would fabricate the missing endpoint call edge.
The four-case capability assessment therefore remains **Incomplete**, not
unsupported. All eight arms share the endpoint-gate failure, but the detailed
declaration diagnosis applies only to the one inspected CPG. A frontend binding
repair or an explicitly accepted scope decision would need independent review
and new prospective controls; this work does not start an accuracy-fixing loop.

## Remaining gates

An opaque-model activation receipt must replay successful model-off/on controls and
bind the same query/model/helper/runtime and phase-contract inputs as its corpus
plan. The exporter independently verifies that receipt and run/raw references.
Fresh native unsupported decisions require evidence for the current population;
old v2 rows cannot fill them. Preparation leaves every row pending capability.
Both #220 and #215 remain open. CodeQL's full108 run separately still requires
its 64 GiB launch reservation.

## Diagnostic admission versus model activation

The runner now distinguishes a `diagnostic-identity-gated` receipt from
`opaque-models` activation. Passing direct baselines may admit genuinely
executed current-population cases with exact identity gates and models **off**,
marked `unqualified`. An actual identity failure can then yield inconclusive
without requiring all opaque controls to pass first. This does not fabricate
attempts or authorize model-on execution. Opaque model activation still requires
the load-bearing off/on matrix; other modeling families require their own
reviewed activation scope. The committed partition remains unresolved pending
review; no new 108-case execution follows from this mechanism.

Control semantic closure binds query, model/configuration generation, native
observation helpers, process invocation helper, runtime trees/paths and phase
contract. Reusing the twelve retained controls after orchestration changes
requires the explicit `execution-revalidation-2026-09-28/amendment.json`.
It binds the old registered runner against plan 03, the factored invocation
module, and every reviewed replacement file. Environment and command-builder
ASTs are compared exactly (including imports, constants, defaults and arguments),
then all twelve arms replay generated argv, cwd, build log, staged source hashes
and the recorded environment fields. This is a bounded compatibility proof,
not general behavioral equivalence. Any subsequent runner or execution change
requires another reviewed amendment or new prospective controls.

Historical command witnesses did not capture `JAVA_OPTS`, `LANG` or `LC_ALL`.
Those values remain **unobserved; registered-code equivalence only**. In
particular, the requested heap size is not measured memory qualification. The
observed PATH is preserved as a historical input, not a claim about a future
shell. No historical file or observation is rewritten.

A future corpus plan and receipt must hash-bind the amendment and reviewed
execution bytes, and the runner requires those files to be committed before
execution. Export rechecks raw capability metadata, the exact native models-off
configuration, and the command arguments that consumed it, even for inconclusive
outcomes. Native-profile configuration and other family activation remain
unresolved; the diagnostic mechanism alone does not establish current108
coverage. No new native run is part of this amendment.

## Prospective current108 diagnostic admission (plan 04)

Plan `plan-2026-09-28-04` admits 96 benchmark-controlled cases for real,
identity-gated, models-off diagnostic attempts. It separately records 12 fresh
scoped unsupported decisions for the unchanged native contracts. Current case
and fixture hashes, all 1,349 installed Joern files, and the retained source,
class and resource evidence were rechecked; these are capability decisions,
not executions or automatic inheritance of an old partition. No claim about
future versions or externally supplied models follows.

The new plan resolves membership only. A reached or not-reached native
observation still exports as inconclusive because aggregate qualification is
unavailable; models-off execution is not modeled accuracy qualification.
The execution amendment preserves the earlier amendment and native controls.

Launch requires 44 GiB free (40 GiB reserve plus 4 GiB scratch allowance), an
exclusive analyzer reservation for this exact committed plan, unchanged runtime
inventories, and committed decisions/evidence. Each attempted case has 75
seconds total; 96 attempts give a 7,200-second maximum case allowance, plus the
30-second version witness and preflight/closure overhead. The storage allowance
is a conservative prospective estimate, not measured hard containment. Reserve
checks remain active between cases and phases. Preparation creates no launch
reservation, native result, full-population report, score, freeze or publication.

## Completed current108 diagnostic run

The registered plan ran on merge commit `4b3f6b78628f9d030d0dbb835fc8eb0f4f1a0679`
after all four post-merge CI checks passed. The exact-plan reservation recorded
48,369,913,856 free bytes and an exclusive analyzer slot. The serial run completed
all 108 rows: 96 actual attempts and 12 prospective native capability decisions.
Normal output is **96 inconclusive and 12 unsupported**, with no scored activation.

Raw diagnostic observations were 30 reached, 58 not-reached and 8 inconclusive.
Four entrypoint fixtures reported incomplete Swift import; four opaque/position
fixtures reported missing exact native endpoint identity. These outcomes remain
visible. No model repair, repeated matrix or fixture execution was performed.
The 284 case phase commands recorded exit zero, no timeouts and tracked-process
cleanup success; that observation does not prove aggregate descendant containment.

Observed run wall time was 534 seconds, summed case time 529.010 seconds and
maximum case time 10.317 seconds. These are diagnostic costs, not comparative
performance certification. The complete local output tree was about 165.4 MiB;
the committed evidence subset is about 9.0 MiB, excluding module caches and
Joern working copies. Original hashes and failed prefixes remain intact.

`python3 -O scripts/check-joern-current108-results-v1.py` independently reconstructs
the normal reports from the registered plan, admission, decisions, commands,
native output and configuration hashes. The resulting reports remain under
`reports/raw/joern-normal-v1/current108-2026-09-28-01/normal` as an unqualified
diagnostic lane. No scorecard, freeze, release or deployed publication changes.
