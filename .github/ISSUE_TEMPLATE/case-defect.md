---
name: Case defect
about:
  Report a defect in a benchmark case itself — its semantics, polarity,
  markers, metadata, or provenance — as distinct from disputing a tool's
  result on it.
title: "Case defect: <case-id>"
---

<!--
A case defect is corrected by dated amendment naming the template IDs and
languages it touches and the freezes it invalidates — never by silently
editing the case. If your complaint is that a published result for a tool is
wrong on a correct case, use the result-dispute template instead.
-->

## The case

- **Case path:** <!-- e.g. cases/taint/python/... -->
- **Case ID and template ID:**
- **Language(s) and score tier affected:** <!-- core / challenge / modeling /
  native; a template defect may touch every language's spelling of it -->

## The defect

<!-- What the case claims, and what is wrong. Typical kinds:
  - the positive does not actually flow, or the negative actually does
    (state the semantics, not a tool's verdict — one tool's outcome is not
    evidence of a case defect);
  - the negative's mechanism is trivial or does not minimally mirror its
    positive partner;
  - DFB-* source/sink markers are misplaced or ambiguous;
  - metadata is wrong (capability requirements, model profile, dimension);
  - fixture provenance is wrong or incomplete
    (docs/fixture-provenance.md). -->

## Supporting evidence

<!-- Ground the claim: language semantics with a reference, a minimal
execution demonstrating the actual runtime behavior of the fixture where
that is decidable, or the provenance record that contradicts the metadata. -->
