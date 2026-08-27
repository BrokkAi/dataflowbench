# Adapter contract

An adapter executes a real supported tool surface, captures its raw output,
and normalizes only the states in `schemas/result.schema.json`: `reached`,
`not-reached`, `inconclusive`, `unsupported`, and `runner-error`.

Canonical cases never contain native rule syntax. Each adapter owns its rules,
models, command line, version discovery, configuration hash, capability notes,
and raw-evidence retention under `adapters/<tool>/` or the adapter's dedicated
report directory.

The initial adapter plan is:

| Tool | Initial profile | Status |
| --- | --- | --- |
| Bifrost | Breadth baseline and per-language propagation kernels | Implemented smoke adapter; kernel runs are reported separately. The Java, JavaScript, PHP, and Scala kernel commands have now been run over their expanded 29-template cores |
| CodeQL | 16-template Java and JavaScript propagation kernels and the 29-template expanded Python kernel | Java, JavaScript, and Python runners implemented as separate language-scoped populations |
| Joern | The Ruby 16-template propagation kernel, the 27-template expanded Rust kernel, and the 29-template expanded Java, Python, JavaScript, and PHP kernels | Implemented as six separate language-scoped populations over one CPG query script |
| Semgrep CE | Supported local analysis only | Implemented as eleven separate language-scoped populations over one committed taint rule per language; only the documented intraprocedural partition is scored. Four front ends are non-GA in the pinned distribution (Kotlin `beta`; Rust, C, C++ `alpha`) and the label is retained without ever changing the partition |
| OpenTaint | Java and Kotlin profile | Planned |

No adapter may synthesize a tool result. If a supported case cannot complete,
emit `inconclusive` or `runner-error` with the raw evidence. If it is outside
a documented tool profile, emit `unsupported`; it is excluded from
false-negative interpretation. An incomplete or failed run must never become
`not-reached` merely because the SARIF result list is empty.

## Challenge-tier rollout mechanics

[The challenge-tier preregistration](challenge-tier.md) fixes *what* the
thirteen additional templates are, which of them apply to each language, and
what each language's expanded core denominator becomes. It deliberately leaves
the validator work to the waves that author the fixtures. This section is the
mechanics: how a language moves from its classic denominator to its expanded one
without any population check being rewritten, and how the tiers stay separated
while only some languages have moved.

**One table.** `CHALLENGE_ROLLOUT` in `src/main.rs` holds one row per language:
its `classic` template set (sixteen, or fifteen where the exception-catch cell
is inapplicable), the `challenge` set the preregistration's applicability matrix
assigns it, and a `rolled_out` flag. `expected_core_templates(language)` returns
`classic` while the flag is `false` and `classic + challenge` once it is `true`.
Every population check reads that function — the corpus-wide balance validator,
the Bifrost per-language kernels, the CodeQL ECMA and C-family kernels, the
Joern kernels, and the Semgrep kernels — so no denominator is stated twice.

**A wave PR flips one row.** The language PR that authors a language's challenge
fixtures sets that row's `rolled_out` to `true` in the same change. Nothing else
in the validator moves: the Bifrost run's expected core count, the CodeQL and
Joern balance checks, and the Semgrep selection all follow the row. Before the
flip, a language with no challenge fixtures validates against its classic set,
so it is never failed for lacking fixtures that do not exist yet; after the
flip, the language is required to carry the full expanded set, so a partial
fixture landing fails validation rather than silently reducing a denominator.
The `challenge` sets themselves are preregistered and are not a wave's to edit.

The per-language balance check used to compare each ECMA kernel's template set
against Java's. That comparison is gone: with the three wave-1 languages landing
in separate PRs, it would have made a language's correctness depend on which
sibling merged first. Each language now answers to its own preregistered row.

**The smoke slice is pinned by template identity, not only by policy.** The
frozen 118-case Bifrost smoke population was pinned by naming the seven policies
it evaluates. That is no longer sufficient: a challenge case names the *same*
language-kernel policy its classic siblings
name, so it would have been swept into the frozen population and quietly changed
what those 118 cases mean. `smoke_population_case` therefore refuses any case
whose `template_id` begins with `dfb-template-chal-`, whatever policy it names
and whether or not it declares an `unsupported_reason`. A regression test pins
the count at 118 and a second one asserts the refusal directly.

**Java and JavaScript have dedicated Bifrost kernels.** `run-bifrost-java-kernel`
and `run-bifrost-javascript-kernel` write `reports/bifrost-java-kernel.json` and
`reports/bifrost-javascript-kernel.json` with their own raw-evidence roots,
matching the pattern every language after Python already follows. Each selects
its language's whole core population — classic today, classic plus challenge
after the row flips — and pins the language-qualified policy for the run so all
of its assertions share one configuration hash, exactly as the Kotlin kernel
does. The frozen direct-propagation pairs keep the policies they were published
with: Java's positive and negative name `direct-positive.rqlp` and
`explicit-negative.rqlp`, JavaScript's pair names the cross-language breadth
policy, and the selector accepts all of them rather than rewriting evidence a
freeze manifest binds byte-for-byte.

Both commands have now been run against their languages' real challenge
fixtures, so `reports/bifrost-javascript-kernel.json` and
`reports/bifrost-java-kernel.json` are those languages' expanded-core Bifrost
evidence. The frozen 118-case smoke slice is untouched by either and remains
the published 32-assertion Java and JavaScript slices.

**A freeze-bound report is not re-run by the wave that expands its language.**
`reports/freeze.json` digest-binds nineteen reports, including all ten CodeQL
kernel reports and eight of the Bifrost kernel reports. Overwriting one would
invalidate a published freeze, so those adapters are deferred to the v0.4.0
freeze-prep re-run and the deferral is recorded in that language's kernel
contract. Deferral is not absence of coverage, and the v0.3.0 and v0.4.0
populations are never compared number-to-number.

