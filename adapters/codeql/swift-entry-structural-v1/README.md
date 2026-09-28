# Two multifile structural controls

Both preregistered controls passed the registered structural assertions using
exact candidate extractor/schema/pack identities from the original experiment.
This is bounded structural evidence, not scored activation or full Swift support.
The original array-negative and callback-positive failures remain unchanged.

| Control | Extraction | Shared query/decode phase sum | Structural result |
|---|---:|---:|---|
| branch | 43.18 s | 29.95 s | One entry, six unique dense declarations, exact file/module ownership, conditional CFG, separate nested scopes |
| throw | 46.35 s | 13.05 s | One entry, three unique dense declarations, normal and exceptional exits, no throw-to-later-sink CFG path |

Both have two closure scopes and eight nested return statements, with no return
leaking into script scope and no library-owned entry. Compiler AST dumps confirm
six/three script declarations in the exported index order; equality and duplicate
checks use database entities in QL. The decoded entity IDs are database-local,
not stable cross-database identifiers. Display locations label independent
compiler observations; neither the patch nor the query orders by location.

The default JSON decode omitted entity IDs. A separately registered 15-second
bounded decode of retained BQRS with `--entities=all` supplies them without new
query/extraction. This supplementary decoding is not retroactively counted in
the original 75-second analysis window. Both initial query syntax failures are
retained before the successful preparation; all fixture compiler checks passed.

Flow rows, separately diagnostic, show source reaching the first branch sink
but not the sink after unconditional overwrite, and reaching the throw fixture's
sink through its non-throwing branch. They are not an invented perfect-accuracy
gate. Native endpoints have CFG/data-flow rows retained in diagnostics.json.

Each run used the preregistered 150-second extraction and 75-second shared query/
decode wall deadline, two threads, 2,048 MiB requested and 40 GiB free-space guard.
The shared deadline was enforced using one monotonic start per database; the
numbers above sum command elapsed times and do not claim to measure inter-command
overhead. CodeQL raised requested RAM to its 2,638 MiB minimum. Aggregate memory
and descendant containment remain unproven; tracked cleanup completed.

Queries changed caches and added logs. The initial/final database delta remains
`IncompleteArtifactClosure`; all removals/changes are under cache and additions
are cache/log paths. A separate post-query pair of snapshots is equal and reports
`CompleteArtifactClosure`. It does not retroactively erase the query-time delta
or certify process containment. Native BQRS and decoded rows are retained in the
portable archive; full databases remain local.

Auxiliary/macro declarations, async and an explicitly triggered lazy extraction
path remain unqualified. These controls verify a library-file negative, not all
possible global initialization semantics. No compiled binary or UserDefaults
native fixture was executed.

Replay: `python3 scripts/check-swift-entry-structural-evidence.py`.
