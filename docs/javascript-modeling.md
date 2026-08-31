# JavaScript taint-modeling matrix

This is wave M1's JavaScript row: the twenty-four fixtures of
[the benchmark-controlled taint-modeling matrix](modeling-matrix.md), the four
per-adapter model encodings JavaScript's partition entitles it to, and the four
runs. It lands after [Python's](python-modeling.md) and is deliberately its
mirror — the same fixture shapes, the same file-per-entity naming, the same
runner and query — so that a difference between the two rows is a difference
between the *frontends*, never between two benchmark designs.

Nothing here amends the preregistration's partition. The twelve template
definitions, the six categories, the negative mechanisms, the capability kinds,
and the per-tool partition were fixed before any of these fixtures existed, and
this document reports against them **as amended by
[A2](modeling-matrix.md#a2--2026-08-26-joerns-propagator-and-summary-categories-are-not-load-bearing)
and [A3](modeling-matrix.md#a3--2026-08-26-semgreps-sanitizer-selectivity-cell-is-undecidable-by-construction)**,
both of which were made against Python's evidence and are confirmed here. This
row contributes one amendment of its own,
[A4](modeling-matrix.md#a4--2026-08-26-the-reflective-opaque-propagator-body-is-not-unfollowable-by-joerns-jssrc2cpg),
which corrects a factual claim and moves no cell.

**JavaScript's modeling denominator is 12 templates / 24 assertions**, on the
`modeling` tier, with its own scorecards. No number in this document is ever
pooled with the JavaScript propagation kernel's 29 templates / 58 assertions,
and a high score here is not a high propagation score.

## What is committed

| Artifact | Path |
| --- | --- |
| Cases and fixtures | `cases/taint/javascript/model-*-{positive,negative}/` |
| Bifrost policy | `adapters/bifrost/policies/model-javascript.rqlp` |
| CodeQL query | `adapters/codeql/javascript/queries/JavaScriptModeling.ql` |
| Joern semantics | `adapters/joern/semantics/model-javascript.semantics` |
| Joern query | `adapters/joern/queries/modeling.sc` (shared by every wave-M1 language) |
| Semgrep rule | `adapters/semgrep/rules/model-javascript.yaml` |
| Reports | `reports/{bifrost,codeql,joern,semgrep}-javascript-modeling.json` |
| Load-bearing probe | `scripts/probe-javascript-modeling-load-bearing.sh` |

## Per-template realization

Every fixture is stdlib-only — no framework, no dependency, no build step — and
passes `node --check`. Every case is `score_tier: "modeling"`,
`model_profile: "benchmark-controlled"`, provenance revision
`m3-modeling-javascript`.

**Fixtures are named for the entity they declare**, not for the case: `Audit.js`,
`Config.js`, `Handler.js`, `Clean.js`, `Store.js`, `Opaque.js`,
`Bridge.js` + `Flow.js`. This is Python's convention and it is not cosmetic —
Joern's flow-semantics keys are method *full names*, which `jssrc2cpg` spells
`<file>::program:<member>`, so a per-case fixture filename would make the
committed declaration a different string in every case.

**The endpoint identities come from each fixture's own `DFB-SOURCE:` /
`DFB-SINK:` markers, and those markers always sit on the *declared* entity**,
including in the negatives, where the declared entity is deliberately not the
one the taint runs through. That is what makes a negative measure the
declaration: the runner selects the declared source and the declared sink, and
the fixture arranges for the flow to go somewhere else.

### Category S — declared sources and sinks

**1. `dfb-template-model-declared-source`.** `Config` is a module-level object
literal whose two members are named function expressions returning constant
strings. The positive sinks `Config.fetchRemote()`; the negative sinks
`Config.fetchLocal()`. The marker sits on `fetchRemote` in both, so the
negative's declared source is present in the file but never called — an absent
*declared* endpoint is the assertion, not an incomplete run (see
[Anchor reconciliation](#anchor-reconciliation)). Neither fixture contains
`dfb_source` at all: the declaration is the only reason anything is tainted.
The two bodies are the same shape and the same length, so an engine that reads
them learns nothing that separates them.

**2. `dfb-template-model-declared-sink`.** `Audit` is the same shape with two
one-parameter members that both drop their argument. The positive calls
`Audit.record(dfb_source())` and `Audit.discard("clean")`; the negative swaps
them. The declared sink `Audit.record` is called in both fixtures, so both cells
resolve a sink callsite and the negative turns purely on which call carries the
taint.

### Category P — declared propagators

**3. `dfb-template-model-opaque-propagator`.** The opaque body is the one the
preregistration fixes for JavaScript: `Reflect.get(_impl, name).apply(null,
[value])`, with `name` a local string constant. This deliberately differs from
the core kernel's JavaScript `reflective-invocation` fixture, which uses a
computed-key call; the matrix uses `Reflect` so the opacity is the same shape in
Java, JavaScript, and Python. That divergence is recorded in
[the preregistration itself](modeling-matrix.md#3-dfb-template-model-opaque-propagator)
and is not drift.

`Opaque.carry` and `Opaque.block` carry byte-identical bodies. The positive
sinks through `carry`, the negative through `block`.

**The preregistration's claim that no engine follows this body unaided is false
for Joern's `jssrc2cpg`, and that measurement is
[Amendment A4](modeling-matrix.md#a4--2026-08-26-the-reflective-opaque-propagator-body-is-not-unfollowable-by-joerns-jssrc2cpg).**
See [Load-bearing verification](#load-bearing-verification). A2 had already
moved Joern's category-P cells to unsupported activation, so A4 changes no
score; it corrects the factual record.

**4. `dfb-template-model-propagator-position`.** `Opaque.select(first, second)`
carries the same reflective body. The positive is
`dfb_sink(Opaque.select("clean", dfb_source()))` — taint at declared position 1
— and the negative is the identical call with the arguments swapped.

### Category Z — declared sanitizers

**5. `dfb-template-model-sanitizer-kill`.** Both fixtures define the same
`scrub` identity function; only the positive's sink call omits it. The positive
therefore asks nothing of the model and exists to establish that the flow is
there at all.

**6. `dfb-template-model-sanitizer-selectivity`.** `Clean.js` holds two identity
functions, `scrub` and `sanitize`. The positive routes through the *undeclared*
`sanitize`, the negative through the declared `scrub`.

One realization decision, and it is the one place JavaScript's fixtures diverge
from the member-qualified style the rest of this row uses: **the declared
sanitizer is a top-level function rather than an object or class member.** The
reason is a measured property of `jssrc2cpg` and is written up under
[the Joern encoding](#the-four-encodings): a member call has no stable,
entity-denoting method full name on the pinned frontend, so a member-spelled
sanitizer could not be declared to Joern at all without keying the artifact to
the fixture's shape. The three other adapters bind the entity by name and are
indifferent to the choice.

### Category O — opaque procedure summaries

**7. `dfb-template-model-summary-through`.** `Bridge` lives in its own fixture
file, `Bridge.js`, which both cases carry alongside `Flow.js` — the only
two-file cases in this row, mirroring Python's `bridge.py` + `flow.py`. `pass`
and `hold` are both the identity function, so the bodies agree and only the
summaries disagree.

**8. `dfb-template-model-summary-field`.** A second `Bridge.js`, this one
holding `deposit(value, box)` with an empty body. The box is a two-property
object literal; the positive sinks `box.payload` and the negative `box.spare`.

### Category E — framework entry points

**9. `dfb-template-model-entrypoint-parameter`.** Both handlers —
`Handler.onRequest` (declared) and `Handler.onIgnored` (undeclared) — are
present in both cells, neither is called from anywhere in the fixture, and
there is no top-level code at all. The positive has the declared handler sink
its parameter and the undeclared one sink a constant; the negative swaps them.

**10. `dfb-template-model-entrypoint-selectivity`.** The same shape with
`onDeclared` and `onUndeclared`. The model always declares `onDeclared`, so a
finding is attributable to exactly one handler and the pair separates selective
synthesis from indiscriminate synthesis.

### Category B — persistence boundaries

**11. `dfb-template-model-store-roundtrip`.** `Store` is a class with two static
no-op methods. `writeSide()` calls `Store.put(key, dfb_source())` and a separate
`readSide()` calls `dfb_sink(Store.get(key))`. The positive shares one constant
key; the negative uses `"a"` and `"b"`. No standard-library map is used, so an
engine with a shipped `Map.get` model cannot pass without reading the
declaration.

**12. `dfb-template-model-store-separation`.** The same class with instance
methods, and two module-level instances constructed once and never reassigned.
The positive writes and reads `alpha`; the negative writes `alpha` and reads
`beta`.

## The four encodings

The same three parts — entity identity, role, binding semantics — in four native
surfaces. Nothing is translated across the surfaces, and a category a tool's
partition declines is **absent** from that tool's artifact rather than
approximated in it. That last rule is now a test:
`the_modeling_artifacts_declare_only_their_scored_categories` fails the suite if
any language's artifact declares a category its partition marks unsupported.

**Bifrost** declared category S alone when this row ran, as two `:sources`
entries bound to `return-value` and two `:sinks` entries bound to
`(argument :index 0)`; Amendment A9 has since promoted category Z and the
committed artifact now also carries one `:sanitizers` entry, whose scored
evidence lands with the next re-run. It sets
`:call-modeling (call-modeling :unmodeled require-model)`, which the pinned
v0.10.7 build accepts — the preregistration could not verify that against the
pinned binary and recorded category P as *to be verified, unsupported until
shown*; **this run does not promote that cell**, because P also requires a
propagator or transform declaration surface, which no committed policy has and
which this policy does not exercise. Promoting a partition cell is a dated
amendment on the preregistration, not a side effect of a language pull request.

**CodeQL** declares all six categories in one `DataFlow::ConfigSig`: `isSource`
over the declared source calls and over the parameter node of each declared
entry point, `isSink` over argument 0 of the declared sink calls, `isBarrier`
over argument 0 of `scrub` (plus the explicit no-flow declarations of `block`
and `hold`), and five `isAdditionalFlowStep` clauses for `carry`, `select`,
`pass`, `deposit`, and the `put`/`get` pair. No data extensions are used; the
query owns the model, which is what `adapters/codeql/README.md` states as this
adapter's design.

Two encoding notes. Template 8's step lands on a `DataFlow::PropRead` of
`payload` off the object that flowed into `deposit`'s argument 1, which is the
`out: 1.payload` binding written in QL. Templates 11 and 12 share **one**
`isAdditionalFlowStep` clause conditioned on both an equal constant key and an
equal receiver binding: template 11's `store: primary` is a type identity and
template 12's is a receiver identity, and in QL a static call's receiver *is*
the class binding, so one relation states both declarations without weakening
either.

**Joern** splits its declarations across the two files the runner hash-binds
together. `modeling.sc` — unchanged, and shared byte-for-byte with Python —
carries the source, sink, and entry-point identities as query roots, selected by
the identity read off each fixture's own DFB markers;
`model-javascript.semantics` carries the sanitizer and persistence declarations
as `FullNameSemanticsParser` entries in Joern's own textual syntax. Categories P
and O are absent from the file, because A2 declines them.

**A measured `jssrc2cpg` surface fact, and the one realization it forces.**
Joern's flow-semantics surface is keyed by the CPG's `methodFullName`. On the
pinned 4.0.614, JavaScript's frontend gives three different answers depending on
how the callee is written, and only one of them denotes the entity:

| Callee shape | `methodFullName` at the call site |
| --- | --- |
| top-level function — `scrub(v)` | `Clean.js::program:scrub` |
| object-literal member — `Clean.scrub(v)` | `{ scrub: (value: ANY) => ANY; sanitize: (value: ANY) => ANY; }:scrub` |
| class method, static or instance — `Store.put(k, v)`, `alpha.put(k, v)` | `<unknownFullName>` |

The middle row is the member's inferred **structural type**: a property of the
object's shape, not of the entity, so adding a third member to `Clean` would
silently un-declare `scrub`. The bottom row is shared by every unresolved call
in the CPG, so declaring it would model all of them. Only the top row is an
identity a benchmark can commit to, which is why the declared sanitizer is a
top-level function. The persistence pair is left spelled as the model names it —
`Store.put` / `Store.get` — and the consequence is measured rather than designed
around; see the [category-B mismatch](#mismatches-in-full). This is recorded as
a published observation about the frontend, not as a defect in Joern's modeling
surface: the same declarations key cleanly on `pythonsrc`.

The Joern semantics file also carries no blank line and no `//` comment, for the
reason recorded beside Python's: the pinned parser drops every declaration on
either, silently, and a scored cell would then be decided by the absence of a
model. A test enforces both rules on both languages' files.

**Semgrep CE** declares categories S, Z, and E and nothing else — no
`pattern-propagators`, no summary, no persistence boundary — and sets
`options: taint_assume_safe_functions: true`, which is the load-bearing
requirement the preregistration verified against the pinned CE binary. Under A3,
template 6 is `unsupported` activation, so Semgrep's scored set is five
templates.

Unlike the kernel rules, nothing in this rule is templated. The kernel rules
substitute each case's own endpoint identifiers into placeholders; here the
endpoint identities *are* the model and are the same for every case, so the
committed rule states them literally and the runner substitutes nothing.

The entry-point patterns name the object-literal member —
`"onRequest: function onRequest($P) { ... }"` with `focus-metavariable: $P` —
rather than a bare `function onRequest(...)`. That is how the JavaScript
fixtures spell `Handler.onRequest`, and the pinned CE parser matches a named
function *expression* only in that position; a bare-declaration pattern matched
nothing at all. This is the same entity identity the other three adapters bind,
written in JavaScript's own syntax.

## Anchor reconciliation

Modeling cases are reconciled by the same machinery every kernel uses, with two
modeling-specific additions that no kernel path can see.

**`AnchorDialect::EcmaMember`** accepts a member-qualified callsite —
`Audit.record(v)` is a callsite of `record` — where the kernel's
`AnchorDialect::Ecma` deliberately refuses one. No kernel needs it, because
every kernel endpoint is a bare function; a modeling declaration binds a type
*and* a member, so a declared sink is reached through its receiver. The kernel
dialect is unchanged and no kernel reconciliation moves.

**`JoernEndpointRule::AbsenceIsTheAssertion`** governs what a zero endpoint
count means. Under the kernels' rule, a run that resolved no source node or no
sink node never observed both benchmark-controlled endpoints and is
`inconclusive`. In this matrix a negative may legitimately contain no *declared*
endpoint — template 1's negative never calls the declared `Config.fetchRemote` —
and that absence is the content of the assertion rather than an incomplete run.
The counts are retained as a diagnostic rather than converted, and an **empty
extraction** (`method_count == 0`) is still `inconclusive` under both rules. The
kernels keep `BothMustBeObserved` unchanged.

This rule also corrects Python's row retroactively:
`dfb-taint-python-model-declared-source-negative`, published as `inconclusive`
in [the Python row](python-modeling.md), is a clean `not-reached` under it, and
`reports/joern-python-modeling.json` has been re-run to say so.

## Results

Run sequentially against the pinned toolchain — Bifrost v0.10.6, CodeQL CLI
2.26.3, Joern 4.0.610, Semgrep CE 1.174.0 (`--oss-only`) — on 2026-08-26. Every
outcome below is retained in `reports/<tool>-javascript-modeling.json` with its
raw evidence under `reports/raw/<tool>-javascript-modeling/`.

### Outcome distribution

| Adapter | Scored | `reached` | `not-reached` | `inconclusive` | `unsupported` | Matches |
| --- | --- | --- | --- | --- | --- | --- |
| Bifrost v0.10.6 | 4 (S) | 0 | 1 | 3 | 20 | **1 / 1 decided** |
| CodeQL 2.26.3 | 24 (all six) | 12 | 12 | 0 | 0 | **24 / 24** |
| Joern 4.0.610 | 16 (S, Z, E, B) | 6 | 10 | 0 | 8 | **14 / 16** |
| Semgrep CE 1.174.0 | 10 (S, Z template 5, E) | 5 | 5 | 0 | 14 | **10 / 10** |

The `unsupported` column is capability coverage, decided from the template
identity before the analyzer was invoked and retained with the
preregistration's own rationale. It is never a negative and it does not reduce
anyone else's denominator.

Configuration hashes: Bifrost `25e1399f…`, CodeQL `50f4a317…`, Joern
`44faa326…`, Semgrep `51a89f86…`.

### Per category

| Category | Bifrost | CodeQL | Joern | Semgrep CE |
| --- | --- | --- | --- | --- |
| S — sources and sinks | 1/1 decided, 3 `inconclusive` | 4/4 | 4/4 | 4/4 |
| P — propagators | `unsupported` | 4/4 | `unsupported` (A2) | `unsupported` |
| Z — sanitizers | `unsupported` | 4/4 | 4/4 | 2/2 (template 6 `unsupported`, A3) |
| O — summaries | `unsupported` | 4/4 | `unsupported` (A2) | `unsupported` |
| E — entry points | `unsupported` | 4/4 | 4/4 | 4/4 |
| B — persistence | `unsupported` | 4/4 | 2/4 | `unsupported` |

**This is the same shape as Python's row, cell for cell**, including Joern's two
category-B false negatives and Semgrep's clean sweep of its five templates. The
one difference is Bifrost, and it is a JavaScript-language property rather than
a modeling one; see below.

### Mismatches, in full

There are two across the whole matrix, and both are Joern's.

**Joern — both category-B positives, false negatives.** The roundtrip does not
close, in either the type-identity (template 11) or the receiver-identity
(template 12) cell. Two things are true and worth keeping apart:

- **The declaration does not bind to the JavaScript call at all.** `jssrc2cpg`
  gives a class-method call — static `Store.put("k", …)` or instance
  `alpha.put("k", …)` — the method full name `<unknownFullName>`, and the
  flow-semantics surface is keyed by method full name, so nothing can attach to
  it. This is the frontend fact tabulated under
  [the Joern encoding](#the-four-encodings).
- **It would not have mattered.** Python's row runs the identical declarations
  against `pythonsrc`, where `store.py:<module>.Store.put` *does* key cleanly,
  and produces the identical pair of false negatives: taint deposited on the
  receiver by `put` does not survive into a separate procedure's `get`. The
  limitation the cell measures is the engine's, not the frontend's, and
  JavaScript reaches it by a shorter route.

Neither is a partition change and neither was tuned around. The fixtures are
left as the preregistration's sketch spells them.

**Bifrost — three category-S cells, `inconclusive`.** Not a mismatch, and
counted in neither direction. See the three-way distinction below.

### What the numbers do and do not say

CodeQL's 24/24 says its data-flow configuration expresses every one of the six
declaration roles and produces the declared semantics. It says nothing at all
about CodeQL's propagation kernel score, and this number is never added to one.

Joern's 14/16 is over a denominator A2 shrank from 24 to 16. That is not a
worse result reported as a better one: the eight withdrawn cells were withdrawn
because a result there would have scored the engine's default optimism rather
than the model, and scoring them would have been the dishonest option.

Semgrep CE decided ten assertions to Bifrost's four, which is the opposite of
the ordering the propagation kernels would suggest — which is the entire reason
this tier exists.

Bifrost's one decided assertion is one, not one out of twenty-four: it declined
five categories in the preregistration, and a decline is coverage.

## The three-way distinction

All three states occur in this run, and each is retained distinctly.

**Missing model** — none, and unrepresentable. Every scored cell has a
declaration behind it in that adapter's committed artifact, and every declined
cell is declined by the preregistered partition. The runner refuses to start
when an artifact is missing, and the population validator refuses a modeling
case that is not one of the twelve or that is not
`model_profile: "benchmark-controlled"`.

**Unsupported activation** — 42 assertions: Bifrost's twenty, Joern's eight, and
Semgrep CE's fourteen. Each is decided from the template identity *before* the
analyzer is invoked, retains the preregistration's rationale verbatim, and
writes a `retained-capability-decision` evidence document beside the report. No
analyzer process ran for any of them.

**Incomplete analysis** — 3 assertions, all Bifrost category-S cells. Bifrost
binds both declared identities and emits the finding, with a source-to-sink
display path, and then reports the run as incomplete (`partial_discovery`,
"procedure value-flow snapshot … is unknown"). Under
[the scoring contract](scoring.md#outcome-interpretation) that is `inconclusive`
and never `not-reached`: the model was activated and the analysis did not
complete, which is a different statement from "the analysis ran and found
nothing". The same incompleteness is what the frozen JavaScript kernel slice
records for this build, so it is a property of the engine on this language
rather than of these fixtures — and it is exactly why Python's Bifrost row
decides all four of its cells and JavaScript's decides one.

No result in this run is `runner-error`.

## Load-bearing verification

`scripts/probe-javascript-modeling-load-bearing.sh` runs one positive fixture
per adapter twice — once against the committed artifact and once against a copy
with the single declaration under test deleted — and retains both raw outputs
under `reports/raw/load-bearing-javascript-modeling/`. It never touches a
committed artifact and never writes a report.

| Adapter | Category | Declaration removed | With model | Without model |
| --- | --- | --- | --- | --- |
| Bifrost | S | the `Config.fetchRemote` source entry | 1 finding | **0 findings** |
| CodeQL | P | the `Opaque.carry` propagator step | 1 result | **0 results** |
| Joern | Z | the `Clean.js::program:scrub` no-flow entry | 0 flows | **1 flow** |
| Semgrep CE | S | the `Audit.record` sink pattern | 1 finding | **0 findings** |

Every scored category is load-bearing on the adapter that scores it, and the
JavaScript row confirms A2's Python finding from the other direction: Joern's
`NilSemantics` sanitizer entry is the only thing standing between the fixture's
identity-function body and a reported flow.

### Amendment A4's evidence

The probe also retains one deliberate **counter-example**, which is what
[Amendment A4](modeling-matrix.md#a4--2026-08-26-the-reflective-opaque-propagator-body-is-not-unfollowable-by-joerns-jssrc2cpg)
is made of.

`reports/raw/load-bearing-javascript-modeling/joern-opaque-propagator-unmodeled.json`
is one run of `modeling.sc` over `model-opaque-propagator-positive` under the
committed semantics file — which, after A2, declares **nothing at all** for
category P. It records `state: analyzed`, `declared_semantic_count: 3` (the
sanitizer and the two persistence mappings, none of them a propagator), and
`flows: 1`. The pinned Joern reaches `dfb_sink` through
`Reflect.get(_impl, target).apply(null, [value])` with no propagator model
whatsoever.

The preregistration argues template 3's assertability from the v0.4.0 freeze's
twelve `dfb-template-chal-reflective-invocation` positive cells, in which no
engine reaches the sink through a reflective body. That evidence was gathered
against the core kernel's *computed-key dispatch* (`handlers[name](...)`), and
it does not carry over to this `Reflect` body for this frontend. A4 withdraws
the transfer; the v0.4.0 evidence itself is untouched.

**A4 changes no score.** A2 had already moved Joern's category-P and category-O
cells to unsupported activation for the stronger reason that `FlowSemantic`
mappings cannot restrict the default pass-through, so a `reached` here was
already outside Joern's scored set. What A4 corrects is the factual record, and
it does so as a dated amendment on the preregistration rather than as a side
effect of this pull request. Nothing in this run was tuned around it; the
retained probe is the evidence.
