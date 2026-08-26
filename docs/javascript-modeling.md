# JavaScript taint-modeling matrix

This is wave M1's JavaScript pull request: the twenty-four fixtures of
[the benchmark-controlled taint-modeling matrix](modeling-matrix.md), the four
per-adapter model encodings JavaScript's partition entitles it to, and the four
runs.

Nothing here amends the preregistration. The twelve template definitions, the
six categories, the negative mechanisms, the capability kinds, and the per-tool
partition were fixed before any of these fixtures existed, and this document
reports against them rather than adjusting them. Where a realization decision
had to be made that the preregistration's sketches leave open, it is stated
below and it is stated as a decision, not as a finding.

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
| Joern query | `adapters/joern/queries/modeling.sc` (shared by all three wave-M1 languages) |
| Semgrep rule | `adapters/semgrep/rules/model-javascript.yaml` |
| Reports | `reports/{bifrost,codeql,joern,semgrep}-javascript-modeling.json` |
| Load-bearing probe | `scripts/probe-javascript-modeling-load-bearing.sh` |

## Per-template realization

Every fixture is stdlib-only — no framework, no dependency, no build step — and
passes `node --check`. Every case is `score_tier: "modeling"`,
`model_profile: "benchmark-controlled"`, provenance revision
`m3-modeling-javascript`.

### Category S — declared sources and sinks

**1. `dfb-template-model-declared-source`.** `Config` is a module-level object
literal whose two members are named function expressions returning constant
strings. The positive sinks `Config.fetchRemote()`; the negative sinks
`Config.fetchLocal()`. Neither fixture contains `dfb_source` at all — the
declaration is the only reason anything is tainted, which is the point of the
template. The two bodies are the same shape and the same length, so an engine
that reads them learns nothing that separates them.

**2. `dfb-template-model-declared-sink`.** `Audit` is the same shape with two
one-parameter members that both drop their argument. The positive calls
`Audit.record(dfb_source())`; the negative calls `Audit.discard(dfb_source())`.

The negative's `DFB-SINK:` marker sits on `discard`, not on `record`, and this
is a deliberate anchoring decision. The anchor names the place taint actually
arrives in *that* fixture, so the assertion reads "taint reaches `discard`,
which is not a declared sink, so there is no finding". Anchoring the negative on
the uncalled `record` would have left the case with no resolvable sink callsite
and turned a correct false-positive into an `inconclusive`.

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

**4. `dfb-template-model-propagator-position`.** `Opaque.select(first, second)`
carries the same reflective body. The positive is
`dfb_sink(Opaque.select("clean", dfb_source()))` — taint at declared position 1
— and the negative is the identical call with the arguments swapped.

### Category Z — declared sanitizers

**5. `dfb-template-model-sanitizer-kill`.** Both fixtures define the same
`Clean.scrub` identity function; only the positive's sink call omits it. The
positive therefore asks nothing of the model and exists to establish that the
flow is there at all.

**6. `dfb-template-model-sanitizer-selectivity`.** `Clean` has two identity
members, `scrub` and `sanitize`. The positive routes through the *undeclared*
`sanitize`, the negative through the declared `scrub`.

### Category O — opaque procedure summaries

**7. `dfb-template-model-summary-through`.** `Bridge` lives in its own fixture
file, `Bridge.js`, which both cases carry — the first two-file cases in the
corpus. `pass` and `hold` are both the identity function, so the bodies agree
and only the summaries disagree.

**8. `dfb-template-model-summary-field`.** A second `Bridge.js`, this one
holding `deposit(value, box)` with an empty body. The box is a two-property
object literal; the positive sinks `box.payload` and the negative `box.spare`.

### Category E — framework entry points

**9. `dfb-template-model-entrypoint-parameter`.** One `Handler` member per
fixture — `onRequest` in the positive, `onIgnored` in the negative — each
sinking its parameter, each never called from anywhere in the fixture, and no
top-level code at all.

**10. `dfb-template-model-entrypoint-selectivity`.** Both handlers live in one
`Handler` object in *both* fixtures, so both are plausible roots in both cells,
and the model always declares `onDeclared`.

