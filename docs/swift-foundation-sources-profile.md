# Resolved environment and argv sources

This prospective diagnostic extends the separately labeled Foundation sink
correction from PR #238 with resolver-proven process-input sources. It uses
CodeQL CLI 2.27.1, `codeql/swift-all` 6.8.4, isolated Swift 6.3.3, SDK 26.5,
and the versioned 2048-MiB/60-second analysis policy. Extraction retains its
separate 150-second deadline. Historical 512-MiB evidence, scored profiles,
Joern, corpus outcomes, and published freezes are unchanged.

## Identity and value contract

The environment source must resolve to the `environment` field declared in
module Foundation and owned by nominal type Foundation.ProcessInfo. Its
receiver and accessor self types must resolve to that same type; the field and
read expression must both have dictionary type with Swift.String keys and
values. The argument source must resolve to the `arguments` field declared in
module Swift and owned by Swift.CommandLine, with Swift.String array element
type. Its resolved getter must be static and its access base a metatype.

Both sources bind a `PropertyGetterCfgNode`, its exact accessor from the field,
and the same member-reference expression as the data-flow node. This marks the
returned collection value, not its receiver, a setter update, or a textual
property name. Normal vendor taint semantics carry these values through
indexing. No additional propagation rules are supplied. Existing vendor
sources remain in the corrected configuration. Vendor-native flow is evaluated
separately with its unmodified source and sink predicates.

The sink definition is copied byte-for-byte from the versioned PR #238 profile
and its identity is verified. This makes the standalone query pack reproducible
without changing the older profile or its retained hashes.

## Controls and interpretation

The preregistered function-wrapped control isolates environment and argv reads,
with each reaching both a real Foundation static-call argument and a real
arguments setter. Negatives cover module-local ProcessInfo/CommandLine with
matching String collection types, other owners with matching property types,
module-local integer collections converted to strings, and a constant input.
All negative paths still target genuine Foundation sinks.

The module, owner, type, and accessor guards are conjunctive. Some near misses
violate several guards; these controls do not establish an isolated causal
contribution for every guard. The accepted declarations and their getter/value
relationships are demonstrated by the positive controls and resolved records.

The initial API diagnostic reuses the earlier compatible control database and
preserves the shipped String initializer flow while adding environment/argv
flows. It does not requalify that database's historical unlimited extraction.
The fresh control has its own bounded extraction and contains no file-content
source, so that source cannot explain its process-input flows. No fixture
binary or function is executed.

This remains a non-scored adapter profile. Top-level-statement behavior remains
outside the proven function-wrapped scope. Raw extraction errors block the
observation gate; retained warnings and incomplete process-tree accounting
prevent semantic-completeness or aggregate-memory certification. Joern, opaque
selection, population activation, and release qualification remain separate.

## Retained result

The fresh `control-attempt-01` database finalized in **101.21 seconds** and
passed the raw extractor error gate. Roles, flow, and identity queries completed
in **15.28 / 18.33 / 3.81 seconds**, with measured command maximum RSS of
**1304.05 / 784.28 / 390.56 MiB**. The archived source matches the preregistered
control byte-for-byte. These are command measurements, not aggregate memory
or semantic-completeness certification.

| Fresh control observation | Vendor-native | Adapter-corrected |
| --- | ---: | ---: |
| Environment/argv source nodes | 0 | 2 |
| Recognized sink nodes | 14 | 14 |
| Positive source-to-sink pairs | 0 | 4 |
| Near-miss or safe-constant flows | 0 | 0 |

Both environment and argv reach the intended static-call argument and setter.
All four negative call sites retain both vendor and corrected sink roles but
have no flow. The earlier shipped String source still works in the separate
retained-database diagnostic; this fresh control deliberately excludes it.

Run `python3 scripts/verify-swift-foundation-sources.py` and
`python3 scripts/test-swift-foundation-sources.py` for the retained package and
its mutation guards. CI runs both. The verifier binds live query bytes,
preregistered source and plans, raw outputs, the unchanged sink predicate,
phase limits, compiler-error checks, and non-vacuous positive/negative results.
