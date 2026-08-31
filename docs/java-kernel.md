# Java propagation kernel

Java is the origin population of the semantic kernel. The sixteen scored
propagation templates were authored here first, and every other language kernel
is a port of them: the [applicability matrix](applicability-matrix.md)
classifies each cell against the Java shape, and
`validate_kernel_balance` in `src/main.rs` enforces that a ported kernel
reproduces the Java classic template identities exactly. Java's own contract
was therefore recorded across
[the adapter contract](adapters.md) and the per-adapter READMEs rather than in a
file of its own. This document is that file, and its subject is the expansion.

Java also carries a population of the
[benchmark-controlled taint-modeling matrix](java-modeling.md), the last of
wave M1's three rows to land. That is a
separate tier with a separate denominator and it is never pooled with anything
below: no number in this document is ever added to a number in that one.

A third Java population, on the same `modeling` tier but a disjoint
`model_profile`, asks what each tool ships rather than what it can be told: six
templates and twelve assertions over real JDK APIs. See
[the Java tool-native probe set](java-native.md). It is pooled with neither of
the two above.

## Classic core: 16 templates, 32 assertions

Unchanged and frozen in v0.3.0. The sixteen `dfb-template-*` identities in
`KERNEL_TEMPLATE_IDS` each have exactly one `positive` and one minimally
different `negative` case under `cases/taint/java/`, all
`model_profile: benchmark-controlled`, all using the `dfb_source`/`dfb_sink`
endpoint names except the two direct-propagation assertions, which predate that
convention and are frozen with the endpoint names they were published with.
Java additionally carries two `calibration` cases —
`dfb-template-one-hop-relay` and `dfb-template-modeled-external-summary` —
which are outside the scored denominator and stay there.

## Challenge-tier expansion: +13 templates, 58 assertions

[The challenge-tier preregistration](challenge-tier.md) fixes thirteen further
templates, all thirteen of them applicable to Java, before any of them was
authored or run. Java is wave 1. Its `CHALLENGE_ROLLOUT` row is flipped, so
**Java's v0.4.0 expanded core denominator is 29 templates and 58 assertions**,
exactly the figure the preregistration's denominator table fixes.

The v0.3.0 sixteen-template core and this expanded core are different
populations of the same name and are never compared number to number. The
classic 32 are reported separately from the challenge 26 throughout this
document for that reason.

Every fixture is a single `.java` file in package `dataflowbench.taint`, uses
only the JDK, and compiles warning-free under `javac 21.0.8 -Xlint:all` — the
host toolchain the CodeQL Java kernel already traces with `javac -d classes`.
Provenance is `authored`/`DataFlowBench`, revision `m3-challenge-java`,
license MIT.

### Adaptation notes

Twelve of the thirteen cells are **directly applicable** to Java and are
authored with the construct the preregistration names. One cell is
**language-adapted**, and it is the one cell the matrix classifies as adapted.

