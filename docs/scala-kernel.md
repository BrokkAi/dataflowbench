# Scala propagation kernel

Issue #41 ports the sixteen scored Java propagation templates to Scala, as
classified in the [applicability matrix](applicability-matrix.md). The Scala
cases keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct is adapted to Scala syntax.
Every scored Scala template has exactly one `positive` and one `negative` `core`
case: 16 templates, 32 core assertions.

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

## The frozen direct-propagation pair

`cases/taint/scala/direct-positive/` and `cases/taint/scala/direct-negative/`
predate this kernel: they are the Scala members of the cross-language
direct-flow breadth slice and were frozen byte-for-byte in the v0.2.0 manifest
and again in v0.3.0 (`reports/freeze.json`). Their `tool_model_references`
therefore still name the language-neutral `core-direct.rqlp` policy, and
editing them would invalidate the published freeze.

The Scala kernel runner consequently selects the Scala core population by
`language`/`track`/`score_tier` and pins the language-qualified policy for the
whole population, exactly as the Kotlin kernel does, so all 32 assertions share
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

The command selects exactly the 32 Scala `taint`/`core` assertions, writes the
normalized report to `reports/bifrost-scala-kernel.json`, and retains the raw
per-case Bifrost JSON under `reports/raw/bifrost-scala-kernel/`. A report with
incomplete runs normalizes as `inconclusive` even when it contains no findings;
it is never interpreted as a negative.

## Analyzer coverage

Scala runs on one analyzer. Both absences below are properties of the pinned
tools, verified against them, and are recorded as coverage — they produce no
results at all, and in particular no negative results.

### CodeQL has no Scala support

CodeQL CLI 2.26.3 — the version pinned by every other kernel in this benchmark
— ships **no Scala extractor and no Scala library pack**, in any build mode.
Scala is not a CodeQL language; there is nothing to pin, no pack to install,
and no query to write. `docs/applicability-matrix.md` records the same fact
under analyzer coverage ("PHP and Scala have no CodeQL support at all"). There
is therefore no `adapters/codeql/scala/` pack and no
`run-codeql-scala-kernel` command, and their absence is deliberate rather than
unfinished work.

### Joern has no Scala source frontend

The pinned Joern 4.0.610 distribution installs no Scala *source* frontend. Its
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
execution health separate from the polarity of the 16 balanced assertions —
which matters more for Scala than for most kernels, because two thirds of this
population is currently incomplete analysis.

Normalized `witness_checkpoints` are empty for every case: the adapter does not
yet prove raw witness locations against the canonical `DFB-SOURCE:`,
`DFB-WITNESS:`, and `DFB-SINK:` markers, so expected checkpoints are never
copied into results as though they had been observed.

## Observed results

### Bifrost v0.10.5

`reports/bifrost-scala-kernel.json` has 32 results: **5 `reached`, 5
`not-reached`, and 22 `inconclusive`**, with zero `unsupported` and zero
`runner-error`. **10 of 32** assertions match the expected polarity — all ten
decisive outcomes are correct, and there are **no** decisive mismatches. Build
identity `728ac69ab93224151c6c951b23d2f5bc681d8558`; configuration hash
`50e658fa533bbd0d2d8c3d712ba4885bf1fb80269be92ae58a2d39b96007018b`.

The five decisive template pairs are direct propagation, the local multi-step
chain, call-context separation, argument-position separation, and the one-hop
return relay.

The 22 `inconclusive` results are eleven complete pairs, both polarities each:
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

Six of the inconclusive cases (`branch-join`, `local-overwrite`, and
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

Adding the Scala kernel grows the benchmark case population, so every
checked-in normalized report now predates the current fixture set. The frozen
v0.3.0 evidence is untouched and still validates, but a future release freeze
must re-run **every** adapter over the grown population before `create-freeze`
will accept it; `create_freeze` refuses reports whose declared fixture revision
does not match the selected case population.
