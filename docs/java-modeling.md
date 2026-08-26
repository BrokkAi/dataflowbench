# Java taint-modeling matrix

Java is wave M1's first language for the
[benchmark-controlled taint-modeling matrix](modeling-matrix.md). This document
is the Java realization of that preregistration: how each of the twelve
templates is spelled in Java, how each of the four adapters encodes the same
analyzer-neutral declarations natively, and what the four runs produced.

It is a *report*, not a contract. Every definition it cites — the templates, the
negative mechanisms, the capability kinds, the per-tool partition — is fixed by
[the preregistration](modeling-matrix.md), which merged before any of this was
authored and which this document does not amend. Where a run disagreed with what
the preregistration expected, the disagreement is published as observed and
flagged as a *proposed* amendment for a separate, dated change.

Modeling assertions are `score_tier: "modeling"`. They are never in Java's core
denominator, never pooled with [the propagation kernel](java-kernel.md), and no
number here is ever added to a number there. The two scorecards answer different
questions: the kernel asks whether an engine can follow flow it can see, and this
matrix asks whether it can be told things.

## The population

Twenty-four assertions — the twelve templates × positive/negative — under
`cases/taint/java/model-<short>-{positive,negative}/`, with case IDs
`dfb-taint-java-model-<short>-<polarity>`. All are `track: taint`,
`score_tier: modeling`, `model_profile: benchmark-controlled`, provenance
`authored`/`DataFlowBench`, revision `m3-modeling-java`, license MIT.

Every fixture is stdlib-only Java in package `dataflowbench.taint` and compiles
warning-free under `javac 21.0.8 --release 21 -Xlint:all -Werror` — the same
host toolchain the CodeQL Java adapter traces with `javac -d classes`. Eleven
templates are a single `.java` file; template 7 is two, because its summarized
procedure has to be external-shaped.

`validate_modeling_cases` in `src/main.rs` enforces the balance and the required
set: exactly one positive and one minimally different negative for each of the
preregistered twelve, one model profile across all twenty-four, and the
structural implication that a `dfb-template-model-` template and the `modeling`
tier imply each other.

### Template realizations

The declared entities are the preregistration's own: `Config.fetchRemote`,
`Audit.record`, `Opaque.carry` / `Opaque.select`, `Clean.scrub`, `Bridge.pass` /
`Bridge.deposit`, `Handler.onRequest` / `Handler.onDeclared`, and `Store`. Each
lives as a package-private top-level class in its fixture's file, so its
fully-qualified name is stable across fixtures — which is what lets the Joern
flow-semantics artifact bind one entry per entity rather than one per case.

| # | Template | Java realization |
| --- | --- | --- |
| 1 | `declared-source` | `final class Config` with two constant-returning statics, `fetchRemote` and `fetchLocal`. The positive sinks `Config.fetchRemote()`, the negative `Config.fetchLocal()`. Both bodies return a string literal, so an engine that reads them learns nothing that distinguishes the two. |
| 2 | `declared-sink` | `final class Audit` with two one-parameter statics that both drop their argument, `record` and `discard`. The positive calls `Audit.record(dfb_source())`, the negative `Audit.discard(dfb_source())`. |
| 3 | `opaque-propagator` | `final class Opaque` with `carry` and `block`, whose bodies are byte-identical reflective self-dispatch: `Opaque.class.getMethod(target, String.class).invoke(null, value)` with `target` a local `String` constant naming a public `identity` method. The positive sinks `Opaque.carry(dfb_source())`, the negative `Opaque.block(dfb_source())`. |
| 4 | `propagator-position` | `Opaque.select(String first, String second)` with the same reflective body, forwarding `second`. The positive is `Opaque.select("clean", dfb_source())` — taint at declared position 1 — and the negative `Opaque.select(dfb_source(), "clean")`, the identical call with taint at the undeclared position 0. |
| 5 | `sanitizer-kill` | `final class Clean` with the identity method `scrub`. The positive is the bare flow `dfb_sink(dfb_source())`; the negative routes the same flow through `Clean.scrub`. `Clean` is present in both fixtures, so the pair differs only in the routing. |
| 6 | `sanitizer-selectivity` | `Clean` with two identity methods, `scrub` and `sanitize`. The positive flows through the *undeclared* `sanitize` and must still be reported; the negative flows through the declared `scrub`. |
| 7 | `summary-through` | `Bridge.java`, a second fixture file, holding `Bridge` with two identity methods `pass` and `hold`. Both bodies say flow; the summaries disagree, which is what makes reading-the-body and activating-the-summary distinguishable. |
| 8 | `summary-field` | `final class Box { String payload; String spare; }` and `static void deposit(String value, Box box) { }` with an empty body. Both cells call `Bridge.deposit(dfb_source(), box)`; the positive sinks `box.payload`, the negative the sibling `box.spare`. |
| 9 | `entrypoint-parameter` | `final class Handler` with two uncalled one-parameter methods `onRequest` and `onIgnored` with byte-identical bodies (`dfb_sink(input);`) and no top-level code invoking either. The positive anchors on `onRequest`, the negative on `onIgnored`. |
| 10 | `entrypoint-selectivity` | The same shape with `onDeclared` and `onUndeclared`, both plausible roots in one class. |
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

