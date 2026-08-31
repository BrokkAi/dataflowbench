# Scala propagation kernel

Issue #41 ports the sixteen scored Java propagation templates to Scala, as
classified in the [applicability matrix](applicability-matrix.md). The Scala
cases keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct is adapted to Scala syntax.
Every scored Scala template has exactly one `positive` and one `negative` `core`
case: 16 templates, 32 core assertions.

That classic core is now joined by the thirteen preregistered challenge
templates, which fold into the same `core` tier and take the Scala denominator
to **29 templates / 58 core assertions**. See [challenge-tier
expansion](#challenge-tier-expansion) below; the table immediately following
describes the classic sixteen only.

Scala has **single-analyzer coverage**. Bifrost is the only tool in this
benchmark that can extract it; the reasons are recorded under [analyzer
coverage](#analyzer-coverage) below, and they are coverage facts, never
negative results.

| Stratum | Template ID | Scala adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct method call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | **Language-adapted.** A `var` local carries the value; Scala is immutable-first and defaults to `val`, and an immutable local cannot express the kill. |
| Local | `dfb-template-local-multi-step-chain` | `val` locals carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | Scala `Int` arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One relay method is called with a tainted and a clean value; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | A helper returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop helper return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two Scala helper returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Two instances of a `class Holder` with a `var` field stand in for distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One `Holder` carries separate `tainted` and `clean` fields. |
| Heap/separation | `dfb-template-alias-propagation-separation` | Assignment of an object reference creates the alias; a second `new Holder()` remains distinct. |
| Heap/separation | `dfb-template-array-element-separation` | `new Array[Int](2)` with distinct constant indices stands in for the Java `int[]`; Scala spells element access `values(0)` rather than `values[0]`, which is surface syntax, not an adaptation. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the tainted path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | **Language-adapted.** A statement-form `if`/`else` assigns to a `var`, rather than Scala's idiomatic expression-valued `if`; the negative overwrites on both branches, the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | **Language-adapted.** A `var` carried across a `while` loop is either overwritten or computed from. Scala has no C-style `for`, and a `for` comprehension over a range does not express a mutable carried value; a `while` loop over a `var` preserves the kill/compute distinction. |
| Control transfer | `dfb-template-exception-catch` | Directly applicable: `class FlowException extends RuntimeException` carries an `Int` field across `throw` and a `catch { case caught: FlowException => ... }` handler. |

Exactly the three cells the matrix marks adapted deviate from the Java
construct: `dfb-template-local-overwrite-kill` and
`dfb-template-loop-carried-kill` require `var` where Java uses a plain mutable
local (and the loop is a `while` rather than a `for`), and
`dfb-template-branch-join` requires the statement form of `if`/`else` rather
than Scala's expression-valued `if`. Every other cell is directly applicable,
matching the matrix exactly.

All Scala fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
method names inside a `package dataflowbench` object, mirroring the Scala
direct-flow fixture already in the breadth slice. Bifrost lowers those
endpoints through its Scala kernel policy; fixture metadata remains
analyzer-neutral and reports retain only observed evidence.

Every fixture was compiled in isolation — one file, one fresh output directory,
no shared classpath — with **Scala 3.8.4** (`scalac -version`: "Scala compiler
version 3.8.4"), installed with `brew install scala`. All 32 compiled with zero
errors and zero warnings. The two frozen direct-propagation fixtures collide
only when compiled *together*, because both declare
`dataflowbench.DirectFlow`; each is a separate single-file case and is never
compiled with its sibling.

## Challenge-tier expansion

[The challenge tier](challenge-tier.md) preregistered thirteen further
propagation templates before any fixture existed. Its applicability matrix
classifies **all thirteen as applicable to Scala**, two of them
`language-adapted`, so the Scala core denominator grows from 16 templates / 32
assertions to **29 templates / 58 assertions**. The challenge cases carry
`score_tier: "core"` — there is no separate tier — and their fixture provenance
revision is `m3-challenge-scala`.

The v0.3.0 sixteen-template core and this expanded core are different
populations and are never compared number to number.

### Adaptation notes

Two cells are `language-adapted`, exactly as the preregistration's Scala row
states, and both for the same reason it gives: **Scala's own reflection API
lives in `scala-reflect`, a separate artifact**, which the tier's stdlib-only
fairness constraint excludes — the identical situation the Kotlin row records
for `kotlin-reflect`. The fixtures therefore reach for the JVM's
`java.lang.reflect`, which every Scala compilation already has on its
classpath. Nothing else deviates.

The challenge fixtures carry `String` values where the classic Scala kernel
carries `Int`. That is surface typing, not an adaptation: the kernel policy
selects `dfb_source`/`dfb_sink` by call name and is type-agnostic, and the
reflective and dispatch-table cells need a reference type to name a member
signature at run time. Kotlin's wave made the same choice for the same reason.

| Stratum | Template ID | Scala realization |
| --- | --- | --- |
| A | `dfb-template-chal-reflective-invocation` | **Language-adapted.** `classOf[Target].getMethod(name, classOf[String])` with `name` a local string constant, then `method.invoke(target, dfb_source())`. The negative points `name` at the sibling `drop` method, which discards its argument and sinks a clean constant. `scala.reflect` is not used and not on the classpath. |
| A | `dfb-template-chal-computed-property` | **Language-adapted.** Scala has no computed member syntax, so the shape goes through `java.lang.reflect.Field`: `classOf[Holder].getDeclaredField(key)`, `field.set(holder, dfb_source())`, and a matching `field.get(holder)`. This is the same adaptation the preregistration fixes for Java and Kotlin. Unlike Kotlin, Scala has no `@JvmField`: a `var` on a class always compiles to a private backing field behind accessors, so the fixture calls `setAccessible(true)` before the reflective read and write. That call is `java.lang.reflect` too, so the stdlib-only constraint holds; the deviation from Kotlin's fixture is recorded here rather than left implicit. The negative writes under `"alpha"` and reads a provably distinct `"beta"`. |
| A | `dfb-template-chal-dispatch-table` | Direct. `Map[String, String => Unit]("leak" -> leak, "drop" -> drop)` — Scala function values are first-class, and Scala 3 eta-expands the method references against the expected function type — selected with `table(key)` and then invoked. |
| B | `dfb-template-chal-closure-capture` | Direct. `makeReporter()` binds the tainted local and returns `() => dfb_sink(captured)`; the caller invokes it after the local has left scope. The negative captures a clean local while the source call stays live. |
| B | `dfb-template-chal-function-field` | Direct. A `class Holder` with a `var fn: String => Unit`; two instances, one holding `leak` and one `drop`, and a separate `dispatch(holder, value)` that reads the field and calls it. The negative hands `dispatch` the second holder. |
| B | `dfb-template-chal-callback-registration` | Direct. A `Registry` with a `var hooks: List[String => Unit]`, a `register` method that appends, and a `fire` driver that iterates and invokes. Immutable `List` rather than a mutable buffer keeps the registration a plain reassignment, which is idiomatic Scala; no framework, no annotation, twenty lines of language. |
| B | `dfb-template-chal-anonymous-implementation` | Direct. `new Handler { def handle(value: String): Unit = { dfb_sink(value) } }` is a genuine anonymous class implementing a one-method `trait`, assigned to a `Handler`-typed local and invoked through it. Both anonymous implementations capture nothing, which is what keeps this distinct from `closure-capture`. |
| C | `dfb-template-chal-map-iteration` | Direct. `for ((key, value) <- records)` over a `scala.collection.mutable.Map`, which iterates entries and never performs a keyed `get`. The negative iterates a second, disjoint map. |
| C | `dfb-template-chal-nested-access-path` | Direct. `outer.middle.inner.value` written and read at depth 3; the negative reads the sibling `outer.middle.inner.other`. |
| C | `dfb-template-chal-element-object` | Direct. `Array(new Item(), new Item())` with distinct constant indices, mirroring the classic `dfb-template-array-element-separation` cell's `new Array[Int](2)`. `negative_mechanism` stays `field-separation`, the corpus-wide precedent for constant-index separation. |
| D | `dfb-template-chal-deep-relay-chain` | Direct. `relay1` … `relay6` as six same-file object members, no branching and no state. The negative feeds the identical chain a clean constant while the source call stays live. |
| D | `dfb-template-chal-recursive-carry` | Direct. `carry(value, depth)` recursing from 5 to the `depth == 0` base case; the negative's base case returns `"clean"` instead of the carried value. Scala's expression-valued `if` is used here — the classic kernel's statement-form `if` adaptation belongs to `dfb-template-branch-join`, whose intent depends on assignment on both arms, and does not apply to this template. |
| D | `dfb-template-chal-context-pair-depth2` | Direct, following [Amendment A1](challenge-tier.md#amendments): `helper` returns its argument, `wrapper` calls `helper`, and `outerTainted`/`outerClean` are the two two-deep contexts. Both are live in both fixtures; only which returned value reaches `dfb_sink` differs. |

All twenty-six fixtures are standard-library-only — no dependency, no framework,
no build tooling, and no `scala-reflect` — and every one of them compiles clean
under the host toolchain this kernel already records, **Scala 3.8.4**, compiled
one file at a time into a fresh output directory with
`scalac -d <out> <Fixture>.scala`, with zero errors and zero warnings.

### Adapter coverage of the expanded population

Scala has single-analyzer coverage, so the expanded population has exactly one
runnable adapter — and it is not freeze-bound, which makes Scala one of the few
waves whose whole expanded core carries fresh evidence from its only engine.

| Adapter | Expanded run | Report | Why |
| --- | --- | --- | --- |
| Bifrost v0.10.5 | Yes | `reports/bifrost-scala-kernel.json` | Post-freeze report; no freeze binds it |
| CodeQL 2.26.4 | **Not covered** | — | No Scala extractor and no Scala library pack exists |
| Joern 4.0.614 | **Not covered** | — | No Scala *source* frontend exists in the pinned distribution |
| Semgrep CE 1.175.0 | **Not commissioned** | — | Maintainer decision, not a tool limitation |

`reports/bifrost-scala-kernel.json` is **not** among the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0 — the freeze binds the Bifrost
smoke report, eight other Bifrost kernel reports, and all ten CodeQL kernel
reports — so it was re-run whole over the expanded 58 and replaced. No
freeze-bound file was touched, and no Bifrost evidence for Scala is deferred to
the v0.4.0 re-run.

The two analyzer absences below are restated for the expanded population.
Neither changes: they are properties of the pinned tools, they were verified
against them, and they produce no results at all — in particular no negative
results — for any of the 58 assertions.

- **CodeQL has no Scala support.** CodeQL CLI 2.26.4 ships no Scala extractor
  and no Scala library pack in any build mode, so there is no
  `adapters/codeql/scala/` pack and no `run-codeql-scala-kernel` command. The
  26 challenge assertions are covered by that absence exactly as the 32 classic
  ones are. This is coverage, not deferral: there is nothing to re-run at
  v0.4.0.
- **Joern has no Scala source frontend.** The pinned Joern 4.0.614 installs no
  Scala source frontend; `jimple2cpg` consumes JVM bytecode, a different
  extraction contract from the single-source-file, no-build fixtures this
  benchmark ships. The challenge fixtures are single-file `scalac`-clean
  sources on exactly the same terms, so the absence extends to them unchanged.
- **Semgrep CE is a maintainer decision.** The pinned distribution records
  `scala` at GA maturity, so no Semgrep Scala slice exists here by decision
  rather than by tool limitation, and none was built for this expansion. The
  preregistered `CHALLENGE_SEMGREP_PARTITION` consequently never sees a Scala
  case. `adapters/semgrep/README.md` records the decision; nothing about it is
  evidence that Semgrep CE cannot analyze Scala.

## The frozen direct-propagation pair

`cases/taint/scala/direct-positive/` and `cases/taint/scala/direct-negative/`
predate this kernel: they are the Scala members of the cross-language
direct-flow breadth slice and were frozen byte-for-byte in the v0.2.0 manifest
and again in v0.3.0 (`reports/freeze.json`). Their `tool_model_references`
therefore still name the language-neutral `core-direct.rqlp` policy, and
editing them would invalidate the published freeze.

The Scala kernel runner consequently selects the Scala core population by
`language`/`track`/`score_tier` and pins the language-qualified policy for the
whole population, exactly as the Kotlin kernel does, so all 58 assertions share
one configuration:

- Bifrost evaluates `adapters/bifrost/policies/core-scala-kernel.rqlp` for
  every selected case.

The Scala kernel results are a separate population from the Scala direct-flow
breadth results, from the Java and Kotlin kernels, and from every other
language.

## Bifrost selection and reproduction

```bash
cargo run -- run-bifrost-scala-kernel --bifrost /path/to/bifrost
```

The command selects exactly the 58 Scala `taint`/`core` assertions, writes the
normalized report to `reports/bifrost-scala-kernel.json`, and retains the raw
per-case Bifrost JSON under `reports/raw/bifrost-scala-kernel/`. A report with
incomplete runs normalizes as `inconclusive` even when it contains no findings;
it is never interpreted as a negative.

## Analyzer coverage

Scala runs on one analyzer. Both absences below are properties of the pinned
tools, verified against them, and are recorded as coverage — they produce no
results at all, and in particular no negative results. Both hold unchanged over
the expanded 58-assertion core; [the expanded population's adapter
coverage](#adapter-coverage-of-the-expanded-population) restates them
template-by-template.

### CodeQL has no Scala support

CodeQL CLI 2.26.4 — the version pinned by every other kernel in this benchmark
— ships **no Scala extractor and no Scala library pack**, in any build mode.
Scala is not a CodeQL language; there is nothing to pin, no pack to install,
and no query to write. `docs/applicability-matrix.md` records the same fact
under analyzer coverage ("PHP and Scala have no CodeQL support at all"). There
is therefore no `adapters/codeql/scala/` pack and no
`run-codeql-scala-kernel` command, and their absence is deliberate rather than
unfinished work.

### Joern has no Scala source frontend

The pinned Joern 4.0.614 distribution installs no Scala *source* frontend. Its
`jimple2cpg` frontend consumes JVM **bytecode**, which is a different
extraction contract from the single-source-file, no-build fixtures this
benchmark ships: it would require a compilation pipeline that no other case
population uses, and the artifact it analyzed would be `scalac` output rather
than the checked-in fixture. That verification is recorded in
[`adapters/joern/README.md`](../adapters/joern/README.md), where Scala is
listed as **explicitly unsupported**. It is now the only such language: Rust was
explicitly unsupported under the previous `4.0.432` pin and is executed under
`4.0.610`, which ships `rust2cpg`; no comparable Scala source frontend appeared.
Introducing a bytecode
pipeline for Scala is out of scope for this kernel.

Issue #14 remains the second-analyzer tracking path. Neither absence blocked
fixture authoring, and neither is allowed to appear as an outcome: a case an
analyzer cannot run is simply absent from that analyzer's population.

## Anchor evidence and result semantics

Bifrost findings are evidence, not ground truth by themselves. The runner
retains each case's raw Bifrost JSON report verbatim and normalizes only what
that report establishes:

- A completed run with at least one finding is `reached`; a completed run with
  no finding is `not-reached`.
- A run Bifrost reports as incomplete — any `completion.type` other than
  `complete`, or the inconclusive exit status 2 — is `inconclusive`, with the
  analyzer's own incompleteness reasons retained verbatim in `diagnostics`.
- A run Bifrost reports as failed, an unparseable report, an absent report, or
  a process that could not be spawned is `runner-error`.
- An explicitly declared adapter incapability is `unsupported`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 29 balanced assertion pairs —
which matters more for Scala than for most kernels, because five sixths of this
population is currently incomplete analysis.

Normalized `witness_checkpoints` are empty for every case: the adapter does not
yet prove raw witness locations against the canonical `DFB-SOURCE:`,
`DFB-WITNESS:`, and `DFB-SINK:` markers, so expected checkpoints are never
copied into results as though they had been observed.

## Observed results

### Bifrost v0.10.5

`reports/bifrost-scala-kernel.json` is a whole-population report over the
expanded core: **58 results — 5 `reached`, 5 `not-reached`, and 48
`inconclusive`**, with zero `unsupported` and zero `runner-error`. **10 of 58**
assertions match the expected polarity — all ten decisive outcomes are correct,
and there are **no** decisive mismatches anywhere in the population. Build
identity `728ac69ab93224151c6c951b23d2f5bc681d8558`; configuration hash
`50e658fa533bbd0d2d8c3d712ba4885bf1fb80269be92ae58a2d39b96007018b`, unchanged
from the classic run because the policy did not change.

| Stratum | Assertions | `reached` | `not-reached` | `inconclusive` | Polarity match | Decisive mismatches |
| --- | --- | --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 5 | 5 | 22 | 10/32 | none |
| Challenge (13 templates) | 26 | 0 | 0 | 26 | 0/26 | none |

**The classic thirty-two are identical case-for-case to the pre-expansion
report** — same outcome on every one of the 32, same five decisive pairs. The
expansion moved nothing in the classic stratum, which is what the whole-report
replacement had to demonstrate before its challenge half could be read at all.

**Every one of the twenty-six challenge assertions is `inconclusive`.** Bifrost
v0.10.5 decides none of the challenge tier for Scala in either direction, so
the challenge stratum contributes **no** matches and **no** mismatches — it is
26 assertions of capability coverage, and it must not be read as 26 misses. The
per-template mismatch list for the challenge tier is therefore empty, for the
uninformative reason that the list of decisive challenge outcomes is empty too.
Each retains its own reason verbatim:

- **12 `capability_incomplete`**, "taint semantic binding is unavailable: no
  analysis root contains both a selected source and sink" — the
  `reflective-invocation`, `dispatch-table`, `closure-capture`,
  `function-field`, `callback-registration`, and `anonymous-implementation`
  pairs. Both strata-A/B reflection and higher-order shapes land here: the
  source and the sink end up in procedures the run does not join under one
  analysis root.
- **2 `capability_incomplete`**, `run` reported "unsupported (assignments)" —
  the `map-iteration` pair, the same incompleteness the classic
  `array-element` pair reports.
- **12 `partial_discovery`**, an `unknown` procedure value-flow snapshot — the
  `computed-property`, `nested-access-path`, and `element-object` pairs (the
  `Holder`, `Inner`, and `Item` constructors), and the `context-pair-depth2`,
  `deep-relay-chain`, and `recursive-carry` pairs (`outerClean`, `relay1`, and
  `carry` respectively).

No challenge case carries a finding message, so none of them is a
findings-bearing incomplete run of the kind six classic cases show.

Read against the preregistration's framing: stratum A measures approximation
character rather than skill, and stratum D's depth-6 relay is calibrated past
known engine defaults. Neither framing is exercised here, because Bifrost's
Scala frontend does not get far enough to take a position on any of it. That is
the honest description of this snapshot.

The 22 classic `inconclusive` results are eleven complete pairs, both polarities each:
the whole heap/separation stratum (`object-separation`,
`same-object-field`, `alias-propagation`, `array-element`), the whole
control-transfer stratum (`infeasible-branch`, `branch-join`,
`loop-carried-kill`, `exception-catch`), plus `local-overwrite-kill`,
`arithmetic-expression-propagation`, and the two-hop return relay. Each retains
an explicit incompleteness reason:

- **18 `partial_discovery`** — the procedure's value-flow snapshot is
  `unknown`, either for the fixture's `run` procedure or for the `Holder`
  constructor in the heap cases.
- **4 `capability_incomplete`** — the `array-element` pair reports `run` as
  "unsupported (assignments)", and the `exception-catch` pair reports the
  `FlowException` constructor as "unsupported (calls)".

Across the whole 58, that is **30 `partial_discovery`** and **18
`capability_incomplete`**.

Six of the classic inconclusive cases (`branch-join`, `local-overwrite`, and
`loop-carried`, both polarities) additionally carry the policy's own finding
message. That is not a decisive outcome: the run that produced it is
incomplete, so the case stays `inconclusive` and is counted as capability
coverage, exactly as the C#, Go, and Kotlin kernels handle the same situation.

This profile is close to the C# and Go v0.10.5 snapshots — a decisive local and
call/return core with an incomplete heap and control-transfer stratum — rather
than to the fully decisive Java, JavaScript, and Python kernels.

No fixture was adjusted to make the analyzer decide a case. The incompleteness
is a published result.

## Re-freeze obligation

Adding the Scala kernel — and now its challenge-tier expansion — grows the
benchmark case population, so every checked-in normalized report that was not
re-run against the grown corpus predates the current fixture set.
`reports/bifrost-scala-kernel.json` was re-run whole for this expansion and
carries the current fixture revision; no Scala adapter evidence is deferred,
because Bifrost is the only adapter that covers Scala at all. The frozen
v0.3.0 evidence is untouched and still validates, but a future release freeze
must re-run **every** adapter over the grown population before `create-freeze`
will accept it; `create_freeze` refuses reports whose declared fixture revision
does not match the selected case population.
