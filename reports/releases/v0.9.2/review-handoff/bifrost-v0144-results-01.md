# Bifrost v0.14.4 benchmark for the v0.9.2 target

The run produced completed reports for **19 of 20 groups**. The four previously
regressed Java/Kotlin fixtures recovered their expected decisive results.
**Scala timed out**, so this target and v0.9.2 are not ready for publication.
The remaining Joern qualification and 108 cases are separately pending; this
Bifrost authorization did not start them.

## Case results and their limits

The completed groups contain **1,046 paired report rows / 932 distinct fixture
IDs**. The full Bifrost target remains 1,116 report rows / 1,000 distinct
fixtures within the unchanged 1,108-case benchmark population. Scala's missing
70 rows remain in the target denominator; its partial raw outputs are not
normalized, scored, or treated as unchanged.

| Observed v0.14.0 → v0.14.4 normalized transition | Report rows |
| --- | ---: |
| Inconclusive → expected decisive result | 6 |
| Unchanged normalized outcome | 1,040 |
| Decisive → inconclusive or newly wrong decisive result, among paired rows | 0 |

The six recovered rows are four unique fixtures. The Java exception pair also
appears in smoke:

| Fixture | v0.14.4 result |
| --- | --- |
| `dfb-taint-java-exception-catch-negative` | Complete, no flow; kernel and smoke |
| `dfb-taint-java-exception-catch-positive` | Complete, proven definite flow; kernel and smoke |
| `dfb-taint-kotlin-expression-positive` | Complete, proven definite flow |
| `dfb-taint-kotlin-loop-carried-positive` | Complete, proven definite flow |

All recovered results match the frozen case expectations. Their runs are
complete with no omitted obligations. Positive findings are explicitly
definite/proven/complete; the negative has zero findings under complete
coverage. This recovers the observed four-fixture regression; it is not a
claim that every engine behavior has been repaired.

Current normalized counts are 312 reached, 310 not-reached, **339 inconclusive**
and **85 unsupported**. Inconclusive and unsupported rows remain separate from
correct or clean results. One existing false negative is unchanged:
`dfb-taint-rust-dispatch-table-positive` remains not-reached despite its
expected flow. Rust's `result-error-propagation-positive` remains inconclusive;
its raw completion reason changes from `partial_discovery` to
`capability_incomplete`. No case obligation arrays changed in the paired audit.
Other raw diagnostics, witness identities and measurement metadata can vary
even when the normalized outcome is unchanged.

The [concise case CSV](case-variation-v0144-partial-01.csv) lists every paired
row. The full JSON and expectation review are retained locally at
`case-variation-v0144-partial-01.json` and
`bifrost-v0144-expectation-review-01.json`; the delivery entrypoint links their
lossless compressed copies. The separate partial-audit reproducer preserves
failed attempts and missing groups. The original strict full-20 audit is
unchanged and cannot accept this incomplete target.

## Actual attempts and failure diagnosis

The original serial invocation stopped on Scala. Its 17 successful groups and
Scala failure remain unchanged. After independent review and explicit root
continuation records, only the never-started smoke and TypeScript groups were
selected through the existing one-group mode. No completed group was rerun.

Scala attempt03/series03 reached its fixed **1,046-second deadline** and ended
after 1,053.306 seconds, exit 124, `timed_out=true`, with no capacity loss. Its
top-level `recorder-error` additionally records the missing aggregate report;
that label is not the cause of the timeout. There are 59 raw analyzer reports
(34 complete, 25 inconclusive), one SIGTERM runner-error payload and 59 timing
files. Timings sum to 1,044.765 seconds. Dependency staging/checking took about
0.013 seconds and source materialization 2.468 seconds. Most case calls took
about 15 seconds, with smaller 27–28 and 40-second clusters. The retained
evidence establishes cumulative per-case runtime, not an isolated engine cause.
See the [independent Scala diagnosis](../validation/bifrost-v0144-scala-stop-01/independent-scala-timeout-diagnosis-01.md).

