# Swift endpoint and artifact closure diagnostics

This prospective diagnostic lane follows the failed attempts recorded in
[the full108 attempt](swift-v3-full108-attempt.md). It does not change canonical
fixtures, historical queries, manifests, outcomes, or scoring eligibility.

## Question and controls

The retained attempt has 54 `MissingExactEndpoints` results: 52 lack both
endpoint roles and two callback fixtures lack only their top-level source.
The pinned Swift library defines control-flow scopes for functions, closures,
and key paths, while expression data-flow nodes require control-flow nodes.
That suggests a top-level coverage boundary; role output alone cannot establish
whether AST calls were extracted or resolved.

The new diagnostic query inventories AST calls before applying the exact
benchmark declaration identity. It distinguishes absent AST calls, unresolved
or nonmatching targets, missing control-flow nodes, missing data-flow nodes,
and fully bound endpoints. Location anchors identify the requested expression;
source spelling never proves target identity. Neither missing endpoints nor
bound endpoints establish whether taint reaches a sink.

A preregistered serial probe first queries APFS clones of three retained
completed databases: direct-positive, array-element-positive, and
callback-registration-positive. It then extracts adapter-local controls for
scope and declaration near misses. Canonical fixture bytes are compared with
retained source archives. Original databases are inventoried before cloning
and after the probe. No fixture binary is executed.

## Prospective closure handling

A versioned artifact inventory records directories, regular files, and symbolic
links without following links during enumeration. Link targets are retained
literally and validated within the artifact root; unsafe or incomplete links
fail closed. Changes between inventories retain added, removed, and changed
paths rather than rewriting the original inventory.

The runner records initial and later inventories outside the inventoried tree.
A timeout or uncertain cleanup stops subsequent probes, because polling does
not establish complete descendant discovery. Any observed artifact drift is
`IncompleteArtifactClosure`. Stable inventories are not process-containment
proof. Requested memory remains 2048 MiB; aggregate memory compliance remains
unproven. Historical symlink failures and late writes remain unchanged.

## Execution and evidence

The adapter's `registration.json` binds the query, controls, runner, helpers,
exact retained observations, and runtime pin sources before execution. Extraction
is capped at 150 seconds; each query and its decode share 75 seconds. The disk
reserve is 40 GiB. All attempts, including errors and unattempted selections,
are retained. A native probe is diagnostic evidence only and cannot activate
scoring, freeze, publish, or close #220/#215.