| Stratum | Template | Java construct |
| --- | --- | --- |
| A | `dfb-template-chal-reflective-invocation` | `Class.getMethod(name, int.class)` with `name` in a local `String`, invoked through `Method.invoke`. The positive's name constant is `"leak"`, the negative's `"drop"` — a sibling method on the same receiver that discards its argument and sinks a constant. |
| A | `dfb-template-chal-computed-property` | **Language-adapted.** Java has no computed member-access syntax, so the write and the read go through `java.lang.reflect.Field`: `Holder.class.getDeclaredField(key).setInt(holder, dfb_source())` and a matching `getInt`. The positive uses one key variable for both; the negative uses two provably distinct constant keys (`"tainted"`, `"clean"`). This is the adaptation the preregistration records for Java and the one SecuriBench Micro's `datastructures` cases use. |
| A | `dfb-template-chal-dispatch-table` | `HashMap<String, IntUnaryOperator>` with two lambda entries, selected by a `String` key variable and invoked with `applyAsInt`. Stdlib only: `java.util.HashMap` plus a `java.util.function` interface. |
| B | `dfb-template-chal-closure-capture` | A `Runnable` lambda capturing an effectively-final tainted local, returned from the creating method and invoked by the caller, with the sink inside the closure body. The negative captures the clean local instead; the tainted local is still created, so the separation is `unrelated-value` and not a missing source. |
| B | `dfb-template-chal-function-field` | A `Holder` class with an `IntConsumer fn` field. Two instances, one holding a sinking lambda and one an argument-dropping lambda; a separate `fire(Holder, int)` method reads the field and calls it. The negative passes the second holder — `object-separation`. |
| B | `dfb-template-chal-callback-registration` | A `Registry` with a `List<IntConsumer>`, a `register` method, and a `fire(int)` driver that iterates and invokes. Zero frameworks: twenty lines of `java.util`. The negative's registered callback ignores its parameter and sinks a constant. |
| B | `dfb-template-chal-anonymous-implementation` | Two anonymous inner classes implementing a locally declared one-method interface `Handler`, assigned to interface-typed variables and invoked through them. Neither captures anything, which is what keeps this distinct from the closure-capture cell. The negative invokes the argument-dropping implementation. |
| C | `dfb-template-chal-map-iteration` | `HashMap<String, Integer>`, retrieved by `for (Map.Entry<String, Integer> e : map.entrySet())` with the sink in the loop body — never by `get`. The negative iterates a second, disjoint map. |
| C | `dfb-template-chal-nested-access-path` | Three nested classes giving `a.b.c.value`, written and read at the identical depth-3 path. The negative reads the sibling `a.b.c.other`. |
| C | `dfb-template-chal-element-object` | `Item[] items = new Item[] {new Item(), new Item()}`; the tainted value sits in `items[0].value`. The negative reads `items[1].value`, so deciding it needs element separation *and* field separation together. |
| D | `dfb-template-chal-deep-relay-chain` | Six same-file static methods `relay1` … `relay6`, no branching and no state, with the sink at hop 6. The negative feeds the identical chain a clean constant and discards the source's value into an unused local. |
| D | `dfb-template-chal-recursive-carry` | `carry(value, depth)` returning `value` at `depth == 0` and `carry(value, depth - 1)` otherwise, invoked with `depth = 5`. The negative's base case returns a clean constant — an `overwrite-kill` marked `DFB-KILL:`, following the local-overwrite convention. |
| D | `dfb-template-chal-context-pair-depth2` | The same `wrapper`/`helper` pair reached through two distinct two-deep call paths, `outerTainted` and `outerClean`. |

**One construction note, on the context-pair cell.** The preregistration
sketches it as `outerTainted() -> wrapper(x) -> helper(x) -> sink`. Written that
way the negative would still contain a live source-to-sink path through
`outerTainted`, and a negative case in this benchmark asserts that *no* flow
exists between its anchors — an analyzer that found that path would be right and
the case would be wrong. The Java fixtures therefore carry the value back by
return (`helper` returns it, `wrapper` returns it, each outer context returns
it) and the sink takes the tainted result in the positive and the clean result
in the negative. Both outer contexts, and both two-deep paths into the shared
helper, are present in both cells. This is exactly how the classic
`dfb-template-call-context-separation` pair — the k = 1 template this one
extends — is built in every language of the corpus, and it preserves the
semantic intent, the polarity, and the `call-context-separation` mechanism
unchanged. It is a fixture-realizability note, not a template amendment.
[The Python kernel contract](python-kernel.md) records the identical decision
for the same cell, for the same reason and in the same form.

### Feature tags and declared capabilities

Taken verbatim from the preregistration, which fixes them per template:
`reflective-dispatch` (1, and the reflective adaptation of 2), `higher-order`
(3–7), `computed-access` (2, 8), `ambiguous-dispatch` (3, 7),
`heap-access-path` (9, 10), `interprocedural-deep` (11, 13), and `recursive`
(12); with `expected_analysis_capability.kind` values
`reflective-dispatch-taint`, `computed-member-access-taint`,
`indirect-callee-resolution-taint`, `closure-capture-taint`,
`heap-stored-callee-taint`, `inverted-control-callback-taint`,
`container-iteration-taint`, `deep-access-path-sensitive-taint`,
`element-scoped-field-sensitive-taint`, `deep-interprocedural-relay-taint`,
`recursive-carry-taint`, and `two-level-context-sensitive-taint`.

