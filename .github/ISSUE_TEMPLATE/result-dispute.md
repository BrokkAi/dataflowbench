---
name: Result dispute
about:
  Dispute a published outcome for a specific case. A dispute that holds is
  corrected by dated amendment and, where frozen evidence is affected, a new
  freeze — never by editing the published record.
title: "Result dispute: <adapter> / <case-id>"
---

<!--
Tool maintainers are the intended filers: if this benchmark states something
wrong about your tool, say so here. The precedent is Amendment A11, in which
OpenTaint's maintainer identified a measured "value-kind boundary" as a
default rule configuration; the amendment enabled primitive tracking and
re-ran both populations. Corrections land as dated amendments in the
repository's single A<n> sequence (docs/new-analyzer.md, "Governance and
corrections"); previously published freezes are never rewritten.
-->

## The disputed result

- **Report path:** <!-- e.g. reports/pysa-python-kernel.json -->
- **Case ID:** <!-- the case_id of the disputed assertion -->
- **Raw-evidence digest:** <!-- the retained_evidence digest recorded in the
  report for this case, so the dispute names one exact artifact -->
- **Published outcome:** <!-- reached / not-reached / unsupported /
  inconclusive / runner-error, as the report states it -->

## The claimed correct outcome

<!-- What the outcome should be, and which kind of correction this is:
  - an evidentiary correction (a stated factual claim is wrong; no scored
    cell need move),
  - a configuration or activation defect (the tool was run outside its
    operable configuration — the A11 shape),
  - a normalization defect (the native output was mapped to the wrong
    outcome state), or
  - a partition defect (a cell is scored that documented capability
    excludes, or vice versa). -->

## Supporting evidence

<!-- The argument, grounded in artifacts: the retained raw evidence itself,
a reproduction against the same pin (name the exact version/digest and the
command), upstream documentation of the shipped surface, or a probe script.
Claims about what the tool "should" do without evidence from the pinned
binary cannot move a result. -->
