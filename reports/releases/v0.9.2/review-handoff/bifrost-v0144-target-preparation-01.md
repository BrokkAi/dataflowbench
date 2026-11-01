# Bifrost v0.14.4 target preparation (2026-11-01)

David authorized a fresh Bifrost v0.14.4 benchmark for the v0.9.2 target. The
20 Bifrost groups are replacements under new attempt identities; all previous
v0.13.1/v0.14.0 attempts and the separate v0.14.1 diagnostic remain retained.
This authorization does not lift the separate publication review hold.

## Engine and harness boundaries

No Bifrost engine source was changed. The official universal macOS artifact
was acquired from the public v0.14.4 release. Its binary SHA-256 is
`a3aa17a18be33e1e841c1bf317c6ca35a6aa3aaef452c607fafbb3b83aeec399`,
with build identity `ff5cf473f4ad414751911ff93ef79e1df1d35823`; the public
snapshot tag commit is separately `786891f9ed19d2086dfd6242ff15ca904b610620`.
The acquisition receipt and publisher checksum are retained under
`acquisition/bifrost-v0144-01/`.

Harness changes pin that identity, preserve the frozen v0.14.0 native evidence
profile, and add an explicit v0.14.4 native profile. Shipped policy catalogs
remain empty with automatic external-pack acquisition disabled; native cells
remain unsupported, never clean negatives. Kernel call modeling stays
`optimistic`; model-activation experiments stay `require-model`. No policy,
case, expectation, time budget or population was changed by this pin update.

Merged PR 298 separately requires Scala's `scala-library:2.13.16` POM evidence
and a fresh Scala run. Both binary and source jars were acquired from Maven
Central into task-owned storage. They must be staged into the actual isolated
Scala HOME Maven repository. The current Scala configuration requires the POM;
historical v0.14.0 policy-only reports remain historical with their original
hash and do not qualify as fresh amended Scala results.

## Qualification evidence and source validation

All 44 qualification commands ran once. Every command returned zero without
timeout or capacity loss. The preserved strict schema-5 qualifier failed on
schema-6 output; command success is separate from policy completeness. Of 39
policy reports, 36 are complete and the same three JavaScript controls retain
partial discovery, including an incomplete zero-finding negative. Those three
must remain inconclusive. No extra engine capture was run to repair reviewer
assumptions about optional run diagnostic counters or exit-code semantics.
The independent review and typed binding are separate retained artifacts.

After fixing current-version test fixtures and the historical native-version
alias, `cargo fmt --check` and all 310 Rust tests passed. Initial failures,
formatting output and final exact command streams are retained under
`validation/bifrost-v0144-source-01/`; the earlier validation diagnosis is in
`execution-state/v092/recovery-20261101/initial-source-validation-01.json`.

## Run and delivery status

At this preparation checkpoint no matrix group has been dispatched. A new
source-bound serial controller, independent review, committed source, optimized
harness identity, immutable plan and fresh resource admission must precede the
run. All global attempt history, consumed unclosed attempts, resource ceilings,
reserve floors and the single analyzer slot remain binding. The ledger starts
from its original 109-row SHA-256
`2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851`.

This checkpoint establishes neither benchmark completion nor semantic or
performance improvement. A final per-case comparison and complete all-fix
handoff are still required. Git history is preserved; detailed evidence is not
silently added back as large ordinary Git blobs. No publication is authorized.

## Retained source helpers

Two pre-existing scripts from this chat's earlier evidence-compression work,
`package-v092-evidence.py` and `test-package-v092-evidence.py`, are preserved
byte-identically in the source snapshot. They are separate from the packaging
tool already merged through PR 295. No automatic invocation, path relocation,
cleanup or packaging-tool replacement is added. All 11 integrity/security tests
pass; exact original hashes and the source-boundary rationale are retained in
`validation/bifrost-v0144-source-01/preexisting-packaging-helper-preservation-01.json`.

## C5 controller and resource review

The new target-specific controller preserves the immutable 84-group parent
contract and selects exactly its 20 Bifrost groups. Only runtime identities,
the new harness and the separately registered Scala staging are projected.
Prior failures and the consumed unclosed Smoke02 remain in the counters: 109
ledger rows correspond to 110 consumed benchmark attempts. Copied v0.9.0
evidence inside preparation source views is historical input, not a new
v0.9.2 attempt. Those copies still count toward disk capacity.

Nineteen focused tests exercise successful and failed recording, captured and
staged report mutation rejection, source/contract drift, historical read-only
verification, isolated Scala staging, exact attempt scope and auxiliary source
accounting. Independent source review and a formatting-only AST equivalence
addendum precede dispatch. The original reviewed source before the final EOF
newline correction is retained as a lossless compressed copy.

The actual pre-commit capacity check passed with 18,765,037,054 bytes of
existing working source plus a conservative 3,109,230,340 bytes for all 20 new
snapshots, below 30 GiB. It includes all 12 auxiliary source projections
(2,273,847,179 bytes). Retention was 24,368,486,255 bytes and scratch was
1,624,560,131 bytes, each below its 24 GiB ceiling. The exact committed source
projection and a fresh 127 GiB admission check remain mandatory at launch.

Original HTTP response headers retain CRLF and raw validation logs retain
original whitespace. Full data-inclusive whitespace output is recorded rather
than altering hash-bound evidence; source-code whitespace is checked separately.

The immutable v0.9.0 parent execution contract is restored byte-identically as
one explicit metadata input in the current source snapshot. Its frozen SHA-256
is `8597f343542d652e0c7063dc9e5832797e9dfd8bf19975e9bcf309181249dd3d`.
This does not restore detailed historical attempts/results to ordinary Git or
claim ancestry from the rewritten old source graph.

## Pre-dispatch accounting correction

The first prepared contract remained unapproved and was never dispatched. A
subsequent source audit found that its C4-derived capacity member set omitted
19,101 copied historical files (2,833,495,180 logical bytes) referenced by later
ledger rows. The corrected controller unions every ledger source-input path
for historical/current repository capacity accounting, while keeping those
old raw paths out of the finite 44-file current source/materialization closure.
The corrected baseline also counts those additional paths in the current
repository, so the total change exceeds the copied-file subtotal.

The corrected actual precheck passed: 21,868,573,192 working-baseline bytes
plus a conservative 3,111,600,000 bytes for all 20 fresh snapshots is below
30 GiB. Retention was 24,369,091,551 bytes and scratch 1,624,560,131 bytes,
both below 24 GiB. Limits, source cases and engine/model flags did not change.
All 19 focused tests and independent source review03 passed on the repair.

The original unapproved `contract.json` (SHA-256 `12a4716def54f87d40b0325ac9794054ef4f7ba3fde6aefdec295e7f3108b5eb`)
is preserved in place and as a lossless compressed copy. Its preliminary
approval recommendation was explicitly put on hold. A new committed source
and `contract-02.json` are required; no benchmark attempt was consumed by
this source-only correction.
