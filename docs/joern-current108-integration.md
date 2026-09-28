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
