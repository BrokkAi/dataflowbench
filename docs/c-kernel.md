# C propagation kernel

Issue #37 ports the scored Java propagation templates to C. The C cases keep the
Java `template_id` values, source-to-sink polarity, and negative mechanism; only
the smallest fixture construct changes to C syntax.

C's **classic** core denominator is **15 templates and 30 assertions**, not 16
and 32. (With the challenge tier now rolled out, C's current core denominator is
24 templates and 48 assertions; see [the challenge-tier
expansion](#challenge-tier-expansion) below. The two are separate populations
and are never compared number to number.) The
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
not interchangeable, and the challenge expansion widens the gap rather than
closing it: C's row is rolled out at 24 templates while C++'s is not yet rolled
out at all, so the two kernels currently carry 24- and 16-template denominators
from the same extractor.

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

## Challenge-tier expansion

[The challenge tier](challenge-tier.md) preregistered thirteen further
propagation templates before any fixture existed. **Nine of the thirteen are
applicable to C** — the largest reduction in the preregistration's matrix — so
the C core denominator grows from 15 templates / 30 assertions to **24 templates
/ 48 assertions**. The challenge cases carry `score_tier: "core"` (there is no
separate tier) and their fixture provenance revision is `m3-challenge-c`.

The v0.3.0 fifteen-template core and this expanded core are different
populations and are never compared number to number. A 24-template C score is
also not interchangeable with a 29-template Java score or a 28-template C++ one.

### The four inapplicable cells

Each exclusion is a genuine absence of the construct in C, not a difficulty, and
each reduces only C's own denominator. The rationales are the preregistration's,
restated here so a reader of this contract does not have to hold both documents
open:

| Template ID | Why C has no fixture |
| --- | --- |
| `dfb-template-chal-reflective-invocation` | C has no run-time reflection of any kind: no standard-library facility maps a name to a function at run time. The nearest construct — a name-keyed table of function pointers — **is** `dfb-template-chal-dispatch-table`, and encoding it twice would inflate the denominator without asking a second question. |
| `dfb-template-chal-computed-property` | C has neither computed member access nor a standard-library associative container. Adapting it would mean authoring a string-keyed lookup structure inside the fixture, which makes the fixture's own hand-written code, rather than a language construct, the object of analysis. |
| `dfb-template-chal-closure-capture` | C has no closures and no capture. A function pointer plus a manually passed context struct is not capture — the environment is an ordinary argument, which the classic `dfb-template-argument-position-separation` and relay templates already cover. |
| `dfb-template-chal-anonymous-implementation` | C has no anonymous functions and no anonymous types. |

Neither excluded construct has a C-idiomatic near-relative worth routing to
`language-extension`, so C's two existing extension cases (error-code return
paths, `goto` cleanup) are unchanged by this expansion, and the extension
scorecard stays at two cases.

### Adaptation notes for the nine applicable cells

Four cells are **language-adapted** and five are **direct**. Every fixture keeps
the C kernel's existing endpoint convention — `int dfb_source(void)` and
`void dfb_sink(int value)` — so the challenge fixtures are the same shape of
assertion as the classic thirty and the same adapter selectors reach them
without change.

