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

## Observed result (2026-09-28)

The probe ran from preregistration commit
`d4dc62fb` and completed all five selections. The exact commit is retained in
`evidence/swift-endpoint-diagnostic-v1/launch.json`.

| Selection | Source | Sink |
| --- | --- | --- |
| Retained direct-positive | Bound | Bound |
| Retained array-element-positive | MissingControlFlow | MissingControlFlow |
| Retained callback-registration-positive | MissingControlFlow | Bound |
| Adapter wrapped control | Bound | Bound |
| Adapter wrong-signature control | NonMatchingDeclaration | NonMatchingDeclaration |

For each sampled `MissingControlFlow` endpoint, the AST call exists, resolves
to exactly one matching benchmark declaration, and has its endpoint expression;
CFG and data-flow node counts are both zero. The callback sink inside its closure
has both node types. The wrong-signature functions have the benchmark names but
use `String`, and are rejected despite having CFG/data-flow nodes. Thus matching
spelling is not sufficient for endpoint identity.

This establishes a structural CFG boundary in the sampled failing endpoints;
it does not prove the diagnosis for every one of the 54 failures. A production
repair would require genuine top-level CFG/data-flow support in the pinned
analyzer or a separately reviewed prospective fixture amendment. This change
does neither and does not manufacture taint reachability for missing nodes.

All final artifact comparisons and all three retained-original comparisons
reported no observed drift. This is a bounded observation, not containment proof.
The old timeout drift and symlink rejection remain in their original archives.
The new typed-link behavior is covered by positive and adversarial filesystem
regressions; the five successful native cases did not require a timeout recovery.

Run `python3 scripts/check-swift-endpoint-evidence.py` to replay the compact
query/classification evidence. It verifies copied file digests, exact selection,
command records, source input registration, classification, and recorded closure
deltas. Full database/cache/binary payloads remain local; the checker is explicitly
not a full database replay, memory qualification, or process-containment proof.

The inventory's path-based checks are not atomic against concurrent directory
replacement. A hostile concurrent writer could swap an intermediate directory
between checks; descriptor-relative traversal would be required for a strict
no-follow security boundary. This helper is a diagnostic drift detector and
must not be used as sandboxing or cleanup authorization.
