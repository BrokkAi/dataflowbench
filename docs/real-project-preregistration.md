# Real-project confirmation slice preregistration

This document is the **preregistration artifact** for a small confirmation
slice of real open-source projects. It merges before any analyzer is pointed at
any of the six repositories it pins, before any real-project case exists, and
before any number derived from one is published. It is the preregistration half
of issue #19; execution, freeze, and publication are issue #20 and change
nothing written here.

Nothing in this document is a result. It is a contract about what will be
measured, stated in advance so that the measurement cannot later be shaped
around what the measurement produced.

The draw it records has already run. That is the point: the repositories were
selected, pinned, and digest-bound while every analyzer outcome over them was
still unknown, and the seeded walk that reached them is committed as evidence a
validator re-runs rather than as prose a reader has to take on trust.

## Motivation

Every DataFlowBench population up to now is authored. The kernels, the
challenge strata, the modeling matrix, and the native probe set are all fixtures
this project wrote, in files sized for a human to hold in their head. That is
what makes them fair, and it is also their limit: an engine can be excellent on
a fifty-line fixture and useless on a repository with a build system, a
framework, five hundred files, and a call graph nobody can draw.

A confirmation slice is the cheapest honest answer to "does any of this
transfer?" — not a new leaderboard, not a scale-up, not a claim about
real-world accuracy, but a small set of real repositories with real, documented
defects, run once, reported per repository, and never averaged into anything.

It is also the population most easily corrupted. Real repositories can be
chosen after the fact. A maintainer who has seen an engine succeed on a project
can put that project in the slice; a maintainer who has seen it fail can call
the project unrepresentative and swap it out; and because DataFlowBench is
published by the vendor of one of the engines it scores, neither move would be
distinguishable from good judgment. So the selection is fixed here, mechanically,
before any engine sees any of it, and the mechanism is committed so a reader can
re-run the draw rather than trust the account of it.

## Governance

### Preregistration and immutability

This document merges before the first real-project fixture is authored. From
the moment the first analyzer executes against the first pinned revision, the
population definition, the eligibility criteria, the sampling procedure, the
seed, the replacement rule, and the claim bounds below are **immutable**.

A defect discovered after that point is corrected by a documented
**amendment**, never by a silent edit. An amendment:

1. appears in a dated `## Amendments` section at the foot of this document;
2. states what changed, why, and which pins, strata, or claims it touches;
3. states which already-published freezes it invalidates, if any;
4. is a separate commit from any fixture or result change.

Amendment numbering is the single repository-wide sequence described in the
[documentation index](README.md); this document joins the amendment-bearing
set.

A pinned repository that turns out to be unusable is **replaced by the
documented replacement rule** (below) if the ground-truth review has not closed,
and **retired by amendment** if it has. A `pin_id` is never reused for a
different repository.

### The rule that makes the rest of it mean anything

> **No analyzer outcome may influence selection, replacement, or ground truth.**

Concretely, and in the order the pipeline runs:

- The sampling frame is built from advisory metadata alone. No analyzer is
  invoked to build it, rank it, or filter it.
- Every eligibility criterion below is decided from repository or advisory
  metadata. None of them can be evaluated by running an analyzer, which is why
  none of them mentions a finding, a rate, or a tool.
- The draw is executed, recorded, and committed before any analyzer runs. The
  draw record declares `analyzer_evidence_consulted: false` and the validator
  rejects any other value.
- Ground truth is authored from the upstream fix diff and adjudicated by
  reviewers who see no analyzer output, and adjudication closes before the
  first run.
- A repository is never redrawn, replaced, or excluded because of what an
  analyzer did to it. After adjudication closes, an unusable repository is an
  amendment and a published exclusion, not a swap.

### Reproducibility, and what is committed

Three artifacts carry the selection:

| Artifact | What it holds |
| --- | --- |
| `corpus/real-project/frame.json` | The retained sampling frame: the exact API queries, the admission rule, and all 219 candidates with their advisory, repository, and fix-commit references. |
| `corpus/real-project/draw.json` | The executed draw: seed, ordering rule, target size, the frame digest it consumed, the criteria table, and the ordered walk over each stratum with a disposition for every candidate the walk reached. |
| `corpus/real-project/pins/*.json` | One pin record per selected repository, against `schemas/real-project-pin.schema.json`. |

