# Historical evidence after the main-only history migration

This repository uses `main` as its primary branch. The migration replaces the
history reachable from `main`, while preserving the original published release
tags and their commit identities. The original `main` tip is
`7fd8c3252a5ed0e03ec7bbc2d96ad0306613c64b`; the rewritten base is recorded in
`evidence-archives/main-before-20261026/manifest.json`.

Older operational notes may call the primary branch `master`; for this
repository, that wording refers to `main`.

## What stays immutable

The eleven published tags from `v0.1.0` through `v0.9.0` listed in the
migration manifest retain their original tag identities. Do not recreate,
retarget, or delete them. They keep the historical Git objects they reference
reachable on the remote, so the rewrite does not reclaim the storage occupied
by those objects. The archive bundle is a separate LFS object of 684,683,049
bytes, split into 17 checksummed parts.

The frozen benchmark revision, `301dd3de146337fdda5fc409c711bf4b133e4d3c`,
and its committed freeze and result artifacts remain unchanged. The migration
does not rerun analyzers or generate replacement measurements. It preserves
the evidence through an archival lineage proof and byte-exact recovery of the
removed paths.

## Verify and recover historical source files

Install Git LFS and fetch the archive before asking the helper to verify it:

```sh
git lfs install
git fetch origin --tags
git lfs pull --include='evidence-archives/main-before-20261026/**'
python3 scripts/historical_evidence.py verify --root .
```

The archive contains the original Git bundle, split into parts. `verify`
checks the part hashes and sizes, the reconstructed bundle, the original
history, all preserved tag identities, the rewritten base, and the required
source and frozen-artifact equivalence. To check a particular freeze claim,
run:

```sh
python3 scripts/historical_evidence.py prove \
  --root . \
  --revision 301dd3de146337fdda5fc409c711bf4b133e4d3c \
  --release v0.9.0
```

To restore the original raw reports and other removed source paths byte for
byte, run:

```sh
python3 scripts/historical_evidence.py hydrate --root .
```

Hydration writes only the paths enumerated by the committed manifest. Keep the
checkout clean before running freeze or release validation; the restored paths
are ignored source details and must not be staged as new benchmark output.

## Validation behavior

Freeze validation first uses ordinary Git ancestry. Only when the frozen
revision is not an ancestor and the committed migration manifest is present
does current `main` invoke the historical evidence helper. The helper must
prove the exact revision and release from the original history and verify that
the rewritten base is in the current `main` history. The ordinary clean
worktree, frozen-file digest, release-tag ancestry, and release-result checks
still apply.

Release validation of a published tag checks out that original tag and follows
the normal ancestry path. The archived proof applies to current `main` after
the rewrite; it does not change the bytes or the validation rules for an
immutable historical tag. CI fetches the LFS archive and hydrates historical
source details before running checks that read them.
