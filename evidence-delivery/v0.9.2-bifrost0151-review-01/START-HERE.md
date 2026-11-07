# v0.9.2 Bifrost v0.15.1 final review package

Start with the [review handoff](../../reports/releases/v0.9.2/review-handoff/bifrost-v0151-final-review-20261107-01/review-handoff.md) and [concise case review](../../reports/releases/v0.9.2/review-handoff/bifrost-v0151-official-outcomes-20261107-01-concise-final.md). All 20 Bifrost groups completed. The actual full canonical check passed 92 reports, with 76 derivable configuration hashes checked, 16 not derivable and zero KnownStale. Publication remains held.

This lossless **review-detail** copy contains 185 files / 143,316,914 raw bytes in 21,767,380 compressed bytes: the complete current-branch 51-commit patch catalog through f9cce0c74a38129d4ae84a3edc763aeb1f18ed92, full seven-field case vectors and detailed audit, exact retained harness/build provenance, all metadata-validation failures and the actual successful canonical04 receipt/streams. The single tar part is 21,756,470 bytes, below 40 MiB, and uses Git LFS. The manifest retains original repository-relative paths, modes, sizes and SHA-256 values. Originals remain intact.

The [full-check receipt](../../reports/releases/v0.9.2/review-handoff/bifrost-v0151-final-review-20261107-01/review-bundle-full-check.json) verifies all compressed/uncompressed content and all current source-file hashes, sizes and modes. Delivery integrity does not certify semantics or timing. The known false positive, partial discovery, unsupported outcomes and Joern’s unavailable/unscored/untimed boundary remain explicit.

After fetching the LFS part, verify the complete bundle with:

```sh
/opt/homebrew/opt/python@3.13/bin/python3.13 -B scripts/evidence_bundle.py check evidence-delivery/v0.9.2-bifrost0151-review-01/detail
```

To restore, pass `--restore` with a **new, nonexistent directory**, for example `/private/tmp/dataflowbench-v092-review-restored-01`. Never restore over the repository or original evidence. The archive entries retain the full original `reports/releases/.../detailed-source-review/` prefix. Restored file copies default to a safe non-executable mode; the retained runner’s provenance records its original 0755 mode and exact hash. This package does not ask you to execute it.

The separate [official-attempt package](../v0.9.2-bifrost0151-official-01/START-HERE.md) preserves the 20 new attempts and retained Joern inputs (394,799,182 raw bytes / 153,378,703 compressed bytes). The [151-row ledger archive](../../reports/releases/v0.9.2/ledger-archives/ledger-151-01/) and [source recovery archives](../../reports/releases/v0.9.2/source-history/) preserve their exact hashes and source/plan identities. Earlier historical snapshots remain indexed by [START-HERE-02.md](../START-HERE-02.md); they were not repacked.

Root verification receipts, source archive04, PR/head/CI observations and other files made after this closed snapshot are separately retained additions. This package authorizes no merge, freeze, tag, release workflow, deployment or publication.
