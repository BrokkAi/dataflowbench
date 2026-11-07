# Official Bifrost 0.15.1 results for v0.9.2 review

All 20 official groups completed at 06:59 SAST on 7 November. The 1,116 report rows cover 1,000 distinct Bifrost fixture IDs; 116 Smoke rows repeat fixtures from another group. All attempts exited zero without a timeout or capacity loss. Operational completion does not make inconclusive or unsupported results decisive.

| Evidence | Correct | False positive | False negative | Inconclusive | Unsupported |
| --- | ---: | ---: | ---: | ---: | ---: |
| Published DataFlowBench v0.9.0 | 660 | 0 | 0 | 371 | 85 |
| Retained v0.9.1 preparation | 660 | 0 | 0 | 371 | 85 |
| Official Bifrost 0.15.1 | 664 | 1 | 0 | 366 | 85 |

The four gains are Go nested-access-path positive and negative, C# recursive-heap-unwind positive, and Rust result-error-propagation negative. C# recursive-heap-unwind negative changed from inconclusive to the known false positive tracked by upstream #9651. Thus four former inconclusive results are now correct and one is now a known incorrect answer. These are four distinct improved fixtures, not duplicated Smoke gains.

Every official outcome matches the retained 0.15.1 diagnostic. Fifty-two diagnostic messages changed: 16 ephemeral mount digests and 36 refreshed native unsupported rationales. The other six compared report fields match. Rust dispatch-table negative remains incomplete with `partial_discovery`; the three native groups retain 36 unsupported rows. Full policy qualification remains false. No timing or relative-performance conclusion follows.

The comparison's published tag is **DataFlowBench v0.9.0**, not a Bifrost engine tag. The retained v0.9.1 manifest says `published=false` and `release_freeze_created=false`; live GitHub release/tag checks found no v0.9.1 publication. Its report outcomes happen to match the published v0.9.0 baseline. Four group configuration hashes differ between historical and current evidence, so this is an outcome comparison without causal attribution.

- [Concise 1,116-row comparison](bifrost-v0151-official-outcomes-20261107-01-concise.csv)
- [Aggregate audit and hash references](bifrost-v0151-official-outcomes-20261107-01-summary.json)
- Full seven-field vectors, detailed CSV and the original independent audit are retained byte-for-byte in the lossless review bundle under `evidence-delivery/v0.9.2-bifrost0151-review-01/detail/`, with source-to-copy hashes in `bifrost-v0151-final-review-20261107-01/case-audit-copy-projection.json`.

The full matrix now passes actual canonical validation: 92 reports, 76 derivable configuration hashes checked, 16 not derivable and zero KnownStale. Publication review, merged-main freeze and publication gates remain separate. This handoff does not approve publication or certify complete descendant containment.
