# Kotlin propagation kernel

Issue #34 ports the sixteen scored Java propagation templates to Kotlin, as
classified in the [applicability matrix](applicability-matrix.md). The Kotlin
cases keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct is adapted to Kotlin syntax.
Every scored Kotlin template has exactly one `positive` and one `negative`
`core` case: 16 templates, 32 core assertions.

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

## The frozen direct-propagation pair

`cases/taint/kotlin/direct-positive/` and `cases/taint/kotlin/direct-negative/`
predate this kernel: they are the Kotlin members of the cross-language
direct-flow breadth slice and were frozen byte-for-byte in the v0.2.0 manifest
(`reports/freeze.json`). Their `tool_model_references` therefore still name the
language-neutral `core-direct.rqlp` policy and declare no CodeQL query, and
editing them would invalidate the published freeze.

Both Kotlin kernel runners consequently select the Kotlin core population by
`language`/`track`/`score_tier` and pin the language-qualified policy and query
for the whole population, so all 32 assertions share one configuration:

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

The command selects exactly the 32 Kotlin `taint`/`core` assertions, writes the
normalized report to `reports/bifrost-kotlin-kernel.json`, and retains the raw
per-case Bifrost JSON under `reports/raw/bifrost-kotlin-kernel/`. A report with
incomplete runs normalizes as `inconclusive` even when it contains no findings;
it is never interpreted as a negative.

## CodeQL selection and reproduction

The CodeQL Kotlin vertical slice is exactly the 32 `taint`/`core` cases under
`cases/taint/kotlin/`. The dedicated query is:

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

### Bifrost v0.10.2

`reports/bifrost-kotlin-kernel.json` has 32 results: **14 `reached`, 8
`not-reached`, and 10 `inconclusive`**, with zero `unsupported` and zero
`runner-error`. **17 of 32** assertions match the expected polarity (17 of the
22 decisive outcomes). Build identity
`57060b8b062330ab3e9804e1f11e17b290f9447a`; configuration hash
`26c37db9bdfc1d848a47052d3753e1d29040f004874290641cb6b706b3a03d61`.

The ten `inconclusive` results are the complete heap/separation stratum
(`object-separation`, `same-object-field`, `alias-propagation`,
`array-element`) and the `exception-catch` pair, both polarities. Each retains
`partial_discovery` evidence with an explicit incompleteness reason — the
`run` procedure's value-flow snapshot is `unknown` or `unproven`. They are
capability coverage, not negatives, and are never counted as such. This mirrors
the Java kernel's v0.10.2 profile.

The five decisive mismatches are:

- `dfb-taint-kotlin-expression-positive` — false negative.
- `dfb-taint-kotlin-local-overwrite-negative` — false positive.
- `dfb-taint-kotlin-branch-join-negative` — false positive.
- `dfb-taint-kotlin-infeasible-branch-negative` — false positive.
- `dfb-taint-kotlin-loop-carried-negative` — false positive.

No fixture was adjusted to make either analyzer pass. The mismatches are
published results.

## Re-freeze obligation

Adding the Kotlin kernel grows the benchmark case population, so every
checked-in normalized report now predates the current fixture set. The frozen
v0.2.0 evidence is untouched and still validates, but a future release freeze
must re-run **every** adapter over the grown population before `create-freeze`
will accept it; `create_freeze` refuses reports whose declared fixture revision
does not match the selected case population.