`cargo run -- validate` recomputes every candidate's draw key from the declared
seed, re-derives each stratum's ordering from the retained frame, and refuses a
walk that does not reproduce it. Substituting a repository by hand fails the
build, because the substituted repository lands at the wrong draw key. That is
the difference between a preregistration and a promise.

The frame is retained rather than re-queried. The GitHub Advisory Database
grows, so the query is reproducible in shape but not in bytes; the committed
frame is the immutable input, its digest is bound by every pin record, and a
re-query that returns something different is a new wave, not a correction to
this one.

## Population definition

The population is **real-world, source-available data-flow vulnerabilities in
open-source projects written in the three languages with the deepest adapter
coverage in this benchmark**: Java, JavaScript, and Python.

It is operationalized as a sampling frame over the GitHub Advisory Database,
because that database is public, enumerable, versioned, analyzer-neutral, and
already the provenance the ecosystems themselves use. An advisory enters the
frame when all of the following hold. These are properties of the frame, not of
a repository, and they are applied by the query and the admission rule, not by
judgment:

- **Reviewed.** `type=reviewed`; the advisory has been curated by GitHub rather
  than mirrored unreviewed from a feed. Not withdrawn.
- **Ecosystem.** `maven` for the Java stratum, `npm` for JavaScript, `pip` for
  Python. Ecosystem, not repository language, is what the database indexes;
  language is enforced later, per repository, by eligibility criterion E1.
- **Publication window.** Published between 2025-01-01 and 2025-12-31
  inclusive. A closed historical window makes the frame stable: the same query
  will keep returning approximately the same advisories, where an open-ended
  window would drift with every new disclosure.
- **Taint-shaped weakness.** At least one of CWE-22 (path traversal), CWE-78
  (OS command injection), CWE-89 (SQL injection), CWE-94 (code injection),
  CWE-611 (XML external entity), CWE-918 (server-side request forgery). These
  six are the weakness classes whose definition *is* a source-to-sink flow with
  an unambiguous sink, which is the track this slice confirms. Cross-site
  scripting is deliberately absent: its sink is a rendering boundary whose
  identity varies by framework and templating layer, so a disagreement about an
  XSS case is usually a disagreement about the sink rather than about the flow.
- **A fix commit in the project's own repository.** The advisory's
  `source_code_location` is a GitHub repository, and at least one of its
  references is a commit URL under that same repository. This is what makes a
  revision pin possible at all.

The frame that these rules produced on 2026-09-04 holds **219 candidates**: 48
Java, 66 JavaScript, 105 Python.

The advisory supplies the *candidate* defect and nothing else. It is never
treated as ground truth — the same rule
[benchmark sources](benchmark-sources.md) already applies to every donor suite.
An upstream maintainer's decision to ship a fix is evidence that something was
wrong, not a specification of which source reaches which sink.

### Strata

Three strata, one per language: **java**, **javascript**, **python**. They are
drawn independently and never pooled. They are these three because they are the
languages that carry a propagation kernel, a benchmark-controlled modeling row,
and a tool-native row, and because they are where adapter coverage is deepest —
seven adapters wired for Java, five for Python, four for JavaScript.

Ten further languages carry kernels and are **out of scope for wave R1**,
recorded here so their absence is not read as a limitation of any tool.

## Eligibility and exclusion criteria

Each criterion is decided from repository or advisory metadata at draw time.
None of them may be evaluated by running an analyzer. Criteria E1–E4 and E7 are
mechanical and were evaluated by the draw script against the GitHub REST API;
E5 is a maintainer judgment recorded per exclusion; E6 and E8 are structural.

| ID | Criterion | Admitted when |
| --- | --- | --- |
| **E1** | Stratum language | The repository's GitHub-reported primary language equals the stratum language exactly. |
| **E2** | Licence | GitHub reports an OSI-approved SPDX identifier (not `NOASSERTION`, not absent), and a licence file resolves at the pinned revision. |
| **E3** | Repository status | The repository is neither archived nor a fork. |
| **E4** | Size budget | The GitHub-reported repository size is at most 250 MB. |
| **E5** | Not a donor, benchmark corpus, or analyzer under evaluation | The repository is not a vulnerability-demo or benchmark corpus, is not an analyzer this project adapts, is not a dependency of one, and is not a donor suite named in [benchmark sources](benchmark-sources.md). |
| **E6** | Unambiguous vulnerable revision | The earliest fix commit the advisory names resolves in the repository and has exactly one parent. |
| **E7** | Substance floor | The repository holds at least 20,000 bytes of the stratum language. |
| **E8** | One advisory per repository | No repository contributes more than one pin to the slice. |

