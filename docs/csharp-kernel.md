# C# propagation kernel

Issue #35 ports the sixteen scored Java propagation templates to C#. The C#
cases keep the Java `template_id` values, source-to-sink polarity, and negative
mechanism; only the smallest fixture construct changes to C# syntax. Every
scored C# template has exactly one `positive` and one `negative` `core` case,
so the C# core denominator is 16 templates and 32 assertions, exactly as the
[applicability matrix](applicability-matrix.md) fixes it.

The matrix classifies every C# cell as **directly applicable**: classes,
fields, arrays, `try`/`catch` with an exception object carrying a property, and
`for`/`while` loops all match the Java kernel constructs. C# is the closest of
the ten remaining languages to the Java kernel, and this contract records no
deviation from the matrix.

| Stratum | Template ID | C# adaptation |
| --- | --- | --- |
| Local | `dfb-template-direct-propagation` | Direct static method call, unchanged in meaning. |
| Local | `dfb-template-local-overwrite-kill` | A local `int` is either preserved or reassigned to a constant before the sink. |
| Local | `dfb-template-local-multi-step-chain` | Local `int` copies carry the value through the same three-step chain. |
| Local | `dfb-template-arithmetic-expression-propagation` | C# integer arithmetic preserves the expression-flow distinction. |
| Calls/returns | `dfb-template-call-context-separation` | One `Relay` method is called with tainted and clean values; the selected call remains the distinction. |
| Calls/returns | `dfb-template-argument-position-separation` | `ChooseFirst` returns its first parameter, so the second-argument negative remains non-flowing. |
| Calls/returns | `dfb-template-return-relay-one-hop` | A one-hop static method return carries the value to the sink. |
| Calls/returns | `dfb-template-return-relay-two-hop` | Two nested static method returns preserve the two-hop depth. |
| Heap/separation | `dfb-template-object-separation` | Two `Holder` instances with the same field name stand in for the distinct Java objects. |
| Heap/separation | `dfb-template-same-object-field-separation` | One `Holder` has separate `Tainted` and `Clean` fields. |
| Heap/separation | `dfb-template-alias-propagation-separation` | Reference assignment (`Holder alias = original`) creates the alias; a second `new Holder()` stays distinct. |
| Heap/separation | `dfb-template-array-element-separation` | An `int[2]` with distinct constant indices stands in for the Java array. |
| Control transfer | `dfb-template-infeasible-branch` | Literal `true`/`false` conditions make the positive/negative path feasible or unreachable. |
| Control transfer | `dfb-template-branch-join` | The negative overwrites the value on both branches; the positive leaves one path tainted. |
| Control transfer | `dfb-template-loop-carried-kill` | A `for` loop either overwrites the carried value or computes from it. |
| Control transfer | `dfb-template-exception-catch` | A `FlowException : Exception` carries the value in a public field across `throw`/`catch`, matching the Java checked-exception construct. |

Since the challenge-tier expansion below, the C# core denominator is **29
templates and 58 assertions**. The paragraph above describes the classic
sixteen-template kernel, which remains exactly as published; the expanded
denominator is a different population and the two are never compared
number-to-number.

All C# fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
method names. Fixtures are single `.cs` files in file-scoped namespace
`DataFlowBench`, with no project file and no external dependency. Adapters may
lower those endpoints through their own models, but the case metadata stays
analyzer-neutral and reports retain only observed evidence.

## Case population and the frozen direct pair

The C# population is the 58 `taint`/`core` cases under `cases/taint/csharp/`.
Thirty of them were authored for this kernel with
`fixture_provenance.revision` `m2-csharp-kernel`, and 26 for the
challenge-tier expansion with revision `m3-challenge-csharp`. The direct-propagation pair
(`dfb-taint-csharp-direct-positive` and `dfb-taint-csharp-direct-negative`)
predates it: it is the C# member of the 13-language direct-flow breadth slice,
and it is frozen byte-for-byte in the published v0.2.0 manifest
(`reports/freeze.json`). Its `case.json` therefore keeps
`fixture_provenance.revision` `m1a-direct-core`, keeps the breadth policy
reference `adapters/bifrost/policies/core-direct.rqlp`, and carries no CodeQL
model reference.

Editing those two files would invalidate the published v0.2.0 evidence, so the
runners accommodate them instead:

- the Bifrost C# selector accepts either `core-csharp-kernel.rqlp` or the
  breadth `core-direct.rqlp` policy for a C# core case, and evaluates each case
  through the policy it declares;
- the CodeQL C# selector defaults a C# core case with no `codeql` model
  reference to this kernel's query, and rejects any C# core case that names a
  different query.

The same case is a member of two populations, but its results are never pooled:
the breadth result lives in `reports/bifrost-smoke.json` and the kernel result
in the dedicated C# reports below.

