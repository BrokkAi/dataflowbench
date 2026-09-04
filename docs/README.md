# Documentation index

This directory holds both the benchmark's contract documents and the Astro
Starlight package for the public site (`astro.config.mjs`, `src/`,
`public/`). The site renders only a handful of pages; the contract surface
below is repo-only and this index is its map. Documents fall into two kinds:
**normative contracts**, which bind what the benchmark does going forward,
and **historical records**, which preserve what was decided, measured, and
released. Six contract documents also carry the repository's amendments —
see the glossary entry below.

## Normative contracts

| Document | What it binds |
| --- | --- |
| [adapters.md](adapters.md) | The adapter contract: the five normalized outcomes, no synthesized results, retained raw evidence, phase timings and the environment stamp, pin-currency policy, per-analyzer population sections, and the analyzer-election bounds. Amendment-bearing. |
| [new-analyzer.md](new-analyzer.md) | The analyzer-admission policy packaged for outside maintainers: the four eligibility bounds, the field-evaluation expectation, the pin/digest and preregistration requirements, the new-adapter deliverables checklist, and the governance and correction mechanism. |
| [adding-an-adapter.md](adding-an-adapter.md) | The step-ordered integration walkthrough for a new analyzer adapter, including the source-tree touchpoints and the shared adapter contract in `src/adapters/mod.rs`. |
| [scoring.md](scoring.md) | The scoring contract: templates not fixture counts, balanced pairs, outcome interpretation, the 50% blind baseline, separate populations, and the model-profile split. |
| [freeze.md](freeze.md) | The `freeze/v1` immutable evidence-manifest contract, the rule that a correction is a new freeze, never a rewrite, the freeze-prep checklist (whose pin-currency step operates the adapters.md policy), and the release-notes template with its pin table. |
| [results.md](results.md) | The result-generation contract: byte-stable artifacts generated only from a validated freeze, provable with `--check`. |
| [applicability-matrix.md](applicability-matrix.md) | How the propagation templates port across languages: the `direct` / `adapted` / `n/a` classification and each language's core denominator. |
| [challenge-tier.md](challenge-tier.md) | Preregistration of the thirteen challenge templates in four strata, the fold-into-core decision, and the amendment procedure. Amendment-bearing. |
| [modeling-matrix.md](modeling-matrix.md) | Preregistration of the benchmark-controlled taint-modeling matrix, on its own `modeling` tier. Amendment-bearing. |
| [native-profile.md](native-profile.md) | Preregistration of the tool-native model profile: shipped-model coverage, never pooled with the controlled matrix. Amendment-bearing. |
| [latency-tier.md](latency-tier.md) | Preregistration of the descriptive latency-characterization tier and the per-adapter granularity table. Amendment-bearing. |
| [real-project-preregistration.md](real-project-preregistration.md) | Preregistration of the real-project confirmation slice: the advisory-derived population, the eligibility criteria, the seeded draw and its replacement rule, the bounded per-repository claims, the independent ground-truth review, and the rule that no real-project outcome touches a core denominator. Amendment-bearing. |
| [fixture-provenance.md](fixture-provenance.md) | The required provenance fields for every fixture and the MIT/CC0 licensing split. |
| [benchmark-sources.md](benchmark-sources.md) | The external suites treated as design inputs, and why none is imported as ground truth. |

## Per-language kernel contracts

The thirteen `*-kernel.md` documents are one family: each ports the Java
propagation kernel to one language, preserving template identities,
polarity, and negative mechanisms, and states that language's classic and
expanded denominators. Each is half contract, half run record — the
adaptation tables bind, the dated results sections record.

[java-kernel.md](java-kernel.md) (the origin population) ·
[javascript-kernel.md](javascript-kernel.md) ·
[python-kernel.md](python-kernel.md) ·
[typescript-kernel.md](typescript-kernel.md) ·
[kotlin-kernel.md](kotlin-kernel.md) ·
[csharp-kernel.md](csharp-kernel.md) ·
[go-kernel.md](go-kernel.md) ·
[c-kernel.md](c-kernel.md) ·
[cpp-kernel.md](cpp-kernel.md) ·
[rust-kernel.md](rust-kernel.md) ·
[ruby-kernel.md](ruby-kernel.md) ·
[php-kernel.md](php-kernel.md) ·
[scala-kernel.md](scala-kernel.md)

## Per-language modeling and native rows

Two smaller families on the `modeling` score tier, separated from each
other by `model_profile` and never pooled:

- Benchmark-controlled rows (wave M1) —
  [python-modeling.md](python-modeling.md) ·
  [javascript-modeling.md](javascript-modeling.md) ·
  [java-modeling.md](java-modeling.md)
- Tool-native rows (wave N1) —
  [java-native.md](java-native.md) ·
  [javascript-native.md](javascript-native.md) ·
  [python-native.md](python-native.md)

## Historical records

