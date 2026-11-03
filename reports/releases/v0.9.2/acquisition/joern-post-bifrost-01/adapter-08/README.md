# Joern adapter-08 source integration

Adapter-08 is a source-only successor to adapter-06/07. It adds the current
130-row archive baseline to the actual inherited runtime graph as seven
source-owned modules. The graph path remains object-based: the existing
opaque-stage bridge receives a graph-owned `load_runtime_context` callback,
checks the resulting `ActualRuntimeContext`, and builds the same immutable
parent/child stage objects. A caller-supplied JSON receipt cannot stand in for
that graph or its callbacks.

## History and source identity

`history.validate()` requires the exact current source-history descriptor and
caller-bound current-source CAS. The descriptor keeps executable HEAD/tree P
separate from source commit/tree S and pins the 130-row live prefix. The
archive-only provider03 path verifies the immutable 130 archive/index chain
without relying on a moving latest index. The live ledger must be precisely
that 130-row byte sequence or that sequence plus physical row131.

The 109-row original cohort and its nine source contexts remain the historical
replay inputs. The 21-row C5/0.14.4 annex is returned as a separate partition;
its Scala entry remains a typed recorder-error/timeout with no completion
claim. Annex rows are not converted into source contexts. They still take part
in exact ledger partition, attempt-directory, and full-ledger wall-provenance
checks.

The current-source CAS requires the exact current S/tree, baseline HEAD,
native08 request ref, unique source-ref closure, and independently reviewed
source-only scope. Its archive-aware proof is loaded from hash-pinned native10
helpers. Post-S source evidence, the CAS document itself, and its review are
validated at their own boundaries and excluded from source refs. The retained
source design and BF0140 qualification remain committed predecessor inputs.

The graph-owned current source proof carries the exact 96 archive-member path
and digest refs only inside the opaque runtime. During current plan parsing,
the adapter records the exact result returned by the frozen
`_resolve_replacement_source_inputs` callback. The normalized inputs must equal
that resolver result exactly; each must also be present in the full CAS source
ref set. This preserves the CAS's additional runtime-code refs without
mistaking them for contract source inputs. The closure is bound to S, P, the
current contract and qualification, the inherited contract, and the graph-owned
executor and stage-runtime refs. Only its digest appears in the compact opaque
runtime diagnostic.

The source snapshot adapter re-reads all 96 indexed members at the frozen
source guard. It keeps the original S-ancestry check, default diff/status
paths, runner Git-blob check, and every direct source-input Git-blob check.
Around the complete frozen `executor.run_group` call, its `_source_file` scope
serves only an exact current-S path/hash match from those same worktree bytes;
direct and unrelated reads retain the original helper. Both callbacks are
identity-checked and restored on every exit path. Thus the archived member
exception applies at both frozen source-check sites and cannot be widened by a
caller-provided path list.

## Runtime behavior

The sealed109 replay reconstructs its contexts through the frozen inherited
graph. Current plan normalization runs separately through the graph-owned
current runner and parser scopes and binds P, S, the current contract, native
decision, and CAS proof. The frozen `_source_delta05` check remains limited to
the historical109 reconstruction; it is not applied to current S.

Replay verifies the 109 historical rows with their original contexts, then
verifies only physical row131 against the normalized current Joern plan. A
current successful row must bind the five report partitions and all 108 case
IDs and must pass the accepted native decision/capture/finalization checks.
The frozen v0.9.2 recorder does not emit `global_attempt_number`; adapter08
derives 132 from the exact archived 21-row annex sequence 111–131 and keeps it
only in the typed tail provenance wrapper. The raw physical row and
`completed.json` remain identical to the frozen recorder output.
The successor group argv uses this directory's `run-joern-common-v092.py`
entrypoint to satisfy the frozen v0.9.2 runner basename check. That wrapper
hash-checks and executes the exact observer08 source bytes, forwarding the
original CLI arguments in order; it is a separately bound source input and is
not one of the seven graph-owned adapter modules.
The 130-row baseline keeps the observed 83-group selection with no selected
Joern attempt; only a validated successful row131 adds that group and yields
the 84-group successor selection. C5 annex rows remain outside both context
sets.
The native evidence is required to retain its 12-arm/36-phase, semantic-only,
known-limits scope. A passing Joern group produces
`joern108-operationally-complete` as a group-level result. It does not open the
full-target, configuration, scoring, or publication gates; the incomplete C5
Scala annex stays visible and `full_release_gate_satisfied` remains false.

The current eligible plan is validated by the exact graph-pinned repair runner
inside an identity-checked scope that temporarily binds its executable-plan
constant to the caller-bound eligible plan. The graph-pinned diagnostic
admission function is wrapped only for the same root, plan bytes, and control
ref; while its original historical-archive check runs, the runner constant is
restored to the immutable `plan-v092-01` path. The scope restores both original
module values on exit and rejects foreign runner/diagnostic objects or scope
escape.

The existing supervisor still owns the one-slot lifecycle, lock, child
containment, deadlines, and no-retry behavior. This source-preparation change
does not dispatch Joern or create admission/eligible-plan authority. Root-owned
current core/CAS production and independent review must bind the final module
hashes before the adapter can be used in qualification or execution.

## Focused checks

The tests use small synthetic JSON and checker fixtures. In addition to the
focused selector and source-snapshot checks, `test_runtime_graph_08.py` builds
the actual pinned outer95 graph, calls its graph-owned runtime loader for
synthetic 130/131 ledgers, and passes both opaque contexts through the frozen
parent/successor constructors. A separate preflight regression invokes the
actual frozen `executor.run_group` and stops at its first tool-file check after
the snapshot guard, population read, and all source-input reads. It substitutes
synthetic subprocess/Git responses and does not reach freshness, resource,
process, or analyzer execution. No native provider is loaded, no retained
126 MB ledger is read, and no Joern or analyzer build is run.

```sh
python3 -B -m unittest -v test_adapter_08 test_runtime_graph_08
```