Notes on the two criteria that are doing the most work, and on what each costs:

**E1 excludes TypeScript-primary repositories from the JavaScript stratum**, and
in this draw it excluded eleven of the first fourteen JavaScript candidates. That
is a real finding about the npm advisory population rather than an accident, and
it is not a silent one: DataFlowBench has a
[separate TypeScript kernel](typescript-kernel.md) with its own denominator, so
folding a TypeScript repository into the JavaScript stratum would mix two scored
populations. A TypeScript stratum is a candidate for a later wave.

**E6 is the criterion that a merge commit fails.** When the advisory's earliest
fix is a merge, "the last revision that still carries the defect" has two
answers, and choosing one of them is exactly the kind of quiet judgment this
document exists to remove. One JavaScript candidate was excluded on this ground;
the replacement rule below records what happened next.

**E7's floor is 20,000 bytes, roughly six hundred lines.** It exists to exclude
a single-file snippet, not to prefer large projects. Setting it higher would
have excluded most of npm's real security surface, which is genuinely
concentrated in small, heavily depended-on packages, and misdescribing that
ecosystem to make the slice look weightier would be a worse error than admitting
a small package.

The criteria were calibrated against the frame's *metadata* — language, size,
and licence distributions — before the draw was executed, and no analyzer had
been run against any candidate at any point. That calibration is recorded here
because a criterion set tuned to reach a chosen repository would look identical
from outside, and the honest defence is disclosure plus a reproducible walk, not
a claim of purity.

### What is deliberately not a criterion

- **Popularity.** No star, download, or dependent-count threshold. A benchmark
  that draws only famous projects measures how well engines do on code their
  vendors have already looked at.
- **Buildability.** Whether a repository builds under a given adapter's
  requirements is an *adapter scope* question, decided per adapter in the
  scope section below and recorded as a preregistered partition. It is not an
  eligibility question, because letting one adapter's build requirements
  reshape the population would let that adapter choose its own exam.
- **Anything an analyzer reports.** Stated again here because it is the
  criterion whose absence matters most.

## Sampling procedure and seed

**Seed.** `dataflowbench-real-project-wave-r1`

**Ordering rule.** Within a stratum, candidates are ordered ascending by

```
draw_key = SHA-256(seed + "\n" + ghsa_id)
```

rendered as lowercase hex, ties broken by ascending GHSA identifier. The rule is
deliberately hash-based rather than a language's pseudo-random shuffle: a reader
with a shell and `sha256sum` can reproduce the entire ordering, and no
implementation, version, or platform difference can change it.

**Procedure.** For each stratum independently, walk the ordered candidates from
position 1. At each candidate, evaluate E1–E8. A candidate that passes all of
them is **selected**; a candidate that fails any is **excluded**, with every
failing criterion and the observed value recorded. Stop when the stratum has
reached its target. The walk is truncated at its last selection, and every
candidate the walk reached carries a disposition — a walk with a gap in it is
rejected by the validator.

**Target size: two repositories per stratum, six in total.**

> **DECISION NEEDED — sample size.** Six repositories across three languages is
> the proposed size: small enough that each case can carry a hand-authored,
> independently reviewed ground truth, and large enough that no single
> repository's peculiarity dominates the whole slice. It is not derived from a
> power calculation, and n = 6 supports no inferential statistic — see the claim
> bounds. A maintainer who wants a different size should change
> `target_per_stratum` and re-run the walk **now**, before any analyzer runs;
> after that point the size is fixed by the immutability rule and can only move
> by amendment.

### The executed draw

Executed 2026-09-04 against the retained frame. Full dispositions, including
the observed value behind every exclusion, are in
`corpus/real-project/draw.json`.

| Stratum | Walked | Excluded | Selected at positions |
| --- | --- | --- | --- |
| java | 6 | 4 | 5, 6 |
| javascript | 15 | 13 | 2, 15 |
| python | 3 | 1 | 2, 3 |

