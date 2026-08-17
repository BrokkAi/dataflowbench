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
performance remain separate scorecards.

## Separate result populations

The direct-flow breadth baseline, the 16-template Java kernel, the
16-template Python kernel, and calibration-only cases have separate
denominators and result sections. The direct baseline checks language routing
and adapter plumbing; Java and Python parity test the deep semantic kernel;
calibration cases exercise capabilities such as one-hop helpers or activated
external summaries without changing a core denominator. Results from one
population are not evidence that another population completed successfully.

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
