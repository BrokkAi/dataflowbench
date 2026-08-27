# Tool-native model profile

This document is the **preregistration artifact** for the `tool-native` model
profile: six templates over platform-native APIs, in the same six categories the
[benchmark-controlled modeling matrix](modeling-matrix.md) fixes, scored on
their own profile and never pooled with it. It merges before any native fixture
exists, before any ruleset is vendored, and before any number derived from them
is published.

Nothing in this document is a result. It is a contract about what will be
measured, stated in advance so that the measurement cannot later be shaped
around what the measurement produced.

It closes issue #16's design half and opens wave N1.

## What the tool-native profile measures

The benchmark-controlled profile measures the **engine** under equivalent
supplied models: every tool is handed the same source, sink, propagator,
sanitizer, summary, entry-point, and store declarations, and the question is
whether it activates them. The tool-native profile measures the **product**: the
sources, sinks, sanitizers, summaries, and entry points each tool *ships* and
activates by default or by its own documented native configuration, over code
that uses real platform APIs.

These are different questions, and the answers are not comparable:

- **Coverage, not accuracy.** A tool-native miss says the shipped model set does
  not cover an API. It says nothing about whether the engine could have followed
  the flow had it been told. A benchmark-controlled miss says the opposite.
- **The two profiles are never pooled.** [The scoring contract](scoring.md#model-profiles)
  already requires this, and it is restated here as an invariant because this is
  the profile most likely to be mistaken for a headline number.
- **Different pins by construction.** The native profile pins each tool's
  shipped model set — for CodeQL, query-pack versions that bundle library
  versions *different from* the adapter's benchmark-controlled pins (see
  [CodeQL](#codeql--cli-2263-shipped-security-suites)). Two profiles running on
  deliberately different pins could not be pooled even if the invariant allowed
  it.

The blind-baseline reading applies to this profile's pairs identically. Each
template contributes one positive and one minimally different negative, so a
tool whose shipped set does not know the API at all answers "no flow" on both
cells, banks one free true negative per pair, and scores exactly half. Published
native coverage is read against
[the 50% blind baseline](scoring.md#balanced-pairs-and-the-blind-baseline), not
against zero, and the per-template true-positive and false-positive rates carry
the evidence rather than the raw correct count.

## Why the canonical kernels are not run natively

The obvious design — run the existing kernels under each tool's shipped models —
is wrong, and it is worth recording why rather than leaving it to be rediscovered.

Every canonical fixture flows from `dfb_source()` to `dfb_sink()`. Those are
benchmark-invented endpoints. No shipped model set knows them, and no shipped
model set should: they are not APIs, they are markers. A native run over them
would measure the absence of an invented name in four vendors' catalogs, produce
zero findings everywhere, and read as a coverage result. It would be a
measurement of nothing, published as if it were a measurement of something.

The canonical kernels are therefore **skipped by design** under this profile.
They remain the benchmark-controlled instrument they always were. The native
probe set below is a separate, small, purpose-built population that uses real
platform APIs precisely so that a shipped model has something real to bind to.

## Governance

### Preregistration and immutability

**The amendment contract of the [challenge tier](challenge-tier.md#preregistration-and-immutability)
applies to this document verbatim**, as it does to the modeling matrix. Restated
so it cannot be lost in a cross-reference: from the moment the first analyzer
executes against the first native fixture, the six template definitions below —
semantic intent, the platform-API identities, positive shape, negative shape,
negative mechanism — and the per-tool activation contracts and partition tables
are **immutable**.

A defect discovered after that point is corrected by a documented **amendment**,
never by a silent edit. An amendment:

1. appears in a dated `## Amendments` section at the foot of this document;
2. states what changed, why, and which template IDs and languages it touches;
3. states which already-published freezes it invalidates, if any;
4. is a separate commit from any fixture, vendored ruleset, or result change.

The partition tables carry the same immutability, for the reason the modeling
matrix gives: a partition decided after a run is not a capability
classification, it is a result being relabelled. A cell that this document
records as unsupported and that a tool turns out to activate is promoted by a
dated amendment, and the run that revealed it is reported as the run that
revealed it.

Neither `docs/modeling-matrix.md` nor `docs/challenge-tier.md` is amended by
this document. Nothing here changes a benchmark-controlled cell.

### Fairness constraint, inverted: platform APIs only, by real identity

The modeling matrix bans real APIs. This document requires them, and the two
rules are the same rule applied to two different questions: a fixture must not
give an engine a second way to be right. There, a real framework endpoint would
let a shipped model decide a cell that was supposed to measure activation of a
*supplied* model. Here, an invented endpoint would leave a shipped model nothing
to bind to.

So the constraint inverts, and it comes with a trap that is easy to fall into
and silent when you do.

#### The native-binding trap

**A native fixture must reference real platform APIs by their real
fully-qualified identities.** A local mock, a same-named stand-in, a helper that
wraps the real call, or a re-export under a different module path all have a
*different identity* from the API a shipped model names, and every mature model
set binds by identity — CodeQL by `["java.lang", "System", …, "getenv", …]`,
Semgrep by a pattern rooted at `subprocess.$FUNC`, Joern by method full name.
A fixture that defines its own `def system(cmd): pass` and calls it is
guaranteed to produce a miss, and that miss will look exactly like a coverage
gap in the product. It is not. It is a benchmark defect that has silently
defeated native model binding.

Two consequences follow, and both are load-bearing:

1. **Fixtures are compile-clean using only the platform or standard library.**
   No vendored dependencies, no build-tool plugins, no package manifests, in
   v1. Every API in the tables below ships with the JDK, with Node, or with
   CPython, so a fixture compiles and runs with nothing installed.
2. **Module-specifier spelling is part of the identity.** Where a platform
   offers more than one spelling of the same import, this document pins one.
   Node's `require("child_process")` and `require("node:child_process")` are the
   same module to CodeQL — `Nodes.qll` resolves `["node:" + path, path]`,
   verified in `codeql/javascript-all@2.9.0` — but a pattern-based rule that
   matches the bare specifier literally will not see the prefixed one. The
   fixtures use the **bare specifier**, and a tool that only recognizes one
   spelling is a finding about that tool, recorded rather than engineered
   around.

**Framework APIs — servlets, Express, Flask — are a documented future
extension**, deliberately excluded from v1. They are where most shipped model
sets actually live, so a framework wave would raise native coverage
substantially. It is gated on a dependency-provenance decision this benchmark
has not made: a fixture that needs `jakarta.servlet` needs a jar, which needs a
pinned artifact with recorded provenance and a license review, which is a
different contract from `fixture_provenance.kind: authored`. That decision is
out of scope here, and a framework template arrives by amendment with the
provenance rule it needs, or not at all.

### Lineage

The six categories are the modeling matrix's own — declared sources and sinks
(S), propagators (P), sanitizers (Z), opaque procedure summaries (O), framework
entry points (E), persistence boundaries (B) — reused deliberately so the two
profiles' scorecards can be read side by side, category for category. What
changes is not the taxonomy but who supplies the model.

Fixtures are original authored code: `fixture_provenance.kind` is `authored`,
origin `DataFlowBench`, revision `n1-native-<language>`, license `MIT`, per
[fixture provenance](fixture-provenance.md). Vendored rulesets are **not**
fixtures and carry their own provenance rule; see
[provenance for vendored activation artifacts](#provenance-for-vendored-activation-artifacts).

### Initial languages

Java, JavaScript, and Python — the three languages whose kernels and modeling
rows are most mature, and the three for which every tool in the partition has a
wired extractor. The remaining ten languages have **no native denominator**
until a later applicability pass, which is different from having a zero.

## Population mechanics

### Same tier, disjoint profile

Native cases carry `score_tier: "modeling"` and
`model_profile: "tool-native"`. The tier is shared with the modeling matrix
because the question is the same *kind* of question — what does the model layer
do — and the tier is what keeps both out of every core denominator. The profile
is what separates them, and the separation is enforced, not assumed:

- a `dfb-template-native-` template implies `modeling` tier **and**
  `tool-native` profile, and each implies the template family back;
- a `dfb-template-model-` template implies `modeling` tier **and**
  `benchmark-controlled` profile, likewise;
- every modeling-tier selection filters on the profile, so a tool-native case
  can never enter a benchmark-controlled run and a benchmark-controlled case can
  never enter a native run;
- a corpus-wide check asserts the two populations never cross-select for any
  language.

That last check exists because profile-disjointness is the one invariant a
future selector could break by omission rather than by commission — a selector
that filters on the tier and forgets the profile silently pools the two, and
pooling them is precisely what [the scoring contract](scoring.md#model-profiles)
forbids.

### Identifiers

- Templates: `dfb-template-native-<short>`.
- Cases: `dfb-taint-<lang>-native-<short>-<polarity>`.

Both satisfy the case schema's existing `id` and `template_id` patterns. No
schema change is required by this document: `model_profile` already carries
`tool-native` in `schemas/case.schema.json`, `score_tier` already carries
`modeling`, and every negative mechanism, semantic dimension, and feature tag
used below already exists in its enum.

### Balanced pairs

Each of the six templates contributes exactly one positive and one minimally
different negative per language — **12 assertions per language**. A
native-population validator enforces balance and completeness against the exact
six template IDs, so an omitted template cannot hide inside a balanced but
smaller subset.

### Sink-existence-only findings, and how they score

This profile has a hazard the benchmark-controlled profile does not, and it must
be defined before any run rather than adjudicated after one.

Many shipped rulesets contain rules that fire on the **existence of a dangerous
sink**, with no flow requirement at all. The pinned upstream
`python/lang/security/audit/dangerous-subprocess-use-audit.yaml` is exactly
this: it matches `subprocess.$FUNC(...)` and excludes only literal-string
arguments. Nothing about taint enters into it.

The rule for this profile:

> **Polarity is about the FLOW.** A native finding that fires on sink existence
> alone is scored on the cell it lands in, unchanged: it is a true positive on
> the positive cell and a **false positive on the negative cell**.

That is not a technicality, it is the measurement. A product that answers "there
is a `subprocess` call here" to the question "does attacker-controlled data
reach a shell" is a product with a false-positive rate, and the balanced pair is
the instrument that reads it. No negative is excused because the rule that
flagged it was not a taint rule, and no such finding is re-scored as coverage.
Correspondingly, a positive cell answered by a sink-existence rule earns its
true positive and tells us nothing about flow — which is why per-template
true-positive *and* false-positive rates are published together and neither is
published alone.

Negatives in this document are therefore constructed so that the sink is
*present and identical* in both cells wherever the template allows it. The
negative differs in the value that reaches the sink, never in whether the sink
is there. A negative that removed the sink would let a sink-existence rule score
a true negative it did not earn.

## The six native templates

Six templates, one per modeling category. Each gives its semantic intent, the
exact platform-API identities per language, what native knowledge the cell
requires, its negative shape and mechanism, its
`expected_analysis_capability.kind`, and the honest expectation.

**On expectations.** Several cells will miss. A shipped model set that does not
cover base64 round-trips, or that credits `encodeURIComponent` only for XSS and
not for command construction, is stating a product fact. It is not a benchmark
defect and it is not an engine failure, and this document says so in advance so
that a disappointing column cannot later be re-read as either.

---

### 1. `dfb-template-native-source-sink` — category S

**Semantic intent.** A value from a platform source that every mature native
model set claims to model reaches a platform sink that every mature native model
set claims to model, in one hop, in one function.

**Native knowledge required.** A shipped **source model** for the environment
API and a shipped **sink model** for the command-execution API, plus whatever
activation the tool's contract needs to turn the source's threat model on.

| Language | Source identity | Sink identity |
| --- | --- | --- |
| Java | `java.lang.System.getenv(String)` → return value | `java.lang.Runtime.exec(String)`, reached through `java.lang.Runtime.getRuntime()` |
| JavaScript | `process.env.<NAME>` — a property read on the Node `process` global | `child_process.execSync(String)`, imported as `require("child_process")` |
| Python | `os.environ["<NAME>"]` | `os.system(String)` |

**Positive.** The environment read reaches the command sink directly.

**Negative.** A clean constant local reaches the **same sink at the same
callsite shape**. `negative_mechanism: unrelated-value`. The sink is present in
both cells by construction — see
[sink-existence-only findings](#sink-existence-only-findings-and-how-they-score).

**Capability kind.** `native-source-sink-coverage`.

**Expectation.** The floor of the profile. A tool that misses this template
ships no usable native taint coverage for that language, whatever else it
declines.

---

### 2. `dfb-template-native-propagator` — category P

**Semantic intent.** Taint passes through a platform string or path operation
that a native model set must summarize as taint-preserving. The operation's body
is inside the platform, not the fixture, so the tool has nothing to read: only a
shipped propagator summary carries the value across.

**Native knowledge required.** A shipped **propagator/summary model** for the
platform operation, in addition to template 1's source and sink models.

| Language | Propagator identity |
| --- | --- |
| Java | `java.lang.String.concat(String)` — `Argument[this]` and `Argument[0]` to return value |
| JavaScript | `path.join(...)` from `require("path")` |
| Python | `os.path.join(str, str)` |

**Positive.** The environment read is joined with a constant and the result
reaches the command sink.

**Negative.** The same join, on the same operation, at the same sink — but the
operand that reaches the sink is the **clean** one, and the tainted value is
joined into a variable that goes nowhere. `negative_mechanism: unrelated-value`.

**Capability kind.** `native-propagator-coverage`.

**Expectation.** String concatenation and path joining are the two most
frequently modeled operations in any catalog; this template is the one most
likely to be covered by a tool that covers anything.

---

### 3. `dfb-template-native-sanitizer` — category Z

**Semantic intent.** A platform sanitization idiom stands between the source and
the sink. The question is whether the shipped model set **credits** it — and, in
the negative, whether the credit is given in the query family that owns this
sink.

**Native knowledge required.** A shipped **sanitizer/barrier model** for the
platform idiom, bound to the query family whose sink the fixture uses.

| Language | Sanitizer identity |
| --- | --- |
| Java | `java.lang.Integer.parseInt(String)` — numeric coercion, the result rendered with `String.valueOf(int)` |
| JavaScript | `encodeURIComponent(String)` — the ECMAScript global |
| Python | `shlex.quote(str)` |

**Positive.** The unsanitized path from source to command sink is flagged.

**Negative.** The identical flow passes through the sanitizer before the sink
and must be suppressed. `negative_mechanism: sanitizer`.

**Capability kind.** `native-sanitizer-credit`.

**Expectation, stated because it is already visible in the pinned artifacts.**
Sanitizer credit is *query-family-scoped* in at least one shipped set, and this
template will surface that. In `codeql/javascript-all@2.9.0`,
`encodeURIComponent` is a sanitizer for XSS (`Xss.qll`) and for request forgery
(`RequestForgeryCustomizations.qll`), while `TaintTracking.qll` lists it among
the taint-**preserving** steps for everything else. In
`codeql/python-all@7.2.3`, `shlex.quote` is a barrier only for
`py/shell-command-constructed-from-input`
(`UnsafeShellCommandConstructionCustomizations.qll`) and is a plain taint
summary in `Stdlib.model.yml`. A false positive on this negative is therefore a
real, publishable product fact about where a sanitizer's credit is scoped, not a
bug in the fixture.

---

### 4. `dfb-template-native-summary` — category O

**Semantic intent.** A value makes a platform round trip — encode, then decode —
and arrives at the sink unchanged in meaning. An engine that reads no platform
bodies needs a shipped summary on **both** halves for the value to survive.

**Native knowledge required.** Shipped **procedure summaries** for the encoder
and the decoder, composed.

| Language | Round-trip identity |
| --- | --- |
| Java | `java.util.Base64.getEncoder().encodeToString(byte[])` then `java.util.Base64.getDecoder().decode(String)`, rendered with `new String(byte[])` |
| JavaScript | `Buffer.from(String).toString("base64")` then `Buffer.from(String, "base64").toString()` |
| Python | `base64.b64encode(bytes)` then `base64.b64decode(bytes)`, with `str.encode` / `bytes.decode` at the ends |

**Positive.** The environment read survives the round trip and reaches the
command sink.

**Negative.** A fresh constant makes the identical round trip into the same
sink. `negative_mechanism: unrelated-value`.

**Capability kind.** `native-summary-coverage`.

**Expectation.** This is the template most likely to miss, and a miss here is
the clearest product fact in the profile: a catalog that models neither half of
a base64 round trip loses the flow at the first call. `codeql/java-all@9.2.3`
happens to ship both halves (`java.util.model.yml` carries `Base64$Encoder` and
`Base64$Decoder` taint rows); whether the other sets and the other languages do
is what the cell measures.

---

### 5. `dfb-template-native-entrypoint` — category E

**Semantic intent.** The platform's own process-entry contract is the source.
No framework, no annotation, no registration — the convention a language's
runtime defines for "this is where the program starts and this is where its
arguments arrive".

**Native knowledge required.** A shipped **entry-point convention** that treats
the argument vector as attacker-controlled, which in a threat-model-aware tool
means the command-line-argument threat model.

| Language | Entry identity |
| --- | --- |
| Java | `public static void main(String[] args)`, reading `args[0]` |
| JavaScript | `process.argv[2]` |
| Python | `sys.argv[1]` |

**Positive.** The argument reaches the command sink.

**Negative.** A constant local, declared **beside** the argv read in the same
function, reaches the same sink; the argv read is present in the negative's
fixture and goes nowhere. `negative_mechanism: unrelated-value`.

**Capability kind.** `native-entrypoint-convention`.

**Expectation.** Whether this template scores at all is usually a *configuration*
question rather than a coverage question — several tools ship the model but do
not enable its threat model by default. That is what makes the per-tool
activation contract below load-bearing, and it is why the contract is pinned in
advance.

---

### 6. `dfb-template-native-persistence` — category B

**Semantic intent.** A value is written into a platform-provided process-wide
store under a key and read back out of the same store under the same key. Only a
native model that links the write to the read carries the taint across.

**Native knowledge required.** A shipped **store-write / store-read link**, with
key discrimination.

| Language | Store identity |
| --- | --- |
| Java | `java.lang.System.setProperty(String, String)` then `java.lang.System.getProperty(String)` |
| JavaScript | assignment to `process.env.<NAME>` then a read of `process.env.<NAME>` |
| Python | `os.environ["<NAME>"] = value` then a read of `os.environ["<NAME>"]` |

**Positive.** Write under key `K`, read under key `K`, sink.

**Negative.** Write under key `K`, read under a **distinct** key `L`, same sink.
`negative_mechanism: field-separation`.

**Capability kind.** `native-persistence-link`.

**Expectation, and a hazard worth naming in advance.** The read side of every
one of these stores is *also* a shipped environment source in at least one
catalog — `codeql/java-all@9.2.3` models `System.getProperty` as an
`environment` source, and its own comment says the get/set key matching "needs
to be modeled by regular CodeQL … to reduce FPs". A tool that treats the read as
a source rather than as a store-read will report both cells and take a false
positive on the negative, because the distinct key is exactly what it is not
looking at. That is the product behavior this template exists to make visible.

### Summary table

| # | `template_id` | Cat. | Neg. mechanism | `expected_analysis_capability.kind` |
| --- | --- | --- | --- | --- |
| 1 | `dfb-template-native-source-sink` | S | `unrelated-value` | `native-source-sink-coverage` |
| 2 | `dfb-template-native-propagator` | P | `unrelated-value` | `native-propagator-coverage` |
| 3 | `dfb-template-native-sanitizer` | Z | `sanitizer` | `native-sanitizer-credit` |
| 4 | `dfb-template-native-summary` | O | `unrelated-value` | `native-summary-coverage` |
| 5 | `dfb-template-native-entrypoint` | E | `unrelated-value` | `native-entrypoint-convention` |
| 6 | `dfb-template-native-persistence` | B | `field-separation` | `native-persistence-link` |

## Native activation per tool

### The activation rule

> **Only shipped models.** A tool-native run must include **no** benchmark-authored
> source, sink, sanitizer, propagator, summary, entry-point, or store
> declaration. Not one. The models under test are the ones the vendor ships.

This is the profile's equivalent of the modeling matrix's
[load-bearing-model requirement](modeling-matrix.md#the-load-bearing-model-requirement),
and it is enforced in the runner rather than trusted: every native invocation
shape is checked against the set of benchmark-authored model artifacts — every
`ModelingLanguage::artifact` path for every tool, plus the shared Joern modeling
script — and a run that would load one is a hard error before the analyzer is
touched. The invocation shapes are pinned by tests, so a later change that
splices a benchmark artifact into a native run fails the build rather than
quietly publishing engine accuracy as product coverage.

The rule cuts both ways, and the second direction matters as much as the first:
a *reconciliation* anchor is not a model. The runner still selects a case's
findings by its own source and sink anchors, exactly as every other population
does. Anchors decide which finding belongs to which assertion; they never tell
the analyzer what a source or a sink is.

### Provenance for vendored activation artifacts

Where a tool's shipped models are not pinnable at run time, the native profile
**vendors a pinned snapshot** rather than fetching. A vendored snapshot is not a
fixture and does not claim `authored` provenance: it is recorded as
`kind: derived`, with the upstream repository, the exact source commit, the
upstream path, the upstream license, and the retrieval date, in a
`provenance.json` beside the vendored files. A snapshot with no recorded source
commit is not a snapshot, and the runner refuses a native run whose activation
directory lacks one.

Nothing is vendored by this document. It pins the conventions, the paths, and
the gates; the snapshots land in wave N1's language pull requests.

### CodeQL — CLI 2.26.3, shipped security suites

**Activation contract.** The shipped security query suite for the language,
resolved from the pinned **query** pack, with the command-line-argument and
environment threat models enabled through the CLI's own documented option. No
adapter query, no data extension, no `--additional-packs` model of ours.

| Language | Query pack | Suite path |
| --- | --- | --- |
| Java | `codeql/java-queries@1.11.9` | `codeql-suites/java-security-extended.qls` |
| JavaScript | `codeql/javascript-queries@2.4.4` | `codeql-suites/javascript-security-extended.qls` |
| Python | `codeql/python-queries@1.8.9` | `codeql-suites/python-security-extended.qls` |

**Verified**, against the pinned CLI 2.26.3 on 2026-08-27: all three packs
download and all three suite paths exist, alongside `-security-and-quality`,
`-code-scanning`, and `-security-experimental` variants. `security-extended` is
selected as the standard taint suite: `code-scanning` is a narrower default and
`security-experimental` is explicitly not a product default.

**Threat models.** `codeql database analyze --threat-model=local` is a
documented CLI option, verified in `--help` on the pinned CLI. It enables the
shipped `local` group, which
`codeql/threat-models@1.0.55/ext/threat-model-grouping.model.yml` defines as
containing `environment` and `commandargs` among others. This is a
*configuration* of shipped models, not a supplied model, so it satisfies the
activation rule: the option turns vendor rows on, it does not add rows. Without
it, templates 1, 5, and 6 would be decided by CodeQL's default `remote`-only
threat model and every cell would miss for a reason that has nothing to do with
coverage.

**Pinned provenance, and a fact worth stating loudly.** A query pack bundles its
own library packs, and those versions are **not** the adapter's
benchmark-controlled pins. Verified in the downloaded packs:
`java-queries@1.11.9` bundles `java-all@9.2.4`, `javascript-queries@2.4.4`
bundles `javascript-all@2.10.0`, and `python-queries@1.8.9` bundles
`python-all@7.2.4` — against the adapter's `java-all@9.2.3`,
`javascript-all@2.9.0`, and `python-all@7.2.3`. The two profiles therefore run
on different library resolutions by construction. That is correct — the native
profile must measure the shipped product as shipped — and it is one more reason
the two profiles are never pooled.

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **supported** | Verified shipped models on all three identities: `["java.lang", "System", …, "getenv", …, "environment"]` and `["java.lang", "Runtime", …, "exec", "(String)", …, "command-injection"]` in `java-all@9.2.3/ext/java.lang.model.yml`; `['os', 'Member[environ]', 'environment']` in `python-all@7.2.3/semmle/python/frameworks/Stdlib.model.yml`; `ProcessEnvThreatSource` and the `child_process` `execSync` sink in `javascript-all@2.9.0/semmle/javascript/frameworks/NodeJSLib.qll`. |
| 2 | P | **supported** | Verified: `String.concat` carries `Argument[this]` and `Argument[0]` to the return value (`java.lang.model.yml`); `os.path.join` has an explicit additional taint step (`Stdlib.qll`). The JavaScript `path.join` row is activation-level rather than row-level verified, which is the measurement, not the partition. |
| 3 | Z | **supported** | `isBarrier`-style sanitizers ship for all three languages; the open question is *which query family* credits each idiom, which is what the cell measures. See the template's expectation. |
| 4 | O | **supported** | Verified for Java: `Base64$Encoder.encodeToString` and `Base64$Decoder.decode` both carry taint rows in `java-all@9.2.3/ext/java.util.model.yml`. The other two languages' rows are the measurement. |
| 5 | E | **supported** | Verified shipped `commandargs` sources: `['sys', 'Member[argv]', 'commandargs']` (`python-all`), `CommandLineArguments.qll` (`javascript-all`). Java's `main` parameter is covered by the same threat model. |
| 6 | B | **supported** | `System.getProperty` and `System.setProperty` are both present in the shipped model set, and the suite runs over them. Whether the pair is *linked* is the measurement — the shipped comment says it is not. |

CodeQL enters this profile with **six of six** templates scored, which reflects
that it ships the largest model set of the four and that its activation surface
is entirely pinnable. It says nothing about how many it will pass.

### Semgrep CE — 1.174.0 (`--oss-only`), vendored official rulesets

> **Amended.** All six **Python** cells were promoted from *to be verified at
> vendoring* to scored by
> [Amendment N-A1](#n-a1--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension),
> on the evidence of the vendored snapshot's
> `audit/dangerous-system-call-tainted-env-args.yaml`, read before any scan.
> Java and JavaScript are unchanged at 0 / 6 until their own snapshots are
> vendored. The same amendment keys the partition by language, which is what
> lets one language's snapshot answer only its own cells.

**Activation contract.** Registry configurations (`--config p/…`) are
network-fetched and version-unpinnable at run time: two runs a week apart are two
different rulesets under one name, which is not a benchmark. The native profile
therefore **vendors** a pinned snapshot of the official per-language security
rulesets to `adapters/semgrep/native/<language>/`, with `provenance.json`
recording the upstream repository, the source commit, the upstream paths, the
license, and the retrieval date. A run points `--config` at the vendored
directory and nothing else.

**Upstream, verified 2026-08-27.** `https://github.com/semgrep/semgrep-rules`,
default branch `develop`, head commit `40b8c63f75dc7c22c8a77482d73bfb864b146f7e`
(2026-07-30). The per-language security paths exist: `java/lang/security/`,
`javascript/lang/security/`, `python/lang/security/`, each with an `audit/`
subdirectory. The wave PR pins whichever commit it vendors and records it; the
head above is evidence that the scheme resolves, not the pin.

**Two asymmetries against the modeling profile, recorded explicitly.**

1. `--oss-only` still applies, exactly as it does in every other Semgrep
   population here. The pinned CE engine is the product under test; Pro is a
   different product and is not measured.
2. **`taint_assume_safe_functions` is NOT set.** The modeling matrix *requires*
   it, because there a permissive default would decide a cell the supplied model
   was meant to decide. Here the default **is** the product: a native run
   measures what the shipped rules do as shipped, options included. Setting it
   would be editing the vendor's rules, which the activation rule forbids. The
   two profiles' Semgrep configurations therefore differ deliberately, and this
   paragraph is the record of why.

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **to be verified at vendoring — unsupported until shown** | Inspection of the upstream head shows taint-mode rules whose sinks cover the template's command APIs (e.g. `python/lang/security/dangerous-system-call.yaml`, `mode: taint`, sink `os.system`), but whose `pattern-sources` are **framework** endpoints — Flask, Django, DRF — not `os.environ`. Whether any vendored rule binds a platform environment source is decided by the snapshot, and the snapshot does not exist yet. |
| 2 | P | **to be verified at vendoring — unsupported until shown** | Depends entirely on which rules the snapshot contains and on CE's default propagation through the platform join; neither is fixed until a commit is pinned. |
| 3 | Z | **to be verified at vendoring — unsupported until shown** | Sanitizer credit in the official rules is per-rule, not global; unverifiable before the snapshot. |
| 4 | O | **to be verified at vendoring — unsupported until shown** | Arg→return summary semantics are outside CE's propagator vocabulary on the pinned version, as [the modeling matrix established by execution](modeling-matrix.md#semgrep-ce--11740---oss-only); a shipped rule cannot supply what the engine does not express. |
| 5 | E | **to be verified at vendoring — unsupported until shown** | The upstream rules' entry conventions are framework-shaped; whether any covers `sys.argv`/`process.argv`/`main` is the snapshot's to answer. |
| 6 | B | **to be verified at vendoring — unsupported until shown** | The pinned CE engine has no interprocedural taint (`--pro-intrafile` requires Pro), and a store round trip that the rules do not link is not carried by anything else. |

Semgrep CE therefore enters with **zero of six scored**, and every promotion is a
dated amendment carrying the vendored commit as its evidence. This is the
document's own rule applied without exception: *to be verified is unsupported
until shown*. It is deliberately conservative — the alternative is to score cells
against a snapshot nobody has taken.

**The sink-existence hazard is concentrated here.** The upstream audit rules are
largely pattern rules, and
`python/lang/security/audit/dangerous-subprocess-use-audit.yaml` excludes only
literal-string arguments — so a negative that passes a clean *variable* to the
same sink is flagged. Under
[the sink-existence rule](#sink-existence-only-findings-and-how-they-score) that
is a false positive, and it is the single most likely observation this profile
will produce about any tool.

### Bifrost — v0.10.6, shipped policy packs

**Activation contract.** Built-in policy packs only: `--policy-pack` /
`--policy-category` / `--policy-id` over the catalog `--list-policies` prints.
A native run may not pass `--policy-file`, which is how every
benchmark-controlled Bifrost run supplies its models, and the no-benchmark-models
gate refuses one.

**Grounded in the adapter README and the vendor's own issue tracker.** The
adapter README states the surface gap directly: *"Sanitizer lowering is a future
Bifrost CLI capability"* and *"External semantic-model activation requires an
embedding with an explicit catalog, so the modeled-external case is reported as
`unsupported` by this CLI adapter with an explicit retained reason. It is not a
negative result."* (`adapters/bifrost/README.md`). On the vendor side,
BrokkAi/bifrost-dev **#2691** (*Modeling surface: activate external procedure
summaries from the standalone policy CLI*, open) is exactly the standalone-CLI
activation surface this profile would need, and BrokkAi/bifrost-dev **#2620**
(*Open-core RQLP security policy wave: Java*, open) is the issue under which
shipped source and sink endpoints — its own candidate inventory names
`System.getenv`, `Runtime.exec`, and `ProcessBuilder` — would first exist at all.
**#1871** (*Ship procedure-summary packs for taint-relevant standard-library
APIs*, closed 2026-08-24 as completed) supplies summaries, not endpoints, and its
problem statement records the starting position: *"Zero procedure-summary packs
ship. The embedded registry holds generator-rule packs only."*

**Verification note.** The pinned v0.10.6 build was not available while writing
this document; a locally installed **v0.9.5** was inspected. Its
`--list-policies` catalog contains exactly one pack, `bifrost.code-smells`
v1.5.0, whose fourteen policies are all `correctness` or `performance`
structural checks — no taint policy, no source or sink endpoint set. Per the
same discipline the modeling matrix applied to its own v0.9.5 inspection, this
is treated as indicative and **not** as verification of the pinned build; every
cell below is unsupported on the *to be verified* rule regardless, so nothing
turns on the difference.

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **unsupported — no shipped endpoint catalog** | The standalone CLI ships no taint policy and no source/sink endpoint set; bifrost-dev #2620 is the open issue under which the first ones would ship. Without a source and a sink, no cell in this profile can produce a finding, which is why every row below reads the same way. |
| 2 | P | **unsupported — no shipped endpoint catalog** | Same. Summary packs (#1871) carry propagation, not endpoints; propagation with nothing to propagate from produces nothing. |
| 3 | Z | **unsupported — sanitizer lowering is a future CLI capability** | Stated by `adapters/bifrost/README.md`, and reproduced by the modeling matrix's own category-Z decision. |
| 4 | O | **unsupported — external activation requires an embedding catalog** | `adapters/bifrost/README.md`, and bifrost-dev #2691 is the issue that would change it. |
| 5 | E | **to be verified — unsupported until shown** | No entry-root convention is described anywhere for the policy CLI. |
| 6 | B | **to be verified — unsupported until shown** | No persistence-boundary vocabulary is described for any adapter, Bifrost included. |

Bifrost enters with **zero of six**. That is the honest starting position for a
standalone policy CLI whose model surface lives in an embedding, it is the same
position the benchmark-controlled matrix recorded for five of its six categories,
and stating it in a preregistration published by Bifrost's own vendor — before a
run, with the vendor's open issues named — is the point.

### Joern — 4.0.610, `DefaultSemantics` only

**Activation contract.** Whatever the distribution activates without a
user-authored query or semantics file. Concretely: `DefaultSemantics`, and
nothing else. No benchmark `.semantics` file may load, and the
no-benchmark-models gate refuses `adapters/joern/semantics/model-*.semantics`
and the shared `adapters/joern/queries/modeling.sc`.

**What `DefaultSemantics` actually ships — verified.** Decompiled from
`io.joern.dataflowengineoss-<version>.jar` in a locally installed distribution
(**4.0.432**, not the pinned 4.0.610; the class surface is expected to be
identical and is to be confirmed against the pinned distribution at
implementation, on the same terms the modeling matrix used for the same jar).
`DefaultSemantics` is a table of **flow constraints**: operator semantics
(`<operator>.assignment`, `<operator>.fieldAccess`, …), a list of C standard
library functions (`strlen`, `strncpy`, `atoi`, `fwrite`, …), and a short list of
JVM-ecosystem method full names (`java.lang.String.split`,
`java.io.PrintStream.println`, `java.sql.PreparedStatement.*`,
`android.text.TextUtils.isEmpty`, `org.apache.http.*`).

It contains **no source catalog and no sink catalog**. Flow semantics constrain
how taint moves through a call; they never say where taint starts or where its
arrival is a finding. In every Joern population this benchmark runs, the sources
and sinks come from the adapter's own query parameters — which is precisely what
the activation rule forbids here.

**And the scan bundle is not shipped.** `joern-scan` is present in the
distribution, but its query database is not: `JoernScan` downloads
`querydb.zip` from
`https://github.com/joernio/joern/releases/latest/download/querydb.zip` —
verified as a string constant in `io.joern.joern-cli-4.0.432.jar`, and note the
floating `latest`. Nothing in the distribution's `lib/` provides it, and a
floating release asset is unpinnable at run time for the same reason Semgrep's
registry is. A vendored `querydb` snapshot is a possible future amendment under
[the vendoring provenance rule](#provenance-for-vendored-activation-artifacts);
it is not part of v1.

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **unsupported — `DefaultSemantics` ships no source or sink catalog** | Verified by decompilation: flow constraints only. Supplying endpoints would be a benchmark-authored model, which the activation rule forbids. |
| 2 | P | **unsupported — no endpoints to propagate between** | `DefaultSemantics` does carry propagation entries, but with no source and no sink nothing is carried anywhere. |
| 3 | Z | **unsupported — no shipped sanitizer catalog for these idioms** | `NilSemantics` is the mechanism, but the distribution declares none of the three platform sanitizers. |
| 4 | O | **unsupported — no shipped summary for these round trips** | The JVM entries in `DefaultSemantics` do not include `java.util.Base64`; neither Python nor JavaScript has any entry at all. |
| 5 | E | **unsupported — no shipped entry-point convention** | Entry roots are query-selected in every Joern population here; the distribution activates none by itself. |
| 6 | B | **unsupported — no shipped store link** | No persistence vocabulary ships. |

Joern enters with **zero of six**, and — worth saying plainly — that is a
statement about the OSS distribution's *product packaging*, not about its
engine. The benchmark-controlled matrix scores Joern on four of six categories
using the same engine. The gap between those two rows is exactly what this
profile exists to make legible.

### Partition summary

Preregistered before any native fixture exists or any ruleset is vendored.
`TBV` = to be verified at implementation or at vendoring, treated as unsupported
until shown otherwise.

> **Amended.** This table is the preregistered default and stays as written.
> [Amendment N-A1](#n-a1--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension)
> keys the partition by language and promotes Semgrep CE's six **Python** cells
> to scored; every cell for every language with no amendment row is still the
> cell below.

| # | Template | Cat. | Bifrost v0.10.6 | CodeQL 2.26.3 | Joern 4.0.610 | Semgrep CE 1.174.0 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `native-source-sink` | S | unsupported | supported | unsupported | TBV |
| 2 | `native-propagator` | P | unsupported | supported | unsupported | TBV |
| 3 | `native-sanitizer` | Z | unsupported | supported | unsupported | TBV |
| 4 | `native-summary` | O | unsupported | supported | unsupported | TBV |
| 5 | `native-entrypoint` | E | TBV | supported | unsupported | TBV |
| 6 | `native-persistence` | B | TBV | supported | unsupported | TBV |
| | **Scored today** | | **0 / 6** | **6 / 6** | **0 / 6** | **0 / 6** |

These counts are activation surfaces, not scores. A tool with six of six has six
templates' worth of assertions it can get wrong; a tool with zero of six has
declined the profile rather than failed it, and its `unsupported` cells are
coverage that never becomes a negative and never reduces anyone's denominator.
Any future summary that reads this table as a ranking is a misreading of this
document.

## Outcome honesty

[The modeling matrix's three-way distinction](modeling-matrix.md#the-three-way-distinction)
applies verbatim, with one substitution: *missing model* is not a benchmark
defect here, because the benchmark supplies no models. Its analogue is a
**missing activation artifact** — a native run whose vendored ruleset or pinned
suite is absent — and that is likewise a hard error that fails the build, never
an outcome.

- **Unsupported activation.** The tool ships nothing this template's category
  could bind to, per the partition above. Decided from the template identity
  **before the tool is invoked**, with the rationale retained verbatim. It is
  capability coverage, never a negative.
- **Incomplete analysis.** The shipped models were activated and the analysis
  did not complete. `inconclusive`, never `not-reached`.
- **Runner failure.** Missing binary, crashed process, malformed vendored
  artifact. `runner-error`, and never any of the above.

`unsupported` is decided before the run; `inconclusive` is decided after it. A
coverage miss by an activated model set is neither — it is a plain
`not-reached`, which on a positive cell is a false negative and is exactly the
number this profile is built to publish.

## Reporting

- **Reports.** Per language, per adapter:
  `reports/<tool>-<language>-native.json`, in the existing result schema, with
  raw evidence under `reports/raw/<tool>-<language>-native/`, bound into the
  freeze manifest like every other report.
- **Scorecards.** Separate, per language and per adapter, at the `modeling` tier
  and the `tool-native` profile. A scorecard states its profile; scorecards of
  the two profiles are never merged even when they share a tier and a language.
- **Per category.** Each report breaks results down by the six categories, so a
  native card and a benchmark-controlled card can be read side by side, category
  for category.
- **Never combined.** *No aggregate combines tool-native coverage with
  benchmark-controlled engine accuracy.* This is issue #16's acceptance
  criterion and it is restated here as an invariant.
- **The site.** The published site treats tool-native as a separate population
  with its own section. That is a later site pass, **out of scope** for this
  document beyond stating that the population must not be folded into an
  existing view.

## Infrastructure landed with this document

The runner infrastructure lands with this preregistration, before any fixture,
on the same terms as [the modeling matrix's](adapters.md#modeling-matrix-rollout-mechanics):

- `NATIVE_TEMPLATE_IDS` and the six-template category mapping in `src/main.rs`,
  transcribed from [the summary table](#summary-table);
- `NATIVE_PARTITION`, twenty-four cells transcribed from
  [the partition summary](#partition-summary), consulted by template identity
  before any tool is invoked;
- profile-disjoint population validators, including the corpus-wide check that
  the tool-native and benchmark-controlled modeling-tier populations never
  cross-select;
- `run-bifrost-native`, `run-codeql-native`, `run-joern-native`, and
  `run-semgrep-native`, each taking `--language java|javascript|python`;
- fail-fast gates: no population, missing pinned activation configuration, a
  `--codeql-packs` path that does not exist;
- the no-benchmark-models gate, over invocation shapes pinned by tests.

No fixture, no vendored ruleset, and no run lands with this document.

## Rollout

**Wave N1 — Java, JavaScript, Python.** One language per pull request, after
this document merges. Each PR adds that language's twelve fixtures and cases,
the vendored activation snapshots its partition needs, the runs, and any
amendment its evidence supports. A wave never edits a template definition or a
partition cell.

**Later — framework APIs,** gated on the dependency-provenance decision
described under [the native-binding trap](#the-native-binding-trap), and **the
remaining ten languages**, via an applicability pass. Neither has a denominator
until it merges.

Nothing in this plan makes a language's fixtures conditional on the results any
analyzer produces for it, and no partition cell is revised because a run was
disappointing.

## Invariants

- Tool-native and benchmark-controlled results are never pooled, never averaged,
  and never presented as one number.
- No aggregate combines native-model coverage with controlled-model engine
  accuracy.
- A tool-native case never enters a benchmark-controlled selection, and a
  benchmark-controlled case never enters a native run.
- Native cases are `score_tier: "modeling"` and never enter a core denominator,
  in any language, in any release.
- A native run supplies no benchmark-authored model of any kind; the gate is
  enforced in the runner, not trusted.
- Vendored activation artifacts carry `derived` provenance with a recorded
  source commit, or they are not used.
- `unsupported`, `inconclusive`, and `runner-error` are capability or execution
  coverage and are never converted into clean negatives.
- A native finding that fires on sink existence alone is scored on the cell it
  lands in, false positives included.
- Activation partitions are decided before runs and revised only by dated
  amendment.
- Published numbers come only from validated freeze manifests.

## Amendments

Amendments are dated, state what changed and which template IDs and languages
they touch, name the freezes they invalidate, and land as their own commits.

### N-A1 — 2026-08-27: Semgrep CE's six Python cells are promoted to scored, and the partition gains a language dimension

**What changed.** Two things, and the second is the reason the first is
expressible at all.

1. **The partition is now keyed by tool × *language* × template.** As
   preregistered it was keyed by tool × template and applied to all three
   languages at once, which was correct while every Semgrep cell read *to be
   verified at vendoring*: no snapshot existed for any language, so one
   undifferentiated `TBV` said everything there was to say. A vendored snapshot
   is per language by this document's own rule — one directory under
   `adapters/semgrep/native/<language>/` — and reading its rules can only
   answer that language's cells. Verifying Python's cells therefore cannot
   speak for Java's or JavaScript's, and a partition that could not say so
   would have forced one language's evidence onto the other two. No
   preregistered cell's *decision* is altered by this change; the twenty-four
   cells above remain the default for every language that has no amendment
   row.
2. **Semgrep CE 1.174.0 × Python: all six templates, `TBV`/unsupported →
   scored.**

**Which template IDs and languages.** All six —
`dfb-template-native-source-sink`, `-propagator`, `-sanitizer`, `-summary`,
`-entrypoint`, `-persistence` — for **Python only**. Java and JavaScript are
untouched and remain 0 / 6 for Semgrep until their own snapshots are vendored
and their own amendments recorded. No other tool's cells change; CodeQL stays
6 / 6, Bifrost and Joern stay 0 / 6.

**Why, from rule text, before any scan.** The snapshot is
`semgrep/semgrep-rules` @ `40b8c63f75dc7c22c8a77482d73bfb864b146f7e`,
`python/lang/security/` including its `audit/` subtree, ninety-one rule files,
vendored verbatim to `adapters/semgrep/native/python/` with `derived`
provenance. The preregistered rationale for Python's cells was that the
upstream taint rules bind their `pattern-sources` to *framework* endpoints —
Flask, Django, DRF — rather than to a platform environment read, which is
exactly what `python/lang/security/dangerous-system-call.yaml` does. The
snapshot contains a second rule the preregistration did not have in front of
it: `audit/dangerous-system-call-tainted-env-args.yaml`, a `mode: taint` rule
whose `pattern-sources` are

```yaml
- pattern: os.environ
- pattern: os.environ.get('$FOO', ...)
- pattern: os.getenv('$ANYTHING', ...)
…
- pattern: sys.argv
- pattern: sys.orig_argv
```

and whose `pattern-sinks` are `os.system(...)` and the `os.popen` family. Both
endpoints of **every** Python template in this document are bound by that one
shipped rule: `os.environ` for templates 1–4 and 6, `sys.argv` for template 5,
and `os.system` throughout. A seventh file,
`audit/dangerous-system-call-audit.yaml`, is the pure sink-existence rule this
document warned about — bare `os.system(...)` with only a literal-first-argument
exclusion, no taint anywhere.

Per-cell, with the retained-or-promoted decision stated for each:

| # | Template | Cat. | Preregistered | Now | Evidence read from rule text |
| --- | --- | --- | --- | --- | --- |
| 1 | `native-source-sink` | S | TBV | **scored** | `dangerous-system-call-tainted-env-args` binds `os.environ` as a source and `os.system` as a sink. The preregistered rationale — sources are framework-shaped — is true of `dangerous-system-call.yaml` and false of this rule. |
| 2 | `native-propagator` | P | TBV | **scored** | Same rule binds both endpoints; the `os.path.join` hop between them is propagation, and whether the shipped configuration carries a value across it is the measurement, not the activation. |
| 3 | `native-sanitizer` | Z | TBV | **scored** | Same rule binds both endpoints and declares **no** `pattern-sanitizers`. `shlex.quote` appears in the `dangerous-subprocess-use` and `dangerous-asyncio-*` families and in no rule that owns the `os.system` sink, so this cell is decidable and what it decides is where the credit is scoped. |
| 4 | `native-summary` | O | TBV | **scored** | Same rule binds both endpoints. The preregistered rationale — arg-to-return summary semantics are outside CE's propagator vocabulary — is about *declaring* a summary, which is a benchmark-controlled concern; this profile declares nothing and asks only whether the shipped configuration survives the round trip. |
| 5 | `native-entrypoint` | E | TBV | **scored** | Same rule's `pattern-sources` include `sys.argv` and `sys.orig_argv` literally. The preregistered rationale — entry conventions are framework-shaped — is answered by the snapshot in the negative. |
| 6 | `native-persistence` | B | TBV | **scored** | Same rule binds both endpoints. The preregistered rationale cited the absence of interprocedural taint in CE; this template's fixture writes and reads the store inside one function, so that limit is not what decides the cell. What decides it is whether the store read is treated as a keyed read or as a fresh source. |

Every promotion is decided from rule text over the pinned commit and recorded
here **before** the first Semgrep native scan of the Python population. That is
the sanctioned path this document preregisters — *to be verified at vendoring*
resolved by taking the snapshot and reading it — and not a result being
relabelled. A promoted cell can and does produce false negatives and false
positives; that is what scoring it means.

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report: the v0.4.0 claim is `benchmark-controlled` at the
`calibration`, `core`, and `language-extension` tiers, and this profile's
reports are new paths outside it.
