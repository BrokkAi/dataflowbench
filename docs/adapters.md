# Adapter contract

An adapter executes a real supported tool surface, captures its raw output,
and normalizes only the states in `schemas/result.schema.json`: `reached`,
`not-reached`, `inconclusive`, `unsupported`, and `runner-error`.

Canonical cases never contain native rule syntax. Each adapter owns its rules,
models, command line, version discovery, configuration hash, capability notes,
and raw-evidence retention under `adapters/<tool>/` or the adapter's dedicated
report directory.

The initial adapter plan is:

| Tool | Initial profile | Status |
| --- | --- | --- |
| Bifrost | Breadth baseline and Java, JavaScript, and Python propagation kernels | Implemented smoke adapter; kernel runs are reported separately |
| CodeQL | 16-template Java and JavaScript propagation kernels | Java and JavaScript runners implemented as separate language-scoped populations |
| Semgrep CE | Supported local analysis only | Planned |
| OpenTaint | Java and Kotlin profile | Planned |

No adapter may synthesize a tool result. If a supported case cannot complete,
emit `inconclusive` or `runner-error` with the raw evidence. If it is outside
a documented tool profile, emit `unsupported`; it is excluded from
false-negative interpretation. An incomplete or failed run must never become
`not-reached` merely because the SARIF result list is empty.

## CodeQL language populations

The CodeQL adapter keeps Java and JavaScript as separate populations. The
JavaScript command selects exactly 32 `taint` cases:

```text
language == "javascript"
track == "taint"
score_tier == "core"
tool_model_references.codeql.query ==
  "adapters/codeql/javascript/queries/JavaScriptKernel.ql"
```

The selection is balanced: one positive and one negative case for each of 16
shared template IDs. It does not select TypeScript cases, even where CodeQL
uses shared JavaScript/TypeScript libraries. JavaScript has its own query,
pack manifest (`adapters/codeql/javascript/qlpack.yml`),
normalized report (`reports/codeql-javascript-kernel.json`), and raw SARIF
directory (`reports/raw/codeql-javascript/`). Java uses its existing query,
report, and evidence directory independently.

For each JavaScript case, the runner materializes the declared fixture files in
an isolated workspace, creates a fresh CodeQL database with the JavaScript
extractor, runs `JavaScriptKernel.ql`, and removes temporary database/workspace
artifacts after retaining the raw output. The normalized report records the
exact CodeQL CLI version/build and configuration hash observed by that run. The
retained snapshot used CodeQL CLI 2.26.3, build SHA
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, with official `github/codeql` tag
`codeql-cli/v2.26.3` at source commit
`44a68d3a47fcbcd6a6a76ec7d1c1b3a1a28b201e`. Its JavaScript pack is
`codeql/javascript-all@2.9.0` with the committed lock. Registry retrieval of
that 2.9.0 pack was unavailable in the test environment, so reproduction used
the matching official source workspace root via `--codeql-packs` (or an
equivalent matching bundle pack root):

```bash
CODEQL=/path/to/codeql-v2.26.3/codeql
CODEQL_SOURCE_ROOT=/private/tmp/codeql-source-v2.26.3
cargo run -- run-codeql-javascript-kernel \
  --codeql "$CODEQL" \
  --codeql-packs "$CODEQL_SOURCE_ROOT"
```

SARIF findings are mapped back to the benchmark's sink anchors, while the
query path evidence identifies the source-to-sink flow and normalized results
retain both anchor sets. A `DFB-SINK:` marker identifies the anchored sink
declaration/function. The SARIF result must be in the same anchor file at the
callsite to that sink identity; it need not be on the marker's exact line.
Only anchor-backed evidence contributes to `reached`; successful execution
with no matching finding contributes to `not-reached`. Unresolved or
incomplete evidence remains `inconclusive`, capability exclusions remain
`unsupported`, and database/query/parse failures remain `runner-error`. All
raw SARIF and runner diagnostics remain available for audit.

The retained JavaScript snapshot has 32 results: 15 `reached`, 17
`not-reached`, and zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. Twenty-nine of 32 match expected polarity. The false negatives are
`dfb-taint-javascript-alias-propagation-positive` and
`dfb-taint-javascript-expression-positive`; the false positive is
`dfb-taint-javascript-loop-carried-negative`. It retains 32 SARIF files, zero
error files, and empty normalized `witness_checkpoints` for every case. The
configuration hash is
`a038e39eb93d6fc674ab59cf2e4de5b3608f1d7b294c19da75ce1bd041c75ac5`.

The direct-flow breadth run, Java kernel run, JavaScript kernel evidence, and
Python kernel run are distinct adapter populations. A kernel command must
select only its language and retain the exact raw output for those cases; it
must not use a direct-flow result or a Java result as a proxy for JavaScript.
The Python kernel's 16-template balance and construct adaptations are defined
in the [Python kernel contract](python-kernel.md).

The checked-in Bifrost snapshot (`reports/bifrost-smoke.json`) contains 88
normalized results from Bifrost 0.9.5 build
`0b0c5c0e2d84eb7fc75baa486f6111623b13507c`: 39 `reached`, 42 `not-reached`, 6
`inconclusive`, and 1 `unsupported`. The JavaScript profile contributes 32
balanced assertions using the Java template IDs and the
`adapters/bifrost/policies/core-javascript-kernel.rqlp` policy. Its current
outcomes are 12 `reached`, 16 `not-reached`, and 4 `inconclusive`; 22 complete
outcomes match the expected polarity and 6 complete outcomes do not. The four
incomplete runs remain `inconclusive`, never synthesized as `not-reached` or
counted as false negatives. See the [Bifrost adapter notes](../adapters/bifrost/README.md)
for raw-report separation and the per-template mismatch breakdown.
