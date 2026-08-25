# Remaining-language applicability matrix

Issue #13 fixes, before any fixture is written, how the sixteen scored
propagation templates port to the remaining ten languages: C, C++, C#, Go,
Kotlin, PHP, Ruby, Rust, Scala, and TypeScript. The matrix is a contract, not
a survey. It decides each language's core denominator, records the adaptation
that a later kernel contract must spell out, and states which templates are
excluded and why. A language tranche may not begin fixture implementation
before its child issue records the classifications and the analyzer coverage
below.

The `template_id` values are stable benchmark identities. A template is never
renamed, split, merged, or silently dropped because a language spells its Java
or JavaScript construct differently.

## Classification vocabulary

Every cell in this matrix carries exactly one of three classifications.

- **`directly applicable`** — the Java/JavaScript/Python construct exists
  idiomatically in the target language; only surface syntax changes.
- **`language-adapted`** — the construct is replaced by a semantically
  equivalent native construct. The `template_id`, source-to-sink polarity,
  negative mechanism, and semantic intent are preserved. The adaptation is
  recorded in that language's kernel contract before fixtures are written.
- **`inapplicable`** — no native construct preserves the semantic intent. The
  template is excluded from that language's core denominator with a stated
  rationale, and any related language-only construct is routed to a
  `language-extension` scorecard case. An inapplicable cell never changes any
  other language's core denominator.

The matrix tables below abbreviate these as `direct`, `adapted`, and `n/a`.

## The sixteen templates

The population is the same one recorded in the [JavaScript adaptation
matrix](javascript-kernel.md) and the [Python kernel
contract](python-kernel.md), in four equally sized strata.

| Stratum | Template IDs |
| --- | --- |
| Local | `dfb-template-direct-propagation`, `dfb-template-local-overwrite-kill`, `dfb-template-local-multi-step-chain`, `dfb-template-arithmetic-expression-propagation` |
| Calls/returns | `dfb-template-call-context-separation`, `dfb-template-argument-position-separation`, `dfb-template-return-relay-one-hop`, `dfb-template-return-relay-two-hop` |
| Heap/separation | `dfb-template-object-separation`, `dfb-template-same-object-field-separation`, `dfb-template-alias-propagation-separation`, `dfb-template-array-element-separation` |
| Control transfer | `dfb-template-infeasible-branch`, `dfb-template-branch-join`, `dfb-template-loop-carried-kill`, `dfb-template-exception-catch` |

## Matrix by stratum

Columns are the ten remaining languages. Cell rationales are in the
per-language subsections that follow; the tables are the index, not the
justification.

### Local

| Template ID | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-local-overwrite-kill` | direct | adapted | adapted | direct | direct | direct | direct | direct | direct | adapted |
| `dfb-template-local-multi-step-chain` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-arithmetic-expression-propagation` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |

### Calls and returns

| Template ID | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-call-context-separation` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-argument-position-separation` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-return-relay-one-hop` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-return-relay-two-hop` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |

### Heap and separation

