# A35 — 2026-09-22: independent Swift CodeQL activation and execution

Prospective adapter work for #218 under #215, based on fixture commit
`f3794bb7bb2136d7e1bf8a63a92f2ea3f18620b5` and the
[Swift contract](swift-kernel.md). No historical report, population, or freeze
is replaced. The repository already has two documents titled A34 (C extraction
correction and the separate hosted Swift compilation profile); this amendment
uses A35 without silently renumbering either historical document.

## Exact pins and activation

CodeQL CLI **2.27.0**, build `b47b3e59262c95aff4eeb84ac72d09e25a9c37e9`,
macOS distribution SHA-256
`95e96dce9eff1c626e4da1f30d6dda00a893ee5015037045bf142947a8578781`;
Swift extractor executable SHA-256
`680adbee37bdbfc5fe0a4b6d63c45bdae23fcf3bb2210530a7b751b58f319530`.
`codeql/swift-all@6.8.3` comes from the exact source tag at commit
`c6baf479093fafc81d4655dc2014dc583360308e`; the adapter commits its transitive lock.
The retained pack-tree manifest hashes each installed pack's sorted relative-path
and SHA-256 records. No moving `latest` resolution is used.

The independent local compilation/extraction profile is Apple Swift 6.4
(`swiftlang-6.4.0.34.1`, `clang-2100.3.34.1`, driver `1.168.6`), Xcode 27.0
build `27A266a`, macOS 27.0 build `26A428` ARM64, SDK 27.0 build `26A425`, target
`arm64-apple-macosx27.0.0`. Compiler SHA-256:
`cf81104bf554eef05e28a8bb5285c763f1323b4511b944d755d8bdd6cb8db717`.
This does not transfer activation to the hosted A34 fixture-validation profile.

Separate non-scored controls are retained under
`evidence/codeql-swift/activation-218`, including failed authoring, extraction-order,
cache-resolution and stale-query attempts. Top-level expressions had resolved
AST calls but no dataflow endpoints; fresh function-wrapped controls matched the
fixture construction and activated. A premature query left a historical error
notification in later SARIF despite exit 0; the verifier rejected it and a fresh
database supplied the near-miss evidence. Query import edits require `--rerun`:
reinterpreting cached BQRS is not fresh query evaluation.

Core activation uses an independent positive, unrelated-value negative, and
wrong-signature/same-name-member decoys. Modeling activation uses model-on/off
controls for each declaration surface, field/key siblings, uncalled handler
siblings, and distinct allocation receivers. The external-summary calibration
positive has a constant-return body, so its declared edge is load-bearing.
The machine-readable certificates bind exact query and raw-control hashes.

## Declaration identity and prospective partition

The committed `adapters/codeql/swift/partition.json` is the per-template
execution partition and must be committed before registry execution. Core is all
33 applicable pairs (66 assertions); controlled modeling is all ten applicable
pairs (20 assertions), subject to separate model activation; calibration is two
pairs (four assertions), excluded from scores. No unfavorable core outcome can
remove a template. No new native, opaque, extension or real-project denominator
is created.

Free endpoints bind resolved module, free-function identity, argument-label
signature, arity and structural Swift.Int/Swift.String types. Modeled declarations
bind module/type/member, receiver/static kind, parameter and return types. Swift
method interface types include an explicit receiver-function layer; predicates
inspect the nested function result structurally. No source-text or display-string
matching supplies semantic identity.

The pinned `ExternalFlow.qll` generic CSV interpreter forces an empty namespace;
it is not used to assert module-specific identity. The checked-in QL predicates
own the controlled models through `ConfigSig`. Summary-field flow binds the exact
Box.payload declaration and CodeQL local object provenance. Persistence binds
literal key values; static stores bind the exact type, while receiver stores
require CodeQL value flow from the same resolved allocation to both receivers.
These are model semantics and analyzer-derived alias relations, not concrete
runtime claims. Undeclared siblings are observed by the endpoint probe without
being declared taint sources/sinks.

The two opaque modeling identities, six native API/model contracts, Swift Result
extension and real-project work remain deferred exactly as in the Swift contract.
Bifrost Swift remains unsupported. No Joern implementation is included.

## Budgets and meaningful incompleteness

The fixture thresholds remain unchanged: 60 seconds analysis and 512 MiB where
specified. The schema calls these analysis budgets and requires reporting an
overrun rather than silently rebudgeting. Existing CodeQL runners do not enforce
RSS or elapsed limits, and write null peak memory; that is a pre-existing gap,
not authorization to claim compliance here.

The Swift runner limits the entire `database analyze` process group to the case
wall-clock budget, including any query compilation and result interpretation.
Database creation/Swift compilation is retained as its own phase, consistent
with the existing Rust/C++ CodeQL extraction-versus-analysis distinction, with a
180-second operational timeout. No analysis phase is removed from the budget.
The analyzer receives the case's memory value through `--ram`; its effective
minimum and any automatic increase are retained in stderr. This option is not a
process-tree memory limit.

`/usr/bin/time -l` reports maximum RSS, retained as `time_maxrss_mb`. It is not
represented as a certified aggregate process-tree peak. A measured individual
peak over 512 MiB proves a budget breach. A lower reading does not prove aggregate
compliance; without that proof this runner records `inconclusive` with a precise
memory-compliance diagnostic and null normalized peak memory. Neither condition
is a clean negative or a language-unsupported decision. Failed extraction, query
execution, or missing exact endpoints remains `runner-error`, taking precedence
over resource uncertainty. No scored-memory-compliance claim is made by activation.

All command argv, stdout/stderr, exit statuses, timings, toolchain witnesses,
fixture hashes, BQRS, SARIF, extraction logs and diagnostics are retained. Runs
use fresh task-owned scratch directories and refuse to overwrite prior evidence.
End-to-end timing remains descriptive, not a performance-track certification.

## Reproduction

Use the witnessed local toolchain and exact CodeQL archive above. Install the
locked pack with `codeql pack install adapters/codeql/swift --common-caches=<cache>`.
Pass `<cache>/packages` as the explicit `--codeql-packs` directory; the runner
verifies every pack's content digest against the activation manifest on each case.
Run the activation verifiers and repository validation first, then commit the
configuration and partition before running:

```sh
python3 scripts/verify-codeql-swift-activation.py
python3 scripts/verify-codeql-swift-models.py
cargo run -- --population swift-synthetic-v1 run-codeql-swift-kernel --codeql /exact/codeql --codeql-packs /exact/cache/packages --tier core
cargo run -- --population swift-synthetic-v1 run-codeql-swift-kernel --codeql /exact/codeql --codeql-packs /exact/cache/packages --tier modeling
cargo run -- --population swift-synthetic-v1 run-codeql-swift-kernel --codeql /exact/codeql --codeql-packs /exact/cache/packages --tier calibration
```

Each command refuses an existing evidence directory. Preserve previous attempts
in a separate immutable location before a new independently identified run; never
remove a failed attempt to make the new result appear to be the first. Reports
are `reports/codeql-swift-{kernel,modeling,calibration}.json`, with corresponding
raw directories. This command does not publish or rewrite a release freeze.

Registry execution retains verbose extractor logs as lossless `.log.txt.gz` files.
Phase durations use a monotonic clock and are also exported in standard case timing sidecars.
