# CodeQL adapter

The CodeQL adapter runs language-scoped benchmark kernels against canonical
fixtures. Java, JavaScript, Python, and C# have separate selections, query
paths, normalized reports, and retained raw-evidence directories. The
JavaScript query may use CodeQL libraries shared with TypeScript, but this
adapter slice selects only JavaScript cases; TypeScript is a future, separate
population.

The checked-in query packs contain the Java, JavaScript, Python, and C# kernel
queries. Each query uses that language's CodeQL data-flow API and the
benchmark-controlled `dfb_source()`/`dfb_sink(value)` contract; the Python query is
`python/queries/PythonKernel.ql` in its own Python database-schema pack, and the
C# query is `csharp/queries/CSharpKernel.ql` in its own C# pack.

The Java kernel adapter creates one CodeQL database per canonical case,
compiles the fixture with its real `javac` build, runs the pinned
`dataflowbench/codeql-java` query pack, retains SARIF, and normalizes only the
presence or absence of query results. It does not treat query compilation,
database creation, or analysis failures as negative results.

## JavaScript kernel

The JavaScript runner selects exactly the 32 `taint` cases whose `language` is
`javascript`, `score_tier` is `core`, and `tool_model_references.codeql.query`
is:

```text
adapters/codeql/javascript/queries/JavaScriptKernel.ql
```

The query belongs to the dedicated JavaScript pack manifest at
`adapters/codeql/javascript/qlpack.yml`; the Java pack and query are separate.

That selection is 16 language-neutral templates with one positive and one
negative assertion each. It writes the normalized report to
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

## Python kernel

The Python query selects exactly the 32 core assertions (the 16 balanced
templates): every benchmark `dfb_source()` call is a source, and argument zero
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

## C# kernel

The C# runner selects exactly the 32 `taint` cases whose `language` is `csharp`
and whose `score_tier` is `core`, and analyzes each with:

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

## Retained v2.26.3 snapshot

The checked-in report uses CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/java-all@9.2.3`. Of 32 assertions, 15 are `reached` and 17 are
`not-reached`; 27 match their expected polarity. The expression, alias, and
exception positives are false negatives, while the array-element and loop-kill
negatives are false positives. Each case uses an isolated cold database; no
database or compiled fixture is reused across the pair. The adapter removes
temporary databases and workspaces after retaining SARIF.

The retained Python snapshot uses the same CodeQL CLI v2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with `codeql/python-all@7.2.3`.
All 32 Python assertions executed with ordinary reached/not-reached outcomes:
14 are `reached` and 18 are `not-reached`, with 28/32 matching the expected
polarity. The false negatives are the alias-propagation positive,
array-element positive, and exception-catch positive; the loop-carried negative
is a false positive. No special or error outcomes occurred. Every Python case
uses an isolated cold database, with no database or compiled fixture reused
across the pair.
