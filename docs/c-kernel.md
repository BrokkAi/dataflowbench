# C propagation kernel

Issue #37 ports the scored Java propagation templates to C. The C cases keep the
Java `template_id` values, source-to-sink polarity, and negative mechanism; only
the smallest fixture construct changes to C syntax.

C's core denominator is **15 templates and 30 assertions**, not 16 and 32. The
[applicability matrix](applicability-matrix.md) classifies
`dfb-template-exception-catch` as **inapplicable** to C: C has no unwinding
construct that transfers a typed value to a handler, and `setjmp`/`longjmp`
transfers control with an `int` status payload and undefined-local semantics
that do not preserve the template's value-carrying intent. No adaptation asks
the same source-to-sink question, so the cell is dropped from the C denominator
rather than faked, and it reduces only C's denominator.

C and [C++](cpp-kernel.md) are ported together because they share CodeQL's `cpp`
extractor and the same struct-based heap adaptations, but they are **two
populations** with different denominators, and are never merged, pooled, or
macro-averaged together. A 15-template C score and a 16-template C++ score are
not interchangeable.

| Stratum | Template ID | C adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | A local `int` is either reassigned from a copy that preserves the value or reassigned to a constant before the sink. |
| Local | `dfb-template-local-multi-step-chain` | Local `int` copies carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | C integer arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One `relay` function is called with tainted and clean values; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | `choose_first` returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop function return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two nested function returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Two `struct Holder` objects with the same member name stand in for the distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One `struct Holder` has separate `tainted` and `clean` members. |
| Heap/separation | `dfb-template-alias-propagation-separation` | A pointer alias (`struct Holder *alias = &original`) aliases the same object, read through `alias->value`, while a second object stays distinct. |
| Heap/separation | `dfb-template-array-element-separation` | A native `int values[2]` with distinct constant indices stands in for the Java array. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `1`/`0` conditions make the positive/negative path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A `for` loop either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | **Inapplicable.** Excluded from the C core denominator; see the rationale above and the two language-extension cases below. |

All C fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
function names. Fixtures are single `.c` files with no header, no build file,
and no external dependency; each compiles standalone under `clang -std=c17`.
Adapters may lower those endpoints through their own models, but the case
metadata stays analyzer-neutral and reports retain only observed evidence.

## Language-extension cases

The nearest C-idiomatic transfer constructs are routed to `language-extension`
cases rather than dropped. They have their own scorecard, are authored as
positives, and **never enter the core denominator** — the C core stays 15
templates and 30 assertions with or without them. The generated result
artifacts partition every population by language *and* score tier, so an
extension outcome can never be counted as a core assertion.

| Case | Template ID | Construct |
| --- | --- | --- |
| `dfb-taint-c-error-code-return-positive` | `dfb-template-c-error-code-return-path` | Error-code return-path propagation: `read_reading` writes the controlled value through a `struct Reading *` out-parameter and returns a non-zero error code; the caller reads the value on the error path. |
| `dfb-taint-c-goto-cleanup-positive` | `dfb-template-c-goto-cleanup-carry` | A `goto cleanup` handler carries the value through a `struct Holder` to the sink in the cleanup block. |

Both cases run inside the C slice of both adapters, and both carry the same
`m2-c-kernel` provenance revision as the core fixtures.

## Case population and the frozen direct pair

The C population is the 30 `taint`/`core` cases plus the 2
`taint`/`language-extension` cases under `cases/taint/c/`. Twenty-eight core
cases and both extension cases were authored for this kernel with
`fixture_provenance.revision` `m2-c-kernel`. The direct-propagation pair
(`dfb-taint-c-direct-positive` and `dfb-taint-c-direct-negative`) predates it:
it is the C member of the 13-language direct-flow breadth slice, and it is
frozen byte-for-byte in the published v0.2.0 manifest (`reports/freeze.json`).
Its `case.json` therefore keeps `fixture_provenance.revision` `m1a-direct-core`,
keeps the breadth policy reference
`adapters/bifrost/policies/core-direct.rqlp`, and carries no CodeQL model
reference.

