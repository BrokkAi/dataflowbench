# CodeQL adapter

The CodeQL adapter runs language-scoped benchmark kernels against canonical
fixtures. Java, JavaScript, TypeScript, Python, Kotlin, C#, Go, C, C++, Rust,
and Ruby have separate selections, query paths, normalized reports, and
retained raw-evidence directories. JavaScript and TypeScript share CodeQL's `javascript` extractor
and standard library, but they are two separate populations: each slice
selects only its own language's cases, and each query additionally guards on
its fixture's file extension so the result sets cannot overlap. Kotlin is
extracted by the same `java` extractor and standard library as Java, so its
query restricts every node to `.kt` files and its runner selects only Kotlin
cases. C# and Go each have their own extractor and their own population. C and
C++ share the `cpp` extractor and one pack, and are likewise two populations
with two denominators: 28 templates (56 assertions) for C++, whose
challenge-tier row is now rolled out, and 15 templates (30 assertions) for C,
plus two C `language-extension` cases that never enter the C core denominator. Each of the two queries restricts its data-flow nodes to its
own fixture extension. Rust has its own extractor too, whose support is a
**public preview** in the pinned CLI, and its own population: the same
reduced 15-template classic denominator as C, expanded to 27 templates by its
challenge-tier row, plus two Rust `language-extension` cases
that never enter the Rust core denominator. Ruby has its own production extractor and its own
expanded 29-template population; it is the primary decisive analyzer for the
Ruby tranche, whose Bifrost coverage gate is recorded in [the Ruby kernel
contract](../../docs/ruby-kernel.md). All eleven kernel reports are bound by
the v0.4.0 freeze, each re-run over its own expanded population at one fixture
revision.

Scala is deliberately absent. CodeQL CLI 2.26.3 has no Scala extractor and no
Scala library pack in any build mode, so there is no `scala/` pack, no query,
and no `run-codeql-scala-kernel` command. That absence is analyzer coverage —
recorded in [the Scala kernel contract](../../docs/scala-kernel.md) — and
never a negative result for any Scala assertion. It is restated unchanged for
Scala's **expanded 29-template / 58-assertion core**: the 26 challenge
assertions are covered by the same absence as the 32 classic ones, and because
the extractor does not exist, this is coverage rather than a missing run: the
v0.4.0 freeze re-ran every CodeQL kernel that exists, and Scala is not one.

The checked-in query packs contain the Java, JavaScript, TypeScript, Python,
Kotlin, C#, Go, C, C++, Rust, and Ruby kernel queries. Each query uses that
language's CodeQL data-flow API and the benchmark-controlled `dfb_source()`/`dfb_sink(value)` contract; the
Python query is `python/queries/PythonKernel.ql` in its own Python
database-schema pack, the TypeScript query is
`typescript/queries/TypeScriptKernel.ql` in its own pack, the Kotlin query
is `kotlin/queries/KotlinKernel.ql` in its own pack pinned to the same
`codeql/java-all@9.2.3` as the root Java pack, and the C# query is
`csharp/queries/CSharpKernel.ql` in its own C# pack, and the Go query is
`go/queries/GoKernel.ql` in its own Go pack. The C and C++ queries are
`cpp/queries/CKernel.ql` and `cpp/queries/CppKernel.ql` in one shared C-family
pack pinned to `codeql/cpp-all@12.0.2`, the Rust query is
`rust/queries/RustKernel.ql` in its own Rust pack pinned to
`codeql/rust-all@0.2.19`, and the Ruby query is
`ruby/queries/RubyKernel.ql` in its own Ruby pack pinned to
`codeql/ruby-all@6.0.3`.

The Java kernel adapter creates one CodeQL database per canonical case,
compiles the fixture with its real `javac` build, runs the pinned
`dataflowbench/codeql-java` query pack, retains SARIF, and normalizes only the
presence or absence of query results. It does not treat query compilation,
database creation, or analysis failures as negative results.

## JavaScript kernel

The JavaScript runner selects the whole JavaScript core `taint` population —
32 assertions classically, and **58** now that its thirteen challenge templates
have rolled out (`docs/challenge-tier.md`) — whose `language` is `javascript`,
`score_tier` is `core`, and `tool_model_references.codeql.query` is:

```text
adapters/codeql/javascript/queries/JavaScriptKernel.ql
```

The query belongs to the dedicated JavaScript pack manifest at
`adapters/codeql/javascript/qlpack.yml`; the Java pack and query are separate.

That selection is 29 language-neutral templates — the classic 16 plus the 13
challenge templates — with one positive and one negative assertion each. It
writes the normalized report to
`reports/codeql-javascript-kernel.json` and keeps each case's SARIF (or raw
runner diagnostic when CodeQL cannot produce SARIF) under the dedicated
`reports/raw/codeql-javascript/` directory. JavaScript evidence is never read
from the Java report or from `reports/raw/codeql/`.

Reproduce the run from the repository root with an already-installed CodeQL
CLI and the required packs:

```bash
cargo run -- run-codeql-javascript-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The runner records the exact `codeql version --format=json` version and build
identity in the normalized report. The retained JavaScript run used CodeQL CLI
2.26.3, build SHA
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, with the official `github/codeql`
tag `codeql-cli/v2.26.3` at source commit
`44a68d3a47fcbcd6a6a76ec7d1c1b3a1a28b201e`.

The tested reproduction pointed `--codeql-packs` at the matching official
source workspace root (the retained SARIF records
`/private/tmp/codeql-source-v2.26.3`), or equivalently at a matching CLI
bundle pack root:

```bash
CODEQL=/path/to/codeql-v2.26.3/codeql
CODEQL_SOURCE_ROOT=/private/tmp/codeql-source-v2.26.3
cargo run -- run-codeql-javascript-kernel \
  --codeql "$CODEQL" \
  --codeql-packs "$CODEQL_SOURCE_ROOT"
```

Registry retrieval of `codeql/javascript-all@2.9.0` was unavailable in that
environment. The committed JavaScript lock and the successful run use
`codeql/javascript-all@2.9.0`; users may use a matching official source
workspace or bundle when registry retrieval is unavailable.

For each selected case, the runner copies only the declared JavaScript fixture
files to an isolated temporary workspace, creates a fresh CodeQL database with
the JavaScript language extractor, runs the dedicated query, and removes the
temporary workspace and database after retaining the raw evidence. A database
or compiled fixture is not reused between cases or between the positive and
negative members of a pair. The per-case CodeQL operations are equivalent to:

```bash
codeql database create /tmp/dataflowbench-js-db \
  --language=javascript \
  --source-root=/tmp/dataflowbench-js-fixture \
  --overwrite