**Semgrep CE's challenge partition is preregistered.** All thirteen challenge
templates are decided `unsupported` by declared capability, from the pinned
distribution's own documentation, before any challenge fixture exists. The
decision is keyed by template ID rather than by fixture tags, so no later
fixture's `feature_tags` and no observed result can move a case between the
partitions. The per-template rationale is in
[the Semgrep adapter notes](../adapters/semgrep/README.md).

**The rollout is complete. All thirteen rows are flipped** — Python,
JavaScript, Java, C#, TypeScript, Kotlin, Go, C++, C, Rust, Scala, PHP, and
Ruby — so every core kernel now carries its preregistered expanded
denominator and no language validates against its classic set alone. Ten of
the thirteen have a core
denominator of 29 templates and 58 assertions; **C++'s is 28 templates and 56
assertions**, **Rust's is 27 templates and 54 assertions**, and **C's is 24
templates and 48 assertions**, because some cells are inapplicable to those
languages — `exception-catch` from the classic sixteen for both C and Rust,
`chal-reflective-invocation` from the challenge thirteen for both C++ and
Rust, and three further challenge cells for C. An inapplicable cell reduces
only its own language's denominator. The Python wave re-ran the
adapters no freeze binds — Joern and Semgrep CE — while leaving its
freeze-bound Bifrost and CodeQL reports exactly as published; the JavaScript
and Java waves re-ran Joern and Semgrep CE too, and each additionally ran its
dedicated `run-bifrost-<language>-kernel` command, which writes a report no
freeze binds and so is not a rewrite of published evidence. The JavaScript and
Java CodeQL reports stay as published. The TypeScript wave could run **only
Semgrep CE**: both its Bifrost and its CodeQL reports are freeze-bound, so both
are deferred to the v0.4.0 re-run, and the Joern adapter has no TypeScript
slice to run at all. The Go wave is in the same position for the same reasons:
its Bifrost *and* CodeQL reports are both freeze-bound, so both are deferred to
the v0.4.0 re-run, and the Joern adapter has no Go slice — Semgrep CE was its
only runnable adapter. The per-adapter evidence, including which adapters were
deferred, is in [the Python kernel contract](python-kernel.md), [the JavaScript
adaptation matrix](javascript-kernel.md), [the Java kernel
contract](java-kernel.md), [the TypeScript adaptation
matrix](typescript-kernel.md), and [the Go kernel contract](go-kernel.md).

The Rust wave ran **Joern and Semgrep CE** over its whole expanded
54-assertion population — `reports/joern-rust-kernel.json` and
`reports/semgrep-rust-kernel.json` are both post-freeze and bind nothing — and
deferred **both** Bifrost and CodeQL, whose Rust reports are digest-bound by
v0.3.0. It is the first engine evidence on any systems language's challenge
strata; see [the Rust kernel contract](rust-kernel.md).

The C# wave ran **no adapter at all**, and that is the honest consequence of the
freeze rule rather than a gap in the wave. Every analyzer that covers C# is
either freeze-bound or absent: `reports/bifrost-csharp-kernel.json` and
`reports/codeql-csharp-kernel.json` are both digest-bound by
`reports/freeze.json`, Joern ships a `csharpsrc2cpg` frontend but this
repository has no C# Joern slice, and Semgrep CE cannot analyze C# at all
because the pinned distribution lists it as a Pro-only language. The C#
challenge fixtures, the flipped row, and the validation battery land now; all
expanded C# evidence arrives at the v0.4.0 re-run. See [the C# kernel
contract](csharp-kernel.md).

Kotlin is the sparsest case and is worth stating explicitly, because a reader
could otherwise mistake it for missing coverage. **Both** of Kotlin's
analyzer reports — `reports/bifrost-kotlin-kernel.json` and
`reports/codeql-kotlin-kernel.json` — are freeze-bound, so both adapters are
deferred to the v0.4.0 re-run; Joern has no Kotlin slice in this repository at
all (its `kotlin2cpg` frontend exists upstream and is recorded as available but
out of scope); so Semgrep CE is the only adapter this wave could run over
Kotlin's expanded population, and it did. The per-adapter evidence, including
which adapters were deferred, is in [the Python kernel
contract](python-kernel.md), [the JavaScript adaptation
matrix](javascript-kernel.md), and [the Kotlin kernel
contract](kotlin-kernel.md).

The C wave carries the most sharply **reduced** challenge set: four of the thirteen
templates are inapplicable to C, so its expanded core is 24 templates / 48
assertions rather than 29 / 58. Like TypeScript, it could run **only Semgrep
CE** — `reports/bifrost-c-kernel.json` and `reports/codeql-c-kernel.json` are
both digest-bound by `reports/freeze.json`, and the Joern adapter has no C
slice — so both engine re-runs are deferred to v0.4.0. See [the C kernel
contract](c-kernel.md).

The Ruby wave is the last of the thirteen and the opposite extreme: the only
one that defers **nothing**. Ruby's kernel landed *after* the v0.3.0 freeze, so
none of its four reports appears in `reports/freeze.json`'s report list, and all
four adapters — CodeQL, Joern, Bifrost, and Semgrep CE — were re-run whole over
the expanded 58 assertions. All thirteen of Ruby's challenge templates are
directly applicable, so its expanded core is the full 29 templates. Ruby is
therefore the only language with complete expanded-core evidence from all four
adapters, and `reports/codeql-ruby-kernel.json` is the **only CodeQL report in
this repository that reflects the challenge tier at all** — every other CodeQL
kernel is digest-bound at its 32-assertion classic population. It scores 49/58
— 29/32 classic and 20/26 challenge, clean **6/6** on stratum D, the context
and depth stress stratum. Joern scores 40/58 — 26/32 and 14/26 — and carries the
wave's one **recorded measured departure** from the challenge preregistration:
at the same pinned `maxCallDepth=4` that makes Java, JavaScript, Python, PHP,
and Rust miss the depth-6 relay positive, Ruby discriminates that pair
correctly. The departure is recorded as measured rather than reconciled to the
prediction. Semgrep CE scores 12/14 on its preregistered intraprocedural
partition with the other 44 assertions `unsupported`, and Bifrost returns 58/58
`inconclusive` under a new *taint semantic binding is unavailable* diagnostic
class rather than reporting absent flows as negatives. See [the Ruby kernel
contract](ruby-kernel.md).

