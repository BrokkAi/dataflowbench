# Prospective normal-report execution

This is a new runner integration for the reviewed compiler-ordered extractor.
Preparation hashes inputs and emits an exact plan without running CodeQL. The
prepared local plan is not a reservation, compatibility qualification, analyzer
result or freeze. Execute requires a committed unchanged plan, exact runtime
file inventories, a plan-bound exclusive-slot reservation, at least 64 GiB free
at launch and a 40 GiB per-phase reserve. Current approximately 41 GiB free does
not satisfy launch capacity. Compiled fixture executables are never run.

The runner witnesses CodeQL's JSON product/version/build and combines it with
explicit extractor/schema/pack hashes for the patched build identity. Phase
records carry exact IDs and roles, extraction has 150 seconds and all query/
decode commands share one monotonic 75-second clock including overhead. Failed
commands and timeout prefixes remain evidence. An incomplete population remains
partial; no fake rows or normal full-population report are created for unattempted
cases. Original stdout/stderr and BQRS/decoded files are retained and hashed.

Queries are copied into a separate adapter with an exact dependency on the
entry-patched 6.8.4 library; historical lane files are unchanged. All 12 planned
kernel/calibration/modeling/opaque/native queries passed serial dependency
resolution and check-only compilation against the exact entry1 schema in
`evidence/swift-normal-query-check-2026-09-28-01`. This establishes compatibility,
not evaluated semantics. Requested RAM 2048 MiB was raised to 2638 MiB by CodeQL;
that observed minimum is retained and is not hard aggregate enforcement.

Compatibility receipts 01/02 retain plan-02/03 observations. A portability fix
required final plan-04; receipt 03 passed all 12 queries against that exact plan.
Plan-04 SHA-256 is `46df6af46ca562d53c37346ed8ed82f21ab205523b4b835d8976b96762e313f9`.
Earlier receipts are never relabeled as evidence for the final plan. Publication copies redact `/Users/dave` to `/REDACTED_HOME` only, with
original/published hashes and changed receipt bindings recorded; originals stay
local. Hash inventories and query/runtime input bytes are unchanged by redaction.

The prepared plan uses the existing full 108-case population, 96 controlled and
12 native rows, with lane-specific phase sequences (including persistence
coverage/scopes). It must be regenerated after implementation changes before
being committed for execution. Run the preparation command shown by
`scripts/run-swift-normal-v1.py prepare --help`; `execute` consumes that committed
plan plus a separate capacity reservation. Tests inject fake process results;
no analyzer runs are needed to validate witness serialization and budget guards.

## Dated pin review: 2026-09-28

The adjacent pin-review directory retains live GitHub release API observations.
CodeQL 2.27.1 is the latest stable CLI (published September 22); hold it and the
exact separately identified reviewed extractor/schema/QL patch. This is not a
claim that the patch is part of stock CodeQL.

Joern latest stable is 4.0.640 (published September 28). Hold the existing 4.0.628
for this bounded comparison to preserve the already recorded frontend/query
identity while integrating reporting; bumping now would introduce a separate
frontend/model change needing its own qualification. This hold does not transfer
old execution evidence. Before any current108 Joern report, independently verify
4.0.628's installed assets and shipped capabilities, assess the four opaque
cases, and preregister current-population decisions. The other 104 IDs require
fresh execution or freshly justified prospective unsupported decisions. Old
v1/v2 rows are not relabeled. Bifrost Swift remains unsupported.

## Remaining execution gates

The implementation binds full compiler/SDK/CLI/extractor/pack inventories,
rejects escaped compiler/SDK symlinks, checks exact query schema/dependency
resolution, and retains extraction-integrity/finalization records and post-run
database closure. Fake process and mutation tests cover witnesses and guards;
no end-to-end 108-case execution is claimed. Plan-04 has its exact-plan check-only receipt; it still needs independent runner
review, a committed unchanged plan and a real capacity reservation. No reservation exists. The 64 GiB launch target is
40 GiB reserve plus approximately 24 GiB projected scratch from prior diagnostic
growth, not proof of a hard maximum. The per-phase guard stops further work;
all stopped evidence remains, and this version never deletes per-case databases
or executes native fixtures. Conservative estimates do not certify resources.

Joern's current108 capability assessment remains open; this CodeQL implementation
does not assert unsupported for its four missing opaque cases or reuse its 104
old rows. No score activation or common release freeze follows from this PR.
