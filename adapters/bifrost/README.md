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
struct, pointer-alias, array, and `panic`/`recover` adaptations. Every
kernel command selects only its own language's 32 core assertions and writes a
dedicated report. The Java calibration slice also
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
```

The smoke command selects only cases with an explicit Bifrost policy or
unsupported declaration. Cases for other adapters are not emitted into the
Bifrost report. Each selected case is materialized into an isolated workspace
and evaluated through Bifrost's path-based policy CLI (`--root` plus
`--policy-file`). A report with incomplete runs is normalized as `inconclusive`
even when it contains no findings; it is never interpreted as a negative.

## Retained v0.10.2 snapshot

The checked-in `reports/bifrost-smoke.json` was produced with Bifrost v0.10.2,
build identity `c2116609f5fc1be318c8fb76fb83763cf326bab6`. The exact binary
SHA-256 is
`93b55dd20c283c278f586e8c8e6ad6bf0e9f5f08165b56096e110af0450d0873`.
The smoke report contains 118 normalized results: 50 `reached`, 37
`not-reached`, 30 `inconclusive`, and 1 `unsupported`. Every result's
`raw_output` points to its retained per-case Bifrost JSON under
`reports/raw/bifrost/`; the normalized report and raw reports are separate
evidence layers. Raw completion and diagnostic fields are never replaced with
a synthetic `not-reached` outcome, and normalized witness checkpoints remain
empty until the adapter can prove their locations.

The 32-case Java kernel has 14 `reached`, 8 `not-reached`, and 10
`inconclusive` outcomes, with 17/32 assertions matching expected polarity
(17 of 22 decisive outcomes). The 32-case Python kernel has 12
`reached`, 8 `not-reached`, and 12
`inconclusive`, with 16/32 assertions matching expected polarity
(16 of 20 decisive outcomes). Its dedicated report is
`reports/bifrost-python-kernel.json` and raw evidence is under
`reports/raw/bifrost-python-kernel/`. The 32-case
JavaScript kernel has 14 `reached`, 12 `not-reached`, and 6 `inconclusive`,
with 19/32 assertions matching expected polarity (19 of 26 decisive outcomes).
This v0.10.2 evidence matches v0.10.1 case-for-case, but does not restore the
complete Java correctness observed in the v0.9.5 snapshot.

The four post-freeze kernels — Kotlin, TypeScript, C#, and Go — were run with
a locally built Bifrost v0.10.5, build identity
`728ac69ab93224151c6c951b23d2f5bc681d8558`. The frozen v0.2.0 slices above
remain v0.10.2 evidence until the next freeze re-runs every Bifrost slice on
one version.

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

The JavaScript alias-propagation and array-element pairs retain
`partial_discovery` evidence, while the exception-catch pair retains
`capability_incomplete` evidence; all six remain `inconclusive`. The Java
heap/separation and exception pairs and the Python heap/control-flow pairs
likewise remain `inconclusive`, never negative results. The Ruby direct-flow
pair retains `partial_discovery` evidence, and the modeled-external Java
calibration case is the single explicit `unsupported` result. [Bifrost #1951](https://github.com/BrokkAi/bifrost/issues/1951)
tracks the final cross-language production-taint acceptance work.
