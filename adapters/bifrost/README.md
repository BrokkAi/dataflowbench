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
and control-flow strata. The JavaScript parity slice uses the same template IDs
and the language-qualified `core-javascript-kernel.rqlp` policy, with any
language adaptations recorded on the canonical cases. See the [JavaScript
adaptation matrix](../../docs/javascript-kernel.md) for the syntax mapping and
the explicit exceptional-flow limitation. The Python parity slice uses
`core-python-kernel.rqlp`, and the Kotlin parity slice uses
`core-kotlin-kernel.rqlp`; see the [Kotlin kernel
contract](../../docs/kotlin-kernel.md) for its two `var`-based adaptations and
for why the Kotlin kernel run pins its policy for the whole population rather
than reading it from each case. The TypeScript parity slice repeats those 16
templates against `.ts` fixtures through `core-typescript-kernel.rqlp`; see the
[TypeScript adaptation matrix](../../docs/typescript-kernel.md). TypeScript is a
separate population from JavaScript and the two are never mixed. The C# parity
slice uses `core-csharp-kernel.rqlp`; its direct-propagation pair is frozen in
the v0.2.0 evidence with the breadth `core-direct.rqlp` policy, so the C#
selector accepts that policy too and evaluates each case through the policy it
declares; see [the C# kernel contract](../../docs/csharp-kernel.md). The Go
parity slice uses `core-go-kernel.rqlp` under the same frozen-direct-pair
arrangement; see [the Go kernel contract](../../docs/go-kernel.md) for its
struct, pointer-alias, array, and `panic`/`recover` adaptations. The C and C++
parity slices use `core-c-kernel.rqlp` and `core-cpp-kernel.rqlp` and are two
separate populations with two different denominators: C++ covers all 16
templates (32 core assertions), while C covers 15 (30 core assertions) because
`dfb-template-exception-catch` is inapplicable to C, and its two
`language-extension` cases run in the same slice on their own scorecard. See
[the C kernel contract](../../docs/c-kernel.md) and [the C++ kernel
contract](../../docs/cpp-kernel.md). The Rust parity slice uses
`core-rust-kernel.rqlp` under the same frozen-direct-pair arrangement as C# and
Go, and carries the same reduced denominator as C for a different reason:
`docs/applicability-matrix.md` classifies `exception-catch` as inapplicable to
Rust, so the Rust core population is 15 templates and 30 assertions, and the
`Result`/`?` construct Rust uses instead is carried by a `language-extension`
pair that the run also evaluates but never counts in the core denominator; see
[the Rust kernel contract](../../docs/rust-kernel.md). The Ruby parity slice
uses `core-ruby-kernel.rqlp` under the same frozen-direct-pair arrangement and
covers all 16 templates (32 core assertions); it is the one
analyzer-coverage-gated slice, run and retained as capability evidence while
the Ruby denominator is decided CodeQL-first, as [the Ruby kernel
contract](../../docs/ruby-kernel.md) records. Every kernel command
selects only its own language's core assertions — 32 for the 16-template
kernels, 30 for C and Rust — and writes a dedicated report. The Java
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
cargo run -- run-bifrost-python-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-kotlin-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-typescript-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-csharp-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-go-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-c-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-cpp-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-rust-kernel --bifrost /path/to/bifrost
cargo run -- run-bifrost-ruby-kernel --bifrost /path/to/bifrost
```

The smoke command selects only cases with an explicit Bifrost policy or
unsupported declaration. Cases for other adapters are not emitted into the
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

The 32-case Java kernel has 16 `reached` and 16 `not-reached` outcomes, with
32/32 assertions matching expected polarity and no incomplete outcomes (under
v0.10.2 it was 17/32). The 32-case Python kernel likewise has 16 `reached`,
16 `not-reached`, and 32/32 matching (v0.10.2: 16/32); its dedicated report is
`reports/bifrost-python-kernel.json` and raw evidence is under
`reports/raw/bifrost-python-kernel/`. The 32-case
JavaScript kernel has 16 `reached`, 16 `not-reached`, and 32/32 matching
(v0.10.2: 19/32). Unlike the v0.10.2 snapshot, this v0.10.5 evidence decides
all three of these kernels completely.

Every Bifrost slice in the v0.3.0 freeze — the smoke population and the
Kotlin, TypeScript, C#, Go, C, C++, Python, and Rust kernels — was run on this
one build.

The 32-case Kotlin kernel has 12 `reached`, 10 `not-reached`, and 10
`inconclusive`, with 19/32 assertions matching expected polarity (19 of 22
decisive outcomes; under v0.10.2 it was 17/32). Its dedicated report is
`reports/bifrost-kotlin-kernel.json` and raw evidence is under
`reports/raw/bifrost-kotlin-kernel/`. The ten `inconclusive` results are the
complete heap/separation stratum and the exception-catch pair, both polarities,
each retaining `partial_discovery` evidence; they mirror the Java kernel
profile and are never counted as negatives.

The 32-case TypeScript kernel, in its own report
`reports/bifrost-typescript-kernel.json` with raw evidence under
`reports/raw/bifrost-typescript-kernel/`, has 15 `reached`, 15 `not-reached`,
and 2 `inconclusive`, with 30/32 assertions matching expected polarity — all
30 decisive outcomes are correct. The two `inconclusive` results are the
exception-catch pair, retaining `capability_incomplete` evidence. Under
v0.10.2 this kernel matched 19/32; the alias-propagation and array-element
pairs are now decisive and correct.

The 32-case C# kernel, in its own report `reports/bifrost-csharp-kernel.json`
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
result; see [the Go kernel contract](../../docs/go-kernel.md).

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
never counted as a negative.

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

The JavaScript alias-propagation and array-element pairs retain
`partial_discovery` evidence, while the exception-catch pair retains
`capability_incomplete` evidence; all six remain `inconclusive`. The Java
heap/separation and exception pairs and the Python heap/control-flow pairs
likewise remain `inconclusive`, never negative results. The Ruby direct-flow
pair retains `partial_discovery` evidence, and the modeled-external Java
calibration case is the single explicit `unsupported` result. [Bifrost #1951](https://github.com/BrokkAi/bifrost/issues/1951)
tracks the final cross-language production-taint acceptance work.
