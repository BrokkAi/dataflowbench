# Scoring contract

DataFlowBench scores semantic templates, not raw fixture counts. A template is a
language-neutral scenario identified by `template_id`. Every scored `core`
template must have exactly one positive and one minimally different negative
case for each language and model profile. Validation rejects an incomplete or
duplicated core pair. The Python parity population is additionally required to
contain the exact 16 IDs in the [Python kernel contract](python-kernel.md), so
an omitted template cannot be hidden by a balanced but smaller subset.

`calibration` cases exercise schemas and adapters but do not contribute to a
correctness score. `language-extension` and `real-project` cases have their own
scorecards and never change the denominator of the cross-language core.

## Outcome interpretation

For a positive case, `reached` is a true positive and `not-reached` is a false
negative. For a negative case, `not-reached` is a true negative and `reached` is
a false positive. `unsupported`, `inconclusive`, and `runner-error` are reported
as capability or execution coverage and are never converted into false
negatives or true negatives.

Reports publish, at minimum:

- true-positive rate and false-positive rate for each semantic dimension;
- supported, inconclusive, unsupported, and runner-error counts;
- results by negative mechanism and model profile;
- macro-averages over templates and then semantic dimensions.

Raw assertion counts may be shown for auditability but are not micro-averaged
into a headline score. Taint, value-flow, typestate, witness quality, and
performance remain separate score dimensions and scorecards.

## Balanced pairs and the blind baseline

Every scored core template contributes exactly one positive and one minimally
different negative assertion, and validation rejects an unbalanced pair. The
population is therefore TP/TN-balanced by construction, which fixes a floor
worth stating plainly: an analyzer that always answers the same way — or that
cannot see a construct at all but still emits an answer — scores exactly half
on the affected pairs. Answering "no flow" on a pair whose callee the engine
never resolves banks a true negative and a false negative together; the true
negative is right for the wrong reason. The 0.4.0 evidence shows the pattern
concretely: on the dynamic-dispatch strata, an engine that declines to follow
the selected callee converts every pair into one free true negative plus one
false negative, while an engine that reports incomplete analysis instead takes
no credit at all.

Published correctness must therefore be read against the 50% blind baseline,
not against zero, and the per-stratum true-positive/false-positive rates —
not the raw correct count — carry an engine's approximation character: an
over-approximator spends its errors as false positives on negatives, an
under-approximator as false negatives on positives, and an engine that
declines honestly appears in the coverage columns rather than either error
column. This is also why `inconclusive`, `unsupported`, and `runner-error`
are never converted into negatives: doing so would hand the blind baseline
to any engine that fails loudly.

## Separate result populations

The direct-flow breadth baseline, the 16-template Java kernel, the
16-template Python kernel, and calibration-only cases have separate
denominators and result sections. The direct baseline checks language routing
and adapter plumbing; Java and Python parity test the deep semantic kernel;
calibration cases exercise capabilities such as one-hop helpers or activated
external summaries without changing a core denominator. Results from one
population are not evidence that another population completed successfully.

The [benchmark-controlled taint-modeling matrix](modeling-matrix.md) joins that
list as a further separate population, on its own `modeling` score tier. It asks
a different question from every kernel — not whether an engine can follow flow it
can see, but whether it activates a model it was given — so its assertions never
enter a core denominator and are never pooled or averaged with a propagation
score. Its pairs are balanced for the same reason the kernels' are: an engine
that ignores a supplied model answers "no flow" on both cells of every category
it did not activate and banks half the assertions, so modeling results are read
against the same 50% blind baseline, with per-category true-positive and
false-positive rates carrying the evidence rather than the raw correct count.

The [real-project confirmation slice](real-project-preregistration.md) is a
further separate population, on the `real-project` tier. It asks whether the
semantics the kernels measure survive contact with an upstream repository, over
six pinned projects drawn by a seeded, preregistered sample. Its unit is a
repository at two pinned revisions rather than an authored pair, so its
negatives are weaker evidence than a synthetic negative and are labelled as
such. Its claims are bounded to the named repositories: no rate over the slice
generalizes, nothing in it is ranked, and no real-project outcome ever changes a
core denominator.

An analyzer may report a candidate finding with incomplete discovery or an
incomplete witness. That evidence remains `inconclusive` until the tool proves
the required path. It must not be normalized to `not-reached` merely because
no complete witness was emitted; this prevents incomplete analysis from being
counted as a negative.

## Model profiles

The `benchmark-controlled` profile supplies equivalent source, sink,
propagator, sanitizer, or procedure-summary models to each tool. It measures
the analysis engine under a common contract.

The `tool-native` profile evaluates models shipped by a tool. It measures useful
out-of-box product coverage. Results from the two profiles are never combined.

The [tool-native profile preregistration](native-profile.md) makes that second
profile concrete: six templates over real platform APIs, one per category of the
benchmark-controlled matrix, on the same `modeling` score tier and separated from
it by `model_profile` alone. Its scorecards are therefore separate populations in
the sense this document already uses — a native card and a benchmark-controlled
card of the same language and tier are never merged, and no aggregate combines
native coverage with controlled engine accuracy. Its pairs are balanced for the
same reason every other population's are, so native coverage is read against the
same 50% blind baseline: a tool whose shipped set does not know an API answers
"no flow" on both cells and banks half the assertions. One reading rule is
specific to it: a native finding that fires on the *existence* of a dangerous
sink, with no flow requirement, is scored on the cell it lands in — a true
positive on the positive and a false positive on the negative — because that is
the product behavior being measured, not an artifact to be excused.
