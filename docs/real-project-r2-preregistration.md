# Prospective real-project confirmation slice R2

This document and `corpus/real-project/r2/protocol.json` define R2 **before the
first R2 population query**. They must merge before
`scripts/capture-real-project-r2.py` is run. R2 is a new wave, not a correction
to R1, and nothing in this document is an analyzer result.

R1 remains the immutable historical record under the top-level
`corpus/real-project/` paths. Its two reviewers accepted the six selected pins,
licenses, ground truth, claim bounds, and latency contract, but could not
certify eligibility or exclusions because the draw-time advisory responses and
complete per-candidate E1-E8 decisions were not retained. Its
`inconclusive` outcome is correct and is not amended into success.

## Order of operations

The R2 pipeline is fail-closed and runs in this order:

1. merge this document, the machine-readable protocol, its schema, and the
   capture tool;
2. query the source-only advisory population once and commit every raw response
   page plus its manifest;
3. derive the frame offline, execute the fixed seeded walk, and retain an E1-E8
   evidence record for every candidate reached;
4. pin vulnerable and fixed revisions, source-archive digests, and license
   evidence, then commit the complete analyzer-free packet;
5. independently review that identical commit from two separate clean
   checkouts and evidence paths; and
6. set `execution_ready` only after both reports contain no unresolved,
   `inconclusive`, or `cannot-determine` subject.

No analyzer may inspect an R2 candidate before step 6. No reviewer may inspect
a selected pin before step 4 commits. A failed or partial API request is not a
smaller population: the capture is discarded and restarted as a newly
identified attempt.

## Population and immutable source snapshot

R2 uses the same closed 2025 GitHub Advisory Database population definition as
R1 so the replacement addresses the provenance defect without changing the
scientific question. The strata are Maven/Java, npm/JavaScript, and
pip/Python. Queries request reviewed advisories published from 2025-01-01
through 2025-12-31 inclusive with at least one of CWE-22, CWE-78, CWE-89,
CWE-94, CWE-611, or CWE-918. An advisory is admitted to the frame only when it
is not withdrawn, its source location is a GitHub repository, and it references
a commit in that repository.

The capture follows GitHub's `Link: rel="next"` chain rather than assuming a
page count. For every request it retains the complete JSON response body and a
manifest entry containing the exact request URL and parameters, page number,
retrieval time, HTTP status, item count, next-page state, repository-relative
response path, and SHA-256. Credentials and authorization headers are never
written. The frame is derived only from those committed bytes. A later query is
a later wave or a named failed attempt, never an update to R2.

The same rule covers draw-time eligibility metadata. For every candidate the
seeded walk reaches, the packet retains the complete source-only GitHub
repository, languages, fix-commit, and license responses used to decide the
criteria. Evidence outside GitHub is allowed only for E5 and must be a captured
repository-owned document or a digest-bound DataFlowBench donor/analyzer list.

## Eligibility decisions

Every walked candidate has exactly one explicit `pass` or `fail` decision for
each criterion, even when an earlier failure is already sufficient to exclude
it. Each decision records its observed value and immutable evidence references.

| ID | Admitted when |
| --- | --- |
| E1 | Captured GitHub primary language equals the stratum exactly. |
| E2 | Captured SPDX identity is OSI-approved and the license file resolves at the vulnerable revision. |
| E3 | Captured repository metadata says the repository is neither archived nor a fork. |
| E4 | Captured GitHub repository size is at most 256,000 KiB (250 MiB). |
| E5 | The repository is not a vulnerability demo, benchmark corpus, evaluated analyzer, dependency of one, named donor suite, or any repository selected by R1. |
| E6 | The earliest captured same-repository advisory fix resolves to one full commit with exactly one parent; divergent maintenance-line fixes are ineligible. |
| E7 | Captured language totals contain at least 20,000 bytes of the stratum language. |
| E8 | No earlier R2 selection names the same case-insensitive owner/repository. |

E5 always includes a written candidate-specific rationale. E8 always records
the selected-repository set immediately before the decision, including an
explicit empty set. This closes the two judgment/structural gaps that made the
R1 audit inconclusive. R1 repository non-reuse makes R2 an independent slice;
it is part of E5 and is checked without consulting any analyzer result.

## Sampling and replacement

The seed is `dataflowbench-real-project-wave-r2`. Within each stratum,

```text
draw_key = SHA-256(seed + "\n" + ghsa_id)
```

is ordered by ascending lowercase hex, with GHSA identifier as a tie-breaker.
The walk starts at position one, evaluates all eight criteria, selects only a
candidate passing all eight, and stops exactly at two selections per stratum.
Six repositories support only named, descriptive observations; the target is
not a power calculation.

Before independent review closes, a declined pin is retained as an exclusion
and the same seeded walk continues. There is no reseed. After review closes, a
declined repository is retired without replacement. Analyzer output never
affects exclusion, selection, replacement, or ground truth.

## Pins and independent review

Each selected repository receives a wave-scoped pin for the vulnerable parent
and fixed commit, source-archive URL, archive SHA-256 and byte length, SPDX
identity, license-file path and digest, and proposed source-to-sink remediation
location. Upstream source is fetched by immutable revision but is not vendored.

Reviewer A is OpenAI `gpt-5.6-sol` at medium effort. Reviewer B is Z.ai
`glm-5.3` at max effort. They work from separate clean checkouts and evidence
paths, receive the same digest set, do not see analyzer output, and do not
exchange conclusions before both reports are immutable. They review snapshot
completeness, frame derivation, every E1-E8 decision, draw/replacement
correctness, pins, archives, licenses, vulnerable/fixed semantics, claim
bounds, and descriptive latency scope.

Any missing response, digest mismatch, incomplete page chain, unresolved
disagreement, rejection, `inconclusive`, or `cannot-determine` verdict keeps
both execution and freeze readiness false. A coordinator may adjudicate a
disagreement only from the immutable packet and the two reports, with a
separate retained decision record.

## Claim bounds

R2 may report only named per-repository, per-revision, per-case, per-adapter
outcomes in the benchmark's five-state vocabulary. It may retain raw cold and
warm latency and the separately preregistered descriptive per-source-LoC view.
It may not publish an accuracy, precision, recall, F-score, generalized rate,
confidence interval, significance test, causal claim, ranking, or combined
leaderboard. R2 never changes any synthetic-core denominator and is never
pooled with R1.