## The four model artifacts

The same three-part declaration — entity identity, role, binding semantics — in
four native surfaces. Each is hash-bound into its report's
`configuration_hash`.

| Adapter | Artifact | Categories it declares |
| --- | --- | --- |
| Bifrost v0.10.6 | `adapters/bifrost/policies/model-java.rqlp` | S |
| CodeQL 2.26.3 | `adapters/codeql/queries/JavaModeling.ql` | S, P, Z, O, E, B |
| Joern 4.0.610 | `adapters/joern/semantics/model-java.semantics` + `adapters/joern/queries/modeling.sc` | S, P, Z, O, E, B |
| Semgrep CE 1.174.0 | `adapters/semgrep/rules/model-java.yaml` | S, Z, E |

**An artifact never declares a category its tool's partition marks
unsupported.** The partition decides those cells before the tool is invoked, so
a declaration for one would smuggle a scored cell past a capability decision
already made. That is why the Bifrost policy carries sources and sinks only and
the Semgrep rule carries no propagator and no summary.

The CodeQL query sits at `adapters/codeql/queries/JavaModeling.ql` rather than
under a `java/` subdirectory. Java's CodeQL pack *is* the adapter root —
`adapters/codeql/qlpack.yml` declares `dataflowbench/codeql-java`, and
`JavaKernel.ql` already lives beside it — and a query outside a pack resolves no
`codeql/java-all` dependency. That is a location, not a declaration surface.

The Joern flow-semantics file carries no comments. The pinned distribution's
`FullNameSemanticsParser` returns an empty list for a file whose first line is a
`//` comment, verified against 4.0.610, so the file is declarations only and its
commentary lives here and in the adapter README.

## Anchor reconciliation on this tier

A modeling fixture carries **both** halves of its pair by construction: the
declared entity and its undeclared sibling live in one type, because that is
what the templates say makes the negative a negative. Category E makes the
consequence unavoidable — a handler needs no caller, so the *declared* handler's
flow is present in the negative fixture too, on a callsite of the same sink
function. Reconciling a finding against the sink anchor alone would read that
sibling's flow as this case's finding.

So every modeling adapter reconciles the **source side as well**: a finding
counts only when it lies in the region the case's own source anchor governs —
the anchored declaration, its body, and the callsites of the anchored source
function — *and* on a callsite of the anchored sink function. The region is
computed by indentation rather than by block punctuation, so one rule serves a
braced body and an indented one.

One modeling-specific reading follows from that. On a kernel, a finding that
reconciles to nothing is unusable evidence and stays `inconclusive`. Here it is
*expected* and fully attributable — it is the pair's other entity — so it is
`not-reached` with the count retained in the result's diagnostics. Evidence with
no usable location at all is still unreadable and still `inconclusive`.

The Joern normalization additionally departs from the kernel's on one point: the
kernel reports `inconclusive` when a run bound zero source or zero sink nodes,
because on a kernel an unobserved endpoint means the run never saw the
assertion. On this tier an unobserved endpoint is frequently *the measurement* —
`Config.fetchLocal` and `Audit.discard` are undeclared on purpose, so zero bound
nodes is the correct and informative answer, and converting it to `inconclusive`
would hide the one thing category S exists to show. A run that produced no CPG
at all is still `runner-error`.

## Observed results

