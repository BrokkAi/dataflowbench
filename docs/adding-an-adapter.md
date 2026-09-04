# Adding an adapter

This is the step-ordered integration walkthrough for a new analyzer adapter.
It packages what already binds every shipped adapter — the [adapter
contract](adapters.md), the [scoring contract](scoring.md), and the shape of the
adapter modules — into one path an integrator can follow. It does not relax any
of it: the contract documents stay normative, and where this guide and a
contract document disagree, the contract document wins.

Whether an analyzer is *eligible* at all — the four admission bounds, the
field-evaluation expectation, the pin/digest requirement — is decided under
["Analyzers evaluated and not adapted"](adapters.md) before any integration
work starts; that election policy is packaged for outside maintainers in
[Proposing a new analyzer](new-analyzer.md). This guide assumes the analyzer
has already been admitted and pinned.

The best onboarding artifacts in this repository are the shipped adapter
READMEs. Read two before writing any code: the
[Pysa adapter](../adapters/pysa/README.md) is the newest and shows the
current expected shape end to end (eligibility evaluation, probe-established
configuration, silent-failure guards, witnessed pins, per-case evidence), and
the [Joern adapter](../adapters/joern/README.md) shows a multi-language
adapter that keeps one engine behind strictly separate per-language
populations. A new adapter's README is expected to stand at that level of
detail, because the README *is* the published capability record.

## 1. Required inputs

An adapter consumes canonical cases; it never gets its own case syntax.

- **Case metadata.** Every case is a `case.json` under
  `cases/<track>/<language>/` validating against
  `schemas/case.schema.json`. The fields the runner reads per case are the
  declared `fixture_files`, the `source_anchors` and `sink_anchors`, the
  expected flows and nonflows, the `execution_budget`, and the selection
  fields (`language`, `track`, `score_tier`, `model_profile`).
- **DFB markers.** Anchors are stable `DFB-*` markers placed in fixture
  comments. The adapter reconciles tool findings against these markers —
  by file and marker line, never by guessing at tool-internal locations —
  so a result is `reached` only when the tool's own evidence lands on the
  benchmark's declared anchors.
- **Native rules and models.** Canonical cases never contain native rule
  syntax. Whatever the tool needs — a taint rule, a `.pysa` model file, a
  CPG query script, a source/sink declaration list — is committed under
  `adapters/<tool>/` and hashed into the report's `configuration_hash`.

## 2. The five outcomes and the normalization rules

An adapter normalizes raw tool output to exactly the five states in
`schemas/result.schema.json`:

- `reached` — the tool's retained evidence shows the flow, reconciled to the
  case's declared anchors.
- `not-reached` — the tool ran to completion, its activation is proven, and
  the retained evidence shows no flow for the declared anchors.
- `inconclusive` — the tool reported something the adapter cannot reconcile
  to the anchors, or reported incomplete analysis. Counted as coverage,
  never as a negative.
- `unsupported` — the case is outside the tool's documented profile, decided
  from case metadata by a preregistered partition *before* the tool is ever
  invoked. Excluded from false-negative interpretation.
- `runner-error` — the invocation failed: nonzero exit, missing or
  malformed output, a model that failed to bind. The raw failure evidence
  is retained.

The normalization rules, from the head of the
[adapter contract](adapters.md):

- **No adapter may synthesize a tool result.** Every `reached` and
  `not-reached` is read out of a retained native document.
- **An incomplete or failed run must never become `not-reached` merely
  because the result list is empty.** This is the anti-vacuous-negative
  rule; section 3 makes it operational.
