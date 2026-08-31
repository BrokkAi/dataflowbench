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
matrix](../../docs/typescript-kernel.md). The retained TypeScript report is now
that expanded 58 — `run-bifrost-typescript-kernel` was re-run whole for the
v0.4.0 freeze. TypeScript is a
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
adaptations. The retained Go report is now that expanded 58 —
`run-bifrost-go-kernel` was re-run whole for the v0.4.0 freeze. The C and C++
parity slices use `core-c-kernel.rqlp` and `core-cpp-kernel.rqlp` and are two
separate populations with two different denominators: C++ covers all 16 classic
templates (32 core assertions), while C's classic core is 15 (30 core
assertions) because `dfb-template-exception-catch` is inapplicable to C, and its
two `language-extension` cases run in the same slice on their own scorecard.
C's challenge row has since rolled out — nine of the thirteen preregistered
challenge templates are applicable to C — taking its core population to **24
templates and 48 assertions**, and C++'s row has rolled out likewise, to **28 templates and 56 assertions**. The
retained C and C++ reports are those expanded populations: both kernels were
re-run whole for the v0.4.0 freeze. See [the C kernel
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
is now that expanded 54 — `run-bifrost-rust-kernel` was re-run whole for the
v0.4.0 freeze. The PHP parity slice uses
`core-php-kernel.rqlp` under the same frozen-direct-pair arrangement as C#, Go,
and Rust, and covers PHP's **expanded 29 templates (58 core assertions)** now
that its challenge-tier row is rolled out; see [the PHP kernel
contract](../../docs/php-kernel.md) for its ordered-map array adaptation, its
thirteen directly-applicable challenge cells, and for why the pinned CodeQL CLI
contributes no PHP results at all. The Ruby parity
slice uses `core-ruby-kernel.rqlp` under that same arrangement and likewise
covers the **expanded 29 templates (58 core assertions)**, all thirteen
challenge cells being directly applicable to Ruby. It is the one
analyzer-coverage-gated slice, run and retained as capability evidence while the
Ruby denominator is decided CodeQL-first; all 58 assertions come back
`inconclusive`, 14 of them under a new *taint semantic binding is unavailable*
diagnostic class — no analysis root contains both a selected source and sink —
and the rest under incomplete-discovery diagnostics. Either way it is a recorded
absence of capability rather than 58 negatives, as
[the Ruby kernel contract](../../docs/ruby-kernel.md) records. The Scala parity
slice uses `core-scala-kernel.rqlp` and pins that policy for its whole
population the way the Kotlin slice does, because its direct-propagation pair
is frozen naming the breadth policy; its core is now the **expanded 29
templates (58 core assertions)**, and Scala is the only kernel with
**single-analyzer coverage** — CodeQL 2.26.4 has no Scala extractor and the
pinned Joern has no Scala source frontend, so Bifrost is the only tool that
produces Scala results at all. See
[the Scala kernel contract](../../docs/scala-kernel.md). Every kernel command
selects only its own language's core assertions — every row is now expanded:
48 for the 24-template C kernel, 54 for the expanded
27-template Rust kernel, 56 for the expanded 28-template C++ kernel, and 58
for the expanded 29-template kernels — and writes a dedicated report. The Java
calibration slice also
covers one-hop helper flow. Generated workspaces live outside the repository so
repository ignore rules cannot hide fixtures from Bifrost's indexer.

**Sanitizer lowering is not a future capability; this README used to say it
was.** The sentence *"Sanitizer lowering is a future Bifrost CLI capability"*
stood here until it was measured and found false: the RQLP `analysis` grammar
accepts a `(sanitizer …)` stanza, the declaration suppresses a flow on a
completing run, deleting it restores that flow with a full witness, and an
undeclared sanitizer-shaped sibling is not suppressed. That measurement is
[Amendment A9](../../docs/modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false),
which promotes category Z of the modeling matrix for this adapter. The retired
sentence was also quoted by the tool-native profile's own category-Z rationale;
that cell turns on the absent shipped endpoint catalog rather than on lowering,
and
[Amendment A10](../../docs/native-profile.md#a10--2026-08-28-bifrosts-native-category-z-cell-is-restated-on-the-absent-endpoint-catalog)
has since restated it on those grounds without moving the decision.

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

All fourteen commands above have now been run for the v0.4.0 freeze, each over
its language's whole current core — 58 assertions for the ten 29-template
kernels, 56 for C++, 54 for Rust, 48 for C, and the pinned 118 cases for the
smoke slice; their evidence is described below. Each
selects its language's whole core population and pins the language-qualified
policy for the run, accepting the frozen direct-propagation pair's historical
policy references (`direct-positive.rqlp` and `explicit-negative.rqlp` for
Java, the cross-language breadth policy for JavaScript) rather than rewriting
evidence a freeze manifest binds. Their populations follow the challenge
rollout table described in [the adapter contract](../../docs/adapters.md): 32
assertions before a language's row is flipped, the expanded denominator after,
and every row is flipped in this freeze.

The smoke command selects only cases with an explicit Bifrost policy or
unsupported declaration, and never a challenge-tier case: any `template_id`
beginning `dfb-template-chal-` is refused so the frozen 118-case population
cannot change meaning when challenge fixtures land under the same policies. Cases for other adapters are not emitted into the
Bifrost report. Each selected case is materialized into an isolated workspace
and evaluated through Bifrost's path-based policy CLI (`--root` plus
`--policy-file`). A report with incomplete runs is normalized as `inconclusive`
even when it contains no findings; it is never interpreted as a negative.

## Retained v0.10.6 snapshot

The checked-in `reports/bifrost-smoke.json` was produced with Bifrost v0.10.6,
build identity `18d09c57d1e5044dec49acac7635d3255ea8e89c`, and is frozen in
the published v0.4.0 manifest. Every Bifrost report on this tree — the smoke
population and all thirteen kernels — was produced by that one build at the one
fixture revision
`sha256:13a11ff48f26dba889f76aeb9ef60213a129abe5ebcfcb966da3a2418c12807e`.
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
under [the Java kernel](#java-kernel-expanded-core) below.

**An observed instability, published as observed.**
`dfb-taint-java-direct-positive` is `reached` here and `not-reached` in
`reports/bifrost-java-kernel.json`, at the same build and the same fixture
revision. The two are separate populations with separate scorecards, both raw
artifacts are retained and digest-bound, and neither run was repeated to force
agreement: the freeze publishes what the runs produced. The 32/32 above is the
smoke population's own result and the Java kernel's 31/32 is its own; neither
supersedes the other.

The classic 32 Python assertions likewise have 16 `reached`, 16 `not-reached`,
and 32/32 matching (v0.10.2: 16/32), both inside the smoke population and
inside the dedicated 58-assertion report
`reports/bifrost-python-kernel.json`, whose raw evidence is under
`reports/raw/bifrost-python-kernel/`.

**The expanded Python population.** Python's challenge-tier row is rolled out
and its core denominator is 29 templates / 58 assertions;
`reports/bifrost-python-kernel.json` was re-run whole for the v0.4.0 freeze and
now carries all 58. It scores **36/58**: the classic 32 reproduce the smoke
evidence case for case at 32/32, and on the challenge 26 the engine decides
only the depth-6 relay pair and the two-level context pair, both ways, and
**all four decisions are correct** — no false positive and no false negative in
the tier. Twenty are `inconclusive` (12 `capability_incomplete` "no analysis
root contains both a selected source and sink" across the reflective,
dispatch-table, closure, function-field, callback and anonymous-implementation
pairs; 8 `partial_discovery` across the computed-property, map-iteration,
nested-access-path and recursive-carry pairs) and 2 are `runner-error` on the
`element-object` pair, the shared `internal_invariant` "oracle relation" defect
tracked upstream as bifrost-dev #2639. The Python challenge cases stay excluded
from the smoke selection, which remains pinned at its frozen 118 cases, and a
32-assertion score is never compared with a 58-assertion one.

The 32 classic
JavaScript assertions have 16 `reached`, 16 `not-reached`, and 32/32 matching
(v0.10.2: 19/32). Unlike the v0.10.2 snapshot, this v0.10.6 evidence decides
all three of these classic slices completely.

### JavaScript expanded core — the dedicated kernel run

JavaScript's thirteen preregistered challenge templates
(`docs/challenge-tier.md`) have rolled out, so its core denominator is 29
templates / **58 assertions**. Those assertions are carried by a new dedicated
report, `reports/bifrost-javascript-kernel.json`, written by
`run-bifrost-javascript-kernel` and evidenced under
`reports/raw/bifrost-javascript-kernel/`. **The smoke population is
unchanged**: its JavaScript slice stays the classic 32 assertions and the smoke
selection stays pinned at 118 cases, because the smoke selector excludes
challenge templates outright.

| Stratum | Assertions | Polarity match | Outcomes |
| --- | --- | --- | --- |
| Classic (16 templates) | 32 | 32/32 | 16 `reached`, 16 `not-reached` |
| Challenge (13 templates) | 26 | 4/26 | 2 `reached`, 2 `not-reached`, 20 `inconclusive`, 2 `runner-error` |

The classic half reproduces the frozen smoke evidence case for case. On the
challenge half the engine decided only two of the thirteen pairs — the
two-level context pair and the depth-6 relay, both ways each — and **every
decision it made was correct**: the stratum contains no false positive and no
false negative. Twenty assertions are `inconclusive`: twelve retain
`capability_incomplete` "taint semantic binding is unavailable: no analysis
root contains both a selected source and sink" (the reflective, dispatch-table,
closure, function-field, callback and anonymous-implementation pairs), two
retain `capability_incomplete` "unsupported (normal_control_flow)" (the
map-iteration pair), and six retain `partial_discovery` (the computed-property,
recursive-carry and nested-access-path pairs). The `element-object` pair is
`runner-error`: on an array of object literals the engine reports
`internal_invariant` with "invalid value-flow snapshot: oracle relation does
not belong to the required query arena and role". That is retained exactly as
observed — an engine defect, tracked upstream as bifrost-dev #2639, and never a
negative result.

This run is at fixture revision
`sha256:13a11ff48f26dba889f76aeb9ef60213a129abe5ebcfcb966da3a2418c12807e`, the
single revision the v0.4.0 freeze binds; a 32-assertion score is never compared
with a 58-assertion one.

Every Bifrost slice in the v0.4.0 freeze — the smoke population and the Java,
JavaScript, Kotlin, TypeScript, C#, Go, C, C++, Python, Rust, Ruby, PHP, and
Scala kernels — was run on this one build.

The Kotlin kernel's **classic 32 assertions** are 12 `reached`, 10
`not-reached`, and 10 `inconclusive`, with 19/32 matching expected polarity (19
of 22 decisive outcomes; under v0.10.2 it was 17/32). Its dedicated report is
`reports/bifrost-kotlin-kernel.json` and raw evidence is under
`reports/raw/bifrost-kotlin-kernel/`. The ten `inconclusive`
results are the complete heap/separation stratum and the exception-catch pair,
both polarities, each retaining `partial_discovery` evidence; they mirror the
Java kernel profile and are never counted as negatives. The three decisive
mismatches are the `expression` positive (a false negative) and the
`infeasible-branch` and `loop-carried` negatives (false positives).

Kotlin's core population is now **58 assertions**, its challenge-tier row
having been rolled out, and `run-bifrost-kotlin-kernel` was re-run whole for
the v0.4.0 freeze, so the report carries all 58 and scores **25/58**. The
classic 32 above reproduce the pre-expansion snapshot case for case. On the
challenge 26 the engine decides three pairs — recursive carry, the two-level
context pair, and the depth-6 relay — **all six decisions correct**, with no
false positive and no false negative in the tier; 18 are `inconclusive` (12
`capability_incomplete` "no analysis root contains both a selected source and
sink" across the reflective, dispatch-table, closure, function-field, callback
and anonymous-implementation pairs, 6 `partial_discovery` across the
computed-property, map-iteration and nested-access-path pairs) and 2 are
`runner-error` on the `element-object` pair, the `internal_invariant` "oracle
relation" defect tracked upstream as bifrost-dev #2639. Twenty undecided
challenge assertions are not twenty misses; see the
[Kotlin kernel contract](../../docs/kotlin-kernel.md).

The TypeScript kernel's classic 32 assertions, in its own report
`reports/bifrost-typescript-kernel.json` with raw evidence under
`reports/raw/bifrost-typescript-kernel/`, are 15 `reached`, 15 `not-reached`,
and 2 `inconclusive`, with 30/32 matching expected polarity — all
30 decisive outcomes are correct. The two `inconclusive` results are the
exception-catch pair, retaining `capability_incomplete` "unsupported
(exceptional_control_flow)" evidence. Under
v0.10.2 this kernel matched 19/32; the alias-propagation and array-element
pairs are now decisive and correct. TypeScript's core is now 58 assertions and
`run-bifrost-typescript-kernel` was re-run whole for the v0.4.0 freeze, so the
report carries all 58 and scores **34/58**. On the challenge 26 it decides the
depth-6 relay pair and the two-level context pair, both ways, and **all four
decisions are correct**; 20 are `inconclusive` (12 `capability_incomplete` "no
analysis root contains both a selected source and sink", 2
`capability_incomplete` "unsupported (normal_control_flow)" on the
map-iteration pair, 6 `partial_discovery` on the computed-property,
recursive-carry and nested-access-path pairs) and 2 are `runner-error` on the
`element-object` pair — the `internal_invariant` "oracle relation" defect
tracked upstream as bifrost-dev #2639. That is the same challenge profile
JavaScript shows, on a population that is nonetheless never pooled with it.

The C# kernel's classic 32 assertions, in its own report
`reports/bifrost-csharp-kernel.json`
with raw evidence under `reports/raw/bifrost-csharp-kernel/`, are 1
`reached`, 1
`not-reached`, and 30 `inconclusive`: only the direct-propagation pair
is decisive, and both of its outcomes match the expected polarity. The 30
inconclusive results retain `partial_discovery` (20) or `capability_incomplete`
(10) evidence with per-case diagnostics showing that Bifrost's procedure
value-flow snapshot for the C# fixture procedure is unknown or unsupported.
This is capability coverage, never a negative result. The same incompleteness
reproduces under the language-agnostic `core-direct.rqlp` policy, so it is not
an artifact of the language-qualified policy.

**The expanded C# population.** C#'s challenge-tier row is rolled out and its
core denominator is 29 templates / 58 assertions;
`reports/bifrost-csharp-kernel.json` was re-run whole for the v0.4.0 freeze and
carries all 58, scoring **3/58**. The classic 32 above reproduce the
pre-expansion snapshot case for case. On the challenge 26 exactly one assertion
is decisive — the depth-6 relay positive, `reached` and correct — and the other
25 are `inconclusive`: 12 retain `capability_incomplete` "no analysis root
contains both a selected source and sink" (the reflective, dispatch-table,
closure, function-field, callback and anonymous-implementation pairs), 6 retain
`capability_incomplete` "unsupported (assignments)" (the element-object,
map-iteration and nested-access-path pairs), and 7 retain `partial_discovery`
(the computed-property and recursive-carry pairs, the two-level context pair,
and the depth-6 relay negative). One decisive cell beside 25 declines is
capability coverage, never 25 negatives. The C# challenge cases are also
excluded from the smoke selection, which stays pinned at its frozen 118 cases.

