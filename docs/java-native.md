# Java tool-native probe set

This is wave N1's Java row: the twelve fixtures of
[the tool-native model profile](native-profile.md), the vendored activation
snapshot Java's partition needs, and the four runs. It is the first row of the
profile to land, so it is also the row that establishes the six templates are
realizable as preregistered rather than badly posed.

Nothing here amends a template definition or a partition cell. The six
templates, the platform-API identities, the negative mechanisms, the capability
kinds, and the per-tool activation contracts were fixed before any of these
fixtures existed. This row contributes one amendment,
[A7](native-profile.md#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot),
which discharges Semgrep CE's *to be verified at vendoring* status for Java and
**moves no cell**.

**Java's native denominator is 6 templates / 12 assertions**, on the `modeling`
tier and the `tool-native` profile, with its own scorecards. No number in this
document is ever pooled with
[the Java taint-modeling matrix](java-modeling.md) or with
[the Java propagation kernel](java-kernel.md), and the reason is not
bookkeeping. The modeling matrix measures the **engine** under models this
benchmark supplies; this document measures the **product** — the sources,
sinks, sanitizers, summaries and entry points each vendor *ships* — over code
that calls real JDK APIs. A miss here says a shipped catalog does not cover an
API. It says nothing about whether the engine could have followed the flow had
it been told, and the modeling row is where that question is already answered.

## What is committed

| Artifact | Path |
| --- | --- |
| Cases and fixtures | `cases/taint/java/native-*-{positive,negative}/` |
| Vendored Semgrep ruleset | `adapters/semgrep/native/java/rules/` |
| Vendored ruleset provenance | `adapters/semgrep/native/java/provenance.json` |
| Reports | `reports/{bifrost,codeql,joern,semgrep,opentaint}-java-native.json` |
| Raw evidence | `reports/raw/{bifrost,codeql,joern,semgrep,opentaint}-java-native/` |
| OpenTaint activation probe | `scripts/probe-opentaint-native-activation.sh` (joined by [Amendment A22](native-profile.md#a22--2026-09-01-opentaint-joins-the-tool-native-profile-at-0--6-and-the-shipped-models-archive-is-ruled-shipped-product); see [below](#opentaint--declined-on-the-same-terms-amendment-a14)) |

There is **no model artifact**, and that absence is the profile. A native run
loads only what the vendor ships; the runner's no-benchmark-models gate reads
the pinned activation shape and refuses the run before the analyzer is touched
if any argument names one of this benchmark's own model artifacts. Every case
carries `tool_model_references: {}` for the same reason.

## Per-template realization

Every fixture is stdlib-only Java in package `dataflowbench.taint` — no
framework, no dependency, no build manifest — and compiles warning-free under
`javac 21 -Xlint:all -Werror`, which is the same host toolchain the CodeQL Java
adapter traces with `javac -d classes`. Every case is `score_tier: "modeling"`,
`model_profile: "tool-native"`, provenance revision `n1-native-java`.

The one lint concession is `@SuppressWarnings("deprecation")` on each method
that calls `Runtime.exec(String)`, which the JDK deprecated in Java 18. It is a
suppression of a *compiler* warning and changes nothing a model binds to: the
call is still `java.lang.Runtime.exec(String)`, reached through
`java.lang.Runtime.getRuntime()`, which is the identity the preregistration
pins.

| # | Template | Cat. | Platform identities, by their real names |
| --- | --- | --- | --- |
| 1 | `native-source-sink` | S | `System.getenv(String)` → `Runtime.getRuntime().exec(String)` |
| 2 | `native-propagator` | P | the same, carried by `String.concat(String)` |
| 3 | `native-sanitizer` | Z | the same, with `String.valueOf(Integer.parseInt(String))` between them in the negative |
| 4 | `native-summary` | O | the same, through `Base64.getEncoder().encodeToString(byte[])` then `Base64.getDecoder().decode(String)`, rendered with `new String(byte[])` |
| 5 | `native-entrypoint` | E | `public static void main(String[] args)`, reading `args[0]` |
| 6 | `native-persistence` | B | `System.setProperty(String, String)` then `System.getProperty(String)` |

### The native-binding trap, and how these fixtures avoid it

[The preregistration's warning](native-profile.md#the-native-binding-trap) is
that a local stand-in, a same-named helper, or a wrapper has a *different
identity* from the API a shipped model names, so a fixture built from one is
guaranteed to miss — and the miss looks exactly like a coverage gap in the
product. Not one of these twelve fixtures declares a source, a sink, a
propagator, a sanitizer, a summary, or a store. Every one of those roles is
played by a JDK API called by its own name. The only benchmark-authored methods
in the corpus are `run`, `main`, and a `report(int)` in four negatives that
consumes an otherwise-unused local; none of them stands in for a platform API.

### Anchoring: markers sit on the real API's callsite

Every other population in this benchmark anchors a `DFB-SINK:` marker on the
**declaration** of a benchmark-invented endpoint and reconciles a finding
against that endpoint's callsites. A native fixture declares nothing — its sink
is a JDK API whose declaration lives in `java.base` — so the marker sits on the
**real API's callsite** and that line is the reconciliation target directly.
No anchor dialect is consulted, because nothing has to be parsed.

That forces one deliberate departure in how a finding is read, and it is worth
stating because it is the only place the native runner differs from its
siblings. A benchmark-controlled run executes one bespoke query, so *every*
finding it produces belongs to the assertion, and a finding that misses the
sink anchor is incomplete evidence — `inconclusive`. A native run executes the
vendor's **entire shipped suite**, so findings about something else entirely —
a weak hash, a missing cookie flag — are the normal case and are simply not
this assertion's findings. They are retained in the diagnostics and never make
the cell `reached`. Only a finding on the sink-anchor line does that. Ambiguity
— a malformed location, or one finding matching two anchors — stays
`inconclusive` exactly as everywhere else.

This is the same `native_sarif_outcome` the JavaScript row runs, over the same
`run_codeql_native_case` and the same shared `codeql_sarif_for_case` database
driver. There is no Java-specific native arm: the language decides the
extractor and the pinned suite, and nothing else.

### Sink existence is preserved in every negative

Six of the twelve fixtures are negatives, and in all six the command sink is
**present and identical** to its positive's, at the same callsite shape. That
is a construction rule, not a coincidence:
[the profile's scoring rule](native-profile.md#sink-existence-only-findings-and-how-they-score)
says polarity is about the flow, so a rule that fires on the existence of a
dangerous sink alone takes a **false positive** on the negative cell. A
negative that removed the sink would let such a rule bank a true negative it
did not earn, and the balanced pair would stop measuring anything.

The negatives differ from their positives only in the value that reaches the
sink:

| Template | What the negative changes |
| --- | --- |
| 1 `source-sink` | the environment read is still there and goes nowhere; a constant reaches the sink (`unrelated-value`) |
| 2 `propagator` | the same `concat` is applied to the same environment read and goes nowhere; a clean `concat` result reaches the sink (`unrelated-value`) |
| 3 `sanitizer` | the identical flow passes through `Integer.parseInt` / `String.valueOf` first (`sanitizer`) |
| 4 `summary` | a constant makes the identical Base64 round trip; the environment read goes nowhere (`unrelated-value`) |
| 5 `entrypoint` | `args[0]` is still read in the same `main` and goes nowhere; a constant reaches the sink (`unrelated-value`) |
| 6 `persistence` | the write is under key `dfb.native.command` and the read is under `dfb.native.other` (`field-separation`) |

## Activation and the runs

All four commands were run for Java, in the preregistered order. Three of them
never handed a fixture to a binary, which is the partition working as designed:
a cell the document declines is decided **from the template identity before the
tool is touched**, so a declined cell can never produce an empty finding list
that later reads as a clean negative. Each of those runs still reads its
binary's version banner once, so its report names a pin it observed — see
[the run-level identity is witnessed](native-profile.md#the-run-level-identity-is-witnessed-including-at-0--6).

| Tool | Activation | Scored | Declined | Report configuration hash |
| --- | --- | --- | --- | --- |
| CodeQL CLI 2.26.3 | `codeql/java-queries@1.11.9:codeql-suites/java-security-extended.qls` with `--threat-model=local` | 12 | 0 | `83ea52f18a6153006b081769de1906b0e3e28d122e56a470f1b3756a2c8aa9fa` |
| Bifrost v0.10.6 | built-in policy packs | 0 | 12 | `0badb216237f88ed709f45e32283b0ea8030875e742424c3377e1fbce525c6d3` |
| Joern 4.0.610 | `DefaultSemantics` only | 0 | 12 | `3b223e2988df9965827d315f8bc6eb922c4825b1b140ad3ea922b78382b9ea28` |
| Semgrep CE 1.174.0 | `--oss-only` over `adapters/semgrep/native/java/` | 0 | 12 | `c0a2d9a459a04bd1511f71fb8d154d6cff5fc843d3a9d472c057a46493aea4b3` |

A configuration hash here binds the *activation shape* — the pinned identity,
the arguments, and the bytes of every vendored artifact — rather than a model
file, because most of a native run's configuration is not a file in this
repository. That is what makes "activation configuration is retained" a
property of the artifact instead of a claim in a README.

## CodeQL — 11 of 12, and one of the six positives is unearned

CodeQL is the only tool with a scored Java row, and it enters with six of six
templates activated. It answers **11 of 12** assertions: every positive
`reached`, five of six negatives `not-reached`, one false positive. No
`inconclusive`, no `runner-error`.

| # | Template | Cat. | Positive | Negative |
| --- | --- | --- | --- | --- |
| 1 | `native-source-sink` | S | `reached` ✓ | `not-reached` ✓ |
| 2 | `native-propagator` | P | `reached` ✓ | `not-reached` ✓ |
| 3 | `native-sanitizer` | Z | `reached` ✓ | `not-reached` ✓ |
| 4 | `native-summary` | O | `reached` ✓ | `not-reached` ✓ |
| 5 | `native-entrypoint` | E | `reached` ✓ | `not-reached` ✓ |
| 6 | `native-persistence` | B | `reached` ✗ (see below) | `reached` ✗ |

**True-positive rate 6/6, false-positive rate 1/6**, published together because
neither means much alone. Read against
[the 50% blind baseline](scoring.md#balanced-pairs-and-the-blind-baseline) — a
tool that knew none of these APIs would answer "no flow" everywhere and bank
six free true negatives — 11 of 12 is a real result, and the two numbers behind
it are where the evidence is.

Every finding is `java/command-line-injection`, and the retained SARIF code
flows show *which* shipped models carried each one:

- **S**: `getenv(...) : String` → `command`. The shipped environment source and
  the shipped `Runtime.exec` sink, one hop, exactly as the pinned model rows
  predicted.
- **P**: `getenv(...)` → `argument` → `concat(...) : String` → `command`. The
  `String.concat` propagator row is real and load-bearing.
- **Z**: the positive's unsanitized path is flagged; the negative's
  `String.valueOf(Integer.parseInt(raw))` **is** credited for the
  command-injection family. This is the cell the preregistration warned might
  expose query-family-scoped sanitizer credit, and for Java's numeric-coercion
  idiom it does not: the credit is given where this sink lives.
- **O**: `getenv(...)` → `getBytes(...)` → `encodeToString(...)` →
  `decode(...)` → `new String(...)` → `command`. Both halves of the Base64
  round trip are summarized, and the whole seven-step trip is traced. The
  template the preregistration called *most likely to miss* is covered
  end to end for Java.
- **E**: `args : String[]` → `command`. The `commandargs` threat model, enabled
  by `--threat-model=local`, is what makes this cell score at all. Without it
  the default `remote`-only threat model would have decided templates 1, 5 and
  6 for a reason that has nothing to do with coverage — which is why the option
  is part of the pinned activation contract rather than a tuning knob.

### The persistence cell: a false positive, and a true positive that is not evidence

Template 6 is the one CodeQL gets wrong, and the retained evidence shows the
failure is more interesting than the score. Both cells' code flows start at
**`System.getProperty(...)` itself**:

```
positive:  18:getProperty(...) : String -> 19:command
negative:  19:getProperty(...) : String -> 20:command
```

Neither flow passes through `System.setProperty` at line 18/19, and neither
begins at the `System.getenv` read the fixture uses as the taint origin. The
shipped catalog models `System.getProperty` as an **environment source**, not
as a store read, so:

1. the negative is reported despite reading a **distinct key** — a false
   positive, because the key is exactly what the model is not looking at; and
2. the positive's `reached` is an **unearned true positive**. It is not
   evidence that the store write/read pair is linked. The same finding would
   appear with the write deleted.

This is the hazard the preregistration named in advance, down to the
mechanism, and the shipped model's own comment says the get/set key matching
"needs to be modeled by regular CodeQL … to reduce FPs". The balanced pair is
what makes it visible: on the positive alone, category B would read as covered.

## Bifrost, Joern, Semgrep CE — declined, not failed

All three decline all six templates, so Java's native row has **no denominator
for them**. Their reports carry twelve `unsupported` outcomes each, with the
preregistered rationale retained verbatim per cell under
`reports/raw/<tool>-java-native/<case-id>-unsupported.json`, and **no binary
was invoked** for any of them.

That is capability coverage, and it never becomes a negative or reduces
anyone's denominator. It is also, deliberately, not a ranking: a tool with zero
of six has declined the profile rather than failed it.

- **Bifrost v0.10.6** — the standalone policy CLI ships no taint policy and no
  source or sink endpoint catalog, so no template can produce a finding
  whatever else it expresses. The benchmark-controlled matrix scores Bifrost on
  a category it declines here, using the same binary, because there the
  benchmark supplies the endpoints.
- **Joern 4.0.610** — `DefaultSemantics` is a table of flow constraints with no
  source catalog and no sink catalog, and `joern-scan`'s query database is
  downloaded from a floating `latest` release asset rather than shipped. The
  gap between Joern's four-of-six benchmark-controlled row and its zero-of-six
  native row is a statement about the OSS distribution's *packaging*, not about
  its engine, and making that gap legible is why this profile exists.
- **Semgrep CE 1.174.0** — the snapshot is vendored and was read; none of its
  86 rule documents binds any of the six categories. See
  [Amendment A7](native-profile.md#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
  for the per-cell evidence. Worth repeating from it: a Semgrep run over these
  fixtures would have produced nothing at all, but these cells are declined
  because no rule *binds* the categories, not because a run came back empty.
  The first is capability coverage; the second would have been six false
  negatives.

## Infer — declined on a measured silence (Amendment A14, 2026-09-01)

Infer v1.3.0 joined the profile after this row landed, by
[Amendment A14](native-profile.md#a14--2026-09-01-infers-native-row-declines-on-a-measured-silence),
for Java alone — the one modeling-tier language its pinned distribution
executes. Its row is **0 / 6**, and unlike the three declines above it could
not rest on a reading: the pinned release ships Pulse's taint analysis
disabled absent a `--pulse-taint-config`, and it *also* silently ignores a
mis-pathed configuration, so an asserted decline would be indistinguishable
from a swallowed mistake. The decline is therefore measured:
`scripts/probe-infer-native-silence.sh` ran the shipped product over all
twelve fixtures of this document with **no configuration argument at all** —
nothing to mis-path — and every run produced zero findings of any rule
(`reports/raw/amendment-a14-infer-native-silence/`). The retained run,
`reports/infer-java-native.json`, carries the twelve `unsupported` decisions
with the identity witnessed from the binary, per the profile's 0 / 6
witnessing rule.

## OpenTaint — declined on the same terms (Amendment A22, 2026-09-01)

OpenTaint joined the profile the same day, by
[Amendment A22](native-profile.md#a22--2026-09-01-opentaint-joins-the-tool-native-profile-at-0--6-and-the-shipped-models-archive-is-ruled-shipped-product),
at **0 / 6** — and its report (`reports/opentaint-java-native.json`,
2026-09-01) carries twelve `unsupported` outcomes with the amendment's
rationale retained per cell, no fixture ever handed to the analyzer, and the
release assets' digests witnessed once for the run.

The amendment settles the one boundary question this adapter poses. Its pinned
release ships `opentaint-models.tar.gz` beside the analyzer jar, and that
archive **is shipped product** — vendor pass-through propagation rows,
accumulated-field approximations, compiled dataflow-approximation classes, the
exact analogue of the flow-constraint table inside Joern's `DefaultSemantics` —
so a native run loads it. What the release does not ship is a rule set, and the
rule set is where every source, sink, and sanitizer lives: run over this row's
own `native-source-sink-positive` fixture with the archive loaded and no rule
set, the pinned analyzer registers zero rules and reports zero results
(`reports/raw/opentaint-native-activation-probe/`). Propagation without
endpoints carries nothing, so every cell is declined — packaging, not engine:
[the Java modeling row](java-modeling.md#opentaint-joins-the-row--amendment-a21-2026-09-01)
scores the same binary 12/12 on the three categories its rule surface can be
told.

## What this row does and does not license

- It licenses the statement that CodeQL's shipped Java catalog covers the
  environment source, the command sink, `String.concat`, the Base64 round trip,
  the `main` argument vector, and the numeric-coercion sanitizer — and that it
  does **not** link the system-property store.
- It licenses nothing about JavaScript or Python, whose native rows have no
  denominator until their own wave-N1 pull requests land.
- It licenses nothing about framework APIs — servlets, Spring — which are where
  most shipped model sets actually live and which
  [the preregistration excludes from v1](native-profile.md#the-native-binding-trap)
  pending a dependency-provenance decision. Native coverage measured over
  platform APIs is a floor, and it is published as one.
- It licenses no aggregate that combines these numbers with
  benchmark-controlled engine accuracy. That is
  [an invariant](native-profile.md#invariants), not a preference.

## FlowDroid — declined on the shipped catalog's text (Amendment A19, 2026-09-01)

[Amendment A19](native-profile.md#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence)
added a sixth adapter to this row after its original runs, with a **Java-only**
activation contract. The contract is live — the vendor's documented default
`SourcesAndSinks.txt` ships inside the pinned, digest-witnessed jar, the CLI's
mandatory `-s` flag is pointed at that catalog extracted verbatim, and the
release-default StubDroid summaries stay on — but the catalog's own text binds
no identity these twelve fixtures read (`Runtime.exec` is a bound sink;
`System.getenv` occurs nowhere), so all six templates are `unsupported` on
shipped-model evidence, the same shape as the other declines above.

`reports/flowdroid-java-native.json` records the twelve retained decisions,
each carrying the witnessed jar identity and the pinned activation shape:

```bash
cargo run -- run-flowdroid-native --language java \
  --flowdroid-jar soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar \
  --android-platform android-34.jar
```

The gap this makes legible is the same one Joern's and Infer's rows state, doubled:
FlowDroid scores **seven of twelve benchmark-controlled modeling templates**
on this language ([Amendment A18](modeling-matrix.md#a18--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row))
and **zero of six native templates**, with the same engine, the same jar, and
the same day's runs. The engine can be told nearly anything; the product ships
an Android-oriented catalog that knows none of the platform identities this
probe set uses. That distance — between what the model layer can activate and
what the shipped model set covers — is exactly what keeping the two profiles
separate is for.
