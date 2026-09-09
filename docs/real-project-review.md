# Real-project confirmation review contract

This document specifies the independent review gate for the small R1
real-project confirmation slice. It complements
[`real-project-preregistration.md`](real-project-preregistration.md), which
defines selection and pinning. The machine-readable record is
[`corpus/real-project/review.json`](../corpus/real-project/review.json), and
its shape is defined by
[`schemas/real-project-review.schema.json`](../schemas/real-project-review.schema.json).

The committed record is intentionally `pending`: it contains no completed
review outcome and no analyzer result. No analyzer may execute against a
selected project, and no result may be frozen or published, until this gate
has a reproducible closeout.

## Packet and provenance

The review packet is the SHA-256-bound preregistration, review protocol,
relevant schemas, frame, draw, six current pin records, and LoC tool listed in
`review.json`. Each reviewer must receive the same
packet digest set from a separate clean checkout and a separate evidence
directory. A reviewer records:

- provider, exact model, reasoning effort, unique run ID, start and completion
  timestamps;
- checkout path, full revision, clean-worktree observation, and observation
  time;
- packet evidence path and every input artifact path plus SHA-256 digest; and
- the submitted report path and digest.

Reviewer A is planned as `openai / gpt-5.6-sol / medium` (the approved
alternative to Astra Light). Reviewer B is planned as `z.ai / glm-5.3 / max`.
A substitution is allowed only when it
is recorded before that reviewer starts; it cannot be chosen after seeing the
other review or analyzer evidence.

The reviewers work independently. They must not exchange conclusions before
both reports are submitted. The packet is analyzer-free, and each reviewer
must record `analyzer_evidence_consulted: false`. A true value, packet digest
mismatch, dirty checkout, missing run identity, or missing report provenance
fails the gate.

The first Sol review of the pre-amendment packet is retained verbatim at
`corpus/real-project/reviews/reviewer-a.md`. It found that the Hibernate
Validator endpoints were drawn from divergent maintenance lines. A33 amended
the ancestry rule, introduced the branch-specific 6.x pin, and added the
latency contract in response, so that report is
provenance for the change rather than acceptance of the changed packet. Both
reviewers must submit again against the current digest set.

## Review questions

Each reviewer independently reports a verdict of `accept`, `reject`,
`inconclusive`, or `cannot-determine` (with `not-reviewed` reserved for a
planned record) for all of these subjects:

1. eligibility and every draw exclusion;
2. replacement decisions and the preregistered replacement rule;
3. repository and revision pins;
4. license identity and redistribution boundary;
5. per-pin ground truth, including the vulnerable revision, fixed revision,
   and the source-to-sink remediation location;
6. claim boundaries; and
7. the separately specified latency views.

The per-pin record is mandatory. Reviewers must inspect the pinned pair and
fix diff without analyzer output. For the two-commit Hibernate Validator 6.x
fix, they must identify what each remediation commit contributes and whether
either includes incidental changes. A reviewer who cannot determine a defensible ground truth leaves
that pin `cannot-determine`; it is not converted to a positive or negative.

After both reports are immutable, the comparison records every disagreement by
subject and pin. A human or explicitly identified adjudicator may resolve a
disagreement from the packet and the two submitted reports. If a disagreement
remains unresolved, or if adjudication cannot determine the answer, the whole
review remains `inconclusive`, with both `execution_ready` and `freeze_ready`
false. Adjudication never consults analyzer output.

## Latency scope

Latency is an auxiliary, descriptive view of this small slice. It must not be
used to change synthetic-core populations or denominators, and it must not be
presented as accuracy, superiority, causality, or a ranking.

Two views are retained separately:

1. **Small-project latency:** raw cold per-project and per-case medians, plus a
   raw warm marginal median where a warm series is applicable. Startup and
   invocation overhead are retained as their own fields; warm marginal values
   may exclude startup only when that exclusion was explicitly measured.
2. **Latency per pinned source LoC:** raw latency divided descriptively by
   physical source LoC in the pinned revision. The record must identify the
   pinned LoC tool and version, language-aware counting and file-selection
   rules, and every excluded generated, vendored, binary, or other path. The
   repository-owned `scripts/count-real-project-loc.py` defines v1 as physical
   newline-delimited lines (including blank and comment lines) in `.java`,
   `.js`/`.cjs`/`.mjs`, or `.py` files, with its exact directory, generated
   marker/name, minified-file, and symlink exclusions retained in every output.

For each observation, retain raw latency, source LoC count, LoC tool and
version, counting rules and exclusions, analyzer and language, source and
analyzer revisions, execution environment, configuration identity, startup
overhead, and cold/warm label. Never replace raw latency with the normalized
value, or use the normalized value as a causal explanation.

## Closeout requirements

The review record can become `complete` only after both reports, packet and
checkout provenance, all per-pin reviews, disagreement handling, and claim
checks are present. The readiness outcome must then be explicitly `ready` only
if no subject is unresolved or cannot-determine. Until that point, the record
must remain pending or inconclusive and both execution and freeze readiness
must remain false.

This contract does not execute analyzers, create real-project cases, alter
synthetic-core denominators, freeze results, or publish a score.