- `inconclusive`, `unsupported`, and `runner-error` are evidence outcomes,
  not clean negatives, and are never converted into either error column —
  see [outcome interpretation](scoring.md#outcome-interpretation) and the
  50% blind baseline it defends.

## 3. Anti-vacuous-negative guards

The single most important property of an adapter is that silence is never
credited. A tool that crashed, mis-loaded its rules, or never resolved the
fixture will usually produce an empty finding list — and an empty finding
list normalized as `not-reached` banks a true negative on every negative
case for free. Every shipped adapter therefore guards the path from failure
to `not-reached`, and a new adapter must guard the same three layers:

1. **Exit-status guard.** A nonzero exit is `runner-error` before any
   finding document is read (`run_semgrep_case`, `run_pysa_case`).
2. **Evidence-shape guard.** A missing, truncated, or malformed native
   document is `runner-error`, and findings that exist but cannot be
   reconciled to the case anchors are `inconclusive`
   (`semgrep_finding_outcome`, `joern_flow_outcome`,
   `normalize_anchored_codeql_sarif`).
3. **Activation guard.** A clean exit with zero findings is only
   `not-reached` when the retained evidence itself proves the benchmark's
   endpoints were bound. Pysa requires each case's `taint-output.json` to
   carry a bound model for both endpoints (`pysa_model_activation_failure`);
   OpenTaint requires its rule-load witness; FlowDroid refuses a results
   XML that shows no completion banner
   (`flowdroid_completion_leaks`, `flowdroid_termination_state`). Silent
   failure modes are real and have been found in the field — the Pysa
   README documents a configuration under which the pinned pair exports
   every call unresolved *while exiting cleanly*, which would have read as
   a clean-negative population without the guard.

Each layer has a regression test to imitate:
`semgrep_runner_failures_never_become_clean_negatives`,
`joern_runner_failures_never_become_clean_negatives`,
`codeql_missing_sarif_keeps_runner_error_evidence`, and
`flowdroid_completion_guard_refuses_silent_failures`, each in its
adapter's module under `src/tests/adapters/`.

## 4. Evidence artifacts to retain

Every run leaves a complete audit trail under `reports/`:

- **Normalized report** — `reports/<tool>-<language>-kernel.json`,
  validating against `schemas/result.schema.json`, carrying the witnessed
  tool identity (`tool_version`, `tool_build_identity`), the
  `adapter_version`, the `configuration_hash` over the committed adapter
  configuration, and one result per selected case. Report paths are
  dedicated per population and never shared between adapters or languages.
- **Raw evidence** — one native document per case under
  `reports/raw/<slice>/`: the tool's own SARIF, JSON, or XML verbatim, or
  a runner-error document carrying the failure, or a capability-decision
  document for a preregistered `unsupported` case. This is what
  `validate-reports` reconciles against the normalized report and what the
  freeze digest covers.
- **Timing sidecar** — `reports/raw/<slice>/<case-id>-timing.json` per
  timed case, written by `write_case_phase_timings`, with phase labels
  stating the boundary the adapter genuinely observes (see
  ["Retained phase timings and the environment stamp"](adapters.md#retained-phase-timings-and-the-environment-stamp)
  and the [latency tier's granularity
  table](latency-tier.md#per-adapter-granularity), where every adapter
  declares its row). Timing is additive metadata: no correctness outcome
  may read it, and a case arm that never invokes the analyzer retains no
  timing and clears any stale sidecar (`clear_stale_case_timing`).
- **Environment stamp** — `reports/raw/<slice>/run-environment.json`, once
  per run, written by `write_run_environment`: hardware model, OS, CPU
  count, beside the tool identity the run witnessed.

## 5. Source-tree touchpoints

An adapter is one module, `src/adapters/<tool>.rs`, over the shared contract
in [`src/adapters/mod.rs`](../src/adapters/mod.rs). That module owns the
adapter's pinned identity, its committed configuration, its case selection,
its invocation, and the normalization of its own retained evidence — and
nothing outside it owns any of those. Imitate Pysa (the newest module)
throughout.

**Where everything else lives.** `src/main.rs` is the command surface only.
Beside `src/adapters/` sit `src/cases.rs` and `src/templates.rs` (the
canonical cases and the preregistered template identities), `src/report.rs`
(the normalized report and the configuration hash), `src/evidence.rs` (anchor
reconciliation and the shared SARIF helpers), `src/runtime.rs` (process,
timing, and environment plumbing), `src/modeling.rs`, `src/native.rs` and
`src/latency.rs` (the three tiers that run beside the core kernels), and
`src/freeze.rs` and `src/results.rs` (the evidence manifest and result
generation).

### What the shared contract gives you

Four things are identical across all eight adapters and are written once, in
`src/adapters/mod.rs`. Use them; do not re-implement them.

- **`ToolIdentity`** — the witnessed `tool_version` / `tool_build_identity`
  pair. Your witness function returns one, and both halves must be read from
  the artifact the run invoked, never from a constant in this repository.
- **`KernelPopulation`** — the identity of your scored population: its tool
  key, language, display name, report path, raw-evidence root, label, scored
  template set, the predicate deciding which canonical cases belong to it,
  and the committed configuration its `configuration_hash` covers.
- **`select_kernel_cases`** — the selection loop and the revalidation against
  your language's rollout row, so an omitted template cannot hide in a
  smaller balanced subset.
- **`normalized_report`** and **`write_runner_error`** — the report envelope
  every adapter writes, and the runner-error document every adapter retains.

### What stays yours

1. **`Commands` enum variants.** In `src/main.rs`, add
   `Run<Tool><Language>Kernel { … }` with the tool binary taken as a flag,
   never a hard-coded path — plus `Run<Tool>Modeling` / `Run<Tool>Native`
   variants if and when the adapter takes modeling-matrix or native-profile
   rows. Wire the dispatch arm in the `match` inside `main`.
2. **The population descriptor.** An enum (or, for a single-language
   adapter, a unit struct — compare `PysaKernel`) with one variant per
   language, implementing `KernelPopulation`. Anything the analyzer needs
   that the contract does not name — a frontend identifier, an anchor
   dialect, a rule path — stays an inherent method on the same type.
   `select_<tool>_cases` is then a one-line call to `select_kernel_cases`.
3. **The runner pair.** `run_<tool>_kernel` witnesses the pinned identity,
   resolves the configuration through `configuration_paths`, writes the
   run-environment stamp, loops `run_<tool>_case` over the selection, and
   publishes through `normalized_report` and `write_and_validate_report`.
   `run_<tool>_case` clears stale artifacts (timing sidecar included),
   materializes the case workspace, spawns the tool under the case budget,
   writes phase timings, and returns `(outcome, diagnostics, raw_path)`.
   Both are bespoke, deliberately: this is where the analyzer's real
   invocation contract lives.
4. **Partition constants.** Preregistered capability decisions are data, not
   control flow scattered through the runner: a partition constant consulted
   before invocation, each `unsupported` cell carrying its verbatim
   rationale. Tier-wide partitions live with their tier (`MODELING_PARTITION`
   in `src/modeling.rs`, `NATIVE_PARTITION` in `src/native.rs`); an
   adapter-specific one lives with its adapter
   (`CHALLENGE_SEMGREP_PARTITION` in `src/adapters/semgrep.rs`).
5. **The normalization function.** One `<tool>_…_outcome` function that reads
   only the retained evidence and implements the section-3 guards (compare
   `pysa_rule_outcome`, `semgrep_finding_outcome`, `joern_flow_outcome`).
   This is bespoke on purpose. The guards are the adapter contract's real
   obligation, and a shared abstraction over them would hide them rather
   than enforce them.
6. **The configuration-hash mapping.** `current_configuration_paths` in
   `src/report.rs` maps a committed report path to the configuration it
   hashes, and is what proves a committed report is not stale. Add your
   population's arm there. Nothing else in the file may reorder or rename an
   existing path: a stamped hash is compared against this set, so a change
   here flags every affected report as drifted.
7. **Tests.** In `src/tests/adapters/<tool>.rs`, the new adapter adds at
   minimum: a population-scoping test
   (`<tool>_kernel_is_language_scoped_and_resolvable`), an identity-pin test
   (`<tool>_identity_is_witnessed_against_the_pin` — Pysa's is
   `pysa_identity_is_witnessed_against_the_pins`, plural, because it
   witnesses two pinned tools), an evidence/anchor-reconciliation test, a
   report-path-disjointness test, and an anti-vacuous-negative test
   (`<tool>_runner_failures_never_become_clean_negatives`). Pysa's and
   FlowDroid's test modules are the current reference lists.

## 6. Validation

Before publishing any result:

```bash
cargo fmt --check
cargo test
cargo run -- validate
cargo run -- validate-reports
```

`validate` schema-validates every case and enforces the case contract
(balanced core pairs, witness-checkpoint placement). `validate-reports`
schema-validates every normalized report and checks that each result's
retained raw evidence exists on disk. When the adapter's evidence enters a
freeze, `cargo run -- validate-freeze reports/freeze.json` from the exact
clean checkout the manifest names, and
`cargo run -- generate-results --manifest reports/freeze.json
--output-directory site/results --check` prove the published artifacts match
the frozen evidence byte for byte — see the [freeze contract](freeze.md) and
the [result generation contract](results.md).

## 7. Document the adapter

Write `adapters/<tool>/README.md` at the standard of the
[Pysa](../adapters/pysa/README.md) and
[Joern](../adapters/joern/README.md) READMEs: the eligibility evaluation as
performed, the pinned identity and how each run witnesses it, the exact
invocation, the committed configuration and its hash, the outcome
normalization including every guard, the capability decisions with their
rationales, and the retained-evidence layout. Then add the adapter's row to
the plan table at the head of the [adapter contract](adapters.md) and its
granularity row to the [latency tier](latency-tier.md).
