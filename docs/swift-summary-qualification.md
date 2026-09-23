# Swift Data roundtrip qualification: blocked independent control

Before the canonical summary pair, one independent control tests a raw-input
Data/Base64/String roundtrip, the same real operations on a safe literal, and
a module-local constant-body Data lookalike plus a local String initializer.
The expected assisted endpoint flow reaches only the real raw-input sink.
The local chain always produces a safe constant and must remain a separating
near-miss. Fixture binaries are never executed.

Source, sink and shipped flow configuration remain unchanged. Observational
queries record each resolved method's defining module, nominal owner/module,
selector and arity. Imported spelling is not declaration provenance: the SDK
may resolve Foundation.Data to a FoundationEssentials declaration. Local
extensions on Swift.String keep their local defining module separately.

Attached manual summary ports and instantiated `summaryThroughStepTaint`
call-site edges are separate observations. The simple-edge predicate explicitly excludes reads and stores; matching
`output.asExpr() = call` does not witness a ReturnValue.OptionalSome store.
The later store probe uses `summarySetterStep` and the shipped Swift
`encodeContent` relation to retain that structural content identity. The public ports retain
OptionalSome where supplied. Empty model-origin strings remain empty and do
not prove an exact originating catalog row. No observation relation is added
to the production flow configuration.

The preregistration binds source, query pack, selected vendor implementation,
runner closure, compiler and SDK before native execution. Pinned CodeQL 2.27.1
/ swift-all 6.8.4 and Swift 6.3.3 / SDK 26.5 use 150 seconds for extraction and
60 seconds / 2048 MiB per diagnostic query. Aggregate memory compliance and
semantic completeness remain unproven. Vendor-native and adapter-assisted
observations remain separate and non-scored.

A failed separating control, absent resolved identities or missing required
summary engagement blocks the canonical summary pair. All attempts remain
retained. Existing append and sanitizer blockers remain unchanged. No local
model workaround, full-corpus execution, scored activation, freeze or
publication is part of this scope.


## Retained result

The independent control is **blocked**. The canonical summary pair has not run.
Portable evidence verification passes only while preserving the failed
near-miss; it does not qualify the family or activate benchmark scores.

| Chain | Attached manual summaries | Assisted endpoint flow |
| --- | --- | --- |
| Real Data roundtrip of raw input | all four calls | source 12 → sink 17 |
| Real Data roundtrip of safe literal | all four calls | none |
| Constant-body local Data/String lookalikes | **all four local calls** | **source 12 → sink 27 (false flow)** |

The vendor-native lane has no source or flow. Each lane retains six sink nodes
across the three calls; the adapter-assisted lane has one environment source.
The local chain's Data initializers discard input, its encoder returns a fixed
base64 string, and its String initializer returns `"echo clean"`. The observed
flow therefore fails the original separating expectation.

Resolved identities distinguish every local method. On this pinned SDK, the
real Data methods resolve to module and owner Foundation.Data. The real String
initializer is defined in Foundation on owner Swift.String. The local String
extension is defined in the fixture module on the same Swift.String owner;
owner identity alone would miss this distinction.

There are 14 attached manual port rows. All four local calls receive ports,
including `ReturnValue.OptionalSome` on the local String initializer. Origins
remain empty; the catalog source is context, not exact originating-row proof.
The nine simple call-site edges cover the three Data operations in each chain.
A separately preregistered store probe retains five store edges: CollectionElement
on the two real Data constructors and OptionalSome on all three String
conversions, including the local constant-body conversion. Attachment, simple
edges, stores and endpoint flow remain separate observations; this package does
not claim an exclusive selected-path attribution from their coexistence.

The first extraction completed in 111.512 seconds and all six queries succeeded.
The simple-edge probe cannot express stores; its original rows and query remain
unchanged. The additional store observation reused the same database after
checking all 422 non-cache source-data file hashes and the source archive.
Only the mutable query-cache subtree was excluded. No new extraction occurred.

Raw attempts, preregistrations, vendor source and archive are retained under
`evidence/swift-summary-qualification-v1`. Run
`python3 scripts/verify-swift-summary-control.py` and
`python3 scripts/test-swift-summary-control.py` for portable integrity and
mutation checks. The append and sanitizer blockers remain independent.
Aggregate memory compliance and semantic completeness remain unproven.
