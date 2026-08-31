# OpenTaint adapter

OpenTaint ([seqra/opentaint](https://github.com/seqra/opentaint)) is an
open-source JVM taint engine: a formal interprocedural IFDS dataflow analysis
over bytecode, driven by Semgrep-syntax AST-pattern rules that the engine
translates into whole-program taint configurations. This adapter runs its
neutral JVM rule/model path over the Java and Kotlin expanded core kernels —
the two languages the pinned distribution actually analyzes — and normalizes
the outcomes to the DataFlowBench contract. It resolves issue #17.

## Eligibility evaluation

`docs/adapters.md` admits an adapter only when four bounds hold. OpenTaint was
evaluated in the field, not from its README:

1. **Semantic data flow** — holds. The engine is a real interprocedural IFDS
   taint analysis (`opentaint-dataflow-core` upstream), verified here by
   probe: flows through calls, aliases, and standard-library containers are
   reported with full SARIF `codeFlows` step traces.
2. **Local, pinnable execution** — holds. The project publishes dated,
   content-addressed analyzer releases (near-daily); the analyzer is a single
   jar invoked locally with no account, network, or service dependency. The
   pin is `analyzer/2026.08.27.17eb0fe`, by asset digest (below).
3. **Retained native output** — holds. The analyzer writes SARIF 2.1.0, one
   document per invocation, retained verbatim per case.
4. **Publishable results** — holds. The engine is Apache-2.0; the CLI, rules,
   and CI integrations are MIT. No benchmark-restricting terms.

Maintenance is active: multiple analyzer releases per week at the time of the
pin, with the engine, CLI, and rules developed in the open in one repository.

Language scope was verified rather than taken from the issue: the pinned
analyzer executes and emits parseable findings for **Java** (`javac` bytecode)
and **Kotlin** (`kotlinc` bytecode) fixtures. Its published language surface
is JVM bytecode only — the roadmap's other languages ship no analyzer path in
the pinned release — so Java and Kotlin are the two adapted populations,
matching the issue's intended profile.

## Pinned tool identity, witnessed per run

The pin is release **`analyzer/2026.08.27.17eb0fe`**, by the SHA-256 of its
two assets:

| Asset | SHA-256 |
| --- | --- |
| `opentaint-project-analyzer.jar` | `811bdb22786e539c9aabdce5bef91f0c6521cc099adbe2720e6a840c09badf54` |
| `opentaint-models.tar.gz` | `c2a8fb0bbc3b6d59ed6db0c62732ff9a6f0f491d515cc2247932f2dd78cbb9f5` |

The analyzer jar self-reports **no version at all**: no manifest attribute, no
version flag, and a SARIF `tool.driver.version` of `"latest"`. So the
witnessed identity is the artifact digest, measured from the bytes of the jar
and archive actually invoked, once per run and before the population is
walked, per the identity-witnessing convention (#87). The release tag is
published into a report only when both measured digests match the pinned
constants; a mismatch fails the run with both values in the error, so a report
can never carry an asserted identity. The digests ride in
`tool_build_identity` and in each run's `run-environment.json`.

`opentaint-models.tar.gz` is the analyzer's own shipped standard-library
model set — pass-through approximations and compiled dataflow-approximation
classes for the JDK, Kotlin builders, and common serialization libraries,
versioned with the analyzer in the same release. They are the tool's platform
models, analogous to the standard-library steps CodeQL's packs carry; they
declare no benchmark endpoint and never decide an outcome by themselves.

## Execution model

OpenTaint analyzes bytecode, so a fixture cannot be handed to it as a loose
source file. Per case, in an isolated scratch workspace that is removed after
its raw evidence is retained:

1. The declared fixture files are materialized on their package paths and
   compiled — `javac -nowarn -d classes` for Java, `kotlinc -nowarn -d
   classes` for Kotlin. The compile is a **harness step**, like the Joern Rust
   kernel's synthesized Cargo manifest: the bytecode is this adapter's input
   encoding. It is therefore outside the timed boundary, per the
   retained-phase-timing convention. A compile failure is `runner-error` with
   the compiler's output retained, never a case outcome.
2. A minimal `project.yaml` is synthesized — source root, the packages the
   fixtures declare, the classes directory, and (for Kotlin)
   `kotlin-stdlib.jar` as the one dependency so stdlib calls resolve.
3. The pinned analyzer runs once:

   ```text
   java -jar opentaint-project-analyzer.jar \
     --project=<workspace>/project.yaml \
     --project-kind=unknown \
     --debug-run-analysis-on-selected-entry-points=* \
     --semgrep-rule-set=<resolved-rule.yaml> \
     --semgrep-rule-load-trace=<workspace>/out/load-trace.json \
     --passthrough-approximations=<models>/java/accumulated-fields.yaml \
     --passthrough-approximations=<models>/java/config \
     --java-dataflow-approximations=<models>/java/dataflow/build/classes/java/main \
     --output-dir=<workspace>/out
   ```

   `--project-kind=unknown` is the analyzer's own non-Spring mode. The
   all-methods entry-point selector is pinned because the analyzer's default
   entry-point discovery is Spring-shaped and the benchmark fixtures declare
   no framework entry point; without it, Java's package-private static `run()`
   methods are simply never analyzed (verified in the field — Kotlin `object`
   members happen to be discovered, Java's statics do not). The flag changes
   which methods are analyzed, never what the engine claims about a flow. The
   single invocation is indivisible from the adapter's vantage and is timed as
   `total` in each case's `*-timing.json` sidecar.

## Benchmark-controlled rules

One committed `mode: taint` rule template per language, under
`adapters/opentaint/rules/`, carrying `__DFB_SOURCE__`/`__DFB_SINK__`
placeholders the runner resolves per case from the fixture's own
`DFB-SOURCE:`/`DFB-SINK:` marker lines — the same resolver and the same Java
anchor dialect the Joern and Semgrep kernels use (Kotlin satisfies the Java
dialect's surface contract exactly as it does for the Semgrep Kotlin kernel).
The resolved rule each case was analyzed under is retained beside its raw
evidence as `<case-id>-rule.yaml`. Both reports' `configuration_hash` is a
SHA-256 over both committed templates, so a change to either invalidates both
retained reports.

Two spellings verified against the pinned engine are load-bearing:

- **`languages: [java]` in both templates**, including Kotlin's. The engine
  keys its JVM rule front end on `java` and analyzes Kotlin through the same
  bytecode IR; a rule declaring `languages: [kotlin]` loads without error and
  matches nothing.
- **Receiver-qualified callsite forms** (`$DFBRECV.__DFB_SOURCE__()` beside
  the bare form). Patterns match the lifted JVM IR, where every Kotlin
  `object` member call carries an `INSTANCE` receiver; the bare pattern alone
  matches only static-style calls.

## Scored partition

The whole expanded core is scored for both languages: all 29 templates, 58
assertions each. OpenTaint's pinned documentation declares whole-program
interprocedural JVM taint — across function boundaries, fields, aliases,
persistence, and async code — and fences nothing behind a paid tier or a
documented capability boundary. Unlike Semgrep CE, whose own CLI text places
interprocedural and path-sensitive analysis outside the scored engine, there
is no vendor-documented boundary here to preregister `unsupported` cells
from. So no case is excluded by declared capability, no capability-decision
documents exist for these populations, and every incapacity the engine
actually has surfaces as a **measured mismatch** — never as a partition
decision taken from an observed result, which the adapter contract forbids.

## Outcome semantics

The five states are retained distinctly, and incompletes never become
negatives:

- `runner-error` — the fixture compiler or the analyzer fails to spawn or
  exits non-zero; the analyzer exits cleanly but writes no SARIF; the SARIF
  does not parse; **or the rule-load trace disqualifies the run**. The
  analyzer exits zero and writes a well-formed empty SARIF even when the rule
  set fails to load, so the runner requires the retained
  `<case-id>-load-trace.json` to show the benchmark rule registered and no
  load error; anything else is a runner error, not an empty finding list.
- `reached` — a SARIF result whose location sits in the case's anchor file on
  a callsite of the anchored sink function (`callsite_anchored_outcome`, the
  same reconciliation the CodeQL, Joern, and Semgrep kernels use). Findings
  are anchor-backed or they are nothing.
- `not-reached` — a clean, rule-loaded, SARIF-producing run with no finding.
- `inconclusive` — endpoints that cannot be resolved from the case's own
  markers, or findings that cannot be reconciled against the sink anchor.
- `unsupported` — unused in these populations; the scored partition above
  excludes nothing.

## The value-kind boundary

The dominant result in these populations is a property of the engine worth
stating before the tables: **the pinned engine carries taint on
reference-typed values and drops it on numeric ones** — `int` and boxed
`Integer` alike.

`scripts/probe-opentaint-value-kind.sh` retains the discrimination under
`reports/raw/opentaint-value-kind-probe/`: four rules over four copies of the
same direct source-to-sink shape, varying only the value type. The load trace
shows all four rules registered; the SARIF reports the `String` and `Object`
flows and neither numeric one. The probe is retained as evidence and is
**not** a partition input — the scored population is unchanged by it.

That boundary reads directly onto the kernels, because the corpus encodes
most endpoint contracts numerically:

- **Java's 29 core templates are all `int`-encoded**, so every core positive
  is missed: the Java kernel measures the value-kind boundary 29 times, and
  says nothing about whether the engine could otherwise follow the templates'
  semantic dimensions in Java.
- **Kotlin's core mixes 15 `Int`-encoded and 14 `String`-encoded templates**,
  so the Kotlin kernel is where the engine's propagation semantics are
  actually visible: every `String`-encoded template is a real measurement,
  and every `Int`-encoded one repeats the value-kind miss.

## Observed results

Both kernels ran the pinned analyzer over their full expanded cores on the
same machine (`run-environment.json` beside each run's raw evidence). No
`runner-error`, no `inconclusive`, no `unsupported` in either population.

### Java — `reports/opentaint-java-kernel.json`

58 assertions: 0 `reached`, 58 `not-reached`; 29/58 match expected polarity.
All 29 mismatches are false negatives on positives, and all 29 are
`int`-encoded — the value-kind boundary, uniformly, with **zero false
positives**: every one of the 29 negatives is clean, including
`infeasible-branch-negative` and `loop-carried-negative`, the two negatives
Semgrep CE's engine gets wrong in every language.

### Kotlin — `reports/opentaint-kotlin-kernel.json`

58 assertions: 17 `reached`, 41 `not-reached`; **38/58** match expected
polarity — 16 false negatives and 4 false positives. The encoding split reads
the mismatches cleanly:

| Subset | Assertions | Polarity match | Detail |
| --- | --- | --- | --- |
| `String`-encoded (direct + all 13 challenge templates) | 28 | 23/28 | 13/14 positives `reached`; 4 negatives over-approximated |
| `Int`-encoded (the other 15 classic templates) | 30 | 15/30 | every positive missed — the value-kind boundary; every negative trivially clean |

By stratum: classic 17/32 (only the `String`-encoded `direct` pair is decided
by propagation; the other fifteen classic templates are `Int`-encoded), and
**challenge 21/26** — the challenge tier is `String`-encoded throughout, so it
is where the engine is actually measured, and it measures well:

- **All depth and context templates discriminate correctly**: the six-hop
  `deep-relay-chain` pair (which Joern's pinned `maxCallDepth=4` misses in
  five languages), `recursive-carry`, `context-pair-depth2`,
  `closure-capture`, `callback-registration`, `anonymous-implementation`,
  `map-iteration`, and `nested-access-path` are all right in both polarities.
- **The one challenge false negative** is
  `dfb-taint-kotlin-reflective-invocation-positive`: the callee resolved from
  a run-time string is not followed — a real reflection-resolution miss,
  retained as measured.
- **The four false positives** — `computed-property`, `dispatch-table`,
  `element-object`, `function-field` negatives — are one family of
  over-approximation: separation between heap locations is not maintained
  where the location is selected dynamically — a keyed container entry, a
  computed member, an object field, a function value fetched from a map — so
  the clean sibling's flow is reported too. The retained SARIF `codeFlows`
  show the engine walking the *wrong* entry (e.g. through `leak` after
  `getValue("drop")` in the dispatch-table negative), so these are genuine
  engine claims, not reconciliation artifacts.

## Retained artifacts

Per case under `reports/raw/opentaint-<language>-kernel/`: the verbatim SARIF
(`<case-id>.json`), the resolved rule (`<case-id>-rule.yaml`), the rule-load
trace (`<case-id>-load-trace.json`), and the phase-timing sidecar
(`<case-id>-timing.json`); `-error.json` diagnostics replace the SARIF where a
stage failed. Once per run: `run-environment.json` with the witnessed
identity.

## Reproduction

Download the pinned release assets and verify their digests against the table
above:

```bash
gh release download analyzer/2026.08.27.17eb0fe --repo seqra/opentaint \
  --pattern 'opentaint-project-analyzer.jar' --pattern 'opentaint-models.tar.gz'
shasum -a 256 opentaint-project-analyzer.jar opentaint-models.tar.gz
```

Then run each kernel (the runner re-verifies both digests before any case):

```bash
cargo run -- run-opentaint-java-kernel \
  --analyzer-jar /path/to/opentaint-project-analyzer.jar \
  --models-archive /path/to/opentaint-models.tar.gz
cargo run -- run-opentaint-kotlin-kernel \
  --analyzer-jar /path/to/opentaint-project-analyzer.jar \
  --models-archive /path/to/opentaint-models.tar.gz \
  --kotlin-stdlib /path/to/kotlin-stdlib.jar
```

The retained runs used OpenJDK Temurin 21.0.8 (`java`/`javac`) and
`kotlinc-jvm 2.4.10` with its distribution's `kotlin-stdlib.jar` (SHA-256
`4ec0293bc3751423b203f1d8493251c57c42e73eb6377a6b8560d0974ff0a6df`). The
fixture toolchain is harness plumbing: it decides whether bytecode exists,
never what the analyzer claims about it.

The value-kind probe:

```bash
scripts/probe-opentaint-value-kind.sh --analyzer-jar /path/to/opentaint-project-analyzer.jar
```