No challenge case is tagged `intraprocedural`. That is a property of the
templates, not a choice about Semgrep, and it is what puts the whole tier in
Semgrep CE's `unsupported` partition below.

## Adapter coverage of the expanded population

Java is covered by four adapters. Two ran here over the whole 58-assertion
population; two report slices are freeze-bound and their expanded-population
evidence is deferred.

| Adapter | Report | Status for the expanded core |
| --- | --- | --- |
| Bifrost `run-bifrost-java-kernel` | `reports/bifrost-java-kernel.json` | **Ran** — new dedicated slice, first run |
| Joern `run-joern-java-kernel` | `reports/joern-java-kernel.json` | **Ran** — whole-population replacement |
| Semgrep CE `run-semgrep-java-kernel` | `reports/semgrep-java-kernel.json` | **Ran** — whole-population replacement |
| CodeQL `run-codeql-java-kernel` | `reports/codeql-java-kernel.json` | **Deferred** — freeze-bound by `reports/freeze.json` (v0.3.0) |
| Bifrost smoke | `reports/bifrost-smoke.json` | **Frozen and unchanged** — pinned at 118 classic cases by contract |
| OpenTaint `run-opentaint-java-kernel` | `reports/opentaint-java-kernel.json` | **Ran** — new adapter (#17), whole 58-assertion population, post-freeze |
| Infer `run-infer-java-kernel` | `reports/infer-java-kernel.json` | **Ran** — new adapter (#82), whole 58-assertion population, post-freeze |
| FlowDroid `run-flowdroid-java-kernel` | `reports/flowdroid-java-kernel.json` | **Ran** — new adapter (#82), whole 58-assertion population, post-freeze |

### Deferred: CodeQL, and the Bifrost smoke slice

`reports/codeql-java-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0. Re-running the Java CodeQL
kernel over the expanded population would overwrite it, so it was not run in
this change. **Expanded CodeQL evidence for Java is pending the v0.4.0
freeze-prep re-run**, which is the repository's established re-run-at-freeze
pattern; the deferral is a scheduling fact and not an absence of CodeQL
coverage. The committed report remains valid evidence for the 32-assertion
v0.3.0 population it was frozen against.

The Bifrost smoke report is frozen at 118 cases and is *not* a Java kernel
slice that grows. `smoke_population_case` excludes the challenge tier outright,
so the smoke population is unchanged by this expansion. Java's Bifrost
expanded-core evidence lives in the new dedicated
`run-bifrost-java-kernel` slice instead.

## Observed results

Reported per stratum, classic and challenge kept apart. The strata are the
preregistration's: **A** dynamic dispatch and reflection (templates 1–3),
**B** higher-order flow (4–7), **C** containers and deep access paths (8–10),
**D** context and depth stress (11–13).

Read stratum A and template 7 as approximation character, not as a ranking —
the preregistration says so in advance, and nothing observed here changes that.
`inconclusive`, `unsupported`, and `runner-error` are capability or execution
coverage and are never converted into negatives.

### Bifrost v0.10.5 — `reports/bifrost-java-kernel.json`

58 results: 18 `reached`, 19 `not-reached`, 19 `inconclusive`, 2
`runner-error`.

| Stratum | n | Correct | TP | TN | FP | FN | Non-decisive |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | **32/32** | 16 | 16 | 0 | 0 | 0 |
| A — dispatch/reflection | 6 | 0 | 0 | 0 | 0 | 0 | 6 `inconclusive` |
| B — higher-order | 8 | 0 | 0 | 0 | 0 | 0 | 8 `inconclusive` |
| C — containers/paths | 6 | 0 | 0 | 0 | 0 | 0 | 4 `inconclusive`, 2 `runner-error` |
| D — context/depth | 6 | **5/6** | 2 | 3 | 0 | 0 | 1 `inconclusive` |
| Challenge total | 26 | 5 | 2 | 3 | 0 | 0 | 21 |

The classic population reproduces its 32/32 exactly, which is the control this
run needed: the expansion did not disturb the population it was added to.

On the challenge tier the engine produces **no false positives and no false
negatives**. Every cell it does not decide, it declines, and it says why in
retained diagnostics:

- **10 `capability_incomplete`** — "taint semantic binding is unavailable: no
  analysis root contains both a selected source and sink": both cells of
  `reflective-invocation`, `dispatch-table`, `closure-capture`,
  `function-field`, and `callback-registration`. Where the callee is named by a
  run-time string, selected from a map, captured by a lambda, stored in a
  field, or fetched from a list, the engine cannot bind a source and a sink
  into one analysis root at all.
- **9 `partial_discovery`** — "taint discovery is incomplete: procedure
  value-flow snapshot for … `run` is unknown": both cells of
  `computed-property`, `anonymous-implementation`, `map-iteration`, and
  `nested-access-path`, plus `deep-relay-chain-positive`. Three of these
  additionally retain "1 candidate finding(s) retained no source origin
  evidence and could not be projected" — a candidate the engine found but could
  not substantiate, which an incomplete run may not turn into a decision.
- **2 `runner-error`** — `element-object`, both cells: a failed run with
  `internal_invariant`, "taint semantic provider failed: … invalid value-flow
  snapshot: oracle relation does not belong to the required query arena and
  role". The failing document is retained verbatim. This is an engine defect
  surfaced by the fixture, and it is published as one.

`deep-relay-chain-positive` is the only stratum-D cell not decided. The five
decided challenge assertions are all in stratum D and all correct:
`recursive-carry` both cells, `context-pair-depth2` both cells, and
`deep-relay-chain-negative`. Per the preregistration's own reading rule, a
correct stratum-D negative beside an undecided positive is a bound, not
precision.

### Joern 4.0.610 — `reports/joern-java-kernel.json`

58 results: 26 `reached`, 32 `not-reached`. **Every case executed**: zero
`inconclusive`, zero `unsupported`, zero `runner-error`, 58 retained evidence
documents and no error documents. `javasrc2cpg` extracted every challenge
fixture, including the reflective, lambda, anonymous-class, and generic-map
ones, without a frontend complaint.

| Stratum | n | Correct | TP | TN | FP | FN |
| --- | --- | --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | **28/32** | 14 | 14 | 2 | 2 |
| A — dispatch/reflection | 6 | 3/6 | 1 | 2 | 1 | 2 |
| B — higher-order | 8 | 5/8 | 2 | 3 | 1 | 2 |
| C — containers/paths | 6 | **6/6** | 3 | 3 | 0 | 0 |
| D — context/depth | 6 | 5/6 | 2 | 3 | 0 | 1 |
| Challenge total | 26 | 19/26 | 8 | 11 | 2 | 5 |

The classic mismatch set is **identical** to the one the previous Joern Java
report published — `alias-propagation-positive` and `exception-catch-positive`
false negatives, `infeasible-branch-negative` and `loop-carried-negative` false
positives. Nothing about the expansion moved the population it was added to.

Challenge mismatches, verbatim:

- `dfb-taint-java-reflective-invocation-positive`: false negative.
- `dfb-taint-java-dispatch-table-positive`: false negative.
- `dfb-taint-java-computed-property-negative`: false positive.
- `dfb-taint-java-callback-registration-positive`: false negative.
- `dfb-taint-java-function-field-positive`: false negative.
- `dfb-taint-java-anonymous-implementation-negative`: false positive.
- `dfb-taint-java-deep-relay-chain-positive`: false negative.

Read as approximation character, which is what stratum A is for: the engine
does **not** resolve a callee named by a run-time string (`Method.invoke`) or
selected by a map lookup, so both of those positives are missed and both of
their negatives are correct for that same reason — a true negative arrived at
by declining to resolve the call. In the same stratum it *over*-approximates
`java.lang.reflect.Field` access, flagging the negative whose write and read
use two distinct constant keys. Under-approximating dispatch and
over-approximating field identity is a coherent design position, and it is one
engine's position, not a score.

Stratum B splits the same way. Closure capture is decided correctly on both
cells. `anonymous-implementation-negative` is a false positive — the
implementation merge the preregistration says that template exists to make
visible. The `function-field` and `callback-registration` positives are missed:
a callee stored in a field or in a `List` is not carried through to the call
site, and their negatives are again correct without the callee having been
resolved.

Stratum C is the standout: **6/6**, with `entrySet()` iteration, the depth-3
access path, and the combined element-plus-field separation all decided
correctly.

Stratum D is the preregistered prediction, confirmed. `recursive-carry` and
`context-pair-depth2` are correct on both cells; the one mismatch is
`deep-relay-chain-positive`, a false negative on the six-hop chain. The pinned
distribution's `EngineConfig` default `maxCallDepth` is **4**, verified from the
distribution itself before any fixture existed, and the chain is deliberately
six hops. The adapter did not raise that bound — no `maxCallDepth` override was
configured, so the run's identity is the documented default — and the negative
of that pair is correct *because* the engine cannot see that far. Per the
preregistration's reading rule, the pair together describes a bound, not
precision.

### Semgrep CE 1.174.0 — `reports/semgrep-java-kernel.json`

58 results: 9 `reached`, 5 `not-reached`, **44 `unsupported`**, with zero
`inconclusive` and zero `runner-error`. 72 retained documents — 14 finding
documents, 14 resolved rule files, and 44 capability-decision documents — and
no error documents.

| Partition | n | Outcome |
| --- | --- | --- |
| Classic scored (`intraprocedural`) | 14 | 9 `reached`, 5 `not-reached`, **12/14** polarity match |
| Classic unsupported | 18 | capability decision from case metadata |
| Challenge unsupported | 26 | capability decision from case metadata |

The scored subset is unchanged at 14 assertions and unchanged at 12/14, with
the same two false positives every Semgrep kernel shows —
`infeasible-branch-negative` and `loop-carried-negative`, the path sensitivity
the pinned CLI documents as Pro-only. **The expansion did not move Semgrep's
scored population at all**, because the scored partition is the
`intraprocedural` tag and no challenge template carries it.

All 26 challenge assertions are `unsupported` by declared capability, decided
from the case's own `feature_tags` and `expected_analysis_capability.kind`
*before* Semgrep was invoked, so not one of them reached a Semgrep process and
none can be read as a false negative. The retained reasons split as the
partition rule predicts: 4 name the interprocedural boundary
(`interprocedural-deep`, the deep relay and depth-2 context pairs), 4 name the
heap boundary (`heap-access-path`, the nested-path and element-object pairs),
and 18 name the general CE local/intraprocedural profile boundary (the
`reflective-dispatch`, `higher-order`, and `computed-access` cells). This is
the preregistered outcome for a bounded engine and it is correct behavior, not
a gap.

The configuration hash is unchanged
(`865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100`): no rule
file was touched for this expansion, and the Java rule that analyzed the
scored subset is byte-identical to the one the other ten kernels use.

### OpenTaint `analyzer/2026.08.27.17eb0fe` — `reports/opentaint-java-kernel.json`

58 results: 0 `reached`, 58 `not-reached`, with zero `inconclusive`, zero
`unsupported`, and zero `runner-error`; 29/58 match expected polarity. The
whole core is scored — the pinned documentation fences no capability — and
every mismatch is a false negative on a positive, with **zero false
positives**: both `infeasible-branch-negative` and `loop-carried-negative`,
the two negatives Semgrep CE's engine trips on in every language, are clean
here.

The 29 misses are one measurement repeated, not twenty-nine: Java's core
encodes every template's endpoint contract with `int`-typed values, and the
pinned engine drops taint on numeric values — `int` and boxed `Integer`
alike — while carrying it on `String` and `Object`. The retained value-kind
probe (`reports/raw/opentaint-value-kind-probe/`, reproducible via
`scripts/probe-opentaint-value-kind.sh`) isolates that boundary on a fixed
flow shape with all four rules provably loaded, so the Java kernel's zero
positives attribute to the value-kind boundary and say nothing about the
templates' semantic dimensions in Java. The Kotlin kernel, whose core mixes
`String`- and `Int`-encoded templates, is where the engine's propagation
semantics are measurable; see
[the Kotlin kernel contract](kotlin-kernel.md) and
[the OpenTaint adapter notes](../adapters/opentaint/README.md).

### Infer v1.3.0 — `reports/infer-java-kernel.json`

58 results: 21 `reached`, 37 `not-reached`, with zero `inconclusive`, zero
`unsupported`, and zero `runner-error`; **50/58 match expected polarity** —
30/32 classic and 20/26 challenge — with all eight mismatches false negatives
and **zero false positives**. The whole core is scored: the pinned
distribution declares interprocedural analysis and fences no capability, so
as with OpenTaint every incapacity is a measured mismatch. Unlike OpenTaint,
Pulse carries taint on Java's `int`-encoded endpoint contracts, so all 58
assertions are real propagation measurements: the six-hop `deep-relay-chain`
pair discriminates correctly (the depth-6 relay Joern's pinned
`maxCallDepth=4` misses), as do `closure-capture`,
`anonymous-implementation`, `exception-catch`, and both path-sensitivity
negatives. The eight misses are four families: arithmetic-expression drops
(`expression`, `loop-carried` — taint does not survive `(value * 3) + 7`),
recursion (`recursive-carry`), flows through unmodeled collections and
registered callbacks (`dispatch-table` and `map-iteration` through map
entries, `callback-registration` through a `List<IntConsumer>` of registered
lambdas), and reflection (`reflective-invocation`'s string-resolved callee —
the same miss OpenTaint records — and `computed-property`'s
`Field.getDeclaredField` access). See
[the Infer adapter notes](../adapters/infer/README.md).

### FlowDroid 2.15.1 — `reports/flowdroid-java-kernel.json`

58 results: 28 `reached`, 30 `not-reached`, with zero `inconclusive`, zero
`unsupported`, and zero `runner-error`; **49/58 match expected polarity** —
30/32 classic and 19/26 challenge — five false negatives and four false
positives. The whole core is scored: the pinned distribution declares
whole-program context- and flow-sensitive taint analysis and fences no
capability, so every incapacity is a measured mismatch. The pinned CLI
analyzes APKs only, so each case is materialized as a minimal APK from
pinned JVM-only pieces; FlowDroid is the language's first
over-approximating engine on the container templates — the `array-element`
and `element-object` negatives are false positives where Infer's misses in
the same family are false negatives — it follows `recursive-carry` (the
recursion Infer misses) and the six-hop `deep-relay-chain`, and its misses
concentrate in stored-function indirection (`dispatch-table`,
`callback-registration`, `function-field`, `closure-capture`) and
default-off reflection (`reflective-invocation`), with `loop-carried`'s
false positive the one path-sensitivity miss. See
[the FlowDroid adapter notes](../adapters/flowdroid/README.md).

### A note on fixture revisions

`fixture_revision` is a digest over the whole case corpus, so landing 26 Java
cases changed it for every future run. The three reports re-run here carry the
expanded revision `sha256:f476894a41d283e3bcaaf5188ee08abe7886ce8e3919257403b0aa853ef718e2`;
the Joern and Semgrep reports of the other languages still carry
`sha256:aee59a14f96633cf5798df6d211525ea0d10748800ba9c9ac0a3787406bd19ea` and
remain valid evidence for the populations they were run against. They are
re-run together at the v0.4.0 freeze prep, which is when a single revision is
restored across the published set.

## Reproduction

```bash
cargo run -- run-bifrost-java-kernel --bifrost /path/to/bifrost
cargo run -- run-joern-java-kernel   --joern   /path/to/joern-cli/joern
cargo run -- run-semgrep-java-kernel --semgrep /path/to/semgrep
cargo run -- run-opentaint-java-kernel \
  --analyzer-jar /path/to/opentaint-project-analyzer.jar \
  --models-archive /path/to/opentaint-models.tar.gz
cargo run -- run-infer-java-kernel \
  --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
cargo run -- run-flowdroid-java-kernel \
  --flowdroid-jar /path/to/soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform /path/to/android-34/android.jar \
  --d8-jar /path/to/r8-8.5.35.jar
```

Run them sequentially, never concurrently: each runner sweeps the whole report
directory at the end of its run, and two runners rewriting their own
`reports/raw/<slice>/` evidence at once race. `run-codeql-java-kernel` is
deliberately not in this list while its report is freeze-bound.