codeql database analyze /tmp/dataflowbench-js-db \
  adapters/codeql/javascript/queries/JavaScriptKernel.ql \
  --format=sarif-latest \
  --output=reports/raw/codeql-javascript/CASE_ID.sarif.json
```

The runner uses isolated, case-specific temporary paths rather than these
illustrative names.

## Kotlin kernel

The Kotlin runner selects exactly the `taint` cases whose `language` is
`kotlin` and `score_tier` is `core` — **58 now that Kotlin's challenge-tier row
is rolled out** — and pins
`adapters/codeql/kotlin/queries/KotlinKernel.ql` for the whole population. It
refuses any Kotlin core case that declares a *different* CodeQL query. Two of
them — the direct-propagation pair frozen in v0.2.0 as part of the
cross-language breadth slice — declare no CodeQL reference at all; see the
[Kotlin kernel contract](../../docs/kotlin-kernel.md).

`reports/codeql-kotlin-kernel.json` was re-run whole over that expanded
population for the v0.4.0 freeze and now carries all 58 assertions, scoring
**46/58** — 27/32 on the classic sixteen templates, unchanged case for case,
and 19/26 on the challenge thirteen. The retained Kotlin snapshot below reports
both strata.

CodeQL CLI 2.26.3 cannot extract Kotlin under `--build-mode=none`, so the
runner traces a real `kotlinc` compile per case:

```bash
cargo run -- run-codeql-kotlin-kernel \
  --codeql /path/to/codeql \
  --kotlinc /path/to/kotlinc
```

It writes `reports/codeql-kotlin-kernel.json` and retains SARIF (or a raw runner
diagnostic when CodeQL cannot produce SARIF) under
`reports/raw/codeql-kotlin-kernel/`. Kotlin evidence is never read from the Java
report or from `reports/raw/codeql/`.

## Evidence and outcome semantics

Canonical fixtures contain only benchmark-controlled source, sink, and witness
markers. The query owns the CodeQL model; the case metadata remains analyzer
neutral. SARIF result locations are reconciled with the case's sink anchors,
while the query path evidence identifies the source-to-sink flow and the
normalized result retains both anchor sets. A `DFB-SINK:` marker identifies
the anchored sink declaration/function; SARIF may locate the corresponding
sink callsite elsewhere on the same fixture file, so matching does not require
the marker's exact line. A normalized `reached` outcome therefore requires
successful query execution and a finding tied to that anchored sink identity.
A successful run with no matching finding is `not-reached`.

The adapter preserves the complete five-state outcome model:

| Outcome | Meaning |
| --- | --- |
| `reached` | Successful CodeQL execution produced anchor-backed flow evidence. |
| `not-reached` | Successful CodeQL execution completed with no matching flow. |
| `inconclusive` | Execution completed, but the retained evidence is incomplete or cannot establish the benchmark assertion. |
| `unsupported` | The case is outside the documented CodeQL profile. |
| `runner-error` | Database creation, query execution, SARIF parsing, or another runner step failed. |

`inconclusive`, `unsupported`, and `runner-error` are never normalized to
`not-reached`. Raw SARIF and raw error diagnostics are retained per case even
when normalization cannot produce a complete semantic outcome.

The Java command and report remain available independently:
`run-codeql-java-kernel` writes `reports/codeql-java-kernel.json` and retains
its evidence under `reports/raw/codeql/`. Its Java query is not a JavaScript
model and must not be used as a proxy for this kernel.

## Retained JavaScript snapshot

`reports/codeql-javascript-kernel.json` was re-run whole over the expanded
population for the v0.4.0 freeze, on this repository's established
re-run-at-freeze pattern, and now contains **58 results**: 23 `reached` and 35
`not-reached`, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. **48 of 58** match the expected polarity — 29/32 on the classic
sixteen templates, identical case for case to the pre-expansion snapshot, and
19/26 on the challenge thirteen. A 32-assertion score and a 58-assertion score
are different populations and are never compared.

The three classic mismatches are:

- `dfb-taint-javascript-alias-propagation-positive`: false negative.
- `dfb-taint-javascript-expression-positive`: false negative.
- `dfb-taint-javascript-loop-carried-negative`: false positive.

The seven challenge mismatches — A **3/6**, B **6/8**, C **4/6**, D **6/6** —
are six false negatives on positives (`reflective-invocation`,
`dispatch-table`, `function-field`, `callback-registration`, `map-iteration`,
`nested-access-path`) and one false positive, the `computed-property` negative.
The `reflective-invocation` and `dispatch-table` positives are missed while
their negatives are correct — an under-approximating refusal to follow a callee
named at run time — and the `computed-property` pair inverts that, reaching the
positive and also flagging the negative. The preregistration reads stratum A as
approximation character rather than as a ranking.

All 58 raw case outputs are SARIF files under
`reports/raw/codeql-javascript/`; there are zero retained error files. The
normalized report has empty `witness_checkpoints` for every case because the
current adapter records anchor-backed flow outcomes while retaining path
evidence in SARIF rather than fabricating normalized witness markers. Its
configuration hash is
`cb54d749e915208a1fa7fceaa1e5e5302c18960aebf724573040fda66c7a7ba8`.

## TypeScript kernel

The TypeScript runner selects the whole TypeScript core `taint` population —
32 assertions classically, and **58** now that its thirteen challenge templates
have rolled out (`docs/challenge-tier.md`) — whose `language` is `typescript`
and `score_tier` is `core`, and runs:

```text
adapters/codeql/typescript/queries/TypeScriptKernel.ql
```

owned by the dedicated pack manifest `adapters/codeql/typescript/qlpack.yml`.
That pack depends on the same `codeql/javascript-all@2.9.0` as the JavaScript
pack, because CodeQL extracts TypeScript with its `javascript` extractor. The
populations stay disjoint through three independent guards: the runner's
`language` selector, each query's fixture-extension predicate (`ts` here, `js`
in `JavaScriptKernel.ql`), and separate report and raw-evidence roots. The
runner refuses JavaScript cases exactly as the JavaScript runner refuses
TypeScript ones, and it refuses any selected case that declares a query other
than its own.

```bash
cargo run -- run-codeql-typescript-kernel --codeql /path/to/codeql
```

It writes `reports/codeql-typescript-kernel.json` and retains per-case SARIF
(or raw runner diagnostics) under `reports/raw/codeql-typescript/`.

The direct-propagation pair is shared with the cross-language direct-flow
breadth slice and was frozen in `v0.2.0` before this pack existed, so its case
bytes carry no CodeQL query reference. Rather than rewrite frozen evidence, the
runner defaults a selected TypeScript case with no declared query to this
kernel's query. See [the TypeScript kernel
document](../../docs/typescript-kernel.md) for the full adaptation table and
the freeze rationale.

### Retained TypeScript snapshot

`reports/codeql-typescript-kernel.json` was re-run whole over the expanded
population for the v0.4.0 freeze, on this repository's established
re-run-at-freeze pattern, and now contains **58 results**: 23 `reached` and 35
`not-reached`, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. **48 of 58** match expected polarity — 29/32 on the classic sixteen,
identical case for case to the pre-expansion snapshot, and 19/26 on the
challenge thirteen (A **3/6**, B **6/8**, C **4/6**, D **6/6**).

The classic mismatches are the alias-propagation and arithmetic-expression
positives, both false negatives, and the loop-carried negative, a false
positive; the challenge mismatches are false negatives on the
`reflective-invocation`, `dispatch-table`, `function-field`,
`callback-registration`, `map-iteration` and `nested-access-path` positives and
one false positive on the `computed-property` negative. That is case-for-case
identical to the JavaScript snapshot above, across both strata, as expected for
fixtures that differ only by
type annotations — and the two remain separate populations that are never
pooled. All 58 raw outputs are SARIF files with zero error files.
The run used CodeQL CLI 2.26.3, build SHA
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, with `codeql/javascript-all@2.9.0`
resolved by `codeql pack install` from the registry — no `--codeql-packs`
fallback was needed. Its configuration hash is
`97949db804086b91f4737ad2e6a8ac5dab461f811a7a033250a00ced32eac54c`.

## Python kernel

The Python query selects exactly Python's core assertions: every benchmark
`dfb_source()` call is a source, and argument zero
of every benchmark `dfb_sink(value)` call is a sink. It does not match fixture
names or treat an absent finding as an execution success. The Python dependency
is pinned to `codeql/python-all@7.2.3`, the compatible pack released for CodeQL
CLI v2.26.3 (CLI build `7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`; Python pack
build SHA `44a68d3a47fcbcd6a6a76ec7d1c1b3a1a28b201e`).

The Python query is a `problem` query over `flow(source, sink)`, selecting the
sink location for each reached flow. CodeQL CLI v2.26.3 emits the result
location and message for this query but no `codeFlows`; the retained SARIF
therefore remains the authoritative raw location evidence.

On the direct positive and direct negative fixtures, the problem query produced
one result at `direct_flow.py:10:14` and zero results respectively; the positive
SARIF result has no `codeFlows`. Exact-path end-to-end analysis took 64.30
seconds (positive) and 85.39 seconds (negative), including query-plan
compilation. This was materially faster than the path-query baseline observed
at approximately 4m10s compile plus 10.5s evaluation on the positive fixture.

With the CLI and packs in explicit locations, assemble one CodeQL bundle for
the Python pack. The bundle manifest is required because `--additional-packs`
accepts a pack root or a `.codeqlmanifest.json` bundle, while `pack download`
stores versioned packs below a `codeql/<name>/<version>` directory:

```bash
CODEQL=/private/tmp/dataflowbench-codeql-v2.26.3/codeql/codeql
PACKS=/private/tmp/dataflowbench-codeql-v2.26.3/packs
BUNDLE=/private/tmp/dataflowbench-codeql-v2.26.3/python-pack-bundle

