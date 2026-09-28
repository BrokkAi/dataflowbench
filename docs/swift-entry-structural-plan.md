# Prospective structural controls — proposal only

This plan is separate from the hash-bound ten-control registration and preserves
its failure. No new extraction or query is authorized by this document. Before
execution, commit exact fixture/query bytes and hashes, compiler/SDK/extractor/
schema/pack identities, argv and retained-output paths in a new registration.
The current extractor and schema are unchanged.

## Minimum scope

Use two serial databases, each compiling `main.swift` with a second
`Library.swift` in one explicit module. The library declares an unreferenced
lazy global initialized by a function, plus a function containing an early
return and a local closure. It contains no script statements. Keep the library
identical in both runs. Fixture compilation is required; no executable runs.

| Database | Script construction | Required structural observations |
|---|---|---|
| A: branch and sequence | Source initialization; runtime-unknown if/else assigning source or clean data; sink; unconditional clean overwrite; second sink. Include a nested function/closure with its own return. | One script entry owned by the exact main file and module. Ordered, unique declaration identities with dense indices; both conditional arms and join; first sink has a source path, second sink has none. Nested bodies retain separate CFG scopes; their returns do not end the script scope. |
| B: abrupt completion | Source initialization; runtime-unknown if condition whose arm throws a local Error enum; sink after the conditional. Use the same library declarations. | Same ownership/membership checks. The throwing arm reaches exceptional completion and has no normal successor to the later sink; the other arm reaches the sink. Do not substitute absence of a finding for CFG completion evidence. |

Use a standard-library runtime input such as `CommandLine.arguments.count` to
avoid a constant conditional. Validate that pinned Swift accepts the top-level
throw before extraction. If the QL completion model cannot expose the asserted
edge/exit identities, record that capability gap and stop; do not reinterpret
the test as passing or replace it with a weak location-based check.

## Observation contract

Export database entity identities for entry, source file, module, declaration,
index, body and CFG scope. Perform equality/uniqueness assertions on entities
inside QL; rendered paths/names are labels only. Include negative membership
queries and counts for all top-level declarations, not just those already
attached to an entry. Verify zero script entries owned by Library.swift and
zero entry membership for its initializer or nested function/closure bodies.
Do not assume the unreferenced initializer must be eagerly emitted: if absent,
record absent; it still must not be manufactured as executable script entry.

Inspect exact CFG predecessor/successor and completion relations, plus exact
source/sink binding, CFG/data-flow node presence and ordered overwrite behavior.
Source line order must never implement the expected ordering. Record compiler
declaration sequence evidence independently of the newly emitted sequence.

Compiler auxiliary declarations remain untested unless an existing supported
fixture can produce them under the pinned compiler and extractor. No macro
installation or invented macro qualification is part of these two controls.
Lazy extraction beyond the library-file negative also remains explicitly
unqualified if that extraction path is not exercised.

## Proposed bounded execution

Reuse the existing candidate identities, with no build or model repair. Reserve
40 GiB free disk before each database; no concurrent analyzer/build workload.
Per database: 150 seconds extraction, then 75 seconds shared across all query
and decode commands, two threads, 2,048 MiB requested. Record any tool-raised
minimum separately. Stop on deadline, failed extraction/finalization, insufficient
space or incomplete tracked cleanup. Retain failed attempts, command records,
before/after artifact closure and typed uncertainty. These are diagnostic
limits, not hard aggregate memory certification.

This closes the immediate file/module ownership, non-entry library, conditional,
abrupt completion and nested-scope review gaps with two databases. It does not
qualify all Swift constructs, optional array/callback models, the current108
population, resource containment, scored activation or release publication.
