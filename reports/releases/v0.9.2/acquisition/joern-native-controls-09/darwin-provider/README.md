# Darwin KERN_PROC_ALL provider ABI v4

This is a new source-bound successor to the immutable ABI3 provider in
`joern-native-controls-07/darwin-provider/`. It keeps ABI3 untouched and
introduces the reviewed first-table-only observation as an explicit ABI4 row
kind. The implementation is based on the scoped decision at
`reports/releases/v0.9.2/qualification/joern-post-bifrost-01/native-snapshot-interval-policy-proposal-03.json`.

## Snapshot contract

Each call makes exactly one fixed-bound `sysctl(KERN_PROC_ALL)` call for the
first table and one for the revalidation table. It performs no size query,
retry, third table, or extra deadline work. Both raw tables must fit below the
existing 8,192-row bound and pass alignment, record, duplicate, and PID-zero
validation. Every positive first-table PID is checked against the second table.
If the same PID is present in both tables, PPID and birth identity must match;
a changed identity fails the whole call.

The output is a bounded union of these typed rows:

- **Stable first-table row:** PID, PPID, birth, and state from the first table;
  `proc_pidpath` or the original short `p_comm` is retained only when the
  second-table PID, PPID, and birth match.
- **First-table-only row:** a positive PID from the first table that is absent
  by PID from the second table. It retains the exact first-table PID, PPID,
  birth, state, and `p_comm`, with source
  `KINFO_FIRST_TABLE_ONLY`, origin `FIRST_TABLE_ONLY`, and witness
  `FIRST_TABLE_ONLY_UNVERIFIED`. The first-table `proc_pidpath` call did occur;
  its returned path bytes are discarded because the row did not revalidate. Its
  actual nonnegative errno is preserved. Path status is
  `DISCARDED_UNREVALIDATED_FIRST_TABLE_ONLY`. Status value `4` is reserved and
  rejected for first-only rows; `-1` remains the not-attempted sentinel only
  for second-table-only rows.
- **Second-table-only row:** a positive PID from the second table absent from
  the first. It retains that second-table record's PID, PPID, birth, state, and
  `p_comm`, with the existing second-table-only/unverified provenance.

First-only and second-only rows are observations, not evidence of a new birth,
current identity, ownership, argv, cleanup authority, or historical absence.
The provider does not classify workload relevance and does not implement the
outer native-before / command / native-after acceptance rule. The caller must
keep one-sided rows out of current identity maps and argv bridges and enforce
the proposal's per-query historical-row and candidate/tracked-PID gates.

The metadata uses exact accounting:

- `first_positive = revalidated_first + first_table_only`
- `second_positive = revalidated_first + second_table_only`
- `output_rows = first_positive + second_table_only`

PID zero is counted separately in each table. The output buffer remains fixed
at 8,192 rows; if the first/second union cannot fit, the call fails closed.

## ABI and source binding

ABI version is 4. The exported snapshot symbol is
`dfb_native_snapshot_v4` with `dfb_native_row_v4` and `dfb_native_meta_v3`.
The metadata adds `first_table_only_pid_count`; exported ABI version, row/meta
sizes (4,152-byte row and 96-byte metadata), row bound, and command bounds are
checked by the C and Python sides.
Production loading requires an absolute regular dylib path and explicit
SHA-256 pin. Symlinked path components and file changes across hash/load are
rejected. The provider source is independently source-pinned by the query
adapter.

The ABI4 constants for first-table-only rows are:

- command source `4`: `KINFO_FIRST_TABLE_ONLY`
- path status `5`: `DISCARDED_UNREVALIDATED_FIRST_TABLE_ONLY`
- snapshot origin `3`: `FIRST_TABLE_ONLY`
- revalidation witness `3`: `FIRST_TABLE_ONLY_UNVERIFIED`

Existing stable and second-table-only enum values are preserved. The previous
first-only status value `4` is reserved; ABI4 now emits value `5` to state that
the path call happened and the unverified result was discarded. No argv,
CPU, credentials, pointers, or whole `kinfo_proc` records leave the provider.

## Validation boundary

The fake-library Python suite and macro-redirected C self-test use synthetic
fixtures only. The test executable redirects `sysctl`, `proc_pidpath`, and
`getpid` before including provider C. The built ABI4 dylib was inspected for
its exported symbols but was not loaded or called. No live process enumeration,
OS-wide query, analyzer, or Joern execution was performed.

The append-only `build-receipt-followup-01.json` records the first-only path
provenance correction and its exact source, test-log, and rebuilt-dylib hashes.
The prior draft source, dylib, receipt, and logs remain byte-preserved under
`recovery-pre-path-provenance-fix-01/` with a hash manifest. The followup adds
synthetic coverage for a successful path whose bytes are discarded and for a
zero-length `proc_pidpath` result with `ENOENT` whose actual errno remains
visible on the first-only row.

Focused commands used from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider \
  /opt/homebrew/bin/python3.13 -B -m unittest -v test_darwin_native_provider

xcrun --sdk macosx clang -std=c11 -O1 -Wall -Wextra -Werror \
  -fvisibility=hidden \
  -I reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider \
  -o reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider/darwin_native_provider_selftest \
  reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider/darwin_native_provider_selftest.c

reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider/darwin_native_provider_selftest

xcrun --sdk macosx clang -std=c11 -dynamiclib -O2 -Wall -Wextra -Werror \
  -fvisibility=hidden \
  -I reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider \
  -o reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider/libdfb_native_provider_abi4.dylib \
  reports/releases/v0.9.2/acquisition/joern-native-controls-09/darwin-provider/darwin_native_provider.c -lproc
```

The integration adapter still needs an independent review of ABI4 count and
row provenance and must enforce the accepted outer-query conditions. This
provider package alone does not establish admission, qualification, scoring,
or publication readiness.