With Ruby's row flipped the challenge-tier rollout is complete: all thirteen
core kernels carry their preregistered expanded denominators, and every
remaining gap is an adapter re-run deferred to v0.4.0 by the freeze rule, not a
missing fixture.

## Modeling matrix rollout mechanics

[The modeling-matrix preregistration](modeling-matrix.md) fixes *what* the
twelve benchmark-controlled modeling templates are, which of the six categories
each analyzer can express, and what a language's modeling denominator becomes.
It deliberately leaves the runner work to the pull requests that author the
fixtures and the model artifacts. This section is the mechanics, on the same
terms as the challenge-tier section above.

**Infrastructure now, fixtures and models per language.** The runner
infrastructure — the template constants, the population validator, the per-tool
partition, the four commands, the artifact-path conventions, and the
load-bearing-model gates — lands ahead of any fixture. Wave M1 then adds Java,
JavaScript, and Python one pull request at a time: that language's twenty-four
fixtures and cases, the per-adapter model encodings its partition entitles it
to, and the runs. A wave never edits a template definition or a partition cell.

**Presence is the signal; there is no rollout table.** The challenge tier needed
`CHALLENGE_ROLLOUT` because its templates *expand an existing denominator*, so
something had to say whether a language's core is the classic set or the
expanded one. Modeling is its own tier with its own denominator, so the
question does not arise: `validate_modeling_cases` in `src/main.rs` checks each
language that has modeling-tier cases against the preregistered twelve, and a
language with none has no modeling denominator at all — which is different from
having a zero, and validates trivially. The first fixture a language commits
turns the check on for that language, and a partial landing fails the build
rather than silently reducing a denominator.

**Tier isolation is structural, not a filter someone has to remember.** A
`dfb-template-model-` template and `score_tier: "modeling"` imply each other,
and the validator rejects a case where they disagree. Because every core,
calibration, `language-extension`, and `real-project` selection already filters
on the tier, a modeling case cannot leak into any of them; `smoke_population_case`
additionally refuses modeling cases outright, the same way it refuses challenge
ones, so the frozen 118-case Bifrost smoke population cannot absorb one.