The Java stratum's four exclusions are all size-budget (E4) failures, with one
also failing on licence (E2) — the Java advisory population at the top of this
draw is dominated by large Apache projects. The JavaScript stratum's thirteen are
dominated by E1: eleven candidates are not JavaScript-primary, ten of them
TypeScript and one C++, and three of those eleven also lack an OSI licence
identifier. The remaining two are one archived repository and the merge-commit
exclusion described above. Python excluded one archived repository and then
selected twice in a row.

### The pinned slice

| Stratum | Repository | Advisory | Weakness | Licence | Pin |
| --- | --- | --- | --- | --- | --- |
| java | [hibernate/hibernate-validator](https://github.com/hibernate/hibernate-validator) | GHSA-7v6m-28jr-rg84 (CVE-2025-35036) | CWE-94 | Apache-2.0 | `dfb-rp-java-hibernate-validator` |
| java | [Robothy/local-s3](https://github.com/Robothy/local-s3) | GHSA-g6wm-2v64-wq36 (CVE-2025-27136) | CWE-611 | Apache-2.0 | `dfb-rp-java-local-s3` |
| javascript | [mafintosh/tar-fs](https://github.com/mafintosh/tar-fs) | GHSA-vj76-c3g6-qr5v (CVE-2025-59343) | CWE-22, CWE-61 | MIT | `dfb-rp-javascript-tar-fs` |
| javascript | [psi-4ward/psitransfer](https://github.com/psi-4ward/psitransfer) | GHSA-xphh-5v4r-r3rx | CWE-22, CWE-23 | BSD-2-Clause | `dfb-rp-javascript-psitransfer` |
| python | [hiyouga/LLaMA-Factory](https://github.com/hiyouga/LLaMA-Factory) | GHSA-xj56-p8mm-qmxj (CVE-2025-53002) | CWE-94 | Apache-2.0 | `dfb-rp-python-llama-factory` |
| python | [clearml/clearml](https://github.com/clearml/clearml) | GHSA-579p-qf78-fqm2 (CVE-2025-8917) | CWE-22 | Apache-2.0 | `dfb-rp-python-clearml` |

### What a pin record binds

Each record in `corpus/real-project/pins/` pins **two** revisions, not one:

- **`vulnerable`** — the first parent of the advisory's earliest fix commit. The
  last revision that still carries the reported defect.
- **`fixed`** — the advisory's latest fix commit. The revision in which it is
  remediated.

Each revision carries the `codeload.github.com` archive URL that names it, the
SHA-256 of the archive as retrieved on 2026-09-04, and its byte length. The
commit identifier is the immutable identity; the archive digest binds the
specific retrieval, so a change in how the host generates a tarball is visible
as a digest mismatch rather than as silent drift. Each record also carries the
SPDX identifier, the repository-relative licence file path as it exists at the
pinned revision, that file's digest, and whether it is identical at both
revisions. It was, for all six.

**DataFlowBench does not vendor this source.** Nothing under
`corpus/real-project/` contains upstream code. Each revision is fetched from
its pinned archive URL and verified against its digest before use, which is why
the slice can include copyleft-licensed repositories without the benchmark
redistributing anything.

The two revisions are the *candidate* positive/negative pair, in the sense the
[scoring contract](scoring.md) already uses: the vulnerable revision should
carry the flow and the fixed revision should not. Whether that pair is
*minimally different* — the property every synthetic negative has by
construction — is an adjudication question, not a schema one. An upstream fix
that also refactors, renames, or upgrades a dependency is not a minimal
negative, and reviewers may decline the pair on exactly that ground.

> **DECISION NEEDED — the hibernate-validator fix span.** That advisory names
> four fix commits spanning 2020-12-04 to 2020-12-16, so its pinned pair spans
> twelve days of unrelated development rather than one focused change. The
> proposal is to keep the pin and let the reviewers decide whether a minimal
> pair can be stated over it; if they cannot, the repository is declined under
> the replacement rule and the walk continues from position 7 of the Java
> stratum.

## Replacement rule

A selected repository may leave the slice for exactly one reason: it fails a
criterion, or the ground-truth review declines it. It never leaves because of
what an analyzer did.

**Before adjudication closes**, a repository is replaced by continuing the same
seeded walk:

1. Record the departing repository's disposition in the walk as an exclusion,
   citing the criterion it failed, with the observed value.
2. Continue the stratum's ordered walk from the next unwalked position under the
   same seed. Do not reseed, do not reorder, do not draw from another stratum.
3. Evaluate E1–E8 at each subsequent candidate until the stratum is back at its
   target.
4. Delete the departing pin record, add the replacement's, and commit both in
   the same change as the amended walk.
5. `cargo run -- validate` must pass, which it cannot unless the new walk
   reproduces from the seed.

This already happened once, in this draw, and the walk records it: JavaScript
position 3 (`joshuayoes/ios-simulator-mcp`) was excluded under E6 because the
advisory's only fix commit is a merge with two parents, and the walk continued
to position 15 (`psi-4ward/psitransfer`), which is the next candidate to satisfy
all eight criteria.

**After adjudication closes**, the walk does not continue. A repository found
unusable at that point is retired by amendment, its exclusion is published, and
the stratum runs at reduced size for that wave. Continuing the walk after the
ground truth is fixed would let a late replacement be chosen with knowledge the
early ones were chosen without, and a smaller honest slice is worth more than a
full one with a hole in its provenance.

**The replacement rule is never a redraw.** Reseeding, reordering, or drawing a
fresh sample discards the property the seed exists to provide. There is no
mechanism in this document for redrawing the slice, and adding one would need an
amendment that says so in those words.

## Analyzer adapters in scope, per language

Scope is per adapter and per language, decided from each adapter's declared
capability and each repository's build shape, and fixed **before** any run — the
same **preregistered partition** discipline the modeling and native tiers
already use. An adapter that is out of scope for a repository is recorded as
such here; it is never a silent absence and never a `not-reached`.

| Language | In scope for wave R1 | Out of scope, with reason |
| --- | --- | --- |
| Java | Bifrost, CodeQL, Joern, Semgrep CE | FlowDroid — its Java wiring analyzes Android APKs, and neither pinned Java repository is an Android application. Recorded-only, not a tool limitation. |
| JavaScript | Bifrost, CodeQL, Joern, Semgrep CE | — |
| Python | Bifrost, CodeQL, Joern, Semgrep CE, Pysa | — |

Semgrep CE runs under the same preregistered `intraprocedural` partition it
carries on every kernel: cells outside that partition are declined
`unsupported` by declared capability, from the case metadata, before the tool is
invoked.

> **DECISION NEEDED — the bytecode-and-build adapters.** OpenTaint (Java) and
> Infer (Java, C, C++) both require a compiled or build-captured artifact rather
> than a source tree, and CodeQL's Java extractor requires a traced build. The
> proposal is: CodeQL Java is in scope with a pinned Maven build recipe recorded
> per repository; OpenTaint and Infer are **deferred to wave R2**, because
> admitting them now means preregistering a per-repository build contract before
> anyone has confirmed the two Java repositories build reproducibly under the
> pinned toolchains, and a build that fails during execution is a
> `runner-error`, which blocks a freeze. Deferral is a maintainer scope
> decision, recorded so that neither tool's absence reads as an inability to
> analyze real projects.

> **DECISION NEEDED — a TypeScript stratum.** E1 excluded ten of the first
> fourteen JavaScript candidates for being TypeScript-primary. Adding a fourth
> stratum would cover a large and growing share of the npm advisory population
> and would exercise the TypeScript kernel's adapters. The proposal is to defer
> it to wave R2 rather than widen wave R1 after its draw has run.

## Bounded claims

The real-project scorecard is a **confirmation** artifact. Six repositories,
one run, reported per repository. The bounds below are what it may and may not
say, and they are bounds on the *claim*, not on the evidence: everything
observed is retained and published either way.

### What the scorecard may claim

- **Per repository, per adapter, per case: the normalized outcome**, in the
  five-outcome vocabulary the [adapter contract](adapters.md) already fixes —
  `reached`, `not-reached`, `inconclusive`, `unsupported`, `runner-error`.
- **Per repository, per adapter: the counts** of those outcomes over that
  repository's cases, and which case each outcome belongs to.
- **The identity of everything involved**: pinned revision, archive digest,
  adapter and analyzer version and build identity, configuration hash, and the
  environment stamp, exactly as every other freeze-bound report binds them.
- **A named, per-repository observation.** "On the pinned vulnerable revision of
  `tar-fs`, adapter X reported the adjudicated flow; on the fixed revision it
  did not" is a claim this slice supports. So is its negation.

### What the scorecard may not claim

- **No rate that generalizes.** No accuracy, precision, recall, or F-score over
  "real-world code", over an ecosystem, over a language, or over the slice as a
  whole. Six repositories drawn from one advisory database in one publication
  window support no such quantity, and presenting one would be the single most
  misleading thing this project could publish.
- **No confidence interval, no significance test, no ranking.** At n = 6 with
  one run each, there is no sampling distribution to speak of. An engine that
  decides five of six and one that decides four of six are not distinguishable
  by this slice, and the scorecard will not print them as if they were.
- **No leaderboard, and no combined score.** The
  [invariant against a combined leaderboard](README.md) applies here without
  modification.
- **No number-to-number comparison with any kernel, modeling, or native
  score.** Different population, different denominator, different question.
  "Engine X scores 51/58 on the expanded core and 4/6 on real projects" is not a
  sentence this project will write.
- **No pooling across tracks or model profiles.** Real-project cases carry one
  `track` and one `model_profile` like every other case, and the freeze
  validator rejects a report that mixes them.
- **No claim that a true negative on a fixed revision is equivalent to a
  synthetic true negative.** It is weaker evidence, because the upstream fix may
  have changed more than the flow, and the scorecard says so beside the number
  every time it shows one.
- **No claim about a repository the slice excluded.** The walk's exclusions are
  provenance, not verdicts. That `apache/tika` exceeded the size budget says
  nothing whatsoever about any analyzer's behavior on `apache/tika`.

### Outcome honesty is unchanged

The [scoring contract](scoring.md) applies without modification.
`unsupported`, `inconclusive`, and `runner-error` are capability or execution
coverage and are never converted into false negatives or true negatives. This
matters more here than on any authored population: real repositories will
produce more inconclusive results and more execution failures than a fifty-line
fixture ever does, and every one of those is a coverage fact rather than a wrong
answer. Per the [freeze contract](freeze.md), semantic mismatches are
publishable outcomes and execution errors block a freeze.

## The real-project scorecard cannot alter synthetic-core denominators

Stated as its own section because it is the invariant most likely to be
violated by accident, and the one issue #21 names twice.

**No real-project outcome changes any core denominator, ever.** Not by folding
in, not by reweighting, not by retiring a template, not by amending an
applicability classification, and not by supplying a reason to.

The mechanism is already built and is not new to this document:

- Real-project cases carry `score_tier: "real-project"`, one of the five values
  `schemas/case.schema.json` admits. The kernel population selectors filter on
  the tier, so a real-project case cannot enter a core, calibration,
  `language-extension`, or `modeling` denominator.
- Each language's core denominator is fixed by its
  [kernel contract](applicability-matrix.md) and checked by
  `validate_scored_kernel_balance`, which compares the observed core template
  set against the preregistered set for that language. A real-project case
  appearing in a kernel population fails `cargo run -- validate`.
- The freeze manifest binds score tiers explicitly and its validator treats
  tracks, dimensions, and profiles as partitions of the claim. A freeze cannot
  pool a real-project report with a kernel report.
- The real-project scorecard is published as a **separate scorecard**, in the
  sense [scoring.md](scoring.md) already uses for separate result populations.

The direction of influence matters too, and it runs one way only. The synthetic
core defines what the templates mean; the real-project slice asks whether that
meaning survives contact with a real repository. A disagreement between them is
a finding to publish, not a licence to edit the core. If a real-project result
suggests that a core template is badly posed, the remedy is the challenge-tier
amendment procedure applied to that template on its own evidence — never a
denominator quietly adjusted because six repositories disagreed with it.

## Independent ground-truth review and adjudication

Ground truth for a real-project case is a specific claim: *this* source reaches
*this* sink along *this* path at the pinned vulnerable revision, and does not at
the pinned fixed revision. The advisory does not state that. Somebody has to
read the code and write it down, and somebody else has to check it without
having seen the first person's reasoning.

### Roles

| Role | Does | Must not |
| --- | --- | --- |
| **Author** | Reads the upstream fix diff and the surrounding code at both pinned revisions. Writes the candidate ground truth: source anchor, sink anchor, the path, the negative mechanism at the fixed revision, and a rationale. | Review or adjudicate their own case. Consult any analyzer output. |
| **Reviewer** (two, independent) | Independently reads the same two revisions and the candidate ground truth, and returns one of: **agree**, **disagree** with a stated alternative, or **cannot determine**. | See the other reviewer's verdict before returning their own. See any analyzer output at any point. |
| **Adjudicator** (one) | Resolves a disagreement or a `cannot determine`. Chooses between the positions the author and reviewers stated, or declines the case. | Introduce a new position of their own. Author or review the case they adjudicate. See any analyzer output. |

### Procedure

1. The author writes the candidate ground truth for each case from the fix diff
   and commits it with the pin record, `ground_truth.status: "proposed"` and
   `ground_truth.adjudication: "pending"`.
2. Two reviewers work independently and blind to each other. Each records a
   verdict and a rationale against the pin record.
3. **Two agrees** closes the case: `status: "accepted"`,
   `adjudication: "agreed"`, both reviewers named in `ground_truth.reviewers`.
4. **Any disagreement or `cannot determine`** goes to the adjudicator, who
   closes it as `accepted` with `adjudication: "adjudicated"`, or as
   `declined`.
5. **A declined case is declined, not guessed.** It leaves the slice, its
   rationale is published, and the replacement rule applies if adjudication has
   not yet closed for the wave.
6. Adjudication closes for the whole wave in one dated commit. **No analyzer may
   be executed against any pinned revision before that commit lands.** This is
   the ordering the acceptance criteria of issue #19 require, and issue #20's
   execution depends on it.
7. Every verdict and rationale is retained and published with the scorecard,
   including the ones that declined a case. A reader who disagrees with a
   ground-truth call needs to see the call, not a summary of it.

### Independence, and the conflict this project actually has

DataFlowBench is published by the vendor of Bifrost, one of the engines this
slice will score. Pretending otherwise would be worse than useless, so the
independence requirement is stated in terms of that conflict:

- The two reviewers for a case must not both be the same person as the author,
  and no person holds two roles on one case.
- **At least one reviewer, and the adjudicator, must be independent of Bifrost
  engineering.** The adjudicator's independence is the load-bearing one: an
  adjudicated case is one where the reviewers disagreed, which is exactly where
  a conflicted tie-break would do the most damage.
- Every participant's affiliation is recorded beside their verdict.
- No participant may have seen any analyzer output over any pinned revision. A
  participant who has is disqualified from all three roles for that case, and
  says so rather than proceeding carefully.

> **DECISION NEEDED — who fills the roles.** The procedure above is complete;
> the assignment is not. The proposal is that the maintainer who authors the
> ground truth (D. Baker Effendi) takes the author role for all six cases, that
> the two reviewer slots per case are filled from the project's contributor pool
> with at least one non-Bifrost reviewer per case, and that a single
> non-Bifrost adjudicator is named for the whole wave rather than per case. A
> named adjudicator is required before adjudication opens — an unnamed
> adjudicator chosen after a disagreement appears is a tie-break chosen with
> knowledge of the tie. If the project cannot staff an independent adjudicator,
> the honest fallback is to declare it and publish the slice with every
> adjudicated case flagged as maintainer-adjudicated, not to quietly fill the
> seat.

## Invariants

1. No analyzer outcome influences selection, replacement, or ground truth.
2. The draw is reproducible from the committed seed and frame, and
   `cargo run -- validate` proves it.
3. Real-project outcomes never alter a synthetic-core denominator.
4. The real-project scorecard is a separate population, never pooled, never
   ranked, never compared number-to-number with a kernel score.
5. No rate over the slice generalizes beyond the six named repositories.
6. `inconclusive`, `unsupported`, and `runner-error` are never clean negatives.
7. Ground truth is adjudicated before the first analyzer runs, and every verdict
   is published.
8. A `pin_id` is never reused, and no pinned revision or digest is ever rewritten
   in place.
9. DataFlowBench pins and fetches upstream source; it never vendors it.

## Amendments

None. This document has not yet been amended; no analyzer has executed against
any pinned revision.
