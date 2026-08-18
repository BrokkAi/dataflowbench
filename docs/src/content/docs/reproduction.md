---
title: Reproduction
description: Validate the frozen evidence and regenerate every published number.
---

Every snapshot is reproducible from the repository alone.

## Verify the current freeze

```bash
git clone https://github.com/BrokkAi/dataflowbench
cd dataflowbench
cargo run -- validate-freeze reports/freeze.json
```

`validate-freeze` re-reads every referenced case, fixture, normalized report,
and retained raw-evidence file and verifies its SHA-256 digest, the bound
benchmark revision, and the release tag.

## Regenerate the published results

```bash
cargo run -- generate-results --manifest reports/freeze.json --output-directory results --check
```

`--check` proves the checked-in artifacts — the same files this site renders —
are byte-identical to a fresh generation from the freeze.

## Re-run the analyzers

Re-execution produces **new** evidence and therefore a new freeze; it never
mutates an existing snapshot.

```bash
cargo run -- run-bifrost-smoke --bifrost <bifrost-binary>
codeql pack install adapters/codeql
cargo run -- run-codeql-java-kernel --codeql <codeql-binary>
```

Release notes with per-snapshot checksums live in
[`docs/releases/`](https://github.com/BrokkAi/dataflowbench/tree/main/docs/releases).