Smoke attempt04/series03 stopped during resource admission, before analyzer
dispatch: two background MCP contenders exceeded the unchanged idle threshold
after source materialization. It consumed its attempt identity but **zero
analyzer cases/seconds**. Its prospectively reviewed successor, attempt05,
completed all 118 rows in 210.399 seconds. TypeScript attempt03 then completed
70 rows in 107.023 seconds. Fresh gates and scoped owned-process observations
preceded both launches. No foreign process was killed, no threshold/deadline
was relaxed, and no automatic launcher retry was used. The original Scala
timeout and zero-dispatch smoke stop remain visible alongside successful rows.

The ledger now has **130 rows**: 122 completed, three failed and five
recorder-error rows. Its SHA-256 is
`79070314d9d27581b9541934c7b701c2640cb1436f162e570b210df787e13d84`.
The original 109-row prefix remains exactly
`2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851`.
The target consumed 21 attempts; the global consumed count is 131 because the
older unclosed Smoke02 remains separately consumed. The production read-only
[reconciliation](../execution-v5/bifrost-v0144-01/reconciliation-19-of20-01.json)
verifies actual receipts, captured/staged hashes, invocation links and the
ledger suffix. It reports **incomplete**, with Scala missing and no series
summary. All recorded final owned identities were absent in post-run scoped
observations; descendant containment and continuous global absence remain
unproven.

## Engine, harness and validation changes

No Bifrost engine source was changed. The official v0.14.4 native macOS binary
has SHA-256 `a3aa17a18be33e1e841c1bf317c6ca35a6aa3aaef452c607fafbb3b83aeec399`
and build identity `ff5cf473f4ad414751911ff93ef79e1df1d35823`. Its public
snapshot tag commit is separately
`786891f9ed19d2086dfd6242ff15ca904b610620`. npm/PyPI installation is not part
of this native-CLI benchmark or a verified distribution claim.

The measured harness SOURCE is
`61ae0cb817322ac81528217479c0be7bd760fa36`; PLAN is
`6500465e02e28ac279047e610d7e8dbccc844ee8`. The approved contract02 SHA is
`1d2188df4e7bc7f5cc4e28cc0700a839a294b0cbecc484f4d9658bb5280164e4`.
The optimized harness SHA is
`114912643aa9b467b00487b1cfaf9985f17b845936da4527dca8cadbbf9682d0`.

| Current commit | Purpose and validation boundary |
| --- | --- |
| `ed40f8846c580868a134c4c1ac2ea87b3340bc05` | Earlier source-provenance repair after squash publication; no engine run follows from this commit. |
| `70a63dc94fb8513dfd05e93ddcdf24382038a10e` | Earlier ordinary-user Darwin process-provider preparation; uncertainty and strict admission retained, not accepted Joern qualification. |
| `c6bb355915200f97397883a2a10c7f98ed2a8674` | Earlier archived Joern input verification; its retained source review reports a 142-test composed suite, not new qualification in this run. |
| `f496f366e4475481c2a1c497d5f27650c4816ac8` | v0.14.4 pin/native profile, historical profile preservation, version-aware Scala configuration, acquisition/control review, C5 controller and initial source snapshot. |
| `61ae0cb817322ac81528217479c0be7bd760fa36` | Pre-dispatch correction to account for every historical source input and copied source view within the original resource ceilings. The unapproved draft remains preserved. |
| `6500465e02e28ac279047e610d7e8dbccc844ee8` | Exact reviewed execution plan and initial serial launcher; separately reviewed later launchers use the same frozen source and contract. |

Full commit diffs are losslessly compressed and indexed in
`evidence-delivery/v0.9.2-bifrost-v0144-01/source-review/manifest-02.json`.
The [preparation handoff](bifrost-v0144-target-preparation-01.md) explains
source repairs, earlier failed tests and the superseded unapproved draft.
The earlier [all-session review index](joern-preparation-review-addendum-13.md)
and [failure-seal addendum](joern-preparation-review-addendum-14.md) remain
preserved; this packet supplements them rather than replacing historical
commit identities or diagnoses.