| Stratum | Template ID | Class | C realization |
| --- | --- | --- | --- |
| A | `dfb-template-chal-dispatch-table` | adapted | An `struct Entry { const char *name; void (*fn)(int); } table[2]` of two function pointers, selected by `strcmp` against a `const char *key` local and fetched into a `void (*selected)(int)` before being invoked. This is the canonical C dispatch-table idiom the preregistration names; the call-graph edge depends on a run-time string comparison, which is the template's question. The negative points `key` at the entry whose function drops its argument and sinks a constant. |
| B | `dfb-template-chal-function-field` | adapted | `struct Holder { void (*fn)(int); }`; `holder.fn = leak` in one function and a separate `dispatch(struct Holder *, int)` that reads `holder->fn` and calls it. C expresses "code stored in the heap" natively, with no wrapper type. The negative hands `dispatch` a **second holder** whose field holds the argument-dropping function. |
| B | `dfb-template-chal-callback-registration` | adapted | `struct Registry { void (*hooks[4])(int); int count; }`, a `register_hook` that appends, and a `fire` driver that iterates `hooks[0..count]` and invokes each with the value. Inversion of control in twenty lines of language, with no framework and no allocation. The negative registers the callback that ignores its parameter. |
| C | `dfb-template-chal-map-iteration` | adapted | C's standard library has no map, so the container is a `struct Record { const char *key; int value; } records[2]` iterated with a `strcmp` match condition in the loop body. **What survives is "retrieved by iterating a container, not by a direct keyed get"; what is lost is "a standard-library map"** — the loop is the fixture's own code rather than a library iteration protocol, and an engine cannot demonstrate a library model here. That loss is the preregistration's own, recorded again here so no reader treats C's result on this cell as evidence about container modeling. The negative iterates a **second, disjoint array** that never received the value. |
| C | `dfb-template-chal-nested-access-path` | direct | `struct Outer { struct Middle middle; }` / `struct Middle { struct Inner inner; }` / `struct Inner { int value; int other; }`, written and read at `outer.middle.inner.value`. The negative reads the sibling `outer.middle.inner.other` at the same depth. |
| C | `dfb-template-chal-element-object` | direct | `struct Item items[2]` with `items[0].value` written from the source; the negative reads `items[1].value`. Element separation and field separation must both hold, which is what distinguishes it from the classic `dfb-template-array-element-separation` pair over a bare `int values[2]`. |
| D | `dfb-template-chal-deep-relay-chain` | direct | `relay1` … `relay6`, one parameter each, no branching and no state, with `relay6` returning the carried value and `run` sinking `relay1(dfb_source())`. The definitions appear callee-first (`relay6` down to `relay1`) because C requires a declaration before use and the kernel's classic relay fixtures already order themselves that way; the *call* order is hop 1 through hop 6, which is what the witness checkpoints name. The negative feeds the identical chain a clean constant while the source call stays live. |
| D | `dfb-template-chal-recursive-carry` | direct | `int carry(int value, int depth)` recursing to `depth == 0` from 5; the negative's base case returns `0` instead of the carried value (`overwrite-kill`). |
| D | `dfb-template-chal-context-pair-depth2` | direct | One `helper` reached through two distinct two-deep paths, `outer_tainted -> wrapper -> helper` and `outer_clean -> wrapper -> helper`, per [Amendment A1](challenge-tier.md#amendments): `helper` returns its argument and `run` sinks the selected result. Both paths are live in both fixtures; only which returned value reaches `dfb_sink` differs. |

Two fixtures include `<string.h>` for `strcmp`; it is part of the C standard
library, so the stdlib-only fairness constraint holds and nothing else is
included anywhere. All eighteen fixtures are single `.c` files with no header,
no build file, and no external dependency, and the whole 48-fixture C
population compiles clean under the host toolchain this kernel records:

```bash
clang -std=c17 -fsyntax-only <fixture>.c
```

### Adapter coverage of the expanded population

One adapter was run over the whole 48-assertion population for this expansion.
Two are deferred by the freeze rule, and one does not cover C at all. The three
reasons are different and the difference matters:

| Adapter | Expanded run | Report |
| --- | --- | --- |
| Semgrep CE 1.174.0 | Yes | `reports/semgrep-c-kernel.json` |
| Bifrost v0.10.5 | **Deferred (freeze-bound)** | `reports/bifrost-c-kernel.json` |
| CodeQL 2.26.4 | **Deferred (freeze-bound)** | `reports/codeql-c-kernel.json` |
| Joern 4.0.617 | **No C slice exists** | — |
| Infer v1.3.0 | **Ran, whole population** — new adapter (#82), landed after the wave, post-freeze | `reports/infer-c-kernel.json` |

**Infer arrived after this wave and is C's second engine.** The Infer adapter
(#82) runs the pinned v1.3.0 release's Pulse taint analysis over the whole
expanded 48-assertion core — the first benchmark-controlled interprocedural
engine evidence on C, whose only prior engine scored its documented
intraprocedural partition. Its report is post-freeze and binds nothing. 48
results: 21 `reached`, 27 `not-reached`, zero `inconclusive`, `unsupported`,
or `runner-error`; **43/48 match expected polarity**. The four false
negatives fall in three shapes: taint dropped through arithmetic expressions
(`expression-positive`'s `(value * 3) + 7`, `loop-carried-positive`'s
`value + iteration`), a recursive carry not followed to its base case
(`recursive-carry-positive`), and a callback registered into a
function-pointer array and fired later (`callback-registration-positive`);
the one false positive, `dispatch-table-negative`, walks the wrong
function-pointer table entry — the same keyed-indirection
over-approximation family the OpenTaint Kotlin kernel measures. See
[the Infer adapter notes](../adapters/infer/README.md).

**Both Bifrost and CodeQL are deferred, and both for the same reason.**
`reports/bifrost-c-kernel.json` and `reports/codeql-c-kernel.json` are two of
the nineteen reports `reports/freeze.json` digest-binds for v0.3.0, so this
change must not overwrite either: **expanded Bifrost and CodeQL evidence for C
is pending the v0.4.0 freeze-prep re-run**, on the repository's established
re-run-at-freeze pattern. The retained reports in [observed
results](#observed-results) below remain the valid 30-assertion classic
snapshots, and they describe a *different population* from the expanded one.
Deferral is not absence of coverage: both engines cover C, both will attempt all
48 assertions at v0.4.0, and this wave simply had no freeze-legal file to write
them to.

**Joern has no C slice, and this wave did not invent one.** The pinned
`joern-v4.0.617` adapter covers Java, JavaScript, Python, Ruby, PHP, and Rust.
`c2cpg` ships with it and `adapters/joern/README.md` already records C as
"Available, not yet in scope", but this repository has no
`run-joern-c-kernel` command, no C selection, and no
`reports/joern-c-kernel.json`; standing up a language slice is its own change,
not a side effect of landing fixtures. C therefore has no Joern evidence at any
denominator, classic or expanded.

### Semgrep CE 1.174.0 — expanded core

`reports/semgrep-c-kernel.json`. The whole 48-case core population is selected
and balance-checked, and the bounded CE profile then decides what is scored,
from case metadata, before Semgrep is invoked. (The C Semgrep slice is the core
population only; the two `language-extension` cases are not part of it, exactly
as before.)

| Stratum | Assertions | Scored | `unsupported` | Polarity match (scored) |
| --- | --- | --- | --- | --- |
| Classic (15 templates) | 30 | 14 | 16 | 12/14 |
| Challenge (9 templates) | 18 | 0 | 18 | n/a |

Whole-population outcome distribution: 9 `reached`, 5 `not-reached`, 34
`unsupported`, zero `inconclusive`, zero `runner-error`.

**All eighteen challenge assertions take the preregistered `unsupported`
partition**, exactly as [the challenge tier](challenge-tier.md) predicted: no
challenge template carries the `intraprocedural` feature tag, so none is inside
the documented CE local-taint profile, and each retains its own
`*-unsupported.json` capability-decision document naming the declared capability
and the boundary it falls outside, citing the preregistered per-template
rationale rather than the generic tag rule. The scored subset therefore stays at
**14 assertions and 12/14**, unchanged from the classic run — the two mismatches
are still the `infeasible-branch` and `loop-carried` negatives, the path
sensitivity the pinned CLI sells as Pro. Comparing the retained report before
and after this expansion, **not one of the 30 classic outcomes moved**. The
partition was not adjusted for this expansion, and eighteen declined assertions
are coverage, never eighteen false negatives.

The expanded report carries fixture revision
`sha256:75f631ca05df2609055972622faaf3946331f7537140b08ba7ec6648bd0e077c`,
configuration hash
`865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100` — unchanged,
because no rule file was touched — and tool build identity
`semgrep-oss:1.174.0`. Reports at different fixture revisions are not pooled.

### What this wave does and does not establish

Stated plainly, because the deferral makes it easy to overclaim: this wave
establishes that the nine applicable C challenge fixtures exist, compile, and
are selected and balance-checked by the population machinery, and it establishes
one adapter's expanded-population behavior — Semgrep CE's, which is a declared
capability boundary rather than an analysis result. It establishes **nothing**
about how well any engine follows C taint through function-pointer dispatch,
heap-stored callees, inverted control, container iteration, deep field chains,
or call depth. That evidence arrives with the v0.4.0 re-run of the two deferred
adapters, and until then C's challenge strata have no analysis outcomes at all.

## Language-extension cases

The nearest C-idiomatic transfer constructs are routed to `language-extension`
cases rather than dropped. They have their own scorecard, are authored as
positives, and **never enter the core denominator** — the C core stays 24
templates and 48 assertions (15 and 30 before the challenge expansion) with or
without them. The generated result
artifacts partition every population by language *and* score tier, so an
extension outcome can never be counted as a core assertion.

| Case | Template ID | Construct |
| --- | --- | --- |
| `dfb-taint-c-error-code-return-positive` | `dfb-template-c-error-code-return-path` | Error-code return-path propagation: `read_reading` writes the controlled value through a `struct Reading *` out-parameter and returns a non-zero error code; the caller reads the value on the error path. |
| `dfb-taint-c-goto-cleanup-positive` | `dfb-template-c-goto-cleanup-carry` | A `goto cleanup` handler carries the value through a `struct Holder` to the sink in the cleanup block. |

Both cases run inside the C slice of both adapters, and both carry the same
`m2-c-kernel` provenance revision as the core fixtures.

## Case population and the frozen direct pair

The C population is the 48 `taint`/`core` cases plus the 2
`taint`/`language-extension` cases under `cases/taint/c/`. Twenty-eight classic
core cases and both extension cases were authored for this kernel with
`fixture_provenance.revision` `m2-c-kernel`; the eighteen challenge cases carry
`m3-challenge-c`. The direct-propagation pair
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

The command selects the C core assertions and the 2 language-extension cases,
and refuses to run if the core count is not exactly the denominator C's
`CHALLENGE_ROLLOUT` row states — 30 before the challenge expansion, **48**
now that C's row is rolled out. It materializes one
isolated workspace per case outside the repository, writes the normalized report
to `reports/bifrost-c-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-c-kernel/`. A report with incomplete runs is
normalized as `inconclusive`, never as a negative.

**This command was not run for the challenge expansion.**
`reports/bifrost-c-kernel.json` is freeze-bound by v0.3.0 and the expanded run
is deferred to the v0.4.0 freeze-prep re-run; see [adapter coverage of the
expanded population](#adapter-coverage-of-the-expanded-population).

## CodeQL selection and reproduction

The CodeQL C vertical slice is those same cases — the C core plus the 2
language-extension cases, so 32 before the challenge expansion and **50** now.
Every selected case is analyzed with the dedicated query:

```text
adapters/codeql/cpp/queries/CKernel.ql
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

**This command was not run for the challenge expansion either.**
`reports/codeql-c-kernel.json` is likewise freeze-bound by v0.3.0, so the
expanded CodeQL evidence for C is pending the v0.4.0 freeze-prep re-run.

For each case the runner creates one cold `cpp` database from the declared
fixture file only, runs the dedicated query, and removes the temporary workspace
and database after retaining the evidence. Databases are created with
`--build-mode=none`, which CodeQL 2.26.4 supports for C and C++: the buildless
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

Both retained snapshots cover the **classic 30** C core assertions and both
language-extension cases. They predate the challenge expansion, are freeze-bound
by v0.3.0, and were deliberately not overwritten by it: everything in this
section describes the 15-template population, never the 24-template one. The two
tiers are scored separately, and neither report is pooled with the C++ kernel or
any other language. The one expanded-population run this wave produced —
Semgrep CE — is reported in [the challenge-tier
expansion](#semgrep-ce-11740--expanded-core) above.

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
slice. Because C's core denominator is 24 templates — 15 classic plus 9
challenge — a C macro-average is never combined with a 28-template C++ score, a
29-template Java score, or C's own 15-template v0.3.0 score without stating both
populations. The two
language-extension cases have their own scorecard and never change the core
denominator, and the Java calibration cases have no C member.
