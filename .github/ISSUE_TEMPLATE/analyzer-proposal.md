---
name: Analyzer proposal
about:
  Propose a new analyzer for adaptation. The four eligibility bounds are
  evaluated against the shipped surface of a pinned binary; see
  docs/new-analyzer.md for the full policy and deliverables checklist.
title: "Analyzer proposal: <tool>"
---

<!--
Tool maintainers are encouraged to propose and integrate their own
analyzers. Read docs/new-analyzer.md first: eligibility is evaluated in the
field, against the pinned binary, not the prospectus, and a candidate enters
the queue with a pinned version, a probe-verified taint mode, and a
partition preregistered before any result exists.
-->

## Tool

- **Name and upstream:**
- **Proposed pin:** <!-- exact version; or release-asset digest if the tool
  self-reports no version (OpenTaint is the precedent) -->
- **How the pin is witnessed from the binary:** <!-- e.g. `tool --version`
  output; binary digest -->

## The four eligibility bounds

State the evidence for each; a bare checkmark is not an evaluation.

- [ ] **Semantic data flow.** The tool performs taint or value-flow
      analysis — a real flow engine, not rule/AST matching.
      Evidence:
- [ ] **Local, pinnable execution.** Analysis runs locally from the exact
      pin, with no account, network, or service dependency.
      Evidence:
- [ ] **Retained native output.** Machine-readable findings (SARIF/JSON)
      retainable verbatim as raw evidence.
      Evidence:
- [ ] **Publishable results.** License/terms permit benchmarking and
      publishing the outcome, with no comparative-publication restriction.
      Evidence: <!-- license name and link; quote any relevant terms -->

## Proposed profile

- **Languages / populations:** <!-- one result population per language -->
- **Taint mode to be probe-verified:** <!-- the shipped mode that will be
  activated, and how activation will be proven from retained evidence -->
- **Known silent-failure modes and guards:** <!-- anything that would read
  as clean negatives without a guard -->
- **Documented capability boundaries** (for preregistering `unsupported`
  cells, if any):

## Integration

- [ ] I maintain this tool / I am proposing on behalf of its maintainers
- [ ] I intend to implement the adapter myself (see the deliverables
      checklist in docs/new-analyzer.md)
