# Milestones

Milestones are deliberately small enough for one maintainer to land directly
and revise. Follow-up issues are useful only when a slice needs independent
design discussion, external infrastructure, or parallel ownership.

## M0: contract and calibration

- Version the case contract around semantic templates, polarity, negative
  mechanisms, score tiers, semantic dimensions, and model profiles.
- Keep the bootstrap Java taint fixtures as non-scoring calibration cases.
- Reject unbalanced future core templates during validation.
- Document benchmark provenance and scoring before publishing scores.

## M1: breadth baseline and Java propagation kernel

First establish one balanced, benchmark-controlled direct-propagation pair in
every language/dialect supported by the Bifrost CLI. This 26-assertion breadth
baseline catches adapter, parser, and language-routing failures before deeper
language work begins.

Then author 16 Java benchmark-controlled templates, with one positive and one
negative case per template. Use four equally sized strata:

1. local propagation and flow-sensitive kills;
2. calls, returns, and context separation;
3. heap, field, alias, and object separation;
4. branches, loops, exceptions, and other control transfers.

The resulting 32 Java assertions form the first deep scored core. Test Bifrost
first; add CodeQL and Joern adapters after the fixture contract stabilizes, and
add OpenTaint when its neutral JVM-rule path is reproducible.

### Current M1 status

The figures in this section record the Bifrost v0.10.2 evidence frozen in
releases v0.1.0 and v0.2.0; the current numbers for these kernels are in the
M2 status section below.

The 26-assertion language breadth baseline and the complete 16-template Java
propagation kernel are implemented. The 32 Java assertions are balanced evenly
across the four planned strata:

| Stratum | Templates | Bifrost v0.10.2 | CodeQL v2.26.3 |
| --- | --- | --- | --- |
| Local propagation and kills | direct, overwrite, multi-step, expression | 6/8 complete matches | 6/8 correct |
| Calls and returns | call context, argument position, one-hop return, two-hop return | 8/8 correct | 8/8 correct |
| Heap and separation | objects, fields, aliases, arrays | 0/0 complete; 8 inconclusive | 6/8 correct |
| Control transfers | infeasible branch, branch join, loop kill, exception catch | 3/6 complete matches; 2 inconclusive | 6/8 correct |

These are benchmark results, not adapter expectations: complete false positives
remain `reached`, while incomplete analysis remains `inconclusive`. In total,
Bifrost has 17/32 Java assertions matching expected polarity (17 of 22 decisive
outcomes); 10 Java outcomes are `inconclusive` and one modeled external case
remains explicitly `unsupported`. CodeQL has 27 correct and 5 incorrect results
across all 32 assertions. The v0.10.2 Java outcomes match v0.10.1, but do not
restore the complete Java correctness observed in v0.9.5.

The JavaScript parity kernel is also implemented: it has the same 16
`template_id` values as Java and exactly one positive and one negative `core`
case for each template. The current retained Bifrost snapshot is evidence of
the adapter and analyzer behavior, not a claim that every JavaScript template
is already correct:

| Stratum | Templates | Bifrost outcomes | Polarity result |
| --- | --- | --- | --- |
| Local propagation and kills | direct, overwrite, multi-step, expression | 4 `reached`, 4 `not-reached` | 6/8 correct; 2 false positives/negatives |
| Calls and returns | call context, argument position, one-hop return, two-hop return | 4 `reached`, 4 `not-reached` | 8/8 correct |
| Heap and separation | objects, fields, aliases, arrays | 0 `reached`, 4 `not-reached`, 4 `inconclusive` | 2/4 decisive matches; 2 false negatives; 4 inconclusive (alias + array pairs) |
| Control transfers | infeasible branch, branch join, loop kill, exception catch | 6 `reached`, 2 `inconclusive` | 3/6 complete matches; 3 false positives |

