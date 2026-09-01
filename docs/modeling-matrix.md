# Benchmark-controlled taint-modeling matrix

This document is the **preregistration artifact** for twelve taint-modeling
templates, in six balanced categories. It merges before any modeling fixture
exists, before any model file is authored for any analyzer, and before any
number derived from them is published. Its purpose is to fix the definitions
while the outcomes are still unknown.

Nothing in this document is a result. It is a contract about what will be
measured, stated in advance so that the measurement cannot later be shaped
around what the measurement produced.

It closes issue #15 and opens milestone M3.

## What this matrix tests

The propagation kernels — the sixteen classic templates and the thirteen
[challenge templates](challenge-tier.md) — test whether an engine can **follow
flow it can see**. Every construct in them is in the language's own manual, and
an engine with no models at all can score full marks.

This matrix tests something else: whether an engine can **be told things**.
Given equivalent benchmark-supplied models — a source it did not know, a
propagator whose body it cannot read, a sanitizer, a procedure summary, an entry
point, a persistence boundary — does the analysis *activate* them, and does
activation produce the *modeled semantics* rather than something adjacent to it?

Modeling correctness is a different competence from propagation correctness.
An engine can be excellent at one and absent at the other, and pooling the two
would hide exactly that. So the modeling matrix is scored on its own tier and is
never pooled with any core kernel.

Two framings are worth stating before any run, because both will otherwise be
misread:

- **A high modeling score is not a high propagation score.** An engine that
  activates every model but follows no dispatch is a good modeling substrate and
  a weak analysis. The two scorecards answer different questions and are never
  added together.
- **A low modeling score is frequently a product decision, not a defect.** A
  standalone CLI that deliberately ships no external-model catalog will decline
  whole categories here. That decline is recorded as `unsupported` with a
  retained reason, exactly as [the scoring contract](scoring.md) requires, and it
  is not a wrong answer.

## Governance

This section is the load-bearing part of the document. The template definitions
are only worth as much as the discipline around them.

### Preregistration and immutability