Editing those two files would invalidate the published v0.2.0 evidence, so the
runners accommodate them exactly as the Kotlin and C# kernels do: the Bifrost
selector accepts either `core-c-kernel.rqlp` or the breadth `core-direct.rqlp`
policy and evaluates each case through the policy it declares, and the CodeQL
selector accepts a C case with no `codeql` model reference while rejecting one
that names a different query. The same case is a member of two populations, but
its results are never pooled: the breadth result lives in
`reports/bifrost-smoke.json` and the kernel result in the dedicated C reports
below.

## Bifrost selection and reproduction

The Bifrost C slice uses the language-qualified policy
`adapters/bifrost/policies/core-c-kernel.rqlp`, whose source and sink selectors
are `(language c (call :callee (name "dfb_source")))` and
`(language c (call :callee (name "dfb_sink")))`, with argument index 0 as the
dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-c-kernel --bifrost /path/to/bifrost
```

The command selects the 30 C core assertions and the 2 language-extension
cases, refuses to run if the core count is not exactly 30, materializes one
isolated workspace per case outside the repository, writes the normalized report
to `reports/bifrost-c-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-c-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

## CodeQL selection and reproduction

The CodeQL C vertical slice is those same 32 cases — 30 core plus 2
language-extension. Every selected case is analyzed with the dedicated query:

```text
adapters/codeql/cpp/queries/CKernel.ql
```

The query is owned by the shared C-family pack manifest at
`adapters/codeql/cpp/qlpack.yml`, pinned to `codeql/cpp-all@12.0.2` — the
version `codeql pack install` resolves for CodeQL CLI 2.26.3 — with the full
transitive set committed in `adapters/codeql/cpp/codeql-pack.lock.yml`. One pack
holds both C-family queries because CodeQL extracts C and C++ with one `cpp`
extractor and one standard library; the populations stay disjoint through three
independent guards, exactly as JavaScript and TypeScript do:

1. the runner selects only its own language's cases and refuses a case that
   declares the other kernel's query;
2. each query restricts every data-flow node to its own fixture extension (`c`
   here, `cpp` in `CppKernel.ql`);
3. the two runs write separate reports and separate raw-evidence roots.

Registry retrieval of the C-family pack succeeded for the pinned CLI, so no
source workspace fallback was needed:

```bash
codeql pack install adapters/codeql/cpp
cargo run -- run-codeql-c-kernel --codeql /path/to/codeql
```

If registry retrieval is unavailable, a matching official source workspace or
CLI bundle pack root passed through `--codeql-packs` is a valid reproduction
input, as documented for the [JavaScript kernel](javascript-kernel.md).

For each case the runner creates one cold `cpp` database from the declared
fixture file only, runs the dedicated query, and removes the temporary workspace
and database after retaining the evidence. Databases are created with
`--build-mode=none`, which CodeQL 2.26.3 supports for C and C++: the buildless
extractor indexes the fixture and resolves the translation unit through a
compiler it discovers on the host (Apple clang 21.0.0 for the retained run). No
`--command=` build is traced, and the fixtures need no makefile or project file.
The normalized report is `reports/codeql-c-kernel.json` and the raw SARIF (or
raw runner diagnostics when CodeQL cannot produce SARIF) is retained per case
under `reports/raw/codeql-c-kernel/`.

## Anchor evidence and result semantics

CodeQL query results are evidence, not ground truth by themselves. The runner
reconciles SARIF result locations with the case's `DFB-SINK:` anchor. That
marker identifies the anchored sink function declaration; the C-family dialect
of the shared reconciler reads the declared function name as the identifier
preceding the parameter list, and then accepts a SARIF result that lies in the
same fixture file on a line that calls that function. A line that reaches a
member through `.`, `->`, or `::` is not such a call. The result need not be on
the marker's own line. Query path evidence identifies the `DFB-SOURCE:` to sink
flow, and normalized results retain both anchor sets.