# Download the pinned direct and transitive packs into PACKS.
$CODEQL pack download --dir "$PACKS" \
  codeql/python-all@7.2.3 codeql/concepts@0.0.29 \
  codeql/controlflow@2.0.39 codeql/dataflow@2.1.11 \
  codeql/mad@1.0.55 codeql/regex@1.0.55 codeql/ssa@2.0.31 \
  codeql/threat-models@1.0.55 codeql/tutorial@1.0.55 \
  codeql/typetracking@2.0.39 codeql/util@2.0.42 \
  codeql/xml@1.0.55 codeql/yaml@1.0.55

# Build one explicit bundle for the runner's single --codeql-packs argument.
rm -rf "$BUNDLE"
mkdir -p "$BUNDLE/qlpacks/codeql"
for pack in concepts controlflow dataflow mad regex ssa threat-models tutorial \
  typetracking util xml yaml python-all; do
  cp -R "$PACKS/codeql/$pack" "$BUNDLE/qlpacks/codeql/"
done
cp /private/tmp/dataflowbench-codeql-v2.26.3/codeql/.codeqlmanifest.json \
  "$BUNDLE/.codeqlmanifest.json"

$CODEQL pack ci adapters/codeql/python --additional-packs "$BUNDLE"
$CODEQL query compile adapters/codeql/python/queries/PythonKernel.ql \
  --additional-packs "$BUNDLE"
cargo run -- run-codeql-python-kernel \
  --codeql /private/tmp/dataflowbench-codeql-v2.26.3/codeql/codeql \
  --codeql-packs "$BUNDLE"
