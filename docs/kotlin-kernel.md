# Kotlin propagation kernel

Issue #34 ports the sixteen scored Java propagation templates to Kotlin, as
classified in the [applicability matrix](applicability-matrix.md). The Kotlin
cases keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct is adapted to Kotlin syntax.
Every scored Kotlin template has exactly one `positive` and one `negative`
`core` case: 16 templates, 32 core assertions.

The kernel has since been expanded by the thirteen preregistered challenge
templates, all thirteen of which apply to Kotlin: the **Kotlin core denominator
is 29 templates / 58 assertions**. See
[the challenge-tier expansion](#challenge-tier-expansion) below for the two
recorded adaptations, the per-adapter results, and — importantly — the two
adapters whose expanded evidence is **deferred** because their Kotlin reports
are bound by the v0.3.0 freeze.

| Stratum | Template ID | Kotlin adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | **Language-adapted.** A `var` mutable local carries the value; Kotlin defaults to `val`, and an immutable local cannot express the kill. |
| Local | `dfb-template-local-multi-step-chain` | `val` locals carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | Kotlin `Int` arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One relay function is called with a tainted and a clean value; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | A helper returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop helper return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two Kotlin helper returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Two instances of a `class Holder` with a `var` property stand in for distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One `Holder` carries separate `tainted` and `clean` properties. |
| Heap/separation | `dfb-template-alias-propagation-separation` | Assignment of an object reference creates the alias; a second `Holder()` remains distinct. |
| Heap/separation | `dfb-template-array-element-separation` | `IntArray(2)` with distinct constant indices stands in for the Java `int[]`. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the tainted path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | Statement-form `if`/`else` over a `var`, exactly as in the Java kernel; the negative overwrites on both branches, the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | **Language-adapted.** A `var` carried across a `for (iteration in 0 until 3)` loop is either overwritten or computed from. |
| Control transfer | `dfb-template-exception-catch` | Directly applicable: `class FlowException : RuntimeException()` carries an `Int` property across `throw`/`catch`. Kotlin has no checked exceptions, so the unchecked JVM exception class is the faithful equivalent of Java's value-carrying exception. |

Only the two cells the matrix marks `adapted` — `dfb-template-local-overwrite-kill`
and `dfb-template-loop-carried-kill` — deviate from the Java construct, and both
deviate only by requiring `var` where Java uses a plain mutable local. Every
other cell is directly applicable, matching the matrix exactly.

All Kotlin fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
function names inside a `package dataflowbench` object, mirroring the Kotlin
direct-flow fixture already in the breadth slice. The Bifrost adapter lowers
those endpoints through its Kotlin kernel policy and the CodeQL adapter through
its Kotlin kernel query; fixture metadata remains analyzer-neutral and reports
retain only observed evidence.

## Challenge-tier expansion

[The challenge tier](challenge-tier.md) preregistered thirteen further
propagation templates before any fixture existed. Its applicability matrix
classifies **all thirteen as applicable to Kotlin**, two of them
`language-adapted`, so the Kotlin core denominator grows from 16 templates / 32
assertions to **29 templates / 58 assertions**. The challenge cases carry
`score_tier: "core"` — there is no separate tier — and their fixture provenance
revision is `m3-challenge-kotlin`.

The v0.3.0 sixteen-template core and this expanded core are different
populations and are never compared number to number.

### Adaptation notes

Two cells are `language-adapted`, exactly as the preregistration's Kotlin row
states, and both for the same reason: **Kotlin's own reflection API lives in
`kotlin-reflect`, a separate Maven artifact**, which the tier's stdlib-only
fairness constraint excludes. The fixtures therefore reach for the JVM's
`java.lang.reflect`, which every Kotlin compilation already has on its
classpath. Nothing else deviates.

| Stratum | Template ID | Kotlin realization |
| --- | --- | --- |
| A | `dfb-template-chal-reflective-invocation` | **Language-adapted.** `Target::class.java.getMethod(name, String::class.java)` with `name` a local string constant, then `method.invoke(target, dfb_source())`. The negative points `name` at the sibling `drop` method, which discards its argument and sinks a clean constant. `kotlin.reflect` is not used and not on the classpath. |
| A | `dfb-template-chal-computed-property` | **Language-adapted.** Kotlin has no computed member syntax, so the shape goes through `java.lang.reflect.Field`: `Holder::class.java.getDeclaredField(key).set(holder, dfb_source())` and a matching `get(holder)`. This is the same adaptation the preregistration fixes for Java. The properties are declared `@JvmField` so the reflective access needs no `setAccessible` call and stays a plain field read and write. The negative writes under `"alpha"` and reads a provably distinct `"beta"`. |
| A | `dfb-template-chal-dispatch-table` | Direct. `mapOf<String, (String) -> Unit>("leak" to ::leak, "drop" to ::drop)` — Kotlin function types are first-class values, so no functional-interface wrapper is needed — selected with `table.getValue(key)` and then invoked. |
| B | `dfb-template-chal-closure-capture` | Direct. `makeReporter()` binds the tainted local and returns `{ dfb_sink(captured) }`; the caller invokes it after the local has left scope. The negative captures a clean local while the source call stays live. |
| B | `dfb-template-chal-function-field` | Direct. A `class Holder` with a `var fn: (String) -> Unit` property; two instances, one holding `::leak` and one `::drop`, and a separate `dispatch(holder, value)` that reads the field and calls it. The negative hands `dispatch` the second holder. |
| B | `dfb-template-chal-callback-registration` | Direct. A `Registry` with a `MutableList<(String) -> Unit>`, a `register` method, and a `fire` driver that iterates and invokes. No framework, no annotation, twenty lines of language. |
| B | `dfb-template-chal-anonymous-implementation` | Direct. Kotlin **object expressions** are genuinely anonymous implementations: `val leak: Handler = object : Handler { override fun handle(value: String) { dfb_sink(value) } }`, invoked through the interface-typed variable. Both object expressions capture nothing, which is what keeps this distinct from `closure-capture`. `Handler` is declared `fun interface` so that the single abstract method is explicit in the source. |
| C | `dfb-template-chal-map-iteration` | Direct. `for ((key, value) in records)` over a `mutableMapOf`, which desugars to entry iteration and never to a keyed `get`. The negative iterates a second, disjoint map. |
| C | `dfb-template-chal-nested-access-path` | Direct. `outer.middle.inner.value` written and read at depth 3; the negative reads the sibling `outer.middle.inner.other`. |
| C | `dfb-template-chal-element-object` | Direct. `arrayOf(Item(), Item())` with distinct constant indices, mirroring the classic `dfb-template-array-element-separation` cell's `IntArray(2)`. `negative_mechanism` stays `field-separation`, the corpus-wide precedent for constant-index separation. |
| D | `dfb-template-chal-deep-relay-chain` | Direct. `relay1` … `relay6` as six same-file object members, no branching and no state. The negative feeds the identical chain a clean constant while the source call stays live. |
| D | `dfb-template-chal-recursive-carry` | Direct. `carry(value, depth)` recursing from 5 to the `depth == 0` base case; the negative's base case returns `"clean"` instead of the carried value. |
| D | `dfb-template-chal-context-pair-depth2` | Direct, following [Amendment A1](challenge-tier.md#amendments): `helper` returns its argument, `wrapper` calls `helper`, and `outerTainted`/`outerClean` are the two two-deep contexts. Both are live in both fixtures; only which returned value reaches `dfb_sink` differs. |

All twenty-six fixtures are standard-library-only — no dependency, no
framework, no build tooling, and no `kotlin-reflect` — and every one of them
compiles clean under the host toolchain this kernel already records,
**kotlinc-jvm 2.4.10**, with `kotlinc -nowarn -d classes <Fixture>.kt`, which is
the same compile the CodeQL runner traces per case.

### Adapter coverage of the expanded population

Kotlin is the wave with the **least** expanded-population evidence in this
change, and the reason is the freeze rule rather than any gap in what the
adapters can do.

| Adapter | Expanded run | Report | Why |
| --- | --- | --- | --- |
| Semgrep CE 1.174.0 | Yes | `reports/semgrep-kotlin-kernel.json` | No freeze binds it |
| Bifrost v0.10.5 | **Deferred** | `reports/bifrost-kotlin-kernel.json` | Freeze-bound |
| CodeQL 2.26.3 | **Deferred** | `reports/codeql-kotlin-kernel.json` | Freeze-bound |
| Joern 4.0.610 | **Not covered** | — | No Kotlin slice exists in this repository |
| OpenTaint `analyzer/2026.08.27.17eb0fe` | Yes | `reports/opentaint-kotlin-kernel.json` | New adapter (#17); post-freeze, binds nothing |

**Both `reports/bifrost-kotlin-kernel.json` and
`reports/codeql-kotlin-kernel.json` are among the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0.** Overwriting either would
invalidate published evidence, so neither adapter was run for this expansion:
**expanded Bifrost and CodeQL evidence is pending the v0.4.0 freeze-prep
re-run**, on the repository's established re-run-at-freeze pattern. This is a
deferral, not an absence of coverage — both adapters cover Kotlin, and the
retained reports below remain valid *classic-population* snapshots of 32
assertions each. They simply predate the 26 challenge fixtures and say nothing
about them in either direction.

**Joern has no Kotlin slice here.** Joern's own distribution ships a
`kotlin2cpg` frontend, and `adapters/joern/README.md` records it as "Available,
not yet in scope"; no Kotlin adapter slice was ever built in this repository,
and this wave did not build one. `JoernKernel` covers Java, JavaScript, Python,
Ruby, PHP, and Rust only. The absence is stated as a fact about this
repository's adapter coverage, not as a Joern capability claim.

### Semgrep CE 1.174.0 — expanded core

`reports/semgrep-kotlin-kernel.json`. The whole 58-case population is selected
and balance-checked, and the bounded profile then decides what is scored, from
case metadata, before Semgrep is invoked.

| Stratum | Assertions | Scored | `unsupported` | Polarity match (scored) |
| --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 14 | 18 | 12/14 |
| Challenge (13 templates) | 26 | 0 | 26 | n/a |

**All twenty-six challenge assertions take the preregistered `unsupported`
partition**, exactly as [the challenge tier](challenge-tier.md) fixed in
advance and as `CHALLENGE_SEMGREP_PARTITION` implements: the decision is keyed
by `template_id`, made from the pinned CE distribution's own documentation, and
each declined assertion retains its own `*-unsupported.json`
capability-decision document naming the declared capability and the documented
boundary it falls outside. The scored subset therefore stays at **14 assertions
and 12/14**, unchanged from the classic run: 9 `reached`, 5 `not-reached`, and
the same two mismatches as every other Semgrep kernel —
`dfb-taint-kotlin-infeasible-branch-negative` and
`dfb-taint-kotlin-loop-carried-negative`, both false positives, both the path
sensitivity the pinned CLI sells as Pro. Zero `inconclusive` and zero
`runner-error`. The partition was not adjusted for this expansion, and
twenty-six declined assertions are coverage, never twenty-six false negatives.

Kotlin's `beta` maturity label in the pinned distribution's own
`semgrep_interfaces/lang.json` is retained in the report, and it did not move a
single case between the partitions — the same statement the classic run made.

### OpenTaint `analyzer/2026.08.27.17eb0fe` — expanded core

`reports/opentaint-kotlin-kernel.json`, from the new OpenTaint adapter (#17):
the pinned JVM-bytecode engine over the whole 58-assertion population, all of
it scored — OpenTaint's pinned documentation fences no capability, so unlike
Semgrep CE there is no documented boundary to preregister an `unsupported`
partition from. 17 `reached`, 41 `not-reached`, zero `inconclusive`, zero
`unsupported`, zero `runner-error`; **38/58** polarity match.

Kotlin is the population where this engine is actually measurable, and the
reason is fixture encoding rather than anything Kotlin-specific: the pinned
engine drops taint on numeric values (the retained value-kind probe under
`reports/raw/opentaint-value-kind-probe/` isolates this), and Kotlin's core
splits 15 `Int`-encoded templates against 14 `String`-encoded ones — the
`direct` pair plus the entire challenge tier. Every `Int`-encoded positive is
missed on that boundary; the `String`-encoded subset scores 23/28. On the
challenge strata the engine scores **21/26**, including correct
discrimination of the depth-6 `deep-relay-chain` pair that Joern's pinned
`maxCallDepth=4` misses in five languages; the one challenge false negative
is the reflective-invocation positive, and the four false positives are one
family of dynamic-heap-location over-approximation (`computed-property`,
`dispatch-table`, `element-object`, `function-field` negatives). See
[the OpenTaint adapter notes](../adapters/opentaint/README.md) for the
per-subset tables and the retained evidence conventions.

### What the deferred adapters are expected to show

Nothing here is a result, and none of it will be reported as one. The
preregistration already states the framing that will apply when the v0.4.0
re-run produces the numbers: stratum A measures approximation character rather
than skill, stratum D's depth-6 relay is calibrated past known engine defaults,
and every engine is expected to be wrong somewhere on the challenge strata. The
retained classic snapshots below are not evidence about the challenge tier and
must not be read as such.

## The frozen direct-propagation pair

`cases/taint/kotlin/direct-positive/` and `cases/taint/kotlin/direct-negative/`
predate this kernel: they are the Kotlin members of the cross-language
direct-flow breadth slice and were frozen byte-for-byte in the v0.2.0 manifest
(`reports/freeze.json`). Their `tool_model_references` therefore still name the
language-neutral `core-direct.rqlp` policy and declare no CodeQL query, and
editing them would invalidate the published freeze.

Both Kotlin kernel runners consequently select the Kotlin core population by
`language`/`track`/`score_tier` and pin the language-qualified policy and query
for the whole population, so all 58 assertions share one configuration:

- Bifrost evaluates `adapters/bifrost/policies/core-kotlin-kernel.rqlp` for
  every selected case.
- CodeQL runs `adapters/codeql/kotlin/queries/KotlinKernel.ql` for every
  selected case, and refuses any Kotlin core case that declares a *different*
  CodeQL query.

The Kotlin kernel results are a separate population from the Kotlin direct-flow
breadth results, from the Java kernel, and from every other language.

## Bifrost selection and reproduction

```bash
cargo run -- run-bifrost-kotlin-kernel --bifrost /path/to/bifrost
```

The command selects exactly the Kotlin `taint`/`core` assertions — 58 now that
the challenge row is rolled out — writes the normalized report to
`reports/bifrost-kotlin-kernel.json`, and retains the raw per-case Bifrost JSON
under `reports/raw/bifrost-kotlin-kernel/`. A report with incomplete runs
normalizes as `inconclusive` even when it contains no findings; it is never
interpreted as a negative.

**This command was not run for the challenge expansion**, because
`reports/bifrost-kotlin-kernel.json` is freeze-bound; see
[the expansion's adapter coverage](#adapter-coverage-of-the-expanded-population).

## CodeQL selection and reproduction

The CodeQL Kotlin vertical slice is exactly the `taint`/`core` cases under
`cases/taint/kotlin/` — 58 now that the challenge row is rolled out. The
dedicated query is:

```text
adapters/codeql/kotlin/queries/KotlinKernel.ql
```

It is owned by the dedicated Kotlin pack manifest at
`adapters/codeql/kotlin/qlpack.yml`, which depends on `codeql/java-all: 9.2.3`
— the same version the root Java pack lock pins. CodeQL extracts Kotlin through
the shared `java` extractor and the shared Java standard library, so the query
restricts every source and sink node to files with the `kt` extension. The Java
kernel and the Kotlin kernel can therefore never share a result set, and the
runner never selects Java cases.

`codeql pack install adapters/codeql/kotlin` resolved the pinned dependency
tree from the registry in the test environment, so no
matching-source-workspace fallback was needed; `adapters/codeql/kotlin/codeql-pack.lock.yml`
is byte-identical to the root Java pack lock.

### Kotlin extraction requires a real compile

CodeQL CLI 2.26.3 **cannot** extract Kotlin under `--build-mode=none`. Verified
directly against the pinned CLI on a minimal Kotlin source root:

```text
CodeQL detected code written in Java/Kotlin but could not process any of it
using the 'none' build mode. Provide a manual build command using --command
```

The runner therefore traces a real Kotlin compile. The tested host used
Homebrew's Kotlin compiler, **kotlinc-jvm 2.4.10 (JRE 26.0.1)**, installed with
`brew install kotlin`; CodeQL 2.26.3 ships Kotlin extractor plugins up to
2.4.0 and selects the matching one. The per-case CodeQL operations are
equivalent to:

```bash
codeql database create /tmp/dataflowbench-kotlin-db \
  --language=java \
  --source-root=/tmp/dataflowbench-kotlin-fixture \
  --overwrite \
  --command="kotlinc -nowarn -d classes LocalChainPositive.kt"
codeql database analyze /tmp/dataflowbench-kotlin-db \
  adapters/codeql/kotlin/queries/KotlinKernel.ql \
  --format=sarif-latest \
  --output=reports/raw/codeql-kotlin-kernel/CASE_ID.sarif.json
```

Run it from the repository root:

```bash
cargo run -- run-codeql-kotlin-kernel \
  --codeql /path/to/codeql \
  --kotlinc /path/to/kotlinc
```

The command creates one cold CodeQL database per case from the declared fixture
files, runs the dedicated query, and clears the temporary database and
workspace after retaining evidence. No database or compiled fixture is reused
between cases or between the members of a pair. It writes the normalized report
to `reports/codeql-kotlin-kernel.json` and raw SARIF or runner diagnostics to
`reports/raw/codeql-kotlin-kernel/`.

## Anchor evidence and result semantics

CodeQL query results are evidence, not ground truth by themselves. The runner
reconciles SARIF result locations with the case's `DFB-SINK:` anchor file; the
marker identifies the anchored sink declaration, and the SARIF result must land
in that anchor file, though not necessarily on the marker's own line. Query path
evidence identifies the `DFB-SOURCE:` to sink flow, and the normalized result
retains both anchor sets.

A successful, anchor-backed finding is `reached`; a successful analysis with no
finding is `not-reached`. Findings that carry no usable physical location, or
that never map onto a canonical Kotlin sink anchor, are `inconclusive`. An
explicitly unsupported capability is `unsupported`, and a database, query,
SARIF, or runner failure is `runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 16 balanced assertions.

## Observed results

Both snapshots below cover the same 32 assertions and are two independent
populations; they are never pooled.

**Both are classic-population snapshots and both are freeze-bound.** They
describe the sixteen-template core only, they were not re-run for the
challenge-tier expansion because `reports/freeze.json` digest-binds them, and
they say nothing about the 26 challenge assertions in either direction. Their
expanded-population successors are pending the v0.4.0 freeze-prep re-run; see
[the expansion's adapter coverage](#adapter-coverage-of-the-expanded-population).
The one adapter re-run over the expanded 58 assertions is Semgrep CE, whose
result is [in that section](#semgrep-ce-11740--expanded-core).

### CodeQL CLI 2.26.3

`reports/codeql-kotlin-kernel.json` has 32 results: **15 `reached` and 17
`not-reached`**, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. **27 of 32** match the expected polarity (27 of 32 decisive). The
mismatches are:

- `dfb-taint-kotlin-expression-positive` — false negative.
- `dfb-taint-kotlin-alias-propagation-positive` — false negative.
- `dfb-taint-kotlin-exception-catch-positive` — false negative.
- `dfb-taint-kotlin-array-element-negative` — false positive.
- `dfb-taint-kotlin-loop-carried-negative` — false positive.

These are exactly the five mismatches the retained Java kernel snapshot shows
against the same CodeQL CLI build, which is the expected result for a shared
extractor and standard library. All 32 retained raw outputs are SARIF files
with zero error files, and normalized `witness_checkpoints` are empty for every
case. Build SHA `7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/java-all@9.2.3`; configuration hash
`25b92ad6190d65fd76c67da51c3ec0d638cea7699e976941c027a48700b9096e`. Kotlin
extraction traced kotlinc-jvm 2.4.10.

### Bifrost v0.10.5

`reports/bifrost-kotlin-kernel.json` has 32 results: **12 `reached`, 10
`not-reached`, and 10 `inconclusive`**, with zero `unsupported` and zero
`runner-error`. **19 of 32** assertions match the expected polarity (19 of the
22 decisive outcomes). Build identity
`728ac69ab93224151c6c951b23d2f5bc681d8558`; configuration hash
`26c37db9bdfc1d848a47052d3753e1d29040f004874290641cb6b706b3a03d61`.

The ten `inconclusive` results are the complete heap/separation stratum
(`object-separation`, `same-object-field`, `alias-propagation`,
`array-element`) and the `exception-catch` pair, both polarities. Each retains
`partial_discovery` evidence with an explicit incompleteness reason — the
`run` procedure's value-flow snapshot is `unknown` or `unproven`. They are
capability coverage, not negatives, and are never counted as such.

The three decisive mismatches are:

- `dfb-taint-kotlin-expression-positive` — false negative.
- `dfb-taint-kotlin-infeasible-branch-negative` — false positive.
- `dfb-taint-kotlin-loop-carried-negative` — false positive.

This improves on the earlier v0.10.2 run (17/32 matching, five decisive
mismatches): the `local-overwrite` and `branch-join` negatives are now
correctly `not-reached`. The frozen v0.2.0 Java kernel evidence remains a
v0.10.2 snapshot until the next freeze re-runs every Bifrost slice.

No fixture was adjusted to make either analyzer pass. The mismatches are
published results.

## Re-freeze obligation

Adding the Kotlin kernel grows the benchmark case population, so every
checked-in normalized report now predates the current fixture set. The frozen
v0.2.0 evidence is untouched and still validates, but a future release freeze
must re-run **every** adapter over the grown population before `create-freeze`
will accept it; `create_freeze` refuses reports whose declared fixture revision
does not match the selected case population.

The challenge-tier expansion sharpens that obligation for Kotlin specifically.
The v0.4.0 freeze-prep re-run must cover, at minimum,
`run-bifrost-kotlin-kernel` and `run-codeql-kotlin-kernel` over the expanded 58
assertions: both were deliberately not run in the expansion because their
reports are digest-bound by the v0.3.0 freeze, and until they are re-run there
is no Bifrost or CodeQL evidence about the Kotlin challenge tier at all.
