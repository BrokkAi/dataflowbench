# FlowDroid adapter

FlowDroid ([secure-software-engineering/FlowDroid](https://github.com/secure-software-engineering/FlowDroid))
is the academic-standard open-source taint engine for Java/Android: a
context-, flow-, field- and object-sensitive IFDS analysis over Soot. This
adapter runs the pinned release's command-line analyzer over the Java and
Kotlin expanded core kernels — the two benchmark languages whose fixtures
compile to the JVM bytecode the engine consumes — and normalizes the
outcomes to the DataFlowBench contract. It implements the FlowDroid entry of
issue #82.

## Eligibility evaluation

`docs/adapters.md` admits an adapter only when four bounds hold. FlowDroid
was evaluated in the field, not from its prospectus:

1. **Semantic data flow** — holds. The engine is a real whole-program IFDS
   taint analysis: probed flows carry source-to-sink evidence, the six-hop
   relay chain is followed, the local-overwrite kill and the branch-join
   pair are discriminated correctly, and the alias-propagation heap flow is
   found.
2. **Local, pinnable execution** — holds. The pin is **2.15.1** (2026-02-23,
   the newest release at evaluation time). The 2.15.x releases publish no
   GitHub release assets; the release channel is Maven Central, and the
   pinned artifact is
   `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar`, invoked locally on
   a plain JVM with no account, network, or service dependency.
3. **Retained native output** — holds. The CLI writes a results XML
   (`-o`) that self-reports a `TerminationState` and echoes, for every
   found flow, the exact sources-and-sinks definition it matched — directly
   reconcilable against the case's anchored sink identity. Two zero-exit
   failure modes require a verified guard (below).
4. **Publishable results** — holds. FlowDroid is LGPL-2.1, with no
   benchmark-restricting terms.

**The APK-only gate was the decisive field question.** The released CLI
analyzes Android packages only, verified against the binary: a plain jar of
compiled classes is refused (`does not contain an Android Manifest`), the
`-p` Android platform directory is mandatory, and entry points come
exclusively from the manifest's declared components. What keeps this within
the adapter bounds is that a *minimal* APK is materializable from pinned,
JVM-only pieces — no Android SDK, no aapt, no Gradle:

- the fixtures compile with the harness `javac`/`kotlinc` exactly as the
  OpenTaint kernels compile them;
- the classes are translated to dex by the **D8** entry point of the pinned
  r8 jar (a single Maven artifact executed on the same JVM — a
  deterministic bytecode translation, not a toolchain);
- the binary (AXML) `AndroidManifest.xml` is generated **once** by the
  committed [`template/ManifestGen.java`](template/ManifestGen.java) using
  the axml writer the pinned FlowDroid jar itself bundles, and the two
  language blobs are committed;
- the APK is a stored zip the runner writes itself.

Language scope was verified rather than assumed: the pinned jar executes and
decides both **Java** (`javac` bytecode) and **Kotlin** (`kotlinc` 2.4.10
bytecode, with `kotlin-stdlib.jar` dexed into the analyzed image), including
flows on `int`-typed values — unlike the OpenTaint engine's value-kind
boundary, FlowDroid carries taint on numerics.

## Pinned tool identity, witnessed per run

The pin is release **2.15.1**. The jar self-reports its version in its
embedded `META-INF/maven/de.fraunhofer.sit.sse.flowdroid/soot-infoflow-cmd/pom.properties`,
and every run witnesses that value from the jar actually invoked — alongside
the measured SHA-256 of the jar's bytes against the pinned digest — refusing
to run, with both values in the error, when either differs. A report can
never carry an asserted identity.

| Artifact | Source | SHA-256 |
| --- | --- | --- |
| `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar` | Maven Central, `de.fraunhofer.sit.sse.flowdroid:soot-infoflow-cmd:2.15.1` | `51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218` |
| `android.jar` (API 34 platform stubs) | [Sable/android-platforms](https://github.com/Sable/android-platforms) `android-34/android.jar` @ commit `b439048e` | `6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad` |
| `r8-8.5.35.jar` (D8 dex translator) | Google Maven, `com.android.tools:r8:8.5.35` | `4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294` |

The platform jar is pinned and digest-witnessed like the analyzer because
FlowDroid resolves the analyzed framework stubs from it — it is part of the
analyzed image, not a build tool. The r8 jar is materialization plumbing (it
decides whether an APK exists, never what the analyzer claims about it), so
its self-reported `D8 --version` and digest are witnessed into the run's
`run-environment.json` stamp rather than gating the run.

## Execution model

Per case, in an isolated scratch workspace that is removed after its raw
evidence is retained:

1. The declared fixture files are materialized on their package paths, the
   way the OpenTaint kernels place them; a fixture declaring any package
   but the language's own (`dataflowbench.taint` for Java, `dataflowbench`
   for Kotlin) is refused as a benchmark defect, never a case outcome.
2. The fixtures are compiled — `javac -nowarn` for Java, `kotlinc -nowarn`
   for Kotlin.
3. The entry shape and the endpoint signatures are **witnessed from the
   compiled classes** (a minimal class-file reader in the runner), not
   guessed from source text.
4. The harness activity wrapper is rendered from the committed template and
   compiled against the platform jar plus the fixture classes. FlowDroid
   derives entry points from the manifest's Android components and the
   fixtures declare none, so the wrapper's `onCreate` calls the fixture's
   own entry method — the adapter's analogue of OpenTaint's documented
   all-methods entry-point selector. Every core fixture in both languages
   declares exactly one method named `run`, taking nothing or one boolean
   (the branch-join pair); the boolean argument is derived from the
   activity bundle (`savedInstanceState == null`) so it stays statically
   unknown and the harness decides no fixture branch.
5. D8 translates every compiled class (plus, for Kotlin, the pinned
   `kotlin-stdlib.jar`) to dex, and the runner zips the dex with the
   committed manifest blob into `case.apk`.
6. FlowDroid runs once:
   `java -jar soot-infoflow-cmd-….jar -a case.apk -p android.jar -s <resolved sources-sinks> -o out.xml`,
   under the release's **default analysis configuration** — documented
   opt-in flags such as `-r` (reflection) stay off, pinned the way the
   Joern kernels pin `maxCallDepth` — and is timed as the single `total`
   phase; every materialization step above is harness work outside the
   timed boundary, per docs/adapters.md.

## Benchmark-controlled sources and sinks

FlowDroid's native endpoint mechanism is a sources-and-sinks definition
file. One committed template, `config/sources-sinks.txt`, carries the
`__DFB_SOURCE_SIGNATURES__`/`__DFB_SINK_SIGNATURES__` placeholders; the
method **names** are resolved from each case's own `DFB-SOURCE:`/`DFB-SINK:`
marker lines through the same resolver the Joern, Semgrep, OpenTaint, and
Infer kernels share, and the exact Soot signatures those names denote are
witnessed from the compiled fixture classes — every non-synthetic method of
the marker's name, the same name-based endpoint contract the other kernels'
queries and rules apply. The resolved copy is retained per case. The report's
`configuration_hash` binds all five committed artifacts (both manifest
blobs, both wrapper templates, and the endpoint template), so a change to
any invalidates both retained reports. This is **benchmark-controlled
configuration**, declared as such in the model profile: the benchmark
supplies the endpoint definitions, and FlowDroid's own shipped
`SourcesAndSinks.txt` is never used.

## Guarded failure modes

Two zero-exit behaviors of the pinned CLI were verified in the field and are
guarded per case, because either would otherwise let a failed run read as a
clean negative:

- **Failures exit zero.** A run that cannot even parse its target prints
  `The data flow analysis has failed` and exits 0. The banner anywhere in
  the retained log is a `runner-error`.
- **A leak-free run writes no results file at all.** The absence of
  `out.xml` is therefore ambiguous between "clean negative" and "never got
  there", and the runner requires the analyzer's own completion line —
  `Found N leaks from M sources` — in the retained log before recording
  any negative; a log without it is a `runner-error`, and a completion line
  reporting leaks with no results file is one too.

The results XML additionally self-reports a `TerminationState`; anything but
`Success` (data-flow or path-reconstruction timeouts, aborts) is incomplete
evidence and normalizes to `inconclusive`, never `not-reached`.

## Scored partition

The whole expanded core is scored for both languages: 29 templates / 58
assertions each, Java and Kotlin's preregistered denominators. The pinned
distribution declares whole-program, context- and flow-sensitive taint
analysis over the full APK and fences no construct class behind a tier or a
documented capability boundary — reflection and implicit-flow support are
documented opt-in *flags* of one configurable analysis, and the run pins
the release's defaults — so as with the OpenTaint and Infer kernels there
is no documented boundary to preregister an `unsupported` partition from:
no case is excluded by declared capability, no capability-decision
documents exist for these populations, and every incapacity the engine
actually has surfaces as a **measured mismatch**, never a partition
decision taken from an observed result, which the adapter contract forbids.

## Outcome semantics

The five states are retained distinctly, and incompletes never become
negatives:

- `runner-error` — a compile, dex, or analyzer stage fails to spawn or
  exits non-zero; the failure banner appears in the log; the log carries no
  completion line; the completion line reports leaks but no results XML
  exists; or the results XML cannot be read.
- `reached` — a `<Result>` whose echoed sink definition
  (`MethodSourceSinkDefinition`) is one of the case's witnessed anchored
  sink signatures, in a results document self-reporting `Success`.
- `not-reached` — a completed run (completion line present, no failure
  banner) with zero leaks, whether FlowDroid wrote an empty results
  document or none at all.
- `inconclusive` — endpoints or the entry shape that cannot be resolved
  from the case's own markers and compiled classes; a `TerminationState`
  other than `Success`; or findings that reconcile against no anchored sink
  signature.
- `unsupported` — unused in these populations; the scored partition above
  excludes nothing.

## Observed results

Both kernels ran the pinned jar over their full expanded cores on the same
machine (`run-environment.json` beside each run's raw evidence). No
`runner-error`, no `inconclusive`, no `unsupported` in either population;
every retained results document self-reports `TerminationState="Success"`.

| Population | Assertions | `reached` / `not-reached` | Polarity match | Classic | Challenge | False positives |
| --- | --- | --- | --- | --- | --- | --- |
| Java — `reports/flowdroid-java-kernel.json` | 58 | 28 / 30 | **49/58** | 30/32 | 19/26 | 4 |
| Kotlin — `reports/flowdroid-kotlin-kernel.json` | 58 | 30 / 28 | **49/58** | 30/32 | 19/26 | 5 |

The mismatches organize into four engine families, and the two front ends —
`javac` bytecode and `kotlinc` bytecode, both dexed the same way — split
inside two of them, which is itself a measurement:

- **Path sensitivity** — the `loop-carried` negative is a false positive in
  both languages: the engine does not separate the iteration that assigns
  the tainted value from the one that overwrites it. This is the same
  family Semgrep CE's engine reports as a false positive in every language;
  unlike Semgrep, the `infeasible-branch` negative *is* discriminated —
  the retained log shows the release's default code elimination removing
  the statically dead code before source lookup (zero sources found).
- **Container-element conflation** — the `array-element` and
  `element-object` negatives are false positives in both languages: the
  access-path abstraction taints the array or container as a whole, so a
  value read from a *different* element reads as the tainted one. This is
  over-approximation on exactly the container class where Infer
  under-approximates (its misses are positives in that family), and the
  same keyed-indirection family the OpenTaint Kotlin kernel measures.
- **Stored-function indirection** — the `dispatch-table` and
  `callback-registration` positives (functions stored in maps and
  registration lists, fired later) are missed in both languages. The
  `function-field` and `closure-capture` cells split by front end: Java
  misses both flows outright, while Kotlin follows them and instead
  over-approximates which stored function fires — its `function-field`
  negative, and its `anonymous-implementation` negative in the same
  dispatch family, are false positives. Same templates, same engine, same
  dex pipeline; the two compilers' function-object encodings measurably
  land on opposite sides of the engine's callgraph boundary.
- **Reflection** — the `reflective-invocation` positive
  (`Method.invoke` on a run-time name) is missed in both languages, the
  expected shape of the pinned default configuration (reflection support is
  the documented opt-in `-r`, left off). The `computed-property` pair
  (Field reflection) splits: Java's `setInt`/`getInt` spelling resolves as
  whole-object taint — the positive is followed, the negative
  over-approximated — while Kotlin's `set`/`get`-through-`KClass.java`
  spelling drops the flow entirely.

Everything else discriminates correctly in both languages, including
`recursive-carry` (the recursion boundary Infer misses in all three of its
languages), the six-hop `deep-relay-chain` (the depth Joern's pinned
`maxCallDepth=4` misses in five languages), `map-iteration` (a container
flow the summaries *do* carry, unlike the stored-function cells),
`alias-propagation`, `heap-object`/`nested-access-path` field flows,
`exception-catch`, `sanitizer-block`, and both context-sensitivity pairs.

## Retained artifacts

Per case under `reports/raw/flowdroid-<language>-kernel/`: the runner's
evidence document (`<case-id>.json` — the invocation, exit status, verbatim
log, leak count, and the verbatim results XML when one was written), the
results XML again as its own verbatim sidecar (`<case-id>-results.xml`,
present exactly when FlowDroid wrote one), the resolved sources-and-sinks
definition (`<case-id>-sources-sinks.txt`), the rendered wrapper
(`<case-id>-wrapper.java`/`.kt`), and the phase-timing sidecar
(`<case-id>-timing.json`, phase `total`); `<case-id>-error.json`
diagnostics replace the evidence document where a stage failed. Once per
run: `run-environment.json` with the witnessed identity, including the
witnessed D8 version and r8 jar digest.

## Reproduction

Download and verify the three pinned artifacts (digests in the identity
table above):

```bash
curl -LO https://repo1.maven.org/maven2/de/fraunhofer/sit/sse/flowdroid/soot-infoflow-cmd/2.15.1/soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar
curl -L -o android-34.jar https://raw.githubusercontent.com/Sable/android-platforms/b439048ed3def8f48fa5801bb4bf4729b112f7ac/android-34/android.jar
curl -L -o r8-8.5.35.jar https://maven.google.com/com/android/tools/r8/8.5.35/r8-8.5.35.jar
shasum -a 256 soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar android-34.jar r8-8.5.35.jar
```

Then run each kernel (the runner re-witnesses every identity before any
case):

```bash
cargo run -- run-flowdroid-java-kernel \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar \
  --d8-jar r8-8.5.35.jar
cargo run -- run-flowdroid-kotlin-kernel \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar \
  --d8-jar r8-8.5.35.jar \
  --kotlin-stdlib /path/to/kotlin-stdlib.jar
```

The retained runs used OpenJDK Temurin 21.0.8 as the JVM for the analyzer
and D8, the same `javac`, and `kotlinc-jvm 2.4.10` with its distribution's
`kotlin-stdlib.jar`. The fixture toolchain is harness plumbing: it decides
whether an APK exists, never what the analyzer claims about it.

## Modeling matrix (Java; Amendment A18)

The adapter joined the benchmark-controlled taint-modeling matrix on
2026-09-01, with a Java-only partition preregistered on retained probe
evidence before the first scored run
([Amendment A18](../../docs/modeling-matrix.md#a18--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row)).
Scored: categories S, P, and O whole, plus category Z's `sanitizer-kill`
template — fourteen of the twenty-four Java assertions. Declined with
retained rationales: `sanitizer-selectivity` (the summary resolution is
exclusive for the whole declaring class, so suppression and selectivity
cannot coexist in one invocation), category E (analysis roots come
exclusively from the APK manifest; a declared parameter source parses and
creates no root — probed), and category B (no surface carries a store
identity or key position).

The declarations live in two surfaces. Sources and sinks resolve per case
from the fixtures' own `DFB-SOURCE:`/`DFB-SINK:` markers through the kernel
mechanism above, witnessed as Soot signatures from the compiled classes. The
propagator, sanitizer, and summary declarations are committed StubDroid
summary XMLs — [`summaries/model-java/`](summaries/model-java/) — activated
per case as `-tw STUBDROID -t <dir>`, which **replaces** the release
default's bundled `summariesManual` provider so the benchmark's declarations
are the only summaries in the run; that replacement is what satisfies the
matrix's load-bearing-model requirement, and the runner refuses a run whose
committed XMLs no longer carry the declared entries. Two field notes for
reproducers, both measured: the *EasyTaintWrapper* text surface needs a `^`
include-prefix line before any entry registers (one reason the summaries
surface was chosen), and an empty `<flows>` method entry does not register as
a no-flow declaration on its own — the class-exclusive resolution is what
drops taint at undeclared members of a summarized class.

The retained run (`reports/flowdroid-java-modeling.json`, raw evidence under
`reports/raw/flowdroid-java-modeling/`) decides all fourteen scored
assertions correctly — positionally faithful on the declared-position pair
and field-precise on the store-through summary. Per-case timing sidecars
record `compile`, `dex`, and `analyze` subprocess phases
([latency-tier Amendment A20](../../docs/latency-tier.md#a20--2026-09-01-flowdroids-modeling-population-declares-three-subprocess-phases));
only `analyze` is an analyzer number. The zero-exit guards above apply
unchanged: no negative is recorded without the analyzer's own `Found N leaks`
completion line, and the failure banner is a `runner-error` wherever it
appears.

```bash
cargo run -- run-flowdroid-modeling --language java \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar \
  --d8-jar r8-8.5.35.jar

scripts/probe-flowdroid-modeling-load-bearing.sh \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar --d8-jar r8-8.5.35.jar
```

## Tool-native profile (Java; Amendment A19)

The release ships its model surface inside the pinned jar: the vendor's
documented default `SourcesAndSinks.txt` catalog (the CLI's `-s` flag is
mandatory — omitting it produces the zero-exit failure banner — so the
activation shape extracts the bundled catalog verbatim and points the flag at
it) and the default StubDroid `summariesManual` taint wrapper. That is a live
activation contract, and it needs no vendored snapshot: the jar digest the
run already witnesses is the provenance
([Amendment A19](../../docs/native-profile.md#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence)).

The catalog's own text decides the cells: it binds the probe set's command
sink (`Runtime.exec(String)`) and **no source any native template reads** —
`System.getenv`, the system-property pair, a `main` argument vector, and
every sanitizer idiom are absent — so all six templates are `unsupported` on
shipped-model evidence, decided before any run, and
`reports/flowdroid-java-native.json` retains the twelve decisions under the
witnessed jar identity.

[Amendment A29](../../docs/native-profile.md#a29--2026-09-02-flowdroids-native-decline-is-re-grounded-on-the-shipped-surfaces-full-enumeration-and-executed-engagement)
(2026-09-02) re-grounded the decline on the shipped surface's full
enumeration and executed engagement, answering a maintainer challenge that
the A19 ruling had read only the default file. The probe
(`scripts/probe-flowdroid-native-shipped-surface.sh`, evidence under
`reports/raw/amendment-a29-flowdroid-shipped-surface/`) witnesses all three
artifact digests, enumerates every declarative resource the jar bundles —
`SourcesAndSinks.txt` is the only endpoint catalog instance in any format
(the bundled `SourcesAndSinks.xsd` XML format has no shipped instance);
`EasyTaintWrapperSource.txt` (435 wrap / 12 exclude / 5 kill entries) has no
endpoint role in its format; `AndroidCallbacks.txt` and `virtualedges.xml`
are lifecycle and callgraph surface; the 347-class `summariesManual` set
declares no `getenv` method and no `java.util.Base64` class — and then
executes. A bare `-a`/`-p` invocation has no fallback catalog (the zero-exit
banner is witnessed after the default wrapper initializes); the shipped
catalog engaged over all twelve Java native fixtures (it parses to 71
sources / 193 sinks; the release's own parser rejects 14 malformed vendor
lines) reports `Found 0 leaks from 0 sources` on every one, under this
adapter's leak-count-line guard; and a control run — the same APK plus one
benchmark-authored `getenv` source line, evidence only, never activation —
finds exactly the floor leak, attributing every zero to the catalog alone.
The only `getenv` bytes anywhere in the jar are three shaded third-party
classes that call it at tool runtime.

```bash
scripts/probe-flowdroid-native-shipped-surface.sh \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar --d8-jar r8-8.5.35.jar
```

```bash
cargo run -- run-flowdroid-native --language java \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar
```
