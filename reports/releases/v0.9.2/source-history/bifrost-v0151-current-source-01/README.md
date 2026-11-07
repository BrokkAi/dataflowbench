# Retained v0.15.1 source history

This directory preserves the Git objects needed to recover the exact current source review tip `f06c0f454536f1af36981163d4d819192e49e814`, excluding all history reachable from base `36d93cc32abc20ff9a0573e755555f4b71f360b3`. The bundle advertises the current branch tip and requires only that base commit.

The finite Git selection is this README, `source-bundle-manifest.json`, and the `original-source.bundle.partNNNN` files. Concatenate the numbered parts in order to reconstruct `original-source.bundle`; verify against the manifest SHA-256. The unsplit bundle and isolated import proof are retained locally and are not part of that selection. Parts are covered by the existing `.gitattributes` Git LFS rule.

The provenance pins source commit `7f99684668065b8fb1ebc9b2852f058c64430647` and plan commit `515d9941978c12cafa37ba58eecacc0a4182226f`; the manifest records the C6 contract object and build receipt identity.
