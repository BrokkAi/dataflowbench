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

Three spellings verified against the pinned engine are load-bearing:

- **`languages: [java]` in both templates**, including Kotlin's. The engine
  keys its JVM rule front end on `java` and analyzes Kotlin through the same
  bytecode IR; a rule declaring `languages: [kotlin]` loads without error and
  matches nothing.
- **Receiver-qualified callsite forms** (`$DFBRECV.__DFB_SOURCE__()` beside
  the bare form). Patterns match the lifted JVM IR, where every Kotlin
  `object` member call carries an `INSTANCE` receiver; the bare pattern alone
  matches only static-style calls.
- **`options: primitive-tracking: true` in both templates**, per
  [Amendment A11](../../docs/adapters.md#a11--2026-08-31-opentaints-value-kind-boundary-is-a-default-rule-configuration-and-primitive-tracking-is-enabled-in-both-kernel-templates).
  The engine disables taint through primitive values by default and enables
  it per rule — the mechanism its own shipped ruleset uses — and the
  benchmark's numerically-encoded endpoint contracts require it. Identified
  by the upstream maintainers in response to the adapter's value-kind report
  ([seqra/opentaint#388](https://github.com/seqra/opentaint/issues/388)) and
  verified against the pinned analyzer by the retained primitive-tracking
  probe (below).

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

## The value-kind boundary, resolved as a default rule configuration

The dominant result in these populations' first retained runs was a
**value-kind boundary**: under the original templates the pinned engine
carried taint on reference-typed values and dropped it on numeric ones —
`int` and boxed `Integer` alike. `scripts/probe-opentaint-value-kind.sh`
retains the discrimination under `reports/raw/opentaint-value-kind-probe/`:
four rules over four copies of the same direct source-to-sink shape, varying
only the value type. The load trace shows all four rules registered; the
SARIF reports the `String` and `Object` flows and neither numeric one.

That boundary was reported upstream as
[seqra/opentaint#388](https://github.com/seqra/opentaint/issues/388), and the
maintainers identified it as a **default rule configuration**, not an engine
limit: primitive tracking is disabled by default and enabled per rule with
`options: primitive-tracking: true`, the mechanism the shipped ruleset's own
primitive-flow rules use. `scripts/probe-opentaint-primitive-tracking.sh`
verified the claim on the same pinned jar, retained under
`reports/raw/opentaint-primitive-tracking-probe/`: with the option absent the
value-kind probe reproduces exactly, and with it enabled all four value kinds
carry — with zero findings on the probe's added clean and overwrite negative
arms, so at probe scale the option costs no over-approximation. A Kotlin
mirror of the probe behaved identically.

[Amendment A11](../../docs/adapters.md#a11--2026-08-31-opentaints-value-kind-boundary-is-a-default-rule-configuration-and-primitive-tracking-is-enabled-in-both-kernel-templates)
therefore enabled the option in both kernel templates and re-ran both
populations; the results below are the amended-template runs. The corpus
encodes most endpoint contracts numerically — all 29 of Java's core
templates and 15 of Kotlin's 29 — so under the original templates those
cases measured the default configuration 44 times over; under the amended
templates they measure the templates' semantic dimensions. Both probes are
retained as evidence and are **not** partition inputs — the scored population
is unchanged by them.

## Observed results

Both kernels ran the pinned analyzer over their full expanded cores on the
same machine (`run-environment.json` beside each run's raw evidence), under
the A11-amended templates. No `runner-error`, no `inconclusive`, no
`unsupported` in either population. The original-template runs — Java 29/58
with all 29 misses on `int`-encoded positives, Kotlin 38/58 with every
`Int`-encoded positive missed — are superseded by these; they measured the
default configuration's value-kind boundary 44 times over, and their
headline movement here (Java +20, Kotlin +12) is that boundary's removal,
not an engine change: the jar is digest-identical.

### Java — `reports/opentaint-java-kernel.json`

58 assertions: 30 `reached`, 28 `not-reached`; **49/58** match expected
polarity — 29/32 classic and 20/26 challenge, four false negatives and five
false positives. With primitives carrying, all 29 templates measure their
semantic dimensions:

- **Depth and context discriminate correctly**: the six-hop
  `deep-relay-chain` pair (which Joern's pinned `maxCallDepth=4` misses in
  five languages), `recursive-carry`, `context-pair-depth2`,
  `closure-capture`, `anonymous-implementation`, and `nested-access-path`
  are right in both polarities, now on `int`-typed values.
- **The four false negatives** are `exception-catch` (taint through a thrown
  exception's payload), `callback-registration` and `map-iteration` (flows
  through registered `IntConsumer` callbacks and map-entry iteration), and
  `reflective-invocation` (the string-resolved callee). The middle two are
  correct in Kotlin, where those templates are `String`-encoded — a residual
  numeric asymmetry retained as measured, not attributed.
- **The five false positives** are the dynamic-heap-location family reported
  upstream as [seqra/opentaint#389](https://github.com/seqra/opentaint/issues/389)
  (`array-element`, `computed-property`, `dispatch-table`, `element-object`
  negatives — the clean sibling of a keyed or indexed location reports too)
  plus `loop-carried-negative`, where the loop's overwritten value is
  over-approximated. `infeasible-branch-negative` stays clean.

### Kotlin — `reports/opentaint-kotlin-kernel.json`

58 assertions: 33 `reached`, 25 `not-reached`; **50/58** match expected
polarity — 29/32 classic and 21/26 challenge, two false negatives and six
false positives. Every `Int`-encoded positive the original run missed on the
value-kind boundary is now `reached`; the two remaining false negatives are
`exception-catch` (`Int`-encoded, the same miss as Java's) and
`reflective-invocation` (the callee resolved from a run-time string is not
followed — the same reflection-resolution miss as before, and as Java's).

The six false positives are the same dynamic-heap-location family
(`computed-property`, `dispatch-table`, `element-object`, `function-field` —
the four the original run measured, unchanged — joined by `array-element`,
whose `Int`-encoded negative was trivially clean before primitives carried)
plus `loop-carried-negative`. The retained SARIF `codeFlows` show the engine
walking the *wrong* entry (e.g. through `leak` after `getValue("drop")` in
the dispatch-table negative), so these are genuine engine claims, not
reconciliation artifacts; the family is reported upstream as
[seqra/opentaint#389](https://github.com/seqra/opentaint/issues/389), with a
minimal repro showing named object fields *are* kept separate — the
over-approximation is specific to dynamically-keyed locations.
`infeasible-branch-negative` stays clean here too.

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

The value-kind probe and the primitive-tracking probe that resolved it:

```bash
scripts/probe-opentaint-value-kind.sh --analyzer-jar /path/to/opentaint-project-analyzer.jar
scripts/probe-opentaint-primitive-tracking.sh --analyzer-jar /path/to/opentaint-project-analyzer.jar
```
