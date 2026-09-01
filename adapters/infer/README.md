# Infer adapter

Infer ([facebook/infer](https://github.com/facebook/infer)) is Meta's
open-source interprocedural static analyzer for C, C++, Java, and
Objective-C. This adapter runs the pinned release's **Pulse taint analysis**
over the C, C++, and Java expanded core kernels — the three benchmark
languages the pinned binary actually executes — and normalizes the outcomes
to the DataFlowBench contract. It implements the Infer entry of issue #82.

## Eligibility evaluation

`docs/adapters.md` admits an adapter only when four bounds hold. Infer was
evaluated in the field, not from its prospectus:

1. **Semantic data flow** — holds. Pulse is a real interprocedural analysis,
   and its taint configuration expresses source→sink flow queries directly:
   probed flows are reported with `bug_trace` steps from the source call to
   the sink argument, and the six-hop Java relay chain is followed through
   every hop.
2. **Local, pinnable execution** — holds. The project publishes versioned
   release binaries; the pin is **v1.3.0** (2026-05-12, the newest release at
   evaluation time), invoked locally with no account, network, or service
   dependency.
3. **Retained native output** — holds. The pinned binary writes SARIF 2.1.0
   (`--sarif` → `report.sarif`) beside its own `report.json`; the SARIF is
   retained verbatim per case.
4. **Publishable results** — holds. Infer is MIT-licensed, with no
   benchmark-restricting terms.

**Which taint mode is operable was verified against the binary, not the
docs.** The historical taint checker, Quandary, is *removed* from v1.3.0 —
`infer help --list-issue-types` names no Quandary issue type at all — so
Pulse's taint configuration (`--pulse-taint-config`, with
`pulse-taint-sources`/`-sinks`/`-policies`) is the release's one operable
taint surface, and the one this adapter drives. Its `TAINT_ERROR` issue type
is enabled by default in the pinned release.

Language scope was verified rather than taken from the issue: the pinned
binary executes and emits anchor-reconcilable findings for **C** and **C++**
(captured with the distribution's own bundled clang front end) and **Java**
(captured from a traced `javac`), including flows on `int`-typed values —
Java's core encodes every endpoint contract numerically, and unlike the
OpenTaint engine's value-kind boundary, Pulse carries taint on numerics.
Objective-C is out of benchmark scope. C and C++ were the issue's stated
motivation: both were single-engine populations (Semgrep CE's documented
intraprocedural profile) for benchmark-controlled interprocedural evidence,
and this adapter is their second engine.

## Pinned tool identity, witnessed per run

The pin is release **v1.3.0**. The binary self-reports it (`infer --version`
→ `Infer version v1.3.0`), and every run witnesses that string from the
binary actually invoked before any case is analyzed, refusing to run — with
both values in the error — when it differs, so a report can never carry an
asserted identity. The witnessed identity also carries the measured SHA-256
of the invoked binary's bytes (`tool_build_identity`, and
`run-environment.json` beside each run's raw evidence).

The retained runs used the official `infer-osx-arm64-v1.3.0.tar.xz` release
asset, SHA-256
`60eccd231e27f2a3d65947ef75b9adcd1983528296bd1da6f67a6da02e22a96e`, whose
`bin/infer` has SHA-256
`17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62`.

## Execution model

Infer analyzes code it watches being compiled, so each case materializes its
own compile command — the adapter's analogue of the per-case build contexts
the CodeQL C-family kernel materializes. Per case, in an isolated scratch
workspace that is removed after its raw evidence is retained:

1. The declared fixture files are materialized — flat for C and C++, on their
   declared package paths for Java, the way the OpenTaint kernels place them.
2. `infer capture --results-dir <out> -- <compile command>` traces the
   compile: `clang -c <fixtures>` for C, `clang++ -c <fixtures>` for C++ —
   both served by the distribution's own bundled clang front end, so the
   C-family toolchain is pinned by the release itself — and the
   harness-supplied `javac` for Java.
3. `infer analyze --results-dir <out> --pulse-only --sarif
   --pulse-taint-config <resolved-config>` runs Pulse over the captured
   intermediate representation and writes the SARIF this adapter retains.

The two subprocess boundaries the adapter genuinely observes — `capture`,
then `analyze` — are the retained phases in each case's `*-timing.json`
sidecar, exactly as the CodeQL kernels retain `database-create` and
`database-analyze`.

## Benchmark-controlled taint configuration

One committed Pulse taint-configuration template per language, under
`adapters/infer/config/`, carrying the same
`__DFB_SOURCE__`/`__DFB_SINK__` placeholders the Semgrep and OpenTaint
kernels resolve, from the same fixture marker lines, with the resolved copy
retained per case as `<case-id>-taint-config.json`. Every report's
`configuration_hash` is a SHA-256 over all three committed templates, so a
change to any invalidates all three retained reports.

Two matcher shapes verified against the pinned engine are load-bearing:

- **The plain `procedure` matcher is a substring match** — verified in the
  field: a matcher for `dfb_source` also matches a procedure named
  `dfb_source_extra`. The templates therefore use `procedure_regex` in
  anchored forms only.
- **The regex subject differs by front end.** For C and C++ it is the plain
  procedure name, so the C-family templates pin `^NAME$`. For Java it is the
  full signature (`int DirectPositive.directUntrustedInput()`), searched
  unanchored — and OCaml `Str`'s `$` does not usefully terminate a match
  inside it — so the Java template pins `\.NAME(`, bounding the method name
  by its qualifying dot and its parameter list's literal paren. Both shapes
  refuse suffixed names; a regression test pins both.

Two silent-failure modes of the pinned binary are guarded per run:

- A **missing** `--pulse-taint-config` file is silently ignored — exit zero,
  no taint question asked, an empty report that would read as a population of
  clean negatives. The runner writes the resolved configuration itself and
  proves its existence immediately before `infer analyze`; a malformed
  configuration fails loudly (exit 3) and is a `runner-error`.
- A template that **parses but declares no `pulse-taint-policies`** would
  load and report nothing; the runner refuses such a template before any case
  runs, and a test pins the committed policy wiring.

## Scored partition

The whole expanded core is scored for all three languages: 24 templates / 48
assertions for C, 28 / 56 for C++, 29 / 58 for Java — each language's own
preregistered denominator, inapplicable cells already excluded by
`applicability-matrix.md`. Infer's pinned distribution declares whole-program
interprocedural analysis, and its Pulse taint-configuration surface —
sources, sinks, propagators, sanitizers, with field accesses followed by
default — fences no construct class behind a tier or a documented capability
boundary. As with OpenTaint, there is therefore no vendor-documented boundary
to preregister `unsupported` cells from: no case is excluded by declared
capability, no capability-decision documents exist for these populations, and
every incapacity the engine actually has surfaces as a **measured mismatch**
— never as a partition decision taken from an observed result, which the
adapter contract forbids. C's `language-extension` pair (error-code-return,
goto-cleanup) is outside the core selection, as it is for the Semgrep and
OpenTaint kernels.

## Outcome semantics

The five states are retained distinctly, and incompletes never become
negatives:

- `runner-error` — `infer capture` or `infer analyze` fails to spawn or exits
  non-zero (a fixture that does not compile surfaces here, with the traced
  compiler's output retained); the analyzer exits cleanly but writes no
  SARIF; the SARIF does not parse; or the resolved taint configuration is
  missing at analysis time (the silent-skip guard above).
- `reached` — a `TAINT_ERROR` result whose location sits in the case's anchor
  file on a callsite of the anchored sink function
  (`callsite_anchored_outcome`, the same reconciliation the CodeQL, Joern,
  Semgrep, and OpenTaint kernels use).
- `not-reached` — a clean, config-loaded, SARIF-producing run with no
  `TAINT_ERROR` finding.
- `inconclusive` — endpoints that cannot be resolved from the case's own
  markers, or findings that cannot be reconciled against the sink anchor.
- `unsupported` — unused in these populations; the scored partition above
  excludes nothing.

`--pulse-only` disables every checker except Pulse, but Pulse itself also
reports memory-safety issues (`NULLPTR_DEREFERENCE` and kin). Those answer a
different question than the benchmark's taint policy asks, so reconciliation
reads only `TAINT_ERROR` results as flow claims and retains any other rule id
as a diagnostic — the same discipline the tool-native profile applies to
findings from queries the benchmark did not ask. One C case in the retained
runs carries such a diagnostic beside its taint outcome.

## Observed results

All three kernels ran the pinned binary over their full expanded cores on the
same machine (`run-environment.json` beside each run's raw evidence). No
`runner-error`, no `inconclusive`, no `unsupported` in any population.

| Population | Assertions | `reached` / `not-reached` | Polarity match | Classic | Challenge | False positives |
| --- | --- | --- | --- | --- | --- | --- |
| C — `reports/infer-c-kernel.json` | 48 | 21 / 27 | **43/48** | 28/30 | 15/18 | 1 |
| C++ — `reports/infer-cpp-kernel.json` | 56 | 19 / 37 | **47/56** | 29/32 | 18/24 | 0 |
| Java — `reports/infer-java-kernel.json` | 58 | 21 / 37 | **50/58** | 30/32 | 20/26 | 0 |

The mismatches organize into a small number of engine families, consistent
across the three front ends:

- **Arithmetic-expression drops** — the `expression` and `loop-carried`
  positives are missed in all three languages: taint on a numeric value does
  not survive `(value * 3) + 7` or `value + iteration`. The `direct`,
  `sanitizer-block`, `branch-join`, and every other straight-carry template
  is followed, so this is an operation boundary, not a value-kind boundary —
  unlike OpenTaint, Pulse carries `int`-typed taint as long as no arithmetic
  transforms it.
- **Recursion** — the `recursive-carry` positive is missed in all three
  languages; the six-hop non-recursive `deep-relay-chain` is followed in all
  three (the depth-6 relay that Joern's pinned `maxCallDepth=4` misses in
  five languages), so the boundary is recursion itself, not call depth.
- **Dynamic dispatch through containers and library types** — Java's
  `dispatch-table`, `map-iteration`, and `callback-registration` positives
  (flows through map entries and a list of registered lambdas) and C++'s
  five (`dispatch-table`, `map-iteration`, `computed-property`,
  `callback-registration`, `closure-capture` — flows through `std::map`
  entries and `std::function` values) are missed. C localizes the boundary
  sharply: its `dispatch-table`
  flow through a **raw function-pointer array** *is* followed — and
  over-approximated, the negative walking the wrong table entry being C's one
  false positive, the same keyed-indirection family the OpenTaint Kotlin
  kernel measures — while C's `callback-registration`, whose function
  pointer is stored into a struct-field array and fired later, is missed. The
  unmodeled standard-library and heap-stored indirection is the boundary,
  not indirection as such.
- **Language-specific misses** — C++'s `exception-catch` positive (the value
  travels through a thrown exception; Java's identical template is followed)
  and Java's two reflection positives: `reflective-invocation` (the callee
  resolved from a run-time string, the same reflection miss OpenTaint
  records) and `computed-property` (a `Field.getDeclaredField` access —
  Java's spelling of the computed member, where C++'s is a `std::map` entry
  and falls in the container family above).

Every other template discriminates correctly in every language it applies
to, including `alias-propagation`, `heap-object`/`nested-access-path` field
flows, `closure-capture` in Java, `anonymous-implementation`,
`context-pair-depth2`, and both path-sensitivity negatives
(`infeasible-branch`, `loop-carried`) that Semgrep CE's engine reports as
false positives in every language.

## Benchmark-controlled modeling matrix (Java)

Infer joined the modeling matrix by
[Amendment A13](../../docs/modeling-matrix.md#a13--2026-09-01-infer-joins-the-modeling-matrix-with-a-field-evaluated-partition-row),
with a partition row **field-evaluated by execution** over the committed Java
modeling fixtures before its first modeling run
(`reports/raw/amendment-a13-infer-partition/`, produced by
`scripts/probe-infer-modeling-partition.sh`). Java is the row's only
language: the pinned distribution executes no JavaScript or Python frontend,
so those languages have no Infer modeling denominator at all, and
`run-infer-modeling` refuses them rather than writing an empty report.

The partition scores **S, P (template 3 alone), and Z** — five of the twelve
templates. The declarations live in one committed configuration,
`adapters/infer/config/model-java.json`, which states the declared identities
literally (nothing is templated) through exact `class_names` +
`method_names` matchers, and which declares exactly the scored categories.
The measured boundaries behind the declined cells:

- **Template 4** — a Pulse propagator declares an output (`taint_target`)
  but no input position: the declared `select` propagator carries taint from
  the undeclared position 0 exactly as from the declared position 1, and
  unknown configuration fields are **silently ignored**, so no spelling can
  be trusted to bind the position.
- **Category O** — captured bodies are read: template 7's identity bodies
  decide both cells with no declaration at all
  (`--pulse-taint-opaque-files` is accepted and measured inert for Java),
  and template 8's `FieldsOfValue` destination taints the sibling field, so
  the field-separation negative is decided by the heap approximation.
- **Category E** — a source matcher's argument `taint_target` applies at
  call boundaries only; declared on the uncalled handler's parameter, the
  analysis synthesizes no root.
- **Category B** — no store-write/store-read vocabulary exists anywhere in
  the configuration surface.

Three silent-failure shapes of the configuration surface are gated per run,
all measured in the probes: a configuration with no `pulse-taint-policies`
loads and asks no taint question; a sanitizer whose kind no policy's
`sanitizer_kinds` names is **silently inert**; and the plain `procedure`
matcher is a substring match. `require_infer_modeling_load_bearing` refuses
all three before any case runs.

The retained run (`reports/infer-java-modeling.json`, raw evidence under
`reports/raw/infer-java-modeling/`) decides **all ten scored assertions
correctly** — both S templates, template 3's pair, and both Z templates —
with the fourteen declined assertions retained as
`preregistered-modeling-partition` capability decisions. Per-case
`capture`/`analyze` phase timings are retained exactly as the kernels'.
Reconciliation uses the member-qualified Java anchor dialect, because a
declared modeling entity is reached through its declaring type
(`Audit.record(v)`), which the kernel dialect deliberately refuses.

## Tool-native profile (Java): declines on a measured silence

Infer's tool-native row
([Amendment A14](../../docs/native-profile.md#a14--2026-09-01-infers-native-row-declines-on-a-measured-silence))
is **0 / 6**: the pinned release ships Pulse's taint analysis disabled absent
a `--pulse-taint-config`, and no Java endpoint catalog. Because this adapter's
own silent-failure guard exists precisely because a *mis-pathed*
configuration is silently ignored, the decline had to be a **measured**
silence rather than an asserted one: `scripts/probe-infer-native-silence.sh`
runs the shipped product over all twelve Java native fixtures with **no
configuration argument at all** — nothing to mis-path — and retains the
verbatim SARIF, exact argv, and exit status per fixture
(`reports/raw/amendment-a14-infer-native-silence/`). Every run produced zero
findings of any rule.

`run-infer-native --language java` writes the twelve retained
`unsupported` decisions with the run's identity witnessed from the binary —
the same version-pin-refusing witness the kernels use — per the 0 / 6
witnessing rule of the native profile. The other two languages have no Infer
native denominator and are refused outright.

## Retained artifacts

Per case under `reports/raw/infer-<language>-kernel/`: the verbatim SARIF
(`<case-id>.json`), the resolved taint configuration
(`<case-id>-taint-config.json`), and the phase-timing sidecar
(`<case-id>-timing.json`, phases `capture` and `analyze`); `-error.json`
diagnostics replace the SARIF where a stage failed. Once per run:
`run-environment.json` with the witnessed identity.

The modeling run retains the same shapes under
`reports/raw/infer-java-modeling/` (the committed configuration is
hash-bound rather than resolved per case, so no per-case config copy exists),
with `-unsupported.json` capability decisions for the declined cells; the
native run retains twelve `-unsupported.json` decisions under
`reports/raw/infer-java-native/`, plus `run-environment.json` with the
witnessed identity.

## Reproduction

Download the pinned release asset for your platform and verify it (the
macOS arm64 digest is in the identity section above):

```bash
gh release download v1.3.0 --repo facebook/infer \
  --pattern 'infer-osx-arm64-v1.3.0.tar.xz'
shasum -a 256 infer-osx-arm64-v1.3.0.tar.xz
tar xf infer-osx-arm64-v1.3.0.tar.xz
```

Then run each kernel (the runner re-witnesses the version before any case):

```bash
cargo run -- run-infer-c-kernel    --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
cargo run -- run-infer-cpp-kernel  --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
cargo run -- run-infer-java-kernel --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
```

The Java modeling tiers, and the two probe scripts whose retained evidence
backs Amendments A13 and A14:

```bash
cargo run -- run-infer-modeling --language java --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
cargo run -- run-infer-native   --language java --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
scripts/probe-infer-modeling-partition.sh --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
scripts/probe-infer-native-silence.sh     --infer /path/to/infer-osx-arm64-v1.3.0/bin/infer
```

The C and C++ compiles run under the distribution's own bundled clang; the
Java capture traces the harness `javac` (`--javac` overrides the default
`PATH` lookup; the retained runs used OpenJDK Temurin 21.0.8). The fixture
toolchain is harness plumbing: it decides whether a capture exists, never
what the analyzer claims about it.
