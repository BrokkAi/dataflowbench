# monitor07 fresh source04 candidate

This candidate is copied from the frozen recovered source03 under `../source-03/`. All implementation changes are isolated here; source03 remains unchanged.

## Changes

- Whitespace-only `args` now returns a typed missing-argv0 error from both the PS-v2 parser and independent receiver validation.
- The parser and receiver reject C0, DEL, and Unicode Cc controls in fixed-width `ucomm`, while retaining the raw padded field byte-for-byte. Printable UTF-8 names with embedded spaces remain supported.
- Added synthetic regressions for malformed fields, raw-row digest binding, four-field classifier projection, ucomm-only dual classification, and the existing argv-basename/idle MCP behavior.

## Validation

The complete fixture suite passed 55 tests using Python 3.13. These tests use synthetic provider rows and mock child processes. No OS process query, native provider call, engine, qualifier, or canonical edit was performed. Exact command and output are in `validation.json`.

`change.patch` is a new recovery-time diff from the exact source03 hashes in `handoff.json`; it is not a prior historical receipt.