Across the 32 JavaScript assertions, 14 are `reached`, 12 are `not-reached`,
and 6 are `inconclusive`; 19/26 complete outcomes match the canonical polarity
and 7 do not. The alias-propagation, array-element, and exception-catch pairs
are inconclusive because Bifrost reports incomplete analysis. The six
incomplete outcomes are not negative results and are excluded from false-
negative interpretation. The complete mismatches remain reportable evidence:
positive expression, object-separation, and same-object-field cases are false
negatives, while the negative branch-join, infeasible-branch, local-overwrite,
and loop-carried cases are false positives. See the [JavaScript adaptation
matrix](javascript-kernel.md) for the syntax-level adaptations.

M2 continued from this JavaScript slice by porting the same semantics to
Python and then to the languages listed in the applicability matrix.

## M2: cross-language parity

The same 16 templates are now ported to JavaScript and Python without changing
their semantic intent. Extend parity language by language where each construct
is meaningful. The Python adaptation rules, exact template population, and
modeled-external boundary are recorded in the [Python kernel contract](python-kernel.md).
Keep the Python, Java, and direct-flow result populations separate; a partial
or unsupported Python path remains capability evidence rather than a negative.
Language-only constructs live in `language-extension` scorecards.

The remaining ten languages — C, C++, C#, Go, Kotlin, PHP, Ruby, Rust, Scala,
and TypeScript — are classified in the [applicability
matrix](applicability-matrix.md). It fixes each language's core denominator
before any fixture is written: 15 templates for C and Rust, whose
exception-catch cell has no semantics-preserving native construct, and 16 for
the rest. Language-only constructs are routed to `language-extension`
scorecards instead of being dropped, and implementation is sequenced in three
tranches with one bounded child issue per language.

The Python CodeQL vertical slice is defined independently of the Bifrost
results. Its runner selects exactly the Python core assertions as one balanced
positive/negative pair per template — 32 over 16 templates when this milestone
was recorded, 58 over 29 since Python's
[challenge-tier row](challenge-tier.md) was rolled out — creates one isolated
database per case, and
retains a dedicated normalized report at `reports/codeql-python-kernel.json`
plus raw SARIF under `reports/raw/codeql-python-kernel/`. Source and sink anchors from
the case metadata remain attached to each normalized result. The five outcome
states remain distinct, so incomplete analysis is `inconclusive`, unsupported
coverage is `unsupported`, and execution failures are `runner-error` rather
than `not-reached`. The validated Python CodeQL run used CodeQL CLI 2.26.3
build `7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7` with
`codeql/python-all@7.2.3`: all 32 assertions produced 14 `reached` and 18
`not-reached` outcomes, with no `inconclusive`, `unsupported`, or
`runner-error`; 28/32 matched the expected polarity. The mismatches were
false negatives for `alias-propagation-positive`, `array-element-positive`,
and `exception-catch-positive`, and a false positive for
`loop-carried-negative`. This evidence is limited to the **v0.3.0
16-template** Python core kernel; the expanded-population CodeQL run is
deferred to the v0.4.0 freeze-prep re-run, because the report is freeze-bound.
See [the Python kernel contract](python-kernel.md).
The Python query pack is separate from the Java pack: it lives under
`adapters/codeql/python/` and owns the Python query plus its database-schema
dependency.

### Current M2 status

Release v0.3.0 freezes ten kernel languages — Java, JavaScript, TypeScript,
Python, Kotlin, C#, Go, C, C++, and Rust — with both a Bifrost v0.10.5
population and a CodeQL 2.26.3 population for each. C and Rust keep their
15-template (30-assertion) cores from the applicability matrix; the other
eight have 16-template (32-assertion) cores. These denominators are never
pooled. PHP, Ruby, and Scala remain breadth-only.

Core correct decisions in that freeze: Bifrost 32/32 on Java, JavaScript,
and Python, 30/32 on TypeScript, 19/32 on Kotlin, 10/32 on Go, and 2 of the
core assertions on C#, C++, C, and Rust, where deep propagation is still
direct-only and the remaining cases report incomplete analysis — including
an 8-case `runner-error` stratum on Rust (`internal_invariant`). CodeQL
produces definitive outcomes for every kernel assertion, ranging from 26/32
to 29/32 on the 16-template cores and 27/30 (C) and 28/30 (Rust, via the
pre-1.0 preview extractor, with zero false negatives) on the 15-template
cores. Ruby breadth remains inconclusive. See
[`releases/v0.3.0.md`](releases/v0.3.0.md) for the bound evidence.

