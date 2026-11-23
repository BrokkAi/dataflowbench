# Accepted diagnostic Swift invocation costs

Campaign `20261122-08` now has a separate retrospective acceptance for **96
unchanged diagnostic invocation-cost rows**, without rerunning any analyzer.
The [acceptance receipt](joern-swift-audit-01/validation-receipt.json) is bound
to the exact capture, release decisions and reviewed offline verifier.

Exactly twelve diagnostics were corrected in new report projections. These
rows are declared-unsupported native cases with no invocation, no output and
zero duration; they remain excluded from latency samples. Their authoritative
role-specific wording comes from the frozen v0.9.2 declared-scope decision
records, matched by exact case, fixture, population, tool and configuration
identity. The mapping retains the original historical reason and both sources.
It does not transfer the release decisions' JVM/control qualification.

All 108 corrected rows match the frozen outcome, diagnostic, checkpoint and
anchor fields. Every other captured report field is unchanged. The accepted
cost artifact contains the same 108 cost rows as the original, including the
twelve excluded declines. All raw timing values, raw links and identities are
preserved.

**Acceptance is limited to diagnostic costs.**
All 96 attempted normalized outcomes remain inconclusive. Ninety-two invocations
completed three phases; four completed only typecheck and frontend and never
ran the query. Those partial costs remain explicitly listed. Settled timing,
full-model qualification, memory/process containment, cold/warm equivalence,
cross-release performance and publication acceptance are not conferred.

The original controller terminal remains failed. Its reports, raw evidence,
cost extraction, README and inventory remain byte-identical; their historical
zero-acceptance statements are superseded only by this separately versioned
diagnostic receipt. No frozen baseline or previous mismatch record changed.
All 7,559 sealed capture files were verified before and after derivation.

Validation: 12 pure reconciliation tests and eight CLI/file-boundary tests pass.
The real capture passed read-only validation, the new projections were compared
with immutable release blobs, and the copied costs were checked for exact
equality. The implementation commit used for acceptance is `895c16af7b`.

The [A37 amendment](../../../../docs/latency-v092-20261123-decline-wording.md)
records the user-authorized correction boundary and all inherited limits,
including A31 diagnostic host admission and A36 retrospective storage accounting.
The [current frontier](chain-frontier-01.json) still records 94 of 95 original
commands attempted: CodeQL Swift's missing pinned extractor remains blocked,
and Joern Rust's substantive mismatch remains quarantined. This reconciliation
does not broaden the permission to correct other mismatches.