Four runs, sequential, on the pinned distributions. `unsupported` is capability
coverage, `inconclusive` is execution coverage, and neither is ever converted
into a negative. No run produced an `inconclusive` or a `runner-error` result.

### The three-way split

| Adapter | Scored | `unsupported` | `inconclusive` | Correct on the scored | Report |
| --- | --- | --- | --- | --- | --- |
| Bifrost v0.10.6 (`18d09c57`) | 4 | 20 | 0 | **4 / 4** | `reports/bifrost-java-modeling.json` |
| CodeQL 2.26.3 | 24 | 0 | 0 | **24 / 24** | `reports/codeql-java-modeling.json` |
| Joern 4.0.610 | 24 | 0 | 0 | **20 / 24** | `reports/joern-java-modeling.json` |
| Semgrep CE 1.174.0 | 12 | 12 | 0 | **11 / 12** | `reports/semgrep-java-modeling.json` |

The scored column is the preregistered partition, not an outcome: Bifrost
declined five of six categories and Semgrep CE three, both decided from the
template ID before the binary ran. **These four numbers are not comparable to
one another**, because they are over different denominators, and none of them is
comparable to anything on [the Java propagation kernel](java-kernel.md).

### Per category

`—` is a category the partition declines for that tool. Each cell is
correct-of-4.

| Category | Bifrost | CodeQL | Joern | Semgrep CE |
| --- | --- | --- | --- | --- |
| S — declared sources and sinks | 4/4 | 4/4 | 4/4 | 4/4 |
| P — declared propagators | — | 4/4 | 3/4 | — |
| Z — declared sanitizers | — | 4/4 | 4/4 | 3/4 |
| O — opaque summaries | — | 4/4 | 3/4 | — |
| E — framework entry points | — | 4/4 | 4/4 | 4/4 |
| B — persistence boundaries | — | 4/4 | 2/4 | — |

### Bifrost v0.10.6 — `reports/bifrost-java-modeling.json`

24 results: 2 `reached`, 2 `not-reached`, 20 `unsupported`. Category S is
**4/4** — 2 true positives, 2 true negatives, no false positive, no false
negative — so both declared-source and declared-sink activation bind by entity
identity, and neither undeclared sibling (`Config.fetchLocal`, `Audit.discard`)
is picked up.

The twenty declined assertions retain the preregistration's rationale verbatim
in a `retained-capability-decision` document beside the report, keyed by
template identity. Nothing about them is a result about Bifrost's analysis; they
are five categories a standalone policy CLI does not expose today.

One preregistration cell can now be answered, and it is the one this run existed
to answer first: **v0.10.6 accepts
`:call-modeling (call-modeling :unmodeled require-model)`.** The partition
recorded category P as *to be verified* partly because that was unknown.
Accepting the switch is necessary but not sufficient for promoting P — a
propagator or transform section still has to be shown to lower — so the cell
stays where the preregistration put it, and the observation is recorded here for
whoever writes that amendment.

### CodeQL 2.26.3 — `reports/codeql-java-modeling.json`

24 results: 12 `reached`, 12 `not-reached`. **24/24** — 12 true positives, 12
true negatives, no false positive and no false negative anywhere in the matrix.
Every category the partition awarded it is answered exactly as declared,
including the two the preregistration flagged as needing implementation-time
verification: template 8's store-through summary (encoded as a step from the
declared argument onto reads of the declared field of the declared object) and
category B's roundtrip (paired steps conditioned on equal constant keys and on
the store identity).

This is the result a query language whose data-flow configuration *is* a
declaration surface should produce, and it is not a ranking. What it does
establish is that the twelve templates are *satisfiable as preregistered* — each
one has at least one engine that gets it right — so a miss elsewhere in this
matrix is a statement about that engine and not about a badly posed cell.

### Joern 4.0.610 — `reports/joern-java-modeling.json`

24 results: 12 `reached`, 12 `not-reached`. **20/24** — 10 true positives, 10
true negatives, 2 false positives, 2 false negatives. Categories S, Z, and E are
4/4. The four misses fall into three distinct engine facts, each worth
publishing on its own terms.

