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

M2 therefore continues with analyzer follow-ups for this JavaScript slice and
then ports the same semantics to Python.

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
results. Its runner selects exactly the 32 Python core assertions (16 balanced
positive/negative template pairs), creates one isolated database per case, and
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
`loop-carried-negative`. This evidence is limited to the Python core kernel.
The Python query pack is separate from the Java pack: it lives under
`adapters/codeql/python/` and owns the Python query plus its database-schema
dependency.

## M3: taint modeling

Add balanced categories for sources and sinks, propagators, sanitizers, opaque
library summaries, framework entry points, and persistence boundaries. Publish
benchmark-controlled and tool-native model profiles separately.

## M4: real-project confirmation

Add a small, pinned, manually reviewed corpus drawn from executable or
buggy/fixed upstream benchmarks. Keep these results separate from the synthetic
semantic core. Performance and typestate receive independent milestone plans
after the correctness contract is stable.
