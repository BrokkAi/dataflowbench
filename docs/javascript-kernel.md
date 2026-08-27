# JavaScript propagation kernel

Issue #11 ports the sixteen scored Java propagation templates to JavaScript.
The JavaScript cases keep the Java `template_id` values, source-to-sink
polarity, and negative mechanism; only the smallest fixture construct is
adapted to JavaScript syntax. Every scored JavaScript template has exactly one
`positive` and one `negative` `core` case.

The kernel has since been expanded by the thirteen preregistered challenge
templates, all of them directly applicable to JavaScript: the **JavaScript core
denominator is 29 templates / 58 assertions**. See
[the challenge-tier expansion](#challenge-tier-expansion) below for the
adaptations, the per-adapter results, and the one adapter whose expanded
evidence is deferred.

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

JavaScript additionally carries a **taint-modeling** population, on its own tier
and with its own scorecards: twelve templates and twenty-four assertions that
test whether an engine can be *told* things rather than whether it can follow
flow it can see. It is never pooled with the core denominator above, and a score
there is not a propagation score. See
[the JavaScript taint-modeling matrix](javascript-modeling.md).

A third JavaScript population, on the same `modeling` tier but a disjoint
`model_profile`, asks what each tool ships rather than what it can be told: six
templates and twelve assertions over real Node and ECMAScript APIs. See
[the JavaScript tool-native probe set](javascript-native.md). It is pooled with
neither of the two above.

All JavaScript fixtures use the benchmark-controlled `dfb_source` and
`dfb_sink` function names. The Bifrost adapter may lower those endpoints through
its JavaScript kernel policy, but fixture metadata remains analyzer-neutral and
retains only observed evidence in reports.

## Challenge-tier expansion

[The challenge tier](challenge-tier.md) preregistered thirteen further
propagation templates before any fixture existed. All thirteen are classified
**directly applicable** to JavaScript, so the JavaScript core denominator grows
from 16 templates / 32 assertions to **29 templates / 58 assertions**. The
challenge cases carry `score_tier: "core"` — there is no separate tier — and
their fixture provenance revision is `m3-challenge-javascript`.

The v0.3.0 sixteen-template core and this expanded core are different
populations and are never compared number to number.

### Adaptation notes

Every cell is direct: JavaScript is the language the preregistration's stratum
A and B sketches were written for. The realizations, recorded so a reader can
check the fixture against the template rather than against a guess:

| Stratum | Template ID | JavaScript realization |
| --- | --- | --- |
| A | `dfb-template-chal-reflective-invocation` | `handlers[name](dfb_source())` with `name` a string constant in a local, so the selected method is never a syntactic literal at the call site. The negative points `name` at the sibling method that drops its argument. |
| A | `dfb-template-chal-computed-property` | `holder[key] = dfb_source()` written and read back through the same local key variable. The negative writes under one constant key and reads a provably distinct one. |
| A | `dfb-template-chal-dispatch-table` | An object literal of two arrow functions; the entry is fetched as a first-class value (`const selected = table[key]`) and then invoked, which is what separates it from the reflective method call above. |
| B | `dfb-template-chal-closure-capture` | A factory captures the tainted local and returns `() => dfb_sink(captured)`, invoked by the caller after the local has left scope. The negative captures the clean local; the source call stays in place. |
| B | `dfb-template-chal-function-field` | Two holder objects each carry a function-valued `fn` property; a separate `invoke(target, value)` reads the field and calls it. The negative hands `invoke` the second holder. |
| B | `dfb-template-chal-callback-registration` | A plain object with a `hooks` array, a `register` function, and a `fire` driver that iterates and invokes. No framework, twenty lines of language. |
| B | `dfb-template-chal-anonymous-implementation` | Two inline anonymous function expressions assigned to variables and invoked through the reference; neither captures anything, which is what keeps it distinct from closure capture. |
| C | `dfb-template-chal-map-iteration` | `for (const [key, value] of Object.entries(carrier))`, never a keyed get. The negative iterates a second, disjoint object. |
| C | `dfb-template-chal-nested-access-path` | `a.b.c.value` written and read at depth 3; the negative reads the sibling `a.b.c.other`. |
| C | `dfb-template-chal-element-object` | An array of object literals; the negative reads `items[1].value` after `items[0].value` was written. |
| D | `dfb-template-chal-deep-relay-chain` | `relay1` … `relay6`, module-level, no branching or state, with the sink inside `relay6`. The negative feeds the identical chain a clean constant. |
| D | `dfb-template-chal-recursive-carry` | `carry(value, depth)` recursing to `depth === 0` from 5; the negative's base case returns a clean constant instead of the carried one. |
| D | `dfb-template-chal-context-pair-depth2` | One `helper` reached through two distinct two-deep paths, `outerTainted -> wrapper -> helper` and `outerClean -> wrapper -> helper`. Both paths are live in both fixtures and the value returns to the sink, which is the two-level extension of the classic `dfb-template-call-context-separation` fixture's own shape; only which returned value reaches `dfb_sink` differs. |

All twenty-six fixtures are standard-library-only — no dependency, no
framework, no build tooling — and each parses clean under the host toolchain
this kernel records, `node --check`.

### Adapter coverage of the expanded population

Three adapters were re-run over the whole 58-assertion population for this
expansion; one is deferred, and the deferral is a freeze rule rather than a
gap in coverage.

| Adapter | Expanded run | Report |
| --- | --- | --- |
| Bifrost v0.10.5 | Yes — first run of the dedicated JavaScript kernel | `reports/bifrost-javascript-kernel.json` |
| Joern 4.0.610 | Yes | `reports/joern-javascript-kernel.json` |
| Semgrep CE 1.174.0 | Yes | `reports/semgrep-javascript-kernel.json` |
| CodeQL 2.26.3 | **Deferred** | `reports/codeql-javascript-kernel.json` |

`reports/codeql-javascript-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0, so this change must not
overwrite it: **expanded CodeQL evidence is pending the v0.4.0 freeze-prep
re-run**, on the repo's established re-run-at-freeze pattern. The retained
CodeQL JavaScript evidence remains the valid 32-assertion classic snapshot
described below. The same rule applies in reverse to the Bifrost smoke report:
its JavaScript slice stays the classic pairs at 118 cases, and the challenge
assertions are carried by the new dedicated kernel report instead.

Because the corpus-wide `fixture_revision` covers every case and fixture byte,
the three expanded JavaScript reports carry revisions no earlier retained
report carries: the Bifrost and Joern reports
`sha256:64ef139f452fd296bb26463bc552e5e5998ca4bb4584d45565d858424814bde9`, and
the Semgrep CE report
`sha256:61c06a78b95b86764d3c220cfefd7af37373db64b15ae0b76c6ebf924217ab2e`,
because it was re-run once more after the Python challenge wave merged so that
its capability rationales cite the preregistered per-template partition rather
than the generic tag rule. Reports at different fixture revisions are not
pooled; the JavaScript outcomes are identical across the two Semgrep runs,
which differ only in those reason clauses.

### Bifrost v0.10.5 — expanded core

`reports/bifrost-javascript-kernel.json`, the first run of the dedicated
`run-bifrost-javascript-kernel` command, covers all 58 assertions under
`adapters/bifrost/policies/core-javascript-kernel.rqlp` (the frozen
direct-propagation pair still names the cross-language breadth policy, as in
every other language kernel).

| Stratum | Assertions | Polarity match | Outcome distribution |
| --- | --- | --- | --- |
| Classic (16 templates) | 32 | 32/32 | 16 `reached`, 16 `not-reached` |
| Challenge (13 templates) | 26 | 3/26 | 1 `reached`, 2 `not-reached`, 21 `inconclusive`, 2 `runner-error` |

The classic half reproduces the frozen smoke evidence exactly. On the challenge
half the engine decided only two of the thirteen pairs, and **every decision it
made was correct**: `context-pair-depth2` both ways, and the
`deep-relay-chain` negative. There is not one false positive or false negative
in the stratum. The remaining twenty-one assertions are `inconclusive` with
retained `partial_discovery` evidence — "taint discovery is incomplete:
procedure value-flow snapshot for … is unknown" — across
`reflective-invocation`, `computed-property`, `dispatch-table`,
`closure-capture`, `function-field`, `callback-registration`,
`anonymous-implementation`, `map-iteration`, `nested-access-path`,
`recursive-carry` (both polarities each) and the `deep-relay-chain` positive.
The `element-object` pair is `runner-error`: the engine reports
`internal_invariant` with "invalid value-flow snapshot: oracle relation does
not belong to the required query arena and role" on an array of object
literals. None of these is a negative result, and none is counted as one.

Read together with the classic half, the honest reading is that this build
decides local, field-at-depth-1, and short-relay JavaScript completely, and
declines rather than guesses on higher-order code, computed access, container
iteration, deep access paths, and recursion.

### Joern 4.0.610 — expanded core

`reports/joern-javascript-kernel.json`, `jssrc2cpg`, the same unmodified
`adapters/joern/queries/kernel.sc` every other Joern kernel uses, at the
distribution's **default** `maxCallDepth` of 4. Nothing was configured up.

| Stratum | Assertions | Polarity match | Outcome distribution |
| --- | --- | --- | --- |
| Classic (16 templates) | 32 | 26/32 | 18 `reached`, 14 `not-reached` |
| Challenge (13 templates) | 26 | 18/26 | 9 `reached`, 17 `not-reached` |

Every one of the 58 assertions executed: zero `inconclusive`, zero
`unsupported`, zero `runner-error`. The classic half reproduces the retained
v0.3.0 Joern snapshot case for case, mismatch for mismatch, so the expansion
introduced no drift in the population it shares.

Challenge mismatches, verbatim:

- `dfb-taint-javascript-reflective-invocation-positive`: false negative.
- `dfb-taint-javascript-dispatch-table-positive`: false negative.
- `dfb-taint-javascript-function-field-positive`: false negative.
- `dfb-taint-javascript-callback-registration-positive`: false negative.
- `dfb-taint-javascript-map-iteration-positive`: false negative.
- `dfb-taint-javascript-deep-relay-chain-positive`: false negative.
- `dfb-taint-javascript-computed-property-negative`: false positive.
- `dfb-taint-javascript-nested-access-path-negative`: false positive.

Three readings, stated as evidence rather than as a ranking:

- **Stratum D confirms the preregistered prediction.** The depth-6 relay
  positive is missed while its negative is correct, and `context-pair-depth2`
  — two deep — is correct both ways. The pair must be read together: the
  stratum-D negative here is a true negative reached partly *because* the
  engine cannot see that far, which is exactly why the preregistration called
  the positive cell the informative one. `recursive-carry` is correct both
  ways at constant depth 5.
- **The two false positives are the field-precision bound, not absence of
  field sensitivity.** `computed-property` and `nested-access-path` are the
  computed-key read and the depth-3 sibling read; the classic
  `same-object-field-negative` and `array-element-negative` are already false
  positives in this engine, so the challenge pair sharpens a known
  over-approximation rather than discovering one.
- **The higher-order misses are under-approximation, uniformly.** Every
  stratum-A and stratum-B negative is correct and five of those positives are
  missed, which is the under-approximating half of the approximation character
  the preregistration described. `closure-capture` and
  `anonymous-implementation` are the two stratum-B pairs it does resolve.

### Semgrep CE 1.174.0 — expanded core

`reports/semgrep-javascript-kernel.json`. The whole 58-case population is
selected and balance-checked, and the bounded profile then decides what is
scored, from case metadata, before Semgrep is invoked.

| Stratum | Assertions | Scored | `unsupported` | Polarity match (scored) |
| --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 14 | 18 | 12/14 |
| Challenge (13 templates) | 26 | 0 | 26 | n/a |

**All twenty-six challenge assertions take the preregistered `unsupported`
partition**, exactly as [the challenge tier](challenge-tier.md) predicted: no
challenge template carries the `intraprocedural` feature tag, so none is inside
the documented CE local-taint profile, and each retains its own
`*-unsupported.json` capability-decision document naming the declared
capability and the boundary it falls outside. The scored subset therefore stays
at **14 assertions and 12/14**, unchanged from the classic run — the two
mismatches are still the `infeasible-branch` and `loop-carried` negatives, the
path sensitivity the pinned CLI sells as Pro. The partition was not adjusted
for this expansion, and twenty-six declined assertions are coverage, never
twenty-six false negatives.

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
