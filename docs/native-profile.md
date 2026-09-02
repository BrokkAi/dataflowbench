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
  [CodeQL](#codeql--cli-2264-shipped-security-suites)). Two profiles running on
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

### CodeQL — CLI 2.26.4, shipped security suites

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

### Semgrep CE — 1.175.0 (`--oss-only`), vendored official rulesets

> **Amended.** All six **Python** cells were promoted from *to be verified at
> vendoring* to scored by
> [Amendment A8](#a8--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension),
> on the evidence of the vendored snapshot's
> `audit/dangerous-system-call-tainted-env-args.yaml`, read before any scan.
> Java and JavaScript stay at 0 / 6, but no longer by default: their snapshots
> were vendored and read too, and
> [A6](#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot)
> and [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
> retain all twelve of those cells **on evidence**. A8 is also what keys the
> partition by language, which is what lets one language's snapshot answer only
> its own cells.
> [Amendment A27](#a27--2026-09-02-semgrep-ces-javascript-and-java-declines-are-re-grounded-on-enumeration-and-execution-and-their-settled-rationales-reach-the-runner)
> later re-grounded A6's and A7's rule-text readings on measurement — the
> vendored snapshots are the complete upstream `lang/security/` trees at the
> pinned commit, no rule anywhere in the upstream `javascript/`, `typescript/`,
> or `java/` trees at that commit binds `process.env`, `process.argv`, or
> `System.getenv`, and the pinned engine over all twenty-four fixtures emits
> zero findings — and mirrored the settled per-cell rationales into the
> runner's amendment table.

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
| 4 | O | **to be verified at vendoring — unsupported until shown** | Arg→return summary semantics are outside CE's propagator vocabulary on the pinned version, as [the modeling matrix established by execution](modeling-matrix.md#semgrep-ce--11750---oss-only); a shipped rule cannot supply what the engine does not express. |
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

### Bifrost — v0.10.8, shipped policy packs

**Activation contract.** Built-in policy packs only: `--policy-pack` /
`--policy-category` / `--policy-id` over the catalog `--list-policies` prints.
A native run may not pass `--policy-file`, which is how every
benchmark-controlled Bifrost run supplies its models, and the no-benchmark-models
gate refuses one.

**Grounded in the adapter README and the vendor's own issue tracker.** The
adapter README states the surface gap directly: *"External semantic-model
activation requires an embedding with an explicit catalog, so the
modeled-external case is reported as `unsupported` by this CLI adapter with an
explicit retained reason. It is not a negative result."*
(`adapters/bifrost/README.md`). A second README sentence — *"Sanitizer lowering
is a future Bifrost CLI capability"* — was quoted here when this profile was
preregistered; it was measured false and retired by
[Amendment A9](modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false),
and this document's category-Z cell was restated on the grounds that survive by
[Amendment A10](#a10--2026-08-28-bifrosts-native-category-z-cell-is-restated-on-the-absent-endpoint-catalog).
On the vendor side,
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

**Verification note.** The build pinned when this document was written —
v0.10.6, since re-pinned to v0.10.8 — was not available at the time; a locally
installed **v0.9.5** was inspected. Its
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
| 3 | Z | **unsupported — no shipped endpoint catalog, and no shipped sanitizer** ([A10](#a10--2026-08-28-bifrosts-native-category-z-cell-is-restated-on-the-absent-endpoint-catalog)) | Preregistered on `adapters/bifrost/README.md`'s *"Sanitizer lowering is a future Bifrost CLI capability"*, which [Amendment A9](modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false) measured false and retired; A10 restates the same outcome on the grounds that survive it. The sanitizer stanza A9 measured is reachable only through `--policy-file`, which this profile's activation contract forbids, and the built-in packs declare no sanitizer, no source, and no sink for one to sit between (#2620). A barrier on a flow that cannot start is unobservable either way. |
| 4 | O | **unsupported — external activation requires an embedding catalog** | `adapters/bifrost/README.md`, and bifrost-dev #2691 is the issue that would change it. |
| 5 | E | **to be verified — unsupported until shown** | No entry-root convention is described anywhere for the policy CLI. |
| 6 | B | **to be verified — unsupported until shown** | No persistence-boundary vocabulary is described for any adapter, Bifrost included. |

Bifrost enters with **zero of six**. That is the honest starting position for a
standalone policy CLI whose model surface lives in an embedding, it is the same
position the benchmark-controlled matrix recorded for five of its six categories,
and stating it in a preregistration published by Bifrost's own vendor — before a
run, with the vendor's open issues named — is the point.

### Joern — 4.0.614, `DefaultSemantics` only

**Activation contract.** Whatever the distribution activates without a
user-authored query or semantics file. Concretely: `DefaultSemantics`, and
nothing else. No benchmark `.semantics` file may load, and the
no-benchmark-models gate refuses `adapters/joern/semantics/model-*.semantics`
and the shared `adapters/joern/queries/modeling.sc`.

**What `DefaultSemantics` actually ships — verified.** Decompiled from
`io.joern.dataflowengineoss-<version>.jar` in a locally installed distribution
(**4.0.432**, not the pinned 4.0.614; the class surface is expected to be
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

**And the scan bundle decides nothing over these probes — measured.**
([Amendment A26](#a26--2026-09-02-joerns-native-decline-is-re-grounded-on-a-field-evaluation-of-the-shipped-scan-bundle).)
The paragraph this replaces declined the scan surface on packaging:
`joern-scan` is present in the distribution, but its query database is not —
`JoernScan` downloads `querydb.zip` from
`https://github.com/joernio/joern/releases/latest/download/querydb.zip`, and
a floating `latest` asset is unpinnable at run time. Half of that claim was
measured false: the same binary carries a **versioned** URL template, and the
shipped `joern-scan --updatedb --dbversion 4.0.614` installs the
`querydb.zip` published as an asset of the pinned release itself
(digest retained). The bundle is pinnable after all, so the decline no longer
rests on unpinnability — the retired sentence is kept above rather than
dropped, per this document's own discipline. What the decline rests on now is
the pinned bundle's content and behavior, field-evaluated: fifty-eight
queries in six languages (27 `c`, 10 `android`, 9 `php`, 7 `java`, 3
`kotlin`, 2 `ghidra` by the bundle's own dump), **none for JavaScript and
none for Python**, no query binding any probe endpoint, and zero findings of
any query over all thirty-six probe fixtures —
the source-sink positives included. A vendored `querydb` snapshot under
[the vendoring provenance rule](#provenance-for-vendored-activation-artifacts)
remains possible and would move nothing: the enumeration is exactly what it
would re-establish.

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **unsupported — `DefaultSemantics` ships no source or sink catalog, and the pinned scan bundle expresses no taint question over the probe endpoints** ([A26](#a26--2026-09-02-joerns-native-decline-is-re-grounded-on-a-field-evaluation-of-the-shipped-scan-bundle)) | Verified by decompilation: flow constraints only. Supplying endpoints would be a benchmark-authored model, which the activation rule forbids. And the version-pinned `joern-scan` bundle, installed and executed, fires no query on any probe cell: its one query naming this profile's command sink (`call-to-exec`) filters the method-name property with a full-match regex and matches zero methods on a `javasrc2cpg` graph, measured on the graph whose `exec` call is present. |
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

### Infer — v1.3.0, shipped Pulse checker with no taint configuration

> **Added by [Amendment A14](#a14--2026-09-01-infers-native-row-declines-on-a-measured-silence)
> (2026-09-01).** A new adapter's activation row, added by amendment before its
> first native run, decided from a **measured silence** rather than an assumed
> one, with the evidence retained under
> `reports/raw/amendment-a14-infer-native-silence/` (produced by
> `scripts/probe-infer-native-silence.sh`). Java alone: the pinned distribution
> executes no JavaScript or Python frontend, so those languages have no Infer
> native denominator at all — different from a 0 / 6 decline, and the runner
> refuses to shape a run for them.

**Activation contract.** The shipped product as shipped:
`infer analyze --pulse-only --sarif`, and **no** `--pulse-taint-config`. The
benchmark-controlled populations supply their models through that flag, so the
no-benchmark-models rule is the absence of the flag itself.

**Why the silence is measured, not swallowed.** The pinned release has a
documented silent-failure mode — a mis-pathed `--pulse-taint-config` is
silently ignored, exit zero, empty report — that could make an asserted
decline indistinguishable from a swallowed misconfiguration. The probe removes
that ambiguity by construction: it passes no configuration argument at all, so
there is nothing to mis-path, and it retains the exact argv beside every
verbatim SARIF. Over all twelve Java native fixtures the shipped product
produced **zero findings of any rule**. The one always-enabled policy
(Simple→Simple, quoted from the binary's own help text and retained beside the
probes) has no shipped Java source or sink bound to its kinds, so it decides
nothing.

**And the silence is engaged, not merely empty — measured.**
([Amendment A28](#a28--2026-09-02-infers-native-decline-is-re-grounded--the-shipped-taint-bundle-is-loaded-unconditionally-and-holds-no-endpoint).)
A14's phrase "Pulse taint is off absent a configuration" was imprecise in a
direction a maintainer challenge exposed: the pinned distribution **does**
bundle default taint data, and a zero-configuration invocation **does**
activate it. The release ships `lib/infer/infer/config/taint/` — four
Objective-C `NSLib` files whose own bundled README states they "are always
included when running infer" — and the loader was proven live rather than
read: corrupting one bundled file in a byte-copy of the distribution kills a
zero-config Java *capture* with a parse error naming the file from
`Config.pulse_taint_config`'s directory fold (exit 3). The bundle is parsed
unconditionally on every invocation. What it contains is the reason the
engagement decides nothing: every file declares `pulse-taint-propagators`
**only** — no source, no sink, no sanitizer, no policy, and no Java identity
anywhere in the shipped tree (no `.inferconfig` ships either, enumerated
distribution-wide). Propagators without endpoints form no taint question, and
no Objective-C selector ever matches a Java procedure. The full default
surface was also executed: `infer run --sarif` — the release's whole default
checker set, not the adapter's `--pulse-only` arm — over all twelve fixtures
produced zero findings of any rule, taint-shaped or otherwise, so no non-taint
Pulse finding exists to reconcile against any anchor and there is no live
activation deciding `not-reached`. The evidence is retained under
`reports/raw/amendment-a28-infer-native-activation/`
(`scripts/probe-infer-native-activation.sh`).

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **unsupported — the shipped taint bundle is loaded unconditionally and holds no endpoint** ([A28](#a28--2026-09-02-infers-native-decline-is-re-grounded--the-shipped-taint-bundle-is-loaded-unconditionally-and-holds-no-endpoint)) | Measured twice: zero findings of any rule on both cells with no configuration path passed (A14), and the zero-config activation proven engaged — the bundled `config/taint/` tree parses on every invocation, declares Objective-C propagators only, and binds no source, sink, or policy in any language (A28). `infer run`'s full default checker set decides nothing either. |
| 2 | P | **unsupported — same engaged-and-silent measurement** | The one thing the release *does* ship natively is propagators — Objective-C `NSLib` rows a Java procedure can never match — and a propagator needs a shipped source and sink to carry anything between; the release ships neither, in any language ([A28](#a28--2026-09-02-infers-native-decline-is-re-grounded--the-shipped-taint-bundle-is-loaded-unconditionally-and-holds-no-endpoint)). |
| 3 | Z | **unsupported — same measured silence** | The sanitizer surface [A13](modeling-matrix.md#a13--2026-09-01-infer-joins-the-modeling-matrix-with-a-field-evaluated-partition-row) measured load-bearing is reachable only through `--pulse-taint-config`, which this profile's activation contract supplies nothing through; and no endpoints ship for a barrier to sit between. |
| 4 | O | **unsupported — same measured silence** | No shipped summary catalog; the taint question itself is off. |
| 5 | E | **unsupported — same measured silence, doubly out of reach** | The shipped product activates no taint question, and A13 measured that the pulse-taint surface has no entry-root vocabulary even when configured. |
| 6 | B | **unsupported — same measured silence, doubly out of reach** | No store vocabulary exists even when configured (A13). |

Infer enters with **zero of six** — the same statement about product packaging,
not engine, that Joern's row makes: the benchmark-controlled matrix scores the
same binary on three of six categories, and the gap between the two rows is
what this profile exists to make legible. Its 0 / 6 run still witnesses its
identity from the binary,
[as every 0 / 6 run must](#the-run-level-identity-is-witnessed-including-at-0--6).

### Pysa — pyre-check 0.10.0 + Pyrefly 1.2.0, shipped taint model suite

> **Added by [Amendment A17](#a17--2026-09-01-pysa-joins-the-tool-native-profile-with-a-live-activation-row).**
> This row was not part of the preregistration, which merged before the Pysa
> adapter existed; it arrives the way the modeling matrix's amendment rows
> do, dated before the adapter's first native run, with its activation
> evidence retained under `reports/raw/amendment-a17-pysa-native/`
> (`scripts/probe-pysa-native-activation.sh`). Its scope is **Python only**,
> the engine's one language.

**Activation contract.** The pinned pyre-check wheel ships a real model suite
inside its own distribution: `lib/pyre_check/taint/` carries
`core_privacy_security/` — a `taint.config` declaring 27 source kinds, 33
sink kinds, and 35 rules, beside the stdlib and framework `.pysa` model files
that bind them — and `common/`, the propagation models for builtins and
collections. A native run points `taint_models_path` at that shipped
directory and nothing else, and passes `--no-verify`. Both halves of that
shape were established by probe, and both are retained:

- **The shipped product refuses to run with no model path** (`Found 1 taint
  configuration error!`): there is no ambient default, so pointing the
  documented `taint_models_path` knob at the wheel's own suite *is* the
  activation. It is a configuration of shipped models, the same kind of
  switch as CodeQL's `--threat-model=local`; it adds no row of ours, so it
  satisfies [the activation rule](#the-activation-rule).
- **The shipped suite does not verify over a stdlib-only project** (`Found
  122 model verification errors!` — its framework models name definitions a
  dependency-free fixture does not carry), and the client's own remediation
  hint names `--no-verify`. The flag is therefore part of the pinned
  invocation, and the activation proof moves from the verifier into the
  retained evidence: every native run's `taint-output.json` must carry the
  shipped model binding for `os.system`, the RemoteCodeExecution sink every
  Python native template sinks through, or the run is a `runner-error` rather
  than a coverage result.

The benchmark-authored artifacts — `adapters/pysa/taint.config`,
`adapters/pysa/models/kernel-python.pysa`, and the modeling artifact — are
never loaded: the no-benchmark-models gate covers the Pysa invocation shape
exactly as it covers the other four.

**What the shipped suite was read to contain**, before any native fixture was
scanned. `rce_sinks.pysa` binds `os.system`, `subprocess.*`, `eval`, and
`exec` as RemoteCodeExecution sinks; `general.pysa` binds framework request
objects and `argparse.ArgumentParser.parse_args` (kind `CLIUserControlled`)
as sources; `sanitizers.pysa` declares `@Sanitize` entities; `common/` ships
builtin and collection propagation. What the suite does **not** contain is a
source model for a bare `os.environ` read or a bare `sys.argv` subscript —
the shipped source catalog is framework-shaped, plus `argparse` for the
command line. All six templates are scored — the suite ships models in every
category's role, so there is an activation for each cell to measure — and the
honest expectation, stated in advance exactly as
[the template expectations](#the-six-native-templates) require, is that the
missing platform sources will cost every positive whose flow starts at
`os.environ` or `sys.argv`. That is a product fact about a security suite
aimed at framework-served code, published as the measurement, never
re-labelled as a benchmark defect or an engine failure.

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **supported** | `os.system` verified bound from the shipped `rce_sinks.pysa` under the pinned activation (retained probe). Whether any shipped source binds the environment read is the measurement. |
| 2 | P | **supported** | `common/` ships propagation models and the engine summarizes stdlib bodies it can read; whether the chain survives `os.path.join` from an uncovered source is the measurement. |
| 3 | Z | **supported** | The shipped suite declares sanitizers (`sanitizers.pysa`); whether `shlex.quote` is credited in the rule family that owns this sink is the measurement. |
| 4 | O | **supported** | The suite ships procedure summaries; whether the base64 round trip is covered is the measurement. |
| 5 | E | **supported** | The shipped command-line convention is `argparse` (`CLIUserControlled`), read before any scan; whether it extends to a bare `sys.argv` subscript is the measurement. |
| 6 | B | **supported** | `os.putenv` carries a shipped model and the suite runs over the store's APIs; whether a write-read pair is linked is the measurement. |

Pysa enters with **six of six templates scored**, and — stated in advance so
the column cannot later be read backwards — with the expectation of a
near-blind-baseline score, because the shipped source catalog does not cover
the platform reads these fixtures start from. A 6 / 6 activation surface and
a low score are not in tension; they are precisely the two facts this profile
exists to keep separate.

### FlowDroid — 2.15.1, shipped catalog and default summaries (Java only; added by Amendment A19)

> **Added by [Amendment A19](#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence)**:
> the adapter joined the benchmark after this document's preregistration, so
> its activation contract and its six cells arrive as a dated amendment, on
> the evidence of the shipped catalog's own text, before any native run. The
> row applies to **Java alone** — the analyzer consumes JVM bytecode packaged
> as an APK, so the JavaScript and Python native populations are outside its
> language reach entirely.

**Activation contract.** The release's shipped model surface, and nothing of
ours: the vendor's documented default sources-and-sinks catalog — *"you can
use our default file \"SourcesAndSinks.txt\""* (the release README) — which
ships **inside** the pinned, digest-witnessed
`soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar`, plus the release
default taint wrapper (StubDroid over the jar's bundled `summariesManual`
summaries). The released CLI refuses to run without `-s` — verified: omitting
it produces the zero-exit failure banner *"No source/sink file specified for
the data flow analysis"* — so the activation shape extracts the bundled
catalog from the jar **verbatim** and points the mandatory flag at it. That
is configuration of shipped models, not supply of ours: every model byte
comes from the pinned artifact, whose digest gates the run, which is why no
vendored snapshot and no `provenance.json` exist for this row — the jar pin
*is* the provenance, stronger than any retrieval record.

**The cells, decided from the catalog's text.** The shipped catalog is 460
lines — 176 source entries, 227 sink entries — of servlet, Spring, Android,
and assorted library identities. It binds this profile's command sink
(`<java.lang.Runtime: java.lang.Process exec(java.lang.String)> -> _SINK_`
is in the catalog), and it binds **no source any native template uses**:
`System.getenv` does not occur in it, nor does `System.getProperty`,
`sys.argv`'s Java analogue (a `main` parameter), or any other identity the
six fixtures read. The bundled summaries cover `String.concat` and
`System.getProperty` (as key→return taint — a propagator on the key, not a
store link) and omit `java.util.Base64`; the catalog's txt format has no
sanitizer role at all. A catalog with a bound sink and no applicable source
cannot produce a finding on these fixtures, which is the same shape
[A6](#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot)
and [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
retained Semgrep's JavaScript and Java cells on — so all six templates are
**unsupported on shipped-model evidence**, per cell in `NATIVE_PARTITION`
(`src/main.rs`), and FlowDroid enters this profile at **0 / 6** with a live
activation contract behind the zero.

**And the fuller shipped surface decides the same way — enumerated and
executed.**
([Amendment A29](#a29--2026-09-02-flowdroids-native-decline-is-re-grounded-on-the-shipped-surfaces-full-enumeration-and-executed-engagement).)
A maintainer challenge asked whether the catalog-text ruling above had
engaged everything the release ships, or only the default file. The answer,
retained under `reports/raw/amendment-a29-flowdroid-shipped-surface/`
(produced by `scripts/probe-flowdroid-native-shipped-surface.sh`): the
pinned jar bundles exactly five declarative surfaces beyond its classes —
`SourcesAndSinks.txt` (the **only** endpoint catalog instance in any format;
the bundled `schema/SourcesAndSinks.xsd` defines an XML catalog format, but
no XML instance ships), the EasyTaintWrapper defaults
(`EasyTaintWrapperSource.txt`: 435 propagation entries, 12 excludes, 5
kills, 4 include prefixes — the format has no source or sink role), the
callback list (`AndroidCallbacks.txt`), the virtual-edge callgraph model
(`virtualedges.xml`), and the 347-class StubDroid `summariesManual` set. No
surface anywhere in the artifact binds `System.getenv` — the only `getenv`
bytes in the whole jar are three shaded third-party classes that *call* it
at tool runtime — and executed over all twelve Java native fixtures with the
shipped catalog engaged (which parses to 71 sources and 193 sinks; 14
malformed vendor lines are rejected by the release's own parser), the
analyzer reports **"Found 0 leaks from 0 sources"** on every fixture,
aborting at source lookup each time. A control run — the same APK, the same
invocation, the shipped catalog plus a single benchmark-authored `getenv`
source line — finds exactly the floor leak, attributing every zero to the
shipped catalog and to nothing else.

### OpenTaint — `analyzer/2026.08.27.17eb0fe`, shipped models archive only (Java only)

> **Added by [Amendment A23](#a23--2026-09-01-opentaint-joins-the-tool-native-profile-at-0--6-and-the-shipped-models-archive-is-ruled-shipped-product).**
> This row was not part of the original preregistration — the adapter did not
> exist when it merged — and it joins on the same terms every row here holds
> to: decided from the pinned release's own assets, by execution, before any
> native run, with the evidence retained.

> **Amended.** [A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)
> re-grounds all six of this row's declines. A23's ground — *the pinned
> release ships no rule set* — was true of the release's two assets and
> incomplete about the shipped product: the vendor's `opentaint` CLI, the
> entry point its own demo documents (`opentaint scan`), defaults to
> `--ruleset builtin` and activates a versioned, digest-pinnable rules
> release through the same `--semgrep-rule-set` flag. That rule set is
> shipped product. Field-evaluated against the pinned analyzer over all
> twelve Java native fixtures, it loads cleanly and stays silent on every
> one — it binds this profile's command sink and no source any template
> reads — so every cell below stays `unsupported`, on measured evidence
> rather than on the absence of a rule set.

**Language scope.** Java only — the one wave-N1 language the pinned engine
analyzes. JavaScript and Python have **no OpenTaint native denominator at
all**, which is different from a zero, and the runner refuses to plan an
OpenTaint native run for either. Kotlin has no native population in any
adapter.

**Activation contract, and the boundary it settles.** The pinned release ships
exactly two assets: the analyzer jar and `opentaint-models.tar.gz`. The
archive is ruled **shipped product**, not benchmark-supplied configuration —
it is vendor-authored, versioned and digest-pinned in the same release as the
analyzer, and it is this tool's exact analogue of the standard-library rows
CodeQL's packs bundle and the flow-constraint table inside Joern's
`DefaultSemantics`. Nothing in it was written by this benchmark, which is the
only thing [the activation rule](#the-activation-rule) forbids. A native
OpenTaint run therefore loads the archive through the pinned
`--passthrough-approximations` / `--java-dataflow-approximations` flags — and
supplies **no `--semgrep-rule-set`**, because the rule set is where every
source, sink, and sanitizer lives, the benchmark's rules are
benchmark-authored by definition, and the pinned release ships none of its
own.

**What the shipped assets activate, verified by execution.** The archive's
contents are `passThrough`/`copy` propagation rows, accumulated-field
approximations, and compiled dataflow-approximation classes — it declares no
source, no sink, and no sanitizer anywhere. Run over the committed Java
`native-source-sink-positive` fixture (`System.getenv` into `Runtime.exec`,
the floor of this profile) with the archive loaded and no rule set, the pinned
analyzer registers **zero rules and reports zero results**
(`scripts/probe-opentaint-native-activation.sh`, retained under
`reports/raw/opentaint-native-activation-probe/`). The upstream repository
does develop a rules component (MIT-licensed), but it is not an asset of the
pinned analyzer release; a vendored snapshot of it is a possible future
amendment under [the vendoring provenance rule](#provenance-for-vendored-activation-artifacts),
exactly as Semgrep's registry rulesets were vendored, and it is not part of
this row.

**What the shipped scan entry point activates, field-evaluated
([A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)).**
The vendor's shipped `opentaint` CLI drives the same analyzer jar, and its
`scan` command — the invocation the vendor's own demo repository documents —
defaults to `--ruleset builtin`, resolved to the vendor's versioned rules
release and passed through the same `--semgrep-rule-set` flag every
benchmark-controlled run uses. That rule set is shipped product on exactly
A23's own reasoning, so the six declines cannot rest on "no rule set ships";
they rest on what the shipped rules bind, measured. The newest rules release
at the analyzer's pin date, `rules/v0.3.0` (asset `opentaint-rules.tar.gz`,
SHA-256 `3d789c9986479fec792333329abe737eccb15bc06fc59a978a58810118ca1d21`),
was run against the pinned analyzer over all twelve Java native fixtures with
the models archive loaded, at every severity — a superset of the CLI's
warning-and-error default. The retained result
(`scripts/probe-opentaint-scan-activation.sh`,
`reports/raw/amendment-a25-opentaint-scan-activation/`): 86 rules registered,
zero load errors in every retained rule-load trace, **zero results on all
twelve fixtures** — and a positive control carrying the real
`jakarta.servlet.http` identities fires the shipped `os-command-injection`
rule under the identical invocation, so the silence is a source-coverage
fact, not a dead harness. The rule set binds `Runtime.exec` as a
command-injection sink; every source rule in it is servlet-, Spring-, or
Seam-shaped, and nothing names `System.getenv`, a `main` parameter, or
`System.getProperty` as a source.

| # | Category | Decision | Rationale |
| --- | --- | --- | --- |
| 1 | S | **unsupported — the shipped rule set binds no platform source** ([A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)) | Originally declined because the release ships no rule set; the shipped scan entry point's builtin rule set was then field-evaluated. It binds `Runtime.exec` as a command-injection sink and no source rule in it names `System.getenv` — every source is servlet-, Spring-, or Seam-shaped. Measured: rules loaded clean, zero results on both cells, control fired. The same bound-sink-no-applicable-source shape [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot) and [A19](#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence) retained cells on. |
| 2 | P | **unsupported — propagation with no applicable source carries nothing** ([A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)) | The models archive's propagation rows and the rule set's join machinery both activate — the control's flow crosses them — but no shipped source binds the environment read this template's flow starts from. Measured silent on both cells. |
| 3 | Z | **unsupported — no flow for a barrier to be observable against** ([A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)) | Sanitizer credit is per-rule in the shipped set, and no shipped rule starts a flow at the environment read for `Integer.parseInt` to suppress. Measured silent on both cells. |
| 4 | O | **unsupported — shipped summaries behind no applicable source** ([A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)) | The archive's approximation classes are exactly template 4's round-trip material, and they activate — behind a source the shipped rule set does not bind. Measured silent on both cells. |
| 5 | E | **unsupported — the shipped entry conventions are framework-shaped** ([A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)) | The rule set's source conventions are servlet handler methods and Spring mapping annotations, not `main(String[])`; entry-point *selection* (`--debug-run-analysis-on-selected-entry-points`) analyzes a method without tainting its parameters. Measured silent on both cells. |
| 6 | B | **unsupported — no shipped store link** ([A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)) | No store vocabulary ships in any asset or rule. Measured silent on both cells. |

OpenTaint enters this profile with **zero of six**, and — as with Joern — that
is a statement about the pinned release's *product packaging*, not about its
engine: the benchmark-controlled matrix scores the same binary on three of six
categories ([Amendment A22](modeling-matrix.md#a22--2026-09-01-opentaint-joins-the-modeling-matrix-with-a-preregistered-java-partition-row)),
and the gap between those two rows is exactly what this profile exists to make
legible.

### Partition summary

Preregistered before any native fixture exists or any ruleset is vendored.
`TBV` = to be verified at implementation or at vendoring, treated as unsupported
until shown otherwise.

> **Amended.** This table is the preregistered default and stays as written.
> Wave N1 discharged every Semgrep CE *to be verified at vendoring* cell against
> a vendored snapshot:
> [A6](#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot)
> retains JavaScript's six,
> [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
> retains Java's six, and
> [A8](#a8--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension)
> promotes Python's six to scored and keys the partition by language.
> [A27](#a27--2026-09-02-semgrep-ces-javascript-and-java-declines-are-re-grounded-on-enumeration-and-execution-and-their-settled-rationales-reach-the-runner)
> re-grounds A6's and A7's retained cells on enumeration and execution and
> gives them their own amendment rows, so the runner's rationale strings say
> what those amendments decided. Every cell for every language with no
> amendment row is still the cell below.

| # | Template | Cat. | Bifrost v0.10.8 | CodeQL 2.26.4 | Joern 4.0.614 | Semgrep CE 1.175.0 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `native-source-sink` | S | unsupported | supported | unsupported | TBV |
| 2 | `native-propagator` | P | unsupported | supported | unsupported | TBV |
| 3 | `native-sanitizer` | Z | unsupported | supported | unsupported | TBV |
| 4 | `native-summary` | O | unsupported | supported | unsupported | TBV |
| 5 | `native-entrypoint` | E | TBV | supported | unsupported | TBV |
| 6 | `native-persistence` | B | TBV | supported | unsupported | TBV |
| | **Scored today** | | **0 / 6** | **6 / 6** | **0 / 6** | **0 / 6** |

#### Adapters added by amendment

A new adapter never splices a column into the preregistered table above — its
four columns are frozen as written. An amendment-added adapter instead appends
**one row** to the table below, so concurrent adapter amendments compose
without rewriting each other's cells; the columns are the six templates in
order, and each row's amendment carries the activation contract and the
evidence.

| Adapter (amendment, language scope) | 1 S | 2 P | 3 Z | 4 O | 5 E | 6 B | Scored |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Infer v1.3.0 ([A14](#a14--2026-09-01-infers-native-row-declines-on-a-measured-silence), Java only) | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | 0 / 6 |
| Pysa 0.10.0 + Pyrefly 1.2.0 ([A17](#a17--2026-09-01-pysa-joins-the-tool-native-profile-with-a-live-activation-row), Python only) | supported | supported | supported | supported | supported | supported | 6 / 6 |
| FlowDroid 2.15.1 ([A19](#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence), re-grounded by execution in [A29](#a29--2026-09-02-flowdroids-native-decline-is-re-grounded-on-the-shipped-surfaces-full-enumeration-and-executed-engagement), Java only) | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | 0 / 6 |
| OpenTaint 2026.08.27 ([A23](#a23--2026-09-01-opentaint-joins-the-tool-native-profile-at-0--6-and-the-shipped-models-archive-is-ruled-shipped-product), re-grounded by [A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence), Java only) | unsupported | unsupported | unsupported | unsupported | unsupported | unsupported | 0 / 6 |

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

### The run-level identity is witnessed, including at 0 / 6

"Before the tool is invoked" is a statement about **cells**, and it is
unconditional: no declined cell is ever handed to the analyzer, and no run of
this profile decides an outcome by looking at one.

It is *not* a statement about the report's `tool_version` and
`tool_build_identity`. Those name which binary the run was pinned to, and a
name is only evidence if something read it. Every run of this profile therefore
reads the pinned binary's version banner **once**, before its population is
walked, including a row whose partition scores nothing — and a row that scores
nothing is the case where it matters most, because there its twelve retained
rationales are the whole of its evidence and an asserted version would go on
naming the previous pin after the binary underneath it moved.

Reading `--version` is not analyzing a fixture, so this leaves the distinction
above untouched: `unsupported` is still decided from the template identity
before anything runs. What it removes is a report that could state a pin it
never observed. One consequence is deliberate and worth stating plainly: a
0 / 6 run no longer completes against a nonexistent binary path — it fails,
because a run that cannot witness its own pin has nothing truthful to write in
those two fields.

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

> **Wave N1 is complete.** [JavaScript](javascript-native.md),
> [Java](java-native.md), and [Python](python-native.md) have each landed their
> twelve assertions, their vendored snapshot, and their runs, and A6, A7, and A8
> record the evidence. That closes issue #16. All three languages now have a
> native denominator; the ten below still have none.

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

Their numbers continue the repository's **single** amendment sequence rather
than restarting per document, so an identifier names exactly one amendment
wherever it is cited and this document's own numbering is deliberately gappy.
Each amendment-bearing document holds only its own entries, and no document
keeps a list of where the other numbers live: the authoritative index is the
set of `### A<n>` headings across the five amendment-bearing documents
([the challenge tier](challenge-tier.md#amendments),
[the modeling matrix](modeling-matrix.md#amendments), this one,
[the adapter contract](adapters.md#amendments), and
[the latency tier](latency-tier.md#amendments)), and a new amendment takes the
first number no heading anywhere claims. Concurrent pull requests can still
race for a number; the loser renumbers at merge, which is cheaper than every
amendment editing five cross-lists. The sequence interleaves across documents
— the number, not the document, is the identity.

### A6 — 2026-08-27: Semgrep CE's JavaScript cells, evaluated against the vendored snapshot

**What changed.** Semgrep CE 1.175.0's six *to be verified at vendoring* cells
are resolved for **JavaScript only**. All six are **retained as unsupported**.
No cell is promoted, no decision flips, and the
[partition summary](#partition-summary) is unchanged: what changes is that the
JavaScript column's rationale is now settled evidence about a pinned snapshot
rather than an open question about one that did not exist.

**Templates and languages touched.** All six —
`dfb-template-native-source-sink`, `-propagator`, `-sanitizer`, `-summary`,
`-entrypoint`, `-persistence` — for `javascript` alone. Java's and Python's
cells stay open and are answered by their own waves.

**Freezes invalidated.** None. No published freeze contains a tool-native
report.

**Evidence.** The snapshot vendored to `adapters/semgrep/native/javascript/`
from `semgrep/semgrep-rules` at commit
`40b8c63f75dc7c22c8a77482d73bfb864b146f7e` — thirty `.yaml` rule files from
`javascript/lang/security/`, the path
[the preregistration names](#semgrep-ce--11750---oss-only). The evaluation
below is a reading of the vendored rule text, made before Semgrep was invoked
over any native fixture, which is the order
[the vendoring rule requires](#provenance-for-vendored-activation-artifacts).

**The finding that decides all six cells.** Fifteen of the thirty vendored
rules are `mode: taint`; the other fifteen are pattern rules. Every one of the
fifteen taint rules roots its `pattern-sources` in a **function parameter or a
framework request object**, and not one names a platform environment, argument,
or process-store identity. `detect-child-process.yaml` and
`audit/dangerous-spawn-shell.yaml` — the two rules whose *sinks* are exactly
this profile's `child_process.execSync` — take
`function ... (...,$FUNC,...) { ... }` with `focus-metavariable: $FUNC` as their
only source. `audit/code-string-concat.yaml`, whose sink is the same family,
takes Express `$REQ.query`/`.body`/`.params`/`.cookies`/`.headers` and the
Next.js router. `audit/path-traversal/path-join-resolve-traversal.yaml`, whose
sink is `path.join`, takes a function parameter. A search of the whole snapshot
for `process.env`, `process.argv`, `encodeURIComponent`, and `Buffer.from`
returns nothing.

That is the shipped product's shape, and it is the shape the preregistration
predicted for Python: the official rules' entry conventions are
framework-shaped. A rule with a correct sink and no applicable source cannot
produce a finding on a fixture whose source is a platform API, so every one of
the six templates is declined for the same reason.

**Per cell.**

| # | Template | Cat. | Decision | Evidence from the vendored rule text |
| --- | --- | --- | --- | --- |
| 1 | `native-source-sink` | S | **retained unsupported — no shipped platform-source model** | `detect-child-process.yaml` binds the `child_process.execSync($CMD)` sink under `require('child_process')`, so the sink half is covered; its only `pattern-sources` entry is an enclosing function's parameter. Nothing in the snapshot binds `process.env`. |
| 2 | `native-propagator` | P | **retained unsupported — no shipped platform-source model** | `path-join-resolve-traversal.yaml` binds `$PATH.join(...,$SINK,...)` under `require('path')`; its source is a function parameter. With no source bound, the propagator has nothing to carry. |
| 3 | `native-sanitizer` | Z | **retained unsupported — no rule reaches this cell to credit or refuse the idiom** | `encodeURIComponent` appears nowhere in the snapshot. Sanitizer credit in the official rules is per-rule (`path-join-resolve-traversal.yaml` lists `$Y.replace`, `$Y.indexOf`, and a `sanitize`-named call), and no rule that could fire on this fixture exists to credit it either way. |
| 4 | `native-summary` | O | **retained unsupported — no shipped source, and no arg→return summary vocabulary** | Both halves of the preregistered rationale hold: no rule binds a platform source, and CE 1.175.0 does not express arg→return summaries, [as the modeling matrix established by execution](modeling-matrix.md#semgrep-ce--11750---oss-only). |
| 5 | `native-entrypoint` | E | **retained unsupported — the shipped entry convention is a function parameter, not `process.argv`** | The snapshot's universal source shape *is* an entry convention — it just is not the platform's. `process.argv` appears in no rule. |
| 6 | `native-persistence` | B | **retained unsupported — no store vocabulary, and no interprocedural taint** | No rule links a write to `process.env.<NAME>` to a read of it, and the pinned CE engine has no interprocedural taint (`--pro-intrafile` requires Pro). |

**Scored count, unchanged: 0 of 6 for JavaScript.** Under
[outcome honesty](#outcome-honesty) those twelve assertions are capability
coverage, never negatives, and they reduce no denominator.

**A note on the sink-existence hazard, which did not materialize here.** The
preregistration expected this profile's most likely observation to be a pattern
rule firing on sink existence and taking a false positive on a negative cell.
For JavaScript it does not: the two vendored rules that match
`child_process.execSync` are both taint rules, and the fifteen pattern rules
match other constructs entirely — `spawn(..., {shell: $SHELL})`,
`spawn('git', ['clone', ...])`, `Buffer` `noassert`, weak hashing. A negative
cell that passes a clean local variable to `execSync` is flagged by none of
them. The hazard remains preregistered for the other two languages, where the
upstream `audit/` rules are shaped differently.

### A7 — 2026-08-27: Semgrep CE's six Java cells are retained unsupported against the vendored snapshot

**What changed in the partition.** Nothing. All six Semgrep CE cells for
**Java** stay `unsupported`. What changes is their *status*: they were
`to be verified at vendoring`, and this amendment discharges that verification
for Java. The Java snapshot exists, it has been read, and it binds none of the
six categories. Semgrep CE's Java row is now unsupported **on evidence**
rather than unsupported **by default**.

**When the evaluation was made.** From the vendored rule text, before Semgrep
was invoked over a single Java fixture — and it never was, because a cell the
partition declines is answered before the binary is touched. Nothing below is
a result being relabelled.

**What was vendored.** `adapters/semgrep/native/java/rules/`: every rule
document (86 files, 86 rule IDs) beneath `java/lang/security/` of
`https://github.com/semgrep/semgrep-rules` at commit
`40b8c63f75dc7c22c8a77482d73bfb864b146f7e`, upstream directory structure
preserved, under the Semgrep Rules License v1.0, with
`adapters/semgrep/native/java/provenance.json` recording the repository, the
commit, the paths, the license, the retrieval date, and a SHA-256 per file.
The upstream tree's per-rule `*.java` files are Semgrep's own rule tests, not
part of the ruleset, and are deliberately not vendored.

**Per cell, with the evidence.**

| # | Cat. | Decision | Evidence from the vendored snapshot |
| --- | --- | --- | --- |
| 1 | S | **retained unsupported** | No vendored rule names `System.getenv` — the string does not occur in the snapshot at all. The two rules whose sink is this template's command API, `audit/command-injection-formatted-runtime-call.yaml` and `audit/command-injection-process-builder.yaml`, are pattern rules that bind no source. The one taint-mode rule that reaches `Runtime.exec`, `audit/tainted-cmd-from-http-request.yaml`, has `pattern-sources: (HttpServletRequest $REQ)`. No shipped rule binds a platform environment source. |
| 2 | P | **retained unsupported** | No vendored rule references `String.concat`. The concatenation-shaped rules (`command-injection-formatted-runtime-call`, `audit/formatted-sql-string.yaml`, `audit/jdbc-sql-formatted-string.yaml`) match `+` or `String.format` *inside a sink argument*; none declares a propagator step, and none binds a platform source for one to carry. |
| 3 | Z | **retained unsupported** | Sanitizer credit in the official rules is per-rule, and no vendored rule declares `Integer.parseInt` or `String.valueOf` as a sanitizer — neither identifier occurs in the snapshot. With no applicable rule at cells 1 and 2, there is also no rule inside which credit could be given. |
| 4 | O | **retained unsupported** | `java.util.Base64` does not occur in the snapshot. This confirms from rule text what [the modeling matrix established by execution](modeling-matrix.md#semgrep-ce--11750---oss-only): argument-to-return summary semantics are outside CE's propagator vocabulary on the pinned version, and a shipped rule cannot supply what the engine does not express. |
| 5 | E | **retained unsupported** | No vendored rule binds `main(String[] args)` or the argument vector; neither `void main` nor `System.` occurs anywhere in the snapshot. Every entry convention it carries is framework-shaped. |
| 6 | B | **retained unsupported** | No vendored rule names `System.setProperty` / `System.getProperty` as a store pair. The one `setProperty` sink shape in the snapshot, `audit/ognl-injection.yaml`, is bound to an `OgnlReflectionProvider` parameter. The pinned CE engine has no interprocedural taint, so an unlinked store round trip is carried by nothing else. |

**A related observation, recorded but not scored.** The
[sink-existence hazard](#sink-existence-only-findings-and-how-they-score) does
**not** materialize on Java's probe set: `command-injection-formatted-runtime-call`
requires `+` or `String.format` *within* the `exec` argument, and
`command-injection-process-builder` requires a `ProcessBuilder`, and the six
pinned Java fixtures use neither. A Semgrep run over them would have produced
nothing. That is not why these cells are retained — they are retained because
no rule binds the categories — and the distinction matters, because a cell
declined for lack of binding is capability coverage while an empty run would
have been a set of false negatives.

**Tools, templates, and languages touched.** Semgrep CE only; all six native
templates; **Java only**. JavaScript's and Python's Semgrep cells keep their
`to be verified at vendoring` status until their own snapshots land.

**Freezes invalidated.** None. No tool-native report is bound by any freeze.

### A8 — 2026-08-27: Semgrep CE's six Python cells are promoted to scored, and the partition gains a language dimension

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
   would have forced one language's evidence onto the other two. The mechanism
   is additive: `NATIVE_PARTITION_AMENDMENTS` carries one row per amended
   tool × language × template and is consulted before the preregistered table,
   which stays the default for every language with no amendment row. No
   preregistered cell's *decision* is altered by this change, and neither
   [A6](#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot)'s
   nor [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)'s
   retained rationales are touched.
2. **Semgrep CE 1.175.0 × Python: all six templates, `TBV`/unsupported →
   scored.**

**Which template IDs and languages.** All six —
`dfb-template-native-source-sink`, `-propagator`, `-sanitizer`, `-summary`,
`-entrypoint`, `-persistence` — for **Python only**. Java and JavaScript are
untouched and remain 0 / 6 for Semgrep on the evidence of A7 and A6. No other
tool's cells change; CodeQL stays 6 / 6, Bifrost and Joern stay 0 / 6.

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
exclusion, no taint anywhere. This is the language where
[the sink-existence hazard](#sink-existence-only-findings-and-how-they-score)
that A6 and A7 found dormant is live, and A6's note said so in advance.

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

**The execution arm lands with the promotion.** This document's own rule is
that a cell promoted by a dated amendment lands the runner that scores it in
the same pull request, rather than being answered by a synthesized outcome. The
Semgrep native arm therefore lands here — and it is not a second reconciler:
it classifies its findings against the same sink anchors the CodeQL arm uses
and tallies them through the same `native_anchor_tally_outcome`, so the two
adapters cannot drift into two readings of [outcome honesty](#outcome-honesty).

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report: the v0.4.0 claim is `benchmark-controlled` at the
`calibration`, `core`, and `language-extension` tiers, and this profile's
reports are new paths outside it.

### A10 — 2026-08-28: Bifrost's native category-Z cell is restated on the absent endpoint catalog

**What changed.** Nothing about the decision. Bifrost's category-Z template,
`dfb-template-native-sanitizer`, stays `unsupported` for all three languages,
Bifrost's activation count stays **0 / 6**, and no other cell of any tool is
touched. What changes is the *citation* the cell rests on.

**Why it had to change.** This document declined the cell by quoting the
adapter README — *"Sanitizer lowering is a future Bifrost CLI capability"* —
and
[Amendment A9](modeling-matrix.md#a9--2026-08-27-bifrosts-sanitizer-category-is-promoted-the-readmes-lowering-claim-was-false)
measured that sentence on the v0.10.7 build `44d9a5be416432bf8ed414afd3ea0031245ebb57`
and found it false: the RQLP `analysis` grammar accepts a `(sanitizer …)`
stanza, the declaration suppresses a flow on a run that completes, deleting it
restores that flow with a full witness, and an undeclared sanitizer-shaped
sibling is not suppressed. A9 promoted the *benchmark-controlled* category Z on
that measurement and said in the same breath that this document's cell quotes a
claim it had withdrawn, and that correcting it was this document's own dated
amendment to make. This is that amendment.

**Why the outcome does not move with the citation.** The two profiles ask
different questions of the same binary, and only one of them can reach the
stanza A9 measured. A sanitizer declaration arrives through `--policy-file`,
which [this profile's activation contract](#bifrost--v0108-shipped-policy-packs)
forbids outright and the no-benchmark-models gate refuses. What the built-in
packs ship is what remains, and they declare no sanitizer — and, prior to that,
no source and no sink for a sanitizer to sit between, which is the same absent
endpoint catalog (BrokkAi/bifrost-dev **#2620**, open) that decides templates 1
and 2. A barrier on a flow that cannot start is unobservable in either
direction, so the cell would be undecidable here even if the CLI shipped one.
The cell's grounds were always available; the preregistration reached for a
README sentence instead, and that is the error being corrected.

**Templates and languages touched.** `dfb-template-native-sanitizer`, for
`java`, `javascript`, and `python` — the rationale string is one constant
shared by all three. No template of any other tool changes, and the
[partition summary](#partition-summary) is unchanged.

**Where the wording now stands.** The [Bifrost row's rationale
table](#bifrost--v0108-shipped-policy-packs) and its mirrored constant in
`NATIVE_PARTITION` (`src/main.rs`) both name the endpoint-catalog grounds and
cite this amendment; the paragraph above the table records the retired sentence
as retired rather than dropping it, because a preregistration that quietly
loses the claim it was decided on is worse than one that was wrong.

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report. The retained tool-native reports predate this amendment and
carry the withdrawn wording in their retained rationales; the corrected string
lands with the next evidence re-run, and the decision those reports record —
`unsupported` — is the decision this amendment leaves in place.

### A14 — 2026-09-01: Infer's native row declines on a measured silence

**What changed.** The profile gains a fifth adapter's activation row. Infer
v1.3.0 — joining the benchmark-controlled modeling matrix in the same pull
request by [Amendment A13](modeling-matrix.md#a13--2026-09-01-infer-joins-the-modeling-matrix-with-a-field-evaluated-partition-row)
— takes a tool-native row of **0 / 6**, for **Java alone**: the pinned
distribution executes no JavaScript or Python frontend, so those languages
have no Infer native denominator at all, which is different from a 0 / 6
decline. No cell of any other adapter moves, and no template definition
changes. The full rationale table is
[the Infer activation section](#infer--v130-shipped-pulse-checker-with-no-taint-configuration)
above.

**Why the decline is a measurement.** The pinned release ships Pulse's taint
analysis **disabled absent a `--pulse-taint-config`** — and it also has a
documented silent-failure mode in which a *mis-pathed* configuration is
silently ignored, exit zero, empty report. An asserted decline could therefore
be a swallowed misconfiguration wearing a decline's clothes, which is exactly
what this document's outcome-honesty section exists to prevent. The evidence
removes the ambiguity by construction: `scripts/probe-infer-native-silence.sh`
ran the shipped product over all twelve Java native fixtures with **no
configuration argument at all** — nothing to mis-path — and retained, per
fixture, the verbatim SARIF, the exact argv, and the analyze exit status,
under `reports/raw/amendment-a14-infer-native-silence/`. Every one of the
twelve runs produced zero findings of any rule. The one always-enabled policy
(Simple→Simple, quoted from the binary's own help text and retained beside the
probes as `always-enabled-policy-help.txt`) has no shipped Java source or sink
bound to its kinds.

**What lands with the row.** `run-infer-native --language java`, on the
staged shape every declining row uses: the partition answers all twelve cells
before the binary touches a fixture, the run witnesses its identity from the
binary once
([the 0 / 6 witnessing rule](#the-run-level-identity-is-witnessed-including-at-0--6)
— the kernel witness, which refuses a binary that is not the pinned release),
and the execution arm stays a hard error, so a future amendment that promotes
a cell must land the arm that runs it. `run-infer-native` over `javascript` or
`python` refuses outright: no denominator, not a zero.

**Templates and languages touched.** All six native templates for the new
Infer column; `java` alone carries a denominator.

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report, and the v0.6.0 freeze is untouched.

### A17 — 2026-09-01: Pysa joins the tool-native profile with a live activation row

**What changed.** The profile gains a sixth adapter row. Pysa — pinned as the
pair pyre-check 0.10.0 + Pyrefly 1.2.0, the same pair the kernel and
[Amendment A16](modeling-matrix.md#a16--2026-09-01-pysa-joins-the-modeling-matrix-with-a-measured-partition-row)
run — takes the activation contract and per-template partition
[stated above](#pysa--pyre-check-0100--pyrefly-120-shipped-taint-model-suite):
all six templates scored, over the model suite the pinned wheel ships in
`lib/pyre_check/taint/`. The row is **Python-scoped**, the engine's one
language; no other language gains a Pysa native cell. The four preregistered
columns, the six template definitions, and every existing cell are untouched.

**Why it is an amendment and not an edit.** The preregistration merged before
this adapter existed. A new adapter's row arrives dated, before its first
native run, on the same terms the modeling matrix states for its partition —
and this profile's own history already keys amendments by language (A8),
which is the shape this row takes.

**What was measured, and what was only read.** Three activation facts were
measured by probe (`scripts/probe-pysa-native-activation.sh`, retained under
`reports/raw/amendment-a17-pysa-native/`): the shipped product refuses to run
with no `taint_models_path` (exit 9, its own taint-configuration error), the
shipped suite refuses strict verification over a stdlib-only project (exit
10, 122 model verification errors, the client's own hint naming
`--no-verify`), and under the pinned activation the suite demonstrably binds
— the retained evidence carries the shipped `os.system` sink model. The
**cells** were decided by reading the shipped suite's rule and model text,
before any native fixture was scanned, exactly as A8 read the vendored
Semgrep snapshot: every category's role is present in the shipped catalog, so
every template has an activation to measure, and the absent platform sources
(`os.environ`, `sys.argv`) are recorded as the expectation the runs will
measure, not as a reason to decline a cell. No cell was decided from a scan
outcome, and no cell is declined at all.

**Tools, templates, and languages touched.** Pysa only; all six templates;
Python only, by the engine's own language scope.

**Freezes invalidated.** None. No published freeze binds a Pysa tool-native
report; v0.6.0 is untouched.

### A19 — 2026-09-01: FlowDroid joins the tool-native profile, with a live activation contract and six cells declined on catalog evidence

**What changed.** The profile gains its seventh adapter row. FlowDroid 2.15.1
takes a **Java-only** activation contract and a full six-cell partition
column, both stated in
[its activation section](#flowdroid--2151-shipped-catalog-and-default-summaries-java-only-added-by-amendment-a16)
and mirrored into `NATIVE_PARTITION` (`src/main.rs`). No existing tool's cell
moves. This is the companion of the modeling matrix's
[Amendment A18](modeling-matrix.md#a18--2026-09-01-flowdroid-joins-the-modeling-matrix-with-a-java-only-partition-row),
and it landed before the adapter's first native run.

**The boundary question, answered YES.** Unlike the four original rows, the
question of *whether this adapter has a native activation at all* needed an
argument, and it is recorded here either way, as the profile's discipline
requires. FlowDroid's released CLI takes its endpoint definitions through a
mandatory `-s` flag — verified in the field: omitting it fails with the
zero-exit banner *"No source/sink file specified for the data flow
analysis"* — so nothing activates *by default*. What decides the question is
that the release **ships the models themselves**: the vendor's README names
`SourcesAndSinks.txt` as *"our default file"*, that catalog is bundled inside
the pinned, digest-witnessed jar, and the default taint wrapper (StubDroid
over the jar's bundled `summariesManual`) engages with no flag at all.
Extracting the bundled catalog verbatim and pointing the mandatory flag at it
is configuration of shipped models — the same boundary reading that admits
CodeQL's `--threat-model=local` — and every model byte in such a run comes
from the vendor's pinned artifact. The activation contract is therefore
**live**: a run under it is the shipped product deciding. No vendored
snapshot exists for this row because none is needed — the jar digest the run
already witnesses is the provenance, and a catalog that cannot drift needs no
retrieval record.

**The cells, declined on the catalog's text.** Read before any run, from the
catalog extracted out of the pinned jar: 460 lines, 176 `_SOURCE_` entries,
227 `_SINK_` entries. The command sink is bound —
`<java.lang.Runtime: java.lang.Process exec(java.lang.String)> -> _SINK_` —
and no identity any native fixture *reads* is: `System.getenv` does not occur,
`System.getProperty`/`setProperty` do not occur, no `main` parameter or argv
convention occurs (the shipped entry convention is the Android component
lifecycle, and the JVM process-entry convention does not exist on the
analyzed platform), and the txt format carries no sanitizer role. The bundled
summaries supply propagation (`String.concat`; `System.getProperty` as
key→return taint — a propagator on the key, not a store link) but propagation
with no source carries nothing. Every cell is therefore declined for the same
first reason — *no shipped source binds a platform environment read* — with
the per-cell specifics retained verbatim in `NATIVE_PARTITION`. This is
precisely the evidence shape on which
[A6](#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot)
and [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
retained Semgrep's JavaScript and Java columns, and the same treatment is the
consistency this document owes its own precedent. A shipped catalog that
gains an environment source is a promotion by dated amendment, carrying the
new jar pin as its evidence.

**What the row still runs.** `run-flowdroid-native --language java` executes
under [the run-level identity rule](#the-run-level-identity-is-witnessed-including-at-0--6):
it witnesses the pinned jar and platform digests and the jar's self-reported
version before its population is walked, writes the twelve retained
`unsupported` decisions with the witnessed identity and the pinned activation
shape in each, and refuses to run at all against artifacts that do not match
the pins. A 0 / 6 row's retained rationales are the whole of its evidence,
which is exactly why the identity behind them is measured rather than
asserted.

**Templates and languages touched.** All six native templates; FlowDroid
only; **Java only** — the JavaScript and Python native populations are
outside the adapter's language reach (the analyzer consumes JVM bytecode),
so those combinations have no FlowDroid native denominator at all, and the
runner refuses them.

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report.

### A23 — 2026-09-01: OpenTaint joins the tool-native profile at 0 / 6, and the shipped models archive is ruled shipped product

**What changed.** The [activation partition](#partition-summary) gains an eighth row — OpenTaint, pinned release `analyzer/2026.08.27.17eb0fe` by asset
digest — for **Java only**, with all six templates **unsupported**: 0 / 6, the
same shape as Joern's row and for the same kind of reason. A new
[activation-contract section](#opentaint--analyzer2026082717eb0fe-shipped-models-archive-only-java-only)
records the contract and the boundary decision below. No preregistered cell of
any other tool moves. JavaScript and Python have no OpenTaint native
denominator at all — the engine analyzes JVM bytecode only — and Kotlin has no
native population in any adapter.

**The boundary question this amendment settles.** OpenTaint's pinned release
ships `opentaint-models.tar.gz` alongside the analyzer jar. Does that archive
count as *shipped product* (a native run activates it) or as
*benchmark-supplied configuration* (a native run declines it)? The activation
rule's own text answers: it forbids **benchmark-authored** declarations, and
nothing in the archive is benchmark-authored. The archive is vendor-authored,
versioned and digest-pinned in the same release as the analyzer, and is this
tool's analogue of the standard-library taint rows CodeQL's query packs bundle
and of the flow-constraint table inside Joern's `DefaultSemantics` — platform
propagation models, shipped with the product. **A native OpenTaint run
therefore loads the archive**, through the same pinned
`--passthrough-approximations` / `--java-dataflow-approximations` flags every
benchmark-controlled OpenTaint run uses. The line the activation rule actually
draws for this adapter is `--semgrep-rule-set`: the rule set is where every
source, sink, and sanitizer lives, the benchmark's rules are benchmark-authored
by definition, and the runner's no-benchmark-models gate refuses a native
invocation that names one. This is the same division Bifrost's row draws
between built-in packs (allowed) and `--policy-file` (forbidden).

**Why the row is still 0 / 6, on executed evidence.** Ruling the archive
shipped product does not put an endpoint in it. Its contents are
`passThrough`/`copy` propagation rows, accumulated-field approximations, and
compiled dataflow-approximation classes; no source, sink, or sanitizer is
declared anywhere in the release's assets, and the release ships no rule set.
Run over the committed Java `native-source-sink-positive` fixture —
`System.getenv` into `Runtime.exec`, the floor of this profile — with the
archive loaded and no rule set supplied, the pinned analyzer registers **zero
rules and reports zero results**. The evidence is retained under
`reports/raw/opentaint-native-activation-probe/`, produced by
`scripts/probe-opentaint-native-activation.sh` before any native run of this
adapter existed. Propagation with no endpoints carries nothing anywhere, so
every cell is `unsupported` before any fixture is handed to the analyzer — and
the run that records those decisions still witnesses the release assets'
digests, per
[the run-level identity rule](#the-run-level-identity-is-witnessed-including-at-0--6).

**What would move a cell.** The upstream repository develops a rules component
(MIT-licensed) that is not an asset of the pinned analyzer release. A future
amendment may vendor a pinned snapshot of it under
[the vendoring provenance rule](#provenance-for-vendored-activation-artifacts),
exactly as Semgrep's registry rulesets were vendored, and re-decide these cells
against what that snapshot actually binds. Nothing is vendored by this
amendment.

**The deliberate asymmetry, restated for this adapter.** The
benchmark-controlled matrix scores the same pinned binary on three of six
categories
([Amendment A22](modeling-matrix.md#a22--2026-09-01-opentaint-joins-the-modeling-matrix-with-a-preregistered-java-partition-row));
this profile scores it on none. That gap is product packaging versus engine
capability — the exact gap Joern's two rows already exhibit — and it is what
this profile exists to make legible, not a contradiction to reconcile.

**Templates and languages touched.** All six native templates, for `java`
alone, for OpenTaint alone.

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report, and the v0.6.0 manifest binds this adapter's two
propagation kernels and nothing else. The declined-cell report this row
entitles lands after this amendment, as post-freeze live evidence.

### A25 — 2026-09-02: the shipped `opentaint scan` entry point is field-evaluated, and the six native declines are re-grounded on its measured silence

**What changed.** No cell moves and no score changes: OpenTaint's Java row
stays 0 / 6. What changes is the **ground** under all six declines, and the
activation contract's description of the shipped product.
[A23](#a23--2026-09-01-opentaint-joins-the-tool-native-profile-at-0--6-and-the-shipped-models-archive-is-ruled-shipped-product)
declined every cell because "the pinned release ships no rule set" — true of
the analyzer release's two assets, and incomplete about the shipped product.
The six rationales in the
[activation-contract section](#opentaint--analyzer2026082717eb0fe-shipped-models-archive-only-java-only)
are restated on the measured evidence below, each cell carrying this
amendment's link, per the same restatement discipline
[A10](#a10--2026-08-28-bifrosts-native-category-z-cell-is-restated-on-the-absent-endpoint-catalog)
established.

**The challenge, and what it turned out to be.** The vendor's demo repository
([seqra/java-spring-demo](https://github.com/seqra/java-spring-demo))
documents the shipped product's intended invocation as `opentaint scan .` —
an entry point A23 never engaged. Read from the vendor's own source: the
`opentaint` CLI's `scan` command defaults to `--ruleset builtin`, and
`builtin` is not an embedded catalog but the vendor's **versioned rules
release**, downloaded by pinned tag and handed to the same analyzer jar
through the same `--semgrep-rule-set` flag every benchmark-controlled run
uses. The released CLI (v0.4.5, 2026-07-10) pins `rules/v0.2.2`; the CLI at
the repository head pins `rules/v0.3.0` (2026-07-30), the newest rules
release at the pinned analyzer's own date (2026-08-27). On A23's own
reasoning that rule set is **shipped product** — vendor-authored, versioned,
digest-pinnable (`opentaint-rules.tar.gz`, SHA-256
`3d789c9986479fec792333329abe737eccb15bc06fc59a978a58810118ca1d21`) — so the
declines could not go on resting on the absence of a rule set. They had to be
re-decided against what the shipped rules actually bind.

**The field evaluation.** `scripts/probe-opentaint-scan-activation.sh`,
evidence retained under `reports/raw/amendment-a25-opentaint-scan-activation/`.
The pinned analyzer (same digests, no version bump), the shipped models
archive, and the `rules/v0.3.0` java rule set — the demo-shaped activation,
at every severity, a superset of the CLI's warning-and-error default, so
silence here implies silence under the product's own filter — over all twelve
committed Java native fixtures. The kernel adapter's rule-load-trace guard
applies: the analyzer exits zero with a well-formed empty SARIF on rule-load
failure, so the silence had to be proven loaded-and-silent. It was: **86
rules registered, 135 rule traces, zero load errors, zero results on all
twelve fixtures.** A positive control proves the harness live rather than
dead: a fixture carrying the real `jakarta.servlet.http` identities (stub
classes on the real package path, so the compiled bytecode carries the
fully-qualified names the shipped source rules bind) flows
`request.getParameter(...)` into `Runtime.exec(...)`, and the shipped
`os-command-injection` rule reports it under the identical jar, models, rule
set, and flags. No finding fired anywhere on any fixture, so there is nothing
for [the outcome-honesty section](#outcome-honesty) to re-score as
`not-reached`: the cells never leave `unsupported`.

**Why the cells stay declined.** The shipped rule set binds this profile's
command sink — `Runtime.exec` is in `command-injection-sinks` — and binds
**no source any native template reads**: every source rule in the java set
(v0.3.0, and v0.2.2 was read too — SHA-256
`367e16db53b37ecd9c0ec260a5c65dc4977dbe9164737f90394b453c37a449d6`, same
three source files) is servlet-, Spring-, or Seam-shaped. Nothing names
`System.getenv`, a `main(String[])` parameter, or `System.getProperty`. A
bound sink with no applicable source cannot produce a finding on these
fixtures — the exact shape
[A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
and
[A19](#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence)
retained Semgrep CE's and FlowDroid's Java cells on, here with the executed
run and the live control on top of the catalog reading. The product fact this
records is the same one FlowDroid's row records: a security suite aimed at
framework-served code, which is a statement about the shipped catalog's
audience, not about the engine.

**What would move a cell.** A vendor rules release whose java set binds a
platform source these templates read. Such a release would be vendored under
[the provenance rule](#provenance-for-vendored-activation-artifacts) — or
pinned by release digest as this evaluation pinned `rules/v0.3.0` — and the
cells re-decided against it by a dated amendment. Nothing is vendored by this
amendment: the declined row still hands no fixture to the analyzer, so no
committed invocation shape changes and the no-benchmark-models gate is
untouched.

**Templates and languages touched.** All six native templates, for `java`
alone, for OpenTaint alone. No partition decision, report, or score changes.

**Freezes invalidated.** None. The v0.6.1 manifest binds
`reports/opentaint-java-native.json` byte-for-byte, with all twelve cells
`unsupported` — and those are still the outcomes, so nothing the freeze
attests moves. The frozen report's retained rationales carry A23's wording,
which was the decision of record when the freeze was taken; that is the
historical record, kept as written. This amendment changes the grounds this
document states for the same declines, not the partition, the outcomes, or
any published byte.

### A26 — 2026-09-02: Joern's native decline is re-grounded on a field evaluation of the shipped scan bundle

**What changed.** Nothing in the partition: all eighteen Joern cells — six
templates across `java`, `javascript`, and `python` — stay `unsupported`, and
the row stays 0 / 6 per language. What changes is the grounds. The
preregistered row declined the scan surface on a packaging claim —
*"`joern-scan` is present in the distribution, but its query database is
not... a floating `latest` release asset is unpinnable at run time"* — and a
maintainer challenge (Joern ships a query database: https://queries.joern.io,
the `joern-scan` bundle) sent that claim into the field, where part of it
failed. The decline survives, on stronger evidence than it had: **the shipped
product was installed at its pin, executed over every probe cell with zero
benchmark input, and decided nothing.** This is the same movement
[A10](#a10--2026-08-28-bifrosts-native-category-z-cell-is-restated-on-the-absent-endpoint-catalog)
made for Bifrost's category-Z cell: the decision stands, the citation it
rested on is corrected, and the retired sentence stays recorded in
[the Joern activation section](#joern--40614-defaultsemantics-only) rather
than being silently dropped. (Renumber-race note, per
[the numbering convention](#amendments): the sequence's top merged heading at
authoring was A24, and this entry was drafted as A25 — then renumbered to A26
before opening, because the concurrent BrokkAi/dataflowbench#121 already
claims A25 for OpenTaint. If that claim dissolves, the number stays A26
anyway; a gap is cheaper than a second race.)

**What was measured false in the old grounds.** Two things, both retained
under `reports/raw/amendment-a26-joern-scan-native/` (produced by
`scripts/probe-joern-scan-native.sh`, which works on a copy of the pinned
distribution — the pin itself is never mutated):

1. **The bundle is pinnable.** The floating `latest` URL is real, but the
   same `JoernScan` carries a versioned URL template, and the shipped
   `joern-scan --updatedb --dbversion 4.0.614` downloads and installs the
   `querydb.zip` published as an asset of the pinned v4.0.614 release itself
   (URL and SHA-256 retained in `querydb-zip-provenance.txt`). Unpinnability
   was the stated reason a vendored snapshot was deferred, and it is not
   true.
2. **The product runs with zero input from us.** `joern-scan <dir>` builds
   the CPG and executes the installed bundle end to end — no query, no
   semantics file, no configuration of ours.

**What the field evaluation established, per language.** The pinned bundle
dumps fifty-eight queries (`query-names.txt`, `querydb.json`), each tagged
with its language: 27 `c`, 10 `android`, 9 `php`, 7 `java`, 3 `kotlin`, 2
`ghidra`.

- **JavaScript and Python: the bundle ships no query for either language at
  all.** Zero queries could bind anything, and the twenty-four
  scans measured zero findings. The Python leg surfaced a shipped-product
  defect worth retaining: on this pin `joern-scan`'s language auto-detection
  emits `importCode.pythonsrc(...)`, which does not compile against the
  product's own console (`python-autodetect-failure.txt`) — the documented
  explicit `--language python` runs, and the probe uses it precisely so a
  crash cannot impersonate a silence.
- **Java: seven queries ship, and none can fire on these probes.** Six bind
  servlet, Spring, SQL, certificate, and crypto identities no probe fixture
  uses. The seventh — `call-to-exec`, the one query in the bundle that names
  this profile's command sink — is
  `cpg.method("java.lang.Runtime.exec").callIn`, and `cpg.method(...)`
  filters the method **name** property with a full-match regex: a
  `javasrc2cpg` method's name is `exec`, so the pattern matches zero methods
  on the very graph whose `cpg.method("exec").callIn` is non-empty
  (`call-to-exec-binding-check.txt`, measured on the source-sink positive's
  own CPG). All twelve Java scans measured zero findings, the source-sink
  positive included.

**Why the cells stay declined rather than becoming scored.** The same
distinction [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
drew for Semgrep's Java column: no shipped query binds any probe endpoint —
by absence in two languages, by a binding that structurally cannot match in
the third — so the cells are capability coverage, decided from the bundle's
text and confirmed by execution, not an activated model set producing
thirty-six false negatives. The thirty-six zero-finding scans are the
decline's evidence, not scored runs. Even the
[sink-existence hazard](#sink-existence-only-findings-and-how-they-score)
cannot reach these fixtures: the one sink-existence query aimed at
`Runtime.exec` is the one that cannot bind.

**What would move a cell now.** A future pin whose bundle gains a query that
binds a probe endpoint — a JavaScript or Python package, or a Java query
matching by method full name — is a promotion by dated amendment, landing the
execution arm that scores it in the same pull request. The re-grounded
rationale is mirrored into `NATIVE_PARTITION` (`src/main.rs`) and the
adapter README's three tool-native sections; the retained 0 / 6 reports
predate this amendment and carry the withdrawn wording in their retained
rationales, exactly as A10's did — the corrected string lands with the next
evidence re-run, and the decision those reports record is the decision this
amendment leaves in place.

**Templates and languages touched.** All six native templates, for `java`,
`javascript`, and `python`, for Joern alone. No decision changes anywhere.

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report; v0.6.1 is untouched.

### A27 — 2026-09-02: Semgrep CE's JavaScript and Java declines are re-grounded on enumeration and execution, and their settled rationales reach the runner

**What changed.** No decision: all twelve Semgrep CE cells for `javascript`
and `java` stay `unsupported`, and both rows stay 0 / 6. Two things change,
one evidentiary and one corrective:

1. **The grounds are strengthened from a rule-text reading to a measured
   enumeration plus a field run.**
   [A6](#a6--2026-08-27-semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot)
   and
   [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)
   decided their cells by reading the vendored snapshots, before Semgrep was
   invoked over a single JavaScript or Java native fixture — and it never
   was. A maintainer challenge to every 0-findings native row asked whether
   that 0 / 6 reflects the shipped product or an under-scoped snapshot, and
   the answer is now measured rather than read
   (`scripts/probe-semgrep-jsjava-native.sh`, retained under
   `reports/raw/amendment-a27-semgrep-jsjava-native/`).
2. **The runner's partition strings catch up with A6/A7.** Those amendments
   discharged the preregistered *to be verified at vendoring* status in this
   document but never mirrored the settled rationales into
   `NATIVE_PARTITION_AMENDMENTS`, so every retained JavaScript and Java
   report kept asserting *"…and no snapshot is vendored"* — false since
   2026-08-27. Twelve `Some(reason)` rows now carry the per-cell A6/A7
   rationales (re-grounded as below) into the runner. The preregistered
   `NATIVE_PARTITION` cells stay as written; the amendment table is
   consulted first, which is what it is for. The retained reports keep
   their committed bytes, because the v0.6.1 freeze manifest binds both
   rows' normalized reports by digest and a freeze is immutable: the
   corrected strings land with the first evidence re-run after v0.6.1,
   which is the same deferral
   [A26](#a26--2026-09-02-joerns-native-decline-is-re-grounded-on-a-field-evaluation-of-the-shipped-scan-bundle)
   chose for Joern's retained rationales — the decision those reports
   record is the decision this amendment leaves in place.

(Numbering note, per [the convention](#amendments): at authoring the top
merged heading is A26, and the open BrokkAi/dataflowbench#121 claims A25 for
OpenTaint, so this entry takes A27 — the first number no heading claims.)

**Question 1: was the vendored snapshot complete?** Yes, measured three ways
against the upstream archive re-fetched at the pinned commit
(`semgrep/semgrep-rules@40b8c63f75dc7c22c8a77482d73bfb864b146f7e`, archive
SHA-256 verified against the digest recorded at vendoring):

- **File lists are identical.** Upstream `javascript/lang/security/` holds
  exactly thirty `.yaml` rule documents and `java/lang/security/` exactly
  eighty-six, and the vendored trees hold exactly those files under the same
  relative paths (`snapshot-enumeration-javascript.txt`, `-java.txt`; empty
  diffs retained).
- **Bytes are identical.** Every vendored document is byte-identical to its
  upstream original after the CRLF→LF normalization the Java provenance
  already records for `jackson-unsafe-deserialization.yaml`.
- **Nothing outside the scoped path binds the platform identities.** A8's
  Python promotion came from a shipped audit rule binding
  `os.environ`/`sys.argv` → `os.system`. The analogous identities occur in
  **no rule document anywhere** in the upstream `javascript/`, `typescript/`,
  or `java/` trees at the pinned commit: `process.env` and `process.argv`
  match zero files, and so do `System.getenv`, `System.getProperty`, and
  `System.setProperty` (`platform-source-grep.txt`). The one `child_process`
  rule outside the vendored scope,
  `javascript/aws-lambda/security/detect-child-process.yaml`, sources from a
  Lambda handler's `$EVENT` parameter — the same framework-shaped entry
  convention A6 found universal inside the scope. The JavaScript and Java
  analogs of `audit/dangerous-system-call-tainted-env-args.yaml` do not
  exist at this commit, in or out of the snapshot.

**Question 2: would a run have produced anything?** No, now measured instead
of predicted. The pinned CE 1.175.0 (`--oss-only`), pointed at the vendored
snapshots with the exact argv the committed runner uses, was executed over
all twenty-four JavaScript and Java native fixtures: **twenty-four scans,
zero findings, zero errors** (`scan-summary.json`, full `--json` output
retained per fixture). This confirms by execution both A6's reading and A7's
stated prediction (*"a run over these fixtures would also have produced
nothing"*), and it confirms that the
[sink-existence hazard](#sink-existence-only-findings-and-how-they-score)
stays dormant for these two languages: no pattern rule fires on any negative
cell's bare sink.

**Why the cells stay declined rather than becoming scored.** Unchanged from
A6/A7, and the enumeration makes it airtight: no shipped rule — in the
snapshot or anywhere in the upstream language trees at the pinned commit —
binds a platform source, so the cells are capability coverage decided from
the shipped rule set's text, confirmed by execution. The twenty-four
zero-finding scans are the decline's evidence, not scored runs, and they
reduce no denominator.

**What would move a cell now.** A future snapshot re-vendor (a dated
amendment with a new digest pin) whose commit gains a JavaScript or Java
analog of the Python env-args audit rule promotes the affected cells, landing
the execution arm that scores them in the same pull request, exactly as
[A8](#a8--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension)
did for Python.

**Templates and languages touched.** All six native templates, for
`javascript` and `java`, for Semgrep CE alone. No decision changes; the
settled rationale strings reach the runner here and reach the retained
reports with the first evidence re-run after v0.6.1.

**Freezes invalidated.** None — and, unlike the boilerplate earlier
amendments could use, not because no freeze holds a tool-native report: the
v0.6.1 manifest binds both rows' normalized reports by digest, with every
outcome `unsupported`. This amendment moves no outcome and rewrites no
frozen byte, so `validate-freeze` stays green; the frozen reports carry the
superseded rationale wording, and this entry is the durable record of what
replaced it.

### A28 — 2026-09-02: Infer's native decline is re-grounded — the shipped taint bundle is loaded unconditionally, and holds no endpoint

**What changed.** Nothing in the partition: all six Infer cells stay
`unsupported` and the row stays 0 / 6, Java alone. What changes is the
grounds, in the same movement
[A26](#a26--2026-09-02-joerns-native-decline-is-re-grounded-on-a-field-evaluation-of-the-shipped-scan-bundle)
made for Joern: a maintainer challenge sent
[A14](#a14--2026-09-01-infers-native-row-declines-on-a-measured-silence)'s
central phrase — *"Pulse taint is off absent a configuration"* — into the
field, and part of it failed. The pinned distribution **bundles default taint
data, and a zero-configuration invocation activates it.** The decline
survives on stronger evidence than it had: the shipped bundle was enumerated
file by file, its loading was proven by execution rather than read from a
README, and the release's full default checker surface was run over every
probe cell and decided nothing. The imprecise sentence stays quoted in
[the Infer activation section](#infer--v130-shipped-pulse-checker-with-no-taint-configuration)
rather than being silently dropped. (Renumber-race note, per
[the numbering convention](#amendments): the sequence's top merged heading at
authoring was A26, with A25 claimed by the concurrent OpenTaint
re-evaluation — a claim that merged as
[A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)
before this entry did. This entry was drafted as A27 — then renumbered to
A28 before merge, because the concurrent BrokkAi/dataflowbench#123 already
claims A27 for Semgrep's own native re-grounding. If that claim dissolves,
the number stays A28 anyway; a gap is cheaper than a second race.)

**What was measured, all three arms retained under
`reports/raw/amendment-a28-infer-native-activation/`**
(`scripts/probe-infer-native-activation.sh`, whose corruption arm operates on
a byte copy of the pinned distribution — the pin itself is never mutated):

1. **The bundle exists and is enumerated.** The distribution ships exactly
   one default taint surface, `lib/infer/infer/config/taint/`: a README and
   four Objective-C `NSLib` files (`NSString`, `NSArray`, `NSDictionary`,
   `NSSet`), retained verbatim with digests. Every file's single top-level
   key is `pulse-taint-propagators`. No `pulse-taint-sources`, no
   `pulse-taint-sinks`, no `pulse-taint-sanitizers`, no
   `pulse-taint-policies`, no `.inferconfig`, and no Java identity exist
   anywhere in the shipped tree (`shipped-taint-bundle-manifest.json`).
2. **The bundle is engaged by every invocation — proven, not quoted.** The
   bundled README's own claim ("always included when running infer") was put
   to execution: with one bundled file corrupted in a scratch copy of the
   distribution, a zero-configuration Java **capture** dies with exit 3
   naming the corrupted file from `Config.pulse_taint_config`'s directory
   fold (`engagement-proof-transcript.txt`). This matters because the pinned
   release's signature failure mode is *silent* config loss; here the
   opposite is established — the default-config machinery is demonstrably
   live in the exact invocation shape A14 measured, so A14's silence is an
   **engaged** silence: the loader ran, loaded the shipped taint data, and
   that data binds no endpoint to any policy. The always-enabled
   Simple→Simple policy has nothing to bind: propagators declare no kind that
   feeds it, and no Objective-C selector matches a Java procedure.
3. **The full default surface decides nothing the split invocation missed.**
   A14's arm was the adapter's own `analyze --pulse-only`; a shipped
   activation could in principle live in a checker that arm disables. It does
   not: `infer run --sarif` — capture plus analyze with the release's whole
   default checker set — over all twelve Java native fixtures produced
   **zero findings of any rule**, taint-shaped or otherwise (verbatim SARIF
   per fixture). There is no non-taint Pulse finding to reconcile against any
   anchor, so no cell becomes a live activation deciding `not-reached`: an
   away-from-anchor diagnostic would at least witness an activated question,
   and none exists.

**Why the cells stay declined rather than becoming scored.** The distinction
is [A7](#a7--2026-08-27-semgrep-ces-six-java-cells-are-retained-unsupported-against-the-vendored-snapshot)'s
and A26's: the shipped model set expresses no flow question over any probe
endpoint — the one taint artifact it ships is propagator-only and
Objective-C-only — so the twelve zero-finding full-default runs are the
decline's evidence, not scored runs, and `unsupported` remains the honest
outcome. A run that reports `not-reached` asserts an asked question that
found no flow; no question is asked.

**What would move a cell now.** A future pin whose bundled tree gains a
source or sink bound to a policy for a Java identity — or any default checker
that fires a reconcilable finding on a probe fixture — is a promotion by
dated amendment, landing the execution arm that scores it in the same pull
request. The re-grounded rationale is mirrored into `NATIVE_PARTITION`
(`src/main.rs`) and the adapter README's tool-native section; the retained
0 / 6 report predates this amendment and carries A14's wording in its
retained rationales, exactly as A26 left Joern's — the corrected string lands
with the next evidence re-run, and the decision that report records is the
decision this amendment leaves in place.

**Templates and languages touched.** All six native templates, for `java`,
for Infer alone. No decision changes anywhere.

**Freezes invalidated.** None. No published freeze manifest contains a
tool-native report; v0.6.1 is untouched.
### A29 — 2026-09-02: FlowDroid's native decline is re-grounded on the shipped surface's full enumeration and executed engagement

**What changed.** Nothing in the partition: all six FlowDroid cells stay
`unsupported`, and the row stays 0 / 6 for Java. What changes is the grounds.
[Amendment A19](#a19--2026-09-01-flowdroid-joins-the-tool-native-profile-with-a-live-activation-contract-and-six-cells-declined-on-catalog-evidence)
declined the cells from the shipped `SourcesAndSinks.txt` catalog's own text,
before any run — a maintainer challenge asked whether that reading had
engaged everything the release ships, or only the default file. This
amendment answers by enumeration and by execution, the same movement
[A25](#a25--2026-09-02-the-shipped-opentaint-scan-entry-point-is-field-evaluated-and-the-six-native-declines-are-re-grounded-on-its-measured-silence)
and
[A26](#a26--2026-09-02-joerns-native-decline-is-re-grounded-on-a-field-evaluation-of-the-shipped-scan-bundle)
made for OpenTaint and Joern: **every declarative surface the pinned jar
bundles was enumerated, none binds any identity the probes read, and the
shipped catalog executed over all twelve Java native fixtures decided
nothing** — so the decline comes back stronger than it went in.
(Numbering note, per [the numbering convention](#amendments): the sequence's
top merged heading at authoring was A26, and this entry was drafted as A27 —
then renumbered to A29 before merge, because the concurrent
BrokkAi/dataflowbench#123 and BrokkAi/dataflowbench#124 both claim A27 and,
by PR order, A28. If either claim dissolves, the number stays A29 anyway; a
gap is cheaper than a second race.)

**The enumeration.** Retained under
`reports/raw/amendment-a29-flowdroid-shipped-surface/` (produced by
`scripts/probe-flowdroid-native-shipped-surface.sh`, which witnesses all
three artifact digests and the jar's self-reported version before touching
anything, and works entirely in scratch space — no committed artifact is
mutated and no report is written). The pinned
`soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar` bundles exactly five
declarative surfaces beyond compiled classes, every one retained verbatim:

1. **`SourcesAndSinks.txt`** — the only endpoint catalog instance the
   release ships **in any format**: the bundled `schema/SourcesAndSinks.xsd`
   defines an XML catalog format the CLI can consume, but no XML instance
   exists in the artifact, and no SuSi-style categorized variant does
   either. Textually 176 `_SOURCE_` / 227 `_SINK_` / 4 `_BOTH_` lines; the
   release's own parser accepts 71 sources and 193 sinks and rejects 14
   malformed vendor lines with `Line does not match` warnings (retained in
   every per-fixture log) — the shipped catalog is smaller in the field than
   on paper, and A19's textual counts overstated what actually loads.
2. **`EasyTaintWrapperSource.txt`** — the EasyTaintWrapper default
   definitions: 435 wrap entries, 12 excludes, 5 kills, and 4 include
   prefixes (`android.`, `java.`, `org.apache.http.`, `org.joda.time.`).
   The format has no source or sink role at all — every entry is
   propagation-side — so it cannot supply what the catalog lacks.
3. **`AndroidCallbacks.txt`** — 520 callback interface names; lifecycle
   surface, not endpoints.
4. **`virtualedges.xml`** — the virtual-edge callgraph model; edges, not
   endpoints.
5. **`summariesManual/`** — the 347-class StubDroid summary set the default
   taint wrapper loads with no flag. Its `java.lang.System` summary models
   `getProperty` as key-argument → return propagation and declares no
   `getenv` method; no summary links `setProperty` to `getProperty` as a
   store; its five `Base64`-named summaries are `android.util`, `okio`, and
   `commons-codec` — `java.util.Base64` has none, exactly as A19 read.

**The load-bearing zero, checked against the whole artifact.** `getenv`
occurs in exactly three entries of the entire jar — shaded third-party
dependency classes that *call* `System.getenv` at tool runtime
(`io.modelcontextprotocol`, `org.snakeyaml`, `io.agentscope` — each named in
the retained search) — and in **no model, catalog, wrapper, or summary
declaration anywhere**. The probe searched every surface for every identity
the six templates use (`getenv`, the `getProperty`/`setProperty` pair, a
`main(String[])` argv convention, `Runtime.exec`, `ProcessBuilder`,
`Base64`): the sink side binds, the source side binds nowhere.

**The execution.** Three witnessed behaviors, each under the adapter's
zero-exit guards (a negative exists only where the analyzer's own
`Found N leaks from M sources` line does; the failure banner anywhere is a
probe failure):

1. **No fallback catalog exists.** A bare `-a <apk> -p <platform>`
   invocation initializes the default StubDroid wrapper (`summaries for 347
   classes`, in the retained log) and then fails with the zero-exit banner
   `No source/sink file specified for the data flow analysis` — the
   activation shape A19 recorded is the only one the release has.
2. **The shipped catalog, engaged, decides nothing.** Per-fixture APKs were
   materialized exactly as the kernel does (javac, the committed activity
   wrapper, D8, the committed manifest blob) and the pinned CLI ran over all
   twelve Java native fixtures with the shipped catalog extracted verbatim
   and the default wrapper active. Every run completed with
   **`Found 0 leaks from 0 sources`**, aborting at source lookup — the
   twelve logs, argv records, and parsed `SourceSinkManager` counts are
   retained per fixture.
3. **The control attributes the zeros.** The same source-sink-positive APK,
   the same invocation, the shipped catalog plus one benchmark-authored line
   — `<java.lang.System: java.lang.String getenv(java.lang.String)> ->
   _SOURCE_`, clearly labelled a control and never part of any activation —
   yields **`Found 1 leaks from 1 sources`**, with the results XML retained.
   One line separates 0 / 6 from the floor flow being found; nothing about
   the APK materialization, the entry wrapper, the platform pin, or the
   engine explains the zeros. The catalog does.

**Why the cells stay declined rather than becoming scored.** Unchanged from
A19, now with executed evidence where a text reading stood: the activation
rule scores a cell only when a shipped model gives the template's flow
something to bind, and a run whose source set is empty over these fixtures
can decide nothing a retained rationale doesn't already state. Recording
twelve executed `Found 0 leaks from 0 sources` outcomes as `not-reached`
would present a catalog gap as a measured miss — the exact conflation this
profile exists to prevent. The per-cell rationales in `NATIVE_PARTITION`
(`src/main.rs`) now carry the A29 citation beside A19's.

**What would move a cell.** As A19 recorded: a shipped catalog release that
gains a platform environment or argv source is a promotion by dated
amendment carrying the new jar pin as its evidence — and this amendment's
enumeration is exactly the check such a promotion would re-run.

**Templates and languages touched.** All six native templates, Java only,
FlowDroid alone. No decision changes anywhere.

**Freezes invalidated.** None. The v0.6.1 freeze pins
`reports/flowdroid-java-native.json` by digest, and this amendment does not
touch that report: its retained decisions and their A19 rationale text are
the run that was frozen, and the re-grounding lives in this document, the
probe evidence, and the rationale text future runs will carry.