## Bifrost selection and reproduction

The Bifrost C# slice uses the language-qualified policy
`adapters/bifrost/policies/core-csharp-kernel.rqlp`, whose source and sink
selectors are `(language csharp (call :callee (name "dfb_source")))` and
`(language csharp (call :callee (name "dfb_sink")))`, with argument index 0 as
the dangerous operand. Run it from the repository root:

```bash
cargo run -- run-bifrost-csharp-kernel --bifrost /path/to/bifrost
```

The command selects only the C# core assertions — 58 since the challenge row
flipped — materializes one isolated
workspace per case outside the repository, writes the normalized report to
`reports/bifrost-csharp-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-csharp-kernel/`. A report with incomplete runs
is normalized as `inconclusive`, never as a negative.

## CodeQL selection and reproduction

The CodeQL C# vertical slice is exactly that population — 58 cases since the
challenge expansion, though the retained report predates it. Every selected case is
analyzed with the dedicated query:

```text
adapters/codeql/csharp/queries/CSharpKernel.ql
```

The query is owned by the dedicated C# pack manifest at
`adapters/codeql/csharp/qlpack.yml`; the Java, JavaScript, and Python packs are
separate. The runner must not select any other language, calibration cases, or
the direct-flow breadth population.

Registry retrieval of the C# pack succeeded for the pinned CLI, so no source
workspace fallback was needed:

```bash
codeql pack install adapters/codeql/csharp
cargo run -- run-codeql-csharp-kernel --codeql /path/to/codeql
```

`codeql pack install` resolved `codeql/csharp-all@7.1.2` for CodeQL CLI 2.26.4
(build SHA `6b1e4dee94adb20f90a671f3fc9e04be32eecf65`); the complete transitive
set is committed in `adapters/codeql/csharp/codeql-pack.lock.yml`. If registry
retrieval is unavailable, a matching official source workspace or CLI bundle
pack root passed through `--codeql-packs` is a valid reproduction input, as
documented for the [JavaScript kernel](javascript-kernel.md).

For each case the runner creates one cold C# database from the declared fixture
file only, runs the dedicated query, and removes the temporary workspace and
database after retaining the evidence. Databases are created with
`--build-mode=none`, which the C# extractor supports, so the fixtures need no
`.csproj` scaffolding, no restore, and no compiler invocation. The normalized
report is `reports/codeql-csharp-kernel.json` and the raw SARIF (or raw runner
diagnostics when CodeQL cannot produce SARIF) is retained per case under
`reports/raw/codeql-csharp-kernel/`.

## Anchor evidence and result semantics

CodeQL query results are evidence, not ground truth by themselves. The runner
reconciles SARIF result locations with the case's `DFB-SINK:` anchor. That
marker identifies the anchored sink method declaration; the C# dialect of the
shared reconciler reads the declared method name as the identifier preceding
the parameter list, and then accepts a SARIF result that lies in the same
fixture file on a line that calls that method. The result need not be on the
marker's own line. Query path evidence identifies the `DFB-SOURCE:` to sink
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