```

The Python run writes its normalized report to
`reports/codeql-python-kernel.json` and retains raw SARIF in the dedicated
`reports/raw/codeql-python-kernel/` directory. Database creation, query
compilation, or analysis failures remain `runner-error`; they are never normalized as
`not-reached`. An unsupported case remains `unsupported`, while a successfully
executed query with no SARIF flow is `not-reached`. The full compile above
populates the compilation cache before the runner starts, so per-case analysis
does not repeat query compilation. Every case still uses an isolated cold
database; no database or compiled fixture is reused across the pair.

**The expanded Python population.** Python's challenge-tier row is rolled out
and its core denominator is 29 templates / 58 assertions;
`reports/codeql-python-kernel.json` was re-run whole for the v0.4.0 freeze and
now contains **58 results**: 23 `reached` and 35 `not-reached`, with zero
`inconclusive`, `unsupported`, or `runner-error` outcomes. **48 of 58** match
the expected polarity — 28/32 on the classic sixteen, identical case for case
to the frozen v0.3.0 evidence, and 20/26 on the challenge thirteen (A **3/6**,
B **6/8**, C **5/6**, D **6/6**). The six challenge mismatches are false
negatives on the `reflective-invocation`, `computed-property`,
`dispatch-table`, `closure-capture` and `callback-registration` positives and
one false positive on the `element-object` negative. The v0.3.0 and v0.4.0
populations are never compared number-to-number. Its configuration hash is
`f97f0198f19f2d1d8630b48ff5d30d947e9f83b940de38af425076cf73e82230`.

## C# kernel

The C# runner selects exactly the 58 `taint` cases whose `language` is `csharp`
and whose `score_tier` is `core` — the expanded core, 29 templates after the
challenge wave — and analyzes each with:

```text
adapters/codeql/csharp/queries/CSharpKernel.ql
```

The query belongs to the dedicated C# pack manifest at
`adapters/codeql/csharp/qlpack.yml`, pinned to `codeql/csharp-all@7.1.2` —
the version `codeql pack install` resolves for CodeQL CLI 2.26.3 — with the
full transitive set committed in `adapters/codeql/csharp/codeql-pack.lock.yml`.

The C# direct-propagation pair predates this kernel and is frozen in the
published v0.2.0 manifest without a `codeql` model reference, so the selector
defaults a C# core case with no reference to this kernel's query and rejects a
C# core case that names any other query. See
[the C# kernel contract](../../docs/csharp-kernel.md).

```bash
codeql pack install adapters/codeql/csharp
cargo run -- run-codeql-csharp-kernel --codeql /path/to/codeql
```

Registry retrieval of the C# pack succeeded for the pinned CLI, so the run
needed no `--codeql-packs` fallback; a matching official source workspace or
bundle pack root remains a valid input when retrieval is unavailable.

Each case gets one cold database created from the declared fixture file with
`--build-mode=none`, which the C# extractor supports, so the fixtures need no
project scaffolding, restore, or compiler invocation. The runner writes
`reports/codeql-csharp-kernel.json` and retains SARIF (or raw runner
diagnostics) under `reports/raw/codeql-csharp-kernel/`. SARIF locations are
reconciled with the case's `DFB-SINK:` anchor by resolving the declared sink
method name and accepting a finding on a line that calls it in the same file.

The checked-in `reports/codeql-csharp-kernel.json` contains **58 results**: 24
`reached` and 34 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes. **47 of 58** match the expected polarity — 27/32 on
the classic sixteen and 20/26 on the challenge thirteen. On the classic stratum
the false
negatives are the alias-propagation, exception-catch, and expression positives,
and the false positives are the array-element and loop-carried negatives — the
same mismatch set the Java kernel shows on those templates; that half is
identical case for case to the frozen v0.3.0 evidence. Its configuration
hash is `cd5f68b8ccb2e4de27cf1606b0c9f2ee8981ce5dfdf8ee2fea08fe977a0c56c9`.

**The expanded C# population.** C#'s challenge-tier row is rolled out and its
core denominator is 29 templates / 58 assertions;
`reports/codeql-csharp-kernel.json` was re-run whole for the v0.4.0 freeze,
exactly as the Python and JavaScript kernels were. Split by stratum the
challenge 20/26 is A **3/6**, B **6/8**, C **5/6**, D **6/6**: five false
negatives on the `reflective-invocation`, `computed-property`,
`dispatch-table`, `function-field` and `callback-registration` positives, and
one false positive on the `element-object` negative. The v0.3.0 and v0.4.0
populations are never compared number-to-number.

## Go kernel

The Go runner selects the whole Go core `taint` population — 32 assertions
classically, and **58** now that its thirteen challenge templates have rolled
out (`docs/challenge-tier.md`) — whose `language` is `go` and whose
`score_tier` is `core`, and analyzes each with:

```text
adapters/codeql/go/queries/GoKernel.ql
```

The query belongs to the dedicated Go pack manifest at
`adapters/codeql/go/qlpack.yml`, pinned to `codeql/go-all@7.2.3` — the version
`codeql pack install` resolves for CodeQL CLI 2.26.3 — with the full transitive
set committed in `adapters/codeql/go/codeql-pack.lock.yml`.

The Go direct-propagation pair predates this kernel and is frozen in the
published v0.2.0 manifest without a `codeql` model reference, so the selector
defaults a Go core case with no reference to this kernel's query and rejects a
Go core case that names any other query. See
[the Go kernel contract](../../docs/go-kernel.md).

```bash
codeql pack install adapters/codeql/go
cargo run -- run-codeql-go-kernel --codeql /path/to/codeql --go /path/to/go
```

Registry retrieval of the Go pack succeeded for the pinned CLI, so the run
needed no `--codeql-packs` fallback; a matching official source workspace or
bundle pack root remains a valid input when retrieval is unavailable.

CodeQL 2.26.3 rejects `--build-mode=none` for Go, so each cold database is built
from an observed compile: the runner writes a minimal `module dataflowbench`
manifest into the per-case workspace and traces `go build ./...` under
`--build-mode=manual`. That is deliberately not autobuild, which would
synthesize its own manifest and resolve dependencies over the network; the
fixtures import nothing, so the traced build is hermetic. The manifest is
extraction scaffolding only and is never committed beside a fixture. The runner
writes `reports/codeql-go-kernel.json` and retains SARIF (or raw runner
diagnostics) under `reports/raw/codeql-go-kernel/`. SARIF locations are
reconciled with the case's `DFB-SINK:` anchor by resolving the declared sink
function name and accepting a finding on a line that calls it in the same file.

`reports/codeql-go-kernel.json` was re-run whole over the expanded population
for the v0.4.0 freeze, on this repository's established re-run-at-freeze
pattern.

It contains **58 results**: 24 `reached`
and 34 `not-reached`, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes, extracted through go1.26.0. **45 of 58** match the expected polarity —
26/32 on the classic sixteen, identical case for case to the frozen v0.3.0
evidence, and 19/26 on the challenge thirteen (A **3/6**, B **5/8**, C **5/6**,
D **6/6**). On the classic stratum the
false negatives are the alias-propagation, exception-catch, and expression
positives, and the false positives are the array-element, loop-carried, and
infeasible-branch negatives. The first five are the same mismatch set the Java
and C# kernels show on those templates; the infeasible-branch false positive is
Go-specific, and the exception-catch false negative is the capability evidence
the `panic`/`recover` adaptation anticipates. The seven challenge mismatches are
six false negatives on the `reflective-invocation`, `computed-property`,
`dispatch-table`, `function-field`, `callback-registration` and
`anonymous-implementation` positives, plus one false positive on the
`element-object` negative. Its configuration hash is
`56f44b3d983f7ea1dc2fa77a796ac547b01d12535a124f0c9975d3d0b7989161`.

## C and C++ kernels

The C++ runner selects exactly the 56 `taint`/`core` cases whose `language` is
`cpp` — 32 classic assertions plus the 24 the challenge-tier expansion added;
the C runner selects the whole C `taint`/`core` population — 30
assertions classically, and **48** now that C's nine applicable challenge
templates have rolled out (`docs/challenge-tier.md`) — plus its 2
`language-extension` cases, which are scored on their own scorecard and never
counted in the core denominator. Each analyzes its own query:

```text
adapters/codeql/cpp/queries/CppKernel.ql
adapters/codeql/cpp/queries/CKernel.ql
```

Both queries live in the shared pack manifest `adapters/codeql/cpp/qlpack.yml`,
pinned to `codeql/cpp-all@12.0.2` with the full transitive set committed in
`adapters/codeql/cpp/codeql-pack.lock.yml`. As with JavaScript and TypeScript,
the shared extractor never merges the populations: the runner's `language`
selector, each query's fixture-extension predicate (`c` versus `cpp`), and
separate report and raw-evidence roots keep them disjoint, and each runner
refuses a case that declares the other kernel's query.

```bash
codeql pack install adapters/codeql/cpp
cargo run -- run-codeql-c-kernel --codeql /path/to/codeql
cargo run -- run-codeql-cpp-kernel --codeql /path/to/codeql
```

Registry retrieval of the C-family pack succeeded for the pinned CLI, so the
runs needed no `--codeql-packs` fallback. Each case gets one cold database
created from the declared fixture file with `--build-mode=none`, which CodeQL
2.26.3 supports for C and C++: the buildless extractor indexes the fixture and
resolves the translation unit through a compiler discovered on the host (Apple
clang 21.0.0 for the retained runs). No build command is traced. The runners
write `reports/codeql-c-kernel.json` and `reports/codeql-cpp-kernel.json` and
retain SARIF (or raw runner diagnostics) under `reports/raw/codeql-c-kernel/`
and `reports/raw/codeql-cpp-kernel/`. SARIF locations are reconciled with the
case's `DFB-SINK:` anchor by resolving the declared sink function name and
accepting a finding on a line that calls it in the same file; a `.`, `->`, or
`::` member access is not such a call. See [the C kernel
contract](../../docs/c-kernel.md) and [the C++ kernel
contract](../../docs/cpp-kernel.md).

The checked-in `reports/codeql-cpp-kernel.json` contains **56 results**: 18
`reached` and 38 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes, and **42 of 56** matching the expected polarity —
28/32 on the classic sixteen, identical case for case to the frozen v0.3.0
evidence, and 14/24 on the challenge twelve (A **2/4**, B **4/8**, C **3/6**,
D **5/6**). The classic mismatches are false
negatives on the alias-propagation and exception-catch positives and false
positives on the array-element and loop-carried negatives. Its configuration
hash is
`8873a63a5898c8b6b10dc24a9fbf2fae3ed5a088faf024524b0bae50f0fc4cc0`.

Every one of the ten challenge mismatches is a **false negative on a positive**
— `computed-property`, `dispatch-table`, `closure-capture`, `function-field`,
`callback-registration`, `anonymous-implementation`, `map-iteration`,
`nested-access-path`, `element-object`, and the two-level context positive — with
no false positive anywhere in the tier. That is a uniformly under-approximating
character on this population, not half a score, and a 32-assertion score is
never compared with a 56-assertion one. `reflective-invocation` is inapplicable
to C++ and reduces only its denominator.

`reports/codeql-c-kernel.json` was likewise re-run whole over C's expanded
48-assertion population for the v0.4.0 freeze, on this repository's established
re-run-at-freeze pattern.

It contains **50 results** with the same
clean execution profile. Of the 48 core assertions, 23 are `reached` and 25 are
`not-reached`, with **41 of 48** matching the expected polarity — 27/30 on the
classic fifteen, identical case for case to the frozen v0.3.0 evidence, and
14/18 on C's nine applicable challenge templates (A **1/2**, B **2/4**, C
**5/6**, D **6/6**). The classic mismatches are the same
alias-propagation false negative and array-element and loop-carried false
positives, with no exception-catch cell in the C population; the challenge
mismatches are false negatives on the `dispatch-table`, `function-field` and
`callback-registration` positives plus one false positive on the
`element-object` negative. Both
`language-extension` cases are `reached`, matching their positive polarity, and
are scored on their own scorecard rather than in the 48-assertion denominator.
Its configuration hash is
`719415b9134dfd43390ffdb76eef45f7ed022f907f22913226c22f93277b62f8`.

## Rust kernel

The Rust runner selects the whole Rust core `taint` population — 30 assertions
over the 15 classic templates `docs/applicability-matrix.md` classifies as
applicable, and **54** now that Rust's twelve applicable challenge templates
have rolled out (`docs/challenge-tier.md`) — plus the two `language-extension`
assertions that carry `Result`/`?` error-path propagation. `exception-catch`
and `chal-reflective-invocation` are both inapplicable to Rust and stay
excluded, reducing only the Rust denominator; the extension pair is scored on
its own tier and never enters the core denominator. Every selected case is
analyzed with:

```text
adapters/codeql/rust/queries/RustKernel.ql
```

owned by the dedicated Rust pack manifest `adapters/codeql/rust/qlpack.yml`,
pinned to `codeql/rust-all@0.2.19` — the version `codeql pack install` resolves
for CodeQL CLI 2.26.3 — with the full transitive set committed in
`adapters/codeql/rust/codeql-pack.lock.yml`.

**Rust support is a public preview.** The pinned CLI emits no maturity flag of
its own; what it does report, and what the lock pins, are pre-1.0 versions:
extractor `rust` 0.1.0 and library pack `codeql/rust-all@0.2.19`, against
1.x-and-above packs for the GA languages. Rust results in this repository are
labelled and read as public-preview analyzer evidence. See [the Rust kernel
contract](../../docs/rust-kernel.md).

```bash
codeql pack install adapters/codeql/rust
cargo run -- run-codeql-rust-kernel --codeql /path/to/codeql
```

Registry retrieval of the Rust pack succeeded for the pinned CLI, so the run
needed no `--codeql-packs` fallback.

Each case gets one cold database created with `--build-mode=none`, so no
fixture is compiled. The Rust extractor does, however, only run its semantic
analyzer when it finds a Cargo manifest in the source root — without one it
warns "semantic analyzer unavailable (no manifest found)" and builds a
syntax-only database in which no call target resolves. The runner therefore
generates a minimal single-crate `Cargo.toml` in each temporary workspace, with
`[[bin]] path` pointing at the case's own `.rs` file so SARIF locations stay on
the case's anchor paths. That manifest is an adapter artifact: no `Cargo.toml`
is checked in beside any case. The runner writes
`reports/codeql-rust-kernel.json` and retains SARIF (or raw runner diagnostics)
under `reports/raw/codeql-rust-kernel/`. SARIF locations are reconciled with
the case's `DFB-SINK:` anchor by resolving the declared sink function name and
accepting a finding on a line that calls it in the same file. Rust declares a
sink exactly as C#, Go, C, and C++ do, so it shares that declaration rule; it
gets its own callsite rule because Rust reaches a member through `.` and a path
through `::`, and neither is a call of the free sink function the anchor
declares.

`reports/codeql-rust-kernel.json` was re-run whole over the expanded
54-assertion population for the v0.4.0 freeze, on this repository's established
re-run-at-freeze pattern.

It contains **56 results**. Its 54
core assertions are 21 `reached` and 33 `not-reached`, with zero `inconclusive`,
`unsupported`, or `runner-error` outcomes; **44 of 54** match the expected
polarity — 28/30 on the classic fifteen, identical case for case to the frozen
v0.3.0 evidence, and 16/24 on Rust's twelve applicable challenge templates
(A **2/4**, B **4/8**, C **4/6**, D **6/6**).
All 15 classic positives are `reached`, so there is no classic false negative;
the two classic mismatches are the array-element and loop-carried negatives,
which are false
positives here as they are for the Java, Kotlin, and C# kernels against this
build. The alias-propagation and expression positives that are false negatives
in every other CodeQL kernel are `reached` here.

On the challenge tier the character inverts: all eight mismatches are **false
negatives on positives** — `computed-property`, `dispatch-table`,
`closure-capture`, `function-field`, `callback-registration`,
`anonymous-implementation`, `map-iteration`, and `element-object` — with no
false positive anywhere in the tier, and every stratum-D cell correct.
`reflective-invocation` is inapplicable to a language with no run-time
reflection and reduces only Rust's denominator.

The two `language-extension` assertions are reported separately and never enter
that denominator: both are `not-reached`, so
`dfb-taint-rust-result-error-propagation-positive` is a false negative — the
pinned preview analyzer does not carry the value through the `Result` error
variant and `?` across the call boundary — and the negative is correct.

All 56 raw outputs are SARIF files under `reports/raw/codeql-rust-kernel/` with
zero error files. Per-case wall clock ran 40.9 s to 43.2 s, about 39 minutes for
the population, because every case re-extracts the Cargo workspace's library
sources. Its configuration hash is
`cc2c728b66e0c273545e3531a672c0987473f3830f5df80b0839f5d04c33600b`.

## Ruby kernel

The Ruby runner selects exactly the 58 `taint` cases whose `language` is `ruby`
and whose `score_tier` is `core` — Ruby's challenge-tier row is rolled out, so
its core is the expanded 29 templates — and analyzes each with:

```text
adapters/codeql/ruby/queries/RubyKernel.ql
```

The query belongs to the dedicated Ruby pack manifest at
`adapters/codeql/ruby/qlpack.yml`, pinned to `codeql/ruby-all@6.0.3` — the
version `codeql pack install` resolves for CodeQL CLI 2.26.3 — with the full
transitive set committed in `adapters/codeql/ruby/codeql-pack.lock.yml`.

The Ruby direct-propagation pair predates this kernel and is frozen in the
published manifest without a `codeql` model reference, so the selector defaults
a Ruby core case with no reference to this kernel's query and rejects a Ruby
core case that names any other query.

`docs/applicability-matrix.md` gates the Ruby tranche on Bifrost's Ruby
indexing, and the tranche proceeds **CodeQL-first**: this is the analyzer the
Ruby denominator is decided by, while the Bifrost outcomes are retained as
capability evidence and never converted into negatives. See [the Ruby kernel
contract](../../docs/ruby-kernel.md).

```bash
codeql pack install adapters/codeql/ruby
cargo run -- run-codeql-ruby-kernel --codeql /path/to/codeql
```

Registry retrieval of the Ruby pack succeeded for the pinned CLI, so the run
needed no `--codeql-packs` fallback. Ruby is buildless: each case gets one cold
database created from the declared fixture file with `--build-mode=none`, with
no project scaffolding, no manifest, and no traced compile. The runner writes
`reports/codeql-ruby-kernel.json` and retains SARIF (or raw runner diagnostics)
under `reports/raw/codeql-ruby-kernel/`. SARIF locations are reconciled with
the case's `DFB-SINK:` anchor through a Ruby-specific dialect: Ruby's parameter
list is optional, so the declared endpoint name is read after the `def` keyword
rather than before a parameter list, comments open with `#`, and a `.` or `::`
prefix is not a call of the free sink method the anchor declares.

