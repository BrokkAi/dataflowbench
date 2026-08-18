---
title: Scoring
description: How outcomes become rates, and why denominators are explicit.
---

For a **positive** case, `reached` is a true positive and `not-reached` is a
false negative. For a **negative** case, `not-reached` is a true negative and
`reached` is a false positive. `inconclusive`, `unsupported`, and
`runner-error` are reported as capability and execution coverage with their
own counts.

## Rates

Per semantic dimension, the site shows exact fractions — numerator and
denominator — over definitive outcomes only. A dimension with no definitive
result publishes **n/a**, never a misleading zero.

Headline rates are **macro-averages**: template rates are averaged within a
semantic dimension, then dimension rates are averaged. Raw case counts remain
visible for audit but are not micro-averaged into a headline number.

## Separate populations

The direct-flow breadth baseline, each 16-template language kernel, and
calibration cases have separate denominators. Results from one population are
never evidence about another.

## Where the numbers come from

Every count and rate on this site is rendered from
[`results/results.json`](https://github.com/BrokkAi/dataflowbench/blob/main/results/results.json),
which `generate-results` derives from a validated immutable freeze. CI runs
`generate-results --check`, so a page whose numbers drift from the frozen
evidence cannot merge. Hand-authored prose on this site carries no numbers of
its own.

The full contract: [scoring.md](https://github.com/BrokkAi/dataflowbench/blob/main/docs/scoring.md).
