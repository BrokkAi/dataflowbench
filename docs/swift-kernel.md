# Swift registry applicability and adaptation contract

Preregistered 2026-09-22 for [#216](https://github.com/BrokkAi/dataflowbench/issues/216),
prerequisite to epic [#215](https://github.com/BrokkAi/dataflowbench/issues/215).
Registry audit base: `2fa72a8994978a0573c958218d998bbe282497e5`.
This is prospective documentation: no Swift fixtures, analyzer activation,
scored runs, or published support are established here. Fixture implementation
belongs to #217, independent CodeQL and Joern integration to #218/#219, and
validation/publication to #220. Bifrost remains explicitly unsupported for Swift;
its supported-language inventory must not be expanded by this work.

## Inventory and classification

The audit enumerates unique `template_id` values in `cases/**/case.json`, checks
the family contracts, and separately reviews `corpus/real-project/` and reserved
tracks. There are 58 synthetic identities: 2 calibration, 16 classic propagation,
14 challenge (including exceptional-exit persistence), 5 recursive composition,
12 controlled modeling, 6 native, and 3 existing language extensions. Challenge
and recursive cases use `score_tier: core`; neither is a new score-tier enum.
The historical `populations/v0.7.0.json` is not the current-template inventory.

`direct` means the semantic construction survives with syntax changes;
`adapted` names the Swift construction preserving its intent; `inapplicable`
means that construction cannot preserve the template within the stated language
scope. `deferred` is an explicit unfulfilled scope item, not a zero denominator,
an analyzer verdict, or evidence that Swift lacks the semantics. An analyzer's
inability to analyze an applicable construct never makes it language-inapplicable.

Scope is synchronous, standard-library Swift, plus separately preregistered real
platform APIs for future native cases. No Objective-C runtime bridge, C++
interop, macros, actors, concurrency, UI framework, or third-party packages are
introduced to manufacture equivalents. Swift `class` instances preserve reference
identity; structs, `Array`, and `Dictionary` have value semantics. Shared heap
and alias fixtures must therefore use classes, not copied structs. This follows
[Swift's value/reference distinction](https://www.swift.org/documentation/articles/value-and-reference-types.html).

Every executable row below is a positive/near-miss negative pair. The positive
has source dependence; the negative changes only the stated separating or
killing operation and retains the source-backed computation (the infeasible-path negative intentionally leaves its source assignment unreachable). Modeling expectations are
model semantics, not claims about the concrete runtime body.

## Calibration (2)

| Stable template ID | Decision | Positive / negative construction |
| --- | --- | --- |
| `dfb-template-one-hop-relay` | direct | Free function returns its argument; query source-fed call versus clean-fed call while retaining both calls. |
| `dfb-template-modeled-external-summary` | adapted | Separate-file `ThirdPartyBridge.passThrough(_:)` with declared input-0-to-return summary; negative uses a sibling with explicit no-flow summary. Requires activation, otherwise unsupported. |

These remain calibration, outside every scored denominator. The historical
single-polarity calibration cases are not rewritten; Swift authors new pairs.

## Classic propagation (16)

| Stable template ID | Decision | Positive / near-miss negative |
| --- | --- | --- |
| `dfb-template-direct-propagation` | direct | Sink source local / unrelated clean local; retain source evaluation. Negative mechanism: `unrelated-value`. |
| `dfb-template-local-overwrite-kill` | adapted | Mutable `var` reaches sink / overwrite same variable with clean value. Negative mechanism: `overwrite-kill`. |
| `dfb-template-local-multi-step-chain` | direct | Three source-backed local copies in both; sink final copy / unrelated clean value. Negative mechanism: `unrelated-value`. |
| `dfb-template-arithmetic-expression-propagation` | direct | Bounded integer multiply/add expression computed from source in both; sink computed value / unrelated clean value. No overflow. Negative mechanism: `unrelated-value`. |
| `dfb-template-call-context-separation` | direct | Identity helper called with both source and clean input; select tainted / clean call's return. Negative mechanism: `call-context-separation`. |
| `dfb-template-argument-position-separation` | direct | Two-argument helper returns argument 0; swap source from position 0 to position 1. Negative mechanism: `call-context-separation`. |
| `dfb-template-return-relay-one-hop` | direct | Source return via one helper in both; sink return / unrelated clean value. Negative mechanism: `unrelated-value`. |
| `dfb-template-return-relay-two-hop` | direct | Source return via two helpers in both; sink return / unrelated clean value. Negative mechanism: `unrelated-value`. |
| `dfb-template-object-separation` | adapted | Two distinct class instances; write one, read same / other instance. Negative mechanism: `object-separation`. |
| `dfb-template-same-object-field-separation` | direct | One class instance with two stored fields; read written / clean sibling field. Negative mechanism: `field-separation`. |
| `dfb-template-alias-propagation-separation` | adapted | Two references to one class instance / second reference to distinct instance; mutate through first and read through second. No struct copy or `inout` substitute. Negative mechanism: `object-separation`. |
| `dfb-template-array-element-separation` | adapted | Initialized Swift array, fixed valid indices; store and read same / distinct element. No shared-buffer alias claim. Negative mechanism: `field-separation`. |
| `dfb-template-infeasible-branch` | direct | Source assignment on feasible / constant-false branch, with initialized clean local and sink afterward. Negative mechanism: `infeasible-path`. |
| `dfb-template-branch-join` | direct | Source initializes local; one feasible arm preserves it / both arms overwrite with clean values before joined sink. Negative mechanism: `overwrite-kill`. |
| `dfb-template-loop-carried-kill` | adapted | Mutable local carried through a bounded nonempty `while` / overwritten before loop exit. Negative mechanism: `overwrite-kill`. |
| `dfb-template-exception-catch` | adapted | `do`/`throw`/`catch` with fixture-private `enum Signal: Error`; associated payload carries source / clean value while source is still evaluated; pattern-match the exact error case and sink its caught payload. Negative mechanism: `unrelated-value`. |

Swift errors provide explicit recoverable transfer from a `throws` function
through `try` to `catch`. This contract tests that transfer and surviving state,
not Java exception objects, Objective-C exceptions, traps, or stack-unwinding
implementation details. `try?`, `try!`, `fatalError`, optional returns, and
`Result` branching are not substitutes. The [Swift language reference](https://github.com/swiftlang/swift-book/blob/main/TSPL.docc/LanguageGuide/ErrorHandling.md) explicitly distinguishes this from runtime call-stack unwinding. That implementation distinction must remain visible in comparisons; these adaptations claim typed transfer and payload/state preservation only.

## Challenge (14, folded into core)

| Stable template ID | Decision | Positive / near-miss negative or exclusion |
| --- | --- | --- |
| `dfb-template-chal-reflective-invocation` | inapplicable | Standard-library Swift has no general string-selected method invocation preserving this contract. `Mirror` inspection is not invocation; a closure dictionary would duplicate dispatch-table. Objective-C selectors are outside this scope. |
| `dfb-template-chal-computed-property` | adapted | `Dictionary<String, Int>` with variable keys, both initialized; same computed write/read key / distinct known keys. This tests keyed storage, not reflective stored-property mutation. Negative mechanism: `field-separation`. |
| `dfb-template-chal-dispatch-table` | adapted | Dictionary containing two function values; variable key selects forwarding / argument-dropping function, then invokes it. Negative mechanism: `call-context-separation`. |
| `dfb-template-chal-closure-capture` | direct | Factory returns closure capturing source / clean immutable local; caller invokes after factory returns. Negative mechanism: `unrelated-value`. |
| `dfb-template-chal-function-field` | direct | Class stores closure in property; separate method loads/invokes it from forwarding holder / distinct dropping holder. Negative mechanism: `object-separation`. |
| `dfb-template-chal-callback-registration` | direct | Register closure in class-held array, separate driver iterates callbacks with source; callback forwards / drops input. Negative mechanism: `unrelated-value`. |
| `dfb-template-chal-anonymous-implementation` | inapplicable | Swift protocols have nominal conforming types, not anonymous inline conforming classes. Named protocol implementations, opaque result types and closures do not preserve unnamed-type interface dispatch; do not relabel them. |
| `dfb-template-chal-map-iteration` | adapted | Iterate dictionary `(key, value)` entries and sink value / iterate separate clean dictionary. No direct lookup replacement or order dependency. Negative mechanism: `object-separation`. |
| `dfb-template-chal-nested-access-path` | direct | Class chain `a.b.c.value` / clean sibling `a.b.c.other`; depth at least three. Negative mechanism: `field-separation`. |
| `dfb-template-chal-element-object` | adapted | Array of separately constructed class instances; read written element's field / other element's field at fixed indices. Negative mechanism: `field-separation`. |
| `dfb-template-chal-deep-relay-chain` | direct | Six distinct helpers forward source / clean value through identical chain. Negative mechanism: `unrelated-value`. |
| `dfb-template-chal-recursive-carry` | direct | Self recursion, constant depth 5, base returns payload / overwrites payload before return. Negative mechanism: `overwrite-kill`. |
| `dfb-template-chal-context-pair-depth2` | direct | Two wrapper contexts share a depth-two relay; sink source context / clean context while both remain present, following challenge A1. Negative mechanism: `call-context-separation`. |
| `dfb-template-chal-interprocedural-exception-persistence` | adapted | Callee writes source to caller-owned class field then throws private signal; caller catches, reads and returns field to outer sink / callee overwrites field before throwing. Negative mechanism: `overwrite-kill`. |

The computed-key adaptation follows the contract's keyed-location intent; it
makes no claim that Swift supports dynamic object member names. Dynamic-dispatch
results retain the challenge contract's approximation-character interpretation.

## Recursive composition (5, folded into core)

All follow [recursive-composition.md](recursive-composition.md): depth 3,
integer payload, bounded `+1`, source/sink outside the recursive component,
live topology in both polarities and a marked base-case kill.

| Stable template ID | Decision | Positive / near-miss negative |
| --- | --- | --- |
| `dfb-template-chal-recursive-payload-transform` | direct | Add 1 on descent and unwind / base overwrites payload with 0 before returning. Negative mechanism: `overwrite-kill`. |
| `dfb-template-chal-mutual-recursive-transform` | direct | A/B alternate, transform on descent and return / both bases kill payload; depth 3 reaches B base. Negative mechanism: `overwrite-kill`. |
| `dfb-template-chal-recursive-heap-unwind` | adapted | Shared class box receives payload at base, field incremented on unwind / same field overwritten at base before unwind. Negative mechanism: `overwrite-kill`. |
| `dfb-template-chal-recursive-callback-transform` | adapted | `walk` invokes a function-typed parameter; separate `step` transforms, calls `walk` with itself, transforms return / `walk` base kills payload. The cycle must cross the indirect call. Negative mechanism: `overwrite-kill`. |
| `dfb-template-chal-recursive-exception-persistence` | adapted | Base writes class field, throws private signal through all recursive `throws` frames to outer catch; sink field+1 / base overwrites field before throwing. No inner catch or normal-path bypass. Negative mechanism: `overwrite-kill`. |

Planned core: **33 pairs / 66 assertions** (16 classic + 12 challenge + 5
recursive). The two excluded identities remain listed above. This prospective
count is not an active population or a change to any frozen denominator.

## Benchmark-controlled modeling (12)

Use `score_tier: modeling`, `model_profile: benchmark-controlled`. The exact
entity/role/position declarations and negative mechanisms in
[modeling-matrix.md](modeling-matrix.md) remain normative. Bind Swift module,
type, member including argument labels/signature, and zero-based declared
parameter position excluding receiver. Never use a bare-name match. Separate
source module files still compile together as one fixture.

| Stable template ID | Decision | Swift construction / negative or deferral |
| --- | --- | --- |
| `dfb-template-model-declared-source` | direct | `Config.fetchRemote()` declared return source / undeclared `fetchLocal()`, both constant-returning static methods. |
| `dfb-template-model-declared-sink` | direct | `Audit.record(_:)` parameter 0 declared sink / undeclared `discard(_:)`, identical dropping bodies. |
| `dfb-template-model-opaque-propagator` | deferred | Required reflective self-dispatch body has no standard-library Swift equivalent. Ordinary forwarding or dictionary dispatch cannot be presumed opaque. Needs separately reviewed body/opacity amendment before fixtures or scoring. |
| `dfb-template-model-propagator-position` | deferred | Same opacity prerequisite; eventual declaration must propagate position 1 only, with source at position 0 in negative. Do not substitute a visible two-argument helper. |
| `dfb-template-model-sanitizer-kill` | direct | `Clean.scrub(_:)` identity body with declared sanitizer / direct source path as positive. |
| `dfb-template-model-sanitizer-selectivity` | direct | Undeclared identity `Clean.sanitize(_:)` positive / declared identity `scrub(_:)` negative. |
| `dfb-template-model-summary-through` | adapted | Separate `Bridge.swift`, escaped Swift member name `` `pass` `` with input-0-to-return summary / `hold(_:)` explicit no-flow summary; both identity bodies. |
| `dfb-template-model-summary-field` | adapted | `Bridge.deposit(_:_:)` empty body, declared write from argument 0 into argument 1's class field `payload`; read payload / spare. |
| `dfb-template-model-entrypoint-parameter` | direct | Uncalled `Handler.onRequest(_:)` parameter 0 declared root/source / undeclared `onIgnored(_:)`; no synthetic fixture call. |
| `dfb-template-model-entrypoint-selectivity` | direct | Same class has uncalled `onDeclared(_:)` and `onUndeclared(_:)`; only former is root. |
| `dfb-template-model-store-roundtrip` | adapted | Fixture-local static `Store.put(_:_:)` no-op and `get(_:)` clean-returning stub, separate write/read procedures, declared primary store; same / different key. |
| `dfb-template-model-store-separation` | adapted | Two class `Store` receivers with no-op/clean-returning stubs; declared persistence bound to receiver; same / distinct receiver. |

Ten pairs (20 assertions) are language-applicable; two remain deferred. This
is not a claim of activated modeling support. The declared store, summaries and
roots must be load-bearing; concrete execution cannot validate their abstract
expected flows. Model-on/model-off controls belong to the adapter activation
record, with known optimistic defaults excluded as proof of model activation.

## Tool-native modeling (6, all explicitly deferred)

These use `score_tier: modeling`, `model_profile: tool-native`, never a `native`
score tier. The existing N1 language rows cannot be transplanted to Swift, and
fixture-local `dfb_source`/`dfb_sink` wrappers cannot stand in for platform APIs.
Each row requires a dated Swift native API contract and independently pinned
shipped-model inventory before implementation/scoring:

| Stable template ID | Decision and precise missing contract |
| --- | --- |
| `dfb-template-native-source-sink` | deferred: select exact platform source and dangerous sink identities, signatures and safe negative argument, then audit shipped coverage. |
| `dfb-template-native-propagator` | deferred: select real platform transformation between those endpoints, with a clean-input near miss; no mock opaque helper. |
| `dfb-template-native-sanitizer` | deferred: select real sanitizer with documented safety for the chosen sink context and matching shipped model; a similarly named escaping API is insufficient. |
| `dfb-template-native-summary` | deferred: select exact platform boundary and shipped summary with a separating negative; no benchmark-supplied model. |
| `dfb-template-native-entrypoint` | deferred: select real platform lifecycle/request callback and undeclared sibling, plus build/runtime identity proving signature binding; invented handler names do not qualify. |
| `dfb-template-native-persistence` | deferred: select real platform write/read pair with exact receiver/key semantics and near miss; no local dictionary presented as persistence. |

These are missing API/model preregistrations, **not language impossibility**.
No Swift native denominator exists yet. #220 must disclose these deferrals;
epic completion requires explicit acceptance or a subsequent contract and
implementation, not silent omission. The same applies to the two modeling
opacity deferrals.

## Existing extensions, real projects and reserved tracks

| Registry identity / population | Swift decision |
| --- | --- |
| `dfb-template-c-error-code-return-path` | inapplicable as a C-specific identity; Swift error handling is covered above, not renamed C error-code flow. |
| `dfb-template-c-goto-cleanup-carry` | inapplicable: Swift has no `goto`; `defer` is not a goto edge. |
| `dfb-template-result-error-propagation` | deferred language-extension: Swift `Result.failure` with associated payload could be an explicit adaptation, but is not exception-catch and is outside this initial synthetic core. Requires its own pair contract before activation. |
| Real-project R1 and R2 | deferred, no new study commissioned. Existing protocol, frame, eligibility, seeded draw, pin/review records and accepted ground truth remain unchanged; no Swift repository is selected by this contract. A future Swift stratum requires prospective selection, immutable revisions/digests and independent review before analysis. |
| `value-flow`, `typestate`, `witness`, `performance` tracks | reserved: no executable Swift cases or denominators; this work activates none. Descriptive latency on future taint runs is a separate dimension, not permission to create a performance track. |

## Stable fixture identities, anchors and compilation

#217 must retain every template ID above. Use case IDs
`dfb-taint-swift-<scenario>-positive` and `...-negative`, with matching directories
under `cases/taint/swift/`; take existing scenario stems for classic cases and
the template suffixes required by recursive-composition.md. Modeling/native
scenario stems must be prefixed `model-`/`native-` to avoid collisions. Case IDs
are never recycled or renamed after publication. Every pair shares track,
profile, template and tier; polarity and explicit negative mechanism differ.

Use schema-v2 metadata and authored MIT provenance with a revision naming the
Swift tranche. List every `.swift` input in `fixture_files`. Put unique
`DFB-SOURCE: <id>` and `DFB-SINK: <id>` comments on the actual source expression
and sink argument (or model-declared parameter/API location), with exact file
and checked line hints; expected flow/nonflow entries reference those markers.
Use `DFB-WITNESS` on required transfer/base/composed operations and `DFB-KILL`
on overwrites. Anchors locate semantic nodes; comments alone cannot establish
entity identity. Zero/multiple resolved anchors or missing analyzed files fail
closed, never produce a clean negative.

Each pair must type-check **and link** independently, with `main.swift` for
executable top-level code and all companion files included. No implicit
cross-fixture module, cached extraction, package download or missing opaque
implementation is allowed. Compile with `swiftc -swift-version 6 -Onone`, an
explicit SDK and target triple, separate output/module cache per case. Pure
propagation/calibration fixtures use the standard library only. For concrete
propagation, run bounded controls with distinct source inputs and check positive
dependence and negative independence; do not execute dangerous native sinks.
Uncalled modeling handlers may compile with an empty main; do not call them to
manufacture analyzer roots.

Initial **fixture compilation pin**, observed locally on 2026-09-22 (not an
analyzer compatibility claim):

| Component | Exact identity |
| --- | --- |
| Compiler | Apple Swift 6.4, `swiftlang-6.4.0.34.1`, `clang-2100.3.34.1`; swift-driver `1.168.6` |
| Xcode | `27.0`, build `27A266a` |
| Host | macOS `27.0`, build `26A428`, `arm64` |
| SDK | macOS `27.0`, build `26A425` |
| Target | `arm64-apple-macosx27.0.0` |

Before any fixture validation or probe, witness these values anew and record
compiler path and SHA-256, full `swiftc --version`, `xcodebuild -version`,
`sw_vers`, SDK path/version/build, argv and environment in retained evidence.
Paths alone are not pins. If a pinned analyzer does not support this compiler,
stop that activation and commit a prospective compatible compilation-pin
amendment; never infer extractor compatibility from successful compilation.
No compiler or analyzer test result is asserted by this identity inspection.

## Analyzer prerequisites and prospective tier partitions

Primary sources reviewed 2026-09-22:

- [CodeQL system requirements](https://codeql.github.com/docs/codeql-overview/system-requirements/)
  require macOS for Swift extraction and a working independent build.
- [CodeQL compiled-language build modes](https://docs.github.com/en/code-security/reference/code-scanning/codeql/build-options-for-compiled-languages)
  documents Swift build capture. Use explicit manual clean compilation of all
  fixture files; do not copy another language's no-build recipe.
- [CodeQL Swift data-flow guide](https://codeql.github.com/docs/codeql-language-guides/analyzing-data-flow-in-swift/)
  documents `DataFlow::ConfigSig`, barriers/additional steps and global taint.
  This supports a candidate controlled query, not proof of model or frontend
  activation in the benchmark's pinned binary.
- [Joern frontends](https://docs.joern.io/frontends/) lists `swiftsrc2cpg` and
  `--language SWIFTSRC`. Select it explicitly; language auto-detection is not
  admissible evidence that the Swift files were analyzed.
- [Joern upstream requirements](https://github.com/joernio/joern#requirements)
  currently say JDK 21, while the older
  [installation page](https://docs.joern.io/installation/) says JDK 19.
  #219 must resolve requirements from the exact pinned release source and
  retain `java -version`, distribution digest, frontend/parser assets and
  their platform/architecture requirements; do not assume either moving page
  proves the chosen release works.
- [Joern custom flow semantics](https://docs.joern.io/dataflow-semantics/)
  documents method/argument flow mappings. It does not by itself prove Swift
  roots, heap summaries, selective barriers or persistence activation.

The following **pre-scoring partition** applies independently to CodeQL and
Joern. “Candidate” fixes the intended scored set conditional on binary
activation, not a supported verdict; pending cells cannot be scored yet.

| Tier / profile | CodeQL | Joern |
| --- | --- | --- |
| Calibration / controlled | Probe-only, both identities; summary activation separately gated | Same, independently gated |
| Core / controlled | Candidate all 33 applicable pairs; excluded reflective/anonymous identities as above | Candidate same 33 pairs; preserve bounded-analysis incompleteness |
| Modeling / controlled: source, sink, sanitizer pair categories (4 templates) | Candidate, pending identity-selective, model-load-bearing controls | Candidate, pending same controls; optimistic default propagation is not activation |
| Modeling / controlled: summary, entrypoint, store categories (6 templates) | Pending capability verification; no scored activation without dated per-template declaration-surface evidence | Pending capability verification on same basis |
| Modeling / controlled: opaque propagators (2 templates) | Deferred language-body contract | Same |
| Modeling / tool-native (6 templates) | Deferred API/shipped-model contract | Same |
| Language-extension, real-project, reserved tracks | No Swift scored activation | Same |

Before the first scored run, #218/#219 must commit independent exact binary
version/build/digest and Swift pack (CodeQL) or frontend/semantics (Joern) pins,
configuration hashes, budgets, and a resolved per-template scored/unsupported
partition. No “latest” assets or guessed Swift pack version. A still-pending
capability is a blocker to claiming full adapter delivery, not grounds for a
fabricated unsupported result. Verified absent capability is recorded as
`unsupported` with its precise declaration-surface reason. No core template may
be dropped merely because its measured result is unfavorable.

Activation probes use separate non-scored controls and evidence directories,
never scored case/report paths: compile/extract, inspect actual source/sink node
identity, prove a positive and separating negative, and inspect completion and
model-on/model-off evidence where applicable. Retain every attempted argv,
stdout/stderr, exit status, raw graph/query output, hashes and environment.
Probe evidence may establish activation; it cannot be relabelled scored evidence.
Any resulting partition amendment must land before fresh scored execution and
state its probe-derived basis. Historical freezes and failed attempts stay intact.

Scored results retain `reached`, `not-reached`, `inconclusive`, `unsupported`,
and `runner-error`. Missing endpoints or failed extraction are errors; incomplete
or budget-exhausted analysis is inconclusive, not absence of flow. A clean
negative requires an activated, complete query over the intended file and
endpoint identities. No pooled score across core/modeling/native/real-project,
profiles, or changed populations is permitted.

## Implementation touchpoints and handoff gates

This commit changes only this contract and its documentation-index link. Future
changes must register fixtures and validation atomically; a partially populated
Swift rollout must fail validation instead of shrinking the expected set.

| Surface | Required follow-up |
| --- | --- |
| `schemas/case.schema.json` | Admit Swift as a benchmark fixture language; preserve tier/profile/negative-mechanism semantics and validate anchors/provenance. This enum is not Bifrost's support inventory. |
| `src/templates.rs`, `src/cases.rs`, `src/tests/templates.rs`, `src/tests/cases.rs` | Add Swift's exact classic/challenge/recursive sets and rollout row, case selectors and 33-pair balance checks; test missing/extra/duplicate polarity and excluded templates. |
| `src/modeling.rs`, `src/native.rs` and their `src/tests/` counterparts | Register applicable Swift modeling identities and explicit deferred categories, then per-tool capability/activation partitions. Do not inherit the three-language M1/N1 constants as Swift evidence. |
| `src/population.rs`, `populations/` | Add a new prospective population only when fixtures exist; preserve `v0.7.0.json` and all digest-bound historical populations. |
| `src/main.rs`, `src/runtime.rs`, `src/batch.rs` | Wire independent Swift CodeQL/Joern runner commands, exact language dispatch, profile/tier selection, budgets and retention; reject unknown/partial wiring. |
| `src/adapters/codeql.rs`, `src/adapters/joern.rs`, `src/adapters/mod.rs`, matching `src/tests/adapters/` | Implement native endpoint identity resolution, extraction/graph completeness checks, five-outcome normalization and retained provenance. Add Swift-specific queries/configuration under `adapters/codeql/` and `adapters/joern/`, with pinned pack/semantics assets and README recipes. |
| `src/evidence.rs`, `src/report.rs`, `src/freeze.rs`, `src/results.rs` and corresponding tests/schemas | Ensure new evidence binds all Swift sources, compiler/SDK and analyzer/configuration identities; keep tier/profile partitions and immutable freezes. Change schema only where necessary, never fabricate fields in old reports. |
| `scripts/`, `.github/workflows/ci.yml` | Add independent compile/link validation and metadata checks in #217, with an explicitly provisioned pinned macOS/Swift environment; the existing Ubuntu Rust CI cannot certify Apple Swift compilation or CodeQL extraction. |
| `docs/swift-kernel.md`, `docs/applicability-matrix.md`, `docs/challenge-tier.md`, `docs/recursive-composition.md`, `docs/modeling-matrix.md`, `docs/native-profile.md`, `docs/adapters.md`, `docs/populations.md`, `docs/README.md`, `README.md` | Link implementation/activation status when it actually changes, carrying explicit exclusions/deferrals and prospective counts; do not rewrite historical tables as if Swift participated. |
| `docs/src/data/`, `docs/src/content/`, `docs/public/`, release scripts | #220 may publish only newly validated frozen evidence, distinguishing analyzer language breadth, fixture participation and measured support. No synthetic Swift result rows. |
| `corpus/real-project/`, `src/real_project.rs`, real-project schemas/contracts | No change in this tranche; any future Swift study requires the separate selection/review protocol above. |
| `src/adapters/bifrost.rs`, Bifrost supported-language metadata | No Swift support addition. Preserve explicit unsupported coverage even when reference tools activate. |

Before #217 is complete: compare the implemented unique template set with this
inventory, validate schema and balanced pairs, compile/link each polarity under
the witnessed pin, inspect negative mechanisms and anchors, and run focused
registry tests plus `cargo fmt --check` and `cargo run -- validate`. Adapter
issues add focused normalization/anti-vacuous-negative tests and independent
activation evidence. Before #220 publishes, run full repository CI and the
freeze/report/result validation contracts on the exact intended revision.

This contract can be completed without claiming those later gates passed.
Deferral resolution and pin/partition changes require dated, prospective
amendments under the repository governance rules, separate from changed fixture,
model or scored-evidence commits. No existing freeze is invalidated here.
