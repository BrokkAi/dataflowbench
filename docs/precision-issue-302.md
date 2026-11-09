# Issue #302: folded local constants

## Proposed template inventory

These are prospective `core` templates for the `taint` track and
`benchmark-controlled` model profile. The parent integration must register
these exact IDs and add their case counts to the corresponding language
populations.

| Template ID | Case directory suffix | Languages |
| --- | --- | --- |
| `dfb-template-folded-local-constant-if` | `folded-local-constant-if-{negative,positive}` | c, cpp, csharp, go, java, javascript, typescript, kotlin, scala, swift, rust, python, ruby, php |
| `dfb-template-folded-local-constant-conditional-expression` | `folded-local-constant-conditional-expression-{negative,positive}` | c, cpp, csharp, java, javascript, typescript, kotlin, scala, swift, rust, python, ruby, php |

Each applicable language gets exactly one positive and one negative case for
each template. Case IDs follow
`dfb-taint-<language>-<case-directory-suffix>-<polarity>`. Fixtures are
authored as a single source file in the matching language's
`cases/taint/<language>/` directory.

## Language forms and limits

| Language | `if` pair | Conditional-expression pair | Constant form and qualification |
| --- | --- | --- | --- |
| C | `if` statement | `?:` | Local `const int` values; no macro or preprocessor constant. |
| C++ | `if` statement | `?:` | Uses a local `constexpr int` and local plain `const int` values. |
| C# | `if` statement | `?:` | Uses local `const int` values. C# has no ordinary readonly-local declaration; `ref readonly` is an alias to storage, not a read-only value local, so it is not substituted. |
| Go | `if` statement | Inapplicable | Uses untyped constants in a local `const` block. Go has no conditional/ternary expression, so no expression pair is forced. |
| Java | `if` statement | `?:` | Uses unmodified `int` locals, which are effectively final. |
| JavaScript | `if` statement | `?:` | Uses `const` numeric bindings. |
| TypeScript | `if` statement | `?:` | Uses `const` numeric bindings. |
| Kotlin | `if` used for branch assignment | `if` value expression | Uses a legal top-level `const val` plus local `val` values. Kotlin does not have a ternary operator. |
| Scala | `if` used for branch assignment | `if` value expression | Uses local `val` values. Scala does not have a ternary operator. |
| Swift | `if` statement | `?:` | Uses local `let` values. |
| Rust | `if` used for branch assignment | `if` value expression | Uses a module `const` and local `let` values. Rust does not have a ternary operator. |
| Python | `if` statement | Conditional expression | Uses a module-level uppercase constant and uppercase function-local constants by convention. Python does not enforce immutable bindings. |
| Ruby | `if` statement | `?:` | Uses file-level constants and an unmodified local. Ruby constants can be reassigned (with a warning); locals are reassignable. |
| PHP | `if` statement | `?:` | Uses a file-level `const`, `define`, and an unmodified local. |

Kotlin, Scala, and Rust use their native `if` value expression in the
conditional-expression template. This exercises value selection with a
compile-time-known condition without inventing a ternary operator.

## Semantic proof

Every pair uses the same condition shape:

```text
(7 * 42) - num > 200
```

The negative assigns `num = 86`, so the condition is `208 > 200`, which is
true and selects the clean arm. The positive assigns `num = 100`, so the
condition is `194 > 200`, which is false and selects `dfb_source()`. C, C++,
C#, Go, Java, Kotlin, Scala, Rust, and Swift use integer payloads: the source
returns `1` (Swift returns `7`) and the clean arm is `0`. JavaScript,
TypeScript, Python, Ruby, and PHP use string payloads: the source returns
`"tainted"` and the clean arm is `"safe"`. All predicate operands are small
integers, so overflow and rounding do not affect the result. The source call
is confined to the source-selected arm; each sink prints the selected value.
The dedicated validator compiles or runs each fixture twice, changing only
the source return from `1` to `2` (Swift `7` to `19`, or `"tainted"` to
`"alternate-tainted"`). It requires positive sinks to follow both source
values and negative sinks to stay clean for both. This runtime check is
independent of analyzer output.

The JavaScript and TypeScript constants are primitive numeric bindings, so
`const` prevents rebinding. Kotlin's `const val` is top-level and initialized
with a compile-time constant as required; local values use `val`. Swift uses
`let`; Rust's `const` and `let`, C++'s `constexpr` and `const`, and Go's
constant declarations likewise have the language's immutable/constant
semantics. Java's numeric locals are assigned once and never reassigned.

Python's module and local uppercase names are conventions, not language
guarantees; the fixture contains no rebinding or mutation. Ruby constants and locals are also not language
final: the fixture has no reassignment, `remove_const`, or reflective
mutation. The negative claim is the concrete path behavior of these source
files; an analyzer that cannot establish it must retain its unsupported or
inconclusive outcome rather than treating an empty finding set as proof.

Swift keeps the repository's exact `dfb_source() -> Int` and
`dfb_sink(_ value: Int)` endpoints, with source and sink markers on the call
lines and exact line hints in `case.json`. The other fixture signatures follow
their current infeasible-branch cases. Canonical fixtures use
`DFB-SOURCE`, `DFB-SINK`, and positive-path `DFB-WITNESS` comments. Existing
adapter models are referenced as in the language's current infeasible-branch
cases; this change does not modify those models, prior releases, evidence,
reports, denominators, pins, or adapters.

## Validation

Run the independent validator with all installed language toolchains:

```sh
python3 scripts/validate-precision-issue-302.py
```

Use `--metadata-only` to run schema, pair, ID, and marker checks without
compiling fixtures. `--language <key>` can be repeated to select one or more
languages; a requested missing toolchain is reported as unavailable and makes
full-runtime validation fail.
