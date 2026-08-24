# TypeScript propagation kernel

Issue #33 ports the sixteen scored Java propagation templates to TypeScript.
The TypeScript cases keep the Java `template_id` values, source-to-sink
polarity, and negative mechanism. TypeScript shares JavaScript's runtime
semantics, so the fixtures start from the JavaScript kernel and differ from it
by type annotations only. Every scored TypeScript template has exactly one
`positive` and one `negative` `core` case.

| Stratum | Template ID | TypeScript adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct function call, unchanged in meaning; parameter and return types annotated. |
| Local | `dfb-template-local-overwrite-kill` | `let value: string` reassignment, as in the JavaScript kernel. |
| Local | `dfb-template-local-multi-step-chain` | Annotated `const` locals carry the value through the same chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | `number` arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One typed relay is called with tainted and clean values; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | A typed helper returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop typed helper return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two typed helper returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Separate object literals typed as `{ value: string }` stand in for distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One object typed `{ tainted: string; clean: string }` has separate properties. |
| Heap/separation | `dfb-template-alias-propagation-separation` | Assignment of an object reference creates the alias; a second literal remains distinct. |
| Heap/separation | `dfb-template-array-element-separation` | A `string[]` with distinct constant indices stands in for Java array elements. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the positive/negative path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A `for` loop over a `number` either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | An `Error` object carries a property through `throw`/`catch`; the property is declared by a local `interface FlowError extends Error` and read back with a `catch` narrowing cast. |

This matches the `docs/applicability-matrix.md` contract exactly: all sixteen
cells are directly applicable and no cell is language-adapted or `n/a`.

## Surface-syntax deltas from the JavaScript kernel

Every TypeScript fixture is the JavaScript fixture of the same template with
annotations added, line for line, so the anchor `line_hint` values carry over
unchanged. Three deltas are worth stating explicitly, because they are the only
places where the TypeScript text is not purely the JavaScript text plus a type:

1. **Exception catch.** JavaScript attaches an ad-hoc `value` property to a
   plain `Error`. TypeScript requires the property to be declared, so the
   fixture adds `interface FlowError extends Error { value: string; }` after the
   sink declaration and uses `new Error("flow") as FlowError` plus
   `(caught as FlowError).value`. The `catch` binding stays untyped, which is
   TypeScript's `unknown` default. The thrown-object identity, the store, and
   the read are unchanged.
2. **Object-separation initializers.** JavaScript initializes the separation
   holders with `{ value: 0 }` and later stores a string. TypeScript requires a
   single property type, so the holders are declared `{ value: string }` and
   initialized with the same `"clean"` literal the JavaScript negative already
   stores. The separation and the clean/tainted distinction are unchanged.
3. **Loop induction variable.** `for (let iteration: number = 0; ...)` annotates
   the induction variable; the loop body and the kill/compute distinction are
   unchanged.

All TypeScript fixtures use the benchmark-controlled `dfb_source` and
`dfb_sink` function names. The Bifrost adapter may lower those endpoints through
its TypeScript kernel policy, but fixture metadata remains analyzer-neutral and
retains only observed evidence in reports.

## CodeQL selection and reproduction

The CodeQL TypeScript vertical slice is exactly the 32 `taint`/`core` cases
under `cases/taint/typescript/`: the 16 template rows above multiplied by one
positive and one negative assertion. The dedicated query is:

```text
adapters/codeql/typescript/queries/TypeScriptKernel.ql
```

The query is owned by the dedicated TypeScript CodeQL pack manifest at
`adapters/codeql/typescript/qlpack.yml`, which depends on the same
`codeql/javascript-all@2.9.0` as the JavaScript pack: CodeQL extracts
TypeScript with its `javascript` extractor. The two populations are kept
disjoint on three independent levels — the runner selects only cases whose
`language` is `typescript`, each query guards on its fixture's file extension
(`ts` here, `js` in `JavaScriptKernel.ql`), and each kernel writes to its own
report and raw-evidence root. The runner must not select JavaScript cases,
Java or Python cases, calibration cases, or the direct-flow breadth population,
exactly as the JavaScript runner must not select TypeScript cases.

Run it with an already-installed CodeQL CLI:

```bash
cargo run -- run-codeql-typescript-kernel --codeql /path/to/codeql
```

The command creates one cold CodeQL database per case from the declared fixture
files, runs the dedicated query, and cleans temporary database/workspace
artifacts after retaining evidence. It writes the language-specific normalized
report to `reports/codeql-typescript-kernel.json` and raw SARIF/runner
diagnostics to `reports/raw/codeql-typescript/`.

