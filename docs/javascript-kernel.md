# JavaScript propagation kernel

Issue #11 ports the sixteen scored Java propagation templates to JavaScript.
The JavaScript cases keep the Java `template_id` values, source-to-sink
polarity, and negative mechanism; only the smallest fixture construct is
adapted to JavaScript syntax. Every scored JavaScript template has exactly one
`positive` and one `negative` `core` case.

| Stratum | Template ID | JavaScript adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | `let` reassignment replaces the Java local assignment. |
| Local | `dfb-template-local-multi-step-chain` | `const` locals carry the value through the same chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | JavaScript number arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One relay is called with tainted and clean values; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | A helper returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop helper return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two JavaScript helper returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Separate object literals stand in for distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One object has separate `tainted` and `clean` properties. |
| Heap/separation | `dfb-template-alias-propagation-separation` | Assignment of an object reference creates the alias; a second literal remains distinct. |
| Heap/separation | `dfb-template-array-element-separation` | Distinct array indices stand in for Java array elements. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the positive/negative path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A loop either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | A JavaScript `Error` object carries a property through `throw`/`catch`; this replaces Java's checked exception class. |

All JavaScript fixtures use the benchmark-controlled `dfb_source` and
`dfb_sink` function names. The Bifrost adapter may lower those endpoints through
its JavaScript kernel policy, but fixture metadata remains analyzer-neutral and
retains only observed evidence in reports.

## CodeQL selection and reproduction

The CodeQL JavaScript vertical slice is exactly the 32 `taint`/`core` cases
under `cases/taint/javascript/`: the 16 template rows above multiplied by one
positive and one negative assertion. Every selected manifest points to the
dedicated query:

```text
adapters/codeql/javascript/queries/JavaScriptKernel.ql
```

The query is owned by the dedicated JavaScript CodeQL pack manifest at
`adapters/codeql/javascript/qlpack.yml`, even though CodeQL's standard library
can cover both JavaScript and TypeScript syntax.

The runner must not select TypeScript cases, calibration cases, Java cases, or
the direct-flow breadth population. Run it with an already-installed CodeQL
CLI and local pack directory:

```bash
cargo run -- run-codeql-javascript-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The command creates one cold JavaScript CodeQL database per case from the
declared fixture files, runs the dedicated query, and cleans temporary
database/workspace artifacts after retaining evidence. It writes the
language-specific normalized report to
`reports/codeql-javascript-kernel.json` and raw SARIF/runner diagnostics to
`reports/raw/codeql-javascript/`. The retained run used CodeQL CLI 2.26.3,
build SHA `7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, with official
`github/codeql` tag `codeql-cli/v2.26.3` at source commit
`44a68d3a47fcbcd6a6a76ec7d1c1b3a1a28b201e`, and
`codeql/javascript-all@2.9.0` from the committed lock. Registry retrieval of
the 2.9.0 pack was unavailable in the test environment, so the tested command
used the matching official source workspace root via `--codeql-packs` (or an
equivalent matching bundle pack root):

```bash
CODEQL=/path/to/codeql-v2.26.3/codeql
CODEQL_SOURCE_ROOT=/private/tmp/codeql-source-v2.26.3
cargo run -- run-codeql-javascript-kernel \
  --codeql "$CODEQL" \
  --codeql-packs "$CODEQL_SOURCE_ROOT"
```

The normalized report records the exact CLI version/build and configuration
hash discovered during the run. A matching official source workspace or
bundle is a valid reproduction input when registry retrieval is unavailable.

## Anchor evidence and result semantics

CodeQL query results are evidence, not ground truth by themselves. The runner
reconciles SARIF result locations with the case's `DFB-SINK:` anchor; that
marker identifies the anchored sink declaration/function. The SARIF result
must be in the same anchor file at the callsite to that sink identity, but it
need not be on the marker's exact line. Query path evidence identifies the
`DFB-SOURCE:` to sink flow, and normalized results retain both anchor sets. A
successful, anchor-backed finding is `reached`; a successful analysis with no
matching finding is `not-reached`. Missing or incomplete location evidence is
`inconclusive`, while an explicitly unsupported capability is `unsupported`
and a database, query, SARIF, or runner failure is `runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 16 balanced assertions.

The retained JavaScript snapshot has 32 results: 15 `reached` and 17
`not-reached`, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. Twenty-nine of 32 match expected polarity. The false negatives are
`dfb-taint-javascript-alias-propagation-positive` and
`dfb-taint-javascript-expression-positive`; the false positive is
`dfb-taint-javascript-loop-carried-negative`. All 32 retained raw outputs are
SARIF files with zero error files, and normalized `witness_checkpoints` are
empty for every case. The configuration hash is
`a038e39eb93d6fc674ab59cf2e4de5b3608f1d7b294c19da75ce1bd041c75ac5`.

The Java kernel also has two calibration cases that are intentionally outside
this sixteen-template scored slice. `dfb-template-one-hop-relay` is a simpler
helper-flow calibration covered by the scored return-relay template, and
`dfb-template-modeled-external-summary` requires an explicitly activated
external semantic-model catalog. The standalone CLI cannot activate that
catalog, so it must remain `unsupported` rather than being translated into a
negative JavaScript result.
