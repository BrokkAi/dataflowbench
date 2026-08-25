# Rust propagation kernel

Issue #38 ports the applicable scored propagation templates to Rust. The Rust
cases keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct changes to Rust syntax or to the
native construct the [applicability matrix](applicability-matrix.md) fixes.

The matrix classifies `dfb-template-exception-catch` as **inapplicable** to
Rust, so the Rust core denominator is **15 templates and 30 assertions**, not
16 and 32. Every scored Rust template has exactly one `positive` and one
`negative` `core` case.

## The excluded template

`dfb-template-exception-catch` asks whether a typed value survives a non-local
control transfer to a handler. Rust has no such construct as an idiomatic
recoverable transfer:

- panics are the abort path, not the recoverable one; idiomatic Rust carries
  recoverable errors as values;
- `std::panic::catch_unwind` is not guaranteed to catch anything — a
  `panic=abort` build profile terminates the process instead, so the template's
  question would not even be well posed across profiles;
- the payload a caught panic yields is type-erased as `Box<dyn Any>`, which
  loses exactly the typed, value-carrying property the template tests.

No adaptation asks the same source-to-sink question, so the template is
excluded with that rationale. The exclusion reduces **only** the Rust
denominator. A 15-template Rust score and a 16-template score for another
language are not interchangeable and are never averaged into one number without
stating the population.

