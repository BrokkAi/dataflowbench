# v0.9.2 final evidence review — Bifrost v0.15.1

All 20 official Bifrost groups completed at 06:59 SAST on 7 November 2026. The full selection verifies **84 groups, 92 report partitions, 4,252 rows and 1,108 distinct fixture IDs**. The actual canonical Rust validator returned exit 0: **92 reports validated, 76 derivable configuration hashes checked, 16 not derivable, zero KnownStale**. These are operational and evidence-validation results. Publication remains held for David’s all-fix and case-variation review, the evidence PR merge, merged-main freeze and separate technical publication gates.

## Results to review

| Bifrost report rows (1,116) | Correct | False positive | False negative | Inconclusive | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: |
| Published DataFlowBench v0.9.0 | 660 | 0 | 0 | 371 | 85 |
| Retained v0.9.1 preparation | 660 | 0 | 0 | 371 | 85 |
| Official Bifrost v0.15.1 | 664 | 1 | 0 | 366 | 85 |

Four distinct fixtures improve: Go nested-access-path positive and negative, C# recursive-heap-unwind positive, and Rust result-error-propagation negative. C# recursive-heap-unwind negative changes from inconclusive to the known false positive tracked upstream as #9651. Rust dispatch-table negative remains inconclusive with partial discovery. The three native Bifrost groups retain 36 unsupported rows. The official outcomes match all 1,116 outcomes from the prior v0.15.1 diagnostic; 52 diagnostic strings differ (16 temporary mount digests and 36 refreshed unsupported rationales).

There are 1,000 distinct Bifrost fixture IDs. Smoke’s 118 rows contain 116 repeats and two Smoke-only cases; the four gains above are distinct fixtures. The compared published baseline is **DataFlowBench v0.9.0**, tag commit `f861b51aabfc98b56315d9097eda58d1801e4558`. The retained v0.9.1 preparation states that it was unpublished, and the live tag/release checks found no v0.9.1 publication. The [baseline observation](publication-baseline-observation.json) and [tag snapshot](published-v090-tag-snapshot.json) retain those checks. Four group configuration hashes differ across historical/current evidence, so the table does not establish causal attribution. No uncontended timing or relative-performance claim is certified.

Read the [concise case review](../bifrost-v0151-official-outcomes-20261107-01-concise-final.md), its [1,116-row CSV](../bifrost-v0151-official-outcomes-20261107-01-concise.csv), and the [aggregate audit/hash summary](../bifrost-v0151-official-outcomes-20261107-01-summary.json). Full seven-field vectors and the original independent audit are retained losslessly in the review bundle below; [case-audit-copy-projection.json](case-audit-copy-projection.json) maps original files to their exact copies.

## Changes, purpose and testing

| Area | Final behavior and source | Validation |
| --- | --- | --- |
| Bifrost engine target | Uses the exact public v0.15.1 artifact, SHA-256 `00b279126297d5e9f7805390799493e915eaf4a2d5940dc3e755138a577a6df9`. No private Bifrost-engine source was modified or imported here. | Fresh bounded controls and independent replay; 20 actual terminal receipts, raw/report hashes and append-only ledger reconciliation. |
| DataFlowBench adapters/harness/configuration | Measured source `7f99684668065b8fb1ebc9b2852f058c64430647`, plan `515d9941978c12cafa37ba58eecacc0a4182226f`, C6 contract SHA-256 `f2c0fe969eb959856c650e8e892a9078342ec63600fc23dd05c3f069c068af65`. Existing fixtures, flags, expectations, source bindings, deadlines and typed unsupported/incomplete states remain explicit. | Rust formatting and 312 tests passed, zero failed/ignored; optimized build receipt and 56 source-input hashes; focused Python profile/selector/validator/projection tests and scoped source reviews. |
| Launcher and monitoring | Parent-wait supervision preserves the actual child lifetime. The first lost controller and earlier failed monitor/Joern attempts remain preserved. This does not establish historical absence or descendant containment. | Reviewed harmless lifetime probes, fresh real admission, one actual serial run, terminal reconciliation and provider-scoped teardown observation. |
| Swift metadata materialization | `f06c0f…` first added 22 missing declared inputs; `503871…` corrected the full nested runner binding. All 119 Swift configuration references are verified against retained source/plan bytes. | 12/19-test source suites and their preserved earlier failures, actual failed validation01/02/03 receipts, source/hash review. |
| Joern canonical schema projection | `25d5bd…` lifts only top-level qualification/scoring annotations and per-row raw SHA into a mandatory lossless sidecar. Frozen result schema, raw files and every other report field remain unchanged. `cc7e45…` adds the verified fresh-copy validator; `f9cce0…` repairs two path argument types through an independently reviewed adapter without changing the original helper/preparation. | Five projector tests, seven gate tests and four typed-argument tests; independent reviews; actual canonical04 exit0/92 reports/0 KnownStale. All 108 Joern raw SHA bindings and reconstruction are checked. |
| Evidence delivery | Concise summaries/CSV stay readable; detailed copies, ledgers and exact source recovery use verified compressed bundles and LFS. Originals remain intact. | Full compressed-content and source-to-copy hash verification, bounded 40 MiB parts, Git LFS pointer checks and isolated source-bundle imports. |

