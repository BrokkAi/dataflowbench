# Java taint-modeling matrix

This is wave M1's Java row, and its last: the twenty-four fixtures of
[the benchmark-controlled taint-modeling matrix](modeling-matrix.md), the four
per-adapter model encodings Java's partition entitles it to, and the four runs.
It lands after [Python's](python-modeling.md) and
[JavaScript's](javascript-modeling.md) and is deliberately their mirror — the
same fixture shapes, the same file-per-entity naming, the same runner, the same
shared `modeling.sc` — so that a difference between the three rows is a
difference between the *frontends*, never between three benchmark designs.

Nothing here amends the preregistration's partition. The twelve template
definitions, the six categories, the negative mechanisms, the capability kinds,
and the per-tool partition were fixed before any of these fixtures existed, and
this document reports against them **as amended by
[A2](modeling-matrix.md#a2--2026-08-26-joerns-propagator-and-summary-categories-are-not-load-bearing),
[A3](modeling-matrix.md#a3--2026-08-26-semgreps-sanitizer-selectivity-cell-is-undecidable-by-construction),
and [A4](modeling-matrix.md#a4--2026-08-26-the-reflective-opaque-propagator-body-is-not-unfollowable-by-joerns-jssrc2cpg)**.
All three were made against earlier rows' evidence, and all three are confirmed
here. This row contributes one amendment of its own,
[A5](modeling-matrix.md#a5--2026-08-26-bifrost-v0106-accepts-unmodeled-require-model),
which is an evidentiary confirmation and moves no cell, and it extends A4's
record from `jssrc2cpg` to `javasrc2cpg`.

**Java's modeling denominator is 12 templates / 24 assertions**, on the
`modeling` tier, with its own scorecards. No number in this document is ever
pooled with [the Java propagation kernel](java-kernel.md), and a high score here
is not a high propagation score. The two answer different questions: the kernel
asks whether an engine can follow flow it can see, and this matrix asks whether
it can be told things.

## What is committed

| Artifact | Path |
| --- | --- |
| Cases and fixtures | `cases/taint/java/model-*-{positive,negative}/` |
| Bifrost policy | `adapters/bifrost/policies/model-java.rqlp` |
| CodeQL query | `adapters/codeql/queries/JavaModeling.ql` |
| Joern semantics | `adapters/joern/semantics/model-java.semantics` |
| Joern query | `adapters/joern/queries/modeling.sc` (shared by every wave-M1 language) |
| Semgrep rule | `adapters/semgrep/rules/model-java.yaml` |
| OpenTaint rule | `adapters/opentaint/rules/model-java.yaml` (joined by [Amendment A22](modeling-matrix.md#a22--2026-09-01-opentaint-joins-the-modeling-matrix-with-a-preregistered-java-partition-row); see [below](#opentaint-joins-the-row--amendment-a22-2026-09-01)) |
| Reports | `reports/{bifrost,codeql,joern,semgrep,opentaint}-java-modeling.json` |
| Load-bearing probe | `scripts/probe-java-modeling-load-bearing.sh` |
| OpenTaint surface probe | `scripts/probe-opentaint-modeling-surface.sh` |

The CodeQL query is the one path that departs from the other two rows'
convention, and it departs *back onto* the preregistration's schematic one.
Java's CodeQL pack **is** the adapter root: `adapters/codeql/qlpack.yml`
declares `dataflowbench/codeql-java` with the `codeql/java-all` dependency, and
`queries/JavaKernel.ql` already lives beside it. There is no
`adapters/codeql/java/` pack to descend into, and a query placed under one would
resolve no dependency at all. The rule is unchanged — a modeling query lives
inside its language's existing pack — and a test now asserts that every modeling
query resolves a `qlpack.yml` two directories up.

## Per-template realization

Every fixture is stdlib-only Java in package `dataflowbench.taint` — no
framework, no dependency, no build manifest — and compiles warning-free under
`javac --release 21 -Xlint:all -Werror`, which is the same host toolchain the
CodeQL Java adapter traces with `javac -d classes`. Every case is
`score_tier: "modeling"`, `model_profile: "benchmark-controlled"`, provenance
revision `m3-modeling-java`. Eleven templates are a single `.java` file;
template 7 is two, because its summarized procedure has to be external-shaped.

**Fixtures are named for the entity they declare** where the entity is the
point — `Bridge.java`, `Handler.java` — and otherwise for the case. Java's
identity story is simpler than JavaScript's: `javasrc2cpg` spells a method full
name as `dataflowbench.taint.<Type>.<member>:<signature>`, which is
file-independent, so the Joern flow-semantics artifact binds one entry per
entity regardless of where the type is declared.

**The endpoint identities come from each fixture's own `DFB-SOURCE:` /
`DFB-SINK:` markers, and those markers always sit on the *declared* entity**,
including in the negatives, where the declared entity is deliberately not the
one the taint runs through. That is what makes a negative measure the
declaration: the runner selects the declared source and the declared sink, and
the fixture arranges for the flow to go somewhere else.

> **Marker-convention correction, recorded rather than quietly fixed.** Four of
> Java's twelve negatives originally marked the *undeclared sibling* —
> `Audit.discard`, `Config.fetchLocal`, `Handler.onIgnored`,
> `Handler.onUndeclared` — which is the same authoring slip
> [the JavaScript row](javascript-modeling.md) found in four of its own. Marking
> the sibling inverts what the negative measures: it anchors the case on the
> entity the model does *not* declare, so a tool that correctly ignored the
> sibling would be reconciled against the sibling anyway. All four now mark the
> declared entity, matching Python's and JavaScript's convention exactly, and
> the two entry-point negatives' bodies moved with them, because a negative
> whose declared handler still carries the flow is not a negative. The two
> entry-point positives' siblings and the declared-sink positive's control call
> were aligned in the same pass, so the three rows' fixtures are now
> shape-for-shape identical. Every number in this document is from runs on the
> corrected fixtures.

| # | Template | Java realization |
| --- | --- | --- |
| 1 | `declared-source` | `final class Config` with two constant-returning statics, `fetchRemote` (declared) and `fetchLocal`. The positive sinks `Config.fetchRemote()`, the negative `Config.fetchLocal()`. Both bodies return a string literal, so an engine that reads them learns nothing that distinguishes the two. |
| 2 | `declared-sink` | `final class Audit` with two one-parameter statics that both drop their argument, `record` (declared) and `discard`. The positive calls `Audit.record(dfb_source())` and `Audit.discard("clean")`; the negative swaps them. |
| 3 | `opaque-propagator` | `final class Opaque` with `carry` (declared) and `block`, whose bodies are byte-identical reflective self-dispatch: `Opaque.class.getMethod(target, String.class).invoke(null, value)` with `target` a local `String` constant naming a public `identity` method. |
| 4 | `propagator-position` | `Opaque.select(String first, String second)` with the same reflective body, forwarding `second`. The positive is `Opaque.select("clean", dfb_source())` — taint at declared position 1 — and the negative the identical call with taint at the undeclared position 0. |
| 5 | `sanitizer-kill` | `final class Clean` with the identity method `scrub` (declared). The positive is the bare flow `dfb_sink(dfb_source())`; the negative routes the same flow through `Clean.scrub`. `Clean` is present in both fixtures, so the pair differs only in the routing. |
| 6 | `sanitizer-selectivity` | `Clean` with two identity methods, `scrub` (declared) and `sanitize`. The positive flows through the undeclared `sanitize` and must still be reported; the negative flows through the declared `scrub`. |
| 7 | `summary-through` | `Bridge.java`, a second fixture file, holding `Bridge` with two identity methods `pass` (declared) and `hold`. Both bodies say flow; the summaries disagree, which is what makes reading-the-body and activating-the-summary distinguishable. |
| 8 | `summary-field` | `final class Box { String payload; String spare; }` and `static void deposit(String value, Box box) { }` with an empty body. Both cells call `Bridge.deposit(dfb_source(), box)`; the positive sinks `box.payload`, the negative the sibling `box.spare`. |
| 9 | `entrypoint-parameter` | `final class Handler` with two uncalled one-parameter methods, `onRequest` (declared) and `onIgnored`, and no code invoking either. Exactly one of them carries `dfb_sink(input)` and the other `dfb_sink("clean")`: the declared one in the positive, the undeclared one in the negative. |
| 10 | `entrypoint-selectivity` | The same shape with `onDeclared` (declared) and `onUndeclared`, both plausible roots in one class. |
| 11 | `store-roundtrip` | `final class Store` with two static no-op methods `put(key, value)` and `get(key)`. `writeSide()` calls `Store.put("k", dfb_source())` and a separate `readSide()` calls `dfb_sink(Store.get("k"))`; the negative uses the distinct constant keys `"a"` and `"b"`. No standard-library map is used, so no shipped `HashMap` model can pass the cell without reading the declaration. |
| 12 | `store-separation` | The same shape with *instance* methods and two `static final Store` fields, `alpha` and `beta`, constructed once and never reassigned. The positive writes and reads `alpha`; the negative writes `alpha` and reads `beta` under the same key. |

No template proved unimplementable as preregistered, and no template's semantics
were altered.

### One authoring decision worth recording

Template 8's `Box` and `Bridge` are auxiliary classes in the fixture's own file
rather than in a second one. `javac -Xlint:all` emits `auxiliaryclass` when a
class hidden in one source file is used from another, so the two-file spelling
would not have compiled warning-free. The preregistration requires a second file
only for template 7 — where external *shape* is part of the semantic intent — so
template 8 is single-file. Nothing about the declaration changes: the entity is
still `Bridge.deposit`, bound by type and member.

## The four encodings

The same three parts — entity identity, role, binding semantics — in four native
surfaces. Nothing is translated across the surfaces, and a category a tool's
partition declines is **absent** from that tool's artifact rather than
approximated in it. That rule is a test:
`the_modeling_artifacts_declare_only_their_scored_categories` now covers all
three wave-M1 languages and fails the suite if any artifact declares a category
its partition marks unsupported.

| Adapter | Artifact | Categories it declares |
| --- | --- | --- |
| Bifrost v0.10.9 | `adapters/bifrost/policies/model-java.rqlp` | S, Z (Amendment [A9](modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false)) |
| CodeQL 2.26.4 | `adapters/codeql/queries/JavaModeling.ql` | S, P, Z, O, E, B |
| Joern 4.0.617 | `adapters/joern/semantics/model-java.semantics` + `adapters/joern/queries/modeling.sc` | S, Z, E, B |
| Semgrep CE 1.176.0 | `adapters/semgrep/rules/model-java.yaml` | S, Z, E |

**Bifrost** declared category S alone when this row ran, as two `:sources`
entries bound to `return-value` and two `:sinks` entries bound to
`(argument :index 0)`; Amendment A9 has since promoted category Z and the
committed artifact now also carries one `:sanitizers` entry, whose scored
evidence lands with the next re-run. It sets
`:call-modeling (call-modeling :unmodeled require-model)`, which the pinned
v0.10.9 build accepts — see [A5](#amendment-a5-require-model-is-accepted) below.
That acceptance does **not** promote category P, which also requires a
propagator or transform declaration surface no committed policy has.

**CodeQL** declares all six categories in one `DataFlow::ConfigSig`: `isSource`
over the declared source calls and over the parameter node of each declared
entry point, `isSink` over argument 0 of the declared sink calls, `isBarrier`
over argument 0 of `Clean.scrub` (plus the explicit no-flow declarations of
`Opaque.block` and `Bridge.hold`), and five `isAdditionalFlowStep` clauses for
`carry`, `select`, `pass`, `deposit`, and the `put`/`get` pair. No data
extensions are used; the query owns the model, which is what
`adapters/codeql/README.md` states as this adapter's design.

**Joern** splits its declarations across the two files the runner hash-binds
together. `modeling.sc` — shared byte-for-byte with Python and JavaScript, and
deliberately not moved by this row — carries the source, sink, and entry-point
identities as query roots, selected by the identity read off each fixture's own
DFB markers; `model-java.semantics` carries the sanitizer and persistence
declarations as `FullNameSemanticsParser` entries in Joern's own textual syntax.
Categories P and O are absent from the file, because A2 declines them. Three
entries remain:

```
"dataflowbench.taint.Clean.scrub:java.lang.String(java.lang.String)"
"dataflowbench.taint.Store.put:void(java.lang.String,java.lang.String)" 2 -> 0
"dataflowbench.taint.Store.get:java.lang.String(java.lang.String)" 0 -> -1
```

**The Java semantics file carries no comments at all**, where Python's and
JavaScript's carry `#` ones. The pinned 4.0.614 parser fails *silently* in more
than one way — a blank line drops every declaration, and a `//` comment does
too — and on this file a leading comment was measured to produce the same empty
parse, so the commentary lives here and in `adapters/joern/README.md` rather
than in the file. The run's own evidence confirms the file parses:
`declared_semantic_count: 3` in every retained Joern document. `modeling.sc`
additionally raises on an empty parse, so a silent drop is a `runner-error` and
never a scored cell decided by a missing model.

**Semgrep CE** declares categories S, Z, and E and nothing else — no
`pattern-propagators`, no summary, no persistence boundary — and sets
`options: taint_assume_safe_functions: true`, the load-bearing requirement.
Under A3, template 6 is `unsupported` activation, so Semgrep's scored set is
five templates. Nothing in the rule is templated: the kernel rules substitute
each case's own endpoint identifiers into placeholders, but here the endpoint
identities *are* the model and are the same for every case, so the committed
rule states them literally.

## Anchor reconciliation

Modeling cases are reconciled by the same machinery every kernel uses, with two
modeling-specific additions that no kernel path can see.

**`AnchorDialect::JavaMember`** accepts a member-qualified callsite —
`Audit.record(v)`, `Config.fetchLocal()`, `beta.get("k")` — where the kernel's
`AnchorDialect::Java` deliberately refuses one. It is the exact counterpart of
JavaScript's `AnchorDialect::EcmaMember`, and Java needs it more sharply than
JavaScript does: Java has no free functions, so *every* declared modeling entity
is a member of some type and every callsite of one is written through its
receiver. The kernel dialect is right for a kernel — its `dfb_sink` is a static
method called bare from the same class, and `other.dfb_sink(v)` really is a
different method — and it is unchanged. No kernel reconciliation moves.

**`JoernEndpointRule::AbsenceIsTheAssertion`** governs what a zero endpoint
count means, exactly as in the other two rows: a modeling negative may
legitimately contain no *declared* endpoint, and that absence is the content of
the assertion rather than an incomplete run. An empty extraction
(`method_count == 0`) is still `inconclusive`.

Reconciliation on this tier is source-anchored as well as sink-anchored, because
a modeling fixture carries both halves of its pair in one type by construction
and category E's handlers need no caller. A finding counts only when it lies in
the region its case's own source anchor governs *and* on a callsite of its
anchored sink function; an unmatched finding is the pair's other entity, fully
attributable, and normalizes to `not-reached` with the count retained rather
than to the kernels' `inconclusive`.

## Results

Run sequentially against the pinned toolchain — Bifrost v0.10.6 (build
`18d09c57`), CodeQL CLI 2.26.3, Joern 4.0.610, Semgrep CE 1.174.0
(`--oss-only`) — on 2026-08-26. Every outcome below is retained in
`reports/<tool>-java-modeling.json` with its raw evidence under
`reports/raw/<tool>-java-modeling/`.

### Outcome distribution

| Adapter | Scored | `reached` | `not-reached` | `inconclusive` | `unsupported` | Matches |
| --- | --- | --- | --- | --- | --- | --- |
| Bifrost v0.10.6 | 4 (S) | 2 | 2 | 0 | 20 | **4 / 4** |
| CodeQL 2.26.3 | 24 (all six) | 12 | 12 | 0 | 0 | **24 / 24** |
| Joern 4.0.610 | 16 (S, Z, E, B) | 6 | 10 | 0 | 8 | **14 / 16** |
| Semgrep CE 1.174.0 | 10 (S, Z template 5, E) | 5 | 5 | 0 | 14 | **10 / 10** |

The `unsupported` column is capability coverage, decided from the template
identity before the analyzer was invoked and retained with the
preregistration's own rationale. It is never a negative and it does not reduce
anyone else's denominator. **These four numbers are not comparable to one
another**, because they are over four different denominators.

No result in this run is `inconclusive` and none is `runner-error`.

Configuration hashes: Bifrost `921d2c8e…`, CodeQL `38acb5de…`, Joern
`55282607…`, Semgrep `d25d4a40…`.

### Per category

`—` is a category the partition declines for that tool, with the amendment that
declined it named where one did.

| Category | Bifrost | CodeQL | Joern | Semgrep CE |
| --- | --- | --- | --- | --- |
| S — sources and sinks | 4/4 | 4/4 | 4/4 | 4/4 |
| P — propagators | — | 4/4 | — (A2) | — |
| Z — sanitizers | — | 4/4 | 4/4 | 2/2 (template 6 declined, A3) |
| O — summaries | — | 4/4 | — (A2) | — |
| E — entry points | — | 4/4 | 4/4 | 4/4 |
| B — persistence | — | 4/4 | 2/4 | — |

**This is the same shape as the Python and JavaScript rows, cell for cell**,
including Joern's two category-B false negatives, with one difference: Bifrost
decides all four of its category-S cells on Java, where JavaScript's row
reported three of them `inconclusive`. That is a JavaScript-language property of
the engine — the same incompleteness the frozen JavaScript kernel slice records
— and not a modeling one. Java and Python behave identically here.

### Mismatches, in full

There are two across the whole matrix, and both are Joern's.

**Joern — both category-B positives, false negatives.** The roundtrip does not
close, in either the type-identity (template 11) or the receiver-identity
(template 12) cell. Both boundary declarations key cleanly on `javasrc2cpg` —
`dataflowbench.taint.Store.put:void(java.lang.String,java.lang.String)` is a
stable, file-independent full name, so Java does not hit the
`<unknownFullName>` binding wall JavaScript does — and both negatives are
correct. Taint deposited on the receiver by `put` simply does not survive into a
separate procedure's `get`. Python's row, where the declarations also bind
cleanly, produces the identical pair. The limitation the cell measures is the
engine's, and all three frontends reach it.

Neither is a partition change and neither was tuned around. The fixtures are
left as the preregistration's sketch spells them.

### What the numbers do and do not say

CodeQL's 24/24 says its data-flow configuration expresses every one of the six
declaration roles and produces the declared semantics. It says nothing at all
about CodeQL's propagation kernel score, and this number is never added to one.
What it does establish across the three rows is that the twelve templates are
*satisfiable as preregistered* — each one has at least one engine that gets it
right — so a miss elsewhere is a statement about that engine and not about a
badly posed cell.

Joern's 14/16 is over a denominator A2 shrank from 24 to 16. That is not a worse
result reported as a better one: the eight withdrawn cells were withdrawn
because a result there would have scored the engine's default optimism rather
than the model. The
[pre-amendment observations](#retained-pre-amendment-observations) below are what
those eight cells produced when they were still scored, kept as evidence rather
than as a score.

Semgrep CE decided ten assertions to Bifrost's four, which is the opposite of
the ordering the propagation kernels would suggest — which is the entire reason
this tier exists.

Bifrost's four decided assertions are four, not four out of twenty-four: it
declined five categories in the preregistration, and a decline is coverage.

## The three-way distinction

All three states are representable and two of them occur.

**Missing model** — none, and unrepresentable. Every scored cell has a
declaration behind it in that adapter's committed artifact, and every declined
cell is declined by the preregistered partition. The runner refuses to start
when an artifact is missing, `modeling.sc` raises when the semantics file parses
to nothing, and the population validator refuses a modeling case that is not one
of the twelve or that is not `model_profile: "benchmark-controlled"`.

**Unsupported activation** — 42 assertions: Bifrost's twenty, Joern's eight, and
Semgrep CE's fourteen. Each is decided from the template identity *before* the
analyzer is invoked, retains the preregistration's rationale verbatim, and
writes a `retained-capability-decision` evidence document beside the report. No
analyzer process ran for any of them.

**Incomplete analysis** — none. Unlike JavaScript's row, every invoked cell on
Java completed.

## Load-bearing verification

`scripts/probe-java-modeling-load-bearing.sh` runs one positive fixture per
adapter twice — once against the committed artifact and once against a copy with
the single declaration under test deleted — and retains both raw outputs under
`reports/raw/load-bearing-java-modeling/`. It never touches a committed artifact
and never writes a report.

| Adapter | Category | Declaration removed | With model | Without model |
| --- | --- | --- | --- | --- |
| Bifrost | S | the `Config.fetchRemote` source entry | 1 finding | **0 findings** |
| CodeQL | P | the `Opaque.carry` propagator step | 1 result | **0 results** |
| Joern | Z | the `Clean.scrub` no-flow entry | 0 flows | **1 flow** |
| Semgrep CE | S | the `Audit.record` sink pattern | 1 finding | **0 findings** |

Every scored category is load-bearing on the adapter that scores it. CodeQL's
probe is also the check that template 3 is doing what it was designed to do:
with the propagator step removed, CodeQL reports nothing through the reflective
body, so the positive cell can only be `reached` because the model was
activated.

### Amendment A5: `require-model` is accepted

The preregistration recorded Bifrost's category P as *to be verified* partly
because no committed policy set `:call-modeling (call-modeling :unmodeled
require-model)` and the pinned CLI's acceptance of the setting was unshown. The
committed Java modeling policy sets it, and the pinned v0.10.6 evaluates it to
completion with an empty `diagnostics` array and one finding on template 1's
positive — retained as
`reports/raw/load-bearing-java-modeling/bifrost-require-model-accepted.json`.

[Amendment A5](modeling-matrix.md#a5--2026-08-26-bifrost-v0106-accepts-unmodeled-require-model)
records that as an evidentiary confirmation. **No partition cell moves.**
Accepting the switch is necessary but not sufficient for promoting category P;
the other stated obstacle — showing that a propagator or transform section
actually lowers — is untouched, and Bifrost's category-S cells were already
scored, so the confirmation changes no denominator and no outcome.

### Amendment A4, extended to `javasrc2cpg`

`reports/raw/load-bearing-java-modeling/joern-opaque-propagator-unmodeled.json`
is one run of `modeling.sc` over Java's `model-opaque-propagator-positive` under
the committed Java semantics — which, after A2, declares **nothing whatsoever**
for category P. It records `state: analyzed`, `declared_semantic_count: 3` (the
sanitizer and the two persistence mappings, none of them a propagator), and
`flow_count: 1`.

A4 was written from `jssrc2cpg` and stated its withdrawal as a general one
rather than a JavaScript-specific one, leaving each language to stand on its own
evidence. This is Java's, and it says the same thing: the pinned engine plus the
`javasrc2cpg` frontend follows
`Opaque.class.getMethod(target, String.class).invoke(null, value)` unaided,
through `Method.invoke`'s `Object[]` argument, with no propagator model
whatsoever. A4's entry carries this as a dated addendum. No cell moves — A2 had
already withdrawn Joern's category-P cells for the stronger reason that
`FlowSemantic` mappings cannot restrict the default pass-through.

## Retained pre-amendment observations

Java's matrix was first run before A2 and A3 were applied to this tree, over the
full 24 for Joern and the full 12 for Semgrep CE. Those runs are not the
published result and no number in them is scored. They are retained here because
each independently confirms an amendment made on another language's evidence,
and because the eight and two cells they cover are now decided by the partition
rather than by a run.

**Joern, categories P and O (now `unsupported`, A2).** The pre-amendment Java
run scored 20 of 24, with four misses: two false positives in P and O and the
same two category-B false negatives published above. Both false positives were
separated from "the model was ignored" by their own crossed probes:

| `Opaque.select` semantics | T4 positive (taint at declared position 1) | T4 negative (taint at undeclared position 0) |
| --- | --- | --- |
| `2 -> -1` (as then committed) | 1 flow | 1 flow |
| declared with no mapping (`NilSemantics`) | 0 | 0 |
| absent from the file entirely | 1 flow, walking the reflective body | 1 flow, walking the reflective body |

The middle row shows the declaration *is* acted on; the top row shows its index
is not what selects the argument; the bottom row is the same reflective-body
result A4 now records for `javasrc2cpg`. Separately, `Bridge.deposit` declared
`1 -> 2 "payload"` also tainted the sibling field `box.spare` — the access-path
destination can be *written* and does not discriminate, which is the exact
condition the preregistration named when it marked template 8 unverified for
Joern. A2 supersedes both findings with a stronger and more general one, so
neither becomes an amendment of its own.

**Semgrep CE, template 6 (now `unsupported`, A3).** The pre-amendment Java run
scored 11 of 12, the single miss being template 6's positive. A crossed four-run
probe over the two selectivity cells and the kill cell, on fixtures this row did
not change, gives the reason:

| `taint_assume_safe_functions` | `pattern-sanitizers` | T6 positive (`Clean.sanitize`) | T6 negative (`Clean.scrub`) | T5 negative (`Clean.scrub`) |
| --- | --- | --- | --- | --- |
| `true` (committed) | declared | 0 | 0 | 0 |
| `true` | removed | 0 | 0 | 0 |
| `false` | declared | 1 | 0 | 0 |
| `false` | removed | 1 | 1 | 1 |

Rows one and two are identical: with the option on, removing the declaration
changes nothing, which is the definition of a declaration that is not
load-bearing on those cells. This is A3's finding reproduced independently on
Java, from the opposite direction — A3 was made on Python's evidence — and
template 6 is now decided by the partition, so the cell is `unsupported` rather
than a published false negative. It was not tuned around: declaring a propagator
for `Clean.sanitize` would recover the cell, and category P is one this
partition does not award CE in the first place.

## Infer — the fifth adapter (Amendment A13, 2026-09-01)

Java is the one wave-M1 language the pinned Infer v1.3.0 executes, so it is
the one language Infer's modeling row
([Amendment A13](modeling-matrix.md#a13--2026-09-01-infer-joins-the-modeling-matrix-with-a-field-evaluated-partition-row))
covers — JavaScript and Python have no Infer modeling denominator at all.
The partition was field-evaluated by execution over this document's own
committed fixtures before the row existed
(`reports/raw/amendment-a13-infer-partition/`): categories S, P (template 3
alone — the propagator surface binds no input position), and Z are scored,
five templates, through the committed
`adapters/infer/config/model-java.json` with exact `class_names` +
`method_names` identity matchers.

The retained run — `reports/infer-java-modeling.json`, evidence under
`reports/raw/infer-java-modeling/` — decides **all ten scored assertions
correctly**: both declared-source/sink pairs, the opaque-propagator pair
(the reflective body carries nothing unaided; the declared `carry` model
carries it; the undeclared `block` does not), and both sanitizer pairs
(suppression through the declared `scrub`, no suppression through the
undeclared `sanitize`). The fourteen declined assertions are retained
`preregistered-modeling-partition` capability decisions. See
[the Infer adapter notes](../adapters/infer/README.md) for the measured
boundaries and the three gated silent-configuration hazards.

## OpenTaint joins the row — Amendment A22, 2026-09-01

None of the sections above move for this adapter either. OpenTaint — issue #17's adapter, whose
[Java propagation kernel](java-kernel.md) landed with v0.6.0 — joined this
matrix afterwards on the rollout plan's own terms: a preregistered partition
row, added by
[Amendment A22](modeling-matrix.md#a22--2026-09-01-opentaint-joins-the-modeling-matrix-with-a-preregistered-java-partition-row)
and decided by executing the pinned analyzer over these very fixtures with
probe declarations **before** its first scored run
(`scripts/probe-opentaint-modeling-surface.sh`, evidence under
`reports/raw/opentaint-modeling-surface-probe/`). Java is this adapter's only
modeling language — the engine analyzes JVM bytecode — so this row is the whole
of its modeling denominator.

**The encoding.** One committed Semgrep-syntax rule,
`adapters/opentaint/rules/model-java.yaml` (rule id `dfb-opentaint-model`,
checked in every retained rule-load trace), declaring exactly the categories
the partition scores — S, P, and Z — and nothing else. Two spellings are the
ones worth recording:

- **Propagators are assignment-shaped.** The engine matches patterns against
  its lifted JVM IR, where a nested call is a temporary assignment, so
  `$DFBTO = Opaque.carry($DFBFROM)` names the call's result as a metavariable
  and expresses the `in: 0, out: return` binding that Semgrep CE's own surface
  cannot. Template 4's `$DFBTO = Opaque.select($DFBIGNORED, $DFBFROM)` binds
  position 1 and leaves position 0 undeclared, and the engine honors the
  position.
- **No load-bearing switch is needed.** The probe measured that with no
  propagator declared the reflective body carries nothing: the engine has no
  optimistic unmodeled-call default, so it is `require-model`-shaped out of the
  box, and `primitive-tracking: true` is carried only for consistency with the
  kernel templates (every modeling fixture is String-typed).

**The run.** 2026-09-01, against the pinned release
`analyzer/2026.08.27.17eb0fe`, both assets verified by witnessed digest before
any case; fixtures compiled per case with `javac` (a harness step outside the
timed boundary) and reconciled under the same `AnchorDialect::JavaMember` the
other four adapters' modeling runs use. Report:
`reports/opentaint-java-modeling.json` (configuration hash `07c652c2…`), raw
evidence under `reports/raw/opentaint-java-modeling/`.

| Adapter | Scored | `reached` | `not-reached` | `inconclusive` | `unsupported` | Matches |
| --- | --- | --- | --- | --- | --- | --- |
| OpenTaint `2026.08.27.17eb0fe` | 12 (S, P, Z) | 6 | 6 | 0 | 12 | **12 / 12** |

Per category: S 4/4, P 4/4, Z 4/4; O, E, and B are declined by the partition
with the amendment's rationale retained per cell. **12/12 is not comparable to
any other adapter's number** — it is over this adapter's own denominator — and
it is not a propagation score. What it does add to the row's record: OpenTaint
is the first adapter besides CodeQL to score category P at all, and its
category-Z pair needed no safe-function assumption, so template 6's
selectivity positive — the cell Amendment A3 had to withdraw from Semgrep CE —
decides correctly here.

Its tool-native mirror is the opposite corner:
[the Java native row](java-native.md) records OpenTaint at 0 / 6 under
[Amendment A23](native-profile.md#a23--2026-09-01-opentaint-joins-the-tool-native-profile-at-0--6-and-the-shipped-models-archive-is-ruled-shipped-product),
because the pinned release ships propagation models and no endpoint catalog.
Engine capability and product packaging, side by side, on one binary — which is
what the two profiles exist to separate.

## Reproduction

```bash
cargo run -- run-bifrost-modeling --language java --bifrost /path/to/bifrost
cargo run -- run-codeql-modeling  --language java --codeql  /path/to/codeql
cargo run -- run-infer-modeling   --language java --infer   /path/to/infer-osx-arm64-v1.3.0/bin/infer
cargo run -- run-joern-modeling   --language java --joern   /path/to/joern-cli/joern
cargo run -- run-semgrep-modeling --language java --semgrep /path/to/semgrep
cargo run -- run-opentaint-modeling --language java \
  --analyzer-jar /path/to/opentaint-project-analyzer.jar \
  --models-archive /path/to/opentaint-models.tar.gz

scripts/probe-java-modeling-load-bearing.sh \
  --bifrost /path/to/bifrost --codeql /path/to/codeql \
  --joern /path/to/joern-cli/joern --semgrep /path/to/semgrep
scripts/probe-infer-modeling-partition.sh \
  --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
scripts/probe-opentaint-modeling-surface.sh \
  --analyzer-jar /path/to/opentaint-project-analyzer.jar \
  --models-archive /path/to/opentaint-models.tar.gz
```

Run them sequentially, never concurrently. Each writes
`reports/<tool>-java-modeling.json` with retained evidence under
`reports/raw/<tool>-java-modeling/`; none of the paths collides with a
report the v0.4.0 freeze binds, and the OpenTaint runner re-verifies both
release-asset digests before any case.

## FlowDroid — the seventh adapter (Amendment A18, 2026-09-01)

[Amendment A18](modeling-matrix.md#a18--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row)
added the matrix's sixth adapter after this row's original four-tool run and Infer's A13 row, with
a **Java-only** partition preregistered on retained probe evidence
(`reports/raw/load-bearing-java-modeling/flowdroid-*.json`, produced by
`scripts/probe-flowdroid-modeling-load-bearing.sh`) before the first scored
run. Nothing above this section is re-run or re-stated by it: the four
original reports stand, and FlowDroid's arrives beside them.

**The encoding.** FlowDroid's declarations use the two surfaces the adapter's
kernel already established plus one new committed artifact:

| Adapter | Artifact | Categories it declares |
| --- | --- | --- |
| FlowDroid 2.15.1 | `adapters/flowdroid/summaries/model-java/` (three StubDroid summary XMLs), plus the per-case marker-resolved sources-and-sinks file | S, P, Z (template 5), O |

The endpoint identities (category S, and every case's `dfb_source`/`dfb_sink`)
resolve per case from the fixtures' own markers and are witnessed as Soot
signatures from the compiled classes, exactly as the kernels do. The
propagator, sanitizer, and summary declarations are StubDroid `flow` and
`clear` stanzas — `carry` (`in: 0` → `out: return`), `select` (`in: 1` →
`out: return`, the positional cell), `scrub` (a `clear` on parameter 0),
`pass`/`hold` (through and explicit no-flow), and `deposit`
(`in: 0` → `out: 1.payload`, a field-destination access path) — activated as
`-tw STUBDROID -t <dir>`, which replaces the release default's bundled
summary provider so the committed declarations are the only summaries in the
run. Categories E and B are absent from the artifact, as the partition
requires: no entry-root declaration surface exists (probed — a parameter
source on the uncalled handler parses and creates no root), and no surface
carries a store identity or key position.

**Results.** Run on 2026-09-01 against the pinned, digest-witnessed 2.15.1
jar; retained in `reports/flowdroid-java-modeling.json` with raw evidence
under `reports/raw/flowdroid-java-modeling/`.

| Adapter | Scored | `reached` | `not-reached` | `inconclusive` | `unsupported` | Matches |
| --- | --- | --- | --- | --- | --- | --- |
| FlowDroid 2.15.1 | 14 (S, P, Z template 5, O) | 7 | 7 | 0 | 10 | **14 / 14** |

| Category | FlowDroid |
| --- | --- |
| S — sources and sinks | 4/4 |
| P — propagators | 4/4 |
| Z — sanitizers | 2/2 (template 6 declined, A18) |
| O — summaries | 4/4 |
| E — entry points | — (A18) |
| B — persistence | — (A18) |

Fourteen of fourteen, over the second-largest scored denominator in the row.
Worth stating the way the matrix's framing rules require: this is a modeling
score, not a propagation score. The same engine's Java kernel misses every
stored-function-indirection positive and over-approximates container
elements; here it activates every declaration it can express, positionally
faithfully and field-precisely. The two axes are independent, which is this
tier's founding observation, and FlowDroid is now its clearest single-engine
demonstration.

Each scored case's timing sidecar records `compile`, `dex`, and `analyze`
phases (the three adapter-observable subprocess boundaries;
[latency-tier Amendment A20](latency-tier.md#a20--2026-09-01-flowdroids-modeling-population-declares-three-subprocess-phases)),
of which only `analyze` is an analyzer number.

**Reproduction, appended to the sequence above:**

```bash
cargo run -- run-flowdroid-modeling --language java \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar \
  --d8-jar r8-8.5.35.jar

scripts/probe-flowdroid-modeling-load-bearing.sh \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar --d8-jar r8-8.5.35.jar
```
