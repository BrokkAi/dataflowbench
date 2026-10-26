# Rebase after the main-history rewrite

Branch `dave/v0.9.2-full-refresh` was transplanted from `0801eb591dda8a1e054931250b2934e0cbb763fd` onto `bff6e6ac2c6ab27f8370d81fa38ac9ba6cfe15d8`, producing `9c542306635e0a7eb24b3898280e267a85234f12`.

All 100 ordered commits remain. The raw Git blob deltas of 98 commits are identical. Commits 1 and 11 differ only in `.gitattributes` and `.github/workflows/ci.yml`, preserving both the new main archive/LFS validation and the v0.9.2 byte-preservation and test rules. The final tree equals main plus the original feature delta except for those two additive integrations. The old main tip is not an ancestor of this branch.

The tracked tree is now 929,641,439 bytes, down from 6,572,880,413 bytes. The 158,888 pre-existing untracked paths were retained. The dirty 123,908,716-byte ledger was restored byte-for-byte at SHA-256 `2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851` and remains unstaged. Backups, stash identity, complete original feature lineage bundle and commit map are recorded in the accompanying JSON and audit directory.

Historical measurement receipts, source pins, rows, failures and timings were not rewritten or requalified. The earlier source commit identities remain the identities actually used by the experiments. Original source-CAS archive retrieval and historical-to-current lineage are distinct from current-HEAD execution permission.

The remaining Joern monitor-policy choice and publication-review hold remain in force. No analyzer, native qualification or release was launched by this rebase.
