# Issue 305: constant-string selector

This change adds one analyzer-neutral taint template for a switch-like
selection whose selector is computed from a literal string. It is primarily a
benchmark idiom motivated by the OWASP BenchmarkJava pattern. It probes
constant evaluation of indexing and standard-library string access together
with local path selection; it does not test heap precision.

## Stable identities

- Template: **dfb-template-constant-string-selector**
- Case directories in every applicable language:
  **constant-string-selector-positive** and
  **constant-string-selector-negative**
- Case IDs:
  **dfb-taint-<language>-constant-string-selector-positive** and
  **dfb-taint-<language>-constant-string-selector-negative**
- Model profile: **benchmark-controlled**
- Score tier: **core**
- Track: **taint**
- Semantic dimensions: **local-flow** and **path-sensitivity**
- Negative mechanism: **infeasible-path**
- Analysis capability: **constant-selector-intraprocedural-taint**

The positive and negative use the same ASCII literal, selector labels, source,
sink, and single template identity. The positive indexes character C (index
2) and routes the source arm to the sink. The negative indexes character B
(index 1), routes the safe arm to the sink, and retains the C source arm in
the fixture. The negative therefore cannot pass because the source was
omitted: changing the source value at runtime changes the positive sink value
and leaves the negative sink value unchanged.

The selected indices are in range. ASCII keeps the intended C/B selection
consistent even though languages expose different string units (bytes, UTF-16
code units, Unicode scalar values, or grapheme-cluster Characters). The
negative is safe because the selector expression is a literal and the
selected B arm never evaluates or assigns the C source arm. No mutable
selector, external model, heap object, or analyzer-specific behavior is
needed.

## Language surfaces and constraints

All fourteen target languages have a natural equivalent, so none is marked
inapplicable. Surface variants are included within the one balanced pair
instead of becoming separate templates.

| Language | Positive selector and branch | Negative selector and branch | Constraints |
| --- | --- | --- | --- |
| C | Literal indexing and switch | Literal indexing and switch | C11 fixture; indexing is built-in array access, not a library call |
| C++ | std::string::at and switch | std::string operator[] and switch | C++11 |
| C# | String index with switch statement | String index with switch expression | C# 8 for switch expressions; runtime harness targets .NET 8 |
| Go | String byte index and switch | []rune literal index and switch | Go 1.0+; ASCII literal makes byte and rune selections agree |
| Java | String.charAt and switch | String.charAt and switch | Java 8 syntax; this uses the OWASP-style selector |
| JavaScript | String.charAt and switch | String bracket index and switch | ECMAScript 2015 syntax |
| TypeScript | String bracket index and switch | String.charAt and switch | Type annotations are erasable; strict tsc validation targets ES2019 |
| Kotlin | String bracket indexing and when | String bracket indexing and when | Kotlin/JVM 1.0+; JDK needed to run compiled fixtures |
| Scala | String.charAt and match | String apply indexing and match | Scala 2.12+ and Scala 3 share this syntax |
| Swift | String.Index indexed Character and switch | String.Index indexed Character and switch | Swift 4+; integer offsets are converted through String.index(_:offsetBy:), since String is not subscripted by Int. Fixtures retain the DataFlowBenchTaintSwift integer source/sink endpoints, with markers on their calls in main.swift |
| Rust | str.chars().nth and match | byte-string indexing and match | Rust 1.0 syntax; the harness uses Cargo edition 2021. The literal is ASCII and nth is checked as present before matching |
| Python | String indexing and if/elif chain | String indexing and if/elif chain | Python 3.0+; this chain works on Python 3.9, while match syntax requires 3.10+ |
| Ruby | String integer indexing and case | String integer indexing and case | Ruby 1.9+; uses the one-character String result for this ASCII literal |
| PHP | String byte offset and switch | String byte offset and match | PHP 8.0+ is needed for the negative match expression; ASCII avoids byte/character ambiguity |

The environment used for authoring has Python 3.9.6, so the Python pair uses
the explicitly allowed if/elif form rather than Python 3.10 match syntax.
The TypeScript fixtures use erasable annotations and receive strict type
checking with tsc; runtime checks execute the compiled JavaScript. The
current tsc installation is available through the workspace documentation
dependencies and should be added to PATH when running the validator.

## Validation

Install the Python jsonschema package and put the available tsc executable on
PATH when checking TypeScript. Run scripts/validate-precision-issue-305.py for
metadata, schema, marker, and runtime source-dependence checks. Pass --metadata-only to run portable
structural checks without language runtimes, or repeat --language with one or
more keys to select a subset. Full-runtime mode requires every selected
language toolchain; missing tools are listed and cause a nonzero result rather
than being counted as a pass.

Each runtime check substitutes a second value in the source definition of a
temporary copy, then builds and executes it. Swift varies its integer source
return while keeping its required source marker on the endpoint call. A
positive must print the changed source value; a negative must retain its
safe-arm value (the string safe or Swift's integer 0). The fixtures in the
worktree are not modified by validation.
