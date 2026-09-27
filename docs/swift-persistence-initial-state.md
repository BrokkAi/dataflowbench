# Initialized-key admission for persistence

The applicability gate now requires a proven same-suite, same-key string write
before each preference read. The write receiver and read receiver both need
complete single-suite provenance. A write in a strictly dominating basic block,
or an earlier position in the same basic block, establishes this conservative
initial-state proof. Names, source order and display strings do not establish
execution order.

The fresh control admits the initialized case and explicitly marks no-write,
conditional-write, wrong-key and write-after-read cases `IncompleteInitialState`.
It retains all five cases in its coverage result. Extraction completed in
85.117 seconds; all three queries and decodes completed. This policy may reject
a valid initialization split across multiple branches because it requires one
dominating write; such rejection is incomplete coverage, not a negative finding.

Executable global calls receive `UnmodeledGlobalExecution`. The benchmark
contract assumes a closed single-threaded fixture and no external mutation of
its preference domain. This is an explicit semantic assumption, not proof of
OS-level isolation, an executed preference reset, or a concurrent-state model.
Fixture binaries are not executed during these observations.

The canonical pair is checked against the same query and pinned runtime. Its
positive and negative both initialize the read keys before the read, so this
gate does not alter their source/sink expectations. Passing applicability does
not activate scoring or prove aggregate memory containment. Production adapter
integration must require the gate output, retain typed incompleteness, and keep
all selected fixtures in the denominator. Historical configurations, reports
and freezes remain immutable.