The checked-in `reports/codeql-ruby-kernel.json` contains 58 results: 22
`reached` and 36 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes, over 243 s wall clock and 4.1 s to 4.4 s per case.
**49 of 58** match the expected polarity — 29/32 on the classic sixteen
templates and 20/26 on the challenge thirteen.

Ruby was the one CodeQL kernel the v0.3.0 freeze did not bind: the Ruby kernel
landed after it, so it could be re-run whole over the expanded population in
the Ruby challenge wave while the other ten languages waited. The v0.4.0 freeze
binds all eleven CodeQL kernel reports, every one of them re-run over its
expanded population at one fixture revision, so Ruby is no longer an exception.

The classic mismatch set is unchanged case for case: the false negatives are the
alias-propagation and exception-catch positives and the false positive is the
loop-carried negative — the same core mismatch set the Java, Kotlin, C#, and
Python kernels show, without the expression or array-element mismatches several
of them add. The six challenge mismatches are all false negatives on positives:
`reflective-invocation`, `computed-property`, `dispatch-table`,
`function-field`, `callback-registration`, and `anonymous-implementation`. Split
by stratum that is A **3/6** — all six stratum-A results `not-reached`, a
uniformly under-approximating character rather than half a score — B **5/8**
with only closure capture decided, and C and D **6/6 each**, the depth-3
accessor chain, `Hash#each` iteration, the six-hop relay, the depth-5 recursion,
and the k = 2 context pair all resolved. Its configuration hash is
`0292361f24c7b18fa59543de15e5709270a5d717f0e7fa3e61de7a9436fb59f7`, unchanged:
neither the query nor the pack moved, only the population.

