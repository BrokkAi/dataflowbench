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
| CodeQL | 16-template Java, JavaScript, and Python propagation kernels | Java, JavaScript, and Python runners implemented as separate language-scoped populations |
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

### CodeQL Python slice

The Python CodeQL command selects exactly the 32 `core` taint cases in
`cases/taint/python/`: one positive and one negative assertion for each of the
16 balanced template IDs. Each case's `tool_model_references.codeql.query`
must point to `adapters/codeql/python/queries/PythonKernel.ql`; Java cases and the
13-language direct-flow baseline are excluded. The command creates a fresh
Python database per case and writes `reports/codeql-python-kernel.json` plus
one retained raw SARIF or runner-error artifact per selected case under
`reports/raw/codeql-python-kernel/`.

The Java and Python query packs are separate: Java uses the pack rooted at
`adapters/codeql/`, while Python uses `adapters/codeql/python/`, including its
language-specific database-schema dependency. Installing or resolving one
pack must not silently substitute the other language's pack.

Reproduce it with CodeQL CLI v2.26.3 and the pinned Python pack
`codeql/python-all@7.2.3`:

```bash
codeql pack install adapters/codeql/python --search-path /path/to/codeql-packs
codeql pack ls adapters/codeql/python --search-path /path/to/codeql-packs
cargo run -- run-codeql-python-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The normalized result copies the case's source and sink anchors and uses the
SARIF finding/diagnostic evidence to classify the anchored assertion. The
adapter retains `reached`, `not-reached`, `inconclusive`, `unsupported`, and
`runner-error` distinctly: incomplete or failed analysis is never a negative
result, and raw SARIF is retained even when normalization cannot complete.
The validated Python run used CodeQL CLI 2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/python-all@7.2.3`. Its 32 results are 14 `reached` and 18
`not-reached`, with no `inconclusive`, `unsupported`, or `runner-error`
outcomes; 28/32 match the expected polarity. The mismatches are false
negatives for `alias-propagation-positive`, `array-element-positive`, and
`exception-catch-positive`, and a false positive for `loop-carried-negative`.
These results cover only the Python core kernel.

The checked-in Bifrost snapshot (`reports/bifrost-smoke.json`) contains 118
normalized results from Bifrost v0.10.2 build identity
`c2116609f5fc1be318c8fb76fb83763cf326bab6`: 50 `reached`, 37 `not-reached`, 30
`inconclusive`, and 1 `unsupported`. The pinned binary has SHA-256
`93b55dd20c283c278f586e8c8e6ad6bf0e9f5f08165b56096e110af0450d0873`.
The Java, Python, and JavaScript 32-assertion profiles have respectively
17/32 assertions matching expected polarity (17 of 22 decisive outcomes),
16/32 (16 of 20 decisive outcomes), and 19/32 (19 of 26 decisive outcomes);
incomplete runs remain `inconclusive`, never synthesized as `not-reached` or
counted as false negatives. The v0.10.2 outcomes match v0.10.1 case-for-case,
but do not restore the complete Java correctness observed in v0.9.5. See the
[Bifrost adapter notes](../adapters/bifrost/README.md) for raw-report
separation and the per-template mismatch breakdown.