One realization decision the preregistration leaves open: the two handlers sink
into two different no-op sink functions, `dfb_sink` and `dfb_sink_sibling`,
rather than into one. With a single shared sink the two handlers' findings would
land on callsites of the same anchored function, and a selective engine's one
finding would match the negative's anchor just as well as the positive's — the
pair would be unable to tell selective synthesis from indiscriminate synthesis,
which is the only thing this template exists to measure. The handlers keep the
same signature and the same body shape; they differ only by the identity of the
callee, which is the same kind of minimal difference `record`/`discard` and
`scrub`/`sanitize` already use. Only `dfb_sink` is declared, so a finding is
attributable to exactly one handler.

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
approximated in it.

**Bifrost** declares category S alone, as two `:sources` entries bound to
`return-value` and two `:sinks` entries bound to `(argument :index 0)`. It sets
`:call-modeling (call-modeling :unmodeled require-model)`, which the pinned
v0.10.6 build accepts — the preregistration could not verify that against the
pinned binary and recorded category P as *to be verified, unsupported until
shown*; **this run does not promote that cell**, because P also requires a
propagator or transform declaration surface, which no committed policy has and
which this policy does not exercise. Promoting a partition cell is a dated
amendment on the preregistration, not a side effect of a language PR.

**CodeQL** declares all six categories in one `DataFlow::ConfigSig`: `isSource`
over the declared source calls and over the parameter node of each declared
entry point, `isSink` over argument 0 of the declared sink calls, `isBarrier`
over argument 0 of `Clean.scrub`, and five `isAdditionalFlowStep` clauses for
`carry`, `select`, `pass`, `deposit`, and the `put`/`get` pair. No data
extensions are used; the query owns the model, which is what
`adapters/codeql/README.md` states as this adapter's design.

Two encoding notes. Template 8's step lands on a `DataFlow::PropRead` of
`payload` off the object that flowed into `deposit`'s argument 1, which is the
`out: 1.payload` binding written in QL. Templates 11 and 12 share **one**
`isAdditionalFlowStep` clause conditioned on both an equal constant key and an
equal receiver local source: template 11's `store: primary` is a type identity
and template 12's is a receiver identity, and in QL a static call's receiver
*is* the type, so one relation states both declarations without weakening
either.

**Joern** splits its declarations across the two files the runner hash-binds
together. `modeling.sc` carries the source, sink, and entry-point identities as
query roots; `model-javascript.semantics` carries the propagator, sanitizer,
summary, and persistence declarations as `FlowSemantic`/`FlowMapping` entries in
Joern's own textual syntax.

One adaptation is worth stating plainly. The committed semantics file keys each
entry by the declared **member name** rather than by a frontend method full
name, and `modeling.sc` re-keys it onto a regex over the CPG's full names.
`jssrc2cpg` names a method on an object literal by its inferred structural type
— `{ carry: (value: ANY) => ANY; block: (value: ANY) => ANY; }:carry` — which is
a property of the fixture's shape rather than of the entity being declared, and
which would make the committed artifact unreadable and brittle. The declaration
itself is unchanged: the entity, the role, and the binding are what the file
states. Positions in the file are the declaration language's positions shifted
by one, because Joern counts the receiver as 0 and the declaration language
excludes it.

`modeling.sc` supplies the engine's own operator flows plus the benchmark's
declarations and nothing else — no language model catalog, no framework
semantics. The kernel script is untouched.

**Semgrep CE** declares categories S, Z, and E and nothing else — no
`pattern-propagators`, no summary, no persistence boundary — and sets
`options: taint_assume_safe_functions: true`, which is the load-bearing
requirement the preregistration verified against the pinned CE binary.

Unlike the kernel rules, nothing in this rule is templated. The kernel rules
substitute each case's own endpoint identifiers into placeholders; a modeling
rule that did the same would make every category-S negative pass for a reason
that has nothing to do with the declaration.

The entry-point patterns name the object-literal member —
`"onRequest: function onRequest($P) { ... }"` with `focus-metavariable: $P` —
rather than a bare `function onRequest(...)`. That is how the JavaScript
fixtures spell `Handler.onRequest`, and the pinned CE parser matches a named
function *expression* only in that position; a bare-declaration pattern matched
nothing at all. This is the same entity identity the other three adapters bind,
written in JavaScript's own syntax.

