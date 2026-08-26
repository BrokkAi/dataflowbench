---
title: Methodology
description: Tracks, semantic templates, model profiles, and outcome semantics.
---

DataFlowBench separates **what** is asked from **who** answers it.

## Tracks and dimensions

Cases belong to one semantic track — `taint`, `value-flow`, `typestate` — with
`witness` quality and `performance` as further score dimensions. A frozen
report binds exactly one track, one score dimension, and one model profile,
and results are never pooled across those partitions or into a combined
leaderboard.

## Semantic templates

A template is a language-neutral scenario identified by `template_id` — for
example alias propagation, loop-carried kills, call-context separation, or
infeasible branches. Every scored `core` template has exactly one positive
case and one minimally different negative case per language and model
profile, so a tool cannot look good by pattern-matching one polarity.

## Balanced pairs and the blind baseline

Every scored template is one positive and one minimally different negative
assertion, so the population is TP/TN-balanced by construction. An analyzer
that always answers the same way — or that cannot see a construct but still
answers — scores exactly half on the affected pairs: the true negative it
banks on a pair whose flow it never resolved is right for the wrong reason.
Read correctness against that 50% blind baseline, not against zero, and read
approximation character from the per-stratum TPR/FPR split: over-approximators
spend errors as false positives, under-approximators as false negatives, and
engines that decline honestly appear as coverage instead of either.

## Score tiers

- `calibration` cases exercise schemas and adapters; they are not scored.
- `core` is the cross-language correctness population.
- `language-extension` and `real-project` tiers have their own scorecards and
  never change core denominators.

## Model profiles

The `benchmark-controlled` profile supplies equivalent source, sink,
propagator, and summary models to every tool, measuring the analysis engine
under a common contract. The `tool-native` profile measures shipped models.
The two are separately scored and never combined.

## Outcomes

Adapters normalize each case to one outcome:

| Outcome | Meaning |
| --- | --- |
| `reached` | The analyzer reports the flow. |
| `not-reached` | The analyzer affirmatively reports no flow. |
| `inconclusive` | Analysis was incomplete; no claim either way. |
| `unsupported` | The analyzer declares the capability out of scope. |
| `runner-error` | Execution failed; evidence retained. |

Incomplete outcomes are **never** converted into negatives — an analyzer that
crashes or gives up is not credited with staying quiet.

The authoritative contracts live in the repository:
[scoring](https://github.com/BrokkAi/dataflowbench/blob/main/docs/scoring.md),
[adapters](https://github.com/BrokkAi/dataflowbench/blob/main/docs/adapters.md),
[freeze](https://github.com/BrokkAi/dataflowbench/blob/main/docs/freeze.md), and
[result generation](https://github.com/BrokkAi/dataflowbench/blob/main/docs/results.md).
