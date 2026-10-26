# Joern v0.9.2 monitor06 policy prototype

Status: private source prototype for review. It is not a qualification, benchmark, or production invocation. The existing `joern-native-controls-05` source in the worktree was not edited.

## Authorization and scope

The implementation follows the human decision at `reports/releases/v0.9.2/qualification/joern-post-bifrost-01/process-snapshot-policy-human-decision-01.json` (SHA-256 `b7130ef72545edaa9599640946921180bd95e00ec5106b5072d9a3981310b2fb`) and corrected independent review `process-snapshot-policy-proposal-independent-review-02.json`.

The exception is active only inside the copied `supervise()` loop. `contenders()` and outer/root admission remain strict. The root-owned source, contract, request, review, authority, and fresh-admission chain is still required before any invocation. The scored Joern adapter also remains outside this prototype.

## Policy behavior

- A rejected command row is eligible only when its original native birth identity is missing or unknown. A known-live foreign row never enters reconciliation.
- The supervisor makes at most one attempt per unresolved PID for that supervisor/admission boundary. Its absolute deadline is `min(current phase/admission deadline, start + 5 seconds)`.
- A single clean Python query child attempts native-before, command, native-after, in that order. It streams completed snapshots and nested-child lifecycle records to the parent so a timeout can retain already-observed evidence. Native tables use OS-native PID enumeration (`libproc` on Darwin, `/proc` on Linux); native executable/path fields remain capped at 4,096 bytes. The middle command table uses the exact `ps -axo pid=,%cpu=,comm=,args=` fields consumed by the existing classifiers. Its output is read incrementally with an 8 MiB aggregate cap, 64 KiB row/argv caps, an 8,192-PID cap, finite deadline, and 50 ms direct-child reap reserve. The parent allows provider work until 150 ms before the five-second cap, 50 ms for query finalization, then reserves 100 ms to kill/reap only the direct Python query child. Parent stdout capture retains at most 16 MiB; stderr capture retains at most 16 KiB. Exceeding a cap produces a typed incomplete result with bounded prefix/hash metadata and is never passed to the general snapshot decoder. Timeout/error paths also decode no more than those retained prefixes. Neither helper signals foreign PIDs or claims descendant/OS-global containment.
- The actual command table, including CPU, comm, argv, and raw rows, feeds the frozen classifiers unchanged. The low-CPU Bifrost `--mcp`/`--lsp` exception and hashed-Bifrost rule are covered by fixtures. A native-only row has no measured CPU or argv; it is treated as ambiguous through the existing conservative classification path rather than given invented command-provider values.
- Provider errors, missing fields, PID reuse, candidate presence in any fresh table, incomplete coverage, truncation, bad order/timestamps, or timeout fail closed. Any other fresh heavy or ambiguous contender also stops.
- The only accepted historical state is `unresolved_historical_absent_at_reconciliation`. It conveys no ownership, harmlessness, exact exit time, cleanup authority, retry, or qualification.
- After a successful durable receipt, the PID is kept in a run-wide reappearance set. Every later current raw command and native PID snapshot checks that set before descendant discovery or owned-row filtering. A later reappearance fails closed even if the PID now looks like an exact owned descendant.
- The supervisor checks the current phase/admission deadline after the query, after evaluation, after durable receipt writing, and after later monitor/child-completion work. A late query/evaluation/receipt writes a typed stop; no historical PID is added to the reappearance set unless the receipt is durable and every check is within the unchanged absolute pass deadline. The terminal parent result reports continuation authorization only when monitoring completed without failure.
- A reconciliation attempt is attached to the current stop snapshot before either receipt write. If the dedicated receipt fails but the fallback stop receipt succeeds, it contains the attempted fresh query, typed evaluation, deadline checks, and write failure. Query/evaluator exceptions are retained as typed incomplete evidence; if all evidence writes fail, the primary failure remains but evidence durability is not claimed.
- Receipt persistence still uses the inherited synchronous atomic/fsynced `immutable()` writer. The supervisor rechecks the deadline immediately after it returns and rejects a late receipt, but cannot interrupt a filesystem/fsync stall; the five-second bound on end-to-end wall time remains unproven until that writer boundary receives separate bounded design/review.
- Existing exact-birth descendant discovery and cleanup logic are unchanged. Fresh native identities feed that logic only after all required fields pass validation.
- The old command/native snapshot remains recorded as legacy, non-provider-complete evidence. Receipts preserve it alongside the fresh observations and typed result.

## Follow-up diagnosis

