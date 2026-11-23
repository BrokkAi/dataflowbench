# Swift preparation record — 2026-11-22

**Status:** untimed preparation is recorded. CodeQL Swift remains blocked because the exact candidate extractor binary is unavailable. No CodeQL build, pack install, query compile, analyzer, or benchmark ran during this preparation.

## Prepared artifacts

- Swift 6.3.3 was expanded from the retained, SHA-256-pinned installer into a new isolated execution root. The frozen 2,877-file, 51-symlink manifest verified exactly, with no external files. A new manifest changes only the root path to the current worktree. A version-only smoke reported Swift 6.3.3.
- The three missing Swift extractor source inputs were recovered from the immutable `github/codeql` commit `a7057b836bf29767461026718b14d20790b9085f`. Their downloaded pre-patch hashes match the retained patch receipt, and applying the corresponding patch hunks to disposable copies produced all three expected after hashes. These are source proof inputs, not executable runtime artifacts.
- The `codeql/swift-all@6.8.5-dfb.entry2` library pack was recreated in a new isolated root from the retained stock Swift 6.8.5 pack, the tracked generic QL patch sections, four tracked ported pack patches, the tracked lock file, and the exact version suffix. Verification matched all 1,498 file hashes and modes, exact membership, and zero symlinks.

## Remaining blocker

The candidate runtime receipt requires `swift/tools/osx64/extractor.real` with SHA-256 `593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f` (173,000,664 bytes). That candidate runtime root is absent. The current timed CodeQL distribution contains a different stock `extractor.real` (SHA-256 `680adbee37bdbfc5fe0a4b6d63c45bdae23fcf3bb2210530a7b751b58f319530`). The wrapper bytes match the retained wrapper hash, but the missing executable prevents restoration of the complete candidate runtime.

The retained relocation receipt attributes the candidate to CodeQL commit `a7057b836bf29767461026718b14d20790b9085f`; the tracked experimental README attributes the same `extractor.real` hash to a build from `6e9f9e38390175c41b99070a423c875f450759ca`. The old local build records and candidate directory are absent, and no immutable binary acquisition URL is recorded. The provenance conflict remains unresolved. No rebuild or substitute binary was attempted.

## Evidence

- [Current preparation summary](codeql-swift-preparation-summary-02.json)
- [Scoped retention inventory](retention-inventory-02.json)
- [Exact 1,498-file pack materialization receipt](entry2-pack-materialization-01.json)
- [Patch parser preflight receipt](entry2-parser-preflight-01/receipt.json)
- [Three-source patch verification receipt](three-source-patch-verification-01.json)
- [Source recovery preregistration](preregistration-source-files-01.json)
- [Entry2 materialization preregistration](preregistration-entry2-pack-03.json)

All new recovery and pack outputs are under the isolated `execution-state/timing-swift-repair-20261122-01/` and `execution-state/timing-codeql-swift-repair-20261122-01/` roots. Existing runtime trees, release reports, qualification plans, and prior receipts were left untouched. The earlier summary and inventory versions are retained with their supersession records for audit history.