### Expanded breadth: the preregistered challenge tier

M2's sixteen-template core is saturating — Bifrost v0.10.5 takes 32/32 on Java,
JavaScript, and Python in the v0.3.0 freeze — so a harder tier of thirteen
templates is preregistered in the
[challenge-tier document](challenge-tier.md) before any fixture is authored or
any analyzer is run against one. Those templates are `core`, not a new score
tier: v0.4.0 is the first expanded-breadth release, and each language's core
denominator grows from 16 templates to 16 plus its applicable challenge
templates (24 for C, 27 for Rust, 28 for C++, 29 elsewhere). The v0.3.0 and
v0.4.0 cores are different populations and are never compared number-to-number;
the frozen v0.3.0 evidence is unaffected because freeze validation is
manifest-scoped.

### Current expanded-breadth status

Release v0.4.0 is that first expanded-breadth freeze: 744 cases and 42 bound
reports at one fixture revision, with all thirteen kernels carrying their
expanded core denominators and four analyzer populations — Bifrost v0.10.6
(build `18d09c57`) over the pinned 118-case breadth slice plus thirteen
kernels, CodeQL 2.26.3 over eleven, Joern 4.0.610 over six, and Semgrep CE
1.174.0 over eleven. Coverage differs per analyzer; a language with no report
for an analyzer is coverage, not a score.

The tier did what it was preregistered to do: no analyzer answers a whole
expanded core correctly in any language, so the core no longer saturates.
Bifrost decides 115 of the 118 breadth-slice cases and 227 of its 738 core
assertions, 222 of those decisions correct, declining the rest as
`inconclusive`; its `element-object` `internal_invariant` failures and its
fully inconclusive Ruby kernel are published as retained execution and
capability coverage and tracked upstream. CodeQL produces a definitive answer
for all 626 of its bound assertions, 509 correct, with dynamic dispatch its
systematic miss. Joern answers all 344 of its assertions, 270 correct, and its
depth-6 behavior tracks the call-depth bound the preregistration verified in
advance. Semgrep CE scores the 154-assertion intraprocedural partition of its
populations and declines the other 468 by declared capability. See
[`releases/v0.4.0.md`](releases/v0.4.0.md) for the bound evidence.

## M3: taint modeling

Add balanced categories for sources and sinks, propagators, sanitizers, opaque
library summaries, framework entry points, and persistence boundaries. Publish
benchmark-controlled and tool-native model profiles separately.

### M3 begins: the preregistered modeling matrix

M3 opens with the [taint-modeling matrix](modeling-matrix.md), preregistered
before any modeling fixture, model file, or run exists, under the same amendment
contract as the challenge tier. It fixes twelve templates in those six
categories — one positive and one minimally different negative each, 24
assertions per language — for Java, JavaScript, and Python, defines each model in
analyzer-neutral terms so the four adapters encode the same declaration in their
own native surfaces, and preregisters per-tool capability partitions so that a
category a tool cannot activate is recorded as `unsupported` in advance rather
than discovered as a failure. Unlike the challenge tier, these templates are
**not** `core`: `score_tier` gains `modeling`, and modeling assertions have their
own scorecards and never enter any language's core denominator. Issue #16's
tool-native profiles build on the same category taxonomy and supply no models.

### Wave M1: Python, JavaScript, Java — complete

All three languages of the matrix's first wave have landed, one pull request
each, on the same four runners and the same shared `modeling.sc`:
[Python](python-modeling.md), [JavaScript](javascript-modeling.md), and
[Java](java-modeling.md). Each row is twenty-four assertions, four per-adapter
model artifacts encoding the same analyzer-neutral declarations, and four runs.

