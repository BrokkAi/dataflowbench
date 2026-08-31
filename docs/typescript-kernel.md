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

## Challenge-tier expansion

[The challenge tier](challenge-tier.md) preregistered thirteen further
propagation templates before any fixture existed. All thirteen are classified
**directly applicable** to TypeScript, so the TypeScript core denominator grows
from 16 templates / 32 assertions to **29 templates / 58 assertions**. The
challenge cases carry `score_tier: "core"` — there is no separate tier — and
their fixture provenance revision is `m3-challenge-typescript`.

The v0.3.0 sixteen-template core and this expanded core are different
populations and are never compared number to number.

As with the classic sixteen, the TypeScript challenge fixtures are the
JavaScript challenge fixtures plus type annotations. The runtime shape — which
value flows where, which key is read, which callee is selected — is byte-for-byte
the same decision in both languages, and TypeScript remains a separate result
population that is never mixed with JavaScript's.

### Adaptation notes

Every cell is direct. The realizations, recorded so a reader can check the
fixture against the template rather than against a guess:

| Stratum | Template ID | TypeScript realization |
| --- | --- | --- |
| A | `dfb-template-chal-reflective-invocation` | `handlers[name](dfb_source())` with `name` a `string`-typed local, so the selected method is never a syntactic literal at the call site. `handlers` is annotated `Record<string, (value: string) => void>`. The negative points `name` at the sibling method that drops its argument. |
| A | `dfb-template-chal-computed-property` | `holder[key] = dfb_source()` written and read back through the same local key variable, with `key: keyof Holder` over a declared `interface Holder { payload: string; other: string }`. The negative writes under one constant key and reads a provably distinct one. |
| A | `dfb-template-chal-dispatch-table` | An object literal of two arrow functions annotated `Record<string, Handler>` for `type Handler = (value: string) => void`; the entry is fetched as a first-class value (`const selected: Handler = table[key]`) and then invoked, which is what separates it from the reflective method call above. |
| B | `dfb-template-chal-closure-capture` | A factory typed `(): () => void` captures the tainted local and returns `(): void => { dfb_sink(captured); }`, invoked by the caller after the local has left scope. The negative captures the clean local; the source call stays in place. |
| B | `dfb-template-chal-function-field` | Two `Holder` objects each carry a function-valued `fn` property declared `(value: string) => void`; a separate `invoke(target: Holder, value: string)` reads the field and calls it. The negative hands `invoke` the second holder. |
| B | `dfb-template-chal-callback-registration` | An object typed `interface Registry { hooks: Hook[] }`, a `register` function, and a `fire` driver that iterates and invokes. No framework, twenty lines of language. |
| B | `dfb-template-chal-anonymous-implementation` | Two inline anonymous function expressions assigned to variables of the **declared call-signature interface** `Handler { (value: string): void }` and invoked through the reference; neither captures anything, which is what keeps it distinct from closure capture. TypeScript is where the template's "invoked through the declared interface type" wording is literally true — the JavaScript fixture can only imply the declared type. |
| C | `dfb-template-chal-map-iteration` | `for (const [key, value] of Object.entries(carrier))` over a `Record<string, string>`, never a keyed get. The negative iterates a second, disjoint object. |
| C | `dfb-template-chal-nested-access-path` | `a.b.c.value` written and read at depth 3 through three declared interfaces (`Level1`/`Level2`/`Level3`); the negative reads the sibling `a.b.c.other`. |
| C | `dfb-template-chal-element-object` | An `Item[]` of object literals; the negative reads `items[1].value` after `items[0].value` was written. |
| D | `dfb-template-chal-deep-relay-chain` | `relay1` … `relay6`, module-level, `(value: string): void` throughout, no branching or state, with the sink inside `relay6`. The negative feeds the identical chain a clean constant. |
| D | `dfb-template-chal-recursive-carry` | `carry(value: string, depth: number): string` recursing to `depth === 0` from 5; the negative's base case returns a clean constant instead of the carried one. |
| D | `dfb-template-chal-context-pair-depth2` | One `helper` reached through two distinct two-deep paths, `outerTainted -> wrapper -> helper` and `outerClean -> wrapper -> helper`, per [Amendment A1](challenge-tier.md#amendments): `helper` returns its argument and the caller sinks the selected result. Both paths are live in both fixtures; only which returned value reaches `dfb_sink` differs. |

### Typing choices that matter analytically

Three annotations are load-bearing rather than cosmetic, in the sense that a
different-but-also-valid annotation would have changed what the fixture asks:

1. **Index signatures on the two stratum-A dynamic holders.** `handlers` and
   `table` are annotated `Record<string, …>` because the templates require the
   selecting key to be a run-time `string`, not a literal. A narrower
   `{ leak: …; drop: … }` annotation would have made TypeScript resolve the
   member statically and quietly converted a dynamic-dispatch question into a
   static one. The `Record` widening is what preserves the template's intent,
   and it is the same choice the preregistration anticipates for TypeScript.
2. **`keyof Holder` for the computed-property keys.** The alternative,
   `Record<string, string>`, would have erased the two declared sibling fields
   and made the negative's field separation invisible in the type. Declaring
   `interface Holder { payload: string; other: string }` and typing the key
   `keyof Holder` keeps both declared fields and still leaves the access site a
   variable-keyed one, which is the property under test.
3. **No-op function initializers instead of `null` in `function-field`.** The
   JavaScript fixture initializes `{ fn: null }` and assigns the real function
   afterwards. Under `strictNullChecks` that field would have to be typed
   `… | null` and the `target.fn(value)` call site would need a narrowing that
   the template does not ask about. The holders are therefore initialized with
   an empty `(value: string): void => {}` of the field's own type, and the
   witness-marked assignment that stores the sinking function is unchanged. The
   store, the fetch, and the object separation are all exactly as in
   JavaScript.

Everywhere else the annotation is the obvious one and adds nothing to the
question. `any` was not needed anywhere: the two index signatures carry every
dynamic stratum this kernel has.

All twenty-six fixtures are standard-library-only — no dependency, no
framework, no build tooling — and the whole 58-fixture TypeScript population
type-checks clean, one file at a time, under the host toolchain this kernel
records:

```bash
npx -p typescript@5.9 tsc --noEmit --strict --target es2020 --lib es2020 <fixture>.ts
```

(One file at a time because every fixture declares `dfb_source` and `dfb_sink`
at script scope; compiling them into one program would collide on those names
rather than find a defect.)

### Adapter coverage of the expanded population

One adapter was re-run over the whole 58-assertion population for this
expansion. Two are deferred by the freeze rule, and one does not cover
TypeScript at all. None of the three is a gap in what this kernel measures, and
the difference between them matters:

| Adapter | Expanded run | Report |
| --- | --- | --- |
| Semgrep CE 1.174.0 | Yes | `reports/semgrep-typescript-kernel.json` |
| Bifrost v0.10.5 | **Deferred (freeze-bound)** | `reports/bifrost-typescript-kernel.json` |
| CodeQL 2.26.4 | **Deferred (freeze-bound)** | `reports/codeql-typescript-kernel.json` |
| Joern 4.0.614 | **No TypeScript slice exists** | — |

**Both Bifrost and CodeQL are deferred, and both for the same reason.**
`reports/bifrost-typescript-kernel.json` and
`reports/codeql-typescript-kernel.json` are two of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0, so this change must not overwrite
either: **expanded Bifrost and CodeQL evidence for TypeScript is pending the
v0.4.0 freeze-prep re-run**, on the repository's established
re-run-at-freeze pattern. The retained reports below remain the valid
32-assertion classic snapshots, and they describe a *different population* from
the expanded one. Deferral is not absence of coverage: both engines cover
TypeScript, both will attempt all 58 assertions at v0.4.0, and this wave simply
had no freeze-legal file to write them to. TypeScript is the only wave language
so far whose *entire* Bifrost and CodeQL evidence is deferred at once — the
JavaScript and Python waves each had at least one non-freeze-bound report to
write.

**Joern has no TypeScript slice, and this wave did not invent one.** The pinned
`joern-v4.0.614` adapter covers Java, JavaScript, Python, Ruby, PHP, and Rust;
`adapters/joern/README.md` already records TypeScript as "Available, not yet in
scope" — its `jssrc2cpg` frontend can parse `.ts`, but no
`run-joern-typescript-kernel` command, query selection, or report exists, and
standing one up is a new adapter slice rather than part of a fixture wave.
Adding one here would have made the wave's own change the object of study.

### Semgrep CE 1.174.0 — expanded core

`reports/semgrep-typescript-kernel.json`. The whole 58-case population is
selected and balance-checked, and the bounded profile then decides what is
scored, from case metadata, before Semgrep is invoked.

| Stratum | Assertions | Scored | `unsupported` | Polarity match (scored) |
| --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 14 | 18 | 12/14 |
| Challenge (13 templates) | 26 | 0 | 26 | n/a |

Whole-population outcome distribution: 9 `reached`, 5 `not-reached`, 44
`unsupported`, zero `inconclusive`, zero `runner-error`.

**All twenty-six challenge assertions take the preregistered `unsupported`
partition**, exactly as [the challenge tier](challenge-tier.md) predicted: no
challenge template carries the `intraprocedural` feature tag, so none is inside
the documented CE local-taint profile, and each retains its own
`*-unsupported.json` capability-decision document naming the declared capability
and the boundary it falls outside, citing the preregistered per-template
rationale rather than the generic tag rule. The scored subset therefore stays at
**14 assertions and 12/14**, unchanged from the classic run — the two mismatches
are still the `infeasible-branch` and `loop-carried` negatives, the path
sensitivity the pinned CLI sells as Pro. Comparing the retained report before
and after this expansion, **not one of the 32 classic outcomes moved**. The
partition was not adjusted for this expansion, and twenty-six declined
assertions are coverage, never twenty-six false negatives.

The expanded report carries fixture revision
`sha256:2c906faeb98b48d1aba7da7bc80a78c4084051b84efac6ac3a1b74f54c843fd2`,
configuration hash
`865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100`, tool build
identity `semgrep-oss:1.174.0`. Reports at different fixture revisions are not
pooled.

### What this wave does and does not establish

Honestly stated, because the deferral makes it easy to overclaim: this wave
establishes that the TypeScript challenge fixtures exist, type-check, and are
selected and balance-checked by the population machinery, and it establishes
one adapter's expanded-population behavior — Semgrep CE's, which is a declared
capability boundary rather than an analysis result. It establishes **nothing**
about how well any engine follows TypeScript taint through reflection,
higher-order code, containers, or depth. That evidence arrives with the v0.4.0
re-run of the two deferred adapters, and until then TypeScript's challenge
strata have no analysis outcomes at all.

## CodeQL selection and reproduction

The CodeQL TypeScript vertical slice is the whole TypeScript `taint`/`core`
population under `cases/taint/typescript/` — 32 assertions classically, and
**58** now that the thirteen challenge templates have rolled out: 29 template
rows multiplied by one positive and one negative assertion. The retained
snapshot below is the classic 32, because the expanded run is deferred to
v0.4.0 by the freeze rule. The dedicated query is:

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

The command selects the whole TypeScript core population — 32 assertions
classically, 58 with the challenge templates rolled out — writes
`reports/bifrost-typescript-kernel.json`, and retains each case's raw Bifrost
JSON under `reports/raw/bifrost-typescript-kernel/`. A report with incomplete
runs is normalized as `inconclusive` even when it contains no findings; it is
never interpreted as a negative.

**This command was deliberately not run for the challenge expansion.**
`reports/bifrost-typescript-kernel.json` is freeze-bound by v0.3.0, so running
it now would overwrite frozen evidence; the expanded run is deferred to the
v0.4.0 freeze-prep re-run, as recorded above.

## Observed results

Both retained snapshots below are the **classic 32-assertion population**.
Neither includes the twenty-six challenge assertions, whose Bifrost and CodeQL
evidence is deferred to the v0.4.0 re-run for the freeze reason recorded in the
[challenge-tier expansion](#challenge-tier-expansion) section. They are not
expanded-core numbers and must not be read as any.

### Bifrost v0.10.5

The retained TypeScript Bifrost snapshot has 32 results: 15 `reached`, 15
`not-reached`, and 2 `inconclusive`, with zero `unsupported` and zero
`runner-error`. Thirty of 32 assertions match the expected polarity — all 30
of the decisive outcomes. There are no decisive mismatches.

The two `inconclusive` results are the exception-catch pair, which retains
`capability_incomplete` evidence. Neither is counted as a negative.

This improves on the earlier v0.10.2 run (14 `reached`, 12 `not-reached`, 6
`inconclusive`, 19/32 matching): the alias-propagation and array-element pairs
became decisive and correct, and all seven earlier decisive mismatches are
resolved. The frozen v0.2.0 JavaScript kernel evidence remains a v0.10.2
snapshot, so the two kernels are no longer directly comparable until the next
freeze re-runs every Bifrost slice on one version.

The run used Bifrost 0.10.5, build identity
`728ac69ab93224151c6c951b23d2f5bc681d8558`, configuration hash
`5b2489c75b433ac15ed6656d43394a17851ee5347a4b24cf00c7dff3531e3b26`.

### CodeQL 2.26.3

The retained TypeScript snapshot has 32 results: 15 `reached` and 17
`not-reached`, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. Twenty-nine of 32 match expected polarity. The false negatives are
`dfb-taint-typescript-alias-propagation-positive` and
`dfb-taint-typescript-expression-positive`; the false positive is
`dfb-taint-typescript-loop-carried-negative`. This is case-for-case identical
to the retained JavaScript snapshot, which is the expected result for a kernel
that differs from it by type annotations only.

All 32 retained raw outputs are SARIF files under
`reports/raw/codeql-typescript/`, with zero error files, and normalized
`witness_checkpoints` are empty for every case — the adapter records
anchor-backed flow outcomes and retains path evidence in SARIF rather than
fabricating normalized witness markers. The configuration hash is
`97949db804086b91f4737ad2e6a8ac5dab461f811a7a033250a00ced32eac54c`.

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
