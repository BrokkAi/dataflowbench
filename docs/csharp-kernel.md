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

All C# fixtures use the benchmark-controlled `dfb_source` and `dfb_sink`
method names. Fixtures are single `.cs` files in file-scoped namespace
`DataFlowBench`, with no project file and no external dependency. Adapters may
lower those endpoints through their own models, but the case metadata stays
analyzer-neutral and reports retain only observed evidence.

## Case population and the frozen direct pair

The C# population is the 32 `taint`/`core` cases under `cases/taint/csharp/`.
Thirty of them were authored for this kernel with
`fixture_provenance.revision` `m2-csharp-kernel`. The direct-propagation pair
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

The command selects only the 32 C# core assertions, materializes one isolated
workspace per case outside the repository, writes the normalized report to
`reports/bifrost-csharp-kernel.json`, and retains the verbatim per-case Bifrost
JSON under `reports/raw/bifrost-csharp-kernel/`. A report with incomplete runs
is normalized as `inconclusive`, never as a negative.

## CodeQL selection and reproduction

The CodeQL C# vertical slice is exactly those 32 cases. Every selected case is
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

`codeql pack install` resolved `codeql/csharp-all@7.1.2` for CodeQL CLI 2.26.3
(build SHA `7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`); the complete transitive
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

<!-- RESULTS -->

## Population boundaries

C# results are their own population. They are never pooled with the Java,
JavaScript, or Python kernels, never pooled with the 13-language direct-flow
breadth slice, and never averaged with a language whose core denominator is not
also 16 templates. The Java calibration cases (`dfb-template-one-hop-relay` and
`dfb-template-modeled-external-summary`) have no C# member and do not change
this denominator.