## Python modeling matrix

`run-codeql-modeling --language python` runs the twenty-four assertions of
[the benchmark-controlled taint-modeling matrix](../../docs/modeling-matrix.md)
for Python, writing `reports/codeql-python-modeling.json` with raw SARIF under
`reports/raw/codeql-python-modeling/`. It is a **modeling**-tier population
with its own denominator: it never enters the Python kernel's 58-assertion
core, and no number here is ever averaged with one there.

CodeQL enters the matrix with **six of six categories scored**, which is
unsurprising: a query language whose data-flow configuration *is* a model
declaration surface has no category to decline. The interesting question is
not whether it can be told, but whether the resulting semantics match — which
is what the assertions measure.

The model is `adapters/codeql/python/queries/PythonModeling.ql`, one
`DataFlow::ConfigSig` covering all six categories, inside the existing
`dataflowbench/codeql-python` pack so it resolves `codeql/python-all@7.2.3`.
It follows the same design this README already records for the kernels — *the
query owns the CodeQL model; the case metadata remains analyzer neutral* — and
uses no data extensions. Category E is `isSource` over a
`DataFlow::parameterNode` of a method the fixture never calls: CodeQL's data
flow does not require a source to be reachable from a call-graph root.
Category B is a single `isAdditionalFlowStep` from `put`'s value argument to
`get`'s result, conditioned on equal constant keys and an equal receiver
identity, which covers both persistence templates at once.