A successful, anchor-backed finding is `reached`; a successful analysis with no
matching finding is `not-reached`. Missing, ambiguous, or unmappable location
evidence is `inconclusive`, an explicitly unsupported capability is
`unsupported`, and a database, query, SARIF, or runner failure is
`runner-error`.

None of `inconclusive`, `unsupported`, or `runner-error` may be normalized to
`not-reached`, and none may be counted as a semantic negative. This keeps
execution health separate from the polarity of the 15 balanced assertions.

## Observed results

Both retained snapshots cover all 30 C core assertions and both
language-extension cases. The two tiers are scored separately, and neither
report is pooled with the C++ kernel or any other language.

### CodeQL, `reports/codeql-c-kernel.json`

CodeQL CLI 2.26.3, build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`,
with `codeql/cpp-all@12.0.2` from the committed lock and Apple clang 21.0.0
(`clang-2100.1.1.101`) as the compiler the buildless extractor discovered.
Configuration hash
`719415b9134dfd43390ffdb76eef45f7ed022f907f22913226c22f93277b62f8`.

32 results, with zero `inconclusive`, `unsupported`, or `runner-error`
outcomes:

- **Core (30 assertions):** 16 `reached` and 14 `not-reached`. 27 of 30 match
  the expected polarity. The three mismatches are one false negative,
  `dfb-taint-c-alias-propagation-positive`, and two false positives,
  `dfb-taint-c-array-element-negative` and `dfb-taint-c-loop-carried-negative`.
- **Language-extension (2 cases, scored separately):** both `reached`, matching
  their positive polarity — CodeQL follows the controlled value through the
  error-code out-parameter and through the `goto cleanup` handler's struct.

The core mismatch set is the C++ set minus exception-catch, which C does not
have: the same alias-propagation false negative and the same array-element and
loop-carried false positives that every ported kernel shows on this CLI. C
resolves the arithmetic-expression positive that the Java and C# kernels miss.

All 32 retained raw outputs are SARIF files under
`reports/raw/codeql-c-kernel/`, with zero error files, and normalized
`witness_checkpoints` are empty for every case: the adapter records
anchor-backed flow outcomes and leaves the path evidence in SARIF rather than
fabricating observed witness markers. Per-case wall clock, including cold
database creation, ranged from 11.1 s to 18.7 s (423 s for the population). The
60-second `execution_budget` on the cases describes the analysis budget shared
with the other language kernels; C extraction time is reported here rather than
silently rebudgeted.

### Bifrost, `reports/bifrost-c-kernel.json`

Bifrost 0.10.5, build identity
`728ac69ab93224151c6c951b23d2f5bc681d8558`. Configuration hash
`345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`; it covers
both `core-c-kernel.rqlp` and the breadth `core-direct.rqlp`, because the frozen
direct pair is evaluated through the policy it declares.

32 results. Of the 30 core assertions, 1 is `reached`, 1 is `not-reached`, and
28 are `inconclusive`; both language-extension cases are `inconclusive`. Only
the direct-propagation pair is decisive, and both of its outcomes match the
expected polarity — 2 of 2 decisive outcomes, 2 of 30 core assertions.

The 30 inconclusive results are capability evidence, never negatives. Each
retains `partial_discovery` with a diagnostic of the form "taint discovery is
incomplete: procedure value-flow snapshot for ... is unknown", naming the
fixture's `dfb_source` procedure. This matches the C++ and C# kernels' Bifrost
profile on the same build: Bifrost's C-family procedure value-flow coverage, not
an artifact of the language-qualified policy.

## Population boundaries

C results are their own population. They are never pooled with the C++ kernel
(whose denominator is 16 templates), with the Java, Kotlin, C#, JavaScript,
TypeScript, or Python kernels, or with the 13-language direct-flow breadth
slice. Because C's core denominator is 15 templates, a C macro-average is never
combined with a 16-template score without stating both populations. The two
language-extension cases have their own scorecard and never change the core
denominator, and the Java calibration cases have no C member.
