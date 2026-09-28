# Swift top-level CFG repair feasibility

The diagnostic lane merged in #264 established that sampled top-level benchmark
calls are extracted and resolve exactly, but lack CFG and data-flow nodes. This
follow-up inspects the structural information required to build a generic CFG.
It does not change canonical fixtures, registered outcomes, or analyzer support.

## Preregistered observations

Three retained completed databases were cloned for each attempt: direct-positive,
array-element-positive, and callback-registration-positive. No extraction or
fixture execution occurred. Each query/decode pair shared 75 seconds with
requested memory 2048 MiB and a 40 GiB disk reserve.

- `1ca85e9d`: query compilation failed because a generic `Element` has no location;
  the first failure and remaining unattempted cases are retained.
- `24053e29`: corrected the type error; all three selections completed.
- `b6973b08`: retained locationless AST labels and added explicit parent/membership
  counts so absent labels could not masquerade as absent structural edges. All
  three completed. This is the decisive version.

| Retained case | Top-level bodies | Structural parents | Declaration membership |
| --- | ---: | --- | --- |
| direct-positive | 1 | 0 for every body owner | 0 for every body owner |
| array-element-positive | 4 | 0 for every body owner | 0 for every body owner |
| callback-registration-positive | 4 | 0 for every body owner | 0 for every body owner |

Each sampled top-level body contains one structurally indexed element at index
zero. The pinned schema exposes `top_level_code_decls(id, body)` and
`decl_members(parent, index, child)`, but these extracted top-level declarations
have neither parent nor membership relationships. Location labels identify rows
for inspection; they never select execution order.

The array/callback diagnosis is `MissingTopLevelSequence`. This is a bounded
feasibility diagnostic, **not** the registry outcome `unsupported`. A solitary
unparented top-level body does not establish the multi-statement ordering gap by
itself. If structural relationships are present in another database, their
semantics still require review rather than automatic acceptance as ordering.

## Required generic repair

A correct repair needs the extractor to preserve the compiler AST's ordered
sequence of executable top-level declarations under an explicit source-file or
entrypoint owner. It must preserve declaration identity across initialization,
assignment, reference, and closure capture; multi-file initialization and lazy
initializers must remain distinct where their execution semantics differ.

The pinned QL library has a `TopLevelCodeDecl.getBody()` hook, but its CFG scope
universe contains only functions, closures, and key paths. Once trustworthy
ordering exists, a versioned pack could add generic top-level entry/exit and
sequence handling using existing completion and SSA rules. Creating independent
scopes for each statement only to obtain endpoint nodes would not establish
correct flow between statements. Joining by source line or spelling is not an
acceptable substitute for missing structural relationships.

No pack patch is claimed here. Extractor provenance and local build feasibility
need investigation before choosing between a generic extractor repair and an
upstream capability dependency. No upstream issue/message has been sent.

## Evidence and limits

`evidence/swift-top-level-topology-v1/portable-evidence.tar.gz` retains all three
attempts, original query/preregistration versions, native commands, BQRS, decoded
rows and artifact inventories. Full databases remain local. Run:

```bash
python3 scripts/check-swift-topology-evidence.py
python3 scripts/test-swift-topology-evidence.py
```

The verifier binds archive membership/digests, original registrations, query
bytes, command arguments, decoded rows, case selection, recorded closure checks,
and the decisive diagnostic. Recorded comparisons found no drift in cloned
artifacts or retained originals. Neither those observations nor this compact
replay prove containment, aggregate memory compliance, or full database replay.
Scoring, freeze, publication and #220/#215 completion remain unqualified.
