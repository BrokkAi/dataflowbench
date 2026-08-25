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
16-template population; it is the primary decisive analyzer for the Ruby
tranche, whose Bifrost coverage gate is recorded in [the Ruby kernel
contract](../../docs/ruby-kernel.md).

Scala is deliberately absent. CodeQL CLI 2.26.3 has no Scala extractor and no
Scala library pack in any build mode, so there is no `scala/` pack, no query,
and no `run-codeql-scala-kernel` command. That absence is analyzer coverage —
recorded in [the Scala kernel contract](../../docs/scala-kernel.md) — and
never a negative result for any Scala assertion. It is restated unchanged for
Scala's **expanded 29-template / 58-assertion core**: the 26 challenge
assertions are covered by the same absence as the 32 classic ones, and because
the extractor does not exist, this is coverage rather than evidence deferred to
the v0.4.0 re-run.

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

`reports/codeql-kotlin-kernel.json` is freeze-bound, so the runner was **not**
executed over the expanded population: the retained Kotlin snapshot below is a
classic 32-assertion result, and **expanded CodeQL evidence for Kotlin is
pending the v0.4.0 freeze-prep re-run**.

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

**Expanded evidence is deferred.** `reports/codeql-javascript-kernel.json` is
one of the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so
the JavaScript challenge expansion did not overwrite it: the expanded
58-assertion CodeQL evidence is pending the v0.4.0 freeze-prep re-run, on this
repository's established re-run-at-freeze pattern, and the deferral is recorded
in `docs/javascript-kernel.md`. What follows is the valid classic
32-assertion snapshot, and it describes a different population from the
expanded one.

The checked-in `reports/codeql-javascript-kernel.json` contains 32 results:
15 `reached` and 17 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes. Twenty-nine of 32 outcomes match the expected
polarity. The three mismatches are:

- `dfb-taint-javascript-alias-propagation-positive`: false negative.
- `dfb-taint-javascript-expression-positive`: false negative.
- `dfb-taint-javascript-loop-carried-negative`: false positive.

All 32 raw case outputs are SARIF files under
`reports/raw/codeql-javascript/`; there are zero retained error files. The
normalized report has empty `witness_checkpoints` for every case because the
current adapter records anchor-backed flow outcomes while retaining path
evidence in SARIF rather than fabricating normalized witness markers. Its
configuration hash is
`a038e39eb93d6fc674ab59cf2e4de5b3608f1d7b294c19da75ce1bd041c75ac5`.

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

**Expanded evidence is deferred.** `reports/codeql-typescript-kernel.json` is
one of the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so
the TypeScript challenge expansion did not overwrite it: the expanded
58-assertion CodeQL evidence is pending the v0.4.0 freeze-prep re-run, on this
repository's established re-run-at-freeze pattern, and the deferral is recorded
in `docs/typescript-kernel.md`. What follows is the valid classic 32-assertion
snapshot, and it describes a different population from the expanded one.

The checked-in `reports/codeql-typescript-kernel.json` contains 32 results: 15
`reached` and 17 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes. Twenty-nine of 32 match expected polarity; the
alias-propagation and arithmetic-expression positives are false negatives and
the loop-carried negative is a false positive. That is case-for-case identical
to the JavaScript snapshot above, as expected for fixtures that differ only by
type annotations. All 32 raw outputs are SARIF files with zero error files.
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

