# C++ propagation kernel

Issue #37 ports the sixteen scored Java propagation templates to C++. The C++
cases keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct changes to C++ syntax. Every
scored C++ template has exactly one `positive` and one `negative` `core` case,
so the C++ core denominator is 16 templates and 32 assertions, exactly as the
[applicability matrix](applicability-matrix.md) fixes it.

C++ and [C](c-kernel.md) are ported together because they share CodeQL's `cpp`
extractor and the same struct-based heap adaptations, but they are **two
populations**: C's denominator is 15 templates and 30 assertions, and the two
are never merged, pooled, or macro-averaged together.

The matrix classifies the local, calls/returns, and control-transfer strata as
directly applicable — including `dfb-template-exception-catch`, which throws a
class instance and catches it by reference with the value carried in a member —
and language-adapts four heap cells. This contract records no deviation from
the matrix.

| Stratum | Template ID | C++ adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct free-function call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | A local `int` is either reassigned from a copy that preserves the value or reassigned to a constant before the sink. |
| Local | `dfb-template-local-multi-step-chain` | Local `int` copies carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | C++ integer arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One `relay` function is called with tainted and clean values; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | `choose_first` returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop function return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two nested function returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Two `Holder` struct objects with the same member name stand in for the distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One `Holder` has separate `tainted` and `clean` members. |
| Heap/separation | `dfb-template-alias-propagation-separation` | A reference alias (`Holder &alias = original`) aliases the same object while a second object stays distinct. |
| Heap/separation | `dfb-template-array-element-separation` | A native `int values[2]` with distinct constant indices stands in for the Java array. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the positive/negative path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A `for` loop either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | A `FlowException` struct carries the value in a member across `throw` / `catch (FlowException &caught)`, matching the Java checked-exception construct. |

All C++ fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
function names. Fixtures are single `.cpp` files with no header, no build file,
and no external dependency; each compiles standalone under `clang++ -std=c++17`.
Adapters may lower those endpoints through their own models, but the case
metadata stays analyzer-neutral and reports retain only observed evidence.

## Case population and the frozen direct pair

The C++ population is the 32 `taint`/`core` cases under `cases/taint/cpp/`.
Thirty of them were authored for this kernel with
`fixture_provenance.revision` `m2-cpp-kernel`. The direct-propagation pair
(`dfb-taint-cpp-direct-positive` and `dfb-taint-cpp-direct-negative`) predates
it: it is the C++ member of the 13-language direct-flow breadth slice, and it is
frozen byte-for-byte in the published v0.2.0 manifest (`reports/freeze.json`).
Its `case.json` therefore keeps `fixture_provenance.revision` `m1a-direct-core`,
keeps the breadth policy reference
`adapters/bifrost/policies/core-direct.rqlp`, and carries no CodeQL model
reference.

Editing those two files would invalidate the published v0.2.0 evidence, so the
runners accommodate them exactly as the Kotlin and C# kernels do: the Bifrost
selector accepts either `core-cpp-kernel.rqlp` or the breadth
`core-direct.rqlp` policy and evaluates each case through the policy it
declares, and the CodeQL selector accepts a C++ core case with no `codeql` model
reference while rejecting one that names a different query. The same case is a
member of two populations, but its results are never pooled: the breadth result
lives in `reports/bifrost-smoke.json` and the kernel result in the dedicated C++
reports below.

## Bifrost selection and reproduction

The Bifrost C++ slice uses the language-qualified policy
`adapters/bifrost/policies/core-cpp-kernel.rqlp`, whose source and sink
selectors are `(language cpp (call :callee (name "dfb_source")))` and
`(language cpp (call :callee (name "dfb_sink")))`, with argument index 0 as the
dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-cpp-kernel --bifrost /path/to/bifrost
```

The command selects only the 32 C++ core assertions, materializes one isolated
workspace per case outside the repository, writes the normalized report to
`reports/bifrost-cpp-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-cpp-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

## CodeQL selection and reproduction

The CodeQL C++ vertical slice is exactly those 32 cases. Every selected case is
analyzed with the dedicated query:

```text
adapters/codeql/cpp/queries/CppKernel.ql
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
2. each query restricts every data-flow node to its own fixture extension
   (`cpp` here, `c` in `CKernel.ql`);
3. the two runs write separate reports and separate raw-evidence roots.

Registry retrieval of the C-family pack succeeded for the pinned CLI, so no
source workspace fallback was needed:

```bash
codeql pack install adapters/codeql/cpp
cargo run -- run-codeql-cpp-kernel --codeql /path/to/codeql
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
The normalized report is `reports/codeql-cpp-kernel.json` and the raw SARIF (or
raw runner diagnostics when CodeQL cannot produce SARIF) is retained per case
under `reports/raw/codeql-cpp-kernel/`.

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
execution health separate from the polarity of the 16 balanced assertions.

## Observed results

Both retained snapshots cover all 32 C++ core assertions. They are separate
populations and are not pooled with each other, with the C kernel, or with any
other language.

### CodeQL, `reports/codeql-cpp-kernel.json`

CodeQL CLI 2.26.3, build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`,
with `codeql/cpp-all@12.0.2` from the committed lock and Apple clang 21.0.0
(`clang-2100.1.1.101`) as the compiler the buildless extractor discovered.
Configuration hash
`8873a63a5898c8b6b10dc24a9fbf2fae3ed5a088faf024524b0bae50f0fc4cc0`.

32 results: 16 `reached` and 16 `not-reached`, with zero `inconclusive`,
`unsupported`, or `runner-error` outcomes. 28 of 32 match the expected polarity.
The four mismatches are:

- false negatives: `dfb-taint-cpp-alias-propagation-positive` and
  `dfb-taint-cpp-exception-catch-positive`;
- false positives: `dfb-taint-cpp-array-element-negative` and
  `dfb-taint-cpp-loop-carried-negative`.

That set is a subset of the five mismatches the Java and C# kernels show on the
same templates with the same CLI: the C++ extractor resolves the
arithmetic-expression positive that those two miss. The alias-propagation and
exception-catch false negatives and the array-element and loop-carried false
positives are the same cells that fail across every ported kernel.

All 32 retained raw outputs are SARIF files under
`reports/raw/codeql-cpp-kernel/`, with zero error files, and normalized
`witness_checkpoints` are empty for every case: the adapter records
anchor-backed flow outcomes and leaves the path evidence in SARIF rather than
fabricating observed witness markers. Per-case wall clock, including cold
database creation, ranged from 6.2 s to 24.8 s (306 s for the population). The
60-second `execution_budget` on the cases describes the analysis budget shared
with the other language kernels; C++ extraction time is reported here rather
than silently rebudgeted.

### Bifrost, `reports/bifrost-cpp-kernel.json`

Bifrost 0.10.5, build identity
`728ac69ab93224151c6c951b23d2f5bc681d8558`. Configuration hash
`b29775f28c44e0830155def3030cb36f7c7f8906c440dc18af2be6f7ddbdc22e`; it covers
both `core-cpp-kernel.rqlp` and the breadth `core-direct.rqlp`, because the
frozen direct pair is evaluated through the policy it declares.

32 results: 1 `reached`, 1 `not-reached`, and 30 `inconclusive`. Only the
direct-propagation pair is decisive, and both of its outcomes match the expected
polarity — 2 of 2 decisive outcomes, 2 of 32 assertions.

The 30 inconclusive results are capability evidence, never negatives. Each
retains `partial_discovery` with a diagnostic of the form "taint discovery is
incomplete: procedure value-flow snapshot for ... is unknown", naming the
fixture's `dfb_source` procedure. This matches the C# kernel's Bifrost profile
on the same build: Bifrost's C++ procedure value-flow coverage, not an artifact
of the language-qualified policy.

## Population boundaries

C++ results are their own population. They are never pooled with the C kernel
(whose denominator is 15 templates), with the Java, Kotlin, C#, JavaScript,
TypeScript, or Python kernels, or with the 13-language direct-flow breadth
slice, and they are never averaged with a language whose core denominator is not
also 16 templates. The Java calibration cases
(`dfb-template-one-hop-relay` and `dfb-template-modeled-external-summary`) have
no C++ member and do not change this denominator.