The run is invoked exactly like the kernels; build the pack bundle once as
described under [Python kernel](#python-kernel), then:

```bash
cargo run -- run-codeql-modeling --language python \
  --codeql /private/tmp/dataflowbench-codeql-v2.26.3/codeql/codeql \
  --codeql-packs "$BUNDLE"
```

The first run decides **all twenty-four assertions correctly** — twelve
`reached` positives and twelve `not-reached` negatives, with no
`inconclusive`, `unsupported`, or `runner-error` outcome anywhere. That is a
statement about model activation and binding, and it is emphatically *not* a
propagation result: CodeQL's Python kernel scores 48/58 on the same fixtures'
tier-mates. The two scorecards answer different questions and are never added
together. Its configuration hash is
`cd3c4feeeb3473e72d9c35a582a32d0b65d281d759bf77f9a2e0c0411d3a7262`.

**Load-bearing verification.** `PythonModelingProbe.ql` is
`PythonModeling.ql` with template 3's propagator declaration — and only that
declaration — removed. Over the same
`model-opaque-propagator-positive` database the committed query returns one
finding and the probe returns zero: the reflective body is not a route CodeQL
follows on its own, so the model, not the propagation, is what the cell
scores. The probe query never scores a case, is never named by a case's
`tool_model_references`, and is never bound into a report's
`configuration_hash`. See [the Python taint-modeling
matrix](../../docs/python-modeling.md).

## Retained v2.26.3 snapshot

Every CodeQL report on this tree uses CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, at the one fixture revision
`sha256:13a11ff48f26dba889f76aeb9ef60213a129abe5ebcfcb966da3a2418c12807e` the
v0.4.0 freeze binds, and every kernel was re-run whole over its expanded
population.

The Java kernel uses `codeql/java-all@9.2.3`. Of its **58** assertions, 29 are
`reached` and 29 are `not-reached`, with **48/58** matching their expected
polarity: 27/32 on the classic sixteen and 21/26 on the challenge thirteen
(A **3/6**, B **7/8**, C **5/6**, D **6/6**). On the classic stratum the
expression, alias, and
exception positives are false negatives, while the array-element and loop-kill
negatives are false positives; on the challenge stratum the
`reflective-invocation` and `computed-property` positives are false negatives
and the `dispatch-table`, `function-field` and `element-object` negatives are
false positives. Its configuration hash is
`eedf28b140e6aaf2c27cac6369ee552803cbc7b7674abd70583e3e962e1ef8b6`. Each case
uses an isolated cold database; no
database or compiled fixture is reused across the pair. The adapter removes
temporary databases and workspaces after retaining SARIF.

The Kotlin snapshot uses the same build with `codeql/java-all@9.2.3`, and
traced Kotlin extraction through kotlinc-jvm 2.4.10. All **58** Kotlin
assertions
executed with ordinary reached/not-reached outcomes: 25 are `reached` and 33
are `not-reached`, with **46/58** matching the expected polarity and zero
special
or error outcomes — 27/32 on the classic sixteen, identical case for case to
the frozen v0.3.0 evidence, and 19/26 on the challenge thirteen (A **3/6**,
B **5/8**, C **5/6**, D **6/6**). The classic false negatives are the
expression, alias-propagation,
and exception-catch positives; the array-element and loop-carried negatives are
false positives — the same five mismatches the Java snapshot shows against this
build. The challenge mismatches are false negatives on the
`reflective-invocation`, `computed-property`, `dispatch-table`,
`callback-registration` and `anonymous-implementation` positives and false
positives on the `function-field` and `element-object` negatives. Its
configuration hash is
`25b92ad6190d65fd76c67da51c3ec0d638cea7699e976941c027a48700b9096e`.

The Python snapshot uses the same build with `codeql/python-all@7.2.3`.
All **58** Python assertions executed with ordinary reached/not-reached
outcomes:
23 are `reached` and 35 are `not-reached`, with **48/58** matching the expected
polarity — 28/32 classic and 20/26 challenge, detailed under [the Python
kernel](#python-kernel) above. The classic false negatives are the
alias-propagation positive,
array-element positive, and exception-catch positive; the loop-carried negative
is a false positive. No special or error outcomes occurred. Every Python case
uses an isolated cold database, with no database or compiled fixture reused
across the pair.

## JavaScript taint-modeling matrix

Its own population, never pooled with a kernel. The
[modeling matrix](../../docs/modeling-matrix.md) preregisters **all six
categories** as scored for CodeQL, which is unsurprising: a query language whose
data-flow configuration *is* a model declaration surface has no category to
decline. The interesting question is not whether it can be told, but whether the
resulting semantics match the declaration.

- Artifact: `adapters/codeql/javascript/queries/JavaScriptModeling.ql`, inside
  the language's existing `qlpack`. That location departs from the
  preregistration's schematic `adapters/codeql/queries/<Language>Modeling.ql`
  because a query outside a pack cannot resolve its `codeql/javascript-all`
  dependency; the declaration surface is unchanged. The report's
  `configuration_hash` binds the query file itself, the same one path every
  modeling run's hash binds.
- No data extensions are used. The query owns the model, which is this adapter's
  stated design, and the case metadata remains analyzer neutral.
- One `DataFlow::ConfigSig` carries all six categories at once: `isSource` over
  the declared source calls *and* over the parameter node of each declared entry
  point, `isSink` over argument 0 of the declared sink calls, `isBarrier` over
  the declared sanitizer's input position and over the two explicit no-flow
  declarations, and five `isAdditionalFlowStep` clauses for the propagators, the
  summaries, and the persistence pair. There is no per-case, per-template, or
  per-polarity branching; each fixture simply contains only the entities its own
  template names, and every undeclared sibling the negatives turn on appears
  nowhere in the query.
- Invocation:
  `cargo run -- run-codeql-modeling --language javascript --codeql <path>`
  (optionally `--codeql-packs <dir>`), writing
  `reports/codeql-javascript-modeling.json` with raw SARIF under
  `reports/raw/codeql-javascript-modeling/`. One cold database per case, the
  same as every kernel, and findings reconciled against the case's own sink
  anchors.

**Result on the pinned CLI: 24 of 24 assertions match** — twelve `reached`
positives and twelve `not-reached` negatives, with no `inconclusive` and no
`runner-error`, across all six categories, the same clean sweep the Python row
records. That is a statement about model activation and binding only; it is not
a propagation-kernel score and is never added to one. Its configuration hash is
`50f4a31741fd93420f8bdad4cbdea9f07dacda897641e12fdcdcdc8d7810e910`.

**Load-bearing verification** is the category-P probe in
`scripts/probe-javascript-modeling-load-bearing.sh`: the same database analyzed
with and without the four-line `Opaque.carry` propagator step returns one SARIF
result and then zero
(`reports/raw/load-bearing-javascript-modeling/codeql-opaque-propagator-{with,without}-model.sarif.json`).
CodeQL does not follow the reflective body on its own — which, on the same
fixture, [Joern does](../joern/README.md#amendment-a4-the-reflective-body-is-followed-unaided).

Two encoding details are worth recording because a first attempt got them
wrong and the run said so. Templates 3 and 7 need their *explicit no-flow*
declarations — `Opaque.block` and `Bridge.hold` — stated as barriers rather than
merely omitted: their bodies are byte-identical to their declared siblings', and
CodeQL reads a body it can see, so `Bridge.hold` produced a false positive until
the no-flow summary was actually declared. And the category-B store identity is
the receiver's *binding*, not its data-flow local source: `put` and `get` sit in
two different procedures by construction, so each reference has its own local
source even when both denote the same store, and comparing local sources linked
nothing.

See [the JavaScript modeling matrix](../../docs/javascript-modeling.md).

## Java taint-modeling matrix

Wave M1's last row. Same partition — **all six categories scored** — and the
same single `DataFlow::ConfigSig` carrying every declaration role, written in
Java's own vocabulary: `MethodCall` and `getArgument` where the JavaScript query
uses `DataFlow::CallNode`.

- Artifact: `adapters/codeql/queries/JavaModeling.ql`. This is the one modeling
  query that sits on the preregistration's *schematic* path rather than under a
  `<language>/queries/` subdirectory, and for the same reason the other two sit
  off it: a modeling query must live inside its language's existing `qlpack`,
  and Java's pack **is** the adapter root. `adapters/codeql/qlpack.yml` declares
  `dataflowbench/codeql-java` with the `codeql/java-all` dependency, and
  `queries/JavaKernel.ql` already lives beside it; there is no
  `adapters/codeql/java/` pack, and a query placed under one would resolve
  nothing. A test asserts that every modeling query resolves a `qlpack.yml` two
  directories up.
- The database is built from a **traced `javac`**, exactly as the Java kernel
  builds it — the Java extractor has no `--build-mode=none` — so the modeling
  run differs from its kernel sibling only in which query it loads.
- Invocation:
  `cargo run -- run-codeql-modeling --language java --codeql <path>`
  (optionally `--codeql-packs <dir>`), writing
  `reports/codeql-java-modeling.json` with raw SARIF under
  `reports/raw/codeql-java-modeling/`.

**Result on the pinned CLI: 24 of 24 assertions match** — twelve `reached`
positives and twelve `not-reached` negatives, no `inconclusive` and no
`runner-error`, across all six categories. That is the third clean sweep in
three languages, and it is what establishes that the twelve templates are
satisfiable as preregistered rather than badly posed. Its configuration hash is
`38acb5de67ed39a244c7eb8a9db755ddbcf197488051a5f1ec0d35b65fa30aee`.

**Load-bearing verification** is the category-P probe in
`scripts/probe-java-modeling-load-bearing.sh`: the same database analyzed with
and without the five-line `Opaque.carry` propagator step returns one SARIF
result and then zero
(`reports/raw/load-bearing-java-modeling/codeql-opaque-propagator-{with,without}-model.sarif.json`).
CodeQL does not follow `Opaque.class.getMethod(…).invoke(…)` on its own — which,
on the same fixture, [Joern does](../joern/README.md#taint-modeling-matrix).

See [the Java modeling matrix](../../docs/java-modeling.md).

## JavaScript tool-native probe set

A different profile, not a different population of the same one. Everything
above supplies CodeQL its models; this run supplies **none**. The activation is
the shipped query suite and one documented CLI option, and the
no-benchmark-models gate reads the invocation shape before the binary is touched
and refuses a run that names any benchmark-authored artifact.

- Activation:
  `codeql/javascript-queries@2.4.4:codeql-suites/javascript-security-extended.qls`
  with `--threat-model=local`. No adapter query, no data extension, no
  `--additional-packs` model of ours. 103 rules resolved for the JavaScript
  fixtures.
- `--threat-model=local` configures shipped models rather than adding any: it
  enables the vendor's `local` group, which
  `codeql/threat-models@1.0.55` defines as containing `environment` and
  `commandargs`. Without it, templates 1, 5, and 6 would be decided by the
  default `remote`-only threat model and would miss for a reason unrelated to
  coverage.
- **The library resolution deliberately differs from this adapter's.** The
  pinned *query* pack bundles `codeql/javascript-all@2.10.0`; every
  benchmark-controlled run above pins `javascript-all@2.9.0`. A native run must
  measure the shipped product as shipped, which is one more reason the two
  profiles are never pooled.
- Database creation is byte-for-byte the benchmark-controlled path —
  `codeql_database_create_args` under `CodeqlLanguage::Javascript` — because
  extraction is a property of the language, not of the model profile. Only the
  analyze step differs.
- Reconciliation anchors sit on the platform callsite rather than on a declared
  entity, because this profile has no declared entity. A shipped suite answers
  many questions at once, so a finding away from the anchor is retained as a
  diagnostic and never becomes evidence of a flow; it did not arise in this run.
- Result: **10 of 12**, with a false positive on the sanitizer negative
  (`encodeURIComponent` is a barrier for XSS and request forgery but a
  taint-preserving step for command injection) and both cells wrong on the
  persistence template (the `process.env` write/read pair is unlinked, while the
  plain environment source fires on the distinct-key read). Both were
  preregistered as expectations before the run.

See [the JavaScript tool-native probe set](../../docs/javascript-native.md).
