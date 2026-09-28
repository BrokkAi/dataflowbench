# Prospective Swift normal reports

The versioned `scripts/swift_normal_reports_v1.py` exporter converts a **new**
registered run into normal `result/v1` reports. It does not convert the historical
60-second run, failed 75-second retry, ten-control experiment or two structural
controls into current108 results. No fresh analyzer run, real normal report,
freeze or release is supplied by this implementation.

The input plan schema discriminator is `swift-normal-report-plan/v1`; the run is
`swift-normal-report-run/v1`; each retained raw record is `swift-normal-raw/v1`.
`scripts/test-swift-normal-reports-v1.py::sample` documents the complete input
shape using explicitly synthetic records. It is test data, not an executable
production plan. Future runner integration must retain actual witnessed fields.

The exporter verifies exact population/case/fixture hashes and case metadata,
recomputes the existing selected-population fixture revision, requires all 108
IDs exactly once, and derives partitions from track, profile, tier and registered
configuration. Current fixtures produce 96 benchmark-controlled and 12 tool-native
rows, split into five tier/profile groups; those counts are verified in tests,
not supplied as a substitute for metadata checks. Different configurations always
remain separate. Configuration hashes cover sorted repository paths and bytes.

A new plan must precede the run, bind the exact population revision, tool/build/
adapter identity and configuration files, and select attempt or unsupported for
every case. Runtime identity requires a successful retained version command,
nonempty original stdout and a matching structured observation within run times.
Tool-specific banner parsing remains the runner's responsibility; this exporter
checks bound provenance and never infers a version from arbitrary text. Missing
or placeholder identity, timing, cache mode, raw data or command evidence fails
closed. Nonzero invocation failures require runner-error; deadlines retain
BudgetExhausted. Case anchors are copied from verified case metadata and observed
checkpoints from raw records, never from expected flows.

Unqualified reached/not-reached/inconclusive observations export as inconclusive;
runner-error remains runner-error. Unsupported is accepted only with a matching
prospective, evidence-backed capability decision reviewed before registration,
no execution and zero execution duration. A post-run unsupported label is not a
capability decision. This boundary checks the decision's provenance and timing;
its underlying analyzer capability still needs independent review. No boolean
or RSS field enables scoring. Raw state must agree with the normalized result,
while raw_outcome and original diagnostics preserve the observation separately.

Usage after a future run is registered and performed:

```sh
python3 scripts/export-swift-normal-reports-v1.py --plan <new-plan.json> --run <new-run.json> --output <new-directory>
```

The output directory must not exist. The command emits normal reports plus a
coverage audit; it neither executes analyzers nor creates a freeze. A frozen
raw record binds references to native artifacts by digest; the exporter verifies
those references. The existing general freeze validator validates top-level raw
record bytes and typed outcomes, not recursively every arbitrary reference.
Retain and independently replay the full referenced closure before publication.

## Existing freeze boundary and next execution plan

`src/population.rs` already supports `swift-synthetic-v3` with the pinned
population digest. `src/freeze.rs::build_freeze_manifest` requires every active
population member and recomputes the hash over the union of selected cases;
`fixture_revision_for_manifest_cases` hashes sorted case paths/bytes and declared
fixture names/bytes. No freeze-validator change is needed. A Swift-only freeze
can use all 108 selected cases at their existing population revision. A combined
release needs one prospective common population revision for **every included
report**, so old other-language reports cannot be pooled into that freeze.

The new Rust regression generates all 108 synthetic rows through the exporter,
validates five normal reports with the existing freeze validator, and rejects a
rehashed attempt to promote inconclusive raw evidence to not-reached. This is
schema/integrity evidence only: unit fixtures bypass Git release checks and do
not claim a release-qualified runtime.

Before real runs, record dated pin bump/hold decisions, exact patched CodeQL
identity and native/query/config closure, a new immutable 150-second extraction /
75-second shared-analysis contract, output namespaces and storage/host reservation.
Joern's existing 104 IDs belong to old revisions; each needs a current run or a
new independently justified prospective unsupported decision. Four opaque IDs
need explicit current capability decisions or execution. Keep Bifrost Swift
unsupported. No other-language reruns are selected until the exact common-release
population and included report set are decided; the historical 1104-case/92-lane
release-preparation snapshot remains unchanged.