## Anchor reconciliation

Modeling cases are reconciled against their sink anchors by the same machinery
every kernel uses, with one addition. `AnchorDialect::EcmaMember` accepts a
member-qualified callsite — `Audit.record(v)` is a callsite of `record` — where
the kernel's `AnchorDialect::Ecma` deliberately refuses one. No kernel needs it,
because every kernel endpoint is a bare function; a modeling declaration binds a
type *and* a member, so a declared sink is only ever reached through its
receiver. The kernel dialect is unchanged and no kernel reconciliation moves.

## Results

Run sequentially against the pinned toolchain on 2026-08-26. Every outcome below
is retained in `reports/<tool>-javascript-modeling.json` with its raw evidence
under `reports/raw/<tool>-javascript-modeling/`.

### Outcome distribution

| Adapter | Scored | `reached` | `not-reached` | `inconclusive` | `unsupported` | Matches |
| --- | --- | --- | --- | --- | --- | --- |
| Bifrost v0.10.6 | 4 (S) | 0 | 2 | 2 | 20 | **2 / 2 decided** |
| CodeQL 2.26.3 | 24 (all six) | 12 | 12 | 0 | 0 | **24 / 24** |
| Joern 4.0.610 | 24 (all six) | 12 | 12 | 0 | 0 | **20 / 24** |
| Semgrep CE 1.174.0 | 12 (S, Z, E) | 5 | 7 | 0 | 12 | **11 / 12** |

The `unsupported` column is capability coverage, decided from the template
identity before the analyzer was invoked and retained with the
preregistration's own rationale. It is never a negative and it does not reduce
anyone else's denominator.

### Per category

| Category | Bifrost | CodeQL | Joern | Semgrep CE |
| --- | --- | --- | --- | --- |
| S — sources and sinks | 2/2 decided, 2 `inconclusive` | 4/4 | 4/4 | 4/4 |
| P — propagators | `unsupported` | 4/4 | 3/4 | `unsupported` |
| Z — sanitizers | `unsupported` | 4/4 | 4/4 | 3/4 |
| O — summaries | `unsupported` | 4/4 | 3/4 | `unsupported` |
| E — entry points | `unsupported` | 4/4 | 4/4 | 4/4 |
| B — persistence | `unsupported` | 4/4 | 2/4 | `unsupported` |

### Mismatches, in full

There are six across the whole matrix.

**Joern — `dfb-taint-javascript-model-propagator-position-negative`, false
positive.** Taint sits at the undeclared position 0 and the declaration maps
position 1 only, and Joern reports the flow anyway. The declaration *is* bound:
replacing it with a no-flow entry on the same entity suppresses the finding
(`flows=1` with `"select" 2->-1`, `flows=0` with `"select"`), so this is
positional fidelity, not binding. Joern's category-P positive is correct and its
positional negative is not.

**Joern — `dfb-taint-javascript-model-summary-field-negative`, false positive.**
The summary declares `out: 1.payload` and the negative sinks the sibling
property `spare`. Joern's `FlowMapping` destination is the parameter, not an
access path off it, so the field discrimination is left to the engine's heap
approximation and the engine does not make it. This is the cell the
preregistration itself marked *to be verified at implementation* for Joern's
category O; it is now verified as expressible but not field-discriminating, and
that is a run result rather than a partition change.

**Joern — both category-B positives, false negatives.** The roundtrip does not
close. Two separate things are true here and they are worth keeping apart:

- The declaration does not bind to the JavaScript call at all. `jssrc2cpg` gives
  a static class-method call — `Store.put("k", …)` — the method full name
  `<unknownFullName>`, and Joern's flow-semantics surface is keyed by method
  full name, so nothing can attach to it.
- It would not have mattered. Re-running the same declarations against an
  object-literal spelling of `Store`, where the call *does* resolve and the
  semantics *are* found for both `put` and `get`, still produces zero flows:
  taint deposited on the receiver by `put` does not survive into a separate
  procedure's `get`.

The published outcome is therefore the same either way, and the fixtures are
left as the preregistration's sketch spells them.