| Template ID | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-object-separation` | direct | direct | direct | direct | adapted | direct | direct | adapted | adapted | adapted |
| `dfb-template-same-object-field-separation` | direct | direct | direct | direct | adapted | direct | direct | adapted | adapted | adapted |
| `dfb-template-alias-propagation-separation` | direct | direct | direct | direct | adapted | direct | direct | adapted | adapted | adapted |
| `dfb-template-array-element-separation` | direct | direct | direct | direct | adapted | adapted | direct | adapted | direct | direct |

### Control transfer

| Template ID | TS | Kotlin | Scala | C# | Go | PHP | Ruby | C++ | C | Rust |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-infeasible-branch` | direct | direct | direct | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-branch-join` | direct | direct | adapted | direct | direct | direct | direct | direct | direct | direct |
| `dfb-template-loop-carried-kill` | direct | adapted | adapted | direct | direct | direct | direct | direct | direct | adapted |
| `dfb-template-exception-catch` | direct | direct | direct | direct | adapted | direct | adapted | direct | **n/a** | **n/a** |

## Per-language classifications

### TypeScript — 16/16 core, 32 assertions

All sixteen templates are directly applicable. TypeScript shares JavaScript
runtime semantics, so the fixtures differ from the JavaScript kernel by type
annotations only.

Fixtures are `.ts` files and form a distinct result population from the
JavaScript kernel. The runner must never mix the two populations; the existing
JavaScript CodeQL runner already explicitly refuses TypeScript cases, and the
TypeScript runner must refuse JavaScript cases in the same way.

### Kotlin — 16/16 core, 32 assertions

Directly applicable except for two local/control cells.
`dfb-template-local-overwrite-kill` and `dfb-template-loop-carried-kill` are
language-adapted through `var` mutable locals, because Kotlin defaults to
`val` immutability and an immutable local cannot express the kill.
`dfb-template-exception-catch` is directly applicable: a JVM unchecked
exception class carrying a field crosses `throw`/`catch` unchanged in meaning.
Array-element separation uses `Array<T>` or `IntArray` with distinct constant
indices.

### Scala — 16/16 core, 32 assertions

As Kotlin, `dfb-template-local-overwrite-kill` and
`dfb-template-loop-carried-kill` are language-adapted via `var`; idiomatic
Scala is immutable-first, and a `while` loop over a `var` preserves the
distinction between killing the carried value and computing from it.
`dfb-template-branch-join` is language-adapted to a statement-form
`if`/`else` assignment rather than Scala's expression-valued `if`.
`dfb-template-exception-catch` is directly applicable: `throw`/`catch` with a
value-carrying exception class. Arrays use `Array[T]`. The remaining
templates are directly applicable.

### C# — 16/16 core, 32 assertions

All sixteen templates are directly applicable: classes, fields, arrays,
`try`/`catch` with an exception object carrying a property, and `for`/`while`
loops all match the Java kernel constructs. C# is the closest of the ten
languages to the Java kernel.

### Go — 16/16 core, 32 assertions

The local stratum is directly applicable. The calls/returns stratum is
directly applicable; Go's multiple return values are not needed to express
any of the four templates.

Language-adapted cells:

- `dfb-template-object-separation` and
  `dfb-template-same-object-field-separation` use structs with named fields.
- `dfb-template-alias-propagation-separation` uses a pointer alias: `p := &s`
  creates the alias, while a second struct literal remains a distinct object.
- `dfb-template-array-element-separation` uses an array or slice with distinct
  constant indices.
- `dfb-template-exception-catch` is adapted to `panic(v)` with a deferred
  `recover()`. `recover` returns the panicked value, so the template's
  semantic intent — a value carried through a non-local control transfer that
  is distinct from a normal return — is preserved. This follows the
  JavaScript precedent of replacing Java's checked exception class with the
  language's native transfer construct.

If the pinned analyzers cannot model `recover`'s return value, the outcome is
capability evidence — `inconclusive` or `unsupported` — and never a silent
redesign of the case into a construct the tools happen to handle.

### PHP — 16/16 core, 32 assertions

Directly applicable except for one heap cell.
`dfb-template-array-element-separation` is language-adapted: PHP arrays are
ordered maps, so the pair uses distinct string or integer keys in place of
Java array indices. The object templates use ordinary classes; PHP object
handles give assignment-alias semantics, so
`dfb-template-alias-propagation-separation` is directly applicable.
`dfb-template-exception-catch` is directly applicable with an `\Exception`
subclass carrying a property.

### Ruby — 16/16 core, 32 assertions

Directly applicable except `dfb-template-exception-catch`, which is adapted in
surface form only: `raise`/`rescue` with a `StandardError` subclass carrying
an attribute is the same construct under Ruby naming. The heap stratum uses
`attr_accessor`-based objects. Arrays are direct.

### C++ — 16/16 core, 32 assertions

The local, calls/returns, and control-transfer strata are directly applicable,
including `dfb-template-exception-catch`, which throws a class instance and
catches it by reference with the value carried in a member.

Language-adapted cells:

- `dfb-template-object-separation` and
  `dfb-template-same-object-field-separation` use plain structs or classes
  with member access.
- `dfb-template-alias-propagation-separation` uses a reference or pointer
  alias to the same object while a second object stays distinct.
- `dfb-template-array-element-separation` uses a native array or
  `std::array` with distinct constant indices.

### C — 15/16 core, 30 assertions

`dfb-template-exception-catch` is **inapplicable**. C has no unwinding
construct that transfers a typed value to a handler. `setjmp`/`longjmp`
transfers control, but its `int` status payload and its undefined-local
semantics do not preserve the template's value-carrying intent, so no
adaptation exists that asks the same source-to-sink question. The C core
denominator is therefore 15 templates and 30 assertions.

The nearest C-idiomatic constructs are routed to `language-extension` cases
rather than dropped: error-code return-path propagation, and a goto-cleanup
handler carrying a value through a struct. Those cases have their own
scorecard and never enter the core denominator.

Language-adapted cells: `dfb-template-object-separation` and
`dfb-template-same-object-field-separation` use structs, and
`dfb-template-alias-propagation-separation` uses pointer aliasing. The local
stratum and array-element separation are direct.

### Rust — 15/16 core, 30 assertions

`dfb-template-exception-catch` is **inapplicable**. Panics are not Rust's
idiomatic recoverable transfer, `std::panic::catch_unwind` is not guaranteed
under `panic=abort` build profiles, and the payload is type-erased as
`Box<dyn Any>`. No adaptation preserves the template's typed, value-carrying
intent as a core obligation. The Rust core denominator is 15 templates and 30
assertions.

`Result`/`?` error-path propagation — a value carried through the error
variant across a call boundary — is routed to a `language-extension` case.

Language-adapted cells:

- `dfb-template-local-overwrite-kill` and `dfb-template-loop-carried-kill`
  use `let mut`.
- `dfb-template-alias-propagation-separation` uses shared-reference aliasing
  (`&T` to the same value, read at the sink), or `Rc<RefCell<T>>` where
  interior mutation is required. Exclusive `&mut` aliasing is prohibited by
  the borrow checker, and the adaptation actually chosen must be recorded in
  the Rust kernel contract.
- `dfb-template-object-separation` and
  `dfb-template-same-object-field-separation` use structs and field access.

The remaining templates are directly applicable.

## Core-denominator summary

| Language | Applicable templates | Core assertions |
| --- | --- | --- |
| TypeScript | 16 | 32 |
| Kotlin | 16 | 32 |
| Scala | 16 | 32 |
| C# | 16 | 32 |
| Go | 16 | 32 |
| PHP | 16 | 32 |
| Ruby | 16 | 32 |
| C++ | 16 | 32 |
| C | 15 | 30 |
| Rust | 15 | 30 |

The invariant: an inapplicable cell reduces only that language's denominator.
Cross-language macro-averages are computed per language population and are
never pooled over unequal template sets without stating the population. A
15-template C or Rust score and a 16-template score are not interchangeable
and are not averaged into one number without that statement.

## Analyzer and adapter coverage

These facts are recorded before any fixture implementation, and are verified
in-repo or against the pinned tool versions.

**Bifrost v0.10.2 direct-flow breadth** (frozen in
`reports/bifrost-smoke.json`) already produces decisive positive and negative
outcomes for `c`, `cpp`, `csharp`, `go`, `kotlin`, `php`, `rust`, `scala`, and
`typescript`. Ruby is `inconclusive` for both direct assertions. The Ruby
tranche is therefore gated on resolving Bifrost Ruby indexing; alternatively
the tranche proceeds CodeQL-first, with the Bifrost outcomes retained as
inconclusive capability evidence and never counted as negatives.

Each language kernel requires a language-qualified Bifrost policy at
`adapters/bifrost/policies/core-<language>-kernel.rqlp`, following the
existing JavaScript and Python pattern.

**CodeQL CLI 2.26.3** — the pinned version — has production extractors and
packs covering C and C++ (`cpp`), C# (`csharp`), Go (`go`), Kotlin through the
`java` extractor, TypeScript through the `javascript` extractor, and Ruby
(`ruby`). Rust support exists only as a public preview: if it is used, the
preview status must be pinned and labeled as such in the report. PHP and Scala
have no CodeQL support at all.

Each CodeQL-covered language follows the dedicated-pack pattern already used
for Java, JavaScript, and Python: `adapters/codeql/<language>/` with its own
`qlpack.yml` and kernel query, and one cold database per case.

PHP and Scala therefore have single-analyzer (Bifrost) coverage until the
Joern adapter (#14) lands. Their kernel issues record Joern as the
second-analyzer path, and must not block fixture authoring on it. The absence
of a second analyzer is recorded as coverage, not as negative results.

**Update (#50, #40).** The Joern adapter has since landed, and PHP's second
analyzer is live: `php2cpg` decides all 32 PHP core assertions, so PHP now has
two-analyzer coverage without any CodeQL involvement. Scala remains
single-analyzer — the pinned Joern distribution ships no Scala *source*
frontend, only bytecode-consuming `jimple2cpg`. See
[the PHP kernel contract](php-kernel.md) and
[the Joern adapter](../adapters/joern/README.md).

**Update (Joern `4.0.610`).** Re-pinning Joern to `4.0.610` adds `rust2cpg`,
which did not exist in `4.0.432`. Rust therefore moves from "explicitly
unsupported by Joern" to a third analyzer beside Bifrost and the
public-preview CodeQL pack, over its own 15-template core denominator; the
`Result`/`?` `language-extension` pair stays outside that selection. Scala is
now the only benchmark language Joern records as explicitly unsupported.

## Tranche plan

- **Tranche 1 — near-parity, two decisive analyzers:** TypeScript, Kotlin, C#.
- **Tranche 2 — adapted heap and control constructs:** Go; C and C++ as one
  language-family child issue (shared CodeQL `cpp` extractor and shared
  struct-based heap adaptations, but two separate core populations and
  denominators — 15/30 for C and 16/32 for C++, never merged); and Rust, with
  its CodeQL preview caveat and 15-template core.
- **Tranche 3 — analyzer-coverage-gated:** Ruby (Bifrost inconclusive gate),
  PHP (no CodeQL; Joern path), Scala (no CodeQL; Joern path).

Each tranche produces one bounded child issue per language, with C and C++ as
the single justified family issue. Fixture implementation for a language must
not begin before its child issue records the adapter and analyzer coverage
stated above.

## Companion matrix: the challenge tier

This matrix fixes the sixteen-template core. A second, preregistered population
of thirteen harder templates — dynamic dispatch and reflection, higher-order
flow, containers and deep access paths, and context/depth stress — is classified
with the same `direct`/`adapted`/`n/a` discipline in the
[challenge-tier document](challenge-tier.md), across all thirteen kernel
languages including Java, JavaScript, and Python. Those templates are also
`core`, so the denominators recorded above are superseded from v0.4.0 onward by
the expanded ones stated there (24 for C, 27 for Rust, 28 for C++, 29 for the
other ten); the two populations are never compared number-to-number, and the
frozen v0.3.0 evidence built on the sixteen-template denominators stays valid.

## Invariants

These restate the [scoring contract](scoring.md) and hold for every language
in this matrix.

- There is no combined leaderboard across languages.
- Benchmark-controlled and tool-native model profiles are never pooled.
- `inconclusive`, `unsupported`, and `runner-error` are capability or
  execution coverage and are never clean negatives.
- `language-extension` and `calibration` cases have their own scorecards and
  never change a core denominator.
- Published numbers come only from validated freeze manifests.
