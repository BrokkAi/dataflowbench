# v0.7.1 release-evidence inventory contract

This document defines the inventory assembled for the DataFlowBench v0.7.1
full refresh. It is a contract for the eventual inventory document; it does
not claim that any measurement or probe has run. The JSON Schema is
[`schemas/release-evidence-inventory.schema.json`](../schemas/release-evidence-inventory.schema.json).

The inventory is a small wrapper around committed measurement records: `plan`
and `ledger` identify the preregistered expected inventory and complete attempt
ledger by repository-relative path and SHA-256. `artifacts` enumerates all
retained evidence files by path and SHA-256. `coverage` reconciles the plan's
expected IDs with retained and missing IDs for each group. No completed
inventory is provided here.

The schema checks shape and fixed baseline values only. Git ancestry, file
hashes, completeness and execution semantics require the verification below;
schema validation alone does not qualify a release.

## Fixed population identity

Every correctness-bound record must resolve to this population identity through the plan and ledger. The
inventory schema fixes these values so a later run cannot silently move to a
different corpus:

| Field | Required value |
| --- | --- |
| Release | `v0.7.1` |
| Baseline tag | `v0.7.0` |
| Baseline commit | `0a4d8b66c1e458b10e2c6196d0e4f9622f4c8ef5` |
| Fixture revision | `sha256:9df209ed3d7723a3ee33f2b289cf2afe34a3add781bdf2a2ac445de42b8d0151` |
| Cases | 852 |
| Reports | 82 |
| Results | 3480 |

The ledger records the population identity for every attempt. A synthetic
fixture used by invocation-overhead measurement may have its own fixture
digest, but it still records the same v0.7.0 population contract as the input
selection and records the synthetic fixture as an output/input artifact.

## Evidence groups

The inventory must contain exactly these preregistered groups. Every group
has coverage status, expected/retained/missing IDs, ledger IDs and explanatory
notes. Raw records retain `reached`, `not-reached`, `inconclusive`,
`unsupported`, and `runner-error` distinctly where those outcomes apply:

| Group | Required evidence |
| --- | --- |
| `cold-sidecars` | Per-case cold timing sidecars and their retained raw evidence for the 82 reports. Unsupported cases have an explicit retained decision and no invented timing. |
| `run-environments` | The environment stamp for every run, including tool/configuration/build identity and observed machine conditions. |
| `warm-observability` | The explicit accounting of warm capability/declines for all eight adapters, including the FlowDroid batch-equivalence uncertainty. |
| `warm-series` | Complete retained warm series for the preregistered repeats and batch sizes; publish ranges over retained repeats. |
| `invocation-overhead` | Three retained repeats per planned adapter/language pair, with settle observations and no agreement gate. |
| `native-probes` | Retained positive and negative controls for tool-native probes and explicit unsupported/inconclusive/runner-error outcomes. |
| `modeling-probes` | Retained positive and negative controls for modeling probes and explicit unsupported/inconclusive/runner-error outcomes. |

The group status describes evidence coverage, not analyzer quality. A group
may be `complete` while retained records include unsupported, inconclusive,
or runner-error outcomes. Missing records make coverage `partial`. Environment
and timing records do not acquire artificial semantic-flow outcomes. A missing artifact, absent ledger row, or
quiet command is never inferred to be clean or complete.

## Identity and digest rules

Retained reports, pin/configuration records, environments, controls and raw
outputs are identified by repository-relative paths and lowercase SHA-256
digests. Binary identity records carry the installed asset hashes. A display name or a tool name alone is not an
identity. The plan and ledger connect normalized-report digests to witnessed
tool/configuration/build identity records and pin declarations.

The inventory may reference an artifact only after checking that the path is
present at the evidence revision and that its bytes hash to the recorded
digest. The ledger's stdout, stderr, retained outputs, and run-environment
stamp are all digest-bearing references.

## Attempt ledger

The attempt ledger is the source of execution provenance. One row represents
one invocation attempt, including attempts that fail, are superseded, or
produce an explicit unsupported or inconclusive result. Each row records:

- exact argument vector, UTC start and end timestamps, and exit code;
- stdout and stderr paths plus SHA-256 digests;
- every input commit, the fixed population identity, and the fixture digest;
- binary and asset locations plus SHA-256 digests in a retained identity record
  (installed binaries need not be committed);
- the run-environment artifact and observed hardware, OS, architecture, CPU,
  and one-minute load sample;
- cache posture, including whether the run was cold, warm, mixed, or unknown;
- attempt identity and supersession links; and
- every retained output path and SHA-256 digest.

The ledger does not replace raw evidence. It makes the evidence discoverable
and auditable, while the group and report records state what the evidence is
for. All attempts remain addressable after a retry; supersession never
deletes or overwrites an earlier artifact.

## Assembly and validation lifecycle

The evidence PRs land first. After those merges, assemble the inventory from
the surviving merged `main` ancestor and verify that every referenced path,
commit, digest, report count, fixture identity, and preregistered group is
present. The inventory is then committed in a separate manifest PR. The
inventory must not contain its own commit or a self-referential digest: its
`evidence_revision` names the surviving merged evidence revision, and
it has no self-reference field or digest.

Verification before publication must:

1. Resolve `evidence_revision` to a commit and prove it is an ancestor of the
   fetched merged `origin/main`, using `git merge-base --is-ancestor`. Verify
   every plan, ledger and artifact path with `git show <revision>:<path>` and
   SHA-256, rather than reading an unrelated working tree. Reject duplicate
   paths, traversal paths, conflicting digests and self-references.
2. Compare the plan's exact case IDs and report-to-case memberships against
   v0.7.0, not just counts: 852 cases, 82 reports and 3480 results; reject the
   22 later cases. Check normalized report pins/configuration/build identities
   against retained witnessed identity records and the dated pin review.
3. Reconcile every planned measurement/control ID with ledger attempts and
   output files. Require `expected_ids` to match the plan, `retained_ids` and
   `missing_ids` to be disjoint and exhaustive, and every `ledger_id` to resolve.
   `complete` requires no missing IDs. Counts alone cannot prove coverage.
4. Retain all attempts, repeats, controls and superseded outputs. Verify UTC
   ordering, commands, input commits, raw output hashes, machine observations
   and cache posture. Explain absent timing with the actual retained outcome;
   never invent warm observability or infer uncontended execution from load
   alone. Preserve any unfavorable or failed attempts.
5. Verify cold/auxiliary site bundles against these retained files and the
   validated freeze's report population. New site bundles and the final freeze
   are downstream artifacts in the separate manifest PR, not inputs to this
   inventory. Leave old release archives byte-identical.

The execution ledger may keep its existing field names; this contract requires
those facts to be present and verifiable rather than duplicating them into a
second ledger. New dated amendments to the plan must remain auditable; never
silently replace the plan after observing measurements. No inventory validator
CLI is introduced by this preparation change: the final independent evidence
audit must execute and record the semantic checks above before publication.
