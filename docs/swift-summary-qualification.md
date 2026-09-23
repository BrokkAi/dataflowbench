# Prospective Swift Data roundtrip qualification

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
call-site edges are separate observations. The latter returns a Node rather
than an output access-path column; matching `output.asExpr() = call` cannot
distinguish ReturnValue from ReturnValue.OptionalSome. The public ports retain
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
