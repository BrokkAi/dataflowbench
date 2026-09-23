# Swift integer sanitizer qualification: blocked independent control

The canonical sanitizer negative parses environment input with `Int(raw,
radix: 10)` and renders the result with `String(parsed, radix: 10)`; its positive
passes the raw string to the command. Before either canonical case runs, an
independent control compares direct raw flow, an explicit `Swift.Int` / decimal
`Swift.String` roundtrip, and a local string-preserving `Int` that conforms to a
module-local `Numeric` protocol. A local String initializer unwraps the latter's
stored raw string. The lookalike preserves arbitrary input and must remain a
flowing positive; its numeric-looking names cannot qualify it as a sanitizer.
A same-body `Plain` wrapper without Numeric conformance supplies an additional
positive control for constructor, stored-field and unwrapping propagation.

The source and sink profile and normal vendor flow configuration remain
unchanged. Additional queries only observe resolved initializer identities,
expression type provenance, and native `CommandInjectionBarrier` membership.
They do not add or suppress a barrier or transfer. The pinned shipped default
barrier matches numeric base-type names; the control tests whether this admits
the unrelated local protocol. Identity, barrier engagement, and endpoint flow
are separate observations.

A committed plan binds source, queries, runtime closure, compiler, SDK, selected
vendor source, and runner files before execution. CodeQL 2.27.1 / swift-all
6.8.4 with Swift 6.3.3 and SDK 26.5 uses 150 seconds for extraction and 60 seconds
/ 2048 MiB per diagnostic query. Aggregate memory compliance and semantic
completeness remain unproven. Fixture binaries are never executed.

The expected assisted flows are source-to-direct-sink, source-to-local-sink and
source-to-plain-sink,
with no source-to-real-integer-sink flow. The vendor-native lane is retained
separately. Missing identity or barrier evidence is not a clean result. A failed
separating control blocks the canonical sanitizer pair and is retained without
changing expectations. Append remains independently blocked; this work does
not activate scores, run the full corpus, freeze, or publish results.


## Retained result

The independent control is **blocked**. The canonical sanitizer pair has not
run. A successful portable evidence check verifies this blocked observation;
it does not qualify the family or activate benchmark scores.

| Control | Native value barrier | Assisted endpoint flow |
| --- | --- | --- |
| Raw string | no | source 17 → sink 19 |
| Swift integer decimal roundtrip | yes, Swift.Int read at 21:33 | none |
| String-preserving local Int:Numeric | **yes, local Int read at 25:33** | missing at sink 27 |
| Same-body Plain wrapper | no, Plain read at 29:34 | missing at sink 31 |

The preregistration expected flows to sinks 19, 27 and 31. Only sink 19 was
observed. Both lanes retain eight sink nodes; the adapter-assisted lane has one
environment source, while the vendor-native lane has no source or flow.

The native base-declaration query ties the local Int at 25:33 to the module-local
Numeric protocol. The shipped `CommandInjectionDefaultBarrier` checks base-type
names without their module. It therefore admits this unrelated string-holding
type as a barrier. The same membership is observed in the local initializer and
unwrapping initializer bodies. The Plain control has no such barrier, yet it
also lacks endpoint flow. Consequently the evidence establishes a spurious
barrier and a failed constructor/field/unwrapping flow control, but **does not
establish that the barrier alone causes the missing endpoint flows**. No
suppression, custom transfer, or changed expectation is supplied.

Resolved initializer identity is retained separately. The real parse target is
`Swift.FixedWidthInteger.init(_:radix:)`; it must remain protocol-owned rather
than being relabeled as a declaration on Int. The real render target is
`Swift.String.init(_:radix:uppercase:)` with its default argument. The local
constructors and String extensions resolve to the fixture module. Printed
formal/result type text is context only; typed barrier rows carry the resolved
module and nominal declaration evidence.

The first attempt extracted successfully in 95.389 seconds and retained source,
role and flow observations. Its conversion-identity query failed compilation
because the optional-type projection produced an empty relation. The failure
and original query remain immutable. A separately committed diagnosis removes
that projection, preserving resolved initializer module/owner and reporting
result type text without claiming it is exact identity. Its three queries
completed in 11.443, 10.925 and 10.293 seconds against the same retained database.
All 424 non-cache source-data hashes and the source archive were checked before
reuse; only the mutable query-cache subtree was excluded. No new extraction or
canonical execution occurred.

The raw attempts, preregistrations, selected vendor source and archive are under
`evidence/swift-sanitizer-qualification-v1`. Run
`python3 scripts/verify-swift-sanitizer-control.py` and
`python3 scripts/test-swift-sanitizer-control.py` to verify the portable package.
Aggregate memory compliance and semantic completeness remain unproven.