The Go kernel's classic 32 assertions, in its own report
`reports/bifrost-go-kernel.json` with
raw evidence under `reports/raw/bifrost-go-kernel/`, are 5 `reached`, 5
`not-reached`, and 22 `inconclusive`. Five template pairs are decisive —
direct propagation, the local multi-step chain, call-context separation, and the
one-hop and two-hop return relays — and all ten of those outcomes match the
expected polarity. The 22 inconclusive results retain `partial_discovery` (12)
or `capability_incomplete` (10) evidence; the ten are the four heap pairs
("procedure value-flow snapshot ... is unsupported (assignments)") and the
`panic`/`recover` exception pair, where Bifrost cannot bind the sink operand
supplied by `recover()`. All of this is capability coverage, never a negative
result; see [the Go kernel contract](../../docs/go-kernel.md). Go's core is now
58 assertions and `run-bifrost-go-kernel` was re-run whole for the v0.4.0
freeze, so the report carries all 58 and scores **14/58**. The classic 32
reproduce the pre-expansion snapshot case for case, and on the challenge 26 the
engine decides the depth-6 relay pair and the two-level context pair, both
ways, **all four correctly**. The remaining 22 are `inconclusive`: 12
`capability_incomplete` "no analysis root contains both a selected source and
sink", 6 `capability_incomplete` "unsupported (assignments)" on the
element-object, map-iteration and nested-access-path pairs, and 4
`partial_discovery` on the computed-property and recursive-carry pairs. Go
produces no `runner-error` anywhere in its population.