Source validation passed: `cargo fmt --check`, 310 Rust tests, all 1,108 case
validations, an optimized harness build, 19 C5 focused tests, 14 qualification
review tests and 11 unchanged packaging integrity/security tests. Exact logs
and independent reviews are retained. Final reporting helpers were syntax/help
checked, independently reviewed, reject optimized Python, and executed against
the actual terminal evidence. A pre-existing dead-code warning remains
recorded; no suppression was added.

Kernel call modeling remains **optimistic**; model-activation experiments
remain **require-model**. Policy, fixture, expectation and model-mode inputs
are unchanged. Native activation evidence paths are versioned and external
pack auto-acquisition remains disabled. The empty shipped catalog still yields
unsupported cells. Scala separately includes the PR298 POM plus real pinned
binary/sources jars staged into isolated HOME; comparison against the old
policy-only Scala configuration would confound engine and configuration.

All 44 qualification commands completed without timeout/capacity loss, but
the strict schema-5 qualifier failure against schema-6 output is preserved.
A separate reviewed binding permits measurement with known limits: 36 complete
policy controls and the same three JavaScript partial-discovery controls.
Full policy qualification is **false**. Process exit zero is not completeness.

## Post-run CI compatibility repairs

CI exposed platform-specific test roots/interpreters and ignored local-only
fixture inputs. Tests now use real Python 3.13 with absolute argv, derive their
checkout roots, preserve strict environment checks, and restore exact control
inputs from their verified compressed archive. Small Scala/ledger fixtures are
explicitly unit-only. An exact historical v0.14.0 Scala report has a separate
3.3 KB lossless copy for CI and an exact-path ignore rule for hydration; the
clean-checkout gate is unchanged. None of these fixtures qualifies a new run.

The isolated v0.9.0 release gate then found a report-consumer bug: it tried to
hash the modern Scala POM before selecting a known historical policy-only
closure. The post-run `src/report.rs` repair selects only registered historical
closures before opening that later file. Exact v0.14.0 policy-only hashes remain
recognized; v0.14.4 still requires its POM and rejects the old closure, and
unknown versions reject. A separate-process regression omits the POM and tests
legacy exact/mismatched hashes plus modern/unknown rejection. Focused Scala
tests, formatting and the 19 controller unit tests passed; independent review
is recorded in `validation/bifrost-v0144-ci-history-01/`.

The measured SOURCE/PLAN, original optimized harness and all result receipts
remain the identities recorded above. This consumer repair was made after the
measurement and did not rerun Bifrost, alter normalization or certify Scala
completion. The complete post-run source delta and file hashes are in
`evidence-delivery/v0.9.2-bifrost-v0144-01/source-review/ci-completion-01/manifest.json`.
The seven failed CI logs plus the exact-base comparison are preserved losslessly
in `evidence-delivery/v0.9.2-bifrost-v0144-01/ci-failures-01/manifest.json`;
`bifrost-v0144-ci-followup-01.json` through `-07.json` retain the diagnoses and
validation boundaries. Live delivery status is on PR #299, separately from
benchmark and publication readiness.

## Delivery and remaining gates

Detailed attempts and normalized report copies are compressed losslessly and
verified. Originals and evidence paths remain intact. Compressed payloads use
the existing Git LFS attributes; no old snapshot is repacked and no history
rewrite or cleanup is performed by this benchmark. The current ledger archive
has a new immutable prefix entry; the 109-row archive remains preserved.

This run does not provide a controlled, uncontended before/after performance
certificate. Version, source/contract and Scala dependency differences remain
explicit. It does not qualify the full 84-group/92-partition/4,252-row release.
Immutable receipts retain original host paths. Lossless archive integrity is
portable; full runtime replay or the host-bound comparison helper on another
checkout has not been qualified merely by compressing the files.
Scala completion, remaining Joern qualification/execution, full checker/config
selection, exact-head CI and David's all-fix/case-variation review remain
distinct gates. Publication, release tags/workflows, publishing merges and
deployment remain held pending his explicit subsequent approval.
