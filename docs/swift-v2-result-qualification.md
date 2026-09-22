# Swift v2 Result feasibility and vendor follow-up

This tranche continues #220 after the merged fixture and preflight tranches.
Canonical inputs, both Swift populations, historical reports, and all prior
attempts remain immutable. No scored partition or activation is inferred from
partial feasibility diagnostics.

## Foundation timeout inspection

The retained second native extraction attempt completed its compiler trace
near the end of the 60-second extraction-phase deadline and began database
finalization/TRAP import. Its logs explicitly round requested RAM 512 up to a
minimum 2048 for import (`-J-Xmx1188M`). Exact referenced log digests and selected
lines are retained in `foundation-diagnosis/retained-log-observations.json`.

The cutoff therefore does not establish absent Foundation declarations or a
missing native model. It also does not isolate a performance bottleneck or
prove complete extraction. No extra native fixture execution or repeated
native extraction is needed to make that distinction.

## Independent Result path

The new probe pack copies the exact resolved controlled endpoint predicates
from v1 without changing v1 bytes. It restricts benchmark integer endpoints by
resolved module, declaration, arity, parameter and return types; the Result
flow probe uses ordinary CodeQL taint propagation, not a new Result summary.
This is a language-extension qualification candidate, not a core/native model.

A non-scored feasibility invocation may use an explicitly recorded 180-second
extraction-phase cap. That cap is not the normative scored analysis budget:
query commands retain `--ram=512`, `--timeout=60`, and a 60-second phase wall
clock bound. Any tool-raised RAM minimum, memory uncertainty, timeout, extraction
incompleteness, or endpoint mismatch remains unqualified. The flags and full
commands are retained per attempt; no normalized scored report is emitted.

Successful extraction must pass the finalized Swift database gate before
queries run. Timeout/abnormal exit or uncertain tracked-process cleanup stops
the attempt. Scratch remains retained and process discovery is explicitly
incomplete; there is no automatic cleanup/retry based on polling.

Joern's exact versioned vendor bundle is inventoried independently. An empty
installed query database cannot prove vendor model absence. Only the inspected
vendor catalog and exact declaration/control evidence can support a later
prospective native partition; benchmark-authored native semantics are forbidden.

## Retained observations

Both CodeQL Result cells finalize and resolve exact source/sink endpoints and
the `Swift.Result.failure` declaration. The flow query emits zero rows for both
cells. A separate direct-flow control emits one flow; wrong source arity, sink
type, and declaration-kind decoys do not enter that direct flow. A diagnostic
checkpoint query on the retained positive database reaches only the source
input at failure construction, not the selected relay or outer payload
checkpoints. This localizes an observation; it does not prove a root cause,
unsupported capability, or semantic completeness.

Joern independently builds each Result CPG with the compiler type-map route,
resolves the exact benchmark methods/call edges, and reports `not-reached` for
both Result cells. Its separate direct/identity control reports `reached`.
No custom Result semantics are loaded. These raw native observations do not
become scored clean negatives: the graph explicitly reports completeness
unproved, and aggregate process-tree memory compliance remains unknown.

CodeQL query RSS exceeds 512 MiB despite the requested flag and its logs raise
the RAM minimum. Joern query RSS is about 390–393 MiB with `-Xmx512m`, but that
single-process measurement is not an aggregate memory certification. All six
pair/control attempts remain `unqualified`; no registry result rows are added.
The non-population identity controls have no population/revision membership.
Some diagnostic work overlapped; no timing or performance comparison is made.

The independent [Joern vendor bundle inventory](joern-swift-v2-vendor.md) finds
58 vendor query records and no Swift record at the exact pinned asset. This
bounds the shipped query surface; it does not assert all possible model
mechanisms are absent. A reviewed prospective partition remains future work.