Both retained snapshots cover the classic 32 C# core assertions — they were
taken before the challenge expansion and are freeze-bound, so neither was
re-run by the challenge wave (see [the challenge-tier
expansion](#challenge-tier-expansion) below). They are separate populations and
are not pooled with each other or with any other language, and neither is
compared with an expanded-core number.

### CodeQL, `reports/codeql-csharp-kernel.json`

CodeQL CLI 2.26.3, build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`,
with `codeql/csharp-all@7.1.2` from the committed lock. Configuration hash
`cd5f68b8ccb2e4de27cf1606b0c9f2ee8981ce5dfdf8ee2fea08fe977a0c56c9`.

32 results: 15 `reached` and 17 `not-reached`, with zero `inconclusive`,
`unsupported`, or `runner-error` outcomes. 27 of 32 match the expected
polarity. The five mismatches are:

- false negatives: `dfb-taint-csharp-alias-propagation-positive`,
  `dfb-taint-csharp-exception-catch-positive`, and
  `dfb-taint-csharp-expression-positive`;
- false positives: `dfb-taint-csharp-array-element-negative` and
  `dfb-taint-csharp-loop-carried-negative`.

That mismatch set is exactly the one the Java kernel shows on the same
templates with the same CLI, which is the expected outcome for a port whose
cells are all directly applicable.

All 32 retained raw outputs are SARIF files under
`reports/raw/codeql-csharp-kernel/`, with zero error files, and normalized
`witness_checkpoints` are empty for every case: the adapter records
anchor-backed flow outcomes and leaves the path evidence in SARIF rather than
fabricating observed witness markers. End-to-end per-case wall clock, including
cold database creation, ranged from 25.5 s to 99.6 s (about 31 minutes for the
population). The 60-second `execution_budget` on the cases describes the
analysis budget shared with the other language kernels; C# extraction time is
reported here rather than silently rebudgeted.

### Bifrost, `reports/bifrost-csharp-kernel.json`

Bifrost 0.10.5, build identity `728ac69ab93224151c6c951b23d2f5bc681d8558`.
The outcome distribution is unchanged from the earlier v0.10.2 run.
Configuration hash
`f08e35507c55aad155ac8f5e8fe587c4b48ebe507efa4e73ca671ef2bea20098`; it covers
both `core-csharp-kernel.rqlp` and the breadth `core-direct.rqlp` because the
frozen direct pair is evaluated through the policy it declares.

32 results: 1 `reached`, 1 `not-reached`, and 30 `inconclusive`. Only the
direct-propagation pair is decisive, and both of its outcomes match the
expected polarity — 2 of 2 decisive outcomes, 2 of 32 assertions.

The 30 inconclusive results are capability evidence, never negatives. Twenty
retain `partial_discovery` and ten retain `capability_incomplete`, each with a
diagnostic of the form "taint discovery is incomplete: procedure value-flow
snapshot for ... is unsupported/unknown". The ten `capability_incomplete`
results are the heap and exception pairs (object separation, same-object field
separation, alias propagation, array element, exception catch). Re-running one
kernel fixture under the language-agnostic `core-direct.rqlp` policy reproduces
the same incompleteness, so this is Bifrost's C# procedure value-flow coverage
rather than an artifact of the language-qualified policy.

## Challenge-tier expansion

The thirteen templates of [the challenge-tier
preregistration](challenge-tier.md) have landed for C#. All thirteen cells are
applicable to C#, so the expansion adds 13 templates / 26 assertions and the
C# core denominator becomes **29 templates / 58 assertions**, exactly as the
preregistration's expanded-denominator table fixes it. The new cases live
under `cases/taint/csharp/<template>-{positive,negative}/` with ids
`dfb-taint-csharp-<template>-<polarity>`, `score_tier` `core`, and
`fixture_provenance.revision` `m3-challenge-csharp`.

Every fixture is a single self-contained `.cs` file in file-scoped namespace
`DataFlowBench`, using only the .NET base class library (`System`,
`System.Collections.Generic`, `System.Reflection`). No project file, no
package reference, no third-party dependency. The 26 fixtures compile together
under `dotnet build` with `net8.0`, `Nullable` enabled and `-warnaserror`:
**0 warnings, 0 errors**. (The classic fixtures are not compiled in the same
project because the frozen direct pair declares the same type name in both
polarities; the challenge fixtures all declare distinct types.) The CodeQL C#
runner still creates databases with `--build-mode=none`, so no build step is
part of the measurement — the compile is an authoring check only.

### Adaptations, per the preregistration's C# row

Eleven cells are **directly applicable** and needed no adaptation. The two
`language-adapted` cells are the ones the preregistration names for C#, and
both are implemented exactly as it prescribes:

| Template | Classification | C# construction |
| --- | --- | --- |
| `dfb-template-chal-reflective-invocation` | direct | `typeof(Handlers).GetMethod(name)` with `name` a local string, then `MethodInfo.Invoke(handlers, new object[] { dfb_source() })`. Positive selects `Leak`, negative the sibling `Drop`, which drops its argument and sinks a constant. |
| `dfb-template-chal-computed-property` | **adapted** | C# has no computed member syntax on ordinary objects, so the write and read go through `System.Reflection` `FieldInfo` resolved by a run-time name — `typeof(Holder).GetField(key).SetValue(...)` and `GetValue(...)` — on the Java precedent the preregistration cites. The negative uses two provably distinct constant keys (`"Payload"` / `"Other"`). Because the adaptation is reflective, the case carries `reflective-dispatch` alongside `computed-access`, which is what the preregistration's feature-tag table specifies for "the reflective adaptations of 2". |
| `dfb-template-chal-dispatch-table` | direct | `Dictionary<string, Action<string>>` populated with two lambdas; the key selects one and the selected delegate is invoked with the tainted value. `Action<string>` rather than a `Func` was chosen so the sink call sits inside the entry, matching the JavaScript and Python fixtures for this template; the template's binding parts — a function value fetched from a stdlib map by string key — are unchanged. |
| `dfb-template-chal-closure-capture` | direct | A lambda captures an enclosing local and is returned as an `Action`, invoked by the caller after the local has left scope syntactically. The negative captures the clean local instead. |
| `dfb-template-chal-function-field` | direct | A `Holder` class with an `Action<string> Fn` field; two instances, one assigned a sinking lambda and one an argument-dropping lambda, with a separate `Invoke` method reading the field and calling it. The negative passes the second holder (`object-separation`). |
| `dfb-template-chal-callback-registration` | direct | `Registry` holds `List<Action<string>>`; `Register` appends and a separate `Fire` iterates and invokes each hook with the tainted value. Zero frameworks. |
| `dfb-template-chal-anonymous-implementation` | **adapted** | C# anonymous types have properties but no methods and implement no interfaces, so — exactly as the preregistration prescribes — the fixture uses an **anonymous method**, `delegate (string value) { ... }`, assigned to a locally declared `delegate void Handler(string value)` type and invoked through that declared type. This preserves "flow through a method of an unnamed implementation invoked via its declared type". A locally declared named class would *not* be anonymous and was not used. The implementation captures nothing, which keeps it distinct from `closure-capture`. |
| `dfb-template-chal-map-iteration` | direct | `Dictionary<string, string>` retrieved by `foreach (KeyValuePair<string, string> entry in ...)`, never by a keyed `get`. The negative iterates a second, disjoint dictionary. |
| `dfb-template-chal-nested-access-path` | direct | Three nested classes give `a.B.C.Value`; the negative reads the sibling `a.B.C.Other`. |
| `dfb-template-chal-element-object` | direct | `Item[]` of two objects with distinct constant indices; `field-separation`, following the precedent the classic `dfb-template-array-element-separation` pair sets in all thirteen languages. |
| `dfb-template-chal-deep-relay-chain` | direct | Six static methods `Relay1`…`Relay6`, no branching and no state, with the sink at hop six. The negative feeds the identical chain a clean constant while the source call stays live. |
| `dfb-template-chal-recursive-carry` | direct | `static string Carry(string value, int depth)` recursing to a base case at `depth == 0`, invoked with `5`. The negative overwrites the carried value with a clean constant at the base case (`overwrite-kill`). |
| `dfb-template-chal-context-pair-depth2` | direct | The canonical [Amendment A1](challenge-tier.md#amendments) construction: `Helper` returns its argument, `Wrapper` calls it, and `OuterTainted` / `OuterClean` are the two distinct two-deep contexts. Both calls stay live in both fixtures; the positive sinks the tainted context's result, the negative the clean one's. |

No template proved unimplementable and no amendment is proposed by this wave.

### Adapter coverage: every covering adapter is deferred or absent

**This wave ran zero adapters, and that is a consequence of the freeze rule
rather than an omission.** Stated plainly so no reader mistakes it for a gap
in the fixtures:

- **Bifrost — deferred.** `reports/bifrost-csharp-kernel.json` is one of the
  nineteen reports `reports/freeze.json` digest-binds for v0.3.0. Re-running
  `run-bifrost-csharp-kernel` would overwrite published evidence and invalidate
  the freeze, so it was not run. Its 32 results remain the frozen
  16-template v0.3.0 evidence and say nothing either way about the thirteen
  challenge templates. **Expanded Bifrost evidence is pending the v0.4.0
  freeze-prep re-run.**
- **CodeQL — deferred.** `reports/codeql-csharp-kernel.json` is likewise
  freeze-bound (all ten CodeQL kernel reports are). **Expanded CodeQL evidence
  is pending the v0.4.0 freeze-prep re-run.** The selector already expects the
  full 58; the runner is simply not invoked until the freeze is re-cut.
- **Joern — absent.** The pinned distribution ships a `csharpsrc2cpg`
  frontend, but this repository has **no C# Joern slice**: there is no
  `JoernKernel` variant for C#, no C# Joern query, and no
  `reports/joern-csharp-kernel.json`. Adding one is a separate change with its
  own reproduction contract, not something a fixture wave may improvise.
- **Semgrep CE — impossible.** C# is a **Pro-only** language in the pinned
  Semgrep CE 1.175.0 distribution, named in the CLI's own `--pro-languages`
  text. There is no C# Semgrep slice and there cannot be one on CE; this is
  recorded in [the Semgrep adapter notes](../adapters/semgrep/README.md) as a
  tool limitation, not a benchmark gap.

The C# challenge cases are excluded from the Bifrost smoke population by
template identity, so the frozen 118-case smoke slice is untouched.

Consequently there are **no observed per-stratum results to report for C# in
this wave**. Reporting any would require inventing them. The expanded-core
confusion matrices for Bifrost and CodeQL will be recorded here when the
v0.4.0 re-run produces them.

## Population boundaries

C# results are their own population. They are never pooled with the Java,
JavaScript, or Python kernels, never pooled with the 13-language direct-flow
breadth slice, and never averaged with a language whose core denominator is not
also 29 templates — nor with a C# score taken over the classic 16, which is a
different population of the same name. The Java calibration cases (`dfb-template-one-hop-relay` and
`dfb-template-modeled-external-summary`) have no C# member and do not change
this denominator.
