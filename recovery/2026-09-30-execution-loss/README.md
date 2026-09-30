# Execution recovery, 30 September 2026

The previous serial supervisor stopped on 29 September at 16:26:04 UTC after seven controls. Its eighth launcher, `probe-java-modeling-load-bearing`, returned 1. No matrix group started. Terminal session events survive, but the original raw outputs, logs, registration checkout and local-only commits do not. Seven transcript completions therefore contribute **zero currently qualified controls**. All 33 controls and 84 matrix groups still require preserved, verifiable evidence.

The missing original contract was identified as SHA-256 `29c1a14d422506cd585a9ab2bc7fe7035b87ed5ca3426a46c51399b2c129db39`, registered in local commits `18322a95c` and `761c693ca`. These names are historical references, not recovered objects. Current main `74c0df38e` changes only README and docs relative to merged harness `94ff0ad5ac1c8e54b9bda73903d461702a89cd9b`.

The command-level replay exits before scratch creation or analyzers: the Java probe requires `--codeql-packs`, absent from its registered argv. The JavaScript probe has the same omission. These deterministic reproductions support an argument defect; the original failure stderr remains unavailable. No native analysis was repeated.

The new candidate is `reports/releases/v0.9.0/execution-v1/recovery-20260930-01/contract.json`. It is intentionally disabled and is not a reconstruction of the missing original bytes. It fixes the two prospective argument arrays, designates durable execution storage inside this workspace, preserves immutable parent-plan bindings, and requires new runtime/source reservations. Historical runner receipts and Swift plans remain evidence of their original installations, not proof that those paths still exist.

Before launch:

1. Restore and verify exact missing CodeQL 2.27.1, Swift 6.3.3, repaired extractor/packs, OpenTaint full bundle, and runner in durable storage. Six other runtime-tree inventories currently verify.
2. Explicitly register relocated runtime plans and new build provenance. Recalculate acquisition/extraction scratch while preserving the 136 GiB launch floor and 40 GiB reserve.
3. Review attempt accounting across the lost run. A new directory does not reset the two-attempt limit; no outcome-selecting retry is allowed.
4. Validate the corrected eighth control under a retained diagnostic attempt before starting a full serial recovery. Wait for the active Bifrost build/coverage slot to clear.
5. Validate all 117 operations in designated roots; commit and push the final sealed packet before heavy execution. Persist supervisor stdout, stderr, started and terminal status in durable storage, stopping on failure with no automatic retry.

`reconstruction-source-events.json` is a local recovery aid extracted from this session, not a release artifact. It is intentionally not part of the committed evidence package. No private session narrative is required to reproduce the argument failures.

The `supervise-release-command-v090.py` wrapper requires an explicit deadline and fresh durable log directory, preserves stdout/stderr and start/terminal receipts, and propagates nonzero status. It never retries. It cannot persist a terminal event after SIGKILL, sudden power loss, or filesystem failure; a started-only receipt is an interrupted/unknown attempt requiring review. Descendants that create their own process sessions remain the inner launcher's containment responsibility. All 117 exact parser/mode checks remain a launch blocker: the two defective shell parsers are covered now, but missing runtimes prevent full command qualification.
