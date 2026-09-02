# Proposing a new analyzer

This document packages the analyzer-admission policy for people outside the
repository — in particular for the maintainer of a tool who wants it measured
here. Everything below already governs the eight adapted analyzers and the
sixteen tools evaluated to date; the normative statements live in
[the adapter contract](adapters.md#analyzers-evaluated-and-not-adapted), the
[pin-currency policy](adapters.md#reference-tool-pin-currency), and the tier
preregistration contracts ([modeling](modeling-matrix.md#preregistration-and-immutability),
[native](native-profile.md)). This page states the same rules in one place and
lists what an integration must deliver.

Tool maintainers are encouraged to integrate their own analyzers. Nobody
knows a tool's operable surface better than the people who ship it, and the
benchmark's one maintainer-driven correction to date — Amendment A11, which
identified OpenTaint's value-kind boundary as a default rule configuration
rather than an engine limit — came from exactly that kind of upstream
knowledge. If any statement this benchmark publishes about your tool is
wrong, file an issue (the **result dispute** template) rather than working
around it; wrong claims are corrected by dated amendment, never left standing.

## The four eligibility bounds

An adapter admits an analyzer only when all four bounds hold. They are
applied identically to every candidate, and every tool evaluated is recorded
against them in
[the adapter contract](adapters.md#analyzers-evaluated-and-not-adapted) so
absence is never ambiguous:

1. **Semantic data flow.** The tool performs taint or value-flow analysis —
   the track this benchmark scores. Linters and rule/AST matchers without a
   flow engine would take a near-blanket `unsupported` and add no signal.
2. **Local, pinnable execution.** Analysis runs on this machine from an
   exactly pinned version, so evidence is reproducible. Cloud-submission
   services fail this bound even when the engine is real.
3. **Retained native output.** Machine-readable findings (SARIF/JSON) the
   runner can retain verbatim as raw evidence.
4. **Publishable results.** The license or terms of service must permit
   running the tool against a benchmark and publishing the outcome. Any
   restriction on comparative publication is disqualifying until explicit
   permission exists; we do not test first and ask later.

A candidate that clears the bounds on paper enters the queue by the standing
rule: **pinned version, probe-verified taint mode, and a partition
preregistered from documentation before any result exists.**

## The field-evaluation expectation

Eligibility is evaluated against the shipped surface, not the prospectus.
Every recent adapter earned its pin against the binary, and every one of them
found the shipped surface differed from the documentation that motivated the
evaluation:

- Infer's pinned release had removed the Quandary checker the tool was queued
  for, so the operable surface — Pulse's taint configuration — was
  established by probe before any population ran.
- FlowDroid's released CLI turned out to analyze APKs only, so what the
  evaluation established was that a minimal per-case APK is materializable
  from pinned, JVM-only pieces without changing what is measured.
- Pysa's pinned client turned out to require a second, separately released
  binary — the Pyrefly front end — whose absence of a project declaration
  silently unresolves every call, so the pin became a version pair and the
  silent mode a guarded part of the invocation.

A proposal should therefore expect to run probes: demonstrate on the pinned
binary that the claimed taint mode activates, that a known flow is reported,
and that the failure modes that would read as clean negatives fail loudly or
are guarded. Probe scripts are committed under `scripts/` and their raw
output retained under `reports/raw/`, so the evaluation is evidence, not
recollection.

## The pin and digest requirement

Every adapter names an exact upstream version, and every run witnesses it:
the runner checks the tool's self-reported version and refuses on mismatch,
and measures the binary's digest into `tool_build_identity` and the run's
`run-environment.json`. A tool that self-reports no version is pinned by
release-asset digest instead (OpenTaint is the precedent). Vendored rule or
model snapshots are pinned the same way and reviewed with the engine pin.

Pins do not drift silently: at every release freeze-prep each pin is
re-evaluated against upstream latest, and the outcome is either a bump with a
full re-run or a dated reason for holding, published in the release notes.
See [the pin-currency policy](adapters.md#reference-tool-pin-currency). A
maintainer who wants a newer version measured proposes a pin bump; the bump
re-runs every slice of that adapter, so no freeze contains mixed-version
evidence.

## Preregistration before any result

Partition decisions — which cells a tool is scored on and which are
`unsupported` by documented capability — are taken from the tool's
documentation **before any result exists**, and revised only by dated
amendment. This protects the tool as much as the benchmark: an incapacity
inside the scored partition is a measured mismatch, but a cell outside it is
a coverage fact, never a penalty, and the decision provably preceded the
evidence. Concretely:

- Kernel-tier capability decisions are taken from case metadata against the
  documented profile before the tool is invoked, and each declined cell
  retains a capability-decision document naming the documented boundary.
- The [modeling matrix](modeling-matrix.md) and
  [tool-native profile](native-profile.md) each require a preregistered
  partition row, added by dated amendment before the tool's first scored run
  in that tier.
- `unsupported`, `inconclusive`, and `runner-error` are evidence outcomes,
  never clean negatives, and no aggregate pools benchmark-controlled with
  tool-native results.

## New-adapter deliverables

A complete integration delivers all of the following.
[The Pysa adapter](../adapters/pysa/README.md) — the newest — is the model
for each item.

- [ ] **Pinned identity, witnessed from the binary.** Exact version (or
      asset digest), refused on mismatch per run, with binary digests
      measured into `tool_build_identity` and `run-environment.json`.
- [ ] **Configuration hash.** Every committed configuration artifact the run
      depends on (rules, model templates, taint config) bound into the
      report's `configuration_hash`.
- [ ] **Per-case retained evidence.** The verbatim native output per case
      under `reports/raw/<adapter>-<language>-<tier>/`, plus the phase-timing
      sidecar (`<case-id>-timing.json`) and, once per run,
      `run-environment.json`. `-error.json` diagnostics replace evidence
      where a stage failed.
- [ ] **Capability-decision documents** for every cell declined by
      documented capability, each naming the documented boundary it falls
      outside (`retained-capability-decision` evidence documents).
- [ ] **Preregistered partitions** for the modeling and native tiers, landed
      as dated amendments before the first scored run in each tier.
- [ ] **An adapter README** under `adapters/<tool>/`, following the shape of
      [`adapters/pysa/README.md`](../adapters/pysa/README.md): eligibility
      evaluation against the four bounds, pinned identity with witnesses,
      execution model, benchmark-controlled configuration, scored partition,
      outcome semantics, observed results, retained artifacts, and exact
      reproduction commands.
- [ ] **Runner integration** in `src/main.rs`. The touchpoints an integrator
      edits, with the Pysa arms as the worked example:
      - a run-command arm in the `Commands` enum (`RunPysaPythonKernel`,
        `RunPysaModeling`, `RunPysaNative`) and its dispatch in `main`;
      - a `ModelingTool` variant plus preregistered rows in the
        `MODELING_PARTITION` and `NATIVE_PARTITION` constants (partition
        revisions go through `NATIVE_PARTITION_AMENDMENTS`, one dated row
        per amended cell);
      - a normalization path mapping the tool's native output to the five
        outcome states (for Pysa: `parse_pysa_evidence`,
        `pysa_issue_anchor_match`, `pysa_rule_outcome`), including the
        activation guards that keep silent failures out of `not-reached`;
      - tests pinning the identity witness, the partition counts, the
        normalization semantics, and the retained-evidence shapes, in the
        same file's test module.

The last two run-quality gates are the same for everyone: `cargo fmt
--check`, `cargo test`, `cargo run -- validate`, and
`cargo run -- validate-reports` must pass, and a report enters a published
claim only through a validated freeze manifest
([the freeze contract](freeze.md)).

## Governance and corrections

DataFlowBench is deliberately small enough for one maintainer to land changes
directly and revise ([milestones](milestones.md)); there is no committee, and
adaptation decisions are the maintainer's. What keeps that model honest is
that every decision is written down against evidence, and every correction is
public:

- **Defects are corrected by dated amendment, never by silent edit.**
  Amendments state what changed, which template IDs and languages they touch,
  and which freezes they invalidate, and land as their own commits. Their
  numbers form a single repository-wide `A<n>` sequence across the five
  amendment-bearing documents; a new amendment takes the first number no
  heading anywhere claims (see
  [the amendment conventions](native-profile.md#amendments)).
- **Corrections distinguish their kind.** An **evidentiary correction**
  withdraws a factual claim without moving a scored cell; an **evidentiary
  confirmation** answers a recorded *to be verified* fact by measurement;
  a corrective amendment moves cells and names the freezes it invalidates.
- **Frozen evidence is never rewritten.** A corrected result is published as
  a new freeze with new revision and digests; the previously published
  manifest and its evidence stand.

An outside maintainer disputing a published outcome files the **result
dispute** issue template with the report path, the case ID, the raw-evidence
digest, the claimed correct outcome, and the supporting evidence. A dispute
that holds becomes an amendment in this taxonomy — as Amendment A11 did.
