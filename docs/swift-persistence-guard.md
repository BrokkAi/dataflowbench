# Structural persistence applicability

The versioned suite-state runtime now preserves possible taint through a
receiver that joins a known suite with an unknown parameter, including a
loop-carried join. The fresh control retains all earlier cases and adds sinks
86 and 96. Both are reached; setter proof rows 84 and 94 report
`must=false, complete=false` and cannot clear known-suite content. All nine
queries and decodes completed after an 89.716-second extraction.

The new structural applicability query is deliberately conservative. It admits
closed, literal-suite/literal-key string-payload operations with complete
receiver provenance. It emits explicit incomplete reasons for unknown helper
calls before a read, property mutations/observers, unmodeled getters, dynamic
keys, unsupported preference operations, unknown receiver origins and
unqualified setter payload types. Getter admission is limited to the resolved
Foundation process environment and resolved Swift string-dictionary reads.
It does not infer purity from a method's name or from an empty finding set.

AST call enumeration also checks for missing CFG coverage. A top-level
preference read that has no modeled CFG scope emits `MissingCfgCoverage`.
The seven other near-miss families retain their individual reasons; an admitted
literal-string control remains `Complete`. Here `Complete` means only that
this explicit applicability policy admits the observed scope. It is not
whole-program, concurrency, resource, or scored qualification.

The Python interpreter preserves findings under `Incomplete`, rejects empty,
malformed or unknown-status coverage evidence, and can require expected scope
membership. It labels an admitted empty finding set
`NoFindingsInAdmittedScope`, never a globally clean program. The production
adapter has not yet been switched to this gate; integration must require the
coverage query and preserve every selected fixture in the denominator.

All observations are non-scored. Both original diagnostic compile failures,
the empty diagnostic call enumeration, corrected structural observations,
canonical gate checks, and fresh controls are retained with their prospective
plans and immutable manifests. The 104-entry population and historical
reports/freezes are unchanged. This work does not claim activation, final
common-revision execution, freeze, release, or publication.

Admission here checks modeled operations and effects; it does not yet prove
that every read key was initialized on every path. Production integration must
add that initial-state proof or return `Incomplete`, and must retain the
benchmark's explicit isolation assumptions. The canonical pair already writes
both keys before reading, but that fixture fact is not a general gate proof.
