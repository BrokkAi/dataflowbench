# Prospective Swift integer sanitizer qualification

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
