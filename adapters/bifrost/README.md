# Bifrost adapter

The smoke adapter invokes Bifrost's policy CLI with `--format json` and retains
the exact report per case. Its policy-local source, sink, and sanitizer
definitions live in `policies/`; canonical cases only reference them.
Raw Bifrost witnesses are retained verbatim. Normalized `witness_checkpoints`
remain empty until the adapter can prove raw witness locations against the
canonical fixture markers; expected checkpoints are never copied into results
as if they were observed evidence.

The core smoke slice applies one balanced direct-flow template to all 13
currently supported language/dialect entries: C, C++, C#, Go, Java,
JavaScript, Kotlin, PHP, Python, Ruby, Rust, Scala, and TypeScript. A Java
propagation kernel adds 16 balanced templates across local, call/return, heap,
and control-flow strata. Java has since been expanded by the same thirteen
challenge templates to a 29-template, 58-assertion core, run by its own
`run-bifrost-java-kernel` command; see the [Java kernel
contract](../../docs/java-kernel.md). The JavaScript parity slice uses the same template IDs
and the language-qualified `core-javascript-kernel.rqlp` policy, with any
language adaptations recorded on the canonical cases. JavaScript has since been
expanded by the thirteen challenge templates to a 29-template, 58-assertion
core, run by its own `run-bifrost-javascript-kernel` command; the smoke slice
keeps only the classic pairs. See the [JavaScript adaptation
matrix](../../docs/javascript-kernel.md) for the syntax mapping, the challenge
realizations, and the explicit exceptional-flow limitation. The Python parity slice uses
`core-python-kernel.rqlp`, and the Kotlin parity slice uses
`core-kotlin-kernel.rqlp`; see the [Kotlin kernel
contract](../../docs/kotlin-kernel.md) for its two `var`-based adaptations and
for why the Kotlin kernel run pins its policy for the whole population rather
than reading it from each case. The TypeScript parity slice repeats those 16
templates against `.ts` fixtures through `core-typescript-kernel.rqlp`, and its
thirteen challenge templates have now rolled out too, taking its core
population to 29 templates and 58 assertions; see the [TypeScript adaptation
matrix](../../docs/typescript-kernel.md). The retained TypeScript report is the
classic 32 — it is freeze-bound by v0.3.0, so its expanded run is deferred to
the v0.4.0 freeze-prep re-run rather than written here. TypeScript is a
separate population from JavaScript and the two are never mixed. The C# parity
slice uses `core-csharp-kernel.rqlp`; its direct-propagation pair is frozen in
the v0.2.0 evidence with the breadth `core-direct.rqlp` policy, so the C#
selector accepts that policy too and evaluates each case through the policy it
declares; see [the C# kernel contract](../../docs/csharp-kernel.md). The Go
parity slice uses `core-go-kernel.rqlp` under the same frozen-direct-pair
arrangement, and its thirteen challenge templates have now rolled out too,
taking its core population to 29 templates and 58 assertions; see [the Go kernel
contract](../../docs/go-kernel.md) for its struct, pointer-alias, array, and
`panic`/`recover` adaptations, and for the three `reflect`-based challenge
adaptations. The retained Go report is the classic 32 — it is freeze-bound by
v0.3.0, so its expanded run is deferred to the v0.4.0 freeze-prep re-run rather
than written here. The C and C++
parity slices use `core-c-kernel.rqlp` and `core-cpp-kernel.rqlp` and are two
separate populations with two different denominators: C++ covers all 16 classic
templates (32 core assertions), while C's classic core is 15 (30 core
assertions) because `dfb-template-exception-catch` is inapplicable to C, and its
two `language-extension` cases run in the same slice on their own scorecard.
C's challenge row has since rolled out — nine of the thirteen preregistered
challenge templates are applicable to C — taking its core population to **24
templates and 48 assertions**, and C++'s row has rolled out likewise, to **28 templates and 56 assertions**. The
retained C report is the classic 30: it is freeze-bound by v0.3.0, so **the
expanded Bifrost C evidence is deferred to the v0.4.0 freeze-prep re-run**
rather than written here. See [the C kernel
contract](../../docs/c-kernel.md) and [the C++ kernel
contract](../../docs/cpp-kernel.md). The Rust parity slice uses
`core-rust-kernel.rqlp` under the same frozen-direct-pair arrangement as C# and
Go, and carries the same reduced denominator as C for a different reason:
`docs/applicability-matrix.md` classifies `exception-catch` as inapplicable to
Rust. Rust's challenge-tier row has now rolled out too, so its core population
is **27 templates and 54 assertions** — the 15 classic templates plus the 12
challenge templates `docs/challenge-tier.md` classifies as applicable, the
reflective-invocation cell being inapplicable to a language with no run-time
reflection. The `Result`/`?` construct Rust uses instead of exception catch is
carried by a `language-extension` pair that the run also evaluates but never
counts in the core denominator; see
[the Rust kernel contract](../../docs/rust-kernel.md). The retained Rust report
is the classic 30 — it is freeze-bound by v0.3.0, so its expanded run is
deferred to the v0.4.0 freeze-prep re-run rather than written here. The PHP parity slice uses
`core-php-kernel.rqlp` under the same frozen-direct-pair arrangement as C#, Go,
and Rust, and covers all 16 templates (32 core assertions); see [the PHP kernel
contract](../../docs/php-kernel.md) for its ordered-map array adaptation and for
why the pinned CodeQL CLI contributes no PHP results at all. The Ruby parity
slice uses `core-ruby-kernel.rqlp` under that same arrangement and also covers
all 16 templates (32 core assertions); it is the one analyzer-coverage-gated
slice, run and retained as capability evidence while the Ruby denominator is
decided CodeQL-first, as [the Ruby kernel
contract](../../docs/ruby-kernel.md) records. The Scala parity
slice uses `core-scala-kernel.rqlp` and pins that policy for its whole
population the way the Kotlin slice does, because its direct-propagation pair
is frozen naming the breadth policy; Scala is the only kernel with
**single-analyzer coverage** — CodeQL 2.26.3 has no Scala extractor and the
pinned Joern has no Scala source frontend, so Bifrost is the only tool that
produces Scala results at all. See
[the Scala kernel contract](../../docs/scala-kernel.md). Every kernel command
selects only its own language's core assertions — 32 for the 16-template
kernels, 48 for the expanded 24-template C kernel, 54 for the expanded
27-template Rust kernel, 56 for the expanded 28-template C++ kernel, and 58
for the expanded 29-template kernels — and writes a dedicated report. The Java
calibration slice also
covers one-hop helper flow. Generated workspaces live outside the repository so
repository ignore rules cannot hide fixtures from Bifrost's indexer. Sanitizer
lowering is a future Bifrost CLI capability.
External semantic-model activation requires an embedding
with an explicit catalog, so the modeled-external case is reported as
`unsupported` by this CLI adapter with an explicit retained reason. It is not a
negative result.