**The amendment contract of the [challenge tier](challenge-tier.md#preregistration-and-immutability)
applies to this document verbatim.** Restated so that it cannot be lost in a
cross-reference: this document merges before any modeling fixture is authored.
From the moment the first analyzer executes against the first modeling fixture,
the twelve template definitions below — semantic intent, model declaration,
positive shape, negative shape, negative mechanism, and the per-tool capability
partition — are **immutable**.

A defect discovered after that point is corrected by a documented **amendment**,
never by a silent edit. An amendment:

1. appears in a dated `## Amendments` section at the foot of this document;
2. states what changed, why, and which template IDs and languages it touches;
3. states which already-published freezes it invalidates, if any;
4. is a separate commit from any fixture, model, or result change.

A template that turns out to be badly posed is **retired by amendment**, not
rewritten. Its `template_id` is never reused for different semantics.

The per-tool capability partition tables carry the same immutability, and for
the same reason. A partition decided after a run is not a capability
classification, it is a result being relabelled. If a tool turns out to express
a category the tables here call unsupported, that is an amendment with a date on
it, and the run that revealed it is reported as the run that revealed it.

The challenge tier does not need to change for this document to land, and it is
not changed by it. Nothing here amends `docs/challenge-tier.md`.

### Fairness constraint: standard library only

Modeling fixtures use **only the target language's standard library**. No
frameworks, no third-party dependencies, no build-tool plugins. This is the same
rule the challenge tier states, and here it is doing more work than usual, so it
is worth spelling out why it does not contradict itself.

The challenge tier excludes frameworks because a framework fixture would measure
whether the analyzer ships a model for that framework. This matrix measures
model *activation* — and it does so by supplying the model itself, to every tool
equally, for code that is entirely inside the fixture. The
`Config.fetchRemote()` of template 1 is not a real remote call and does not
pretend to be one; it is an ordinary fixture method whose *only* claim to being
a source is that the benchmark declared it so. That is the whole point. If the
fixture used a real framework entry point, an engine with a shipped model for it
would pass without ever reading the benchmark's model, and the assertion would
stop being about activation.

Framework-shipped coverage is a genuine and separate product question. It is
issue #16's `tool-native` profile, and it is out of scope here.

### Lineage

The category taxonomy — sources and sinks, propagators, sanitizers, opaque
library summaries, framework entry points, persistence boundaries — is the one
[M3 recorded in the milestones](milestones.md#m3-taint-modeling) before any of
this was designed, and it is the standard decomposition used by every
configurable taint engine: CodeQL's models-as-data rows (`sourceModel`,
`sinkModel`, `summaryModel`, `barrierModel`, `neutralModel`), Joern's flow
semantics, Semgrep's `pattern-sources` / `pattern-sinks` /
`pattern-propagators` / `pattern-sanitizers`, and Bifrost's RQLP endpoint sets.
The taxonomy is not invented here; what is invented here is a balanced,
polarity-paired way to *test* it.

Fixtures themselves are original authored code — `fixture_provenance.kind` is
`authored`, origin `DataFlowBench`, revision `m3-modeling-<language>`, license
`MIT`, per [fixture provenance](fixture-provenance.md).

### Initial languages

Java, JavaScript, and Python — the floor issue #15 sets, and the three languages
whose kernels are most mature. Per-language sketches for those three are given
with every template below.

The remaining ten languages are **deliberately not classified in this
document**. The challenge tier classified all thirteen up front because its
constructs are language features, and a language whose cells were classified
later would have had its denominator decided by implementation convenience.
Modeling applicability is a different question: it depends on each analyzer's
declaration surface *for that language*, which is a per-adapter fact, not a
per-language one. Those cells are decided by a later applicability pass with the
same three-way vocabulary the
[applicability matrix](applicability-matrix.md#classification-vocabulary)
already defines. Until that pass merges, no language outside Java, JavaScript,
and Python has a modeling denominator at all — which is different from having a
zero.

## Population mechanics

### A new score tier

`score_tier` gains the value **`modeling`**. This is the opposite of the
challenge tier's decision, and the difference is not arbitrary. Challenge
templates fold into the core because they ask the core's question — can the
engine follow this flow — one notch harder. Modeling templates ask a different
question, so a denominator that mixed them would mean nothing.

The consequences, stated plainly:

- Modeling cases have **their own scorecards**, per language and per adapter.
- They are **never** in a core denominator, in any language, in any release.
- They are never pooled with `core`, `language-extension`, `calibration`, or
  `real-project` populations.
- No headline number combines a modeling score with a kernel score.
- Adding the enum value does not touch any existing freeze. Freeze validation is
  manifest-scoped: a manifest binds the cases and reports of its own release, and
  an added enum value changes nothing a v0.3.0 or v0.4.0 manifest asserts.

### Identifiers

- Templates: `dfb-template-model-<category>-<short>`.
- Cases: `dfb-taint-<lang>-model-<short>-<polarity>`.

Both follow the corpus conventions already enforced by the case schema's `id`
and `template_id` patterns.

### Model profile

Every case in this matrix carries `model_profile: "benchmark-controlled"`. That
is not a formality — **this whole matrix is the benchmark-controlled modeling
instrument.** The profile field says the models came from DataFlowBench and were
supplied equally to every tool.

Its counterpart is issue #16's `tool-native` profile, which evaluates the models
a tool ships on its own. #16 builds on this document's category taxonomy — it
reports tool-native coverage in the same six categories, so the two can be read
side by side — but it supplies **no models**, and it is **out of scope here**.
The two profiles are never combined, as
[the scoring contract](scoring.md#model-profiles) already requires.

### Balanced pairs, for the reason the blind baseline gives

Each of the twelve templates contributes exactly one positive and one minimally
different negative case per language — **24 assertions per language** where all
twelve cells apply. A modeling-population validator enforces the balance; it is
specified below and implemented when the first fixtures land.

The pairing is balanced for exactly the reason
[the scoring contract's blind-baseline section](scoring.md#balanced-pairs-and-the-blind-baseline)
gives for the kernels, and the hazard is sharper here. On the kernels, an engine
that cannot see a construct but answers anyway banks one free true negative per
pair. On this matrix, an engine that **ignores the model entirely** does the
same thing: it answers "no flow" on both cells of every category it did not
activate, collects half the assertions, and looks like it partially supports
modeling. Balanced pairs make that floor visible; per-category
true-positive/false-positive rates, not the raw correct count, are what
distinguish activation from silence.

There is a second, modeling-specific form of the same hazard, and it decides
several partition cells below: an engine whose **unmodeled-call default is
optimistic** will carry taint through a declared propagator whether or not it
read the declaration. Its positive cell is then correct for a reason that has
nothing to do with the model. This matrix therefore requires that, for any
category to be scored for a tool, the tool's modeling configuration must make
the model load-bearing — the default must not already decide the cell. See
[the load-bearing-model requirement](#the-load-bearing-model-requirement).

## The model declaration language

Every template below defines its model in **analyzer-neutral** terms, in exactly
three parts. This vocabulary is the equivalence contract's unit of comparison:
two adapters encode the *same* declaration when all three parts agree.

**Entity identity.** What the declaration binds to, as a
type-plus-member-plus-position triple: the declaring type (or module), the
member name, and — where the role needs it — a parameter position, counted from
**0** for the first declared parameter, with the receiver excluded and the
return value written as `return`. Identity binding is always by this triple,
never by name shape and never by a substring: `Audit.record` and `Audit.discard`
are different entities, and a model for one says nothing about the other. Half
the negatives in this matrix exist to prove that.

**Role.** Exactly one of:

| Role | Meaning |
| --- | --- |
| `source` | the named entity's bound position produces tainted data |
| `sink` | tainted data arriving at the named entity's bound position is a finding |
| `propagator` | taint at the named input position appears at the named output position; the entity's body is irrelevant |
| `sanitizer` | taint arriving at the named input position does not leave the entity at any position |
| `summary` | a propagator for an entity whose body the contract says must be ignored even when it is present |
| `entry-point` | the named entity is an analysis root that is never called from the fixture; the named parameter position is tainted on entry |
| `store-write` | the named entity writes its input position into the named store, under a key given by another position |
| `store-read` | the named entity reads from the named store under a key given by a position, and returns it |

**Binding semantics.** How the role's positions attach: which position is the
input, which is the output, and — for `store-write` / `store-read` — which
store identity the pair shares. Written throughout as `in: <position>`,
`out: <position>`, and `store: <name>`.

`propagator` and `summary` are the same mechanism with different obligations.
A `propagator` model is a *permission* to skip a body the engine may also
choose to read. A `summary` model is an *instruction*: the body is present in
the fixture (fixtures are self-contained and stdlib-only), and the contract says
the analysis must produce the summarized semantics whether or not it read it.
Category O's negatives are what make the difference observable, because there the
body and the summary disagree.

## The twelve templates

Six categories of two. Each template gives its semantic intent, its model
declaration, its positive and negative shapes with the negative mechanism, its
`expected_analysis_capability.kind`, and sketches for Java, JavaScript, and
Python.

Every negative mechanism used below is drawn from the enum the case schema
already carries. No new mechanism is introduced; see
[metadata groundwork](#metadata-groundwork) for why the `sanitizer-kill` value
the design sketch proposed was **not** added.

---

### Category S — declared sources and sinks

The floor of the whole matrix. If a tool cannot be told "this method is a
source", nothing else in this document can be asked of it. Both templates are
one-hop and involve no interesting propagation at all: whatever an engine scores
here is a statement about model binding, not about analysis.

#### 1. `dfb-template-model-declared-source`

**Semantic intent.** A value enters the flow from a benchmark-declared source
API that is *not* `dfb_source`. The fixture contains no other indication that the
value is tainted; the declaration is the only reason it is.

**Model declaration.**

- Entity identity: type `Config`, member `fetchRemote`, position `return`.
- Role: `source`.
- Binding: `out: return`.

**Positive.** `Config.fetchRemote()` returns a value that reaches `dfb_sink`
directly.

**Negative.** The identical flow reads from `Config.fetchLocal()`, a sibling
method on the same type with the same signature and an equally opaque-looking
body, which is **not** declared. `negative_mechanism: unrelated-value`.

Both methods return a constant string in the fixture, so an engine that reads
their bodies learns nothing that distinguishes them. Only the declaration does.

**Capability kind.** `declared-source-activation`.

**Sketches.**

- Java — `class Config { static String fetchRemote() { return "r"; } static
  String fetchLocal() { return "l"; } }`, then `dfb_sink(Config.fetchRemote());`.
- JavaScript — a module-level `const Config = { fetchRemote() { return "r"; },
  fetchLocal() { return "l"; } };`, then `dfb_sink(Config.fetchRemote());`.
- Python — a module `config.py` with `def fetch_remote(): return "r"` and
  `def fetch_local(): return "l"`.

#### 2. `dfb-template-model-declared-sink`

**Semantic intent.** The mirror of template 1. Taint from `dfb_source()` reaches
a benchmark-declared sink API that is not `dfb_sink`.

**Model declaration.**

- Entity identity: type `Audit`, member `record`, position `0`.
- Role: `sink`.
- Binding: `in: 0`.

**Positive.** `Audit.record(dfb_source())`.

**Negative.** `Audit.discard(dfb_source())` — an undeclared sibling with the
same signature. `negative_mechanism: unrelated-value`.

**Capability kind.** `declared-sink-activation`.

**Sketches.** Structurally identical in the three languages: a two-method
`Audit` type (class, object literal, module) whose methods both accept one
string and both drop it.

---

### Category P — declared propagators

The category the whole matrix turns on, because it is where "the engine
activated the model" and "the engine would have said this anyway" are hardest to
tell apart. Both templates are constructed so that the two are distinguishable,
and the construction is stated here rather than left to the fixtures.

#### 3. `dfb-template-model-opaque-propagator`

**Semantic intent.** Taint passes through a helper whose body the analyzer must
**not** need to read, because it demonstrably cannot. The declaration is the
only route from the helper's argument to its result.

**The opaque body shape, and the evidence for choosing it.** The helper's body
routes its argument through a **reflective self-dispatch resolved from a
run-time string** — the construct the challenge tier calls
`dfb-template-chal-reflective-invocation`. That construct is chosen because the
v0.4.0 freeze already establishes, across four engines and three languages, that
none of them follows it.

In the v0.4.0 bound evidence — freeze manifest `reports/freeze.json`, benchmark
revision `306211a` (tag `v0.4.0`), documented in
[`releases/v0.4.0.md`](releases/v0.4.0.md) — the twelve positive cells of
`dfb-template-chal-reflective-invocation` across Java, JavaScript, and Python
contain **zero `reached` outcomes**:

| Analyzer | Java | JavaScript | Python |
| --- | --- | --- | --- |
| Bifrost v0.10.6 | `inconclusive` | `inconclusive` | `inconclusive` |
| CodeQL 2.26.3 | `not-reached` | `not-reached` | `not-reached` |
| Joern 4.0.610 | `not-reached` | `not-reached` | `not-reached` |
| Semgrep CE 1.174.0 | `unsupported` | `unsupported` | `unsupported` |

Bound reports: `reports/{bifrost,codeql,joern,semgrep}-{java,javascript,python}-kernel.json`.
Stated precisely, because the four cells mean four different things: CodeQL and
Joern **definitively answer `not-reached`** in all six of their cells; Bifrost
reports **incomplete analysis** in all three of its; Semgrep **declines by
declared capability** in all three of its, decided from case metadata before the
scan. No engine's `witness_checkpoints` array is non-empty for any of the twelve.
The property this template needs is the weaker and better-supported one: *no
engine reaches the sink through this body on its own*. That is true in twelve of
twelve cells, and — as [`releases/v0.4.0.md`](releases/v0.4.0.md) records
independently for CodeQL — it holds across all eleven languages that have a
reflective-invocation fixture, with not one `reached` anywhere in the freeze.

This is the entire reason the template is assertable. Its positive cell can only
be `reached` if the model was activated.

**Model declaration.**

- Entity identity: type `Opaque`, member `carry`, positions `0` and `return`.
- Role: `propagator`.
- Binding: `in: 0`, `out: return`.

**Positive.** `dfb_sink(Opaque.carry(dfb_source()))`.

**Negative.** `Opaque.block(dfb_source())` — a sibling on the same type, with an
identical reflective body, which is declared as **not** propagating (an explicit
no-flow declaration where the tool has one; otherwise simply undeclared, which
the partition records per tool).
`negative_mechanism: call-context-separation`.

The negative is what catches an engine that treats *any* declared type as
wholly modeled, or that binds a declaration to a type rather than to a member.

**Capability kind.** `opaque-propagator-activation`.

**Sketches.** The three languages express the same opacity through their own
reflective facility, and the divergence from the core kernel's JavaScript
fixture is deliberate and recorded here in advance:

- Java — `static String carry(String v) { return (String)
  Opaque.class.getMethod(name, String.class).invoke(null, v); }` with `name`
  bound from a local string constant to a private identity method.
- Python — `def carry(v): return getattr(_impl, name)(v)`, `name` a local
  string constant.
- JavaScript — `Reflect.get(_impl, name).apply(null, [v])`. The core kernel's
  JavaScript `reflective-invocation` fixture uses a computed-key call
  (`handlers[name](...)`), which is structurally closer to a dispatch table.
  This matrix uses `Reflect` so that the opacity is the same shape in all three
  languages. That is a modeling-matrix fixture decision, it changes nothing about
  the core fixture, and it is stated here so it is not later mistaken for drift.

#### 4. `dfb-template-model-propagator-position`

**Semantic intent.** Positional fidelity of model application. The declaration
names **parameter 1 only** (the second declared parameter); an engine that
applies the model to any tainted argument, rather than to the declared position,
fails the negative.

**Model declaration.**

- Entity identity: type `Opaque`, member `select`, positions `1` and `return`.
- Role: `propagator`.
- Binding: `in: 1`, `out: return`.

**Positive.** `dfb_sink(Opaque.select("clean", dfb_source()))` — taint at the
declared position 1.

**Negative.** `dfb_sink(Opaque.select(dfb_source(), "clean"))` — the identical
call with taint at the undeclared position 0.
`negative_mechanism: call-context-separation`, following the precedent the core
kernel's `dfb-template-argument-position-separation` already sets for
position-distinguished negatives.

`select` carries the same reflective body as `carry`, for the same reason.

**Capability kind.** `positional-propagator-activation`.

**Sketches.** A two-parameter static method / module function / object method in
each language, with the reflective body of template 3.

---

### Category Z — declared sanitizers

The only category whose *negative* is the modeled one. Everywhere else the model
creates a flow; here it removes one. That inversion is the point: an engine can
fake source and propagator activation by being optimistic, but it cannot fake
sanitizer activation by being optimistic.

#### 5. `dfb-template-model-sanitizer-kill`

**Semantic intent.** A benchmark-declared sanitizer suppresses a flow that
otherwise exists.

**Model declaration.**

- Entity identity: type `Clean`, member `scrub`, position `0`.
- Role: `sanitizer`.
- Binding: `in: 0`.

**Positive.** `dfb_sink(dfb_source())` — the flow, direct, with no sanitizer
anywhere on the path. The positive cell of this pair deliberately asks nothing
of the model; it establishes that the flow exists at all, so that the negative's
absence means something.

**Negative.** The **same** flow routed through `Clean.scrub`:
`dfb_sink(Clean.scrub(dfb_source()))`. The declared sanitizer must suppress the
finding. `negative_mechanism: sanitizer`.

`scrub`'s body is the identity function. That is deliberate. A sanitizer whose
body actually sanitizes would let an engine reach the right answer by reading
the body, and the assertion would stop being about the model.

**Capability kind.** `declared-sanitizer-activation`.

**Sketches.** `class Clean { static String scrub(String v) { return v; } }`, and
its object-literal and module equivalents.

#### 6. `dfb-template-model-sanitizer-selectivity`

**Semantic intent.** Sanitizer models bind by entity identity, not by name
shape. Two sanitizer-*looking* calls exist; only one is declared.

**Model declaration.**

- Entity identity: type `Clean`, member `scrub`, position `0`.
- Role: `sanitizer`.
- Binding: `in: 0`.

The sibling `Clean.sanitize` — same type, same signature, same identity body, a
name at least as sanitizer-shaped — is **not** declared.

**Positive.** `dfb_sink(Clean.sanitize(dfb_source()))`. The flow passes through
the *undeclared* sanitizer-looking call and must still be reported.

**Negative.** `dfb_sink(Clean.scrub(dfb_source()))`, through the declared one,
suppressed. `negative_mechanism: sanitizer`.

This is the pair that catches heuristic name matching — an engine that treats
anything called `sanitize`, `escape`, or `clean` as a barrier fails the
positive, and it fails it for a reason worth publishing.

**Capability kind.** `sanitizer-identity-binding`.

**Sketches.** One `Clean` type with two identity methods in each language.

---

### Category O — opaque procedure summaries

Where category P declares "you may skip this body", category O declares "ignore
this body; these are the semantics". The distinction is only observable when the
two disagree, and template 8 is built so they do.

This category generalizes the existing Java calibration case
**`dfb-taint-java-modeled-external`**
(`cases/taint/java/modeled-external-unsupported/case.json`, template
`dfb-template-modeled-external-summary`), whose `ThirdPartyBridge.passThrough`
is exactly an `in: 0, out: return` summary and whose retained Bifrost outcome is
`unsupported` with the reason *"Bifrost's standalone policy CLI has no ambient
external semantic-model catalog; this requires an embedding with explicit
activation."*

**That calibration case stays calibration and is not selected into this
matrix.** It is `score_tier: "calibration"`, it is bound into published freezes
at that tier, and re-tiering it would silently change what those freezes assert.
The modeling matrix authors its own cases; the calibration case remains what it
has always been — the adapter-plumbing precedent that showed this category
needed a tier of its own.

#### 7. `dfb-template-model-summary-through`

**Semantic intent.** An **external-shaped** procedure carries flow per a supplied
summary. External-shaped means: declared in a separate fixture file, named as a
boundary, and covered by a contract clause saying its body must be ignored.

**Model declaration.**

- Entity identity: type `Bridge`, member `pass`, positions `0` and `return`.
- Role: `summary`.
- Binding: `in: 0`, `out: return`.

**Positive.** `dfb_sink(Bridge.pass(dfb_source()))`, with `Bridge` in its own
fixture file.

**Negative.** `dfb_sink(Bridge.hold(dfb_source()))`, where the sibling `hold`
carries an explicit **no-flow** summary. `negative_mechanism:
call-context-separation`.

Both bodies are the identity function. So the *bodies* say flow in both cells and
the *summaries* disagree with each other: an engine that reads bodies reports
both, an engine that activates summaries reports one, and an engine that does
neither reports neither. The three are distinguishable, which is the property a
summary template needs and the reason the bodies are identical rather than
convenient.

**Capability kind.** `procedure-summary-activation`.

**Sketches.** A second fixture file per case — `Bridge.java`, `bridge.js`,
`bridge.py` — containing two one-line identity methods.

#### 8. `dfb-template-model-summary-field`

**Semantic intent.** A **store-through** summary: the declaration says the
procedure writes its first argument into a named field of its second, and the
sink reads that field. The summary's output position is a heap location, not a
return value.

**Model declaration.**

- Entity identity: type `Bridge`, member `deposit`, positions `0` and `1`.
- Role: `summary`.
- Binding: `in: 0`, `out: 1.payload`.

**Positive.** `Bridge.deposit(dfb_source(), box); dfb_sink(box.payload);`.

**Negative.** The identical call, with the sink reading a **sibling field** of
the same object: `dfb_sink(box.spare);`. `negative_mechanism: field-separation`.

`deposit`'s body writes nothing at all, so the field's contents come from the
summary or from nowhere.

**Capability kind.** `store-through-summary-activation`.

**Sketches.**

- Java — `class Box { String payload; String spare; }` and
  `static void deposit(String v, Box b) { }`.
- JavaScript — `const box = { payload: "", spare: "" };`.
- Python — a two-attribute class, or a module-level object with two attributes.

---

### Category E — framework entry points

The category with the sharpest three-way distinction, and the one most likely to
be misread as a failure. A handler that nothing calls is dead code to an engine
without entry-point synthesis. Declining it is correct behavior.

**Stated before any run:** an analyzer with no entry-point synthesis must report
`unsupported` here, **not** `not-reached`. `not-reached` on this category is a
claim that the analysis ran with the declared root and found nothing, which is a
different and much stronger claim than "I cannot make a root out of a
declaration". The per-tool partition below decides which of the two a tool is
entitled to say, and it decides it before the tool runs.

#### 9. `dfb-template-model-entrypoint-parameter`

**Semantic intent.** A handler method that is **never called from anywhere in
the fixture** is declared an entry point with its parameter tainted on entry.
The engine must synthesize a root it was not given by the call graph.

**Model declaration.**

- Entity identity: type `Handler`, member `onRequest`, position `0`.
- Role: `entry-point`.
- Binding: `in: 0` tainted on entry.

**Positive.** `onRequest(input)`'s body is `dfb_sink(input);`. Nothing in the
fixture calls `onRequest`.

**Negative.** A sibling handler `onIgnored(input)` with a byte-identical body,
also never called, and **not** declared.
`negative_mechanism: call-context-separation`.

**Capability kind.** `entry-point-root-activation`.

**Sketches.** In all three languages: one type (class / object literal / module)
with two uncalled one-parameter methods whose bodies each sink the parameter,
and no top-level code that invokes either.

#### 10. `dfb-template-model-entrypoint-selectivity`

**Semantic intent.** Entry-point declarations bind by member identity. Template 9
proves a root can be synthesized; this one proves the synthesis is *selective*
rather than "every uncalled method is a root", which is a common and defensible
whole-program default and one this matrix must be able to see.

**Model declaration.** Identical to template 9, applied to a fixture where
**both** handlers are plausible roots.

- Entity identity: type `Handler`, member `onDeclared`, position `0`.
- Role: `entry-point`.
- Binding: `in: 0` tainted on entry.

**Positive.** `onDeclared(input)` sinks its parameter; declared.

**Negative.** `onUndeclared(input)` sinks its parameter; **not** declared, and
in the same class, with the same signature and the same body.
`negative_mechanism: call-context-separation`.

The pair is the entry-point analogue of template 6: an engine that treats every
public uncalled method as an entry root passes the positive and false-positives
the negative, and the pair reports that as approximation character rather than
as a ranking.

**Capability kind.** `entry-point-identity-binding`.

**Sketches.** As template 9, with both methods in one type.

---

### Category B — persistence boundaries

A write in one procedure and a read in another, linked only by a model that says
they are two ends of the same store. This is the category with the least prior
art in the corpus — nothing in the schema, no policy section, no query
construct, and no fixture addresses it today — so its declaration vocabulary is
defined here from scratch.

#### 11. `dfb-template-model-store-roundtrip`

**Semantic intent.** A tainted value is written into a fixture-local store type
under a key, and read back from a **separate procedure** under a key. The model
links the write and the read as the two roles of one persistence boundary; the
key decides whether the roundtrip closes.

**Model declaration.** Two declarations sharing one store identity:

- Entity identity: type `Store`, member `put`, positions `0` (key) and `1`
  (value). Role: `store-write`. Binding: `in: 1`, `key: 0`, `store: primary`.
- Entity identity: type `Store`, member `get`, positions `0` (key) and `return`.
  Role: `store-read`. Binding: `out: return`, `key: 0`, `store: primary`.

**Positive.** `writeSide()` calls `Store.put("k", dfb_source())`; a separate
`readSide()` calls `dfb_sink(Store.get("k"))`. Same key constant.

**Negative.** The identical pair of procedures with **distinct constant keys** —
`put("a", …)` and `get("b")`. `negative_mechanism: field-separation`, following
the corpus precedent that constant-key separation inside a container is recorded
as field separation.

`Store`'s `put` and `get` have empty bodies. The roundtrip exists only in the
model.

**Capability kind.** `persistence-boundary-activation`.

**Sketches.** A `Store` type with two static no-op methods per language, plus two
top-level procedures. No standard-library map is used: an engine that models
`HashMap.get` would otherwise pass this without reading the declaration, which is
the same trap the fairness constraint exists to avoid.

#### 12. `dfb-template-model-store-separation`

**Semantic intent.** Persistence declarations are **per store instance**. Two
`Store` instances exist; the model links each instance's own write and read, and
does not link across them.

**Model declaration.** As template 11, with the store identity bound to the
receiver instance rather than to the type: `store: <receiver identity>`.

**Positive.** `alpha.put("k", dfb_source())` in one procedure;
`dfb_sink(alpha.get("k"))` in another. Same instance, same key.

**Negative.** `alpha.put("k", dfb_source())` and `dfb_sink(beta.get("k"))` —
same key, **different instance**. `negative_mechanism: object-separation`.

**Capability kind.** `persistence-instance-binding`.

**Sketches.** Two module-level or field-held `Store` instances per language,
constructed once and never reassigned.

---

### Summary table

| # | `template_id` | Neg. mechanism | `expected_analysis_capability.kind` |
| --- | --- | --- | --- |
| 1 | `dfb-template-model-declared-source` | `unrelated-value` | `declared-source-activation` |
| 2 | `dfb-template-model-declared-sink` | `unrelated-value` | `declared-sink-activation` |
| 3 | `dfb-template-model-opaque-propagator` | `call-context-separation` | `opaque-propagator-activation` |
| 4 | `dfb-template-model-propagator-position` | `call-context-separation` | `positional-propagator-activation` |
| 5 | `dfb-template-model-sanitizer-kill` | `sanitizer` | `declared-sanitizer-activation` |
| 6 | `dfb-template-model-sanitizer-selectivity` | `sanitizer` | `sanitizer-identity-binding` |
| 7 | `dfb-template-model-summary-through` | `call-context-separation` | `procedure-summary-activation` |
| 8 | `dfb-template-model-summary-field` | `field-separation` | `store-through-summary-activation` |
| 9 | `dfb-template-model-entrypoint-parameter` | `call-context-separation` | `entry-point-root-activation` |
| 10 | `dfb-template-model-entrypoint-selectivity` | `call-context-separation` | `entry-point-identity-binding` |
| 11 | `dfb-template-model-store-roundtrip` | `field-separation` | `persistence-boundary-activation` |
| 12 | `dfb-template-model-store-separation` | `object-separation` | `persistence-instance-binding` |

## The equivalence contract

This is the section that makes the matrix a benchmark rather than four separate
experiments.

**The claim.** *What* is declared is identical across tools — the entity
identity, the role, and the binding semantics of
[the model declaration language](#the-model-declaration-language). *How* it is
declared is each tool's own native mechanism. A tool that cannot express a
category does not get a translated approximation of it; it takes
`unsupported` for that category, recorded before any run.

**Encoding.** Each adapter encodes the declaration in the surface its own
documentation gives it, in a per-language modeling artifact committed to the
repository and hash-bound into the report's `configuration_hash` the same way
every existing adapter artifact is:

| Adapter | Modeling artifact | Declaration surface |
| --- | --- | --- |
| Bifrost | `adapters/bifrost/policies/model-<language>.rqlp` | RQLP `:analysis` endpoint sets — verified in the committed policies for `:sources` (`:bind return-value`) and `:sinks` (`:dangerous-operand (argument :index N)`); other sections per the partition below |
| CodeQL | `adapters/codeql/queries/<Language>Modeling.ql` (+ any `ext/*.model.yml`) | `DataFlow::ConfigSig` predicates `isSource` / `isSink` / `isBarrier` / `isAdditionalFlowStep`, optionally models-as-data rows |
| FlowDroid | `adapters/flowdroid/summaries/model-java/` (added by [Amendment A16](#a16--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row)) | sources-and-sinks definitions resolved per case from the fixtures' own markers (the kernel mechanism), plus StubDroid summary XMLs — `flow` (`from`/`to` with parameter indices, `Return`, and field access paths) and `clear` stanzas — activated as `-tw STUBDROID -t <dir>` |
| Infer | `adapters/infer/config/model-java.json` (Java only; added by [A13](#a13--2026-09-01-infer-joins-the-modeling-matrix-with-a-field-evaluated-partition-row)) | Pulse `--pulse-taint-config` JSON — `pulse-taint-sources` / `-sinks` / `-propagators` / `-sanitizers` with exact `class_names` + `method_names` matchers, wired through a `pulse-taint-policies` flow whose `sanitizer_kinds` names every declared sanitizer kind |
| Joern | `adapters/joern/queries/modeling.sc` plus a flow-semantics file | query roots over `cpg.method…parameter` and `FlowSemantic` / `FlowMapping` entries |
| Semgrep | `adapters/semgrep/rules/model-<language>.yaml` | `mode: taint` with `pattern-sources` / `pattern-sinks` / `pattern-propagators` / `pattern-sanitizers` |

Like Joern and Semgrep, Infer has no case-level `tool_model_references` key: its
invocation is pinned in the runner and its declarations live inside the single
committed configuration its report's `configuration_hash` binds.

Bifrost and CodeQL cases name their artifact through the `tool_model_references`
keys the case schema already carries — `policy` and `query` respectively. Joern
and Semgrep have no case-level model reference today (both pin their invocation
in the runner, as their READMEs record), and the modeling matrix does not change
that. **No new `tool_model_references` key is required**, because each adapter's
modeling declarations live inside the single per-language artifact its existing
key already names.

### The load-bearing-model requirement

A modeling assertion is only evidence of activation if the tool's behavior
*without* the model would differ. Two of the four adapters have an
unmodeled-call default that would otherwise decide category P and category O
cells on their own:

- **Bifrost.** Every committed kernel policy sets
  `:call-modeling (call-modeling :unmodeled optimistic)`. Under that setting an
  unmodeled call may pass taint through, which would decide template 3's positive
  without reading the propagator declaration.
- **Semgrep CE.** Verified against the pinned CE 1.175.0: with no propagator
  declared at all, a taint-mode rule reports `dfb_sink(prop("clean", t))` — the
  engine's default is to carry taint from any tainted argument to a call's
  result. Setting `options: taint_assume_safe_functions: true` removes that
  default (verified: the same finding disappears).

The contract is therefore: **for a category to be scored for a tool, that tool's
modeling artifact must configure the unmodeled-call default so that the model is
load-bearing** — `require-model`-style behavior where the tool has such a switch,
`taint_assume_safe_functions: true` for Semgrep. Where a tool has no such switch
for a category, the category is `unsupported` for that tool rather than scored,
because a cell the default already decides is not a measurement.

This requirement is why several partition cells below say `unsupported` for a
tool whose declaration *syntax* exists. Syntax that the engine does not lower, or
that a permissive default overrides, is not activation.

## Per-tool capability partition

Preregistered here, in this document, before any modeling fixture or model file
exists — the same discipline `CHALLENGE_SEMGREP_PARTITION` in `src/main.rs`
already applies to the challenge tier, and for the same reason: a partition
decided from a result is not a capability classification.

**Reading the tables.** `supported` means the tool's declaration surface can
express the category and the model can be made load-bearing. `unsupported` means
it cannot, today, on the pinned version — those cells are `unsupported` outcomes
with a retained reason, decided from case metadata before the tool is invoked.
Cells marked **to be verified** could not be checked against the pinned tool
while writing this document; per the rule stated at the head of each table,
**they are treated as unsupported until shown otherwise**, and promoting one is
a dated amendment.

An `unsupported` cell is coverage, never a negative, and never a false negative.
It does not reduce any other tool's denominator, and it does not reduce the
benchmark's — a tool that declines a category simply has no assertions in it.

### Bifrost — v0.10.7 (build `44d9a5be`)

> **Amended.** Category Z was promoted to scored activation by
> [Amendment A9](#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false):
> the sentence this table declined it on — *"Sanitizer lowering is a future
> Bifrost CLI capability."* — was measured and is false. Bifrost's scored set is
> S and Z, four of the twelve templates. P, O, E, and B are unchanged.

Verified surface: the seventeen committed `.rqlp` policies use exactly
`:sources` (with `:bind return-value` and `:labels`) and `:sinks` (with
`:dangerous-operand (argument :index N)` and `:accepts`), under
`(analysis :type taint :mode may :call-modeling (call-modeling :unmodeled
optimistic))`. No committed policy contains a sanitizer, transform, or
external-model section. The build pinned when this document was written —
v0.10.6, since re-pinned to v0.10.7 — was not available at the time; a locally
installed **v0.9.5** binary was inspected and exposes
policy-schema pointers for `/analysis/sanitizers/entries/`,
`/analysis/transforms/entries/` and `/analysis/external_models/entries/`, plus
`call-modeling` values `paranoid | optimistic | require-model`. **A schema that
accepts a section is not proof that the CLI lowers it into the engine**, which is
precisely what the adapter README says is missing, so none of that is treated as
verification.

| Cat. | Decision | Rationale |
| --- | --- | --- |
| S | **supported** | Source and sink endpoint sets are the surface every committed policy already uses, in thirteen languages, with frozen v0.4.0 evidence. Binding is by RQLP selector, which addresses a callee by name and can be language-qualified — enough for the type+member identity the declaration language requires. |
| P | **to be verified — unsupported until shown** | No committed policy declares a propagator or transform, and the adapter README makes no propagator claim. Additionally, every committed policy sets `:unmodeled optimistic`, so the modeling policy must also be shown to accept `require-model` before either P cell is load-bearing. Both must be demonstrated on the pinned build. |
| Z | ~~**unsupported**~~ → **supported** ([A9](#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false)) | Preregistered as unsupported because the adapter README stated it directly: *"Sanitizer lowering is a future Bifrost CLI capability."* (`adapters/bifrost/README.md`). The matrix surfaced this rather than hiding it — DataFlowBench is published by Bifrost's vendor, and a partition that quietly granted its own engine a category its own documentation says is unimplemented would be the single most damaging thing this document could do. Amendment A9 withdrew the claim on a measurement: the `analysis` grammar accepts a `(sanitizer …)` stanza, the declaration suppresses on a completing run, its removal restores the flow with a full witness, and an undeclared sanitizer-shaped sibling is not suppressed. The README sentence was wrong, and correcting it *against* our own engine's preregistered position is the same discipline that recorded it. |
| O | **unsupported** | The adapter README: *"External semantic-model activation requires an embedding with an explicit catalog, so the modeled-external case is reported as `unsupported` by this CLI adapter with an explicit retained reason. It is not a negative result."* The existing `dfb-taint-java-modeled-external` calibration case already carries that retained reason in the frozen smoke report. |
| E | **to be verified — unsupported until shown** | Nothing in the repository or the README describes an entry-root declaration for the policy CLI. |
| B | **to be verified — unsupported until shown** | No persistence-boundary vocabulary is described anywhere for any adapter, Bifrost included. |

Bifrost therefore enters this matrix with **one of six categories scored**. That
is the honest starting position for a standalone policy CLI whose modeling
surface lives in an embedding, and stating it in the preregistration — rather
than after a run — is the point. It holds **two of six as amended**: A9 moved
category Z, and moved it on a measurement that contradicted this adapter's own
documentation rather than on a re-reading of it.

### CodeQL — CLI 2.26.4

Verified surface: the shared `codeql/dataflow` library at the pinned resolution
defines `DataFlow::ConfigSig` with `isSource`, `isSink`, and the defaulted
`isBarrier`, `isBarrierIn`, `isBarrierOut`, and `isAdditionalFlowStep`. The
pinned language packs each ship models-as-data extensible predicates —
`sourceModel`, `sinkModel`, `summaryModel`, `barrierModel`, `neutralModel` — in
`codeql/java-all@9.2.3`
(`semmle/code/java/dataflow/internal/ExternalFlowExtensions.qll`),
`codeql/javascript-all@2.9.0` and `codeql/python-all@7.2.3`
(`semmle/…/frameworks/data/internal/ApiGraphModelsExtensions.qll`). The adapter
uses **no** data extensions today; the query owns the model, which
`adapters/codeql/README.md` states as the design (*"The query owns the CodeQL
model; the case metadata remains analyzer neutral."*).

| Cat. | Decision | Rationale |
| --- | --- | --- |
| S | **supported** | `isSource` / `isSink` over a named callee is what all eleven committed kernel queries already do. |
| P | **supported** | `isAdditionalFlowStep(node1, node2)` expresses arg-position → return-value directly, and positional fidelity is native: the step is written against `call.getArgument(1)` specifically. |
| Z | **supported** | `isBarrier` is a defaulted member of the same `ConfigSig` the adapter already instantiates. |
| O | **supported** | Same `isAdditionalFlowStep` mechanism; the store-through form of template 8 is a step into a field content node. The alternative encoding — `summaryModel` MaD rows — is available in all three packs but is API-graph-keyed and its binding to *fixture-local* types is **to be verified at implementation**; the pack-predicate encoding is the primary and the MaD one is optional, so this cell does not depend on that verification. |
| E | **supported** | `isSource` can name a parameter node of an uncalled method, and CodeQL's data flow does not require a source to be reachable from a call graph root. Selectivity is by the method's identity in the predicate body. |
| B | **supported** | Two `isAdditionalFlowStep` clauses — one from `put`'s value argument to a synthetic store node, one from that node to `get`'s result — conditioned on equal constant key arguments and, for template 12, on the receiver. Expressible in QL without leaving the checked-in pack. |

CodeQL enters with **six of six**, which is unsurprising: a query language whose
data-flow configuration *is* a model declaration surface has no category to
decline. The interesting question for CodeQL is not whether it can be told, but
whether the resulting semantics match — which is what the assertions measure.

### FlowDroid — 2.15.1 (Java only; added by Amendment A16)

> **Added by [Amendment A16](#a16--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row)**,
> per the joining rule the rollout plan states: a new adapter arrives with its
> own preregistered partition row, added by amendment before its first
> modeling run. The row applies to **Java alone** — the pinned CLI analyzes
> JVM bytecode packaged as an APK, so the JavaScript and Python modeling
> populations are outside the adapter's language reach, which is different
> from being declined.

Verified **by execution** against the pinned 2.15.1 jar, on the committed
Java modeling fixtures themselves, before any scored run; the retained probe
evidence is `reports/raw/load-bearing-java-modeling/flowdroid-*.json`,
produced by `scripts/probe-flowdroid-modeling-load-bearing.sh`. The
declaration surface is two-part: the sources-and-sinks definition file the
kernels already use (endpoint identities resolved per case from the
fixtures' own markers and witnessed as Soot signatures from the compiled
classes), and a committed directory of StubDroid summary XMLs activated as
`-tw STUBDROID -t adapters/flowdroid/summaries/model-java` — which
**replaces** the release default's bundled `summariesManual` provider, so the
benchmark's declarations are the only summaries in the run and the
[load-bearing-model requirement](#the-load-bearing-model-requirement) is met
by the invocation shape itself: the engine's only alternative for an
unmodeled call is reading its body, and the opaque bodies carry nothing on
the pinned defaults (probed — the kernel's `reflective-invocation` misses are
the same measurement at core scale).

| Cat. | Decision | Rationale |
| --- | --- | --- |
| S | **supported** | The sources-and-sinks file is the engine's own endpoint mechanism, and identity binding is by exact Soot signature. Probed: the declared `Config.fetchRemote` source flows, the undeclared `fetchLocal` sibling does not. One field quirk worth recording for reproducers: the *EasyTaintWrapper* text format needs a `^` include-prefix line before any entry registers — measured, and one reason the summaries surface was chosen instead. |
| P | **supported** | A StubDroid `flow` stanza expresses `in: <index>` → `out: return` directly, and positional fidelity is native: the `select` summary names parameter 1 and the pinned engine does not apply it to position 0 (`flowdroid-propagator-position-{declared,undeclared}-position.json`). The `carry` declaration is load-bearing in both directions (`flowdroid-opaque-propagator-{with,without}-model.json`). |
| Z | **template 5 supported; template 6 unsupported** | A `clear` stanza is the format's kill declaration: it suppresses template 5's negative on a completing run and deleting it restores the flow through `scrub`'s identity body (`flowdroid-sanitizer-kill-{with,without}-model.json`). Template 6 is undecidable by construction: `SummaryTaintWrapper.isExclusive` answers true for **any method of a class that has summaries**, so the one file that suppresses `scrub` also swallows the undeclared `sanitize` sibling — measured as zero leaks on the positive (`flowdroid-sanitizer-selectivity-undecidable.json`) — and suppression and selectivity cannot coexist in one invocation. The same class-level exclusivity holds for the EasyTaintWrapper surface (`hasWrappedMethodsForClass`), so no alternative encoding rescues the cell. This is Amendment A3's shape, for a different mechanical reason. |
| O | **supported** | Template 7's identical identity bodies decide nothing — the summaries do: `pass` (declared through) is reported, `hold` (explicit no-flow) is not, and deleting the model reports both, which is exactly the three-way distinguishability the template requires. Template 8's field destination is expressible as a StubDroid access path (`out: 1.payload`), the sibling-field read stays clean, and `deposit`'s body writes nothing, so the flow exists only in the model (`flowdroid-summary-field-{with-model,sibling,without-model}.json`). |
| E | **unsupported** | The released CLI derives analysis roots exclusively from the APK manifest's Android components; no per-method entry-root declaration surface exists. Probed: the XML sources-and-sinks format *parses* a `callback` parameter source on the uncalled handler ("Loaded 1 sources") and the analysis still finds zero, because a declaration cannot create a root the manifest does not (`flowdroid-entrypoint-parameter-undeclarable.json`). Correctly `unsupported`, never `not-reached`, per [the category's own rule](#category-e--framework-entry-points). |
| B | **unsupported** | No FlowDroid declaration surface carries a store identity or a key position: sources-and-sinks roles are `_SOURCE_`/`_SINK_`/`_BOTH_`, EasyTaintWrapper lists are taint/exclude/kill per method, and StubDroid positions are parameters, fields, and the return value. The `store:` and `key:` bindings of templates 11 and 12 have no encoding, so the category is declined rather than approximated, as the equivalence contract requires. |

FlowDroid enters with **seven of the twelve templates scored, four of six
categories** — more than any adapter except CodeQL — which is worth a
sentence of framing: the engine whose *kernel* results show heavy
container-conflation and stored-function misses is simultaneously the
second-best modeling substrate in the field. Modeling capability and
propagation capability are different axes, which is this tier's founding
observation.

### Joern — 4.0.614

> **Amended.** Categories P and O were moved to unsupported activation by
> Amendment A2 after the first wave-M1 run measured `FlowSemantic` as
> additive rather than restrictive; Joern's scored set is S, Z, E, B.


Verified surface: the OSS data-flow engine ships a flow-semantics loader —
`io.joern.dataflowengineoss.semanticsloader` with `FlowSemantic`, `FlowMapping`,
`FlowPath`, `ParamOrRetNode`, `NilSemantics`, `NoCrossTaintSemantics`, and
`FullNameSemanticsParser`, plus a `SemanticsParser`/`SemanticsLexer` grammar for
the textual semantics format. Verified by inspecting
`io.joern.dataflowengineoss-<version>.jar` in a locally installed distribution,
which is **4.0.432, not the pinned 4.0.614** — the class surface is expected to
be identical and is **to be confirmed against the pinned distribution at
implementation**, on the same terms as the challenge tier's verified
`maxCallDepth` bound. The committed `adapters/joern/queries/kernel.sc` supplies
no semantics today, which the README states: *"No custom semantics, no
additional propagation or sanitizer models, and no engine configuration are
supplied."* Supplying them for the modeling matrix is a new adapter capability,
scoped to a separate `modeling.sc` so the kernel script is untouched.

| Cat. | Decision | Rationale |
| --- | --- | --- |
| S | **supported** | The kernel script already selects sources and sinks by callee name through CLI parameters; a modeling script selects the declared identities the same way. |
| P | **supported** | `FlowMapping` over `ParamOrRetNode` expresses argument-index → return propagation, and the index is the mapping's own key, so positional fidelity is native rather than emulated. |
| Z | **supported** | `NilSemantics` — a method declared with no flow mappings — is precisely "taint does not leave this entity", which is the `sanitizer` role. |
| O | **supported** | The same semantics mechanism, with an access path on the destination for template 8's `out: 1.payload`. `FlowPath` is the surface; its access-path expressiveness for a field destination is **to be verified at implementation**, and template 8 alone is unsupported for Joern if it cannot be expressed. |
| E | **supported** | `reachableByFlows` takes arbitrary CPG nodes as sources; `cpg.method.fullNameExact(…).parameter.index(1)` is a valid root regardless of whether any call site reaches the method. Selectivity is the query's own predicate. |
| B | **supported** | Two `FlowSemantic` entries — `put` mapping its value parameter into its store parameter, `get` mapping its receiver to its return — leave the key and instance discrimination to the engine, which is the correct division: the model declares the boundary, the analysis decides whether the roundtrip closes. |

### Semgrep CE — 1.175.0 (`--oss-only`)

> **Amended.** Template 6 (sanitizer-selectivity) was moved to unsupported
> activation by Amendment A3: the mandated safe-function assumption and
> selectivity cannot coexist in one invocation. Semgrep's scored set is
> five templates.


This partition is **verified by execution** against the pinned CE binary
(`semgrep 1.175.0`, `--oss-only`), on small Python probes, before any fixture
exists. Each cell below states what was run and what came back.

The existing `CHALLENGE_SEMGREP_PARTITION` precedent applies: cells are decided
from case metadata and the pinned distribution's documented behavior, before
Semgrep is invoked, and no result can talk the runner into or out of the
partition.

| Cat. | Decision | Rationale |
| --- | --- | --- |
| S | **supported** | `pattern-sources` / `pattern-sinks` are what all eleven committed rules already use. Both category-S templates are single-statement and intraprocedural, so they sit inside the CE profile. |
| P | **unsupported** | Verified twice over. First, `pattern-propagators` binds `to:` to a **metavariable**, not to a call's return value: a propagator written `pattern: prop($A,$B) / from: $B / to: prop(...)` produced no finding when the default pass-through was disabled. Second, with the default enabled, CE reports the sink whether taint sits at the declared position 1 or the undeclared position 0 — so both cells of template 4 are decided by the default, not the model, and the [load-bearing-model requirement](#the-load-bearing-model-requirement) is violated either way. Arg→return propagation is outside CE's propagator vocabulary. |
| Z | **supported** | Verified: `pattern-sanitizers` on `scrub(...)` suppresses a finding that the same rule reports without it, and leaves an unrelated direct flow reported. Both category-Z templates are intraprocedural. The rule must set `options: taint_assume_safe_functions: true` so the sanitizer, not the default, is what the cells turn on. |
| O | **unsupported** | Template 7 needs arg→return summary semantics, which P has already established CE cannot express, and puts the summarized procedure in a separate file, which CE's intra-file engine does not cross. Template 8's destination is a *field* of an argument; `to: $L` reaches the whole object, and the pinned CE documents only *"Experimental support for basic field-sensitive taint tracking"* — so the field-separation negative would be decided by CE's heap approximation rather than by the summary. |
| E | **supported** | Verified, and this is the surprising cell: a source written as `patterns: [pattern: "def on_request($P): ...", focus-metavariable: $P]` produced a finding inside the declared handler's body and **no** finding inside a byte-identical undeclared sibling. Both templates in this category are intraprocedural — the handler's body contains the sink — so the absence of a caller is not a problem for an intraprocedural engine, it is the normal case. |
| B | **unsupported** | The write and the read are in two different procedures by construction, and the pinned CE engine has no interprocedural taint at all: `semgrep scan --help` offers `--pro-intrafile` (*"Intra-file inter-procedural taint analysis … Requires Semgrep Pro Engine"*), so the step from `put` to `get` is outside the engine regardless of what is declared. |

Semgrep CE enters with **three of six**, and — worth saying plainly, because the
expectation from the kernels would be the opposite — it enters with a *larger*
share of this matrix than Bifrost does. Modeling capability and propagation
capability are not the same axis, which is the whole reason this tier exists.

### Infer — v1.3.0

> **Added by [Amendment A13](#a13--2026-09-01-infer-joins-the-modeling-matrix-with-a-field-evaluated-partition-row)
> (2026-09-01).** A new adapter joins this matrix with its own preregistered
> partition row, added by amendment before its first modeling run — this is
> that row. Every cell below was decided by **field evaluation executed against
> the committed Java modeling fixtures** before the row existed, with the
> evidence retained under `reports/raw/amendment-a13-infer-partition/`
> (produced by `scripts/probe-infer-modeling-partition.sh`) — acceptance was
> the load-bearing-model requirement, not a lowered bar. Java is the row's
> only language: the pinned distribution executes no JavaScript or Python
> frontend, so those languages have **no Infer modeling denominator at all**,
> which is different from having a zero.

Verified surface: the pinned v1.3.0's one operable taint mode is Pulse's
`--pulse-taint-config` (Quandary is removed from the release), whose
configuration defines `pulse-taint-sources`, `-sinks`, `-sanitizers`,
`-propagators`, `-policies`, and `-data-flow-kinds` — and nothing else. Exact
`class_names` + `method_names` matchers carry the type+member identity the
declaration language requires. Infer has no unmodeled-call default to pin:
where a body is captured, Pulse reads it, which is what decides category O
below.

| Cat. | Decision | Rationale |
| --- | --- | --- |
| S | **supported** | Both templates' four cells decide correctly: exact matchers bind `Config.fetchRemote` and `Audit.record` (position 0) by identity, the undeclared same-type siblings produce nothing, and deleting the source declaration flips the positive. |
| P | **supported — template 3 only** | Template 3 is load-bearing three ways: the reflective body carries nothing unaided, the declared `Opaque.carry` propagator carries it, and the undeclared identical `Opaque.block` does not. Template 4 is overridden out: a Pulse propagator declares an output (`taint_target`) but **no input position** — the measured propagator carries taint from the undeclared position 0 exactly as from the declared position 1, so both cells are decided by the any-argument default, and unknown configuration fields are silently ignored, so no spelling can be trusted to bind the position. |
| Z | **supported** | The sanitizer stanza suppresses on a completing run, its removal restores the flow, and the undeclared `Clean.sanitize` lookalike is not suppressed. One measured quirk is load-bearing for the runner's gate: a sanitizer whose kind is not named in a policy's `sanitizer_kinds` is **silently inert**, so the committed artifact must wire every sanitizer kind or the run is refused. |
| O | **unsupported** | Template 7's identity bodies are captured and read — both cells report with no declaration at all, so the cells are decided by body analysis, and the release has no surface that makes a captured body ignored (`--pulse-taint-opaque-files` is accepted and measured inert for Java). Template 8's `FieldsOfValue` destination is not field-precise: the declared `1.payload` summary taints the sibling `spare` too, so the field-separation negative is decided by the heap approximation rather than by the summary. |
| E | **unsupported** | A source matcher's argument `taint_target` applies at call boundaries only: declared on the uncalled handler's parameter, the analysis synthesizes no root and reports nothing inside the handler's body, and the surface documents no entry-root vocabulary. |
| B | **unsupported** | No store-write/store-read vocabulary and no key discrimination exist anywhere in the configuration surface (the binary's own enumeration is retained beside the probes), and `Store.put`/`Store.get` have empty bodies, so nothing else can carry the roundtrip. |

Infer enters with **three of six categories scored — five of the twelve
templates**, category P by template 3 alone, the same template-level override
mechanism Amendment A3 established for Semgrep's template 6.

### Partition summary

Preregistered, before any modeling fixture exists. `TBV` = to be verified at
implementation, treated as unsupported until shown otherwise.

> **Amended.** [A13](#a13--2026-09-01-infer-joins-the-modeling-matrix-with-a-field-evaluated-partition-row)
> adds the Infer v1.3.0 column — a new adapter's own row, field-evaluated
> before its first modeling run, Java-only — and
> [A16](#a16--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row)
> adds the FlowDroid column on the same terms, preregistered on retained probe
> evidence before its first run. The four preregistered columns are unchanged,
> as amended by A2, A3, and A9.

| Category | Bifrost v0.10.7 | CodeQL 2.26.4 | Joern 4.0.614 | Semgrep CE 1.175.0 | Infer v1.3.0 (A13) | FlowDroid 2.15.1 (A16) |
| --- | --- | --- | --- | --- | --- | --- |
| S — sources and sinks | supported | supported | supported | supported | supported | supported |
| P — propagators | TBV | supported | supported | unsupported | supported (T4 unsupported) | supported |
| Z — sanitizers | unsupported | supported | supported | supported | supported | T5 only |
| O — summaries | unsupported | supported | supported (T8 TBV) | unsupported | unsupported | supported |
| E — entry points | TBV | supported | supported | supported | unsupported | unsupported |
| B — persistence | TBV | supported | supported | unsupported | unsupported | unsupported |
| **Scored today** | **1 / 6** | **6 / 6** | **6 / 6** | **3 / 6** | **3 / 6** | **4 / 6** |

These counts are categories, not scores. A tool with six of six has six
categories' worth of assertions it can get wrong, and a tool with one of six has
declined five categories rather than failed them. Any future summary that reads
this table as a ranking is a misreading of this document.

## The three-way distinction

Issue #15 requires that missing models, unsupported activation, and incomplete
analysis remain distinguishable. Defined precisely, and mapped onto outcomes the
[scoring contract](scoring.md#outcome-interpretation) already carries. They are
never conflated, and none of them is ever a negative.

**Missing model — a benchmark error, impossible by construction.** A modeling
case whose declaration does not exist for an adapter that is supposed to cover it
is a defect in DataFlowBench, not evidence about the analyzer. The
modeling-population validator makes it unrepresentable: for every modeling case
and every adapter, *either* the adapter's modeling artifact contains the
declaration for that case's template, *or* that template's category is
`unsupported` for that adapter **by the partition table above**. There is no
third state, and in particular there is no silent one. Validation fails the
build; it does not produce a result.

**Unsupported activation — the tool cannot accept or activate this category of
model.** Outcome `unsupported`, with the partition's rationale retained verbatim
as the reason, decided from case metadata **before the tool is invoked**. This
is capability coverage. It is never a false negative and never a true negative,
and no aggregate converts it into either.

**Incomplete analysis — the model was activated but the analysis did not
complete.** Outcome `inconclusive`. The tool accepted the declaration and then
failed to produce a decisive answer: it ran out of budget, hit an internal
invariant, or emitted a candidate without a complete witness. This is execution
coverage. It is emphatically *not* `not-reached`: normalizing it would count
incomplete analysis as a negative, which is the one conversion the scoring
contract forbids most explicitly.

Runner failures — a missing binary, a crashed process, a malformed artifact —
remain `runner-error` and are never any of the three.

The distinction between the second and third is the one this matrix is most
likely to blur, so it has a rule: **`unsupported` is decided before the run and
`inconclusive` is decided after it.** If the partition says a tool cannot
activate a category, no execution of that tool can produce anything but
`unsupported` for it. If the partition says it can, no failure to produce an
answer may be reported as `unsupported` — it is `inconclusive`, and the reason is
retained.

## Reporting

Modeling results are their own population, end to end.

- **Reports.** Per language, per adapter:
  `reports/<tool>-<language>-modeling.json`, in the existing result schema, bound
  into the freeze manifest like every other report.
- **Scorecards.** Separate, per language and per adapter, at the `modeling` tier.
  Generated results order the tier alongside the existing four.
- **Never on a kernel card.** A modeling assertion never appears on a
  propagation-kernel scorecard, never enters a core denominator, and is never
  macro-averaged with one.
- **Per category.** Every report breaks results down by the six categories, so
  that "activates sources but not summaries" is readable off the card rather than
  reconstructed from case IDs.
- **The site.** The published site treats modeling as a new population, with its
  own section. That is a later site pass and is out of scope for this document
  beyond stating that the population must not be folded into an existing view.

## Metadata groundwork

Additive schema changes only, made in the same change as this document so that
fixture authoring is unblocked. Every addition was checked against the existing
enum first; nothing already expressible was duplicated.

### New score tier

`score_tier` gains `"modeling"` in both `schemas/case.schema.json` and
`schemas/freeze.schema.json`. Existing freezes are unaffected: freeze validation
is manifest-scoped, and an added enum value changes nothing that a
previously-validated manifest asserts.

The result-generation tier ordering in `src/main.rs` (`SCORE_TIER_ORDER`) is
extended in the same change. That constant decides which tiers get a section on a
generated scorecard, and a tier absent from it would be **silently dropped** from
every generated result rather than reported as an error — so it is registered
here, with the schemas, ahead of the first modeling case.

### No new negative mechanism

The design sketch for this document proposed adding `sanitizer-kill`. It was
checked against the enum and **not added**: `schemas/case.schema.json` already
carries `sanitizer` in `negative_mechanism`, and it has been there since the v2
case contract without ever being used by a case. It means exactly what
`sanitizer-kill` would have meant. Adding a second spelling of an existing value
would have been duplication, and templates 5 and 6 use `sanitizer`.

The twelve negatives use `unrelated-value` (1, 2), `call-context-separation`
(3, 4, 7, 9, 10), `sanitizer` (5, 6), `field-separation` (8, 11), and
`object-separation` (12). `infeasible-path` and `overwrite-kill` are unused by
this matrix.

### No new semantic dimensions

Checked and **not** added. The enum already carries `external-summary`
(categories O and E), `sanitizer` (Z), `interprocedural-flow` (P, O, B),
`heap-field-sensitivity` (templates 8 and 11), and `object-sensitivity`
(template 12). Every category maps onto an existing dimension, so adding one
would have been duplication.

### No new feature tags

Checked and **not** added. `modeled-external` marks every case in this matrix —
the value exists for exactly this purpose and is currently carried by one
calibration case. `summary-required` covers categories P, O, and E;
`sanitized` covers Z; `heap-access-path` covers templates 8, 11, and 12;
`interprocedural-one-hop` covers the rest.

### No new `tool_model_references` key

`tool_model_references` per-tool objects are `additionalProperties: false` with
`policy`, `query`, and `unsupported_reason`. That is sufficient: Bifrost
modeling cases name their `.rqlp` through `policy`, CodeQL cases name their query
through `query`, unsupported cells carry `unsupported_reason`, and Joern and
Semgrep pin their invocation in the runner as they already do. No schema change.

### `expected_analysis_capability.kind`

Not enum-constrained — a free-form string with an optional `notes` sibling — so
no schema change is required and none was made. The twelve kind strings are fixed
in [the summary table](#summary-table) so that fixtures cannot drift. They follow
the corpus convention the existing `external-summary-activation` establishes:
this matrix measures *activation* and *binding*, so its kinds end in
`-activation` (the category can be turned on) or `-binding` (the category binds
to the right entity), rather than the kernels' `-taint` suffix.

### Validator scope, stated now, implemented later

A modeling-population validator is specified here and implemented alongside the
first language's fixtures, because a required-set check that runs before the
fixtures exist would fail against the current corpus. It must enforce:

1. **Balance.** Each language's modeling population contains exactly one
   positive and one minimally different negative case for each applicable
   template — 24 assertions for a full twelve-template language.
2. **Completeness.** The population contains the exact twelve `template_id`
   values above, so an omitted template cannot hide inside a balanced but smaller
   subset. This mirrors the existing Python-parity required-set check.
3. **Tier isolation.** No `modeling` case appears in any core, calibration,
   `language-extension`, or `real-project` selection, and no core selection
   admits a `modeling` case.
4. **Declaration coverage.** For every modeling case and every covering adapter,
   either the adapter's modeling artifact declares that case's model, or the
   case's category is `unsupported` for that adapter by the partition table —
   never neither. This is what makes *missing model* unrepresentable.
5. **Profile.** Every modeling case is `model_profile: "benchmark-controlled"`.

## Rollout plan

**Wave M1 — Java, JavaScript, Python. Complete.** One language per pull
request, after this document merged. Each PR added that language's twenty-four
fixtures and cases, the per-adapter model encodings its partition entitles it
to, the runs, and the language's row in the modeling validator. A wave never
edits a template definition in this document.

| Language | Row | Landed |
| --- | --- | --- |
| Python | [python-modeling.md](python-modeling.md) | first; A2 and A3 are made on its evidence |
| JavaScript | [javascript-modeling.md](javascript-modeling.md) | second; A4 is made on its evidence |
| Java | [java-modeling.md](java-modeling.md) | third; A5 is made on its evidence, and A4's addendum |

All three rows run on the same four runners, the same shared
`adapters/joern/queries/modeling.sc`, and the same twelve templates; a
difference between two rows is a difference between frontends.

**Later — the remaining ten languages,** via the applicability pass described
under [initial languages](#initial-languages). Those languages have no modeling
denominator until that pass merges.

**Adjacent issues.** #16 (tool-native profiles) builds on this matrix's category
taxonomy so the two profiles can be read side by side, and supplies **no
models**. #17 (OpenTaint) and #18 (Semgrep CE) join per their own issues; a new
adapter joining this matrix arrives with its own preregistered partition row,
added by amendment before its first modeling run.

Nothing in this plan makes a language's fixtures conditional on the results any
analyzer produces for it, and no partition cell is revised because a run was
disappointing.

## Invariants

Restating the obligations this tier is most at risk of eroding:

- Modeling cases are `score_tier: "modeling"` and never enter a core
  denominator, in any language, in any release.
- Modeling and propagation-kernel scores are never pooled, never averaged, and
  never presented as one number.
- Benchmark-controlled and tool-native model profiles are never pooled.
- `unsupported`, `inconclusive`, and `runner-error` are capability or execution
  coverage and are never converted into clean negatives.
- A missing model is a benchmark defect that fails validation, never a result.
- Capability partitions are decided before runs and revised only by dated
  amendment.
- Published numbers come only from validated freeze manifests.
- The category partition table counts categories, not correctness, and is not a
  ranking.

## Amendments

Amendment numbers continue the repository's **single** sequence rather than
restarting per document: A1 is in [the challenge tier](challenge-tier.md#amendments),
A6–A8, A10, A14, and A17 are in [the tool-native profile](native-profile.md#amendments),
A11 is in [docs/adapters.md](adapters.md#amendments), and A12, A15, and A18 are in
[the latency tier](latency-tier.md#amendments), so an identifier names exactly
one amendment wherever it is cited. That is why this document's own sequence
reads A2–A5, then A9, then A13 and A16.

### A2 — 2026-08-26: Joern's propagator and summary categories are not load-bearing

**What changed.** Joern's cells for category P (`opaque-propagator`,
`propagator-position`) and category O (`summary-through`, `summary-field`)
move from scored to **unsupported activation**. Its scored modeling set is
now the eight templates of categories S, Z, E, and B.

**Why.** The first wave-M1 run (Python) probed the load-bearing contract and
found that on the pinned 4.0.614, `FlowSemantic` mappings are **additive**
over the engine's default unmodeled-call pass-through and cannot restrict
it: removing the propagator declaration leaves the finding standing, and a
declared positional mapping does not exclude the undeclared position — so a
P or O result scores the engine's optimism, not the model. A summary's
field-destination access path is likewise ignored (the whole object is
tainted), resolving that cell's to-be-verified marker negatively. Category Z
remains scored: `NilSemantics` was demonstrated genuinely load-bearing
(removing it restores the flow). The preregistration's stated justification
for leaving Joern ungated — "a method with no `FlowMapping` propagates
nothing" — was measured false and is corrected by this amendment.

**Tools, templates, and languages touched.** Joern only; templates 3, 4, 7,
8; all wave-M1 languages (the limitation is engine-level, verified on
Python, expected identical elsewhere and to be confirmed by each language's
retained evidence).

**Freezes invalidated.** None. No modeling report is bound by any freeze.

### A3 — 2026-08-26: Semgrep's sanitizer-selectivity cell is undecidable by construction

**What changed.** Template 6 (`sanitizer-selectivity`) moves from scored to
**unsupported activation** for Semgrep CE, by a template-level override; its
category sibling, template 5 (`sanitizer-kill`), remains scored. Semgrep's
scored modeling set is now five templates.

**Why.** The preregistration mandates `taint_assume_safe_functions: true`
so that propagator models stay load-bearing — and that same option
suppresses flow through the *undeclared* sanitizer-lookalike that template
6's positive requires. Selectivity and the safe-function assumption cannot
coexist in a single CE invocation, so the cell's positive is undecidable by
construction rather than by capability: the first wave-M1 run recorded it
as Semgrep's only false negative before this amendment reclassified it.

**Tools, templates, and languages touched.** Semgrep CE only; template 6;
all wave-M1 languages.

**Freezes invalidated.** None.

### A4 — 2026-08-26: the reflective opaque-propagator body is not unfollowable by Joern's `jssrc2cpg`

**What changed.** Nothing in the partition, the templates, or the rollout. This
amendment is an **evidentiary correction**: it withdraws a factual claim the
preregistration made about the opaque body of
[template 3](#3-dfb-template-model-opaque-propagator) and leaves every scored
cell exactly where [A2](#a2--2026-08-26-joerns-propagator-and-summary-categories-are-not-load-bearing)
put it.

**What the preregistration claimed.** Template 3's assertability rests on the
stated property that *no engine reaches the sink through this body on its own*,
argued from the v0.4.0 freeze's twelve `dfb-template-chal-reflective-invocation`
positive cells, in which Joern answers `not-reached` in all six of its. The
preregistration carried that property forward to this matrix's own reflective
body — JavaScript's `Reflect.get(_impl, name).apply(null, [v])` — and concluded
that a `reached` positive there could only mean the model was activated.

**What was measured.** It is false for Joern's `jssrc2cpg` on the pinned
4.0.614. Run `adapters/joern/queries/modeling.sc` over
`cases/taint/javascript/model-opaque-propagator-positive` under the committed
`adapters/joern/semantics/model-javascript.semantics` — which, after A2,
declares **nothing whatsoever** for `Opaque.carry`, or for category P at all —
and the engine still reports one flow from `dfb_source` to `dfb_sink`. The
retained evidence is
`reports/raw/load-bearing-javascript-modeling/joern-opaque-propagator-unmodeled.json`
(`state: analyzed`, `declared_semantic_count: 3`, `flows: 1`), produced by
`scripts/probe-javascript-modeling-load-bearing.sh`. The frontend plus the
engine's default unmodeled-call pass-through carries taint through the
reflective self-dispatch unaided. The v0.4.0 kernel evidence is not contradicted
— that fixture is a computed-key dispatch table, and this one is `Reflect` — so
what is corrected is the *transfer* of the property from one body shape to the
other, for one engine and one frontend.

**Why the scoring is unaffected.** A2 already moved Joern's category-P and
category-O cells to unsupported activation for the stronger reason that
`FlowSemantic` mappings cannot restrict the default pass-through. A `reached`
here is therefore never scored for Joern in the first place, and A4 removes no
cell that A2 had left standing. The three engines whose category-P cells remain
scored are unaffected: CodeQL's `carry` step is demonstrably load-bearing on
JavaScript (`codeql-opaque-propagator-{with,without}-model.sarif.json`: one
result becomes zero), and Bifrost and Semgrep decline category P by partition.

**Tools, templates, and languages touched.** Joern only; template 3 (and, by
the same body, template 4); JavaScript measured directly. The claim is withdrawn
as a *general* one rather than re-asserted for the other languages: the
preregistration's blanket transfer is what was wrong, and each language's
retained evidence now stands on its own.

**Freezes invalidated.** None. No modeling report is bound by any freeze, and
no core or challenge result changes.

#### Addendum, 2026-08-26: the same is true of `javasrc2cpg`

A4 withdrew the claim as a general one and left each language to stand on its
own evidence. Java's row now supplies its own, and it agrees.
`reports/raw/load-bearing-java-modeling/joern-opaque-propagator-unmodeled.json`
runs `adapters/joern/queries/modeling.sc` over
`cases/taint/java/model-opaque-propagator-positive` under the committed
`adapters/joern/semantics/model-java.semantics` — which, after A2, declares
**nothing whatsoever** for category P — and records `state: analyzed`,
`declared_semantic_count: 3`, `flow_count: 1`. The pinned 4.0.614 follows
`Opaque.class.getMethod(target, String.class).invoke(null, value)` through
`Method.invoke`'s `Object[]` argument with no propagator model at all.

The reflective body differs between the two languages — `Reflect.get(…).apply`
in JavaScript, `Method.invoke` in Java — so this is a second, independent
measurement rather than the same one restated. A4's correction is therefore not
`jssrc2cpg`-specific, and the withdrawal stands as the general one A4 already
made it.

**What this addendum changes.** Nothing beyond the record. No partition cell
moves, no denominator moves, and no outcome changes: A2 had already withdrawn
Joern's category-P cells for the stronger reason. See
[the Java modeling row](java-modeling.md#amendment-a4-extended-to-javasrc2cpg).

### A5 — 2026-08-26: Bifrost v0.10.6 accepts `:unmodeled require-model`

**What changed.** Nothing in the partition, the templates, or the rollout. This
amendment is an **evidentiary confirmation**: it answers, with a measurement,
one of the two facts the preregistration recorded as *to be verified* about
Bifrost, and it moves no cell in either direction.

**What the preregistration said.** Bifrost's category-P cell is `unsupported`
with the reason that *"no committed policy declares a propagator or transform,
and the adapter README makes no propagator claim. Additionally, every committed
policy sets `:unmodeled optimistic`, so the modeling policy must also be shown
to accept `require-model` before either P cell is load-bearing. Both must be
demonstrated on the pinned build."* Two obstacles, joined by "both".

**What was measured.** The second obstacle is cleared. Every committed modeling
policy — Python's, JavaScript's, and Java's — sets
`:call-modeling (call-modeling :unmodeled require-model)`, and the pinned
v0.10.6 (build `18d09c57`) evaluates such a policy to completion rather than
rejecting the setting. Java's run is the retained demonstration:
`reports/raw/load-bearing-java-modeling/bifrost-require-model-accepted.json`
records the committed `model-java.rqlp` evaluated with an empty `diagnostics`
array and one finding on template 1's positive. The runner has enforced the
setting since the infrastructure landed
([the load-bearing-model requirement](#the-load-bearing-model-requirement)), and
`the_java_modeling_artifacts_are_load_bearing` in `src/main.rs` keeps it true.

**Why no cell moves.** The *first* obstacle is untouched. Nothing here shows
that a propagator or transform section lowers to a flow step on the pinned
build, and no committed policy declares one — a modeling policy that did would
violate this document's own rule that an artifact never declares a category its
partition marks unsupported. Category P therefore stays `unsupported` for
Bifrost. Bifrost's category-S cells, the only ones its partition scores, were
already scored, so this confirmation changes no denominator, no outcome, and no
published number.

**Why it is recorded at all.** Because the preregistration asked for it by name.
A *to be verified* note that is quietly satisfied and never written down is
indistinguishable from one that was never checked, and the next reader deciding
whether Bifrost's category P can be promoted needs to know which of the two
obstacles is still standing.

**Tools, templates, and languages touched.** Bifrost only; no template; Java
measured directly, with Python's and JavaScript's committed policies carrying
the same setting.

**Freezes invalidated.** None. No modeling report is bound by any freeze, and
no core or challenge result changes.

### A9 — 2026-08-27: Bifrost's sanitizer category is promoted; the README's lowering claim was false

**What changed.** Category Z — declared sanitizers — moves from `unsupported` to
scored for Bifrost. Its two templates, 5 (`sanitizer-kill`) and 6
(`sanitizer-selectivity`), join category S's two, so this adapter's scored set
goes from two of the twelve templates to four, and from one of six categories to
two. Categories P, O, E, and B are untouched.

**What the preregistration said.** Category Z was declined on a quotation, not a
measurement: *"The adapter README states it directly: 'Sanitizer lowering is a
future Bifrost CLI capability.'"* The reasoning attached to it was explicitly
about publishing discipline — a partition that granted its own vendor's engine a
category the vendor's own documentation called unimplemented would be the most
damaging thing this document could do. That reasoning was right. The sentence it
rested on was wrong.

**What was measured.** On the v0.10.7 build `44d9a5be416432bf8ed414afd3ea0031245ebb57`,
against the committed fixtures of both category-Z templates, in all three of
wave M1's languages:

- **The grammar accepts the stanza.** `(analysis … :sanitizers (endpoint-set
  :entries [(sanitizer :id … :selector (rql …) :input (argument :index 0)
  :output return-value :removes [attacker-controlled])]))` evaluates with an
  empty `diagnostics` array. This is not a schema-pointer inspection of the kind
  the preregistration refused to treat as verification; it is the CLI running
  the policy.
- **The declaration suppresses, on a run that completes.** Template 5's negative
  — the flow routed through the declared `scrub` — reports zero findings with
  `completion: complete`. A suppression produced by an incomplete analysis would
  be vacuous, so the completion is part of the claim.
- **Removing the declaration restores the flow, with a full witness.** The same
  fixture under a policy identical but for the deleted `:sanitizers` section
  reports the flow again, `certainty: definite`, `completeness: complete`, and a
  strong source-to-sink anchor. The declaration is load-bearing in the sense
  [the load-bearing-model requirement](#the-load-bearing-model-requirement)
  means: the cell is decided by the model, not by the engine's default.
- **The binding is by declared identity, not by name shape.** Template 6's
  positive routes the flow through the *undeclared* `sanitize` — same signature,
  same identity body, a name at least as sanitizer-shaped — and is still
  reported; its negative, through the declared `scrub`, is suppressed. An engine
  that treated anything sanitizer-shaped as a barrier would fail this pair, and
  it does not.

All four cells decide correctly in all three languages. The evidence is retained
under `reports/raw/amendment-a9-bifrost-sanitizer/`, produced by
`scripts/probe-bifrost-sanitizer-lowering.sh`, which is the same
run-it-twice shape as the per-language load-bearing probes beside it.

**Why the other four cells do not move.** They were re-examined on the same
build, by enumerating which `analysis` sections the grammar accepts, and the
answer separates them into two kinds:

- **E and B have no surface at all.** `:entry-points`, `:entry_points`,
  `:stores`, and `:persistence` are each rejected with *unknown field … for
  `analysis`*. The preregistration's *to be verified* note for both categories
  stands exactly as written.
- **P and O have adjacent sections whose lowering is unshown.** `:transforms`
  and `:external-models` are accepted fields, and a `transform` entry is a
  label-rewriting declaration (*"transform requires at least one removed or
  added label"*) rather than the argument-position → return-value propagation
  category P declares. Acceptance is not lowering — the rule this document
  applied to a v0.9.5 schema pointer applies here too — and no committed policy
  declares either section. Both stay `unsupported` until something measures
  them, which is a different amendment than this one.

**The README is corrected, not quietly.** `adapters/bifrost/README.md` no longer
states that sanitizer lowering is a future capability; it records what was
measured and points here. One consequence is left standing deliberately: the
tool-native profile's category-Z cell
([docs/native-profile.md](native-profile.md#partition-summary)) quotes the
retired sentence in its own rationale. That cell's *outcome* does not depend on
it — the standalone CLI ships no source or sink endpoint catalog, so no native
template can produce a finding regardless of what the CLI can be told — but its
wording now cites a claim this amendment withdrew. Correcting a tool-native
partition cell is that document's own dated amendment, and it is not this one's
to make.

**Why this direction of correction matters.** Every amendment before this one
moved a cell *away* from scored, or confirmed a fact and moved nothing. This one
grants a category to the engine published by this benchmark's own vendor, which
is the direction in which a partition is least trustworthy. That is why the
measurement is four-way rather than two-way — accept, suppress, restore, and
discriminate — why the raw evidence is retained rather than described, and why
the negative result about `:transforms` and `:external-models` is recorded in
the same breath.

**Tools, templates, and languages touched.** Bifrost only; templates 5 and 6;
Python, JavaScript, and Java measured directly, and all three committed policies
carry the sanitizer declaration.

**Freezes invalidated.** None. No modeling report is bound by any freeze, and no
core or challenge result changes. The scored evidence for the promoted cells
lands with the next evidence re-run; until it does, the retained modeling
reports predate this amendment and record category Z as `unsupported`.

### A13 — 2026-09-01: Infer joins the modeling matrix with a field-evaluated partition row

**What changed.** The matrix gains a fifth adapter. Infer v1.3.0 — already
adapted for the C, C++, and Java propagation kernels
([`adapters/infer/README.md`](../adapters/infer/README.md)) — takes its own
partition row, on the path [the rollout plan](#rollout-plan) preregisters: *"a
new adapter joining this matrix arrives with its own preregistered partition
row, added by amendment before its first modeling run."* This is that
amendment. No cell of any other adapter moves, and no template definition
changes.

**The row, and its language.** Categories **S**, **P**, and **Z** are scored —
category P by **template 3 alone**, with template 4 declined by the same
template-level override mechanism [A3](#a3--2026-08-26-semgreps-sanitizer-selectivity-cell-is-undecidable-by-construction)
established — and categories O, E, and B are unsupported. The full rationale
table is [the Infer partition section](#infer--v130) above. The row exists for
**Java alone**: the pinned distribution executes no JavaScript or Python
frontend, so those languages have no Infer modeling denominator at all — which
is different from having a zero, and the runner refuses to shape a run for
them rather than writing an empty report.

**How the cells were decided.** By **field evaluation executed against the
committed Java modeling fixtures**, before this row existed and before any
Infer modeling run — retained verbatim under
`reports/raw/amendment-a13-infer-partition/`, produced by
`scripts/probe-infer-modeling-partition.sh`. Acceptance was
[the load-bearing-model requirement](#the-load-bearing-model-requirement)
applied without lowering: every scored cell shows the three-way property —
declared model enables or suppresses, removal flips it, undeclared lookalike
does not move — and every declined cell retains the measurement that declines
it. The decisive probes:

- **S** — `class_names` + `method_names` matchers bind by exact type+member
  identity; deleting the `Config.fetchRemote` declaration flips template 1's
  positive to silence; the undeclared siblings produce nothing.
- **P** — template 3's positive is silent with no propagator (the reflective
  body is not followed unaided), reported with the declared `Opaque.carry`,
  and silent through the undeclared identical `Opaque.block`. Template 4's
  negative is the cell that fails: with the `select` propagator declared, the
  flow is reported with taint at the **undeclared position 0** exactly as at
  the declared position 1 — the surface has no input-position vocabulary, and
  a hypothetical spelling of one is **silently ignored** rather than rejected.
- **Z** — suppression, restoration, and identity-selectivity all measured. A
  fourth probe pins the quirk the runner now gates: a sanitizer whose kind no
  policy's `sanitizer_kinds` names is silently inert.
- **O** — template 7's cells report through the captured identity bodies with
  no declaration at all (`--pulse-taint-opaque-files` measured inert for
  Java), and template 8's `FieldsOfValue` summary taints the sibling field.
- **E** — the declared entry-point source on the uncalled handler synthesizes
  no root: zero findings.
- **B** — no store vocabulary exists to probe; the binary's own enumeration of
  its configuration surface is retained as `pulse-taint-config-surface.txt`.

**What lands with the row.** Per the rule A8 stated — a promoted or newly
scored cell lands the runner that scores it in the same pull request —
`run-infer-modeling --language java` lands with this amendment: partition
consulted before invocation, five outcomes retained distinctly, witnessed
identity (the kernel witness, which refuses a binary that is not the pinned
release), per-case `capture`/`analyze` phase timings, and a load-bearing gate
that refuses a configuration with no `pulse-taint-policies`, an unwired
sanitizer kind, or a substring `procedure` matcher — all three silent-failure
shapes measured in the probes. The committed artifact is
`adapters/infer/config/model-java.json`, and it declares exactly the scored
categories: the `carry` propagator but not `select`, and nothing for `Bridge`,
`Handler`, or `Store`.

**Templates and languages touched.** All twelve templates for the new Infer
column; `java` alone. No other tool's cells change.

**Freezes invalidated.** None. No published freeze binds an Infer modeling
report; the v0.6.0 freeze is untouched.

### A16 — 2026-09-01: FlowDroid joins the modeling matrix, with a Java-only partition row

**What changed.** The matrix gains its sixth adapter. FlowDroid 2.15.1 — the
adapter [issue #99 landed over the Java and Kotlin expanded cores](adapters.md) —
takes its own preregistered capability partition row, added here per
[the rollout plan's joining rule](#rollout-plan): *"a new adapter joining this
matrix arrives with its own preregistered partition row, added by amendment
before its first modeling run."* This amendment is that row, and it merged
with the probe evidence retained and **before** the first scored modeling run
of the adapter. No existing adapter's cell moves; no template changes.

**The row is Java-only, and the partition gains nothing for the other
languages.** The pinned CLI analyzes JVM bytecode packaged as an APK.
JavaScript and Python — the other two wave-M1 modeling languages — are outside
the adapter's language reach, so those combinations have **no FlowDroid
modeling denominator at all**, which is the applicability-matrix distinction
(inapplicable, not zero, not declined) applied to an adapter dimension. The
runner refuses `run-flowdroid-modeling` for them outright.

**The partition, preregistered on evidence.** The full row and its rationale
table are in [the partition section](#flowdroid--2151-java-only-added-by-amendment-a15);
in summary: categories S, P, and O supported; category Z split at the template
level — template 5 (`sanitizer-kill`) scored, template 6
(`sanitizer-selectivity`) unsupported because the summary resolution's
class-level exclusivity makes suppression and selectivity undecidable in one
invocation, the same shape as
[Amendment A3](#a3--2026-08-26-semgreps-sanitizer-selectivity-cell-is-undecidable-by-construction)
for a different mechanical reason; categories E and B unsupported (no
entry-root declaration surface; no store/key vocabulary). Seven of twelve
templates, four of six categories.

**Evidence.** Eleven retained probe documents under
`reports/raw/load-bearing-java-modeling/flowdroid-*.json`, produced by
`scripts/probe-flowdroid-modeling-load-bearing.sh` against the pinned,
digest-witnessed jar, on the committed Java modeling fixtures, before any
scored run:

- **Load-bearing in both directions.** Template 3's positive leaks under the
  committed `carry` summary and stops when the declaration is deleted;
  template 5's negative is suppressed under the committed `scrub` `clear` and
  leaks through the identity body when it is deleted; template 8's positive
  exists only under the committed `deposit` summary (`deposit`'s body writes
  nothing).
- **Identity and positional binding.** Undeclared siblings do not activate
  (`fetchLocal`, `block`, `hold`, the sibling field `spare`), and the
  positional declaration `in: 1` is not applied to position 0.
- **The declined cells' grounds are measured, not assumed.** Template 6's
  positive is suppressed by class-level exclusivity under the committed model
  (the undecidability itself), and category E's parameter-source declaration
  parses yet creates no root.

**The load-bearing mechanism, stated for the record.** FlowDroid has no
unmodeled-call *optimism* to disable — the analogue of Bifrost's
`require-model` and Semgrep's `taint_assume_safe_functions` is the invocation
shape itself: `-tw STUBDROID -t adapters/flowdroid/summaries/model-java`
replaces the release default's bundled `summariesManual` provider, so the
benchmark's declarations are the only summaries in the run and an unmodeled
call is decided by its body, which the probes show carries nothing through
the opaque shapes. The runner additionally refuses a run whose committed
summaries no longer carry the declarations the scored cells rest on
(`require_flowdroid_modeling_declarations` in `src/main.rs`).

**Mechanics.** `ModelingTool` gains `Flowdroid`; `MODELING_PARTITION` gains
its six cells and `MODELING_TEMPLATE_OVERRIDES` its template-6 override;
`run-flowdroid-modeling --language java` lands in the same change, reusing the
kernel adapter's APK materialization, witnessed jar identity, leak-line and
failure-banner guards, and echoed-sink reconciliation unchanged. Its timing
sidecars record the three adapter-observable subprocess phases the latency
tier's [Amendment A18](latency-tier.md#amendments) declares for this
population.

**Tools, templates, and languages touched.** FlowDroid only; all twelve
templates (seven scored, five declined); Java only.

**Freezes invalidated.** None. No modeling report is bound by any published
freeze, and no core or challenge result changes.