**The expanded C population.** C's challenge-tier row is rolled out and its
core denominator is 24 templates / 48 assertions — nine of the thirteen
preregistered challenge templates are applicable to C — and
`reports/bifrost-c-kernel.json` was re-run whole for the v0.4.0 freeze. It
contains 50 results and scores **2/48**: 1 `reached` and 1 `not-reached` on the
direct-propagation pair, 46 `inconclusive` core outcomes (28 classic and 18
challenge), plus 2 `inconclusive` `language-extension` cases reported on their
own scorecard, detailed in [the C kernel contract](../../docs/c-kernel.md). No
challenge assertion is decisive: 6 retain `capability_incomplete` "no analysis
root contains both a selected source and sink" (the dispatch-table,
function-field and callback-registration pairs) and 12 retain
`partial_discovery` "procedure value-flow snapshot … is unknown". Eighteen
undecided challenge assertions are capability coverage, never eighteen
negatives.

**The expanded C++ population.** C++'s core denominator is 28 templates / 56
assertions — twelve of the thirteen challenge templates apply, the
reflective-invocation cell being inapplicable — and
`reports/bifrost-cpp-kernel.json`, with raw evidence under
`reports/raw/bifrost-cpp-kernel/`, was re-run whole for the v0.4.0 freeze. It
scores **2/56**: the direct-propagation pair is the only decisive one, both
ways correct, and the other 54 assertions are `inconclusive` — 10 retaining
`capability_incomplete` "no analysis root contains both a selected source and
sink" (the dispatch-table, closure, function-field, callback and
anonymous-implementation pairs) and 44 retaining `partial_discovery`. C++
produces no `runner-error` anywhere in its population; see [the C++ kernel
contract](../../docs/cpp-kernel.md).