**Positional fidelity did not hold (template 4's negative, a false positive).**
The semantics entry declares `Opaque.select` as index 2 → return, and taint at
the *undeclared* index 1 reached the sink anyway. The declaration is still
load-bearing — replacing the mapping with `NilSemantics` removes both cells'
findings, and removing the entry entirely lets the engine walk the reflective
body instead — so this is not "the model was ignored". It is narrower and more
interesting: the mapping is applied, and its **index is not enforced**. The
preregistration expected the opposite ("the index is the mapping's own key, so
positional fidelity is native rather than emulated"), and the disagreement is
published as observed.

**The access-path destination did not discriminate (template 8's negative, a
false positive).** `Bridge.deposit` is declared `1 -> 2 "payload"`, and the
sibling field read `box.spare` was reported as tainted too. The preregistration
recorded exactly this as unverified — *"`FlowPath` is the surface; its
access-path expressiveness for a field destination is to be verified at
implementation, and template 8 alone is unsupported for Joern if it cannot be
expressed."* It can be *written*; it does not discriminate. Under the document's
own rule this is the shape of a proposed amendment for that cell, dated and
separate.

**The persistence roundtrip did not close (both category-B positives, false
negatives).** The two boundary declarations load and the negatives are correct,
but no flow crosses from `Store.put`'s value parameter to `Store.get`'s return
in either the type-bound or the instance-bound spelling. The preregistration
chose to *leave the key and instance discrimination to the engine* — the model
declares the boundary, the analysis decides whether the roundtrip closes — and
on this engine it does not close at all. That is a coverage result about Joern's
handling of a store modeled through a receiver, not a defect in the
declarations, and the two correct negatives are correct for the same reason the
positives are wrong, which is exactly the case the balanced-pair design exists
to make visible.

### Semgrep CE 1.174.0 — `reports/semgrep-java-modeling.json`

24 results: 5 `reached`, 7 `not-reached`, 12 `unsupported`. **11/12** on the
scored partition — 5 true positives, 6 true negatives, no false positive, one
false negative.

Categories S and E are 4/4. Category E is worth restating because it is the
counter-intuitive one and the preregistration called it in advance: an
intraprocedural engine handles an uncalled handler *well*, because the sink is
inside the handler's own body and the absence of a caller is the normal case
rather than a problem. The declaration binds selectively — the undeclared
siblings `onIgnored` and `onUndeclared` produce nothing.

The single miss is **template 6's positive**, where the flow passes through the
*undeclared* sanitizer-shaped `Clean.sanitize` and must still be reported. It is
not reported, and the reason is the load-bearing option itself: see below.

## Load-bearing verification

The preregistration's rule is that the model, not the propagation, is what is
being scored — a cell the tool's default already decides is not a measurement.
Every scored tool has at least one demonstrated counterfactual here: remove the
declaration, and the finding goes away. Each probe removes **one** declaration
from the committed artifact, leaves the rest intact, and re-runs the affected
cell together with a control cell that depends on a different declaration.

| Tool | Category | Declaration removed | Affected cell | Control cell |
| --- | --- | --- | --- | --- |
| Bifrost | S | the `Config.fetchRemote` `:sources` entry | template 1 positive: 1 finding → **0** | template 2 positive: 1 → 1 |
| CodeQL | P | the `Opaque.carry` `isAdditionalFlowStep` clause | template 3 positive: 1 result → **0** | template 4 positive: 1 → 1 |
| Joern | Z | the `Clean.scrub` semantics line (8 of 9 entries kept) | templates 5 and 6 negatives: 0 flows → **1 each** | template 7 negative: 0 → 0 |
| Semgrep CE | S | the `Config.fetchRemote(...)` `pattern-sources` entry | template 1 positive: 1 finding → **0** | template 2 positive: 1 → 1 |
| Semgrep CE | E | the `void onRequest($T $P) { ... }` source | template 9 positive: 1 finding → **0** | template 10 positive: 1 → 1 |

CodeQL's probe is also the check that template 3 is doing what it was designed
to do. The reflective body is the construct the v0.4.0 freeze establishes no
engine follows, and with the propagator step removed CodeQL indeed reports
nothing — so the positive cell can only be `reached` because the model was
activated, which is the whole reason the template is assertable.

### Where the requirement did not hold: Semgrep CE, category Z

The load-bearing gate obliges a Semgrep modeling rule to set
`options: taint_assume_safe_functions: true`, because without it the pinned CE
engine carries taint from any tainted argument to a call's result. On this
population that option **also suppresses the flow through the declared
sanitizer**, so the sanitizer declaration is inert and the default is what
decides the category-Z cells. Four runs over the two selectivity cells and one
kill cell, with the two variables crossed:

| `taint_assume_safe_functions` | `pattern-sanitizers` | T6 positive (`Clean.sanitize`) | T6 negative (`Clean.scrub`) | T5 negative (`Clean.scrub`) |
| --- | --- | --- | --- | --- |
| `true` (committed) | declared | 0 | 0 | 0 |
| `true` | removed | 0 | 0 | 0 |
| `false` | declared | 1 | 0 | 0 |
| `false` | removed | 1 | 1 | 1 |

Rows one and two are identical: with the option on, removing the declaration
changes nothing, which is the definition of a declaration that is not
load-bearing. Rows three and four are the pair the preregistration's own probe
found: with the option off, the `Clean.scrub` declaration is exactly what
decides both negatives, and template 6's positive is reported correctly through
the undeclared sibling.

So on Java the option and the requirement point in opposite directions. Category
Z is scored here as the preregistration and the runner gate require — option on,
sanitizer declared — and the outcome (3/4, with template 6's positive as a false
negative) is published as observed. **It is not tuned around.** Declaring a
propagator for `Clean.sanitize` would recover the cell and would be tuning
toward the expected polarity, and category P is one this partition does not
award CE in the first place.

The proposed amendment this run supports is narrow: for Semgrep CE, the
load-bearing configuration for category Z is
`taint_assume_safe_functions: false`, not `true`, because on a category-Z
fixture the sanitizer's own call is the call the option neutralizes. Writing
that is a dated amendment on [the preregistration](modeling-matrix.md), in its
own commit, and nothing here anticipates it.

### Joern's propagator declaration, separated from its index

The category-P false positive above deserves its own counterfactual, because
"the model was ignored" and "the model was applied to the wrong position" are
different findings and only one of them is true.

| `Opaque.select` semantics | T4 positive (taint at declared position 1) | T4 negative (taint at undeclared position 0) |
| --- | --- | --- |
| `2 -> -1` (committed) | 1 flow | 1 flow |
| declared with no mapping (`NilSemantics`) | 0 | 0 |
| absent from the file entirely | 1 flow, walking the reflective body | 1 flow, walking the reflective body |

The middle row is the demonstration: the declaration is what the engine acts on,
and switching it from a mapping to no-flow removes both findings. The top row is
the defect: the mapping's index is not what selects the argument. The bottom row
is why the file must declare `select` at all — with no entry, Joern walks the
reflective body through `Method.invoke`'s `Object[]` argument and reaches the
sink on its own.

## Proposed amendments

None applied. Recorded here for a separate, dated change on
[the preregistration](modeling-matrix.md)'s own terms:

1. **Semgrep CE, category Z, load-bearing configuration.** The requirement's
   `taint_assume_safe_functions: true` makes the sanitizer declaration inert on
   a category-Z fixture; the four-way probe above is the evidence.
2. **Joern, template 8.** `FlowPath`'s access-path destination can be written
   but does not discriminate the declared field from its sibling on 4.0.610 —
   which is the condition the preregistration itself named for that cell.
3. **Joern, category P, positional fidelity.** The preregistration states the
   mapping's index is native; on 4.0.610 it is not enforced.
4. **Bifrost, `require-model`.** The pinned build accepts it. This removes one
   of the two stated obstacles to promoting Bifrost's category P; the other —
   showing that a propagator or transform section actually lowers — is
   untouched, so the cell does not move on this evidence alone.

## Reproduction

```bash
cargo run -- run-bifrost-modeling --language java --bifrost /path/to/bifrost
cargo run -- run-codeql-modeling  --language java --codeql  /path/to/codeql
cargo run -- run-joern-modeling   --language java --joern   /path/to/joern-cli/joern
cargo run -- run-semgrep-modeling --language java --semgrep /path/to/semgrep
```

Run them sequentially, never concurrently. Each writes
`reports/<tool>-java-modeling.json` with retained evidence under
`reports/raw/<tool>-java-modeling/`; none of the eight paths collides with a
report the v0.4.0 freeze binds.
