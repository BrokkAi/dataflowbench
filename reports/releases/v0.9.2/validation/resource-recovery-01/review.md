# Authorized resource-only successor

The human authorized C4 with a 110 GiB launch floor. The original 40 GiB protected reserve, 24 GiB scratch and retention ceilings, one analyzer slot, series 1, maximum two attempts per group, origin 2026-10-20T00:57:00.680937+00:00, and deadline 2026-10-21T05:33:00.680937+00:00 remain unchanged.

The sealed 57-row predecessor prefix contains 25 C2 completions, 30 C3 completions, and the original two failures. Its SHA-256 is 31ea08cf5f0fa04fe07697bb8d3683e2a313140e6e12e15fe7e7963a82cdc1f2. Retained measurements continue to use their original source, contract, and plan identities. Only the remaining 29 groups may run under C4.

C4 keeps the exact C3 analyzer/runtime bindings, command vectors, environments, report partitions, qualifications, fixtures, and Rust harness. The separate harness-v3 binary remains dfbc0e4865366a47386c9e541d2342f56f43548ae12b55d1c802fac07174134c. The source validator rejects changes to Rust, adapters, cases, populations, schemas, corpus, Cargo inputs, or scripts outside the explicit resource implementation and tests.

The new disk checks project source extraction, the entire capture batch, and original/normalized report staging before writing. Copies use bounded chunks and capacity rechecks. Admission projects all remaining source snapshots against a 12 GiB working ceiling. Active checks stop at 48 GiB, providing 8 GiB of margin above the protected reserve. Partial writes and typed capacity failures remain evidence; they do not become completed reports or trigger automatic retries.

The 48 GiB stop is a polling guard, not a filesystem reservation against unrelated writers. The uncontended admission gate remains necessary. Benign temporary-file disappearance, compiler symlinks, and Pysa sockets are accounted without following links or treating them as regular-file allocation. Captured evidence remains strict regular-file data.

Before C4 preparation, the measured source-only footprint was 7,836,802,610 bytes. The old source projection for 29 remaining snapshots was 4,108,351,497 bytes; C4 adds the sealed 16,086,045-byte history prefix and small resource records to each future source snapshot. The exact committed C4 source is remeasured at admission.

Finished-candidate cleanup verified 6,020 capture hashes plus original/staged reports and empty process/handle audits, then removed only 17 nonempty completed candidate caches (1.29048 GiB logical). Failed-attempt caches, original capture roots, source snapshots, acquired runtimes, receipts, and reports remain intact. See ../finished-cache-cleanup-20261020-01/receipt.json.

No C4 analyzer measurement has started while these changes are being prepared. The original C3 supervisor13 remains unlaunched and must not be used for C4.

Final Python validation passed all 155 tests across executor, checker, generator, guard, recovery-packet, failure-replay, and staging suites. Process-ownership tests ran with live process-table access; the final elevated run had no platform skips. Logs and source hashes are sealed in test-run-01/receipt.json. Rust and analyzer runtime inputs were not changed or rebuilt.

The first prospective-plan replay exposed an existing checker representation bug: FlowDroid build identity received the raw group instead of its validated group, omitting the derived D8 component list. Preflight stopped before any C4 attempt. The refused prospective contract and diagnosis remain in plan-preflight-01/. The checker now uses the validated group; a regression replays the actual retained Java kernel receipt and rejects a missing-D8 near miss. The final test-run-02 rerun passed all 156 tests.

A final pre-invocation review normalized C4 no-child failures to the executor sentinel (125, no timeout, zero analyzer duration, empty stream receipts). This prevents guard-check overhead from being presented as analyzer duration, and makes generic source-setup errors independently replayable. Both phase-edge regressions passed; test-run-03 passed all 158 tests. No C4 measurement had started under the earlier unexecuted plan; its exact approved contract, launcher, review and Git plan commit are preserved under plan-preflight-03/ and in commit history. The first actual C4 measurement will use the subsequently frozen single plan.