The **54-assertion** Rust kernel, in its own report
`reports/bifrost-rust-kernel.json` with raw evidence under
`reports/raw/bifrost-rust-kernel/`, was re-run whole for the v0.4.0 freeze and
scores **2/54**. On its classic 30 it produces 1 `reached`, 1 `not-reached`,
20 `inconclusive` and 8 `runner-error` results: only the
direct-propagation pair is decisive, and both of its outcomes match the
expected polarity (2 of 2 decisive outcomes, 2 of 30 classic assertions). The two
`language-extension` assertions are both `inconclusive` and are reported
separately, never in the core denominator. The inconclusive core results
retain `partial_discovery` evidence. The eight `runner-error` results — the
complete heap/separation stratum, both polarities of object separation,
same-object field separation, alias propagation, and array element — retain
raw runs that complete as `failed` with `internal_invariant` ("semantic IR
gap_contract error in procedure 2: gap 8 duplicates the same scoped fact"): a
failed evaluation is an execution error, normalized as `runner-error`, and is
never counted as a negative. That signature is tracked upstream as bifrost-dev
#2638.

On Rust's twelve applicable challenge templates — 24 assertions, the
reflective-invocation cell being inapplicable to a language with no run-time
reflection — **no assertion is decisive**: 20 are `inconclusive` (10 retaining
`capability_incomplete` "no analysis root contains both a selected source and
sink" across the dispatch-table, closure, function-field, callback and
anonymous-implementation pairs, and 10 retaining `partial_discovery` across the
computed-property, map-iteration, recursive-carry, depth-6 relay and two-level
context pairs) and 4 are `runner-error` on the `element-object` and
`nested-access-path` pairs, failing with the same `gap_contract` signature as
the classic heap stratum — bifrost-dev #2638, not the separate "oracle
relation" defect the other frontends hit. Twenty-four undecided challenge
assertions are execution and capability coverage, never twenty-four negatives.

The 58-case Ruby kernel, in its own report `reports/bifrost-ruby-kernel.json`
with raw evidence under `reports/raw/bifrost-ruby-kernel/`, contains **58
`inconclusive` results and nothing else**: no assertion is decisive, so the
polarity match is 0 of 0 decisive outcomes. This is not a regression and not a
negative result — it is the analyzer-coverage gate
`docs/applicability-matrix.md` records for Ruby, now measured over the whole
expanded 29-template population instead of the 16-template core or the two
breadth assertions, and it is tracked upstream as bifrost-dev #2637.
`reports/bifrost-ruby-kernel.json` was not bound by the v0.3.0 freeze — the
Ruby kernel landed after it — and is one of the 42 reports
`reports/freeze.json` digest-binds for v0.4.0. Twenty-eight results retain `partial_discovery` evidence ("procedure
value-flow snapshot for `<procedure>` is unknown"); fourteen retain
`capability_incomplete` "unsupported (assignments)" (the four classic
heap/separation pairs, the exception-catch pair, and the challenge
`nested-access-path` and `element-object` pairs); fourteen retain
`capability_incomplete` "taint semantic binding is unavailable: no analysis root
contains both a selected source and sink" (the seven challenge pairs whose sink
call sits inside a lambda, a block, a `Method` object, or an anonymous class
body); and two retain "unsupported (local_flow)" (the loop-carried pair).
Bifrost's Ruby indexing was not modified by this wave any more than by the
original tranche; the Ruby denominator is decided CodeQL-first instead, and none
of these 58 outcomes is ever counted as `not-reached`. See [the Ruby kernel
contract](../../docs/ruby-kernel.md).

The **58-assertion** PHP kernel, in its own report
`reports/bifrost-php-kernel.json` with raw evidence under
`reports/raw/bifrost-php-kernel/`, contains 12 `reached`, 10 `not-reached`, and
36 `inconclusive` results, with 21 of the 22 decisive outcomes matching the
expected polarity (21 of 58 assertions). PHP's challenge-tier row is rolled
out, so its core is the expanded 29 templates — the sixteen v0.3.0 templates
plus all thirteen preregistered challenge templates ([the challenge
tier](../../docs/challenge-tier.md)) — and the report is a whole-population
replacement, not an append. The classic 32 reproduce the previous PHP snapshot
exactly (10 `reached`, 8 `not-reached`, 14 `inconclusive`, 17/32), with the one
decisive mismatch still `dfb-taint-php-infeasible-branch-negative`, where
Bifrost reports a flow through an `if (false)` body — the same
over-approximation the Go kernel shows. On the challenge 26 the engine produces
**no false positive and no false negative**: 22 are `inconclusive` (12
`capability_incomplete` "no analysis root contains both a selected source and
sink" across the reflective, dispatch-table, closure, function-field, callback,
and anonymous-implementation pairs; 8 `capability_incomplete` "unsupported
(assignments)" across the computed-property, map-iteration, element-object, and
nested-path pairs; 2 `partial_discovery` on the recursive-carry pair) and the 4
it decides — the deep-relay and depth-2 context pairs — are all correct. No
inconclusive result is ever counted as a negative. This report was produced
after the v0.3.0 freeze and is bound by the v0.4.0 one; see [the PHP kernel
contract](../../docs/php-kernel.md).

The Scala kernel, in its own report `reports/bifrost-scala-kernel.json` with raw
evidence under `reports/raw/bifrost-scala-kernel/`, was re-run whole on the same
v0.10.6 build over its **expanded 58-assertion core** — 32 classic plus the 26
challenge assertions the [challenge-tier
preregistration](../../docs/challenge-tier.md) adds. The report post-dates the
v0.3.0 freeze and is bound by the v0.4.0 one. It produces 5
`reached`, 5 `not-reached`, and 48 `inconclusive` results, **10 of 58** matching
the expected polarity with **no decisive mismatch anywhere**. The classic
thirty-two are identical case-for-case to the pre-expansion report — the same
five decisive pairs (direct propagation, the local multi-step chain,
call-context separation, argument-position separation, and the one-hop return
relay) at 10/32 — and **all twenty-six challenge assertions are
`inconclusive`**, contributing neither a match nor a mismatch. The 48
inconclusive results retain `partial_discovery` (30) or `capability_incomplete`
(18) evidence; six classic ones additionally carry the policy's finding message,
which an incomplete run cannot make decisive. This is capability coverage, never
a negative result, and twenty-six undecided challenge assertions are not
twenty-six misses; see [the Scala kernel
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

The v0.4.0 run of this slice, on the v0.10.6 build, produces 18 `reached`,
20 `not-reached`, 18 `inconclusive`, and 2 `runner-error` results, scoring
**37/58**. Its classic 32 assertions match **31/32**: they reproduce the
smoke slice's Java outcomes case for case except for
`dfb-taint-java-direct-positive`, which is `not-reached` here — a false
negative — and `reached` in `reports/bifrost-smoke.json` at the same build and
the same fixture revision. That disagreement is published as observed rather
than re-run to agreement; the two populations keep separate scorecards and both
raw artifacts are retained and digest-bound.

Of the 26 challenge assertions, six are decisive and all six are correct (both
`recursive-carry` cells, both `context-pair-depth2` cells, and both
`deep-relay-chain` cells — Java and Kotlin are the only Bifrost kernels that
decide all three stratum-D pairs); there is no false positive and no false negative
anywhere in the tier. The other 20 are capability or execution coverage: 18
`inconclusive` — 10 retaining `capability_incomplete` "no analysis root
contains both a selected source and sink" (the reflective-invocation,
dispatch-table, closure-capture, function-field, and callback-registration
pairs) and 8 retaining `partial_discovery` "procedure value-flow snapshot ...
is unknown" (the computed-property, anonymous-implementation, map-iteration,
and nested-access-path pairs) — and 2
`runner-error` on the `element-object` pair, where the run fails with
`internal_invariant` and "invalid value-flow snapshot: oracle relation does not
belong to the required query arena and role". That failure is retained
verbatim and published as an engine defect, tracked upstream as bifrost-dev
#2639; it is not a negative result. The undecided stratum-A and stratum-B
pairs are the nested-callable-root gap tracked as bifrost-dev #2640: the sink
call sits inside a lambda, an anonymous class body, or a registered callback,
and no analysis root contains both endpoints. See [the Java
kernel contract](../../docs/java-kernel.md).