The prior read-only provider probe is `/private/tmp/dfb-v092-transplant-20261026T160424Z/monitor06-provider-probe-01.json` (SHA-256 `42bbc9a7f50a0601eba2c00d9e9c961ab723f26ca4bbccc65c05870e1bf1aa59`); this policy02 task did not rerun it. It reported incomplete native-before/native-after snapshots at `proc_pidinfo` for PID 10491 and an incomplete `ps` table under the prototype's 4,096-byte row limit. Root's diagnosis identifies a valid editor command row for PID 4588 with 9,239-byte args. The old probe did not retain the libproc returned count, expected buffer size, or `ctypes` errno, so the PID 10491 event cannot be distinguished from exit, access denial, or another native failure. Policy02 records those values after clearing errno before each libproc call, but still fails closed and never turns that failure into absence.

The 64 KiB limit applies only to `ps` rows/argv; native command/path bounds remain 4,096 bytes and the aggregate `ps` table remains 8 MiB. This corrects the demonstrated editor-row cap mismatch while preserving strict failure for larger rows, larger aggregate output, malformed/missing fields, and every native API error. Even if the command table now parses, the probe's native PID failure means all-native-pass completeness is still blocked; the sole historical-absence outcome is unavailable for that observation.

## Files

- `native_qualifier.py`: private copy with original-snapshot timestamps, reconciliation receipt handling, bounded supervisor integration, and the persistent raw-PID reappearance guard.
- `process_reconciliation.py`: isolated-child deadline runner, streamed-result decoder, strict completeness validator, candidate evaluator, and conservative fresh-contender checks.
- `snapshot_query.py`: stdlib-only query child with Darwin libproc and Linux `/proc` native providers plus the bounded `ps` command provider.
- `retained_resources.py`, `test_contention_repair.py`, `test_native_qualifier.py`, `test_pending_plan_gate.py`: byte-identical copies from native-controls-05.
- `test_reconciliation_policy.py`: fake-provider, fake-Popen and supervisor policy regressions covering actual command fields, MCP CPU thresholds, hashed Bifrost, realistic 9,239-byte editor args, 64 KiB row/argv and 8 MiB table caps, detailed native short-read errno evidence, provider truncation/stalls, bounded parent stdout/stderr capture, child lifecycle evidence, receipt-write fallback evidence, slow-evaluator/receipt deadline overruns, and later PID reuse/reappearance.
- `diff-vs-native-controls-05.patch`: source and test additions relative to the copied native-controls-05 baseline.
- `handoff.json`: machine-readable scope, evidence, validation, and remaining integration work.

## Validation

Using `/opt/homebrew/bin/python3.13` (3.13.7), with fake providers and fake Popen for the new policy path:

- `test_reconciliation_policy.py`: 30 passed.
- `test_contention_repair.py`: 8 passed.
- Combined focused policy and contention suite: 38 passed.
- AST parsing: 8 copied/prototype Python files passed.
- No engine, JVM, control invocation, or additional live OS process-table query was run for policy02. The prior diagnostic probe is incomplete, so Darwin provider behavior remains unqualified and actual provider latency is unmeasured.

An exploratory run of the broader copied `test_native_qualifier.py` under the Xcode system Python failed because that interpreter lacks `sys.orig_argv`, the private copy did not include auxiliary worker fixtures, and one real tiny-child timing test returned `late or reversed child phase`. It did not launch an engine or Java. This suite was not used as qualification evidence.

## Limits and next integration steps

The query child and parent pipe capture have configured limits of five seconds total, a 4.85-second provider deadline, 50 ms for query finalization, 100 ms reserved for direct query-child cleanup, 8,192 PIDs, 4,096 bytes for native path/command fields, 64 KiB per `ps` row/argv, 8 MiB for the aggregate `ps` table, 16 MiB retained parent stdout, and 16 KiB retained parent stderr. Parent capture is incremental and stops the query child on over-cap output; the retained hashes identify only bytes observed before that stop, not a complete child stream. The synchronous receipt writer is not interruptible and can exceed the pass deadline while inside filesystem operations; late return fails closed, but bounded end-to-end latency is not established. Exceeding an observation/capture bound marks it incomplete. These are configured caps, not measured throughput. Darwin native observations use executable path or process name, not argv; actual argv and CPU are preserved separately from the bounded `ps` command table. Native-only heavy rows remain ambiguous and may stop the monitor. The prior diagnostic provider probe failed closed on PID 10491; policy02 did not repeat it. Provider success means complete only within that provider's local enumeration and does not prove OS-global absence or continuous absence.

The original native-controls-05 command/native snapshot still uses its frozen `ps` providers before this reconciliation starts. They are preserved as legacy evidence with their incompleteness recorded. Boundedness of those inherited pre-reconciliation observations remains an integration boundary for root review. Root admission contenders stay strict, and the scored Joern adapter is not integrated by this private prototype.

Before any invocation, root must integrate the helper into the approved source/contract/request/review/admission chain, perform independent source review, decide whether a new read-only OS-provider probe is appropriate after reviewing the existing failure, and resolve the synchronous receipt-writer latency boundary if a strict end-to-end five-second wall bound is required. The global publication hold, prior failures, analyzer/resource budgets, and all completed Bifrost/CodeQL runs remain unchanged.
