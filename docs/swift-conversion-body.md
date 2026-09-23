# Swift conversion body and initializer controls

The initial catalog applicability patch removed local summaries and the original
constant-body false flow. It did not establish ordinary-body preservation. This
follow-up adds a transparent local Data/String body chain, a matching safe chain,
and a constant three-parameter String initializer called with real tainted Data.
The original independent evidence remains unchanged.

The new source is typechecked with pinned Swift 6.3.3 and is never executed.
One extraction is shared by separately locked stock and patched query packs.
The source, queries, runtime manifests, runners, and expectations are committed
before execution. Extraction took 91.163 seconds under the 150-second limit.
Queries retain 60-second / 2048-MiB requests. These are non-scored diagnostics;
aggregate memory containment and complete semantics remain unproven.

## Expanded result

| Sink | Intended flow | Stock assisted | Patched catalog |
| --- | --- | --- | --- |
| Real raw roundtrip | yes | yes | yes |
| Real safe roundtrip | no | no | no |
| Local constant chain | no | yes | no |
| Local transparent body chain | yes | yes | **missing** |
| Local safe body chain | no | no | no |
| Constant wrong-arity String initializer | no | yes | **false flow** |

The stock body's reported flow is not evidence of body propagation: its local
calls receive summaries. In the patched lane all 13 local calls have no manual
summaries. A separate query also confirms no other summary attachment. Eight
real calls retain their summaries. Both remaining failures block qualification
and the canonical summary pair.

## Separate diagnostics

A preregistered all-node sink configuration records intermediate reachable
nodes on the same hash-verified database. It reaches the local encoder result
and the `.value` input of the local String initializer, but not the final local
body-chain sink. This is diagnostic evidence of where propagation is missing,
not proof of a specific internal cause or a production flow configuration.

A separate structural query witnesses a native additional taint edge from the
`data` argument to the constant wrong-arity initializer call. The pinned
`InitializerFromDataStep` admits any `data` argument. This is independent of
catalog summary attachment, which is absent on that call.

The next preregistered experiment filters only the additional heuristic for
resolved Swift.String data initializers, retaining the proved Foundation
initializer identity. Other owners remain stock; ordinary method bodies and
summary steps remain available. The ordinary-body failure remains a separate
blocker even if the false flow is removed. No fixture-specific barrier,
unsupported classification, score activation, or release is authorized by a
successful diagnostic command.

The resolved-initializer experiment completed within its query limit. The
catalog-only lane retained real sink 20 and false sink 42. The additional
resolved filter retained only real sink 20. It removes this false flow but still
misses body sink 35; conversion qualification remains blocked. Portable body
verification reports the original two blockers, and the separate diagnostic
verifier records the narrower correction without rewriting the original result.

## Structural SSA repair

The follow-up resolved-AST/SSA query found the literal assignment on line 11
connected through an SSA definition to the initializer return, while the
property-getter assignment on line 12 did not. The pinned `WriteDefinition.assigns`
compared `value.getNode().asAstNode()` with the assignment RHS, omitting the
property-getter CFG representation. The isolated `6.8.4-dfb.3` adapter library
uses the existing `value.getAst()` mapping instead. This one-line structural
change has no fixture name, location, source, or sink condition.

With that patch, both assignments have the expected SSA and return links.
The catalog-plus-SSA lane reports real sink 20, legitimate body sink 35, and
wrong-arity false sink 42. Adding the resolved initializer filter retains only
20 and 35. All three safe/constant sinks remain absent. This separates the
body repair from the heuristic correction and preserves every earlier failure.
Fresh extraction and canonical summary controls remain necessary before
family qualification; these retained-database results do not activate scores.
