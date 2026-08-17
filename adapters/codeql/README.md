# CodeQL adapter

The CodeQL adapter runs language-scoped benchmark kernels against canonical
fixtures. Java and JavaScript have separate selections, query paths, normalized
reports, and retained raw-evidence directories. The JavaScript query may use
CodeQL libraries shared with TypeScript, but this adapter slice selects only
JavaScript cases; TypeScript is a future, separate population.

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