The nearest Rust-idiomatic construct — a value carried through the error
variant of a `Result` across a call boundary, propagated with `?` — is routed
to a `language-extension` case instead of being dropped. It has its own
scorecard tier and never enters the core denominator; see
[Language extension](#language-extension-result--error-path-propagation) below.

## Adaptations

| Stratum | Template ID | Rust adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct free-function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | **Adapted:** a `let mut` local is either preserved or reassigned to a constant before the sink. Rust locals are immutable by default, so an immutable binding cannot express the kill. |
| Local | `dfb-template-local-multi-step-chain` | `let` locals carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | Rust `i32` arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One `relay` function is called with tainted and clean values; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | `choose_first` returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop free-function return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two nested free-function returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | **Adapted:** two `Holder` struct values with the same field name stand in for the distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | **Adapted:** one `Holder` struct has separate `tainted` and `clean` fields. |
| Heap/separation | `dfb-template-alias-propagation-separation` | **Adapted:** shared-reference aliasing — see below. |
| Heap/separation | `dfb-template-array-element-separation` | A `[i32; 2]` array with distinct constant indices stands in for the Java array. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `if true` / `if false` conditions make the positive/negative path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | **Adapted:** a `for` loop over a `let mut` local either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | **Inapplicable** — excluded, see above. |

### The alias-propagation adaptation actually chosen

The matrix permits either shared-reference (`&T`) aliasing read at the sink or
`Rc<RefCell<T>>` where interior mutation is required, and requires this
contract to record which one the fixtures use.

**The Rust kernel uses shared-reference (`&T`) aliasing.** `Rc<RefCell<T>>` was
not needed and is not used: introducing a reference-counted cell would add a
standard-library container and a runtime borrow check to a template that is
about aliasing, not about containers, and would test the analyzer's model of
`RefCell` rather than its alias reasoning.

Exclusive `&mut` aliasing — the direct analogue of the Java/C# fixture, where
the alias is created first and the store happens afterwards through the
original binding — is prohibited by the borrow checker: an `&mut` borrow is
exclusive, so the original binding cannot be written while the alias is live.
The fixtures therefore reorder the two statements relative to the C# kernel:
the tainted store happens through the owning binding first, and the shared
alias is taken afterwards and read at the sink.

```rust
let mut original = Holder { value: 0 };
let distinct = Holder { value: 0 };
original.value = dfb_source(); // DFB-WITNESS: alias-propagation-store
let alias = &original;         // DFB-WITNESS: alias-propagation-alias
dfb_sink(alias.value);         // the negative reads distinct.value instead
```

The reordering is a borrow-checker obligation, not a weakening: the positive
still requires the analyzer to carry taint from a store on one binding to a
read through a different binding that aliases it, and the negative still
requires it to keep a second, unaliased struct value distinct.

## Fixtures

All Rust fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
function names, in Rust's snake_case, which is the same spelling the
cross-language contract already uses. Fixtures are single `.rs` files with no
Cargo manifest, no module structure, and no external dependency. They are not
compiled by any adapter; they do type-check under `rustc 1.97.1` with
`--edition 2021 --crate-type=lib`, with only `unused_variables` warnings, which
the frozen direct-flow fixture already carries. Adapters may lower the
benchmark endpoints through their own models, but the case metadata stays
analyzer-neutral and reports retain only observed evidence.

## Case population and the frozen direct pair

The Rust core population is the 30 `taint`/`core` cases under
`cases/taint/rust/`. Twenty-eight of them were authored for this kernel with
`fixture_provenance.revision` `m2-rust-kernel`. The direct-propagation pair
(`dfb-taint-rust-direct-positive` and `dfb-taint-rust-direct-negative`)
predates it: it is the Rust member of the 13-language direct-flow breadth
slice, and it is frozen byte-for-byte in the published v0.2.0 manifest
(`reports/freeze.json`). Its `case.json` therefore keeps
`fixture_provenance.revision` `m1a-direct-core`, keeps the breadth policy
reference `adapters/bifrost/policies/core-direct.rqlp`, and carries no CodeQL
model reference.

Editing those two files would invalidate the published v0.2.0 evidence, so the
runners accommodate them instead, exactly as the [C# kernel](csharp-kernel.md)
does:

- the Bifrost Rust selector accepts either `core-rust-kernel.rqlp` or the
  breadth `core-direct.rqlp` policy for a Rust case, and evaluates each case
  through the policy it declares;
- the CodeQL Rust selector defaults a Rust case with no `codeql` model
  reference to this kernel's query, and rejects any Rust case that names a
  different query.

The same case is a member of two populations, but its results are never pooled:
the breadth result lives in `reports/bifrost-smoke.json` and the kernel result
in the dedicated Rust reports below.

## Language extension: `Result` / `?` error-path propagation

Two additional cases carry `score_tier` `language-extension` and the template
identity `dfb-template-result-error-propagation`:

- `dfb-taint-rust-result-error-propagation-positive`
- `dfb-taint-rust-result-error-propagation-negative`

The fixture carries the controlled value in the field of a `FlowError` struct
inside `Err(..)`, propagates it across a call boundary with `?`, and reads it
from the error binding of a `match` at the sink. The negative differs only in
what reaches the sink.

This tier is scored separately and **never** changes the 15-template, 30-
assertion core denominator. `validate_rust_kernel_population` in `src/main.rs`
enforces that: the core subset must be exactly 30 balanced assertions over the
15 applicable templates, and the only other tier a Rust kernel run may select
is `language-extension`. DataFlowBench's shared pair-balance validation
(`validate_balanced_core_pairs`) applies to `core` cases only, so the tier is
not obliged to be a pair; it is authored as one anyway, because a positive with
no minimally different negative is a weaker assertion.

## Bifrost selection and reproduction

The Bifrost Rust slice uses the language-qualified policy
`adapters/bifrost/policies/core-rust-kernel.rqlp`, whose source and sink
selectors are `(language rust (call :callee (name "dfb_source")))` and
`(language rust (call :callee (name "dfb_sink")))`, with argument index 0 as
the dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-rust-kernel --bifrost /path/to/bifrost
```

The command selects only the 30 Rust core assertions plus the two
`language-extension` assertions, materializes one isolated workspace per case
outside the repository, writes the normalized report to
`reports/bifrost-rust-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-rust-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

## CodeQL selection and reproduction

### Rust support status in the pinned CLI

CodeQL CLI 2.26.3 — the pinned version — ships a `rust` extractor
(`codeql resolve languages` lists it at
`<dist>/codeql/rust`), and `codeql pack install` resolves the library pack
`codeql/rust-all@0.2.19` from the registry. The CLI itself emits **no maturity
label**: neither `codeql version --format=json` nor
`codeql resolve languages --format=betterjson` reports a beta, preview, or GA
flag for any extractor, so there is no in-CLI string to quote. What the pinned
CLI does report, and what this contract pins, is:

- extractor `rust`, `version: 0.1.0` in
  `<dist>/codeql/rust/codeql-extractor.yml`, with `build_modes: [none]`;
- library pack `codeql/rust-all@0.2.19`, built for `cliVersion: 2.26.3` at
  source sha `44a68d3a47fcbcd6a6a76ec7d1c1b3a1a28b201e`.

Both are pre-1.0 version numbers, which is consistent with GitHub's documented
**public preview** status for CodeQL Rust support and inconsistent with the
1.x-and-above packs the GA languages ship (`codeql/csharp-all@7.1.2`,
`codeql/javascript-all@2.9.0`). Rust results in this repository are therefore
labelled and read as **public-preview analyzer evidence**: they are real,
reproducible observations of the pinned toolchain, and they are not a claim
about a stable Rust analyzer.

### Pack and query

The CodeQL Rust vertical slice is the 30 core assertions plus the two
`language-extension` assertions. Every selected case is analyzed with the
dedicated query:

```text
adapters/codeql/rust/queries/RustKernel.ql
```

The query is owned by the dedicated Rust pack manifest at
`adapters/codeql/rust/qlpack.yml`; the Java, JavaScript, TypeScript, Python,
Kotlin, and C# packs are separate. The runner must not select any other
language, calibration cases, or the direct-flow breadth population.

Registry retrieval of the Rust pack succeeded for the pinned CLI, so no source
workspace fallback was needed:

```bash
codeql pack install adapters/codeql/rust
cargo run -- run-codeql-rust-kernel --codeql /path/to/codeql
```

`codeql pack install` resolved `codeql/rust-all@0.2.19` for CodeQL CLI 2.26.3
(build SHA `7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`); the complete transitive
set is committed in `adapters/codeql/rust/codeql-pack.lock.yml`. If registry
retrieval is unavailable, a matching official source workspace or CLI bundle
pack root passed through `--codeql-packs` is a valid reproduction input, as
documented for the [JavaScript kernel](javascript-kernel.md).

### Why the runner generates a Cargo manifest

The Rust extractor accepts `--build-mode=none` and never compiles a fixture,
but it only runs its semantic analyzer when it finds a Cargo manifest in the
source root. Extracting a bare `.rs` file produces the extractor warning

```text
semantic analyzer unavailable (no manifest found): macro expansion will be skipped
```

and a syntax-only database (about 15 KiB of relations) in which no call target
resolves. The runner therefore writes a minimal single-crate `Cargo.toml` into
each materialized workspace, with `[[bin]] path` pointing straight at the
case's own fixture file and an empty `[workspace]` table so Cargo does not walk
out of the temporary directory. The fixture stays at the workspace root rather
than moving under `src/`, which keeps SARIF locations on the case's own anchor
paths. With the manifest present the extractor loads the manifest and library
sources and produces a database of about 38 MiB.

The generated manifest is an adapter artifact, not fixture content: no
`Cargo.toml` is checked in beside any case, and `fixture_files` lists only the
`.rs` file. For each case the runner creates one cold Rust database from that
generated workspace, runs the dedicated query, and removes the temporary
workspace and database after retaining the evidence. The normalized report is
`reports/codeql-rust-kernel.json` and the raw SARIF (or raw runner diagnostics
when CodeQL cannot produce SARIF) is retained per case under
`reports/raw/codeql-rust-kernel/`.

## Joern selection and reproduction

```bash
cargo run -- run-joern-rust-kernel --joern <joern-cli>/joern
```

The command selects the 30 Rust **core** assertions runner-side
(`language == "rust"`, `track == "taint"`, `score_tier == "core"`) against the
15-template set, and drives the single shared kernel script
`adapters/joern/queries/kernel.sc` with `language=RUST`. Unlike the Bifrost and
CodeQL Rust slices, the two `language-extension` assertions are **not** in this
population: the Joern Rust kernel is the core denominator and nothing else. One
cold CPG is built per case inside a per-case scratch root, and the retained
evidence document is written to `reports/raw/joern-rust-kernel/<case id>.json`.

### Joern needs the same generated manifest, for a different reason

Rust is the only benchmark language whose Joern frontend refuses a loose source
file. `rust2cpg` walks a Cargo crate; handed a bare `.rs` fixture it exits
successfully and produces an empty CPG — no methods, no calls at all. CodeQL's
extractor degrades to a syntax-only database in the same situation; Joern's
produces nothing. Both failure modes look like a clean negative if they are not
caught, which is why neither runner analyzes a bare file.

The Joern runner therefore reuses `write_rust_cargo_manifest`, the same
single-crate `Cargo.toml` the CodeQL Rust runner generates, written into the
per-case scratch workspace and destroyed with it. No `Cargo.toml` is checked in
beside any fixture and `fixture_files` still lists only the `.rs` file.

Keeping the fixture at the crate root rather than moving it under `src/` also
settles the anchoring question: Joern reports node locations as crate-relative
paths, so the fixture stays `local_chain_positive.rs` in the evidence and the
shared sink-callsite reconciliation matches it directly. A generated
`src/main.rs` layout would have forced the runner to map the reported path back
to the case's anchor file before any flow could be proved.

`rust2cpg` is new in Joern `4.0.610` — the first release to ship it. Its results
are recorded as a snapshot of a young frontend.

## Anchor evidence and result semantics

CodeQL query results are evidence, not ground truth by themselves. The runner
reconciles SARIF result locations with the case's `DFB-SINK:` anchor. That
marker identifies the anchored sink function declaration; the Rust dialect of
the shared reconciler reads the declared function name as the identifier
preceding the parameter list, and then accepts a SARIF result that lies in the
same fixture file on a line that calls that function. The result need not be on
the marker's own line. Rust and C# ask the reconciler the same two surface
questions and answer them identically, so they share one dialect
implementation. Query path evidence identifies the `DFB-SOURCE:` to sink flow,
and normalized results retain both anchor sets.

A successful, anchor-backed finding is `reached`; a successful analysis with no
matching finding is `not-reached`. Missing, ambiguous, or unmappable location
evidence is `inconclusive`, an explicitly unsupported capability is
`unsupported`, and a database, query, SARIF, or runner failure is
`runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 15 balanced assertions.

## Observed results

The CodeQL and Bifrost snapshots cover all 30 Rust core assertions and both
`language-extension` assertions; the Joern snapshot covers the 30 core
assertions only. The three populations — Rust core, Rust language extension,
and every other language — are separate and are not pooled.

### CodeQL, `reports/codeql-rust-kernel.json`

CodeQL CLI 2.26.3, build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`,
with `codeql/rust-all@0.2.19` from the committed lock — **public-preview
analyzer evidence**, per the status section above. Configuration hash
`cc2c728b66e0c273545e3531a672c0987473f3830f5df80b0839f5d04c33600b`.

**Core, 30 assertions:** 17 `reached` and 13 `not-reached`, with zero
`inconclusive`, `unsupported`, or `runner-error` outcomes. **28 of 30 match the
expected polarity.** All 15 positives are `reached`, so there are no false
negatives at all. The two mismatches are both false positives:

- `dfb-taint-rust-array-element-negative`
- `dfb-taint-rust-loop-carried-negative`

That is the array-element and loop-carried pair of false positives the Java,
Kotlin, and C# kernels also show against this CLI. What Rust does *not* share
with them is their false-negative set: the alias-propagation and
arithmetic-expression positives are false negatives for every other kernel and
are `reached` here, as is every heap positive. On this fixture population the
preview Rust analyzer is the most accurate of the CodeQL kernels in this
repository — with the caveats that the denominator is 15 templates rather than
16, that `exception-catch` (a template several other kernels miss) is not in it,
and that a single 30-assertion population is not a general claim about the
analyzer.

**Language extension, 2 assertions:** both `not-reached`, so 1 of 2 matches the
expected polarity. `dfb-taint-rust-result-error-propagation-positive` is a
**false negative**: the pinned analyzer does not carry the controlled value from
the `FlowError` field inside `Err(..)`, through the `?` propagation across the
call boundary, to the `match` error binding at the sink. The negative is
correctly `not-reached`. This is a real, reproducible capability observation and
is reported on its own tier; it does not change the core denominator, and no
fixture was adjusted to make the analyzer pass.

All 32 retained raw outputs are SARIF files under
`reports/raw/codeql-rust-kernel/`, with zero error files, and normalized
`witness_checkpoints` are empty for every case: the adapter records anchor-backed
flow outcomes and leaves the path evidence in SARIF rather than fabricating
observed witness markers. End-to-end per-case wall clock, including generating
the Cargo manifest and creating the cold database, ranged from 50.8 s to 98.4 s
(about 40 minutes for the population). The 60-second `execution_budget` on the
cases describes the analysis budget shared with the other language kernels; Rust
extraction time — which includes rust-analyzer loading the manifest and library
sources for every case — is reported here rather than silently rebudgeted.

### Bifrost, `reports/bifrost-rust-kernel.json`

Bifrost 0.10.5, build identity `728ac69ab93224151c6c951b23d2f5bc681d8558`.
Configuration hash
`36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`; it covers
both `core-rust-kernel.rqlp` and the breadth `core-direct.rqlp`, because the
frozen direct pair is evaluated through the policy it declares.

**Core, 30 assertions:** 1 `reached`, 1 `not-reached`, 20 `inconclusive`, and
8 `runner-error`. Only the direct-propagation pair is decisive, and both of its
outcomes match the expected polarity — 2 of 2 decisive outcomes, 2 of 30
assertions.

The 20 inconclusive results retain `partial_discovery` with a diagnostic of the
form "taint discovery is incomplete: procedure value-flow snapshot for ... is
unsupported/unknown"; they are capability evidence, never negatives. The eight
`runner-error` results are the entire heap/separation stratum — both polarities
of object separation, same-object field separation, alias propagation, and
array element. Their raw runs complete as `failed` with `internal_invariant`
and the diagnostic "taint semantic provider failed: semantic IR gap_contract
error in procedure 2: gap 8 duplicates the same scoped fact"; a failed
evaluation is an execution error, so it is normalized as `runner-error` rather
than `inconclusive`, and it is never a negative. Several results also carry the
policy's own finding message, so Bifrost located candidate flows before the
analysis failed or went incomplete.

**Language extension, 2 assertions:** both `inconclusive`, both retaining
`partial_discovery`. No decisive outcome, so nothing is scored on this tier for
Bifrost.

This mirrors the C# kernel's Bifrost profile, where only the direct pair is
decisive; the Rust `internal_invariant` failures on the struct and array
fixtures are a distinct, more specific incompleteness than the C#
`capability_incomplete` results, and are recorded as observed rather than
diagnosed here.

### Joern, `reports/joern-rust-kernel.json`

Joern 4.0.610, build identity `joern-cli:4.0.610`, frontend `rust2cpg`.
Configuration hash
`ab10e81860305e492a930e2c2691873b23be25e97e5b354ca785058e09a20025` — the same
hash every other Joern kernel carries, because all six drive one unmodified
script.

**Core, 30 assertions:** 16 `reached` and 14 `not-reached`, with zero
`inconclusive`, `unsupported`, or `runner-error` outcomes, 30 retained evidence
documents and zero error documents. **27 of 30 match the expected polarity.**

The three mismatches:

- false negative: `dfb-taint-rust-alias-propagation-positive`;
- false positives: `dfb-taint-rust-infeasible-branch-negative` and
  `dfb-taint-rust-loop-carried-negative`.

That is the recurring Joern mismatch set — field aliasing missed, infeasible
branch and loop-carried kill over-approximated — intersected with Rust's 15
applicable templates; the fourth member of that set, exception catch, is not a
Rust cell. Joern and CodeQL agree only on the loop-carried false positive: Joern
misses the field alias CodeQL resolves and over-approximates the infeasible
branch CodeQL decides, while CodeQL over-approximates the array-element
separation Joern decides correctly. Two decisive analyzers disagreeing this way
on a 15-template denominator is exactly the sort of contrast the kernel exists to
surface, and neither result was adjusted to bring them closer.

The two `language-extension` assertions are **not** in this population; unlike
the CodeQL and Bifrost Rust slices, the Joern kernel selects the core 30 only.

`rust2cpg` shipped for the first time in Joern `4.0.610`. These are its first
recorded DataFlowBench results, and they are published as a snapshot of a
brand-new frontend rather than as a settled characterization of Joern on Rust.
What can be said flatly is that it decided every assertion: no case fell to
`inconclusive`, and no frontend or engine exception was caught. Per-case wall
clock, including cold CPG construction, ranged from 14.3 s to 52.6 s (about 12.6
minutes for the population), measured while five other Joern kernels were
running concurrently on the same host.

Normalized `witness_checkpoints` are empty for every case, as for every other
Joern kernel: the adapter records anchor-backed flow outcomes and retains the
element-by-element path evidence in the raw document.

## Population boundaries

Rust results are their own population. They are never pooled with the Java,
JavaScript, TypeScript, Python, Kotlin, or C# kernels, never pooled with the
13-language direct-flow breadth slice, and never averaged with a language whose
core denominator is not also 15 templates. The `language-extension` results are
a third population again, and never enter the core scorecard. The Java
calibration cases (`dfb-template-one-hop-relay` and
`dfb-template-modeled-external-summary`) have no Rust member and do not change
this denominator.
