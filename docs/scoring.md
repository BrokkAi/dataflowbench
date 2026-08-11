# Scoring contract

DataFlowBench scores semantic templates, not raw fixture counts. A template is a
language-neutral scenario identified by `template_id`. Every scored `core`
template must have exactly one positive and one minimally different negative
case for each language and model profile. Validation rejects an incomplete or
duplicated core pair.

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

## Model profiles

The `benchmark-controlled` profile supplies equivalent source, sink,
propagator, sanitizer, or procedure-summary models to each tool. It measures
the analysis engine under a common contract.

The `tool-native` profile evaluates models shipped by a tool. It measures useful
out-of-box product coverage. Results from the two profiles are never combined.
