# Retained v0.15.1 source history delta 04

This bundle preserves the exact Git delta from canonical schema-01 helper commit `cc7e4540ffc52f624c47cb0b77c308fef86f31b6` through typed prepared-invocation adapter commit `f9cce0c74a38129d4ae84a3edc763aeb1f18ed92`. The adapter commit's parent is archive-03 retention commit `121bdb96a6b88606886d1c25a3460cb2d2cab4b0`, so both commits are included. Archive-01, archive-02, and archive-03 remain unchanged.

The isolated import was seeded from exact main commit `36d93cc32abc20ff9a0573e755555f4b71f360b3`, then fetched archives 01 through 04 without tags. It proves measured source commit `7f99684668065b8fb1ebc9b2852f058c64430647` with tree `7af8853a1e2eb7ea7832f7c0bad4d2299c1ab416`, plan commit `515d9941978c12cafa37ba58eecacc0a4182226f` and its source parent, the exact C6 contract blob, the retained repair-02 helper, the canonical runner and Joern projector, and the typed adapter, tests, diagnosis, and independent review. Exact blob identities and hashes are in the manifest.

The finite Git selection is this README, `source-bundle-manifest.json`, and numbered `original-source.bundle.partNNNN` files. Concatenate parts in numeric order and verify the byte count and SHA-256 in the manifest. The unsplit raw bundle and isolated import proof are local-only and excluded from that selection. The numbered part matches the existing Git LFS rule.

This is source-history retention. The canonical-04 execution evidence is recorded separately; this archive operation did not run tests, builds, or analyzers and does not make a publication decision.