- [milestones.md](milestones.md) — the M0–M4 roadmap with dated status
  sections; names the governance model in passing.
- [releases/](releases/) — one immutable snapshot per published release
  (`v0.1.0.md` through `v0.7.0.md`): the freeze identity, the bound
  evidence, the scorecards, and which amendments the cycle recorded.
  Release notes cite amendments; they never hold them.

## Glossary

- **Template** — a language-neutral semantic scenario identified by a
  stable `template_id`. DataFlowBench scores templates, not raw fixture
  counts, and a template is never renamed, split, merged, or silently
  dropped.
- **Assertion** — one scored case outcome. Every scored `core` template
  yields exactly two per language and model profile: one positive and one
  minimally different negative, which is why populations read "29 templates
  / 58 assertions" and why correctness is read against the 50% blind
  baseline.
- **Kernel** — one language's scored propagation population: the ported
  classic sixteen plus its applicable challenge templates, fixed by that
  language's kernel contract.
- **Core** — the `score_tier` whose denominator is the scored
  cross-language propagation population, as opposed to `calibration`,
  `language-extension`, `modeling`, and `real-project`, which never change
  a core denominator.
- **Challenge tier** — the thirteen preregistered harder templates of
  [challenge-tier.md](challenge-tier.md). Despite the name it is not a
  separate score tier: the templates carry `score_tier: "core"` and fold
  into each language's kernel, growing its denominator; the classic and
  expanded populations are never compared number to number.
- **Stratum** — a named subgroup of templates within a kernel that
  isolates one well-known engine limit (for the challenge tier: A dynamic
  dispatch and reflection, B higher-order flow, C containers and deep
  access paths, D context and depth stress). Per-stratum breakdowns are
  always reported so a fold-in cannot hide them. The real-project slice reuses
  the word for its per-language sampling strata, which are drawn independently
  and never pooled.
- **Wave** — a bounded rollout unit that adds one language's fixtures (or
  one language row of a tier) and its adapter artifacts without editing any
  template definition. Waves are numbered per tier: M1 is the
  benchmark-controlled modeling rows, N1 the tool-native rows, R1 the first
  real-project confirmation slice.
- **Benchmark-controlled vs tool-native profile** — the two values of
  `model_profile` and a hard partition of every claim. The controlled
  profile supplies equivalent models to each tool and measures the
  *engine*; the native profile evaluates the models a tool *ships* and
  measures the product. Results from the two are never combined, and the
  freeze validator rejects pooling.
- **Amendment** — the only sanctioned way to change a preregistered
  definition after the first analyzer has run against it: a dated entry
  stating what changed, why, and which freezes it invalidates, in a
  separate commit from any fixture or result change. Numbering is a single
  repository-wide sequence (A1, A2, …); the authoritative index is the set
  of amendment headings across the six amendment-bearing documents
  ([challenge-tier.md](challenge-tier.md),
  [modeling-matrix.md](modeling-matrix.md),
  [native-profile.md](native-profile.md), [adapters.md](adapters.md),
  [latency-tier.md](latency-tier.md),
  [real-project-preregistration.md](real-project-preregistration.md)), so each
  document's own numbering is deliberately gappy.
- **Freeze-bound** — a report whose bytes are digest-bound by a published
  `freeze/v1` manifest and may not be overwritten. A freeze-bound report is
  deferred to the next freeze-prep re-run rather than re-run in place;
  deferral is not absence of coverage.
- **Recorded-only** — a slice an engine could legitimately run but that the
  maintainer scoped out, with the exclusion written into the record so its
  absence is never misread as a tool limitation.
- **Preregistered partition** — the per-tool, per-template decision, fixed
  from the pinned distribution's own documentation before any result
  exists, of which cells are scored and which are declined `unsupported` by
  declared capability. Keyed by template ID so no observed result can move
  a case between the partitions.
- **Pin declaration vs retained-evidence description** — a pin literal
  either declares what the benchmark pins going forward or describes what
  retained evidence already witnessed. A pin review moves declarations
  only; retained-evidence descriptions move with the report bytes that
  produced them.
- **Slice** — one adapter × language × population unit of execution and
  reporting; the aggregation unit for latency and for raw-evidence
  directories (`reports/raw/<slice>/`).
- **Real-project confirmation slice** — the six pinned upstream repositories
  of [real-project-preregistration.md](real-project-preregistration.md), on
  the `real-project` score tier. Its unit is a repository at two pinned
  revisions, vulnerable and fixed, rather than an authored fixture; its
  selection artifacts live under `corpus/real-project/` and are replayed by
  `cargo run -- validate`. Confusingly close to the term above and distinct
  from it: this one is a population, that one is an execution unit.
- **Draw record** — `corpus/real-project/draw.json`: the seed, the retained
  frame it consumed, and the ordered walk over each stratum with a disposition
  for every candidate the walk reached. It is what makes "analyzer outcomes did
  not influence selection" a checkable claim instead of an assurance.
