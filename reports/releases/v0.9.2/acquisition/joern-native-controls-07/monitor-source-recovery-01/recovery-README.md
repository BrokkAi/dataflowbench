# monitor07 recovery after reboot

This ignored local recovery area preserves the private source candidates and their history. Nothing here was copied into canonical acquisition or validation paths. The original `/private/tmp/v092-native-monitor07-integration-03` directory was gone after reboot.

## Recovered candidates

- `source-02/` reconstructs the completed ABI-v3 candidate. All three source file hashes match the historical handoff pins. Its README, `handoff.json`, and `change.patch` were reconstructed and their hashes match the recorded receipts.
- `source-03/` reconstructs the latest recorded PS-v2 monitor edits from source02 plus all 17 recorded patch calls, including the final fixture-helper patch. The source files and a newly generated review diff are preserved. The session log contains no final source03 handoff or final file hash.
- `source-01/` is retained as the exact base for source02. Its three source hashes match the earlier handoff.
- `recovery-receipts.json` records exact pins, historical test boundaries, session provenance, and which hashes were reconstructed versus historically recorded.

The source03 log records a 48-test synthetic pass before its last test-helper patch. That pass is historical evidence only; it does not validate the final source03 test file.
