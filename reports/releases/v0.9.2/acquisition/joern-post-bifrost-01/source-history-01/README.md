# v0.9.2 original-source history helper

This helper verifies one pinned private Git bundle and creates two isolated
forms of access to the original pre-rebase source history. It is intentionally
not a generic archive importer: the descriptor schema, source commits, refs,
bundle hash and size, main-archive verifier, and rebased-head boundary are all
fixed in `source_history.py`. Tests replace those constants only while building
synthetic repositories; there is no production override or CLI.

In the descriptor, `original_main` is the preserved main-history tip `7fd8…`.
The source view uses the separate PR295 ref `2991…`; `original_source_refs`
binds both that ref and the pre-main-rebase ref `0801…`.

## API

`ensure_original_objects(root, manifest_ref)` verifies the source descriptor,
every bundle part, the assembled bundle, both pinned source refs, and the
existing main-history archive. It creates a separate bare source cache and
fetches the two old source refs into the current repository using object-only
fetches. It verifies that the current `HEAD`, refs, `FETCH_HEAD`, and replace
refs are unchanged, and that no object alternates were added. The receipt has
`current_ancestor_claim: false`; object visibility does not make the old
history part of the new current branch.

`historical_source_view(root, manifest_ref, extra_source_paths)` returns a
receipt with `view_root` at the original `2991bfb...` source commit. The
checkout selects the source scopes used by
`execute-release-v092._assert_source_snapshot` plus the supplied repository
relative source-input paths. It has an independent normal Git object store,
uses sparse checkout, and refuses symlinks, alternates, changed source bytes,
or a modified cached view. This is the root on which the unchanged historical
`_assert_source_snapshot` may be run. A successful result verifies that
historical snapshot only; it is not a current-root or runtime qualification.

Both APIs first require the current checkout to descend from the pinned
rebased feature head `9c542306...` and new-main base `bff6e6ac...`. They do not
add a parent edge between the old source history and the current branch.

## Descriptor layout

The fixed descriptor is
`reports/releases/v0.9.2/source-history/pre-main-rebase-01/manifest.json`.
Its `original_source_refs` object must contain exactly the two pinned heads.
Bundle parts are named `original-source.bundle.partNNNN`, are each at most 40
MiB, and are checked on every call, including when a verified cache already
exists. The descriptor also binds the current main-history archive manifest,
its original-main commit. The helper separately pins the SHA-256 of
`scripts/historical_evidence.py`. The main helper verifies its archived
rewritten-base tree and preserved tags without requiring the current v0.9.2
frozen report files to match the old v0.9.0 snapshot.

Cache paths live below the worktree Git directory in
`original-source-history/<bundle-sha256>/`. Existing bundle, object-store, or
view cache tampering causes a failure; the helper does not repair those
caches silently. It does not execute archived code or perform analyzer,
build, release, publication, or runtime qualification work.

## Synthetic tests

Run:

```sh
python3 -B -m unittest -v test_source_history
```

Tests use small temporary repositories and patched production pins. They do
not load the private production bundle or materialize its historical
working tree.

Root integration status: archived source support only. The production cache/view and frozen snapshot callback have not been invoked. Synthetic tests cover pinned core328 and original2991 views plus graft/shallow rejection. No current source-CAS mapping, scored adapter07, native06 or Joern05 is activated by these files.
