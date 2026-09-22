# A36 — 2026-09-22: independent Swift Joern activation and execution

This is the prospective #219 adapter record under #215, based on fixture and
CodeQL integration commit `257fd13e9f6dfa5ee29c561a42b61a72fb50268c` and the
[Swift applicability contract](swift-kernel.md). It changes no historical
configuration hash, fixture, report, population, or freeze. It does not publish
Swift results or activate Bifrost Swift support.

## Native frontend identity and activation

Joern **4.0.628**, upstream commit
`0b81c759a38b98b3abb4c90406818a90d6b299c1`, uses the released macOS ARM64
distribution and bundled SwiftAstGen **0.4.4**. The independent runtime is
Temurin **21.0.8+9**, matching the exact release root README's JDK 21 requirement.
The frontend-specific README still says Java 11; that older text does not replace
the distribution requirement. The Swift compiler is Apple Swift **6.4**,
`swiftlang-6.4.0.34.1`, Xcode **27.0 / 27A266a**, macOS **27.0 / 26A428** ARM64,
SDK **27.0 / 26A425**, target `arm64-apple-macosx27.0.0`. Every executable,
frontend and console JAR, parser asset, compiler and command identity is retained
in the activation evidence and machine-readable certificate.

The syntax-only `importCode(..., language = "SWIFTSRC")` route **fails the exact
identity control**: free source and sink calls acquire callee edges to same-name
static members of `Decoy`. A plain positive/negative pair produces 1/0 flows,
but the member decoy makes the intended native endpoint sets empty. The defect
reproduces on JDK 21 as well as the initially witnessed Java 26 installation.
Attempts 01–05 retain the actual declarations, calls, edges, controls and failed
measurement attempts. No bare-name matcher repairs these edges.