**Deferred: the expanded Python population.** Python's challenge-tier row is
now rolled out and its core denominator is 29 templates / 58 assertions, but
`reports/codeql-python-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0. Overwriting it would invalidate
a published freeze, so the Python challenge wave left it untouched. Its 32
results remain the frozen 16-template v0.3.0 evidence, and CodeQL's evidence
for the expanded Python core arrives with the v0.4.0 freeze-prep re-run. This
is deferral, not absence of coverage, and the two populations are never
compared number-to-number. The selection code already expects 58; the runner is
simply not invoked until the freeze is re-cut.

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

The checked-in `reports/codeql-csharp-kernel.json` contains 32 results: 15
`reached` and 17 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes. 27 of 32 match the expected polarity; the false
negatives are the alias-propagation, exception-catch, and expression positives,
and the false positives are the array-element and loop-carried negatives — the
same mismatch set the Java kernel shows on those templates. Its configuration
hash is `cd5f68b8ccb2e4de27cf1606b0c9f2ee8981ce5dfdf8ee2fea08fe977a0c56c9`.

**Deferred: the expanded C# population.** C#'s challenge-tier row is now
rolled out and its core denominator is 29 templates / 58 assertions, but
`reports/codeql-csharp-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0. Overwriting it would invalidate
a published freeze, so the C# challenge wave left it untouched, exactly as the
Python and JavaScript waves left theirs. Its 32 results remain the frozen
16-template v0.3.0 evidence, and CodeQL's evidence for the expanded C# core
arrives with the v0.4.0 freeze-prep re-run. This is deferral, not absence of
coverage, and the two populations are never compared number-to-number. The
selection code already expects 58; the runner is simply not invoked until the
freeze is re-cut.

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

**Expanded evidence is deferred.** `reports/codeql-go-kernel.json` is one of the
nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so the Go
challenge expansion did not overwrite it: the expanded 58-assertion CodeQL
evidence is pending the v0.4.0 freeze-prep re-run, on this repository's
established re-run-at-freeze pattern, and the deferral is recorded in
`docs/go-kernel.md`. What follows is the valid classic 32-assertion snapshot,
and it describes a different population from the expanded one.

The checked-in `reports/codeql-go-kernel.json` contains 32 results: 16 `reached`
and 16 `not-reached`, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes, extracted through go1.26.0. 26 of 32 match the expected polarity; the
false negatives are the alias-propagation, exception-catch, and expression
positives, and the false positives are the array-element, loop-carried, and
infeasible-branch negatives. The first five are the same mismatch set the Java
and C# kernels show on those templates; the infeasible-branch false positive is
Go-specific, and the exception-catch false negative is the capability evidence
the `panic`/`recover` adaptation anticipates. Its configuration hash is
`56f44b3d983f7ea1dc2fa77a796ac547b01d12535a124f0c9975d3d0b7989161`.

## C and C++ kernels

The C++ runner selects exactly the 56 `taint`/`core` cases whose `language` is
`cpp` — 32 classic assertions plus the 24 the challenge-tier expansion added;
the C runner selects the 30 `taint`/`core` cases whose `language` is `c`
plus its 2 `language-extension` cases, which are scored on their own scorecard
and never counted in the core denominator. Each analyzes its own query:

The C++ runner selects exactly the 32 `taint`/`core` cases whose `language` is
`cpp`; the C runner selects the whole C `taint`/`core` population — 30
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

The checked-in `reports/codeql-cpp-kernel.json` contains 32 results: 16
`reached` and 16 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes, and 28 of 32 matching the expected polarity — false
negatives on the alias-propagation and exception-catch positives, false
positives on the array-element and loop-carried negatives. Its configuration
hash is
`8873a63a5898c8b6b10dc24a9fbf2fae3ed5a088faf024524b0bae50f0fc4cc0`.

That snapshot is the **classic 32-assertion population only**. It is one of
the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so the C++
challenge wave did not re-run it: **the expanded CodeQL C++ evidence is pending
the v0.4.0 freeze-prep re-run**, on the repository's established
re-run-at-freeze pattern. The selector already expects the full 56; deferral is
not absence of coverage, and a 32-assertion score is never compared with a
56-assertion one.

**Expanded C evidence is deferred.** `reports/codeql-c-kernel.json` is one of
the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so the C
challenge expansion did not overwrite it: the expanded 48-assertion CodeQL
evidence for C is pending the v0.4.0 freeze-prep re-run, on this repository's
established re-run-at-freeze pattern, and the deferral is recorded in
`docs/c-kernel.md`. What follows is the valid classic 30-assertion snapshot,
and it describes a different population from the expanded one.

The checked-in `reports/codeql-c-kernel.json` contains 32 results with the same
clean execution profile. Of the 30 core assertions, 16 are `reached` and 14 are
`not-reached`, with 27 of 30 matching the expected polarity — the same
alias-propagation false negative and array-element and loop-carried false
positives, with no exception-catch cell in the C population. Both
`language-extension` cases are `reached`, matching their positive polarity, and
are scored on their own scorecard rather than in the 30-assertion denominator.
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

