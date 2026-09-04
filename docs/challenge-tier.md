# Challenge-tier preregistration

This document is the **preregistration artifact** for thirteen additional
propagation templates. It merges before any challenge fixture exists, before
any analyzer is pointed at one, and before any number derived from them is
published. Its purpose is to fix the definitions while the outcomes are still
unknown.

Nothing in this document is a result. It is a contract about what will be
measured, stated in advance so that the measurement cannot later be shaped
around what the measurement produced.

## Motivation

The sixteen-template core is saturating at the top. In the v0.3.0 freeze,
Bifrost v0.10.5 scores 32/32 core assertions on Java, on JavaScript, and on
Python. A benchmark whose top scorer answers every question correctly has
stopped discriminating: it can no longer rank engines against each other, it
cannot show improvement, and — because DataFlowBench is published by the vendor
of one of the engines it scores — a saturated core invites the reading that the
benchmark was built to be passed.

The remedy is not to retune the existing sixteen. Those templates are frozen
evidence and remain exactly as they are. The remedy is a harder tier with real
headroom, whose definitions are committed to the record *before* the first run,
so that the credibility of the harder numbers does not depend on trusting the
maintainer's after-the-fact account of how the cases were chosen.

The four strata below were selected because each names a well-known limit of
production data-flow engines — dynamic dispatch, higher-order code, container
and access-path depth, and call-depth/context bounds — rather than because any
particular engine was observed to fail them.

## Governance

This section is the load-bearing part of the document. The template
definitions are only worth as much as the discipline around them.

### Preregistration and immutability

This document merges before any challenge fixture is authored. From the moment
the first analyzer executes against the first challenge fixture, the thirteen
template definitions below — semantic intent, positive shape, negative shape,
negative mechanism, and applicability classification — are **immutable**.

A defect discovered after that point is corrected by a documented **amendment**,
never by a silent edit. An amendment:

1. appears in a dated `## Amendments` section at the foot of this document;
2. states what changed, why, and which template IDs and languages it touches;
3. states which already-published freezes it invalidates, if any;
4. is a separate commit from any fixture or result change.

