# Relocated Joern Swift qualification

This is untimed preparation for the separate `20261122-03` timing operation,
under [A30](../../../../docs/latency-v092-20261122-swift-recovery.md).
It does not modify the frozen v0.9.2 plan or any earlier timing capture.

The active prospective input is
`adapters/joern/swift-common-v2/plan-v092-02/qualification-pending-plan-05.json`.
Candidates 01–04 are retained, unused and superseded. The new runner preserves
all 108 cases, 12 unsupported cases, the complete old 33-reference configuration
closure, and only 11 reviewed relocation/provenance additions. Actual runtime
verification passed both in the chat worktree and a separate release snapshot.
The focused suite passed 17 tests; independent review passed after fixing the
configuration-closure gate.

Fresh controls captured all six fixtures, twelve off/on arms and 36 analysis
phase invocations. The outer supervisor exited zero without timeout or capacity
loss. Its elapsed time was 189.153 seconds; the control capture reports 143.928
seconds. These are setup/resource observations, not latency-corpus samples.
No CPU-triggered abort or wait was introduced, and no cleanup signal was sent.
The first launch failed before any analyzer dispatch because its resource call
omitted ancestor namespaces; that failure and the committed correction remain.

The analyzer-free replay established `measurement-with-known-limits` and created
`execution-plan-qualified.json`. Direct controls passed; all eight opaque arms
retain the exact endpoint-identity limitation. **Full model qualification and
scored activation remain false.** The receipt and replay graphs preserve that
strict incomplete assessment. The finalizer validated the receipt before
creating the separate final plan, then validated that plan against the runtime.

The post-control ownership audit checked 118 recorded process identities across
37 command records (including the version witness), found none still alive,
and observed the shared serial lock available. Process descendant containment
remains unproven; the audit does not promote that uncertainty into certification.

The regular-file qualification tree is retained locally and in the repository's
lossless evidence-bundle format under `controls-evidence-bundle-01/`. The bundle
records hashes, modes and timestamps and deduplicates repeated bytes. Use
`python3 scripts/evidence_bundle.py check <bundle>` for delivery verification;
`--restore <fresh-directory>` restores into a new location without overwriting
existing evidence. Bundle verification qualifies delivery integrity only.

The untimed resource-observer profile and its inputs are retained separately.
The subsequent timing controller must count closed ancestor storage while
continuously checking active paths and filesystem capacity, under unchanged
limits. No timing completion or publication is inferred from this preparation.
