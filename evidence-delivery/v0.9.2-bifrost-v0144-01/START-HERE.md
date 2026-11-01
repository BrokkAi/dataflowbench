# Bifrost v0.14.4: v0.9.2 benchmark review

**19/20 groups completed. Scala timed out. Publication remains held.**

The four previously regressed fixtures recovered their expected results. There
are six changed report rows because the Java pair also appears in smoke. The
other 1,040 paired rows retain their normalized outcomes. Scala's 70 missing
rows, 339 inconclusive rows, 85 unsupported rows and one unchanged Rust false
negative remain explicit.

Start with the [readable result handoff](../../reports/releases/v0.9.2/review-handoff/bifrost-v0144-results-01.md),
the [concise machine-readable summary](../../reports/releases/v0.9.2/review-handoff/bifrost-v0144-result-summary-01.json),
and the [1,046-row comparison CSV](../../reports/releases/v0.9.2/review-handoff/case-variation-v0144-partial-01.csv).

Detailed copies are lossless and digest checked:

- [Benchmark bundle index](benchmark-bundles-01.json): 21 actual attempts and
  19 completed normalized report scopes; 24.14 MB of files in 2.25 MB of bundles
  including manifests. Scala's timeout and smoke's zero-dispatch resource stop
  are separate retained attempts.
- [Detailed case-review copies](review-detail/manifest.json): 9.88 MB of full
  comparison/expectation JSON in 0.63 MB of gzip payloads.
- [Full source-commit diffs](source-review/manifest-02.json): six current commits,
  5.66 MB uncompressed / 1.16 MB compressed. The first manifest's historical
  index-path typo is preserved and explicitly corrected by manifest02.
- [Ledger archive](../../reports/releases/v0.9.2/ledger-archives/ledger-130-01/manifest.json):
  exact 130-row ledger, 126.02 MB / 13.30 MB compressed. The prior 109-row prefix
  and its archive are unchanged.
- [Packaging verification](../../reports/releases/v0.9.2/validation/bifrost-v0144-delivery-01/README.md)
  and [independent result review](../../reports/releases/v0.9.2/validation/bifrost-v0144-scala-stop-01/final-partial-results-independent-review-01.json).

Post-run CI repairs are indexed in the [complete source delta](source-review/ci-completion-01/manifest.json) and [retained CI failure logs](ci-failures-01/manifest.json). They preserve the original measured source and outcomes.

Compressed payload parts use the existing Git LFS rules. Fetch LFS objects
before verification. For each benchmark bundle, use:

```sh
python3 -B scripts/package-v092-evidence.py check path/to/detail --restore /absolute/new-restore-root
```

The verifier checks each part, manifest and uncompressed object before restoring
the original relative paths. Use a fresh restore directory. Detailed case JSON
and commit diff parts are individual gzip streams; their manifests specify
compressed and uncompressed hashes. The ledger's selected immutable archive
can be restored with:

```sh
python3 -B scripts/v092_ledger_archive.py hydrate-current --root .
```

Original files remain intact in the benchmark checkout. No cleanup, old snapshot
repack, Git history rewrite, engine change or publication was performed. Archive
integrity does not establish portable runtime replay or a performance certificate.