The retained run used CodeQL CLI 2.26.3, build SHA
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, with `codeql/javascript-all@2.9.0`
from the committed lock. Unlike the JavaScript run recorded in
`docs/javascript-kernel.md`, registry retrieval succeeded here:
`codeql pack install` in `adapters/codeql/typescript` resolved the pinned pack
set into `~/.codeql/packages`, so no `--codeql-packs` fallback was needed. That
fallback remains valid when registry retrieval is unavailable:

```bash
cargo run -- run-codeql-typescript-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/matching-source-or-bundle-root
```

### The direct-propagation pair and the v0.2.0 freeze

`dfb-taint-typescript-direct-{positive,negative}` belong both to this kernel
and to the cross-language direct-flow breadth slice, and their bytes were
frozen in `v0.2.0` before this pack existed. `reports/freeze.json` binds their
SHA-256 digests, so they were not rewritten to add a CodeQL query reference or
to change their Bifrost policy. Instead:

- the CodeQL runner defaults a selected TypeScript case with no declared query
  to this kernel's query, and still refuses any case that declares a different
  one;
- the Bifrost runner accepts the language-agnostic
  `adapters/bifrost/policies/core-direct.rqlp` alongside
  `core-typescript-kernel.rqlp`. The two policies differ only by the
  `(language typescript ...)` selector qualifier, which is redundant for a
  single-fixture TypeScript workspace.

The other 30 cases declare
`adapters/bifrost/policies/core-typescript-kernel.rqlp` and the TypeScript
query directly. The JavaScript kernel resolves the same overlap the same way:
its direct pair also keeps `core-direct.rqlp`.

## Anchor evidence and result semantics

CodeQL query results are evidence, not ground truth by themselves. The runner
reconciles SARIF result locations with the case's `DFB-SINK:` anchor; that
marker identifies the anchored sink declaration/function. The SARIF result must
be in the same anchor file at the callsite to that sink identity, but it need
not be on the marker's exact line. Query path evidence identifies the
`DFB-SOURCE:` to sink flow, and normalized results retain both anchor sets. A
successful, anchor-backed finding is `reached`; a successful analysis with no
matching finding is `not-reached`. Missing or incomplete location evidence is
`inconclusive`, while an explicitly unsupported capability is `unsupported` and
a database, query, SARIF, or runner failure is `runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 16 balanced assertions.

## Bifrost slice

`adapters/bifrost/policies/core-typescript-kernel.rqlp` is the JavaScript
kernel policy with a `(language typescript ...)` selector qualifier. Run it
with:

```bash
cargo run -- run-bifrost-typescript-kernel --bifrost /path/to/bifrost
```

The command selects only the 32 TypeScript core assertions, writes
`reports/bifrost-typescript-kernel.json`, and retains each case's raw Bifrost
JSON under `reports/raw/bifrost-typescript-kernel/`. A report with incomplete
runs is normalized as `inconclusive` even when it contains no findings; it is
never interpreted as a negative.

## Observed results

### Bifrost v0.10.2

The retained TypeScript Bifrost snapshot has 32 results: 14 `reached`, 12
`not-reached`, and 6 `inconclusive`, with zero `unsupported` and zero
`runner-error`. Nineteen of 32 assertions match the expected polarity — 19 of
the 26 decisive outcomes. This is case-for-case identical to the JavaScript
kernel's v0.10.2 outcome distribution.

The six `inconclusive` results are the alias-propagation and array-element
pairs, which retain `partial_discovery` evidence, and the exception-catch pair,
which retains `capability_incomplete` evidence. None of them is counted as a
negative.

Of the decisive mismatches, four are false positives — the branch-join,
infeasible-branch, local-overwrite, and loop-carried negatives — and three are
false negatives: the arithmetic-expression, object-separation, and
same-object-field positives.

The run used Bifrost 0.10.2, build identity
`57060b8b062330ab3e9804e1f11e17b290f9447a`, configuration hash
`5b2489c75b433ac15ed6656d43394a17851ee5347a4b24cf00c7dff3531e3b26`.

### CodeQL 2.26.3

TO BE FILLED IN

## Relationship to the other kernels

TypeScript results are a separate population from JavaScript, from every other
language, and from the direct-flow breadth slice. Cross-language macro-averages
are computed per language population and are never pooled without stating the
population.

The Java kernel's two calibration cases are intentionally outside this
sixteen-template scored slice and are not ported here.
`dfb-template-one-hop-relay` is a simpler helper-flow calibration already
covered by the scored return-relay template, and
`dfb-template-modeled-external-summary` requires an explicitly activated
external semantic-model catalog that the standalone CLI cannot activate.