**Semgrep CE — `dfb-taint-javascript-model-sanitizer-selectivity-positive`,
false negative.** The flow runs through the *undeclared* `Clean.sanitize`, and
`taint_assume_safe_functions: true` — the load-bearing switch this category is
required to run under — stops taint at any call the rule does not model. Semgrep
correctly refuses to treat a `sanitize`-shaped name as a barrier; it simply
cannot carry taint through an unmodeled call while the switch is on. Publishing
this as a miss is the honest reading: the alternative would have been to turn
the switch off and score category Z on the engine's default instead of on the
declaration, which the load-bearing requirement forbids.

**Bifrost — both category-S positives, `inconclusive`.** Not a mismatch, and
counted in neither direction. See the three-way distinction below.

### What the numbers do and do not say

CodeQL's 24/24 says its data-flow configuration expresses every one of the six
declaration roles and produces the declared semantics. It says nothing at all
about CodeQL's propagation kernel score, and this number is never added to one.

Bifrost's two decided assertions are two, not two out of twenty-four: it
declined five categories in the preregistration, and a decline is coverage.

Semgrep CE decided twelve assertions to Bifrost's four, which is the opposite
of the ordering the propagation kernels would suggest — which is the entire
reason this tier exists.


## The three-way distinction

All three states occur in this run, and each is retained distinctly.

**Missing model** — none, and unrepresentable. Every scored cell has a
declaration behind it in that adapter's committed artifact, and every declined
cell is declined by the preregistered partition. The runner refuses to start
when an artifact is missing, and the population validator refuses a modeling
case that is not one of the twelve or that is not
`model_profile: "benchmark-controlled"`.

**Unsupported activation** — 32 assertions: Bifrost's twenty and Semgrep CE's
twelve. Each is decided from the template identity *before* the analyzer is
invoked, retains the preregistration's rationale verbatim, and writes a
`retained-capability-decision` evidence document beside the report. No analyzer
process ran for any of them.

**Incomplete analysis** — 2 assertions, both Bifrost category-S positives.
Bifrost binds both declared identities and emits the finding, with a
source-to-sink display path, and then reports the run as incomplete
(`partial_discovery`, "procedure value-flow snapshot ... is unknown"). Under
[the scoring contract](scoring.md#outcome-interpretation) that is `inconclusive`
and never `not-reached`: the model was activated and the analysis did not
complete, which is a different statement from "the analysis ran and found
nothing". The same incompleteness is what the frozen JavaScript kernel slice
records for this build, so it is a property of the engine on this language
rather than of these fixtures.

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
| CodeQL | P | the `Opaque.carry` propagator step | 1 finding | **0 findings** |
| Joern | Z | the `"scrub"` no-flow entry | 0 flows | **1 flow** |
| Semgrep CE | S | the `Audit.record` sink pattern | 1 finding | **0 findings** |

Joern's row is the sanitizer rather than the propagator, and the reason is
retained in the same directory as a deliberate counter-example.

**Joern's category-P declaration is not load-bearing on JavaScript.** Removing
`"carry" 1->-1` leaves the finding in place — `flows=1` either way. The pinned
Joern follows the fixture's `Reflect.get(_impl, name).apply(null, [v])` body on
its own, so its template-3 positive is `reached` for a reason that need not have
anything to do with the declaration. The preregistration's argument for that
template rests on the v0.4.0 freeze's twelve reflective-invocation cells, in
which no engine reaches the sink through a reflective body; that evidence was
gathered against the core kernel's computed-key dispatch, and it does not carry
over to this `Reflect` body for this engine.

Stated as the preregistration requires it to be stated: **Joern's
`dfb-template-model-opaque-propagator` positive is not evidence of model
activation on JavaScript, and should not be read as such.** Its category-P
*negative* still is — the no-flow declaration on `Opaque.block` suppresses a
finding that Joern would otherwise produce — and so are its other five scored
categories. This is a **proposed amendment** to
[the modeling matrix](modeling-matrix.md): either template 3 needs an opaque
body that Joern demonstrably does not follow, or Joern's category-P positive
cell needs to be recorded as not load-bearing for JavaScript. It is written up
here rather than acted on, because a partition or template revision is a dated
amendment on the preregistration and never a side effect of a language pull
request. Nothing in this run was tuned around it; the retained probe is the
evidence.

