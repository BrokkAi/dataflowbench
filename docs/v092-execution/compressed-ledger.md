# Compressed v0.9.2 execution ledger

The runtime ledger remains `reports/releases/v0.9.2/ledger-v1.jsonl`. Its original bytes are restored from an immutable gzip archive held in Git LFS, selected by `reports/releases/v0.9.2/ledger-archive-index.json`. The raw file is local and ignored by Git; compression does not change attempt status, source identities, receipts, or rows.

Run `python3 -B scripts/v092_ledger_archive.py hydrate-current --root .` before reading the ledger in a fresh checkout. The helper checks the selected manifest digest, compressed and uncompressed content digests, every line digest, row count, and the original committed 57-row prefix. It refuses to overwrite a different existing ledger. CI performs the same restoration before the execution tests.

The initial `ledger-109-01` archive contains 109 rows, 123,908,716 raw bytes, SHA256 `2049200a6c4085a926f51f7869b47f4e78916148dfe5650ff25e024d9e8d4851`. Its gzip is 12,990,606 bytes. The original 57-row prefix remains identified by SHA256 `31ea08cf5f0fa04fe07697bb8d3683e2a313140e6e12e15fe7e7963a82cdc1f2` and original Git blob `aa299771be8ebce13c8e7473723aa37cdafac305`.

After an authorized real attempt appends a row, create a **new** archive directory with `pack --root . --output <new-directory>` and update the index to that manifest and its SHA256. Preserve prior archives. Never overwrite an archive or select a stale archive to conceal a changed live ledger. Verify the new selection before committing its LFS payload and index.

The separate `source-history/pre-main-rebase-01` archive preserves original pre-rebase commit identities. Retrieving those objects is archival provenance only: it does not make the old graph an ancestor of the rewritten branch or authorize a runtime attempt.
