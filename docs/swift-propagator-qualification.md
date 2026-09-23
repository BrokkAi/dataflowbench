# Swift propagator qualification: blocked independent control

The next native family is `dfb-template-native-propagator`: the canonical
positive and negative both call `Swift.String.append(_ other: String)` on a
mutable command. Data conversion belongs to the separate summary family.

Before the canonical pair, an independent function-wrapped control checks a
real append of environment input, the same operation with a safe literal, a
module-local `String` owner, and a local wrong-arity String extension. It never
executes fixture binaries. Source/sink predicates remain byte-identical to the
retained Foundation source profile; no transfer rule is supplied locally.

The new query pack checks the resolved method's module, nominal owner, selector,
String parameter, instance dispatch, and `self.isInout()`. A separate observation
joins the exact static target to its attached manual argument-to-receiver taint
summary and to the instantiated `summaryThroughStepTaint` relation. This internal
relation is used only to observe shipped summary engagement; it is never added
to the production taint configuration. Endpoint flow is measured separately.

The pinned `Collection.qll` catalog contains a `RangeReplaceableCollection`
`append(_:)` argument-to-receiver taint row. Its matcher uses subtypes, an empty
signature and no namespace restriction. The vendor `ExternalFlow` implementation
sets the exposed model-origin string to empty. Therefore attached-summary and
call-site edge evidence must not be advertised as exact originating-CSV-row
provenance. The retained source snapshot records this limitation explicitly.

The control source, query files, selected shipped implementation files, runtime
assets, runner closure and policy are bound in
`evidence/swift-propagator-qualification-v1/control-plan.json` before execution.
Use CodeQL 2.27.1 / swift-all 6.8.4, Swift 6.3.3 and SDK 26.5, with extraction
150 seconds and each query 60 seconds/2048 MiB. Aggregate memory and semantic
completeness remain unproven, and all observations remain non-scored.

Only after the independent control passes may the unchanged canonical pair run
under its own committed runner/selection. Failures and near-miss observations
remain retained; missing identity or summary edges are not clean negatives or
unsupported decisions. Previous source–sink and entrypoint configurations,
runners, raw packages and reports remain unchanged. No scored activation,
full-corpus execution, freeze, or publication is part of this diagnostic scope.


## Retained result

The independent control **failed** its preregistered separating expectation.
The canonical propagator pair has not run. Evidence verification succeeds only
when it preserves this blocked result; CI success does not qualify the family.

| Control | Exact append identity / attached summary | Assisted endpoint flow |
| --- | --- | --- |
| Real append of environment input, line 13 | yes / yes | source 11 → sink 14 |
| Real append of safe literal, line 16 | yes / yes | none |
| Local String owner, line 19 | no / no | none |
| Local wrong-arity extension, line 22 | no / no | **source 11 → sink 23 (false flow)** |

Both real calls have instantiated shipped argument-to-receiver summary edges.
The vendor-native lane has no source or flow; each lane has eight sink nodes
across the four sink calls. Extraction completed in 98.533 seconds. These are
non-scored observations under the diagnostic limits above.

The wrong-arity extension assigns the constant `"echo clean"`, independently of
its input. A retained native path reports `.environment` at 11:15 → `wrong` at
23:94 with `AdditionalTaintStep` provenance, then → the argument array at 23:87.
Its attached-summary query is empty. This false flow must not be attributed to
the catalog summary merely because the real append calls have that summary.

The shipped `Heuristic.qll` `AppendCallStep` accepts `append`/`insert` by short
name and a blank/`contentsOf` argument label. It does not constrain owner,
module, signature, or body. A separate native witness observes its matching
argument-to-post-update-receiver relation on all four calls, including both
lookalikes. Identifying this implementation combines native relation evidence
with the hash-verified shipped source; the engine does not expose the private
class name in the path. The local-owner step alone did not produce an observed
flow through its `.value` field.

All attempts remain in `evidence/swift-propagator-qualification-v1`: the initial
path query's `edges/2` compilation error, a query-cache fingerprint rejection
before analyzer execution, the corrected `edges/4` path, and the heuristic
witness. The successful reused-database diagnoses preserve all 414 original
non-cache source-data file hashes and the source archive. Only the mutable
query-cache subtree is excluded by the successor preregistrations.

Run `python3 scripts/verify-swift-propagator-control.py` and
`python3 scripts/test-swift-propagator-control.py` for portable evidence checks.
Mutation tests prevent erasing the false flow, promoting the diagnosis, or
inventing path provenance. A genuine precision fix or separately authorized
revised qualification is required before the canonical propagator gate can
advance. No local suppression or transfer-model replacement is introduced.
