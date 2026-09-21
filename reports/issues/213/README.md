# Issue 213 correction evidence

This directory is retrospective correctness evidence for
[A34](../../../docs/codeql-c-extraction-correction.md). It is not a release
freeze and does not replace the published v0.8.0 artifacts.

- `identity.json`: baseline, exact CodeQL CLI/pack, runner binary/source,
  command, and SDK identities.
- `frozen-audit.json`: extraction failures in all 126 frozen C/C++ cells.
- `reproduction/`: unchanged direct-positive probes after sandbox versus host
  extraction, including command arrays, process logs, and raw SARIF.
- `endpoint-controls/`: eight successful executable positive/near-miss
  controls; fixture/query/SARIF hashes are in `summary.json`.
- `cpp-partial-attempt/`: interrupted first host C++ attempt, retained as an
  incomplete population. It exposed partial extraction in current SDK headers
  and must not be used as a completed report.
- `sdk-control/`: complete extraction of the formerly partial closure-capture
  fixture with the explicitly selected macOS 15.2 SDK.
- `rerun/`: completed full-population reports and their unmodified raw outputs.
  Report-relative raw paths resolve within this directory.
- `c-comparison.json` and `cpp-comparison.json`: `compare-reports` output
  against v0.8.0, without pooling populations or changing denominators.
- `clippy-comparison.json`: strict Clippy diagnostics on the exact base and
  branch; the branch adds none.
- `summary.json`: coverage, eligible-positive recall, and shared-cell
  transitions, reproducible with `scripts/summarize-codeql-c-correction.py`.

The Rust regression
`codeql_213_rerun_evidence_reconciles_with_the_corrected_decoder` replays every
retained result through the corrected extraction-error decoder, unchanged
endpoint-observation gate, and existing C/C++ callsite reconciliation. The
separate frozen-artifact regression proves that every failed published
extraction is now rejected, while both real host controls remain valid.

Full sweeps ran in an isolated archive of the baseline repository. Their own
report validator checked schemas, retained raw evidence, and configuration
hashes there. The copied reports and raw outputs are byte-for-byte originals;
their historical durations are diagnostic only and make no performance claim.