Run from the repository root:

```bash
cargo run -- run-bifrost-smoke --bifrost /path/to/bifrost
cargo run -- run-bifrost-java-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-javascript-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-python-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-kotlin-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-scala-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-typescript-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-csharp-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-go-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-c-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-cpp-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-rust-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-ruby-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-php-kernel --bifrost /path/to/bifrost
```

`run-bifrost-java-kernel` and `run-bifrost-javascript-kernel` have both now been
run, each over its language's expanded 58-assertion core; their evidence is
described below. Each
selects its language's whole core population and pins the language-qualified
policy for the run, accepting the frozen direct-propagation pair's historical
policy references (`direct-positive.rqlp` and `explicit-negative.rqlp` for
Java, the cross-language breadth policy for JavaScript) rather than rewriting
evidence a freeze manifest binds. Their populations follow the challenge
rollout table described in [the adapter contract](../../docs/adapters.md): 32
assertions before a language's row is flipped, the expanded denominator after.

The smoke command selects only cases with an explicit Bifrost policy or
unsupported declaration, and never a challenge-tier case: any `template_id`
beginning `dfb-template-chal-` is refused so the frozen 118-case population
cannot change meaning when challenge fixtures land under the same policies. Cases for other adapters are not emitted into the
Bifrost report. Each selected case is materialized into an isolated workspace
and evaluated through Bifrost's path-based policy CLI (`--root` plus
`--policy-file`). A report with incomplete runs is normalized as `inconclusive`
even when it contains no findings; it is never interpreted as a negative.