**Expanded evidence is deferred.** `reports/codeql-rust-kernel.json` is one of
the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so the Rust
challenge expansion did not overwrite it: the expanded 54-assertion CodeQL
evidence is pending the v0.4.0 freeze-prep re-run, on this repository's
established re-run-at-freeze pattern, and the deferral is recorded in
`docs/rust-kernel.md`. What follows is the valid classic 30-assertion snapshot,
and it describes a different population from the expanded one.

The checked-in `reports/codeql-rust-kernel.json` contains 32 results. Its 30
core assertions are 17 `reached` and 13 `not-reached`, with zero `inconclusive`,
`unsupported`, or `runner-error` outcomes; 28 of 30 match the expected polarity.
All 15 positives are `reached`, so there are no false negatives; the two
mismatches are the array-element and loop-carried negatives, which are false
positives here as they are for the Java, Kotlin, and C# kernels against this
build. The alias-propagation and expression positives that are false negatives
in every other CodeQL kernel are `reached` here.

The two `language-extension` assertions are reported separately and never enter
that denominator: both are `not-reached`, so
`dfb-taint-rust-result-error-propagation-positive` is a false negative — the
pinned preview analyzer does not carry the value through the `Result` error
variant and `?` across the call boundary — and the negative is correct.

All 32 raw outputs are SARIF files under `reports/raw/codeql-rust-kernel/` with
zero error files. Per-case wall clock ran 50.8 s to 98.4 s, about 40 minutes for
the population, because every case re-extracts the Cargo workspace's library
sources. Its configuration hash is
`cc2c728b66e0c273545e3531a672c0987473f3830f5df80b0839f5d04c33600b`.

## Ruby kernel

The Ruby runner selects exactly the 32 `taint` cases whose `language` is `ruby`
and whose `score_tier` is `core`, and analyzes each with:

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

The checked-in `reports/codeql-ruby-kernel.json` contains 32 results: 15
`reached` and 17 `not-reached`, with zero `inconclusive`, `unsupported`, or
`runner-error` outcomes. 29 of 32 match the expected polarity; the false
negatives are the alias-propagation and exception-catch positives and the false
positive is the loop-carried negative — the same core mismatch set the Java,
Kotlin, C#, and Python kernels show, without the expression or array-element
mismatches several of them add. Its configuration hash is
`0292361f24c7b18fa59543de15e5709270a5d717f0e7fa3e61de7a9436fb59f7`.

## Retained v2.26.3 snapshot

The checked-in report uses CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/java-all@9.2.3`. Of 32 assertions, 15 are `reached` and 17 are
`not-reached`; 27 match their expected polarity. The expression, alias, and
exception positives are false negatives, while the array-element and loop-kill
negatives are false positives. Each case uses an isolated cold database; no
database or compiled fixture is reused across the pair. The adapter removes
temporary databases and workspaces after retaining SARIF.

The retained Kotlin snapshot uses the same CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with `codeql/java-all@9.2.3`, and
traced Kotlin extraction through kotlinc-jvm 2.4.10. All 32 Kotlin assertions
executed with ordinary reached/not-reached outcomes: 15 are `reached` and 17
are `not-reached`, with 27/32 matching the expected polarity and zero special
or error outcomes. The false negatives are the expression, alias-propagation,
and exception-catch positives; the array-element and loop-carried negatives are
false positives — the same five mismatches the Java snapshot shows against this
build. Its configuration hash is
`25b92ad6190d65fd76c67da51c3ec0d638cea7699e976941c027a48700b9096e`. It covers
Kotlin's classic 32-assertion population only; the 26 challenge assertions
added since are not in it, and their CodeQL evidence is deferred to the v0.4.0
re-run.

The retained Python snapshot uses the same CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with `codeql/python-all@7.2.3`.
All 32 Python assertions executed with ordinary reached/not-reached outcomes:
14 are `reached` and 18 are `not-reached`, with 28/32 matching the expected
polarity. The false negatives are the alias-propagation positive,
array-element positive, and exception-catch positive; the loop-carried negative
is a false positive. No special or error outcomes occurred. Every Python case
uses an isolated cold database, with no database or compiled fixture reused
across the pair.