Within the pinned smoke population the Java, JavaScript, and Python slices are
now decided completely: the only incomplete outcomes left are the Ruby
direct-flow pair, which retains `partial_discovery` evidence, and the
modeled-external Java calibration case, the single explicit `unsupported`
result. Neither is ever counted as a negative. [Bifrost #1951](https://github.com/BrokkAi/bifrost/issues/1951)
tracks the final cross-language production-taint acceptance work; the defects
and coverage gaps this population exposes are tracked as bifrost-dev #2637
(Ruby), #2638 (Rust `gap_contract`), #2639 (`element-object`), and #2640
(nested-callable roots).

## Python modeling matrix

`run-bifrost-modeling --language python` runs the twenty-four assertions of
[the benchmark-controlled taint-modeling matrix](../../docs/modeling-matrix.md)
for Python, writing `reports/bifrost-python-modeling.json` with raw evidence
under `reports/raw/bifrost-python-modeling/`. This is a **modeling**-tier
population with its own denominator: it is never in a core denominator, and no
number here is ever added to or averaged with a kernel number. The two answer
different questions.

The preregistered partition scored **one of six categories** for this adapter
— declared sources and sinks — and that is the honest starting position for a
standalone policy CLI whose modeling surface lives in an embedding.
[Amendment A9](../../docs/modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false)
added a second, **declared sanitizers**, on a measurement that contradicted this
README. The remaining four are `unsupported` with the preregistration's
rationale retained verbatim, decided from the template identity **before the
binary is invoked**: external semantic-model activation is recorded in this
README as a future CLI capability, and the propagator, entry-root, and
persistence-boundary cells are the document's *to be verified* cells, which its
own rule treats as unsupported until shown otherwise. An `unsupported` cell is
coverage, never a negative and never a false negative.

The model is `adapters/bifrost/policies/model-python.rqlp`: two endpoint sets,
adding the declared source `fetch_remote` beside `dfb_source` and the declared
sink `record` beside `dfb_sink`, plus — since Amendment A9 — one `:sanitizers`
entry declaring `scrub` and deliberately not its sibling `sanitize`. Unlike
every committed kernel policy it sets
`:call-modeling (call-modeling :unmodeled require-model)` rather than
`optimistic`, which is
[the load-bearing-model requirement](../../docs/modeling-matrix.md#the-load-bearing-model-requirement);
the runner reads the policy before the run and refuses one that does not.

The first run, on the pinned v0.10.6 build, decides all four scored assertions
correctly — two `reached` positives and two `not-reached` negatives, with no
`inconclusive` and no `runner-error` — and takes the preregistered
`unsupported` on the other twenty. **Re-run pending:** that report predates
Amendment A9, so its four sanitizer cells are still recorded there as
`unsupported`; the scored evidence for them lands with the next evidence
re-run. **Load-bearing verification:** re-running
the same four fixtures under a policy identical except that the two declared
endpoint entries are removed drops both positives from one finding to zero. The
model, not the propagation, is what this tier scores. See [the Python
taint-modeling matrix](../../docs/python-modeling.md).

## JavaScript taint-modeling matrix

Separate from every kernel above, and never pooled with one. The
[modeling matrix](../../docs/modeling-matrix.md) scores whether an engine can
*be told* things — a source it did not know, a sanitizer, a summary, an entry
point, a persistence boundary — and its preregistered partition gives this
adapter **categories S and Z** — declared sources and sinks, and declared
sanitizers, four of the twelve templates. S was preregistered; Z arrived with
[Amendment A9](../../docs/modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false).
The other four categories are `unsupported` for the standalone policy CLI,
decided from the template identity before the binary is invoked and retained
verbatim with the document's own rationale.

- Artifact: `adapters/bifrost/policies/model-javascript.rqlp`. It declares two
  `:sources` entries bound to `return-value`, two `:sinks` entries bound to
  `(argument :index 0)`, one `:sanitizers` entry declaring `scrub` and not its
  sibling `sanitize`, and nothing for categories P, O, E, or B — a declined
  category is absent from the artifact rather than approximated in it.
- Load-bearing model: the policy sets `:call-modeling (call-modeling :unmodeled
  require-model)`, which the pinned v0.10.7 build accepts. The runner refuses
  the artifact if that setting is missing, and refuses it again if it names the
  kernel policies' permissive default. This does **not** promote the
  preregistration's *to be verified* cell for category P: that cell also needs a
  propagator or transform declaration surface, which no committed policy has,
  and promoting a partition cell is a dated amendment on the preregistration
  rather than a side effect of a language pull request.
- Invocation:
  `cargo run -- run-bifrost-modeling --language javascript --bifrost <path>`,
  writing `reports/bifrost-javascript-modeling.json` with raw evidence under
  `reports/raw/bifrost-javascript-modeling/`.
- Result on the pinned build: of the four scored assertions, one is decided
  (`model-declared-source-negative`, `not-reached`) and three are
  `inconclusive`, retaining `partial_discovery` and "procedure value-flow
  snapshot … is unknown". The policy does bind both declared identities — the
  retained reports carry the finding message and a source-to-sink display path
  — but the run does not complete, so the outcome is incomplete analysis and
  never a negative. That is the same JavaScript incompleteness the frozen
  kernel slice records, and it is the whole of the difference between this row
  and the Python row above, which decides all four of its cells. The other
  twenty assertions are capability coverage with no analyzer invocation at all.
  Its configuration hash is
  `25e1399fb9b7c2e5dfa469d56e9b4edeccff655f1d8866290f4f55d29eb7117f`.
- **Re-run pending.** That row and that hash describe the pre-A9 run and the
  pre-A9 artifact. The committed policy now carries the sanitizer declaration,
  so the next run of this slice scores four more cells and reports a different
  configuration hash; until it lands, the retained report records category Z as
  `unsupported`.
- **Load-bearing verification.** Removing the `Config.fetchRemote` source entry
  from a copy of the policy drops `model-declared-source-positive` from one
  finding to zero
  (`reports/raw/load-bearing-javascript-modeling/bifrost-declared-source-{with,without}-model.json`).
  The declaration, not the propagation, is what the cell scores.

See [the JavaScript modeling matrix](../../docs/javascript-modeling.md).

## Java taint-modeling matrix

Wave M1's last row, and the same shape as the two above. The
[modeling matrix](../../docs/modeling-matrix.md) gives this adapter
**categories S and Z** — declared sources and sinks, and declared sanitizers
since [Amendment A9](../../docs/modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false),
four of the twelve templates — and the other four categories are `unsupported`
for the standalone policy CLI, decided from the template identity before the
binary is invoked and retained verbatim with the document's own rationale.

- Artifact: `adapters/bifrost/policies/model-java.rqlp`. Two `:sources` entries
  bound to `return-value`, two `:sinks` entries bound to
  `(argument :index 0)`, one `:sanitizers` entry declaring `Clean.scrub` and not
  its sibling `Clean.sanitize`, and nothing for categories P, O, E, or B.
- Load-bearing model: the policy sets `:call-modeling (call-modeling :unmodeled
  require-model)`. The preregistration recorded the pinned CLI's *acceptance* of
  that setting as one of two unverified facts behind Bifrost's category-P cell;
  it is now confirmed by
  [Amendment A5](../../docs/modeling-matrix.md#a5--2026-08-26-bifrost-v0106-accepts-unmodeled-require-model),
  which moves no cell. The other obstacle — showing that a propagator or
  transform section actually lowers — is untouched, so category P stays
  `unsupported`.
- Invocation:
  `cargo run -- run-bifrost-modeling --language java --bifrost <path>`, writing
  `reports/bifrost-java-modeling.json` with raw evidence under
  `reports/raw/bifrost-java-modeling/`.
- Result on the pinned build: **all four scored assertions decided correctly** —
  two `reached` positives, two `not-reached` negatives, no `inconclusive` and no
  `runner-error`, with neither undeclared sibling (`Config.fetchLocal`,
  `Audit.discard`) picked up. That is Python's row exactly, and it is the
  difference between Java and JavaScript: the JavaScript slice's three
  `inconclusive` cells are that language's engine incompleteness, not a modeling
  property. Its configuration hash is
  `921d2c8e531813bf7c9bb93fd6da710e62020f60f9caadc7ac0096c5c31121d9`.
- **Re-run pending.** That row and that hash describe the pre-A9 run and the
  pre-A9 artifact. The committed policy now carries the sanitizer declaration,
  so the next run of this slice scores four more cells and reports a different
  configuration hash; until it lands, the retained report records category Z as
  `unsupported`.
- **Load-bearing verification.** Removing the `Config.fetchRemote` source entry
  from a copy of the policy drops `model-declared-source-positive` from one
  finding to zero
  (`reports/raw/load-bearing-java-modeling/bifrost-declared-source-{with,without}-model.json`).

See [the Java modeling matrix](../../docs/java-modeling.md).

## JavaScript tool-native probe set

Zero of six, decided before the CLI is asked about a fixture — and the twelve
assertions were produced without Bifrost analyzing anything. The run reads the
pinned binary's version banner once so its report names an observed pin
([the run-level identity is witnessed](../../docs/native-profile.md#the-run-level-identity-is-witnessed-including-at-0--6)).

The tool-native activation contract is built-in policy packs only:
`--policy-pack` / `--policy-category` / `--policy-id` over the catalog
`--list-policies` prints. A native run may not pass `--policy-file`, which is
how every benchmark-controlled Bifrost run in this repository supplies its
models, and the no-benchmark-models gate refuses one.

The standalone policy CLI ships no taint policy and no source or sink endpoint
set. BrokkAi/bifrost-dev **#2620** is the open issue under which shipped
endpoints — its own candidate inventory names `System.getenv`, `Runtime.exec`,
`ProcessBuilder` — would first exist at all, and **#2691** is the standalone-CLI
activation surface for external procedure summaries that this profile would
need. **#1871** (closed) supplies summaries, not endpoints. Without a source and
a sink, no cell in this profile can produce a finding, which is why every
template reads the same way, and the sanitizer and summary categories are
additionally declined for the surface gaps this README already records above.

Stating that position in a preregistration published by Bifrost's own vendor,
before a run, with the vendor's open issues named, is the point. It is capability
coverage: the twelve `unsupported` assertions are never negatives and reduce no
denominator.

See [the JavaScript tool-native probe set](../../docs/javascript-native.md).

## Java tool-native probe set

Wave N1's first row. See [the tool-native profile](../../docs/native-profile.md)
for the contract and [the Java row](../../docs/java-native.md) for the results.

- **Activation contract.** Built-in policy packs only: `--policy-pack` /
  `--policy-category` / `--policy-id` over the catalog `--list-policies`
  prints. A native run may **not** pass `--policy-file`, which is how every
  benchmark-controlled Bifrost run supplies its models, and the
  no-benchmark-models gate refuses one.
- **Invocation:** `cargo run -- run-bifrost-native --language java`, writing
  `reports/bifrost-java-native.json`. Configuration hash
  `0badb216237f88ed709f45e32283b0ea8030875e742424c3377e1fbce525c6d3`.

**Result: zero of six templates activated, twelve `unsupported` outcomes, and
the CLI was never asked about a fixture.** Every cell is decided from the
template identity before the CLI analyzes anything, with the preregistered rationale retained
verbatim under `reports/raw/bifrost-java-native/<case-id>-unsupported.json`.
The standalone policy CLI ships no taint policy and no source or sink endpoint
catalog — bifrost-dev **#2620** is the open issue under which the first ones
would ship, and **#2691** is the standalone-CLI activation surface an external
catalog would need — so no template can produce a finding whatever else the
engine expresses.

That is capability coverage, not a negative: it reduces no denominator and is
never converted into a clean answer. It is also the honest reading of the gap
between this row and the benchmark-controlled matrix, which scores Bifrost on a
category it declines here **using the same binary**, because there the
benchmark supplies the endpoints. Publishing that gap in a preregistration
written by Bifrost's own vendor, before the run, with the vendor's open issues
named, is the point.

See [the Java tool-native probe set](../../docs/java-native.md).

## Python tool-native probe set

Wave N1's final row, and it closes the wave. See
[the tool-native profile](../../docs/native-profile.md) for the contract and
[the Python row](../../docs/python-native.md) for the results.

- **Activation contract.** Built-in policy packs only: `--policy-pack` /
  `--policy-category` / `--policy-id` over the catalog `--list-policies`
  prints. A native run may **not** pass `--policy-file`, which is how every
  benchmark-controlled Bifrost run supplies its models, and the
  no-benchmark-models gate refuses one.
- **Invocation:** `cargo run -- run-bifrost-native --language python`, writing
  `reports/bifrost-python-native.json` with retained decisions under
  `reports/raw/bifrost-python-native/`.

**Result: zero of six templates activated, twelve `unsupported` outcomes, and
the CLI was never asked about a fixture.** The retained decisions are
byte-identical whatever the binary reports; the run does read its version
banner once, so the nonexistent-path check this row was originally verified
with no longer holds, by design
([the run-level identity is witnessed](../../docs/native-profile.md#the-run-level-identity-is-witnessed-including-at-0--6)). The standalone
policy CLI ships no taint policy and no source or sink endpoint catalog, so no
template can produce a finding regardless of what else the engine expresses;
the sanitizer and external-summary rows restate this README's own statements
about sanitizer lowering and embedding-based activation.

That is capability coverage, not a negative: an `unsupported` cell never
becomes a clean negative and never reduces anyone's denominator. Bifrost has no
tool-native Python denominator, which is different from having a zero.

See [the Python tool-native probe set](../../docs/python-native.md).