## Retained v0.10.5 snapshot

The checked-in `reports/bifrost-smoke.json` was produced with Bifrost v0.10.5,
build identity `728ac69ab93224151c6c951b23d2f5bc681d8558`, and is frozen in
the published v0.3.0 manifest.
The smoke report contains 118 normalized results: 58 `reached`, 57
`not-reached`, 2 `inconclusive`, and 1 `unsupported`. Every result's
`raw_output` points to its retained per-case Bifrost JSON under
`reports/raw/bifrost/`; the normalized report and raw reports are separate
evidence layers. Raw completion and diagnostic fields are never replaced with
a synthetic `not-reached` outcome, and normalized witness checkpoints remain
empty until the adapter can prove their locations.

The 32-case Java kernel *within the frozen smoke population* has 16 `reached`
and 16 `not-reached` outcomes, with 32/32 assertions matching expected polarity
and no incomplete outcomes (under v0.10.2 it was 17/32). That population is
frozen and does not grow; Java's expanded core is a separate slice, described
under [the Java kernel](#java-kernel-expanded-core) below. The 32-case Python kernel likewise has 16 `reached`,
16 `not-reached`, and 32/32 matching (v0.10.2: 16/32); its dedicated report is
`reports/bifrost-python-kernel.json` and raw evidence is under
`reports/raw/bifrost-python-kernel/`.

**Deferred: the expanded Python population.** Python's challenge-tier row is
rolled out and its core denominator is now 29 templates / 58 assertions, but
`reports/bifrost-python-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0, so the Python challenge wave did
not re-run it. Those 32 results are the frozen 16-template v0.3.0 evidence and
say nothing either way about the thirteen challenge templates; Bifrost's
evidence for the expanded Python core arrives with the v0.4.0 freeze-prep
re-run. Deferral is not absence of coverage, and the v0.3.0 and v0.4.0
populations are never compared number-to-number. The Python challenge cases are
also excluded from the smoke selection, which stays pinned at its frozen 118
cases.

The 32-case
JavaScript kernel has 16 `reached`, 16 `not-reached`, and 32/32 matching
(v0.10.2: 19/32). Unlike the v0.10.2 snapshot, this v0.10.5 evidence decides
all three of these kernels completely.

### JavaScript expanded core — the dedicated kernel run

JavaScript's thirteen preregistered challenge templates
(`docs/challenge-tier.md`) have rolled out, so its core denominator is 29
templates / **58 assertions**. Those assertions are carried by a new dedicated
report, `reports/bifrost-javascript-kernel.json`, written by
`run-bifrost-javascript-kernel` and evidenced under
`reports/raw/bifrost-javascript-kernel/`. **The frozen smoke report is
untouched**: its JavaScript slice stays the classic 32 assertions and the smoke
population stays pinned at 118 cases, because the smoke selector excludes
challenge templates outright.

| Stratum | Assertions | Polarity match | Outcomes |
| --- | --- | --- | --- |
| Classic (16 templates) | 32 | 32/32 | 16 `reached`, 16 `not-reached` |
| Challenge (13 templates) | 26 | 3/26 | 1 `reached`, 2 `not-reached`, 21 `inconclusive`, 2 `runner-error` |

The classic half reproduces the frozen smoke evidence case for case. On the
challenge half the engine decided only two of the thirteen pairs — the
two-level context pair, both ways, and the depth-6 relay negative — and **every
decision it made was correct**: the stratum contains no false positive and no
false negative. Twenty-one assertions are `inconclusive`, each retaining
`partial_discovery` evidence of the form "taint discovery is incomplete:
procedure value-flow snapshot for … is unknown", across the reflective,
computed-property, dispatch-table, closure, function-field, callback,
anonymous-implementation, map-iteration, nested-path and recursive pairs plus
the depth-6 relay positive. The `element-object` pair is `runner-error`: on an
array of object literals the engine reports `internal_invariant` with "invalid
value-flow snapshot: oracle relation does not belong to the required query
arena and role". That is retained exactly as observed — an engine defect worth
reporting upstream, and never a negative result.

This run is at fixture revision
`sha256:64ef139f452fd296bb26463bc552e5e5998ca4bb4584d45565d858424814bde9`,
which no earlier Bifrost report carries; the two are not pooled, and a
32-assertion score is never compared with a 58-assertion one.

Every Bifrost slice in the v0.3.0 freeze — the smoke population and the
Kotlin, TypeScript, C#, Go, C, C++, Python, and Rust kernels — was run on this
one build.

The Kotlin kernel snapshot covers the **classic 32-case population**: 12
`reached`, 10 `not-reached`, and 10 `inconclusive`, with 19/32 assertions
matching expected polarity (19 of 22 decisive outcomes; under v0.10.2 it was
17/32). Its dedicated report is `reports/bifrost-kotlin-kernel.json` and raw
evidence is under `reports/raw/bifrost-kotlin-kernel/`. The ten `inconclusive`
results are the complete heap/separation stratum and the exception-catch pair,
both polarities, each retaining `partial_discovery` evidence; they mirror the
Java kernel profile and are never counted as negatives.

Kotlin's core population is now **58 assertions**, its challenge-tier row
having been rolled out, but `reports/bifrost-kotlin-kernel.json` is one of the
nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so
`run-bifrost-kotlin-kernel` was **not** re-run for that expansion: **expanded
Bifrost evidence for Kotlin is pending the v0.4.0 freeze-prep re-run**, and the
snapshot above remains a valid classic-population result that says nothing
about the 26 challenge assertions. Deferral is not absence of coverage; see the
[Kotlin kernel contract](../../docs/kotlin-kernel.md).

The 32-case TypeScript kernel, in its own report
`reports/bifrost-typescript-kernel.json` with raw evidence under
`reports/raw/bifrost-typescript-kernel/`, has 15 `reached`, 15 `not-reached`,
and 2 `inconclusive`, with 30/32 assertions matching expected polarity — all
30 decisive outcomes are correct. The two `inconclusive` results are the
exception-catch pair, retaining `capability_incomplete` evidence. Under
v0.10.2 this kernel matched 19/32; the alias-propagation and array-element
pairs are now decisive and correct. That report is the classic 32-assertion
population only: TypeScript's core is now 58 assertions, but the report is
freeze-bound by v0.3.0, so **the expanded Bifrost TypeScript evidence is
pending the v0.4.0 freeze-prep re-run** and this snapshot is not an
expanded-core number.

The C# kernel's frozen 32-case run, in its own report
`reports/bifrost-csharp-kernel.json`
with raw evidence under `reports/raw/bifrost-csharp-kernel/`, contains 1
`reached`, 1
`not-reached`, and 30 `inconclusive` results: only the direct-propagation pair
is decisive, and both of its outcomes match the expected polarity. The 30
inconclusive results retain `partial_discovery` (20) or `capability_incomplete`
(10) evidence with per-case diagnostics showing that Bifrost's procedure
value-flow snapshot for the C# fixture procedure is unknown or unsupported.
This is capability coverage, never a negative result. The same incompleteness
reproduces under the language-agnostic `core-direct.rqlp` policy, so it is not
an artifact of the language-qualified policy.

**Deferred: the expanded C# population.** C#'s challenge-tier row is now
rolled out and its core denominator is 29 templates / 58 assertions, but
`reports/bifrost-csharp-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0, so the C# challenge wave did not
re-run it — the same treatment the Python wave gave its freeze-bound report.
Those 32 results are the frozen 16-template v0.3.0 evidence and say nothing
either way about the thirteen challenge templates; Bifrost's evidence for the
expanded C# core arrives with the v0.4.0 freeze-prep re-run. Deferral is not
absence of coverage, and the v0.3.0 and v0.4.0 populations are never compared
number-to-number. The C# challenge cases are also excluded from the smoke
selection, which stays pinned at its frozen 118 cases.

The 32-case Go kernel, in its own report `reports/bifrost-go-kernel.json` with
raw evidence under `reports/raw/bifrost-go-kernel/`, contains 5 `reached`, 5
`not-reached`, and 22 `inconclusive` results. Five template pairs are decisive —
direct propagation, the local multi-step chain, call-context separation, and the
one-hop and two-hop return relays — and all ten of those outcomes match the
expected polarity. The 22 inconclusive results retain `partial_discovery` (12)
or `capability_incomplete` (10) evidence; the ten are the four heap pairs
("procedure value-flow snapshot ... is unsupported (assignments)") and the
`panic`/`recover` exception pair, where Bifrost cannot bind the sink operand
supplied by `recover()`. All of this is capability coverage, never a negative
result; see [the Go kernel contract](../../docs/go-kernel.md). That report is
the classic 32-assertion population only: Go's core is now 58 assertions, but
the report is freeze-bound by v0.3.0, so **the expanded Bifrost Go evidence is
pending the v0.4.0 freeze-prep re-run** and this snapshot is not an
expanded-core number.

**Deferred: the expanded C population.** C's challenge-tier row is now rolled
out and its core denominator is 24 templates / 48 assertions — nine of the
thirteen preregistered challenge templates are applicable to C — but
`reports/bifrost-c-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0, so the C challenge wave did not
re-run it, exactly as the C# and TypeScript waves treated their freeze-bound
reports. The retained C snapshot (32 results: 1 `reached`, 1 `not-reached`, 28
`inconclusive` core outcomes plus 2 `inconclusive` `language-extension` cases,
detailed in [the C kernel contract](../../docs/c-kernel.md)) is the classic
30-assertion population and is not an expanded-core number. **Expanded Bifrost
C evidence is pending the v0.4.0 freeze-prep re-run.**

The 30-assertion Rust kernel, in its own report
`reports/bifrost-rust-kernel.json` with raw evidence under
`reports/raw/bifrost-rust-kernel/`, produces 1 `reached`, 1 `not-reached`, and
20 `inconclusive` and 8 `runner-error` core results: only the
direct-propagation pair is decisive, and both of its outcomes match the
expected polarity (2 of 2 decisive outcomes, 2 of 30 assertions). The two
`language-extension` assertions are both `inconclusive` and are reported
separately, never in the core denominator. The inconclusive core results
retain `partial_discovery` evidence. The eight `runner-error` results — the
complete heap/separation stratum, both polarities of object separation,
same-object field separation, alias propagation, and array element — retain
raw runs that complete as `failed` with `internal_invariant` ("semantic IR
gap_contract error in procedure 2: gap 8 duplicates the same scoped fact"): a
failed evaluation is an execution error, normalized as `runner-error`, and is
never counted as a negative. That report is the classic 30-assertion population
only: Rust's core is now 54 assertions, but the report is freeze-bound by
v0.3.0, so **the expanded Bifrost Rust evidence is pending the v0.4.0
freeze-prep re-run** and this snapshot is not an expanded-core number.

The 32-case Ruby kernel, in its own report `reports/bifrost-ruby-kernel.json`
with raw evidence under `reports/raw/bifrost-ruby-kernel/`, contains **32
`inconclusive` results and nothing else**: no assertion is decisive, so the
polarity match is 0 of 0 decisive outcomes. This is not a regression and not a
negative result — it is the analyzer-coverage gate
`docs/applicability-matrix.md` records for Ruby, now measured over the whole
16-template population instead of only the two breadth assertions. Twenty
results retain `partial_discovery` evidence ("procedure value-flow snapshot for
`<fixture>.run` is unknown") and twelve retain `capability_incomplete` evidence
— the four heap/separation pairs and the exception-catch pair ("unsupported
(assignments)") plus the loop-carried pair ("unsupported (local_flow)").
Bifrost's Ruby indexing was not modified by that tranche; the Ruby denominator
is decided CodeQL-first instead, and none of these 32 outcomes is ever counted
as `not-reached`. See [the Ruby kernel contract](../../docs/ruby-kernel.md).

The 32-assertion PHP kernel, in its own report
`reports/bifrost-php-kernel.json` with raw evidence under
`reports/raw/bifrost-php-kernel/`, contains 10 `reached`, 8 `not-reached`, and
14 `inconclusive` results, with 17 of the 18 decisive outcomes matching the
expected polarity (17 of 32 assertions). Eight template pairs are decisive and
correct on both halves; the one decisive mismatch is
`dfb-taint-php-infeasible-branch-negative`, where Bifrost reports a flow through
an `if (false)` body, the same over-approximation the Go kernel shows. The 14
inconclusive results retain `capability_incomplete` (10 — the whole
heap/separation stratum and the exception-catch pair) or `partial_discovery`
(4 — the arithmetic-expression and loop-carried pairs) evidence and are never
counted as negatives. This report was produced after the v0.3.0 freeze and is
not bound by it; see [the PHP kernel contract](../../docs/php-kernel.md).

The 32-case Scala kernel, in its own report `reports/bifrost-scala-kernel.json`
with raw evidence under `reports/raw/bifrost-scala-kernel/`, was run on the
same v0.10.5 build after the v0.3.0 freeze and is therefore not part of it. It
produces 5 `reached`, 5 `not-reached`, and 22 `inconclusive` results: five
template pairs are decisive — direct propagation, the local multi-step chain,
call-context separation, argument-position separation, and the one-hop return
relay — and all ten of those outcomes match the expected polarity, with no
decisive mismatch. The 22 inconclusive results retain `partial_discovery` (18)
or `capability_incomplete` (4) evidence; six of them additionally carry the
policy's finding message, which an incomplete run cannot make decisive. This is
capability coverage, never a negative result; see [the Scala kernel
contract](../../docs/scala-kernel.md).

## Java kernel (expanded core)

Java now has a dedicated slice of its own, `run-bifrost-java-kernel`, writing
`reports/bifrost-java-kernel.json` with raw evidence under
`reports/raw/bifrost-java-kernel/`. It exists because Java's core grew: the
[challenge-tier preregistration](../../docs/challenge-tier.md) adds thirteen
templates to it, so its denominator is **29 templates and 58 assertions**, while
the smoke population that also covers Java is frozen at 118 cases and must not
grow. The challenge tier is excluded from the smoke selection outright for that
reason.

The first run of this slice, on the same v0.10.5 build, produces 18 `reached`,
19 `not-reached`, 19 `inconclusive`, and 2 `runner-error` results. Its classic
32 assertions reproduce the frozen smoke slice's Java outcomes case for case —
16 `reached`, 16 `not-reached`, 32/32 matching — which is the control that says
the expansion did not disturb the population it was added to.

Of the 26 challenge assertions, five are decisive and all five are correct
(both `recursive-carry` cells, both `context-pair-depth2` cells, and
`deep-relay-chain-negative`); there is no false positive and no false negative
anywhere in the tier. The other 21 are capability or execution coverage: 19
`inconclusive` — 10 retaining `capability_incomplete` "no analysis root
contains both a selected source and sink" (the reflective-invocation,
dispatch-table, closure-capture, function-field, and callback-registration
pairs) and 9 retaining `partial_discovery` "procedure value-flow snapshot ...
is unknown" (the computed-property, anonymous-implementation, map-iteration,
and nested-access-path pairs, plus the six-hop relay positive) — and 2
`runner-error` on the `element-object` pair, where the run fails with
`internal_invariant` and "invalid value-flow snapshot: oracle relation does not
belong to the required query arena and role". That failure is retained
verbatim and published as an engine defect; it is not a negative result. Per
the preregistration's own reading rule, correct stratum-D negatives beside an
undecided six-hop positive describe a bound, not precision. See [the Java
kernel contract](../../docs/java-kernel.md).

The JavaScript alias-propagation and array-element pairs retain
`partial_discovery` evidence, while the exception-catch pair retains
`capability_incomplete` evidence; all six remain `inconclusive`. The Java
heap/separation and exception pairs and the Python heap/control-flow pairs
likewise remain `inconclusive`, never negative results. The Ruby direct-flow
pair retains `partial_discovery` evidence, and the modeled-external Java
calibration case is the single explicit `unsupported` result. [Bifrost #1951](https://github.com/BrokkAi/bifrost/issues/1951)
tracks the final cross-language production-taint acceptance work.
