# Retained v0.15.1 source history delta 03

This bundle preserves the exact Git delta from archive-02 tip `503871a36451ddbb5098a9ea010115202bd5ead9` through reviewed canonical-helper commit `cc7e4540ffc52f624c47cb0b77c308fef86f31b6`. Its prerequisites are the archive-02 tip; source-01 and source-02 remain unchanged. The delta also includes the two commits between archive-02 and the helper commit.

The imported history proves the measured source commit `7f99684668065b8fb1ebc9b2852f058c64430647` with tree `7af8853a1e2eb7ea7832f7c0bad4d2299c1ab416`, plan commit `515d9941978c12cafa37ba58eecacc0a4182226f` with parent `7f99684668065b8fb1ebc9b2852f058c64430647`, the exact C6 contract blob, the retained repair-02 helper, and the new canonical runner and Joern projector blobs. The manifest records the blob identities and hashes.

The finite Git selection is this README, `source-bundle-manifest.json`, and numbered `original-source.bundle.partNNNN` files. Concatenate parts in numeric order and verify the SHA-256 in the manifest. The unsplit raw bundle and isolated import proof are local-only and excluded from that selection. The numbered parts match the existing Git LFS rule.

This is source-history retention only. It does not assert canonical-04 success, qualification, publication, or release approval. No root source or root repository ref/index mutation, test, build, or analyzer dispatch was performed. The isolated bare import database is local-only under `.local-import-proof/`.