No template proved unimplementable as preregistered, and every partition cell
that moved moved by a **dated amendment on the preregistration**, never by an
edit to a table: A2 (Joern's propagator and summary categories are not
load-bearing), A3 (Semgrep's sanitizer-selectivity cell is undecidable by
construction), A4 (the reflective opaque-propagator body is followed unaided —
extended from `jssrc2cpg` to `javasrc2cpg` by the Java row), and A5 (Bifrost
v0.10.6 accepts `:unmodeled require-model`, an evidentiary confirmation that
moves no cell). Observations made before an amendment applied are retained in
the language rows as evidence rather than deleted.

Across the three rows the results are the same shape cell for cell, which is the
point of running three languages against one design: CodeQL 24/24 everywhere,
Joern 14/16 with the same two category-B false negatives, Semgrep CE 10/10, and
Bifrost 4/4 on Python and Java — JavaScript's three `inconclusive` category-S
cells are that language's engine incompleteness rather than a modeling property.
The remaining ten languages have no modeling denominator until the applicability
pass merges, which is different from having a zero.

### The tool-native profile: preregistration and infrastructure

M3's second half opens with the [tool-native profile](native-profile.md),
preregistered on the same amendment contract before any native fixture or
vendored ruleset exists. Where the modeling matrix measures the *engine* under
equivalent supplied models, this profile measures the *product*: the sources,
sinks, sanitizers, summaries, and entry points each tool ships and activates by
default or by its own documented native configuration. It reuses the matrix's six
categories — one template each, over real platform APIs — so the two can be read
side by side, and it shares the `modeling` score tier while being separated from
it by `model_profile` alone, with corpus-wide validation that the two populations
never cross-select. No aggregate combines native coverage with controlled
accuracy.

The canonical kernels are deliberately **not** run natively: they flow from
`dfb_source` to `dfb_sink`, which no shipped model set knows, so a native run
over them would measure the absence of an invented name. The preregistered
activation partition enters with **CodeQL 6 templates of 6** — pinned to the
shipped `security-extended` suites of `codeql/{java,javascript,python}-queries`
with the `local` threat-model group — and **Bifrost, Joern, and Semgrep CE at 0
of 6**, each with a verified rationale: no shipped endpoint catalog in the
standalone policy CLI (BrokkAi/bifrost-dev #2620, #2691), `DefaultSemantics`
shipping flow constraints but no source or sink catalog and a `joern-scan` query
database that is downloaded rather than shipped, and a Semgrep ruleset that is
unpinnable at run time until a snapshot is vendored. Wave N1 rolls out Java,
JavaScript, and Python, one pull request each.

### Wave N1 in progress

[JavaScript's native probe set](javascript-native.md) has landed: twelve
assertions over `process.env`, `process.argv`, `child_process.execSync`,
`path.join`, `encodeURIComponent`, and the `Buffer` base64 round trip, plus the
first vendored Semgrep snapshot (`semgrep/semgrep-rules@40b8c63f`, thirty rules)
and the CodeQL native execution arm. CodeQL scores **10 of 12** against the 50%
blind baseline; Bifrost, Joern, and Semgrep decline all six templates without
being invoked. The two mismatches are both preregistered product facts:
`encodeURIComponent`'s sanitizer credit is scoped to the XSS and request-forgery
query families and not to command injection, and the `process.env` write/read
store boundary is unlinked in the direction that carries a real flow while the
plain environment source fires in the direction where the key says there is
none.
[Amendment N1](native-profile.md#n1--2026-08-27--semgrep-ces-javascript-cells-evaluated-against-the-vendored-snapshot)
resolves Semgrep CE's six JavaScript cells against the vendored snapshot and
retains all six as unsupported: every taint rule in the official JavaScript
security set roots its sources in a function parameter or a framework request
object, so a rule with the right sink has no applicable source.

## M4: real-project confirmation

Add a small, pinned, manually reviewed corpus drawn from executable or
buggy/fixed upstream benchmarks. Keep these results separate from the synthetic
semantic core. Performance and typestate receive independent milestone plans
after the correctness contract is stable.
