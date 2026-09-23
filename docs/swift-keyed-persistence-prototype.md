# Swift keyed persistence prototype

The pinned stock library has no UserDefaults value transfer through a key.
The isolated `6.8.4-dfb.5` adapter prototype adds literal-key contents to the
existing heap representation, stores into receiver post-update nodes, reads the
matching content, and clears that content on overwrite. It requests precise
tracking of each key. It does not add direct write-call to read-call edges or
source/sink barriers.

Applicability binds resolved Foundation.UserDefaults instance methods, full
member names, arity and Swift.String key parameters. Key values come from
StringLiteralExpr nodes. The independent local UserDefaults owner remains
outside the model. Prior conversion, SSA and numeric patches remain explicitly
identified in the versioned runtime; no patched lane is labeled vendor-native.

The retained small control reaches the direct sink and the real same-key sink,
with no other-key or local-owner flow. Three store relations, two read relations
and three content-specific overwrite relations are observed. All six queries
and decodes completed. This is feasibility evidence, not qualification.

The expanded preregistration requires clean overwrites, aliases, alias
overwrites, different receivers/domains, same-suite separate instances and
read-before-write separation. Apple documents that a suite initializer reads
and writes the specified settings domain:
[init(suiteName:)](https://developer.apple.com/documentation/foundation/userdefaults/init%28suitename%3A%29).
Treating every constructed object as an independent backing store would miss
that shared-domain behavior. A missing required positive remains incomplete;
a successful small control cannot override it.

No fixture binary is executed or preferences mutated. Dynamic-key and general
shared-domain coverage, aggregate memory compliance and full semantic
completeness remain unproven. No canonical qualification, scored activation,
fixture/population amendment, freeze or publication is claimed here.

## Ordered suite state

The receiver-local `6.8.4-dfb.5` model failed the expanded control: it reached
sinks 13, 16 and 37, but missed alias sink 29 and shared-suite sink 43. This
attempt remains incomplete. Its absence of negative flows does not qualify
alias overwrite behavior.

The `6.8.4-dfb.8` prototype represents state before and after each resolved
literal-key operation, grouped by literal suite name within a callable.
Reference provenance follows CFG/SSA definitions, pattern matching expressions
and forced optional values. Consecutive operations follow CFG paths and cannot
bypass another recognized operation in the same suite. Stores update only their
key; reads select that content. This is a state graph with ordered updates,
not an unordered store-to-load relation.

All development attempts remain retained. Suite-state v1 failed compilation
because its identity proof depended on the data-flow node universe. V2 compiled
but produced empty state domains. The origin diagnostics showed native alias
flow and SSA definitions; the missing step was the typed pattern-to-matching-
expression relation. V3 adds that relation independently of the heap model.

The retained expanded control now reaches exactly sinks 13, 16, 29, 37 and 43.
It excludes other-key, local-owner, clean-overwrite, alias-overwrite,
different-domain and read-before-write near misses. The fresh branch control
repeats those checks and requires both-branch cleaning to be safe while
one-branch cleaning retains a possible flow. It observes exactly sinks
13, 16, 29, 37, 43 and 61. Extraction completed in 97.961 seconds; all eight
queries and decodes completed within their recorded limits.

The portable verifier checks the actual state domains, key contents, clears,
and branch edges as well as endpoint flows. Mutation tests reject a bypass of
an intervening write, a lost branch edge, a false flow through both clean paths,
a missing one-path flow, and a forged suite identity.

## Applicability limits

This is still an isolated, non-scored prototype, not a general UserDefaults
model. The controls use resolved literal suites and keys with unambiguous
receiver provenance. The current existential SSA origin relation is not a
must-alias proof for mixed-origin receivers. Such receivers must not receive a
clean/complete conclusion from this prototype. Dynamic or missing suite names,
dynamic keys, unsupported preference operations, registration/search-domain
behavior, cross-call writes, and concurrent changes remain unqualified.
A production adapter requires a structural applicability/completeness gate or
additional semantics for those forms. No empty result under that missing
coverage is clean evidence.

The new artifacts neither change the 104-entry population nor revise its
historical results or fixture resource budgets. The runtime composes prior
conversion, SSA and scalar-barrier patches with the explicit suite-state
patch. The profile is labeled `adapter-patched-suite-state`, never vendor-native.

## Canonical pair observation

The prospective canonical plan binds both unchanged persistence fixtures from
`swift-synthetic-v2`, their metadata and fixture digests, all query and runner
files, the compiler/SDK/CLI/extractor identities and the 3,398-file patched
runtime manifest. Each fixture is independently extracted and its source
archive retained. The positive requires environment source line 7 to reach sink
line 10 through `payload`; the negative reads `other` and must have no flow.
Both must retain resolved endpoint roles and the actual key-specific state
relations. These observations are explicitly `observed-unqualified`; they do
not activate a scored population lane or establish whole-profile completeness.

The retained pair matches those expectations: the positive has exactly
`7 -> 10`, the negative has zero flow rows, and both retain the environment
source and process-argument sink roles. Extractions took 110.552 and 96.342
seconds respectively; all nine queries and decodes succeeded for each fixture.
The retained-attempt, fresh-control and canonical verifiers exercise 30 regression tests.

Independent source review confirmed the patch/runtime hash joins and identified
three concrete restrictions: existential phi origins can incorrectly strongly
clear multiple suites; unmodeled calls and preference operations can be crossed
without accounting for their writes; and the `Any?` setter payload is not
separately qualified for the string getter. The retained controls use string
payloads and contain no such unmodeled mutations. Future qualification must
prove all reaching receiver origins, account for intervening mutation effects,
and qualify stored/read value types. These are capability gaps, not automatic
unsupported partitions or permission to interpret empty findings as clean.
