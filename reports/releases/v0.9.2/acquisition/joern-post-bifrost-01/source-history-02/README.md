# v0.9.2 source-history successor for the squash-published main base

This isolated successor keeps the source-history-01 descriptor, archive, source
commit identities, and legacy archive verifier unchanged. It changes the
current-lineage gate to the actual squash-published main commit
`6d34b4ce9cee7f3745c6f69e795428fa706b1080`, pinned with tree
`a985bd61bc1b153cf92fef02d99f45a0da4593d3`.

The descriptor's `rebased_feature_head` remains `9c542306...` historical
transplant metadata. It is not required to be an ancestor of the current
checkout and is never reported as the current published base. If that old
commit is present in the current object store, the helper checks that it is not
an ancestor. Receipts separately report `current_published_base: {commit, tree}`
and whether the historical feature object was present. The original descriptor
schema and all archive hashes/refs remain unchanged.

## API

`ensure_original_objects(root, manifest_ref)` performs the same pinned source
bundle, main archive, descriptor, cache, and object-only import checks as the
original helper. It requires both the descriptor's `new_main_base`
`bff6e6ac...` and the pinned current published base to be ancestors of `HEAD`,
and verifies the published base tree exactly. It leaves `HEAD`, refs,
`FETCH_HEAD`, replacement refs, and alternates unchanged. It does not make an
ancestry claim for the imported old source history.

`historical_source_view(root, manifest_ref, extra_source_paths, snapshot_commit)`
creates the same isolated sparse view at pinned original source `2991bfb...` or
core source `328bebab...`. Its receipt binds that historical view separately
from the current published base. The view includes the source paths used by the
unchanged historical `_assert_source_snapshot` plus the exact additional source
inputs supplied by the caller.

Both APIs reject grafts, shallow metadata, alternates, symlinked archive/cache
inputs, and tampered caches. Object import also rejects local URL rewrites and
Git config includes, partial-clone settings, and promisor remotes; they also
reject `.promisor` pack markers in the current store, main archive cache,
source cache, and sparse view. Every Git subprocess disables lazy fetch.
Object presence uses one exact
`cat-file --batch-check` request: only Git's explicit `missing` record means
absent, while command failures or malformed replies are errors. The helper
still verifies the archived legacy main base through the pinned historical
archive helper; it does not reinterpret the current freeze as that legacy base.

## Synthetic tests and boundary

`test_source_history.py` uses disposable local Git repositories and synthetic
pins. The fixture models a squash publication: the historical feature commit is
present, while current `HEAD` descends from the separate published-base commit
and tree. A fresh-checkout case expires reflogs and prunes the unreachable
historical feature object, then verifies object import succeeds without
reintroducing it or changing refs. Other cases distinguish a fatal object-store
error from absence and reject partial-clone and promisor configurations. Tests
cover exact base/tree pins, unrelated heads, historical non-ancestry, masked
merge parents, unchanged refs/`FETCH_HEAD`, object-store isolation, and the
historical 328 source view, alongside the inherited archive, symlink, cache,
descriptor, graft, shallow, and path-safety cases.

Run:

```sh
python3 -B -m unittest -v test_source_history
```

This is helper-source work only. No production cache/view, object import,
eligible plan, source CAS, native qualification, Joern attempt, or runtime
qualification was performed.