This mirrors the preregistration ethos already adopted for real-project
confirmation (#19): the analysis plan is registered before the data arrives, and
deviations from it are reported as deviations rather than presented as the
original plan.

A template that turns out to be badly posed is **retired by amendment**, not
rewritten. Its `template_id` is never reused for different semantics.

### Lineage

Every template cites the third-party benchmark category whose semantics it
descends from. The fixtures themselves are original authored code —
`fixture_provenance.kind` is `authored`, origin `DataFlowBench`, revision
`m3-challenge-<language>`, license `MIT`, per
[fixture provenance](fixture-provenance.md) — but the *scenario* is not
invented here. Citing the ancestry is what demonstrates that the tier is drawn
from the field's existing account of what is hard, and not shaped around any one
engine's known behavior.

The donor suites are:

- **SecuriBench Micro** — the `refl` (reflection), `aliasing`, `collections`,
  `datastructures`, and inner-class categories.
  <https://github.com/too4words/securibench-micro>
- **OWASP Benchmark** — its indirection tests, where the flow is routed through
  a level of dispatch or container indirection before reaching the sink.
  <https://owasp.org/www-project-benchmark/>
- **NIST Juliet** — the recursion and deep-call CWE variants (the `*_recursion`
  and multi-hop `*_bad`/`*_good` sink-chain flow variants).
  <https://samate.nist.gov/SARD/test-suites/112>
- **Ichnaea** — for the JavaScript higher-order shapes: its account of taint
  through closures, callbacks, and dynamically keyed property access in Node.js
  informs stratum B and template `dfb-template-chal-computed-property`.

These join the donors already recorded in
[benchmark sources](benchmark-sources.md). Donor status confers no authority:
a donor's own ground truth is a design input, never independent ground truth
for a DataFlowBench assertion.

### Fairness constraint: standard library only

Challenge fixtures use **only the target language's standard library**. No
frameworks, no third-party dependencies, no build-tool plugins.

This is a fairness rule, not a convenience one. A fixture that routes taint
through a web framework's request lifecycle measures whether the analyzer ships
a model for that framework — a genuine product question, but a different one.
This tier measures analysis *semantics*: whether the engine can follow a value
through dispatch, capture, containers, and depth when nothing about the code is
proprietary and every construct is in the language's own manual. An engine with
no framework models at all must be able to score full marks here.

Framework and library modeling belongs to the M3 taint-modeling milestone and
its `modeled-external` cases, where the model is the object of study and the
`benchmark-controlled` / `tool-native` profile split already exists to keep it
honest.

### Population: these fold into the core

**Maintainer decision: there is no new score tier.** The challenge templates
carry `score_tier: "core"` and fold into each language's core kernel
population.

The consequence is stated plainly. v0.4.0 is the first **expanded-breadth**
release. Each language's core denominator grows from 16 templates / 32
assertions to (16 + that language's applicable challenge templates), with the
per-language numbers fixed in
[the expanded core denominators](#expanded-core-denominators) below.

The v0.3.0-era 16-template core and the v0.4.0 expanded core are **different
populations and are never compared number-to-number**. "Bifrost scored 32/32 in
v0.3.0 and 51/58 in v0.4.0" is not a regression, not an improvement, and not a
sentence this project will write. The snapshot mechanism already enforces this:
freeze validation is manifest-scoped, each release binds its own manifest, and
published numbers come only from validated freeze manifests. The frozen v0.3.0
evidence therefore remains valid and unamended by anything in this document.

Folding into the core does **not** hide the challenge strata. Within a snapshot,
the existing per-stratum and per-dimension breakdowns keep each challenge
stratum individually visible — the reflection stratum remains its own row, the
depth stratum remains its own row — so a reader can see exactly where an
engine's expanded-core score was won or lost without a separate scorecard being
invented for it.

### Outcome honesty is unchanged

The [scoring contract](scoring.md) applies without modification.
`unsupported`, `inconclusive`, and `runner-error` are capability or execution
coverage and are never converted into false negatives or true negatives.

This matters more on this tier than on the existing core, because more engines
will legitimately decline more of it. An engine that documents reflection as
out of scope takes `unsupported` on stratum A by a declared-capability decision
made from the case metadata *before* the tool is invoked — exactly the mechanism
the Semgrep CE adapter already uses. Declining to model reflection is a design
position, and the benchmark records it as one. It is not a wrong answer, and it
will not be reported as thirteen false negatives.

## Classification and mechanism vocabulary

This document reuses, without change, the three-way vocabulary of the
[remaining-language applicability matrix](applicability-matrix.md):
**`directly applicable`** (the construct exists idiomatically; only surface
syntax changes), **`language-adapted`** (a semantically equivalent native
construct is substituted, preserving `template_id`, polarity, negative
mechanism, and semantic intent, with the adaptation recorded in that language's
kernel contract before fixtures are written), and **`inapplicable`** (no native
construct preserves the intent; the template is excluded from that language's
core denominator with a stated rationale, and any related language-only
construct is routed to a `language-extension` case). Tables abbreviate these
`direct`, `adapted`, and `n/a`.

Every negative mechanism used below is drawn from the mechanism enum the case
schema already carries. No new mechanism is introduced. In particular,
element-level separation in a collection uses `field-separation`, following the
precedent already set by the sixteen-template
`dfb-template-array-element-separation` negatives in every language.

## The thirteen templates

Four strata: A and C and D of three templates each, B of four. Each template
has exactly one positive and one minimally different negative case per language
and model profile — **26 assertions per language where all thirteen cells
apply**, and correspondingly fewer where a cell is inapplicable.

Per-language sketches are given for Java, JavaScript, and Python, the initial
implementation tranche. The remaining ten follow the matrix in
[the applicability matrix for challenge templates](#applicability-matrix-for-challenge-templates).

---

### Stratum A — dynamic dispatch and reflection

**Framing, stated before any run.** On this stratum, every engine is expected to
be wrong somewhere. A sound over-approximating engine will resolve the positive
and also flag the negative; a precise under-approximating engine will refuse the
negative and also miss the positive. Being *right* on both cells of a stratum-A
pair is, for most engines, the luck of having a propensity that happens to match
the shape of that pair.

This stratum therefore measures **approximation character**, not skill. Its
results are reported as such. A per-stratum A score is read as "this engine
over-approximates / under-approximates dynamic dispatch", and it does not crown
a winner. Any future summary that ranks engines by stratum A alone is a
misreading of this document.

#### 1. `dfb-template-chal-reflective-invocation`

**Semantic intent.** Taint reaches a sink through a call whose *target method* is
selected at run time from a string, rather than named at the call site.

**Positive.** A method name is held in a local string constant; the reflective
API resolves that name to a method on a receiver; the tainted value is passed as
the argument; that method's body reaches the sink.

**Negative.** The name constant selects a *sibling* method on the same receiver
which drops its argument and sinks a clean constant instead.
`negative_mechanism: call-context-separation`.

**Sketches.**

- Java — `Method m = C.class.getMethod(name, String.class); m.invoke(o, tainted);`
  where `name` is `"leak"` (positive) or `"drop"` (negative).
- JavaScript — `o[name](tainted);` with `name` bound to a string constant in a
  local variable, so the property is not a syntactic literal at the call site.
- Python — `getattr(o, name)(tainted)`.

**Lineage.** SecuriBench Micro `refl` category; OWASP Benchmark reflection
tests.

**Approximation note.** An engine that treats every reflective call as reaching
every same-signature method will be correct on the positive and produce a false
positive on the negative. An engine that refuses to resolve reflection at all
will be correct on the negative and produce a false negative on the positive.
Both are defensible engineering positions and the report must present them as
paired evidence about the same design choice, never as one engine being "two
better" than the other.

#### 2. `dfb-template-chal-computed-property`

**Semantic intent.** A value is written into a location named by a *computed*
key, and read back through the same computed key. The analyzer must keep the
write and the read associated without the field name ever appearing as a
literal at either access site.

**Positive.** `k` is a local string variable; the tainted value is stored under
`k`; the same `k` is used to read the value back; the result reaches the sink.

**Negative.** The write and the read use two **provably distinct constant keys**,
so no flow exists. `negative_mechanism: field-separation`.

**Sketches.**

- JavaScript — `o[k] = tainted; sink(o[k]);` (negative: `o[k1] = tainted;
  sink(o[k2]);` with `k1`/`k2` distinct string constants).
- Python — `setattr(o, k, tainted); sink(getattr(o, k))`.
- Java — *adapted.* Java has no computed member syntax; the shape is expressed
  through `java.lang.reflect.Field`: `C.class.getDeclaredField(k).set(o,
  tainted)` and a matching `get(o)`.

**Lineage.** SecuriBench Micro `datastructures`; Ichnaea's dynamic property
access.

**Approximation note.** A field-insensitive engine passes the positive and fails
the negative for free, without ever having reasoned about the key. Stratum A
results should be read against the sixteen-template
`dfb-template-same-object-field-separation` outcome, which establishes whether
that engine has field sensitivity at all.

#### 3. `dfb-template-chal-dispatch-table`

**Semantic intent.** A *function value* is selected from a standard-library map
by a string key and then invoked with the tainted value. Unlike template 1, the
callee is an ordinary first-class value, not a reflective handle — the
difficulty is that the call graph edge depends on a map lookup.

**Positive.** The map holds at least two entries; the key selects the entry
whose function forwards its argument to the sink.

**Negative.** The key selects the entry whose function ignores its argument and
returns/sinks a clean constant.
`negative_mechanism: call-context-separation`.

**Sketches.**

- Java — `Map<String, UnaryOperator<String>> table = new HashMap<>();` populated
  with two lambdas; `table.get(key).apply(tainted)`.
- JavaScript — a plain object literal of functions: `const table = { leak: v =>
  sink(v), drop: () => sink("clean") }; table[key](tainted);`.
- Python — a `dict` of functions: `table[key](tainted)`.

**Lineage.** OWASP Benchmark indirection tests; SecuriBench Micro `collections`.

**Approximation note.** An engine that resolves the map contents but not the key
will call both entries reachable and fail the negative. An engine that models
neither will decline both. Read alongside template 8 (`map-iteration`), which
separates "can it model a stdlib map at all" from "can it resolve the key".

---

### Stratum B — higher-order flow

Four templates, because higher-order code has four genuinely distinct
difficulties: environment capture, code stored in the heap, inversion of
control, and unnamed types in the call graph. Collapsing them would hide which
of the four an engine actually handles.

#### 4. `dfb-template-chal-closure-capture`

**Semantic intent.** A tainted local is captured by a closure at closure-creation
time; the closure is invoked later, at a point where the tainted local is no
longer in scope syntactically, and reaches the sink from the captured
environment.

**Positive.** The closure captures the tainted local; a later call site invokes
it with no arguments; the sink is inside the closure body.

**Negative.** An otherwise identical closure captures the *clean* local instead.
`negative_mechanism: unrelated-value`.

**Sketches.**

- Java — a `Supplier<String>` lambda capturing an effectively-final tainted
  local, returned from the creating method and invoked by the caller.
- JavaScript — a factory returning `() => sink(captured)`.
- Python — a nested `def` closing over the enclosing function's local, returned
  and called.

**Lineage.** Ichnaea's closure taint cases; SecuriBench Micro inner-class
categories (the pre-lambda expression of the same capture).

#### 5. `dfb-template-chal-function-field`

**Semantic intent.** A function *value* is stored into an object field, fetched
from that field somewhere else, and invoked with the tainted value. This is heap
indirection of **code**, not of data: the engine must carry a callee through the
same field-sensitivity machinery it uses for values.

**Positive.** `holder.fn` is assigned the sinking function; a different method
reads `holder.fn` and calls it with taint.

**Negative.** A **second holder object**'s field holds the argument-dropping
function, and the call site reads that second holder.
`negative_mechanism: object-separation`.

**Sketches.**

- Java — a class with a `UnaryOperator<String> fn` field; two instances, one
  assigned a sinking lambda and one an argument-dropping lambda.
- JavaScript — `holder.fn = v => sink(v);` then `otherHolder.fn(tainted)` in the
  negative.
- Python — `holder.fn = lambda v: sink(v)`, invoked as `holder.fn(tainted)`.

**Lineage.** SecuriBench Micro `datastructures` and `aliasing`, extended from
data fields to code-valued fields.

#### 6. `dfb-template-chal-callback-registration`

**Semantic intent.** Inversion of control with **zero frameworks**. A callback is
registered into a holder object by one method; a separate driver method,
unaware of what was registered, later iterates the registrations and invokes
each with the tainted value.

**Positive.** The registered callback forwards its parameter to the sink; the
driver supplies the tainted value.

**Negative.** The registered callback ignores its parameter entirely and sinks a
clean constant. `negative_mechanism: unrelated-value`.

**Sketches.**

- Java — `class Registry { List<Consumer<String>> hooks = new ArrayList<>();
  void register(Consumer<String> c) {...} void fire(String v) { for (var c :
  hooks) c.accept(v); } }`.
- JavaScript — an array of functions on a plain object, plus a `fire(v)` method.
- Python — a list of callables on an instance, plus a `fire(v)` method.

**Lineage.** OWASP Benchmark indirection tests; the framework-free reduction of
the listener/handler shape that framework benchmarks usually test through a
framework.

**Note.** This template is the reason the stdlib-only fairness constraint is
worth stating twice. The registration/driver split is exactly what a framework
would normally supply; expressing it in twenty lines of standard library proves
the engine's difficulty is with inversion of control itself, not with a missing
framework model.

#### 7. `dfb-template-chal-anonymous-implementation`

**Semantic intent.** Taint flows through the method of an **anonymous
implementation** of an interface, invoked through the *declared interface type*.
This is distinct from template 4: the difficulty is call-graph construction for
a type that has no name, not environment capture. The fixture's anonymous
implementation captures nothing.

**Positive.** An anonymous implementation of a one-method interface forwards its
argument to the sink; it is instantiated inline, assigned to an
interface-typed variable, and invoked through that variable with taint.

**Negative.** A **second anonymous implementation** of the same interface drops
its argument and sinks a clean constant; the call site invokes that one.
`negative_mechanism: call-context-separation`.

**Sketches.**

- Java — an anonymous inner class implementing a locally declared one-method
  interface (or `UnaryOperator<String>`), `new Handler() { public void
  handle(String v) { sink(v); } }`, invoked as `h.handle(tainted)`.
- JavaScript — an inline anonymous function expression, or an object literal
  with a method, assigned to a variable and invoked through the reference.
- Python — *adapted.* Python has no anonymous classes. Where a `lambda` body
  suffices, the fixture uses a `lambda`; where the sink call cannot be an
  expression, it uses a locally defined single-use class. Whichever is chosen is
  recorded in the Python kernel contract before the fixture is written.

**Lineage.** SecuriBench Micro inner-class categories.

**Approximation note.** An engine that merges all implementations of an
interface — a common and defensible call-graph over-approximation — resolves the
positive and false-positives the negative. This template exists specifically to
make that merge visible, and is reported as approximation evidence in the same
spirit as stratum A.

---

### Stratum C — containers and deep access paths

Standard-library containers only, and no container is used in a way that
requires modeling more than one method of it.

#### 8. `dfb-template-chal-map-iteration`

**Semantic intent.** The tainted value is stored under one key of a
standard-library map, and retrieved by **iterating the map's entries** — never
by a direct `get`. The sink is inside the loop body. The engine must propagate
through the container's iteration protocol rather than through a single
recognizable getter.

**Positive.** Iteration over the map that contains the tainted entry.

**Negative.** Iteration over a **second, disjoint map** that never received the
tainted value. `negative_mechanism: object-separation`.

**Sketches.**

- Java — `for (Map.Entry<String,String> e : map.entrySet()) sink(e.getValue());`.
- JavaScript — `for (const [k, v] of Object.entries(obj)) sink(v);` or a `Map`
  with `for...of`.
- Python — `for k, v in d.items(): sink(v)`.

**Lineage.** SecuriBench Micro `collections`.

**Approximation note.** Engines commonly model `Map.get` as a summarized
propagator while modeling `entrySet`/`items` iteration not at all. The pair
distinguishes "models maps" from "models a list of map method names".

#### 9. `dfb-template-chal-nested-access-path`

**Semantic intent.** A field chain of depth ≥ 3 (`a.b.c.value`). Direct stress
on engines with a bounded access-path length, which is a standard precision/cost
trade-off rather than a bug.

**Positive.** The tainted value is written at the deep path `a.b.c.value` and
read back from the identical deep path.

**Negative.** The read is from a **sibling deep path** of the same depth —
`a.b.c.other`, or `a.b.d.value` — which never received the tainted value.
`negative_mechanism: field-separation`.

**Sketches.**

- Java — three nested classes, `a.b.c.value = tainted; sink(a.b.c.other);` in the
  negative.
- JavaScript — nested object literals.
- Python — three nested instances with plain attributes.

**Lineage.** SecuriBench Micro `datastructures`; xAST's field-sensitivity
scenarios.

**Approximation note.** An engine with a k-limited access path (commonly k = 1
or k = 2) will conflate the positive and negative reads and produce a false
positive on the negative. The pair is designed to make the *bound*, not the
presence, of field sensitivity observable, given that the sixteen-template core
already establishes depth-1 field sensitivity.

#### 10. `dfb-template-chal-element-object`

**Semantic intent.** A collection or array of *objects*; the tainted value sits
in one element's field. The engine must combine element separation with field
separation in a single query — either alone is insufficient.

**Positive.** The sink reads the tainted element's field.

**Negative.** The sink reads a **different element's** corresponding field.
`negative_mechanism: field-separation` — following the precedent already set by
`dfb-template-array-element-separation`, where distinct constant indices are
recorded as field separation in all thirteen languages. Where a language's
adaptation makes the separating step object identity rather than index (see the
matrix), the cell uses `object-separation` and that choice is recorded in the
language's kernel contract before fixtures are written.

**Sketches.**

- Java — `Item[] items = new Item[2]; items[0].value = tainted;
  sink(items[1].value);` in the negative.
- JavaScript — an array of object literals with distinct constant indices.
- Python — a `list` of instances with distinct constant indices.

**Lineage.** SecuriBench Micro `collections` and `datastructures` combined.

---

### Stratum D — context and depth stress

**Framing, stated before any run.** The depths in this stratum are chosen to sit
**beyond known engine defaults**, and the expectation is written down here
rather than discovered afterwards.

**Verified bound.** The pinned Joern distribution — `joern-v4.0.614` — sets its
data-flow engine's call-depth bound to **4** by default. This is verified from
the distribution itself, not asserted from memory:
`joern-cli/lib/io.joern.dataflowengineoss-4.0.614.jar` contains
`io/joern/dataflowengineoss/queryengine/EngineConfig`, whose first constructor
parameter is `maxCallDepth: Int`; the companion object's default-argument
accessor `EngineConfig$.<init>$default$1()` compiles to `iconst_4; ireturn`, and
`EngineContext$.<init>$default$2()` constructs its default `EngineConfig` from
exactly those defaults. So an unconfigured Joern `reachableBy` query explores to
a call depth of 4.

Stratum D's relay chain is therefore **six** hops — calibrated deeper than the
verified bound, with margin, not equal to it. Summary-based and k-bounded
engines are **expected** to fall off here; unbounded or IDE/IFDS-grade analyses
are expected to keep resolution. That is the prediction this preregistration
makes, and the run tests it. If a future pinned Joern raises its default, the
chain depth is revisited by amendment rather than left silently under-calibrated.

Depth-6 relays also sit beyond Semgrep CE's documented scope entirely — the
pinned CE engine is not a whole-program interprocedural data-flow engine, and
stratum D assertions will be `unsupported` by declared capability, decided from
the case metadata before Semgrep is invoked.

#### 11. `dfb-template-chal-deep-relay-chain`

**Semantic intent.** A relay chain of **six distinct helper functions**, each
taking one parameter and passing it to the next, with the sink at the end. Depth
6 exceeds the verified k = 4 default above.

**Positive.** The tainted value enters hop 1 and reaches the sink after hop 6.

**Negative.** The identical six-hop chain is fed the **clean** value.
`negative_mechanism: unrelated-value`.

**Sketches.** Structurally identical in Java, JavaScript, and Python: six
same-file static/module-level functions `relay1` … `relay6`, no branching, no
state.

**Lineage.** NIST Juliet deep-call / multi-hop sink-chain variants.

**Approximation note.** The negative is deliberately trivial to decide. A
k-bounded engine will answer the negative correctly *because* it cannot see
that far — a true negative arrived at for the wrong reason. Stratum D's positive
cell is therefore the informative one, and the pair must be read together: a
6/6-correct stratum D with all positives `not-reached` is a bounded engine, not
a precise one.

#### 12. `dfb-template-chal-recursive-carry`

**Semantic intent.** The tainted value is carried through a **self-recursive**
function that decrements a counter (constant depth 5) and returns the carried
value at the base case.

**Positive.** The base case returns the carried tainted value, which reaches the
sink.

**Negative.** The base case **overwrites** the carried value with a clean
constant before returning. `negative_mechanism: overwrite-kill`.

**Sketches.** Identical shape in the three languages: `carry(v, n)` returning
`n == 0 ? v : carry(v, n - 1)` (positive) versus `n == 0 ? "clean" : carry(v, n
- 1)` (negative), invoked with `n = 5`.

**Lineage.** NIST Juliet recursion variants.

**Approximation note.** Recursion forces a fixed-point rather than a chain
traversal. An engine that widens recursive summaries to "everything in, everything
out" resolves the positive and false-positives the negative; the `overwrite-kill`
negative is what makes that widening visible.

#### 13. `dfb-template-chal-context-pair-depth2`

**Semantic intent.** The **same** helper is reached through two distinct
two-deep call paths, and only one outer context carries taint. Context
sensitivity at k = 2 — enough to defeat context-insensitive merging and 1-CFA.

**Positive.** The tainted outer context's path reaches the sink.

**Negative.** The clean outer context's path does not.
`negative_mechanism: call-context-separation`.

**Sketches.** `outerTainted() -> wrapper(x) -> helper(x) -> sink` and
`outerClean() -> wrapper(x) -> helper(x) -> sink`, with the *same* `wrapper` and
`helper` bodies shared by both outer methods. Identical in Java, JavaScript, and
Python. *See Amendment A1: the canonical fixture construction carries the value
back by return and sinks the selected result in the caller.*

**Lineage.** OWASP Benchmark indirection tests; xAST's context-sensitivity
scenarios. It is the two-level extension of the core's
`dfb-template-call-context-separation`, which establishes k = 1.

---

### Future-extension candidates, explicitly out of this tier

Named here so that their absence is a recorded decision rather than an
oversight. None of them is part of this tier's population, and adding one later
is a new preregistration, not an amendment to this one.

- **Interprocedural exception flow** — a tainted value thrown across a call
  boundary and caught by the caller.
- **Async/await and promise scheduling** — taint through a scheduled
  continuation. The `asynchronous-flow` semantic dimension already exists in the
  schema for it.
- **`eval`/`exec`-constructed code** — almost certainly `language-extension`
  territory rather than a cross-language core template, since the construct's
  semantics differ too much between languages to preserve one intent.

## Metadata groundwork

Additive schema changes only, made in the same change as this document so that
fixture authoring is unblocked. Every addition below was checked against the
existing enum first; nothing already expressible was duplicated.

### No new score tier

`score_tier` is unchanged. Challenge cases are `core`. This is the population
decision recorded above.

### No new negative mechanisms

All thirteen negatives use mechanisms the enum already carries:
`call-context-separation` (templates 1, 3, 7, 13), `field-separation`
(2, 9, 10), `unrelated-value` (4, 6, 11), `object-separation` (5, 8), and
`overwrite-kill` (12). `infeasible-path` and `sanitizer` remain unused by this
tier.

### No new semantic dimensions

Checked and **not** added: the `semantic_dimensions` enum already carries
`dynamic-dispatch` (strata A and B), `context-sensitivity` (templates 3, 7, 13),
`heap-field-sensitivity` and `object-sensitivity` (stratum C, template 5),
`interprocedural-flow` (strata B and D), and `recursion` (template 12). Adding a
dimension here would have been duplication, so none was added.

### New feature tags

Three values are genuinely missing from the `feature_tags` enum and are added:

| Tag | Covers | Why the existing enum is insufficient |
| --- | --- | --- |
| `reflective-dispatch` | templates 1, and the reflective adaptations of 2 | `ambiguous-dispatch` describes an unresolved *virtual* call site; it does not distinguish a callee named by a run-time string, which is the property that makes engines declare the case out of scope. |
| `higher-order` | templates 3–7 | Nothing in the enum marks a case whose difficulty is a *function value* rather than a data value. `ambiguous-dispatch` covers the call site's ambiguity, not code-as-data. |
| `computed-access` | templates 2, 8 | `heap-access-path` covers access through a statically named path. It does not mark access through a key computed at run time, which is a separate capability. |

`ambiguous-dispatch` itself remains in the enum and is used by templates 3 and
7, where the call site is genuinely ambiguous. `interprocedural-deep` covers
templates 11 and 13; `recursive` covers template 12; `heap-access-path` covers
templates 9 and 10.

### `expected_analysis_capability.kind`

This field is **not** enum-constrained in `schemas/case.schema.json` — it is a
free-form string with an optional `notes` sibling — so no schema change is
required, and none was made. The existing corpus nevertheless follows a strict
naming convention (`heap-field-sensitive-taint`,
`two-hop-interprocedural-return-taint`, and so on), and the challenge tier
extends it rather than inventing a second style. The kinds this tier will use,
fixed here so fixtures do not drift:

| Templates | `kind` |
| --- | --- |
| 1 | `reflective-dispatch-taint` |
| 2 | `computed-member-access-taint` |
| 3, 7 | `indirect-callee-resolution-taint` |
| 4 | `closure-capture-taint` |
| 5 | `heap-stored-callee-taint` |
| 6 | `inverted-control-callback-taint` |
| 8 | `container-iteration-taint` |
| 9 | `deep-access-path-sensitive-taint` |
| 10 | `element-scoped-field-sensitive-taint` |
| 11 | `deep-interprocedural-relay-taint` |
| 12 | `recursive-carry-taint` |
| 13 | `two-level-context-sensitive-taint` |

### Validator scope, stated now, implemented later

`validate_scored_kernel_balance` (`src/cases.rs`) and the per-language
template-ID sets in `src/templates.rs` currently pin each language to the sixteen-template
`KERNEL_TEMPLATE_IDS` population. Those sets **will be extended** to each
language's expanded template set — the exact IDs given by the matrix below — as
each language's fixtures land. That extension is deliberately **not** part of
this change, because extending the required set before the fixtures exist would
make validation fail against the current corpus.

The frozen v0.3.0 evidence is unaffected in either direction. Freeze validation
is manifest-scoped: a manifest binds the cases and reports of its own release,
and adding enum values or, later, adding cases to the corpus does not
retroactively change what a v0.3.0 manifest asserts.

## Applicability matrix for challenge templates

Thirteen templates × thirteen languages, using the vocabulary above. The tables
are the index; the per-language subsections are the justification. As in the
sixteen-template matrix, **an inapplicable cell reduces only that language's
denominator** and never any other language's.

Column order groups the initial tranche (Java, JavaScript, Python) first.

### Stratum A — dynamic dispatch and reflection

| Template ID | Java | JS | Py | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-chal-reflective-invocation` | direct | direct | direct | direct | adapted | adapted | direct | adapted | direct | direct | **n/a** | **n/a** | **n/a** |
| `dfb-template-chal-computed-property` | adapted | direct | direct | direct | adapted | adapted | adapted | adapted | direct | direct | adapted | **n/a** | adapted |
| `dfb-template-chal-dispatch-table` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | adapted | adapted |

### Stratum B — higher-order flow

| Template ID | Java | JS | Py | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-chal-closure-capture` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | **n/a** | direct |
| `dfb-template-chal-function-field` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | adapted | adapted |
| `dfb-template-chal-callback-registration` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | adapted | adapted |
| `dfb-template-chal-anonymous-implementation` | direct | direct | adapted | direct | direct | direct | adapted | adapted | direct | direct | adapted | **n/a** | adapted |

### Stratum C — containers and deep access paths

| Template ID | Java | JS | Py | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-chal-map-iteration` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | adapted | direct |
| `dfb-template-chal-nested-access-path` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-chal-element-object` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |

### Stratum D — context and depth stress

| Template ID | Java | JS | Py | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-chal-deep-relay-chain` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-chal-recursive-carry` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-chal-context-pair-depth2` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |

Strata C and D are almost uniformly direct by construction: containers, field
chains, call depth, and recursion exist in every language in the matrix. That is
intentional. The cross-language variance in this tier is concentrated in strata
A and B, where it reflects real differences in what the languages can express,
not differences in how hard the benchmark chose to be.

### Per-language classifications

#### Java — 13/13 challenge templates

`dfb-template-chal-computed-property` is **language-adapted**: Java has no
computed member-access syntax, so the write and read go through
`java.lang.reflect.Field` resolved by a name held in a local variable. This
keeps the intent (a member located by a run-time name) and is the same
adaptation SecuriBench Micro's `datastructures` cases use. Everything else is
direct: `java.lang.reflect.Method` for template 1, `HashMap` plus functional
interfaces for template 3, lambdas and anonymous inner classes for stratum B,
`entrySet()` iteration for template 8.

`java.lang.reflect` is part of the JDK, so the stdlib-only constraint holds.

#### JavaScript — 13/13 challenge templates

All thirteen are directly applicable; the language is the natural home of every
construct in strata A and B. Computed property access, object-literal dispatch
tables, closures, function-valued properties, and `Object.entries` iteration are
all idiomatic and require no adaptation.

#### Python — 13/13 challenge templates

`dfb-template-chal-anonymous-implementation` is **language-adapted**: Python has
no anonymous classes. The fixture uses a `lambda` where the body is a single
expression and a locally defined single-use class where the sink call is a
statement; the choice is recorded in the [Python kernel
contract](python-kernel.md) before the fixture is authored. All other cells are
direct — `getattr`/`setattr` give templates 1 and 2 without adaptation, and
`dict.items()` gives template 8.

#### TypeScript — 13/13 challenge templates

All thirteen are directly applicable. As with the sixteen-template core,
TypeScript shares JavaScript runtime semantics and the fixtures differ from the
JavaScript ones by type annotations only — including the index-signature or
`Record<string, ...>` annotations needed to type the computed-property and
dispatch-table cells. TypeScript remains a separate result population from
JavaScript and the two are never mixed.

#### Kotlin — 13/13 challenge templates

Templates 1 and 2 are **language-adapted**. Kotlin's own reflection lives in
`kotlin-reflect`, a *separate artifact*, which the stdlib-only constraint
excludes; the fixtures therefore use the JVM's `java.lang.reflect` through
`javaClass.getMethod` / `getDeclaredField`. The adaptation is recorded in the
[Kotlin kernel contract](kotlin-kernel.md). Everything else is direct: Kotlin
has first-class function types for template 3, closures for template 4, function-typed
properties for template 5, and object expressions (`object : Handler { ... }`)
that are genuinely anonymous implementations for template 7.

#### Scala — 13/13 challenge templates

Templates 1 and 2 are **language-adapted** for the same reason as Kotlin:
`scala-reflect` is a separate artifact, so the fixtures use `java.lang.reflect`.
The rest is direct — function values for template 3, closures for template 4,
`new Handler { ... }` anonymous classes for template 7, and `Map` iteration for
template 8.

#### C# — 13/13 challenge templates

`dfb-template-chal-computed-property` is **language-adapted** through
`System.Reflection` `FieldInfo`/`PropertyInfo` resolved by a run-time name, on
the Java precedent: C# has no computed member syntax on ordinary objects.

`dfb-template-chal-anonymous-implementation` is **language-adapted**: C#
anonymous types have properties but no methods and implement no interfaces. The
fixture uses an anonymous method (`delegate (string v) { Sink(v); }`) assigned to
a declared delegate type and invoked through it — an unnamed implementation
reached through a declared type, which is the template's intent. The adaptation
is recorded in the [C# kernel contract](csharp-kernel.md).

Template 1 is direct via `MethodInfo.Invoke`; the remainder are direct.

#### Go — 13/13 challenge templates

Three language-adapted cells, all through the standard library:

- Templates 1 and 2 use `reflect` — `reflect.ValueOf(o).MethodByName(name).Call`
  and `reflect.ValueOf(&s).Elem().FieldByName(k)`. Go has no non-reflective
  computed member access, and `reflect` is stdlib.
- `dfb-template-chal-anonymous-implementation` uses the `http.HandlerFunc`
  idiom without importing `net/http`: a locally declared func type with a method
  satisfying a one-method interface, with an anonymous func literal converted to
  it and invoked through the interface value. Go has no anonymous types
  implementing interfaces; this is the idiomatic equivalent.

Closures, func-typed struct fields, slices of funcs, `range` over maps, nested
structs, and slices of structs are all direct.

#### PHP — 13/13 challenge templates

All thirteen are directly applicable. PHP has variable method calls
(`$o->$name($v)`), variable property access (`$o->$k`), arrays of closures,
`use`-clause closures, closure-valued properties, `foreach` over arrays, and —
unusually among the statically-flavored languages here — genuine anonymous
classes (`new class implements Handler { ... }`), so template 7 needs no
adaptation.

#### Ruby — 13/13 challenge templates

All thirteen are directly applicable. `public_send(name, v)` gives template 1,
`instance_variable_set`/`instance_variable_get` give template 2, hashes of
lambdas give template 3, blocks and procs give stratum B, and `Class.new do ...
end` gives a genuinely anonymous class for template 7. `Hash#each` gives
template 8.

Ruby's tranche remains gated on the analyzer-coverage condition already recorded
in [the applicability matrix](applicability-matrix.md); that gate is unchanged
by this document.

#### C++ — 12/13 challenge templates

`dfb-template-chal-reflective-invocation` is **inapplicable**. Standard C++ has
no run-time reflection: no standard-library facility resolves a member function
from a string at run time. The nearest construct — a `std::map<std::string,`
member-function-pointer`>` — *is* `dfb-template-chal-dispatch-table`, and
encoding it as template 1 as well would put the same fixture under two
`template_id` values, inflating the denominator without asking a second
question. The cell is therefore excluded rather than duplicated. Compile-time
reflection (P2996) is not in the pinned language standard and is not used.

`dfb-template-chal-computed-property` is **language-adapted**: since member
access by run-time name does not exist, the computed key indexes a
`std::map<std::string, std::string>` through a non-constant key variable, with
two distinct constant keys in the negative. The member-access flavor of the
template is lost and the computed-key flavor is preserved; this loss is recorded
in the [C++ kernel contract](cpp-kernel.md).

`dfb-template-chal-anonymous-implementation` is **language-adapted**: C++ has no
anonymous classes, but a lambda's closure type *is* unnamed, so the fixture
invokes a capture-less lambda through a declared `std::function<void(std::string)>`.
Capture-less is what keeps it distinct from template 4.

The remaining ten cells are direct: `std::function` members and vectors for
templates 5 and 6, `std::map` range-`for` for 8, nested structs for 9,
`std::vector<Item>` for 10, and ordinary functions for stratum D.

#### C — 9/13 challenge templates

C has the largest reduction in this matrix, and every exclusion is a genuine
absence of the construct rather than a difficulty.

**Inapplicable:**

- `dfb-template-chal-reflective-invocation` — C has no run-time reflection of
  any kind. No standard-library facility maps a name to a function at run time.
- `dfb-template-chal-computed-property` — C has neither computed member access
  nor any standard-library associative container. Adapting it would require
  authoring a string-keyed lookup structure inside the fixture, which makes the
  fixture's own hand-written code, not a language construct, the object of
  analysis.
- `dfb-template-chal-closure-capture` — C has no closures and no capture. A
  function pointer plus a manually passed context struct is not capture; the
  environment is an ordinary argument, which the sixteen-template core already
  covers.
- `dfb-template-chal-anonymous-implementation` — C has no anonymous functions
  and no anonymous types.

**Language-adapted:**

- `dfb-template-chal-dispatch-table` — an array of `{const char *name; char
  *(*fn)(char *);}` entries selected by `strcmp`. This is the canonical C
  dispatch-table idiom and preserves the intent exactly.
- `dfb-template-chal-function-field` — a function pointer stored in a struct
  field, fetched elsewhere and called. C expresses "code stored in the heap"
  natively.
- `dfb-template-chal-callback-registration` — an array of function pointers in a
  holder struct, plus a driver loop. Also canonical C.
- `dfb-template-chal-map-iteration` — C's standard library has no map, so the
  container is an array of key/value structs iterated with a match condition in
  the loop. The intent that survives is "retrieved by iterating a container, not
  by a direct keyed get"; the intent that is lost is "a standard-library map",
  and that loss is recorded in the [C kernel contract](c-kernel.md).

Nested structs (9), arrays of structs (10), and stratum D are direct.

The excluded closure and reflection constructs have no C-idiomatic near-relative
worth routing to `language-extension`; C's existing `language-extension` cases
(error-code return paths, goto-cleanup handlers) are unaffected.

#### Rust — 12/13 challenge templates

`dfb-template-chal-reflective-invocation` is **inapplicable**. Rust's standard
library has no run-time reflection; `std::any::Any` supports downcasting to a
known static type and offers no name-based member or method lookup. There is no
adaptation that asks "does the engine follow a callee named by a run-time
string", so the cell is excluded. Trait-object dispatch is a *different*
question and is already asked by templates 3, 5, and 7.

**Language-adapted:**

- `dfb-template-chal-computed-property` — as in C++, a `HashMap<String, String>`
  indexed by a non-constant key, with two distinct constant keys in the negative;
  the member-access flavor is lost and recorded as lost in the [Rust kernel
  contract](rust-kernel.md).
- `dfb-template-chal-dispatch-table` — a `HashMap<&str, fn(String) -> String>`
  of function pointers rather than of closures, since `fn` items are the
  form that avoids boxing.
- `dfb-template-chal-function-field` and
  `dfb-template-chal-callback-registration` — a struct field of type
  `Box<dyn Fn(String)>` and a `Vec<Box<dyn Fn(String)>>` respectively. Rust
  requires the indirection to be explicit; the driver takes `&self`.
- `dfb-template-chal-anonymous-implementation` — Rust has no inline anonymous
  `impl` of a trait. A capture-less closure has an unnamed type and is invoked
  through a declared `Box<dyn Fn(String)>`, which preserves "unnamed
  implementation reached through a declared type". Capture-less keeps it
  distinct from template 4.

`dfb-template-chal-closure-capture` is direct via a `move` closure capturing a
`String`. Stratum C is direct (`HashMap` iteration, nested structs,
`Vec<Item>`), as is stratum D — the recursive carry in template 12 is a plain
recursive `fn` with a decrementing `u32`.

## Expanded core denominators

Each language's v0.4.0 core denominator is its sixteen-template core (15 for C
and Rust, whose `dfb-template-exception-catch` cell is inapplicable per the
[applicability matrix](applicability-matrix.md)) plus its applicable challenge
templates.

| Language | v0.3.0 core | Applicable challenge | v0.4.0 expanded core | Expanded assertions |
| --- | --- | --- | --- | --- |
| Java | 16 | 13 | 29 | 58 |
| JavaScript | 16 | 13 | 29 | 58 |
| Python | 16 | 13 | 29 | 58 |
| TypeScript | 16 | 13 | 29 | 58 |
| Kotlin | 16 | 13 | 29 | 58 |
| Scala | 16 | 13 | 29 | 58 |
| C# | 16 | 13 | 29 | 58 |
| Go | 16 | 13 | 29 | 58 |
| PHP | 16 | 13 | 29 | 58 |
| Ruby | 16 | 13 | 29 | 58 |
| C++ | 16 | 12 | 28 | 56 |
| C | 15 | 9 | 24 | 48 |
| Rust | 15 | 12 | 27 | 54 |

The invariants of the sixteen-template matrix carry over without change. An
inapplicable cell reduces only that language's denominator. Cross-language
macro-averages are computed per language population and are never pooled over
unequal template sets without stating the population. A 24-template C score and
a 29-template Java score are not interchangeable and are not averaged into one
number without that statement.

And, restating the population rule because it is the one most likely to be
violated by a casual reader: a 16-template v0.3.0 score and a 29-template v0.4.0
score are also not interchangeable. They are different populations of the same
name.

## Rollout plan

The expansion targets **all thirteen languages** for v0.4.0, so the release
ships one coherent expanded breadth rather than a core that means different
things in different languages. This is why the applicability matrix above covers
all thirteen up front, before the first fixture: a language whose cells were
classified later would have its denominator decided by what was convenient to
implement.

**Waves.** Fixture implementation begins only after this document merges, and
proceeds in waves:

1. **Wave 1 — the saturated kernels:** Java, JavaScript, Python. These are the
   languages where the core is at 32/32 and headroom is most urgently needed,
   and they are the three with per-language sketches written above.
2. **Wave 2 — near-parity languages:** TypeScript, Kotlin, C#, Scala.
3. **Wave 3 — adapted-construct languages:** Go, C++, Rust, C.
4. **Wave 4 — analyzer-coverage-gated languages:** PHP, Ruby, carrying forward
   the coverage gates already recorded in the applicability matrix.

Each wave is a bounded change that adds fixtures, extends that language's
template-ID set in the balance validator, and adds the language-qualified
adapter artifacts the existing pattern requires. A wave never edits a template
definition in this document.

**Analyzer runs.** All four adapters run wherever their documented profiles
reach, and the profile — not the result — decides participation:

- **Bifrost** and **CodeQL** are expected to attempt the full expanded core in
  the languages they already cover.
- **Joern** attempts the full expanded core in the languages its pinned
  frontends cover, with stratum D expected to fall off at its verified default
  call-depth bound of 4 unless the adapter is configured otherwise. If the
  adapter ever raises `maxCallDepth` above the default, that configuration
  change is a reported part of the run's identity, not a silent tuning.
- **Semgrep CE** will mark most challenge templates `unsupported` by declared
  capability. Its intraprocedural profile does not reach stratum B, C's
  iteration cases, or any of stratum D. **This is correct behavior and not a gap
  to paper over.** The adapter already decides `unsupported` from case metadata
  before invoking the tool, and the resulting coverage numbers are the honest
  description of a bounded engine, not a scoreboard failure.

Nothing in this plan makes a language's fixtures conditional on the results any
analyzer produces for it.

## Invariants

Restating the [scoring contract](scoring.md) obligations that this tier is most
at risk of eroding:

- There is no combined leaderboard across languages, and none across strata.
- Benchmark-controlled and tool-native model profiles are never pooled.
- `inconclusive`, `unsupported`, and `runner-error` are capability or execution
  coverage and are never clean negatives.
- `language-extension` and `calibration` cases have their own scorecards and
  never change a core denominator.
- Published numbers come only from validated freeze manifests.
- The v0.3.0 sixteen-template core and the v0.4.0 expanded core are separate
  populations and are never compared as if they were one.
- Stratum A and template 7 results are reported as approximation character, not
  as a ranking.

## Amendments

### A1 — 2026-08-25: canonical construction for `dfb-template-chal-context-pair-depth2`

**What changed.** The illustrative sketch above places the sink call inside
`helper`. Taken literally, that shape is not assertable: both fixtures must
contain the tainted outer context (that is what makes the negative a context
question rather than a dead-code question), so a sink inside the shared
`helper` body would leave a genuine live source-to-sink flow in the *negative*
fixture and falsify its non-flow assertion regardless of analyzer quality. The
canonical construction — used by every implementing language — is the corpus
convention the classic `dfb-template-call-context-separation` pair already
establishes at k = 1: `helper` returns its argument, and the caller sinks the
result of the selected two-deep path. The positive sinks the tainted context's
result; the negative sinks the clean context's result while the tainted call
remains live, which is precisely the false-positive trap for context-merging
engines that the template exists to set.

**Why.** Sketch under-specification, not a semantic change. The template's
binding parts — semantic intent (k = 2 context separation), polarity,
`negative_mechanism: call-context-separation`, and applicability — are
untouched. The correction was identified independently by the first two
implementing languages (Java and Python) before any analyzer executed against
either fixture, and both recorded it in their kernel contracts at the time.

**Templates and languages touched.** `dfb-template-chal-context-pair-depth2`,
all languages (the construction is language-uniform).

**Freezes invalidated.** None. No published freeze binds any challenge
fixture.