The full current-branch review contains **51 exact commits** from reviewed main `36d93cc32abc20ff9a0573e755555f4b71f360b3` through final implementation `f9cce0c74a38129d4ae84a3edc763aeb1f18ed92`. The lossless review bundle contains `detailed-source-review/catalog-03.json`, every complete binary/full-index commit patch, and `final-main-to-final-source.patch`. Each catalog entry records its purpose, touched files and patch hash. Earlier catalogs remain preserved. Validation receipts identify the exact source tested; a later successful test is not relabeled as a test of each earlier commit. Prior original-history fixes and their diffs remain indexed by the older [review handoff](../review-handoff-01.md) and preserved recovery/source archives.

Exact original source/plan commit identities can be recovered even after a later squash from the incremental [source01](../../source-history/bifrost-v0151-current-source-01/README.md), [source02](../../source-history/bifrost-v0151-current-source-02/README.md), [source03](../../source-history/bifrost-v0151-current-source-03/README.md), and [source04](../../source-history/bifrost-v0151-current-source-04/README.md) archives. Their source bytes/Git objects and prerequisites were verified in isolated imports. The retained exact harness binary is in the detailed review bundle with build provenance; its restored mode must be set to the recorded executable mode before execution. No analyzer rerun is required to review this packet.

## Canonical validation and Joern limits

[The explicit final selection overlay](publication-selection-with-canonical-validation.json) binds the original selector result, all 92 selected report hashes, the five canonical Joern copies, sidecar and actual canonical04 receipt. Its schema is intentionally separate from the original selector output. It keeps `publication_approved`, `full_release_gate_satisfied`, `scoring_enabled`, `scorecard_generation_allowed` and `freeze_created` false.

Canonical04 used the original optimized harness SHA-256 `99d997b31024ee7ff5edbee381cf2addff5f25d6851cc19980f515142b9508a5`, unchanged result schema, exact argv/environment and 1,800-second deadline. Receipt SHA-256: `694b25c5c62cbed78adb267c1f39478ec5febe1c845487a333afb2c5f4f85366`. Sixteen configuration hashes are **not derivable**, not certified checked hashes. The complete receipt, streams, inventories and failed predecessors are copied into the lossless detail bundle, with source-to-copy hashes in [canonical04-validation-copy-check.json](canonical04-validation-copy-check.json).

The retained Joern 108-case evidence remains **96 inconclusive / 12 unsupported**, aggregate resource qualification unavailable, `scored_activation=false`, semantic-only and timing uncertified. Every row retains `AggregateResourceQualificationUnavailable`; the sidecar preserves all lifted qualification values and raw-file hashes. Schema success does not turn its raw reached/not-reached observations into decisive qualified outcomes. Full Bifrost policy qualification also remains false: the limited measurement eligibility, three incomplete control reports, empty native catalog and unbound control endpoints are retained explicitly.

## Preserved failures and delivery

The [append-only failure inventory03](retained-failure-inventory-03.json) retains the old inventories, ledger failures, unclosed Smoke02, lost supervision01, missing Swift input, full-runner binding failure, strict-schema rejection, pre-Rust path-type stop, superseded projection preparations and source/test failure records. No failed attempt or diagnostic was relabeled as official completion. The 151-row ledger SHA-256 is `5528a3ff7683546a09c03d5791b5283bba3e08428c9380890e3e4cfe5d268679`; its exact original 131-row prefix remains `2dd64f7b4ac11ca0bdd46de972a005488f5e4b4da77b29760a1be70f76176199`.

- [Compressed full review, source patches and validation details](../../../../../evidence-delivery/v0.9.2-bifrost0151-review-01/START-HERE.md)
- [Verified 20-attempt and retained Joern delivery copies](../../../../../evidence-delivery/v0.9.2-bifrost0151-official-01/START-HERE.md)
- [Prior evidence entry point and historical snapshot](../../../../../evidence-delivery/START-HERE-02.md)
- [Controlling human publication hold](../human-publication-hold-01.json)

The review bundle is a closed snapshot. Root receipts, PR/CI observations or source archives created after its sealing are separate, explicitly dated additions. The evidence PR is ready for review after its own current-head CI succeeds. Its merge and the merged-main publication freeze remain separate; no automatic merge, release tag, workflow, deployment or publication is authorized by this handoff.