The pinned frontend already ships a compiler-backed remedy:
[`--build-log-path`](https://github.com/joernio/joern/blob/0b81c759a38b98b3abb4c90406818a90d6b299c1/joern-cli/frontends/swiftsrc2cpg/README.md),
introduced by [upstream PR #5632](https://github.com/joernio/joern/pull/5632).
It obtains declaration/call identities from the actual Swift compiler. The
shipped type provider filters compiler commands by module-directory names, and
reads compiler JSON from stdout. Attempts 06 and 07 retain unsuccessful build
log layouts and output redirection. Attempt 08 uses a directory named
`DataFlowBenchTaintSwift` and a witnessed `swiftc -typecheck` command without
`-o`, activating compiler-derived identities. No native graph/resolver is edited,
no distribution is forked, and no pin is changed. Searches and the related
upstream PR records are retained under `evidence/joern-swift/upstream-search-219`;
those bounded searches do not prove that no other upstream issue exists.

`adapters/joern/swift/query.sc` uses exact module-qualified native method
identities and single-target native callee edges, then selects the declared
argument or parameter node. File/line anchors constrain which native calls may
supply the benchmark endpoints. They never repair a missing or wrong callee.
Source text and bare function names never infer semantic identity. Each exact
configured identity must resolve to one native declaration. Parameter sources
are anchored at that declaration before index 1 is selected; an otherwise valid
observation cannot admit a second unanchored root or an ambiguous declaration.

## Model declarations and prospective partitions

All **33 core pairs / 66 assertions** remain executable candidates. Both
calibration pairs remain outside scored denominators. Modeling activation is
independent: declared source and sink roles, selective sanitizers, scalar
summaries, and uncalled handler parameters are each tested with model-on/off
controls and undeclared siblings. The scalar summary positive uses a constant
body, so the declared argument-to-return edge must carry the flow; its no-flow
sibling has an explicitly forwarding body. Neither optimistic external-call
propagation nor a listing of model declarations establishes activation.

`models.json` maps only exact compiler-derived method identities. The source and
sink/entrypoint query roles are similarly exact. Implicit-return controls retained
in model attempt 02 did not carry interprocedural flow without a summary;
explicit-return controls distinguish model activation from that measured native
body-analysis limitation. Canonical registry fixtures keep their original
implicit returns and are never edited to improve analyzer outcomes.

The per-template partition is committed before any registry execution. The
proposed executable modeling set comprises declared source, declared sink,
sanitizer kill, sanitizer selectivity, scalar summary, entrypoint parameter,
and entrypoint selectivity (**14 assertions**). Three templates remain
`unsupported` (**six assertions**) because the pinned declaration surface lacks
the exact required semantics:

- `summary-field` requires an edge into the specific `Box.payload` field while
  leaving `Box.spare` untainted. The native `FlowSemantic` destination is a
  parameter index/name, not a field/access path.
- `store-roundtrip` requires a persistent store identity plus equality of the
  write/read key across different methods. A same-call argument/return mapping
  supplies neither store identity nor a write/read relation.
- `store-separation` additionally requires receiver identity across calls; a
  receiver flow mapping alone cannot express the required key-sensitive store
  relation. A source on every getter or object-wide taint would change the model.

The exact pinned [grammar](https://github.com/joernio/joern/blob/0b81c759a38b98b3abb4c90406818a90d6b299c1/dataflowengineoss/src/main/antlr4/io/joern/dataflowengineoss/Semantics.g4)
and [native API](https://github.com/joernio/joern/blob/0b81c759a38b98b3abb4c90406818a90d6b299c1/dataflowengineoss/src/main/scala/io/joern/dataflowengineoss/semanticsloader/Semantics.scala)
are retained as primary-source evidence. Their argument names identify formal
parameters, not runtime key values or fields. These capability decisions precede
scoring and are independent of observed fixture outcomes. They do not inherit
another language's older Joern partition.

The two opaque-body modeling templates, six tool-native contracts, language
extensions, real projects and reserved tracks remain deferred exactly as in the
Swift contract. No new denominator is invented for them.

## Budgets, failures and evidence

The analysis budget remains **60 seconds / 512 MiB**. Unlike CodeQL's existing
extract/analyze split, Joern's normative timing granularity is `total`.
Typecheck, compiler-backed CPG extraction, overlay construction, query-script
compilation and flow querying all share one enforced wall-clock deadline.
Environment witnessing and input materialization are setup; the descriptive
reported total includes setup as well. Process-group timeout preserves evidence
and returns `inconclusive`; failed imports, inactive compiler metadata, malformed
output and missing exact endpoint bindings return `runner-error`.

Each subprocess is measured with macOS `/usr/bin/time -l`. Its individual maximum
RSS is retained, and a reading above the fixture limit proves a breach. A lower
reading cannot certify the aggregate process-tree peak, so normalized memory
remains null and otherwise determinate native outcomes become `inconclusive`
with an explicit memory diagnostic. Native endpoint/import errors take
precedence. Neither `-Xmx` nor a low launcher footprint is a process-tree memory
certificate. There is no clean budget-compliance claim.

The pinned `EngineConfig` also defaults to call/field depth 4 and argument
expansion caps of 1,000. `reachableByFlows` supplies paths but no exhaustion
certificate. The recorder retains these bounds; an empty native path set is a
provisional observation, never proof of unbounded completeness. Native output separates `query_completed: true` from
`analysis_completeness.status: unproven`, with the actual engine limits included.
Consumers reject the legacy `complete` field and any unsupported semantic
completeness claim. Even without a memory budget, an absence remains
`inconclusive`.

Raw graph/query JSON, argv, stdout/stderr, exit statuses, source and binary
hashes, environment and per-case manifests are retained. The native query result
is kept separately from normalized budget decisions. Every probe and registry
attempt has a fresh evidence directory; prior failures are preserved.

## Reproduction and validation

Use the distribution, JDK and compiler hashes in `activation.json`. Probe
commands write only separate non-scored evidence directories:

```sh
python3 scripts/probe-joern-swift.py --compiler-backed --joern /exact/joern --java-home /exact/jdk21 --output /new/native-probe
python3 scripts/probe-joern-swift-models.py --joern /exact/joern --java-home /exact/jdk21 --output /new/model-probe
python3 scripts/test-joern-swift.py
python3 scripts/verify-joern-swift-activation.py
```

After committing the exact configuration and resolved partition:

```sh
cargo run -- --population swift-synthetic-v1 run-joern-swift-kernel --joern /exact/joern --java-home /exact/jdk21 --tier core
cargo run -- --population swift-synthetic-v1 run-joern-swift-kernel --joern /exact/joern --java-home /exact/jdk21 --tier modeling
cargo run -- --population swift-synthetic-v1 run-joern-swift-kernel --joern /exact/joern --java-home /exact/jdk21 --tier calibration
```

Commands refuse existing evidence directories and require the activation and
configuration bytes to match their committed preregistration. Reports use new
`joern-swift-{kernel,modeling,calibration}` names. Repository report, evidence,
site and isolated historical release checks remain required. No release,
publication or complete-epic claim follows from adapter implementation.

## Review correction and retained attempts

The original configuration was committed before execution at `126c17c3`, with
the version-witness preflight corrected at `233e9402`. The preflight failure is
retained separately; no fixture was invoked by it. The first complete registry
run produced 66 core inconclusive, 14 modeling inconclusive, six modeling
unsupported, and four calibration inconclusive results.

Independent review required the explicit completion/uncertainty fields and
unique anchored parameter roots described above. That entire original run,
including configuration snapshots, reports, raw outputs, command logs and
manifest, remains byte-for-byte under
`evidence/joern-swift/execution-219/attempt-02`. Its original `complete` field is
not relabelled. Revised activation and fresh registry execution use a separately
committed configuration; no result is reinterpreted as if it had used that query.
The prospective per-template partition remains unchanged.