**The partition is `CHALLENGE_SEMGREP_PARTITION` generalized to four tools.**
`MODELING_PARTITION` holds one cell per tool per category — twenty-four cells,
transcribed from the preregistration's tables, with the cells it marks *to be
verified* recorded as `unsupported` per its own rule, and with the dated
amendments applied on top as template-level overrides. Scored today, after
Amendments A2 and A3: **Bifrost 2 templates of 12** (category S alone),
**Semgrep CE 5 of 12** (S, E, and one of Z's two templates), **CodeQL 12 of
12**, **Joern 8 of 12** (S, Z, E, B). A declined cell is decided from the
template ID *before the tool is invoked*, retains the document's rationale
verbatim as its reason, and writes a `retained-capability-decision` evidence
document beside the report. The decision is keyed by template identity, never
by `feature_tags` and never by an observed result — a regression test asserts
the cell does not move when a case's tags are rewritten — and revising one is a
dated amendment on the preregistration, not an edit here.

**Model artifacts are conventions the language PRs populate.** One artifact per
tool per language, hash-bound into the report's `configuration_hash`:

| Adapter | Modeling artifact |
| --- | --- |
| Bifrost | `adapters/bifrost/policies/model-<language>.rqlp` |
| CodeQL | `adapters/codeql/<language>/queries/<Language>Modeling.ql`, except Java's, which is `adapters/codeql/queries/JavaModeling.ql` |
| Joern | `adapters/joern/semantics/model-<language>.semantics`, plus the shared `adapters/joern/queries/modeling.sc` |
| Semgrep | `adapters/semgrep/rules/model-<language>.yaml` |

The CodeQL path departs from the preregistration's schematic
`adapters/codeql/queries/<Language>Modeling.ql` and sits inside that language's
existing `qlpack`, because a query outside a pack cannot resolve its
`codeql/<language>-all` dependency. That is a location, not a declaration
surface: the document's `ConfigSig` encoding is unchanged. Java is the one
language for which the schematic path is already correct, because Java's pack
*is* the adapter root — `adapters/codeql/qlpack.yml` declares
`dataflowbench/codeql-java` and `JavaKernel.ql` sits beside it — so there is no
`adapters/codeql/java/` to descend into and a query under one would resolve
nothing. Joern is the one adapter with two files, and both bind the
configuration hash.

**Four commands, parameterized by language.** `run-bifrost-modeling`,
`run-codeql-modeling`, `run-joern-modeling`, and `run-semgrep-modeling`, each
taking `--language java|javascript|python` and writing
`reports/<tool>-<language>-modeling.json` with raw evidence under
`reports/raw/<tool>-<language>-modeling/`. The per-language *kernel* commands
are separate commands because each language's kernel differs in real toolchain
plumbing — a `kotlinc` trace, a `go build`, a synthesized Cargo crate, a
different extractor. A modeling run has none of that: three languages, three
already-wired toolchains, and a run that differs from its sibling only in which
artifact it loads and which population it selects. A `--language` argument says
that once instead of twelve times.

**Fail fast, never an empty report.** A run refuses, before touching the
analyzer, when:

- the language has no modeling population — *"no modeling population for
  `<language>`"*, because a report over zero assertions asserts nothing;
- the tool's modeling artifact for that language is missing or unreadable. This
  is the preregistration's *missing model* arm: a scored cell with no
  declaration behind it is a defect in DataFlowBench, not evidence about the
  analyzer, so it is a **hard error** that fails the build and never an
  outcome — not `unsupported`, not `not-reached`, not a result;
- a `--codeql-packs` search path is named but does not exist.

**The load-bearing-model gates are wired now so a language PR cannot forget
them.** A modeling assertion is only evidence of activation if the tool's
behavior *without* the model would differ, and two adapters have an
unmodeled-call default that would otherwise decide category P and O cells on
their own. So the runner reads each artifact before the run and refuses it
unless the default is disabled: a Bifrost modeling policy must set
`:call-modeling (call-modeling :unmodeled require-model)` and must not name the
kernel policies' `optimistic`, and a Semgrep modeling rule must set `options:
taint_assume_safe_functions: true`. Tests pin both strings. CodeQL has no
such switch to pin — a `ConfigSig` with no `isAdditionalFlowStep` adds no
step. Joern's equivalent claim ("a method with no `FlowMapping` propagates
nothing") was measured false by the first wave-M1 run: `FlowSemantic`
mappings on the pinned 4.0.610 are additive over the engine's default
pass-through, which is why Amendment A2 moved Joern's propagator and summary
categories to unsupported activation rather than gating them.

**The execution arm lands with the language.** The arm that invokes an
analyzer over a *scored* cell is written by the pull request that authors that
adapter's declarations for that language. All three of wave M1's languages are
wired on the same four runners: Python (`docs/python-modeling.md`), JavaScript
(`docs/javascript-modeling.md`), and Java (`docs/java-modeling.md`). Wave M1 is
therefore complete, and a scored cell in a language that has no arm stays a hard
error rather than a synthesized outcome, which the adapter contract at the head
of this document forbids. The `unsupported` arm is independent of all of that,
so a tool that declines every category a population carries produces a whole,
validated report of retained capability decisions without the analyzer being
invoked at all.

**Reconciliation on this tier is source-anchored as well as sink-anchored,** and
that is a property of the fixtures rather than of any adapter. A modeling fixture
carries both halves of its pair in one type — the declared entity and its
undeclared sibling — because that is what the templates say makes the negative a
negative, and category E's handlers need no caller, so the declared handler's
flow is present in the negative's fixture too. A finding therefore counts only
when it lies in the region its case's own source anchor governs *and* on a
callsite of its anchored sink function. An unmatched finding on this tier is the
pair's other entity, fully attributable, so it normalizes to `not-reached` with
the count retained — not to the kernels' `inconclusive`, which is reserved here
for evidence with no usable location at all.

**Reporting stays separate.** Modeling reports are their own population per
language and per adapter, bound into a freeze manifest like every other report,
ordered on generated scorecards by the `modeling` entry in `SCORE_TIER_ORDER`.
A modeling assertion never appears on a propagation-kernel scorecard, never
enters a core denominator, and is never macro-averaged with one.

## Tool-native rollout mechanics

[The tool-native preregistration](native-profile.md) fixes *what* the six
platform-API templates are, what each tool's activation contract pins, and which
cells each tool can activate at all. This section is the mechanics, on the same
terms as the two sections above.

**Infrastructure now, fixtures and vendored snapshots per language.** The
template constants, the category mapping, the activation partition, the
profile-disjoint validators, the four commands, the activation shapes, and the
gates land ahead of any fixture. Wave N1 then adds Java, JavaScript, and Python
one pull request at a time: that language's twelve fixtures and cases, the
vendored activation snapshots its partition needs, and the runs.

**One tier, two profiles, and the selectors say which.** Native cases carry
`score_tier: "modeling"` and `model_profile: "tool-native"`. The tier keeps both
modeling populations out of every core, calibration, `language-extension`, and
`real-project` denominator; the *profile* is what keeps them out of each other,
so `modeling_case` and `native_case` both filter on it and
`validate_profile_disjoint_populations` asserts corpus-wide that no case is
selected by both, in either direction, for any language. That check exists
because pooling the profiles is a fault of omission — a selector that filters on
the tier and forgets the profile — which no assertion about a case's own fields
would catch.

**The partition is keyed by template, not by category — and, since
[Amendment N-A1](native-profile.md#n-a1--2026-08-27-semgrep-ces-six-python-cells-are-promoted-to-scored-and-the-partition-gains-a-language-dimension),
by language too.** `NATIVE_PARTITION` holds one cell per tool per template —
twenty-four cells, transcribed from the preregistration's summary, with its *to
be verified* cells recorded as `unsupported` per its own rule — and
`NATIVE_PARTITION_AMENDMENTS` sits in front of it with one row per amended
tool × language × template. The language dimension exists because a vendored
activation snapshot is per language: reading Python's rules can only answer
Python's cells, and a partition without a language could not say so. As
preregistered: **CodeQL 6 templates of 6**, and **Bifrost, Joern, and Semgrep
CE 0 of 6**. As amended: Semgrep CE is **6 of 6 for Python** on the evidence of
its vendored snapshot, and unchanged elsewhere. The asymmetry with the
benchmark-controlled matrix is the point rather than a defect — Joern scores four
of six categories there on the same engine — because this profile measures
product packaging and that one measures the engine. A declined cell is decided
from the template ID *before the tool is invoked*, retains the document's
rationale verbatim, and writes a `retained-capability-decision` document beside
the report carrying the pinned activation configuration with it.

**Four commands, parameterized by language.** `run-bifrost-native`,
`run-codeql-native`, `run-joern-native`, and `run-semgrep-native`, each taking
`--language java|javascript|python` and writing
`reports/<tool>-<language>-native.json` with raw evidence under
`reports/raw/<tool>-<language>-native/`.

**Fail fast, never an empty report.** A run refuses, before touching the
analyzer, when the language has no tool-native population, when a pinned
activation artifact is missing — this profile's analogue of the modeling
matrix's *missing model*, and a hard error for the same reason — or when a named
`--codeql-packs` path does not exist.

**The no-benchmark-models gate is the profile's load-bearing check.** A native
run must supply no benchmark-authored model of any kind, so the runner reads the
pinned activation shape and refuses it if any argument names a benchmark model
artifact. The artifact set is derived from the modeling matrix's own constants —
every `ModelingLanguage::artifact` for every tool, plus
`adapters/joern/queries/modeling.sc` — so a modeling artifact added later is
covered the moment it is declared. Tests pin every activation shape literally:
`--threat-model=local` plus the shipped `<language>-security-extended.qls` suite
for CodeQL, `--oss-only` plus `--config=adapters/semgrep/native/<language>` for
Semgrep, `--policy-pack` and never `--policy-file` for Bifrost, and nothing at
all for Joern, which activates `DefaultSemantics` by running.

**Activation configuration binds the configuration hash.** Most of a native
run's configuration is not a file in this repository — it is a suite name, a
pack version, a threat-model group — so `native_configuration_hash` hashes the
pinned activation identity and arguments alongside whatever vendored bytes
exist. That is what makes issue #16's *"model/version provenance and activation
configuration are retained"* a property of the artifact.

**Vendored activation artifacts carry `derived` provenance.** Where shipped
models are not pinnable at run time — Semgrep's registry, Joern's floating
`querydb` release asset — the profile vendors a pinned snapshot with a
`provenance.json` recording the upstream repository, source commit, paths,
license, and retrieval date. Wave N1's Python pull request landed the first —
ninety-one Semgrep rule files under `adapters/semgrep/native/python/`, pinned to
one `semgrep-rules` commit, with a per-file digest so the report's
`configuration_hash` binds the rules and not just the manifest.

**The execution arm lands with the language.** The arm that invokes an analyzer
over a *scored* native cell is written by the wave-N1 pull request that vendors
that adapter's snapshot for that language. Until then a scored cell is a hard
error rather than a synthesized outcome, which the adapter contract at the head
of this document forbids.

**Native anchoring binds a callsite, not a declaration.** Every other population
here puts a `DFB-SINK:` marker on the declaration of a benchmark-invented
endpoint and reconciles against that function's callsites. A native fixture
declares no endpoint — the sink is inside the platform — so the marker sits on
the real platform-API callsite and a finding is bound to that line. Findings
away from the anchor are retained as diagnostics and are never flow evidence;
only unreadable evidence makes a cell `inconclusive`, because a coverage miss by
an activated model set is a plain `not-reached` and calling it incomplete would
quietly remove the cell from the vendor's denominator. An anchor still only
decides which finding belongs to which assertion; it never tells an analyzer
what a sink is.

**Reporting stays separate.** Native reports are their own population per
language and per adapter. A native scorecard is never merged with a
benchmark-controlled one, even though the two share a score tier and a language,
and no aggregate combines native coverage with controlled accuracy.

## Analyzers evaluated and not adapted

An adapter admits an analyzer only when four bounds hold, and every analyzer
we evaluate is recorded here against them so absence is never ambiguous:

1. **Semantic data flow.** The tool performs taint or value-flow analysis —
   the track this benchmark scores. Linters and rule/AST matchers without a
   flow engine would take a near-blanket `unsupported` and add no signal.
2. **Local, pinnable execution.** Analysis runs on this machine from an
   exactly pinned version, so evidence is reproducible. Cloud-submission
   services fail this bound even when the engine is real.
3. **Retained native output.** Machine-readable findings (SARIF/JSON) the
   runner can retain verbatim as raw evidence.
4. **Publishable results.** The license or terms of service must permit
   running the tool against a benchmark and publishing the outcome.
   Commercial SAST terms commonly restrict comparative publication; any such
   restriction is disqualifying until explicit permission exists, and we do
   not test first and ask later.

### Evaluated (2026-08, from the field surveyed in Sourcegraph's
"12 Best Static Code Analysis Tools in 2026" and our own review)

| Analyzer | Verdict | Bound(s) failed |
| --- | --- | --- |
| Semgrep CE | **Adapted** | — (bounded to its documented intraprocedural profile) |
| CodeQL | **Adapted** | — |
| Snyk Code | Not eligible | (2) analysis is cloud-backed and account-bound; (4) terms to be verified but commonly restrictive — both must clear before any attempt |
| Coverity | Not eligible | (2) no free local pinned CLI (Coverity Scan is cloud submission); (4) benchmark restrictions |
| Checkmarx | Not eligible | (2) and (4) — enterprise-only, no local CLI, standard no-benchmark terms |
| Veracode | Not eligible | (2) and (4) — same class |
| Fortify | Not eligible | (2) and (4) — same class |
| SonarQube | Not eligible for the taint track | taint/injection analysis is a commercial-edition feature; the open Community engine has no cross-procedure taint, so (1) fails for the open build and (4) for the commercial one |
| Qodana | Not eligible for the taint track | taint lives in the commercial Ultimate tier; same split as SonarQube |
| PMD | Not eligible | (1) — rule/AST analysis; its historical DFA module is deprecated, no taint engine |
| ESLint | Not eligible | (1) — linter; plugins add patterns, not flow analysis |
| CodeScene | Not eligible | (1) — behavioral/hotspot analysis, not data flow |

The SonarQube and Qodana rows are coverage facts of the same shape as
Semgrep CE's C# cell: the open tier genuinely cannot analyze the track, and
that is recorded rather than tested around.

### Queued candidates that do qualify

Three open-source engines pass all four bounds on their face and are queued
for future adapters, alongside the OpenTaint adapter issue (#17):

- **Infer** (Meta) — open source, local CLI, interprocedural analysis for
  C/C++/Java/Objective-C. The strongest next candidate.
- **Pysa** (Meta) — open-source Python taint analysis on the Pyre engine.
- **FlowDroid** — the academic standard for Java/Android taint analysis,
  open source and locally runnable.

Each still requires the standard adapter diligence before implementation:
pin an exact version, verify the taint mode against a probe fixture, and
preregister the capability partition from documentation — nothing here is a
result yet.

## CodeQL language populations

The CodeQL adapter keeps Java and JavaScript as separate populations. The
JavaScript command selects that language's whole core `taint` population —
32 assertions classically, and 58 now that JavaScript's challenge row is
rolled out:

```text
language == "javascript"
track == "taint"
score_tier == "core"
tool_model_references.codeql.query ==
  "adapters/codeql/javascript/queries/JavaScriptKernel.ql"
```

The selection is balanced: one positive and one negative case for each shared
template ID — the 16 classic templates, plus the 13 challenge templates
[the challenge tier](challenge-tier.md) classifies as applicable to
JavaScript. `reports/codeql-javascript-kernel.json` is digest-bound by the
v0.3.0 freeze, so it still holds the 32-assertion classic evidence and is not
rewritten by the JavaScript expansion; the expanded CodeQL evidence is
deferred to the v0.4.0 freeze-prep re-run, as recorded in
[the JavaScript kernel contract](javascript-kernel.md). It does not select
TypeScript cases, even where CodeQL
uses shared JavaScript/TypeScript libraries. JavaScript has its own query,
pack manifest (`adapters/codeql/javascript/qlpack.yml`),
normalized report (`reports/codeql-javascript-kernel.json`), and raw SARIF
directory (`reports/raw/codeql-javascript/`). Java uses its existing query,
report, and evidence directory independently.

For each JavaScript case, the runner materializes the declared fixture files in
an isolated workspace, creates a fresh CodeQL database with the JavaScript
extractor, runs `JavaScriptKernel.ql`, and removes temporary database/workspace
artifacts after retaining the raw output. The normalized report records the
exact CodeQL CLI version/build and configuration hash observed by that run. The
retained snapshot used CodeQL CLI 2.26.3, build SHA
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, with official `github/codeql` tag
`codeql-cli/v2.26.3` at source commit
`44a68d3a47fcbcd6a6a76ec7d1c1b3a1a28b201e`. Its JavaScript pack is
`codeql/javascript-all@2.9.0` with the committed lock. Registry retrieval of
that 2.9.0 pack was unavailable in the test environment, so reproduction used
the matching official source workspace root via `--codeql-packs` (or an
equivalent matching bundle pack root):

```bash
CODEQL=/path/to/codeql-v2.26.3/codeql
CODEQL_SOURCE_ROOT=/private/tmp/codeql-source-v2.26.3
cargo run -- run-codeql-javascript-kernel \
  --codeql "$CODEQL" \
  --codeql-packs "$CODEQL_SOURCE_ROOT"
```

SARIF findings are mapped back to the benchmark's sink anchors, while the
query path evidence identifies the source-to-sink flow and normalized results
retain both anchor sets. A `DFB-SINK:` marker identifies the anchored sink
declaration/function. The SARIF result must be in the same anchor file at the
callsite to that sink identity; it need not be on the marker's exact line.
Only anchor-backed evidence contributes to `reached`; successful execution
with no matching finding contributes to `not-reached`. Unresolved or
incomplete evidence remains `inconclusive`, capability exclusions remain
`unsupported`, and database/query/parse failures remain `runner-error`. All
raw SARIF and runner diagnostics remain available for audit.

The retained JavaScript snapshot has 32 results: 15 `reached`, 17
`not-reached`, and zero `inconclusive`, `unsupported`, or `runner-error`
outcomes. Twenty-nine of 32 match expected polarity. The false negatives are
`dfb-taint-javascript-alias-propagation-positive` and
`dfb-taint-javascript-expression-positive`; the false positive is
`dfb-taint-javascript-loop-carried-negative`. It retains 32 SARIF files, zero
error files, and empty normalized `witness_checkpoints` for every case. The
configuration hash is
`a038e39eb93d6fc674ab59cf2e4de5b3608f1d7b294c19da75ce1bd041c75ac5`.

The direct-flow breadth run, Java kernel run, JavaScript kernel evidence, and
Python kernel run are distinct adapter populations. A kernel command must
select only its language and retain the exact raw output for those cases; it
must not use a direct-flow result or a Java result as a proxy for JavaScript.
The Python kernel's template balance and construct adaptations — sixteen
templates in v0.3.0, twenty-nine once its challenge row was rolled out — are
defined in the [Python kernel contract](python-kernel.md).

### CodeQL Python slice

The Python CodeQL command selects exactly the `core` taint cases in
`cases/taint/python/`: one positive and one negative assertion for each of the
balanced template IDs in Python's core denominator — 32 assertions over 16
templates before the challenge rollout, and **58 assertions over 29 templates**
now that Python's `CHALLENGE_ROLLOUT` row is flipped. Each case's
`tool_model_references.codeql.query`
must point to `adapters/codeql/python/queries/PythonKernel.ql`; Java cases and the
13-language direct-flow baseline are excluded. The command creates a fresh
Python database per case and writes `reports/codeql-python-kernel.json` plus
one retained raw SARIF or runner-error artifact per selected case under
`reports/raw/codeql-python-kernel/`.

The Java and Python query packs are separate: Java uses the pack rooted at
`adapters/codeql/`, while Python uses `adapters/codeql/python/`, including its
language-specific database-schema dependency. Installing or resolving one
pack must not silently substitute the other language's pack.

Reproduce it with CodeQL CLI v2.26.3 and the pinned Python pack
`codeql/python-all@7.2.3`:

```bash
codeql pack install adapters/codeql/python --search-path /path/to/codeql-packs
codeql pack ls adapters/codeql/python --search-path /path/to/codeql-packs
cargo run -- run-codeql-python-kernel \
  --codeql /path/to/codeql \
  --codeql-packs /path/to/codeql-packs
```

The normalized result copies the case's source and sink anchors and uses the
SARIF finding/diagnostic evidence to classify the anchored assertion. The
adapter retains `reached`, `not-reached`, `inconclusive`, `unsupported`, and
`runner-error` distinctly: incomplete or failed analysis is never a negative
result, and raw SARIF is retained even when normalization cannot complete.
The validated Python run used CodeQL CLI 2.26.3 build
`7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/python-all@7.2.3`. Its 32 results are 14 `reached` and 18
`not-reached`, with no `inconclusive`, `unsupported`, or `runner-error`
outcomes; 28/32 match the expected polarity. The mismatches are false
negatives for `alias-propagation-positive`, `array-element-positive`, and
`exception-catch-positive`, and a false positive for `loop-carried-negative`.
These results cover only the Python core kernel.

`reports/codeql-python-kernel.json` is one of the nineteen reports
`reports/freeze.json` digest-binds for v0.3.0, so the Python challenge wave did
**not** re-run it: those 32 results describe the 16-template v0.3.0 population
and are left exactly as frozen. CodeQL evidence for Python's expanded
58-assertion core arrives with the v0.4.0 freeze-prep re-run. See
[the Python kernel contract](python-kernel.md).

## Joern language populations

The Joern adapter keeps Java, JavaScript, Python, Ruby, PHP, and Rust as six
separate populations. Each command selects that language's core `taint` cases
runner-side:

```text
language == "java" | "javascript" | "python" | "ruby" | "php" | "rust"
track == "taint"
score_tier == "core"
```

The v0.3.0 freeze digest-binds every `case.json` and fixture byte, so no case
declares a Joern model reference; the per-language invocation is pinned in the
runner instead, the way the Kotlin Bifrost run pins its policy. Three of the
selections are 16 templates with one positive and one negative assertion — 32
assertions — under one model profile; Rust's exception-catch cell is
inapplicable, so its core selection is the other 15 templates, 30 assertions,
and its `Result`/`?` `language-extension` pair is not selected. Python and
JavaScript move the other way: both challenge-tier rows are rolled out, so each
core selection is the expanded 29 templates, **58 assertions**, and each was
re-run whole. The six are
disjoint. Each has its own report (`reports/joern-<language>-kernel.json`) and
its own retained-evidence root (`reports/raw/joern-<language>-kernel/`).

One committed CPG query script, `adapters/joern/queries/kernel.sc`, serves all
six. It is parameterized by the benchmark-controlled source and sink
identifiers the runner reads out of each fixture's own `DFB-SOURCE:` and
`DFB-SINK:` marker lines, and runs a single `sinks.reachableByFlows(sources)`
under the OSS data-flow engine. There is no per-case, per-template, or
per-polarity branching, and Joern's own default source/sink models are not
used. Flow evidence is reconciled against the case's anchored sink callsites; a
frontend or engine failure is `runner-error`, missing or ambiguous location
evidence is `inconclusive`, and neither can become `not-reached`. Languages
whose frontend is absent from the pinned distribution are recorded as
explicitly unsupported rather than as failures.

Rust is the one language whose fixture cannot be handed to its frontend as a
loose file: `rust2cpg` walks a Cargo crate, and given a bare `.rs` file it
produces an empty CPG. The runner therefore synthesizes a minimal `Cargo.toml`
in each case's temporary workspace, with the binary target pointed straight at
the fixture rather than at a generated `src/main.rs`. Nothing is written beside
a fixture, no case's declared file list changes, and every location Joern
reports stays on the case's own anchor filename. The pinned distribution is the
first Joern release to ship `rust2cpg` at all; the adapter records what that
frontend does today rather than treating it as settled. See the
[Joern adapter notes](../adapters/joern/README.md) for the pinned version,
frontend coverage, model assumptions, and the observed per-language results.

## Semgrep CE language populations

The Semgrep adapter keeps Java, JavaScript, TypeScript, Python, Go, Ruby, PHP,
Kotlin, Rust, C, and C++ as eleven separate populations. Each command selects
that language's whole core `taint` population runner-side by language, track,
and score tier, exactly as the Joern kernels do, and each has its own report
(`reports/semgrep-<language>-kernel.json`) and its own retained-evidence root
(`reports/raw/semgrep-<language>-kernel/`). No case declares a Semgrep model
reference: the v0.3.0 freeze digest-binds every `case.json` byte, so the
invocation is pinned in the runner instead.

Every one of the eleven now selects its expanded core, the Ruby row having been
the last to flip. **Java, JavaScript, TypeScript, Python, Go, Kotlin, PHP, and
Ruby select 58** each, their expanded 29-template cores, **C++ selects 56**,
**Rust selects
54** and **C selects 48** — 622 selected assertions in all; every one of their
challenge assertions falls in the
`unsupported` partition, so each scored subset is the same 14 as everyone
else's. **C and Rust have 15-template classic halves**: their
exception-catch cell is inapplicable in `applicability-matrix.md`, so they are
balance-checked against the fifteen-template
`KERNEL_TEMPLATE_IDS_WITHOUT_EXCEPTION_CATCH` set the CodeQL and Bifrost C and
Rust kernels already use; Rust's expanded core is 27 templates (15 classic plus
12 challenge) and C's is 24 (15 plus 9), both reduced denominators being
inapplicable cells that reduce only that language's own count. The
`score_tier == "core"` filter keeps C's
error-code-return and goto-cleanup cases and Rust's `Result`/`?` pair — all
`language-extension` — out of the core denominator.

Four front ends are not GA in the pinned distribution. Its shipped
`semgrep_interfaces/lang.json` records `kotlin` at `beta` and `rust`, `c`, and
`cpp` at `alpha`; the other seven are `ga`. The label is retained on the first
`diagnostics` entry of every normalized result and in every capability-decision
document, the way the CodeQL adapter records its Rust extractor's public preview
status, and it is never an input to the partition: `semgrep_capability_exclusion`
reads only `feature_tags` and `expected_analysis_capability`, so it cannot see a
language. Taint mode was verified to function on all four before they were wired
up.

Semgrep CE is the one adapter here whose scored population is a strict subset of
its selected population, and that subset is defined by documentation rather than
by results. The pinned CLI's own `semgrep scan --help` sells interprocedural
taint (`--pro-intrafile`), cross-file taint (`--pro`), and path sensitivity
(`--pro-path-sensitive`) as Pro Engine features, and the bundled `CHANGELOG.md`
records CE's heap support as "Experimental support for basic field-sensitive
taint tracking" with index sensitivity and inter-procedural field sensitivity
both marked Pro. The scored profile is therefore intra-file, intraprocedural,
flow-sensitive, path-insensitive taint — that is, the `intraprocedural`
partition of each kernel: 7 templates and 14 assertions.

The remaining templates — the `interprocedural-one-hop`,
`interprocedural-deep`, and `heap-access-path` partitions, 18 assertions in a
16-template kernel, 34 in the expanded 24-template C kernel, 40 in the
expanded 27-template Rust kernel, 42 in the expanded 28-template C++ kernel,
and 44 in each of the expanded 29-template Java, Python, JavaScript,
TypeScript, Kotlin, and Go kernels, whose challenge
templates are all outside the profile — are `unsupported`. That decision is
taken from each case's own `feature_tags` and
`expected_analysis_capability.kind` *before* Semgrep is invoked, so an
out-of-profile case never reaches a Semgrep process and cannot produce an empty
finding list that later reads as a false negative. Each retains a
capability-decision document naming the documented boundary it falls outside.
The whole selection is still balance-checked by the same
`validate_kernel_population_with` every other kernel uses, against that
language's own template set; the bounded profile narrows what is scored, never
what is selected. The scored subset is 14 assertions in all eleven languages,
because every intraprocedural template is applicable everywhere — and it stays
14 in a language whose challenge tier has rolled out, because no challenge
template carries the `intraprocedural` tag.

Rules are benchmark-controlled and committed under `adapters/semgrep/rules/`,
one `mode: taint` rule per language. Because endpoint identifiers vary per
fixture, each rule carries `__DFB_SOURCE__`/`__DFB_SINK__` placeholders that the
runner resolves per case from that fixture's own `DFB-SOURCE:` and `DFB-SINK:`
marker lines — the same resolver the Joern kernels use. Every report's
`configuration_hash` is a SHA-256 over all eleven committed rule files, so
adding the four new ones invalidated the seven existing reports and all eleven
kernels were re-run rather than four being appended beside a stale hash. The
exact resolved rule each case was analyzed under is retained beside its finding
document. `--metrics=off` and `--oss-only` are passed on every invocation, and a
finding reporting any engine other than `OSS` is a `runner-error` rather than a
data point. Issue #15 will later formalize a cross-tool taint-modeling matrix;
these rules are the endpoint-contract instantiation of it.

Semgrep's native `--json` document is the retained raw evidence, one per scored
case. Findings are reconciled against the case's anchored sink callsites: only
anchor-backed evidence is `reached`, a clean scan of the fixture with no finding
is `not-reached`, and a non-zero exit, a non-empty `errors` array, a skipped
rule, or unparseable output is `runner-error`. `raw_special_outcome` — the
freeze's raw-evidence guard — now also refuses a Semgrep document whose `errors`
array is non-empty, so a failed scan's well-formed empty `results` list can
never be frozen next to a clean negative.

All eleven kernels ran on Semgrep CE 1.174.0 (`semgrep-oss:1.174.0`, Homebrew).
Each produced 9 `reached`, 5 `not-reached`, and its whole remainder
`unsupported` — 18 each for the two unexpanded 16-template PHP and Ruby
kernels, 34 for the expanded C kernel, 40 for the expanded Rust kernel, 42 for
the expanded C++ kernel, and 44 each for the expanded Java, Python,
JavaScript, TypeScript, Kotlin, and Go kernels — with
zero `inconclusive` and zero `runner-error` outcomes, and 12/14 of each scored
subset matching the expected polarity. Every intraprocedural positive is
`reached` in every language; the two mismatches, identical in all eleven, are
false positives on `infeasible-branch-negative` and `loop-carried-negative` —
precisely the path sensitivity the pinned CLI documents as Pro-only. The four
non-GA front ends score exactly what the seven GA ones score, which says the
mismatch belongs to the shared engine rather than to any parser; it is not a
general claim about those parsers, since the scored partition exercises only
local propagation inside one function.

C# is named in that CLI's own `--pro-languages` text and so cannot be run under
CE at all — a tool limitation, permanent under the current pin. **Scala is
different in kind**: the pinned distribution records `scala` at `ga`, more
mature than three of the four languages just added, and nothing in the engine
blocks it. It is left recorded-only because the maintainer scoped it out, and
that is written down so its absence is never read as a Semgrep limitation. See
the [Semgrep adapter notes](../adapters/semgrep/README.md) for the pinned
version, the documented-scope and maturity citations, the per-language
partition, and the model assumptions.

The checked-in Bifrost snapshot (`reports/bifrost-smoke.json`) contains 118
normalized results from Bifrost v0.10.2 build identity
`c2116609f5fc1be318c8fb76fb83763cf326bab6`: 50 `reached`, 37 `not-reached`, 30
`inconclusive`, and 1 `unsupported`. The pinned binary has SHA-256
`93b55dd20c283c278f586e8c8e6ad6bf0e9f5f08165b56096e110af0450d0873`.
The Java, Python, and JavaScript 32-assertion profiles have respectively
17/32 assertions matching expected polarity (17 of 22 decisive outcomes),
16/32 (16 of 20 decisive outcomes), and 19/32 (19 of 26 decisive outcomes);
incomplete runs remain `inconclusive`, never synthesized as `not-reached` or
counted as false negatives. The v0.10.2 outcomes match v0.10.1 case-for-case,
but do not restore the complete Java correctness observed in v0.9.5. See the
[Bifrost adapter notes](../adapters/bifrost/README.md) for raw-report
separation and the per-template mismatch breakdown.
