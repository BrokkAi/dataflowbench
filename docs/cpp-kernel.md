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

Since the challenge-tier expansion below, the C++ core denominator is **28
templates and 56 assertions**. The paragraph above describes the classic
sixteen-template kernel, which remains exactly as published; the expanded
denominator is a different population and the two are never compared
number-to-number.

All C++ fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
function names. Fixtures are single `.cpp` files with no header, no build file,
and no external dependency; each compiles standalone under `clang++ -std=c++17`.
Adapters may lower those endpoints through their own models, but the case
metadata stays analyzer-neutral and reports retain only observed evidence.

## Case population and the frozen direct pair

The C++ population is the 56 `taint`/`core` cases under `cases/taint/cpp/`.
Thirty of them were authored for this kernel with
`fixture_provenance.revision` `m2-cpp-kernel`, and 24 for the challenge-tier
expansion with revision `m3-challenge-cpp`. The direct-propagation pair
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

The command selects only the C++ core assertions — 56 since the challenge row
flipped — materializes one isolated
workspace per case outside the repository, writes the normalized report to
`reports/bifrost-cpp-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-cpp-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

## CodeQL selection and reproduction

The CodeQL C++ vertical slice is exactly that population — 56 cases since the
challenge expansion, though the retained report predates it. Every selected
case is analyzed with the dedicated query:

```text
adapters/codeql/cpp/queries/CppKernel.ql
```

The query is owned by the shared C-family pack manifest at
`adapters/codeql/cpp/qlpack.yml`, pinned to `codeql/cpp-all@12.0.2` — the
version `codeql pack install` resolves for CodeQL CLI 2.26.4 — with the full
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
`--build-mode=none`, which CodeQL 2.26.4 supports for C and C++: the buildless
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

Both retained snapshots cover the classic 32 C++ core assertions — they were
taken before the challenge expansion and are freeze-bound, so neither was
re-run by the challenge wave (see [the challenge-tier
expansion](#challenge-tier-expansion) below). They are separate
populations and are not pooled with each other, with the C kernel, or with any
other language, and neither is compared with an expanded-core number.

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

## Challenge-tier expansion

Twelve of the thirteen templates of [the challenge-tier
preregistration](challenge-tier.md) have landed for C++. The preregistration's
C++ row classifies `dfb-template-chal-reflective-invocation` **inapplicable**,
so the expansion adds 12 templates / 24 assertions and the C++ core denominator
becomes **28 templates / 56 assertions**, exactly as the preregistration's
expanded-denominator table fixes it. The new cases live under
`cases/taint/cpp/<template>-{positive,negative}/` with ids
`dfb-taint-cpp-<template>-<polarity>`, `score_tier` `core`, and
`fixture_provenance.revision` `m3-challenge-cpp`.

Every fixture is a single self-contained `.cpp` file using only the C++
standard library (`<string>`, `<map>`, `<vector>`, `<functional>`). No header,
no build file, no third-party dependency — the same shape the classic kernel
ships. All 24 compile clean under the kernel's documented host check,
`clang++ -std=c++17` (Apple clang 21.0.0), which is an authoring check only:
the CodeQL C++ runner still creates databases with `--build-mode=none`, so no
build step is part of any measurement.

### The excluded cell, stated as an exclusion

`dfb-template-chal-reflective-invocation` has **no C++ fixture and is not in
the C++ denominator**. Standard C++ has no run-time reflection: no
standard-library facility resolves a member function from a string at run
time. The nearest construct — a `std::map<std::string, ...>` of callable
values — *is* `dfb-template-chal-dispatch-table`, and encoding the same fixture
under a second `template_id` would inflate the denominator without asking a
second question. Compile-time reflection (P2996) is not in the pinned language
standard and is not used. This exclusion reduces only C++'s denominator and no
other language's, and it is the reason C++'s expanded core is 28 templates
where Java's, JavaScript's, Python's, TypeScript's, and C#'s are 29.

### Adaptations, per the preregistration's C++ row

Ten cells are **directly applicable**. The two `language-adapted` cells are the
ones the preregistration names for C++, and both are implemented exactly as it
prescribes:

| Template | Classification | C++ construction |
| --- | --- | --- |
| `dfb-template-chal-computed-property` | **adapted** | C++ has no member access by run-time name, so the computed key indexes a `std::map<std::string, std::string>` through a non-constant local key variable: `holder[key] = dfb_source(); dfb_sink(holder[key]);`. The negative writes and reads two **provably distinct constant keys** (`"payload"` / `"other"`). **The member-access flavor of the template is lost; the computed-key flavor is preserved.** That loss is recorded here, as the preregistration requires, and it is why the case carries `computed-access` without `reflective-dispatch` — the C++ adaptation is not reflective, unlike Java's and C#'s. |
| `dfb-template-chal-dispatch-table` | direct | `std::map<std::string, std::function<void(const std::string &)>>` populated with two free functions, `leak` and `drop`; a non-constant `key` selects one and the selected function value is invoked with the tainted value. The negative selects `drop`, which ignores its argument and sinks a clean constant. |
| `dfb-template-chal-closure-capture` | direct | A lambda captures an enclosing local by copy and is returned as a `std::function<void()>`, invoked by the caller after the capturing frame has returned. The negative captures the clean local instead; the tainted local is still assigned from `dfb_source()` in both. |
| `dfb-template-chal-function-field` | direct | A `Holder` struct with a `std::function<void(const std::string &)> fn` member; two instances, one assigned a sinking lambda and one an argument-dropping lambda, with a separate `invoke` function reading the member and calling it. The negative passes the second holder (`object-separation`). |
| `dfb-template-chal-callback-registration` | direct | A `Registry` struct holding `std::vector<std::function<void(const std::string &)>>`; `register_hook` appends and a separate `fire` iterates the registrations and invokes each with the tainted value. Zero frameworks, twenty lines of standard library. |
| `dfb-template-chal-anonymous-implementation` | **adapted** | C++ has no anonymous classes, but a lambda's **closure type is unnamed**, so the fixture invokes a **capture-less** lambda through a declared `std::function<void(const std::string &)>` variable. That preserves "flow through the method of an unnamed implementation, invoked via its declared type"; capture-less is what keeps it distinct from `closure-capture`. Both the sinking and the argument-dropping implementation are constructed in both polarities, and the negative invokes the dropping one. |
| `dfb-template-chal-map-iteration` | direct | `std::map<std::string, std::string>` retrieved by a range-`for` over the map's entries, never by a keyed `at`/`find`. The negative iterates a second, disjoint map that never received the tainted value. |
| `dfb-template-chal-nested-access-path` | direct | Three nested structs give `a.b.c.value`; the negative reads the sibling `a.b.c.other` at the same depth. |
| `dfb-template-chal-element-object` | direct | `std::vector<Item>` of two objects with distinct constant indices; `field-separation`, following the precedent the classic `dfb-template-array-element-separation` pair sets in all thirteen languages. C++'s adaptation separates by index, not by object identity, so the cell keeps `field-separation` rather than `object-separation`. |
| `dfb-template-chal-deep-relay-chain` | direct | Six free functions `relay1`…`relay6`, no branching and no state, with the sink applied to `relay1`'s returned result. The negative feeds the identical chain a clean constant while the `dfb_source()` call stays live. |
| `dfb-template-chal-recursive-carry` | direct | `std::string carry(const std::string &value, int depth)` recursing to a base case at `depth == 0`, invoked with `5`. The negative overwrites the carried value with a clean constant at the base case (`overwrite-kill`). |
| `dfb-template-chal-context-pair-depth2` | direct | The canonical [Amendment A1](challenge-tier.md#amendments) construction: `helper` returns its argument, `wrapper` calls it, and `outer_tainted` / `outer_clean` are the two distinct two-deep contexts. Both calls stay live in both fixtures; the positive sinks the tainted context's result, the negative the clean one's. |

No template proved unimplementable and no amendment is proposed by this wave.

### Adapter coverage over the expanded population

| Adapter | This wave | Report |
| --- | --- | --- |
| Semgrep CE 1.174.0 | **Ran, whole population** | `reports/semgrep-cpp-kernel.json` |
| Bifrost v0.10.5 | **Deferred (freeze-bound)** | `reports/bifrost-cpp-kernel.json` |
| CodeQL 2.26.4 | **Deferred (freeze-bound)** | `reports/codeql-cpp-kernel.json` |
| Joern 4.0.614 | **No C++ slice exists** | — |
| Infer v1.3.0 | **Ran, whole population** — new adapter (#82), landed after the wave, post-freeze | `reports/infer-cpp-kernel.json` |

**Infer arrived after this wave and is C++'s second engine.** The Infer
adapter (#82) runs the pinned v1.3.0 release's Pulse taint analysis over the
whole expanded 56-assertion core — the first benchmark-controlled
interprocedural engine evidence on C++. Its report is post-freeze and binds
nothing. 56 results: 19 `reached`, 37 `not-reached`, zero `inconclusive`,
`unsupported`, or `runner-error`; **47/56 match expected polarity**, with all
nine mismatches false negatives and **zero false positives** — every
negative is clean, including the two path-sensitivity negatives Semgrep CE's
engine trips on. Five of the nine misses share one property: the flow
crosses standard-library machinery — `std::function` values
(`closure-capture`, `callback-registration`, `dispatch-table`), `std::map`
entries (`map-iteration`, `computed-property`) — which the unmodeled Pulse
engine does not follow. The other four repeat the C kernel's measured
families (arithmetic-expression drops in `expression` and `loop-carried`,
the unfollowed `recursive-carry`) plus the C++-only `exception-catch`
positive, whose value travels through a thrown exception. The contrast with
C — where the raw function-pointer `dispatch-table` flow *is* followed, and
over-approximated in the negative — localizes the C++ indirection misses to
the library types rather than to indirection as such. See
[the Infer adapter notes](../adapters/infer/README.md).

**Bifrost and CodeQL are both deferred, and both for the same reason.**
`reports/bifrost-cpp-kernel.json` and `reports/codeql-cpp-kernel.json` are two
of the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so this
change must not overwrite either: **expanded Bifrost and CodeQL evidence for
C++ is pending the v0.4.0 freeze-prep re-run**, on the repository's established
re-run-at-freeze pattern. The retained reports above remain the valid
32-assertion classic snapshots and describe a *different population* from the
expanded one. Deferral is not absence of coverage: both engines cover C++, both
selectors already expect the full 56, and this wave simply had no freeze-legal
file to write the expanded results to.

**Joern has no C++ slice, and this wave did not invent one.** The pinned
`joern-v4.0.614` distribution ships `c2cpg`, which handles C++ upstream, but
this repository has no `JoernKernel` variant for C++, no C++ Joern query, and
no `reports/joern-cpp-kernel.json`; `adapters/joern/README.md` records C++ as
"Available, not yet in scope". Standing up a language slice is its own change
with its own reproduction contract, not a side effect of landing fixtures. C++
therefore has no Joern evidence at any denominator, classic or expanded.

### Semgrep CE 1.174.0 — expanded core

`reports/semgrep-cpp-kernel.json`. The whole 56-case population is selected and
balance-checked, and the bounded CE profile then decides what is scored, from
case metadata, before Semgrep is invoked.

| Stratum | Assertions | Scored | `unsupported` | Polarity match (scored) |
| --- | --- | --- | --- | --- |
| Classic (16 templates) | 32 | 14 | 18 | 12/14 |
| Challenge (12 templates) | 24 | 0 | 24 | n/a |

Whole-population outcome distribution: 9 `reached`, 5 `not-reached`, 42
`unsupported`, zero `inconclusive`, zero `runner-error`.

**All twenty-four challenge assertions take the preregistered `unsupported`
partition**, exactly as [the challenge tier](challenge-tier.md) predicted: no
challenge template carries the `intraprocedural` feature tag, so none is inside
the documented CE local-taint profile, and each retains its own
`*-unsupported.json` capability-decision document naming the declared
capability and the boundary it falls outside, citing the preregistered
per-template rationale rather than the generic tag rule. The scored subset
therefore stays at **14 assertions and 12/14**, unchanged from the classic run
— the two mismatches are still the `infeasible-branch` and `loop-carried`
negatives, the path sensitivity the pinned CLI sells as Pro. Comparing the
retained report before and after this expansion, **not one of the 32 classic
outcomes moved**. The partition was not adjusted for this expansion, and
twenty-four declined assertions are coverage, never twenty-four false
negatives.

The expanded report carries fixture revision
`sha256:a1570fc74526f0088488e3fba0941a7da47244635d7ceecf6787f1f76200b4ee`,
configuration hash
`865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100`, tool build
identity `semgrep-oss:1.174.0`. C++'s front end is recorded `alpha` in the
pinned distribution and that label is retained on every assertion. Reports at
different fixture revisions are not pooled.

### What this wave establishes, and what it does not

Read plainly: the C++ challenge strata have **no analysis outcomes**. The only
adapter that ran over the expanded population declined every challenge
assertion by declared capability, which is a statement about Semgrep CE's
documented boundary and not a measurement of C++ data-flow difficulty. Nothing
here establishes how well any engine follows C++ taint through dispatch tables,
lambdas, containers, or depth. That evidence arrives with the v0.4.0 re-run of
the two deferred adapters.

The C++ challenge cases are excluded from the Bifrost smoke population by
template identity, so the frozen 118-case smoke slice is untouched.

## Population boundaries

C++ results are their own population. They are never pooled with the C kernel
(whose denominator is 15 classic templates), with the Java, Kotlin, C#,
JavaScript, TypeScript, or Python kernels, or with the 13-language direct-flow
breadth slice, and they are never averaged with a language whose core
denominator is not also 28 templates — nor with a C++ score taken over the
classic 16, which is a different population of the same name. The Java
calibration cases
(`dfb-template-one-hop-relay` and `dfb-template-modeled-external-summary`) have
no C++ member and do not change this denominator.
