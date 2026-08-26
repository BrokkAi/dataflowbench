# Python taint-modeling matrix

Wave M1's Python row of the
[benchmark-controlled taint-modeling matrix](modeling-matrix.md). It adds
Python's twenty-four modeling assertions, the four per-adapter model
encodings its partition entitles it to, and the first runs of all four
adapters against them.

Nothing in the preregistration is changed by this document. The twelve
template definitions, the six categories, the per-tool capability partition,
and the three-way missing/unsupported/incomplete distinction are fixed there
and are only *realized* here. This wave's probes did produce two capability
findings, and those were carried into the preregistration through its own
amendment procedure — [A2](modeling-matrix.md#a2--2026-08-26-joerns-propagator-and-summary-categories-are-not-load-bearing)
(Joern's categories P and O) and
[A3](modeling-matrix.md#a3--2026-08-26-semgreps-sanitizer-selectivity-cell-is-undecidable-by-construction)
(Semgrep's template 6) — before the runs below were taken. The pre-amendment
observations that motivated them are kept in
[What the amendments were made of](#what-the-amendments-were-made-of). Where Python forces a spelling the document's
analyzer-neutral identity cannot carry verbatim, it is recorded below under
[Python realization notes](#python-realization-notes) rather than absorbed
silently.

This is a **modeling** population. It is never in a core denominator, it is
never pooled with [the Python semantic kernel](python-kernel.md), and no
headline number combines the two. They answer different questions: the kernel
asks whether an engine can follow flow it can see, and this matrix asks
whether an engine can be told things.

## The population

Twenty-four cases under `cases/taint/python/model-<short>-{positive,negative}/`,
ids `dfb-taint-python-model-<short>-<polarity>`, all
`score_tier: "modeling"`, `model_profile: "benchmark-controlled"`,
`fixture_provenance.revision: "m3-modeling-python"`, standard library only.

| # | Template | Cat. | Fixture | Declared entity | Neg. mechanism |
| --- | --- | --- | --- | --- | --- |
| 1 | `dfb-template-model-declared-source` | S | `config.py` | `config.fetch_remote` | `unrelated-value` |
| 2 | `dfb-template-model-declared-sink` | S | `audit.py` | `audit.record` | `unrelated-value` |
| 3 | `dfb-template-model-opaque-propagator` | P | `opaque.py` | `opaque.carry` | `call-context-separation` |
| 4 | `dfb-template-model-propagator-position` | P | `opaque.py` | `opaque.select` | `call-context-separation` |
| 5 | `dfb-template-model-sanitizer-kill` | Z | `clean.py` | `clean.scrub` | `sanitizer` |
| 6 | `dfb-template-model-sanitizer-selectivity` | Z | `clean.py` | `clean.scrub` | `sanitizer` |
| 7 | `dfb-template-model-summary-through` | O | `flow.py` + `bridge.py` | `bridge.pass_through` | `call-context-separation` |
| 8 | `dfb-template-model-summary-field` | O | `flow.py` + `bridge.py` | `bridge.deposit` | `field-separation` |
| 9 | `dfb-template-model-entrypoint-parameter` | E | `handler.py` | `handler.on_request` | `call-context-separation` |
| 10 | `dfb-template-model-entrypoint-selectivity` | E | `handler.py` | `handler.on_declared` | `call-context-separation` |
| 11 | `dfb-template-model-store-roundtrip` | B | `store.py` | `Store.put` / `Store.get` | `field-separation` |
| 12 | `dfb-template-model-store-separation` | B | `store.py` | `Store.put` / `Store.get` | `object-separation` |

## Python realization notes

**The declaring type is the fixture module.** The declaration language binds an
entity by "the declaring type (or module), the member name, and, where the
role needs it, a parameter position". Python's idiomatic spelling of a
namespace of free functions is a module, and the preregistration's own Python
sketch for template 1 says so directly — *"a module `config.py` with `def
fetch_remote()`"*. Every fixture is therefore a module named after the
declaring type (`config`, `audit`, `opaque`, `clean`, `handler`, `bridge`,
`store`), and its members are module-level functions. Templates 11 and 12 are
the exception the preregistration itself requires: template 12 needs two
*instances*, so `Store` is a class in both, with static members in template 11
and instance members in template 12.

**`pass` is a Python keyword.** Template 7's member is `Bridge.pass`. Python
reserves that word, so the member is spelled `pass_through`, following the
precedent the existing Java calibration case
`dfb-taint-java-modeled-external` already sets with
`ThirdPartyBridge.passThrough`. The sibling `hold` is unchanged. This is a
spelling adaptation of one identifier, not a change to the entity identity,
the role, or the binding semantics — the three parts the equivalence contract
compares.

**Templates 9 and 10 keep both handlers, and move the tainted parameter rather
than the handler.** The preregistration sketches category E as "one type with
two uncalled one-parameter methods whose bodies each sink the parameter". Both
fixtures of each pair carry two uncalled one-parameter handlers of the same
signature in the same module, and neither is called from anywhere. What the
negative moves is which handler sinks its *parameter*: in the positive the
declared handler sinks `payload` and the undeclared sibling sinks a constant,
and in the negative the two are exchanged.

The alternative — both handlers sinking their parameter in the negative cell
too — is not assertable, and the reason is a property of the benchmark's
evidence contract rather than of any engine. Every adapter reconciles a finding
against the case's own `DFB-SINK:` anchor, and the anchored sink's callsites
are resolved across the whole fixture file. An engine that correctly activated
the declared entry point would report a genuine finding inside the *declared*
handler of such a negative fixture, that finding would land on a callsite of
the anchored sink, and the cell would record a false positive for behavior
that is exactly right. Moving the tainted parameter keeps the negative's
question — *is the undeclared sibling a root?* — and removes an assertion that
could only ever be wrong.

**The `DFB-SOURCE:` marker sits on the declared handler in both polarities**,
and that placement is load-bearing rather than cosmetic. Joern's adapter reads
its source identity off the marker line, so a marker on the undeclared sibling
would point the engine at an entity the matrix never declared: it would
faithfully root `on_ignored`, find the flow, and record a false positive that
measured the benchmark's anchoring rather than Joern's selectivity. That is
what the first Joern run did before the anchors were corrected. The declared
member, the role, the binding, and the `call-context-separation` mechanism are
unchanged; what changed is which of two lines carries the marker.

**Every non-anchor sibling still has a callsite.** Template 2's negative calls
`discard(dfb_source())` *and* `record("clean")`. The second call is not
decoration: the sink-anchor contract resolves the anchored sink function's
callsites in its own file, and a sink with no callsite is unresolvable
evidence rather than a negative. The clean call gives the anchor a callsite
without giving the cell a flow, exactly as the core kernel's
`dfb-taint-python-direct-negative` already does.

## What each adapter was told

One artifact per adapter, hash-bound into that adapter's
`configuration_hash`. An artifact never declares a category the partition
marks `unsupported` for its tool: those cells are decided from the template
identity before the binary is invoked, and a declaration behind them would be
a claim the partition does not make.

| Adapter | Artifact | Categories declared |
| --- | --- | --- |
| Bifrost | `adapters/bifrost/policies/model-python.rqlp` | S |
| CodeQL | `adapters/codeql/python/queries/PythonModeling.ql` | S, P, Z, O, E, B |
| Joern | `adapters/joern/semantics/model-python.semantics` + `adapters/joern/queries/modeling.sc` | S, Z, E, B (P and O declined by Amendment A2) |
| Semgrep CE | `adapters/semgrep/rules/model-python.yaml` | S, Z, E (template 6 declined by Amendment A3) |

### Bifrost

Two RQLP endpoint sets: `:sources` gains `fetch_remote` beside the benchmark's
own `dfb_source`, and `:sinks` gains `record` beside `dfb_sink`. The policy
sets `:call-modeling (call-modeling :unmodeled require-model)` rather than the
kernel policies' `optimistic`, which is
[the load-bearing-model requirement](modeling-matrix.md#the-load-bearing-model-requirement);
the runner refuses a modeling policy that does not.

### CodeQL

One `DataFlow::ConfigSig` — `isSource`, `isSink`, `isBarrier`, and
`isAdditionalFlowStep` — covering all six categories, inside the existing
`dataflowbench/codeql-python` pack so it resolves `codeql/python-all@7.2.3`.
Category E is `isSource` over `DataFlow::parameterNode` of an *uncalled*
method: CodeQL's data flow does not require a source to be reachable from a
call-graph root. Category B is one `isAdditionalFlowStep` from `put`'s value
argument to `get`'s result, conditioned on equal constant keys and an equal
receiver identity; that single clause covers both templates, because template
11's receiver is the type and template 12's is the instance.

The explicit no-flow declarations of templates 3 and 7 are `isBarrier` on
`block`'s and `hold`'s arguments. They are not tuning: `hold`'s body is the
identity function, CodeQL reads bodies, and without the declaration the
*body* — not the summary — would decide template 7's negative, which is
precisely the disagreement the template is built to expose.

### Joern

`modeling.sc` is a second script beside `kernel.sc`, which stays untouched, as
the preregistration requires. It loads
`adapters/joern/semantics/model-python.semantics` through the distribution's
own `FullNameSemanticsParser`, layers it on top of `DefaultSemantics()` — the
operator flows are not the model and dropping them would break propagation
this matrix is not measuring — and runs `reachableByFlows` under the resulting
`EngineContext`.

Two properties of the pinned 4.0.610 semantics parser were found by probing it
rather than assumed, and both **fail silently**, producing a well-formed empty
model instead of an error:

- **A blank line anywhere in the file drops every declaration.** The same nine
  declarations parse as nine with no blank line and as zero with one.
- **`#` opens a comment; `//` does not.** A `//`-commented file parses to zero.

A model that parses to nothing is the preregistration's *missing model* arm —
a benchmark defect, never an outcome — so `modeling.sc` raises on an empty
parse and a unit test asserts the committed file has neither a blank line nor
a `//` comment.

Category E is the one selector shape that differs: its source is
`cpg.method.nameExact(...).parameter.index(1)` rather than a call, because the
handler is never called. The runner picks the shape from the *template
identity*, never from a fixture's tags and never from an observed result.

The committed semantics file declares three entities, not nine: `clean.scrub`'s
`NilSemantics` for category Z and the two `Store` mappings for category B.
Categories P and O declare nothing, because
[Amendment A2](modeling-matrix.md#a2--2026-08-26-joerns-propagator-and-summary-categories-are-not-load-bearing)
moved their cells to unsupported activation, and an artifact must not declare a
category its partition declines. What the pre-amendment file declared, and what
its declarations measured, is recorded under
[What the amendments were made of](#what-the-amendments-were-made-of).

### Semgrep CE

`pattern-sources`, `pattern-sinks`, and `pattern-sanitizers` only — no
propagator and no store vocabulary, because P, O, and B are `unsupported` for
CE by the partition, and
[Amendment A3](modeling-matrix.md#a3--2026-08-26-semgreps-sanitizer-selectivity-cell-is-undecidable-by-construction)
declines template 6 inside category Z as well. That amendment changes no
declaration here: template 6's subject is the deliberately *undeclared* sibling
`sanitize`, so what it removes is an assertion, not a model entry. Nothing in this rule is templated: the kernel rules carry
endpoint placeholders because the endpoints are a property of each fixture,
whereas here the endpoint identities *are* the model, so the committed rule
states them literally. `options: taint_assume_safe_functions: true` is the
load-bearing-model requirement, and the runner refuses a modeling rule without
it.

## Results

Four runs, one per adapter, sequential, on the pinned distributions, under the
partition **as amended** by A2 and A3. Three of the four are the original runs
at fixture revision `sha256:32bbebe…`; Joern's was re-taken when the JavaScript
row landed a modeling-specific endpoint rule that moved one of its cells, and
carries the later revision. Nothing else about it changed — same semantics
file, same script, same `configuration_hash`. Every raw evidence document is retained under
`reports/raw/<tool>-python-modeling/`. These are the first modeling numbers
this benchmark has ever produced; there is nothing to compare them to and
nothing was re-run toward an expected polarity.

| Adapter | Scored | Correct | FP | FN | `unsupported` | `inconclusive` | `configuration_hash` |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Bifrost v0.10.6 | 4 | **4** | 0 | 0 | 20 | 0 | `578414e1…` |
| CodeQL 2.26.3 | 24 | **24** | 0 | 0 | 0 | 0 | `cd3c4fee…` |
| Joern 4.0.610 | 16 | **14** | 0 | 2 | 8 | 0 | `f7f9d9d5…` |
| Semgrep CE 1.174.0 | 10 | **10** | 0 | 0 | 14 | 0 | `a2eefdc0…` |

Two of those denominators moved with the amendments, and moved *before* these
runs were taken rather than after: Joern's from 24 to 16 (categories P and O
declined), Semgrep's from 12 to 10 (template 6 declined). Neither adapter's
scored cells changed their outcome as a result — what the amendments removed
from the scored set is exactly what the pre-amendment run had reported as
Joern's two false positives and Semgrep's one false negative, and those
observations are kept below rather than deleted.

The three-way distinction, stated explicitly because it is the one this tier
is most likely to blur:

- **`unsupported` (42 cells)** is capability coverage, decided from the
  template identity *before* the tool was invoked, with the preregistration's
  rationale retained verbatim beside the report. It is never a negative and
  never a false negative, and it reduces nobody's denominator: a tool that
  declines a category simply has no assertions in it.
- **`inconclusive` (0 cells)** would be execution coverage, decided *after* the
  run, and is never `not-reached`. This matrix has none.
- **Missing model (0 cells)** is unrepresentable: the runner refuses to start
  without the artifact, and `modeling.sc` refuses a semantics file that parses
  to nothing.

### Per category

| Category | Bifrost | CodeQL | Joern | Semgrep CE |
| --- | --- | --- | --- | --- |
| S — sources and sinks | 4/4 | 4/4 | 4/4 | 4/4 |
| P — propagators | *unsupported* | 4/4 | *unsupported* (A2) | *unsupported* |
| Z — sanitizers | *unsupported* | 4/4 | 4/4 | 2/2 (template 6 *unsupported*, A3) |
| O — summaries | *unsupported* | 4/4 | *unsupported* (A2) | *unsupported* |
| E — entry points | *unsupported* | 4/4 | 4/4 | 4/4 |
| B — persistence | *unsupported* | 4/4 | 2/4 (2 FN) | *unsupported* |

### The mismatches, one by one

Two mismatches remain in the amended partition. Both are Joern's, both are
false negatives, and both are in category B.

**Joern, templates 11 and 12 positives — false negatives.** `put` maps its
value into its store receiver and `get` maps its receiver to its return, as
the preregistration specifies, but the write and the read are in two different
procedures and the engine does not link the two uses of the module-level
`Store` identifier. The model declares the boundary and the analysis does not
close the roundtrip. Both negatives are correct, so this is a clean
"declared but not activated" reading rather than a coin flip.

### One cell corrected after publication

**Joern, template 1 negative — was `inconclusive`, is `not-reached`.** The
declared source `fetch_remote` has no call site in that fixture, which is the
whole point of the negative, and the first run recorded "resolved 0 source
node(s) and 1 sink node(s); the run never observed both benchmark-controlled
endpoints" as `inconclusive` — the kernels' rule, applied uniformly rather than
special-cased for this tier.

That uniformity was wrong for this tier, and the JavaScript row said so with a
population of its own in which several negatives are constructed the same way.
An absent **declared** endpoint is the content of a modeling negative, not an
incomplete run; only an empty extraction (`method_count == 0`) is incomplete.
The modeling path now carries `JoernEndpointRule::AbsenceIsTheAssertion` — the
kernels keep `BothMustBeObserved`, unchanged — the endpoint counts are retained
as a diagnostic rather than converted, and `reports/joern-python-modeling.json`
has been re-run under it. One cell moved, from `inconclusive` to `not-reached`,
and Joern's category S is four assertions rather than three. This is a runner
correction and not an amendment: no partition cell, template, or capability
decision changed.

## What the amendments were made of

The partition tables and the template definitions are immutable from the moment
the first analyzer runs, so neither of the findings below was acted on inside a
run. Both were carried through the preregistration's own amendment procedure —
[A2](modeling-matrix.md#a2--2026-08-26-joerns-propagator-and-summary-categories-are-not-load-bearing)
and
[A3](modeling-matrix.md#a3--2026-08-26-semgreps-sanitizer-selectivity-cell-is-undecidable-by-construction)
— and the runs above were then taken under the amended partition. What follows
is the evidence those amendments were made of, including the pre-amendment
results that motivated them. Those results are no longer this matrix's numbers,
and they are kept because a capability reclassification is only auditable if
the measurement behind it stays on the record.

**Pre-amendment run (Joern 24 scored, Semgrep 12 scored).** Joern decided 19 of
24, with two false positives — template 4's negative and template 8's negative
— two false negatives in category B, and one `inconclusive` (template 1's
negative, since corrected as described above). Semgrep decided
11 of 12, its single false negative being template 6's positive. The two Joern
false positives and the Semgrep false negative are precisely the cells the
amendments reclassified; the remaining outcomes are unchanged in the runs
above, cell for cell.

**1. Joern's category P and O are not load-bearing on the pinned build.** The
preregistration scores both, and `docs/adapters.md` justifies not gating Joern
on the ground that *"a Joern method with no `FlowMapping` propagates nothing"*.
Probed against 4.0.610, that is false: with `opaque.carry` removed from the
semantics file the propagator positive is still `reached`, because the engine's
default already carries the argument through the reflective body's unmodeled
`getattr` and unknown-callee calls. By
[the load-bearing-model requirement](modeling-matrix.md#the-load-bearing-model-requirement)'s
own rule — *"a cell the default already decides is not a measurement"* — those
cells are decided by the default rather than by the model. Two pre-amendment
results are the same fact seen from the scored side: template 4's negative was
reported `reached` even though the declaration maps position 1 only — Joern
reports that flow with `select` removed from the semantics entirely — and
template 8's negative was reported `reached` because the destination access
path of `"bridge.py:<module>.deposit" 1->2 "payload"` is not honored: the
retained flow was `dfb_source()` → `box` → `box.spare`, the whole object
tainted and the sibling attribute inheriting it. The preregistration had marked
that cell *to be verified at implementation*; it is verified, negatively.

Joern does have a `NilSemantics.where(…)` surface that could express a
require-model fallback; adopting it would be a configuration change with its
own consequences (it would cost template 6's positive the way Semgrep's option
does), so **A2** declines the two categories rather than reconfiguring the
engine. Category Z stays scored, because `NilSemantics` was demonstrated
genuinely load-bearing — the probe in the table below.

**2. Semgrep's category Z rationale and its load-bearing requirement
disagree.** The preregistration's Z cell verifies that *"`pattern-sanitizers`
on `scrub(...)` suppresses a finding that the same rule reports without it"*
and, in the same cell, mandates `taint_assume_safe_functions: true`. Both hold
individually and not together: with the option set, removing
`pattern-sanitizers` changes nothing, because the option already suppresses the
flow through `scrub(...)`. The declaration is load-bearing only with the option
off. Category Z's negatives are therefore decided by the option rather than by
the sanitizer declaration on the configuration the cells are actually scored
under.

The pre-amendment run showed the other half of the same option: template 6's
positive, `dfb_sink(sanitize(dfb_source()))`, routes through the deliberately
*undeclared* sanitizer-shaped `sanitize`, and the option carries taint through
no undeclared call at all — so the flow was dropped before the name heuristic
the pair exists to catch could ever be tested, and the cell was recorded as
CE's only false negative. With the option off the same rule reports it, but the
option is mandatory. **A3** therefore declines template 6 alone, by a
template-level override, and leaves template 5 scored: the cell is undecidable
by construction in one CE invocation rather than a capability CE lacks.

## Load-bearing verification

A modeling assertion is only evidence of activation if the tool's behavior
*without* the model would differ. One demonstration per adapter, on a scored
category, run against the committed fixtures.

| Adapter | Category | Probe | With the declaration | Without it |
| --- | --- | --- | --- | --- |
| Bifrost | S | the two declared endpoint entries removed from the `.rqlp` | `declared-source-positive` 1 finding, `declared-sink-positive` 1 finding | 0 and 0 |
| CodeQL | P | `PythonModelingProbe.ql` — the committed query with template 3's propagator step removed | `opaque-propagator-positive` 1 finding | 0 |
| Joern | Z | `clean.scrub`'s `NilSemantics` entry removed from the semantics file | `sanitizer-kill-negative` 0 flows | 1 flow |
| Semgrep CE | S | `fetch_remote(...)` and `record(...)` removed from the rule | `declared-source-positive` 1 finding, `declared-sink-positive` 1 finding | 0 and 0 |

CodeQL's probe is committed as
`adapters/codeql/python/queries/PythonModelingProbe.ql` so it can be re-run;
it never scores a case, is never named by a case's `tool_model_references`,
and is never bound into a report's `configuration_hash`. The other three
probes are one-line deletions from the committed artifact, reproducible by
making the deletion the table names and re-running that adapter's command.

Joern's demonstration is on category Z rather than P deliberately, and the
reason is Amendment A2: on the pinned build the *only* direction in which a
Joern declaration is load-bearing is the suppressive one, so category Z is the
only Joern category a probe can demonstrate. The corresponding probe on
category P is what established that, and it is the amendment's evidence rather
than a demonstration — which is why P is no longer scored for Joern at all.
