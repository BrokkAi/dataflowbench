# Darwin KERN_PROC_ALL provider ABI v3 source candidate

Status: **source-only candidate** in `/private/tmp/v092-darwin-native-provider-03`.
It is a fresh source copy based on provider02. The predecessor's build03 and
provider02 files are untouched. This directory contains no dylib or build
receipt, and no binary is attributed to these source bytes.

## Snapshot contract

The helper makes exactly one fixed-bound `sysctl(KERN_PROC_ALL)` call for the
first table and one for the revalidation table. It does not size-query, retry,
probe permissions, or take a third snapshot. It reads `proc_pidpath` only for
nonzero PIDs from the first table. Those rows must all validate and match PID,
PPID, and birth identity in the second table.

Every positive PID found in the second table but absent from the first is now
retained as a separate row. The row carries atomic PID, PPID, birth seconds and
microseconds, normalized state, and short `p_comm` bytes copied from that one
second-table record. Its typed fields state:

- command source `KINFO_SECOND_TABLE_NEW`;
- native snapshot origin `SECOND_TABLE_ONLY`;
- revalidation witness `SECOND_TABLE_ONLY_UNVERIFIED`;
- path status `NOT_ATTEMPTED_SECOND_TABLE_NEW`;
- path errno sentinel `-1`, translated by Python to `None`.

The source and path-status tags establish that no path call was made. The
adapter does not infer path success from an errno value. Second-table-only
rows are not described as new process births or historical absence; PID reuse
is possible across observations, and downstream must bracket each candidate
through the outer native-before / complete-`ps` / native-after pass or fail
closed.

The C and Python receivers enforce exact counts. If `first_positive` is the
number of first-table nonzero rows and `added` is the number of second-table
only rows, then `output_rows = first_positive + added`,
`revalidated_first_rows = first_positive`,
`first_record_count = first_positive + first_pid0`, and
`second_record_count = first_positive + added + second_pid0`. The Python
adapter also requires row-origin/source/witness categories to match these
counts, rejects duplicate output PIDs and unknown source enums, and fails the
whole result on malformed metadata or row fields.

The fixed ABI returns only allowlisted scalar identity fields, bounded command
bytes, and typed provenance/status. It never returns `kinfo_proc`, pointers,
credentials, argv, or CPU data. PID 0 is counted separately in each table.
First-table path fallback keeps the ABI-v2 rule: a zero-length
`proc_pidpath` result uses validated `p_comm` regardless of errno, while a
positive path requires errno zero and valid termination.

## ABI and source binding

ABI v3 adds a third command-source enum plus explicit path-status,
snapshot-origin, and revalidation-witness enums. The C exports row/meta sizes
and `dfb_native_snapshot_v3`; the Python ctypes structures check the ABI
version and exact exported sizes before reading rows.

The production adapter requires an absolute regular dylib path and explicit
SHA-256 pin. It rejects symlinks in every path component before hashing and
again after loading, checks the file identity across the hash read, and checks
the loaded library hash against the caller's pin. The adapter source itself is
separately hash-pinned by the monitor integration. Use the approved absolute
`/private/tmp/...` path; `/tmp` may resolve through a symlink on macOS.

## Build recipe (not run)

Compile only after independent source review and root authorization:

```sh
xcrun --sdk macosx clang \
  -std=c11 -dynamiclib -O2 -Wall -Wextra -Werror -fvisibility=hidden \
  -I/private/tmp/v092-darwin-native-provider-03 \
  -o /private/tmp/v092-darwin-native-provider-03/libdfb_native_provider.dylib \
  /private/tmp/v092-darwin-native-provider-03/darwin_native_provider.c \
  -lproc
```

The separate `darwin_native_provider_selftest.c` redirects only `sysctl`,
`proc_pidpath`, and `getpid` at compile time before including the production C
body. It has no test hooks in the production dylib. Compile and run this
synthetic test executable only after root authorization and independent review:

```sh
xcrun --sdk macosx clang \
  -std=c11 -O1 -Wall -Wextra -Werror \
  -I/private/tmp/v092-darwin-native-provider-03 \
  -o /private/tmp/v092-darwin-native-provider-03/darwin_native_provider_selftest \
  /private/tmp/v092-darwin-native-provider-03/darwin_native_provider_selftest.c
/private/tmp/v092-darwin-native-provider-03/darwin_native_provider_selftest
```

The self-test source has **27 synthetic scenarios** covering the positive
retained second-only identity/source, malformed second-only
birth/parent/state/command, duplicate second-table PID, second-table
saturation, first-row PID reuse and parent change, and existing path, table,
and state-mapping behavior. It has **not** been compiled or run.

## Synthetic Python tests

Run only the stdlib fake-library suite:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=/private/tmp/v092-darwin-native-provider-03 \
  /opt/homebrew/bin/python3.13 -B -m unittest -v test_darwin_native_provider.py
```

The suite uses an injected fake ctypes library, not a compiled dylib. It checks
ABI size/version, bounded row decoding, exact first/second coverage equations,
second-table-only identity and typed provenance, no-path sentinel handling,
source/provenance mismatch negatives, duplicate rows, saturation, path errors,
symlinked ancestor rejection, hash pinning, and deadlines. These tests do not
establish C/SDK compatibility or live macOS API behavior. Current result:
**29 tests passed**.

## Qualification boundary

This source has not been compiled, loaded, or called against macOS APIs. No
monitor, native06, Joern, analyzer, privilege, TCC, process-signal, or cleanup
action was performed. Root must review this source, then separately authorize
the fake C self-test and one ordinary-user probe if appropriate. Before
production integration, monitor07 needs a successor that understands the
ABI-v3 source/status/origin/witness fields and bridges second-table-only rows
through the complete outer process observation. A probe pass would still not
qualify native06, Joern05, scoring, or publication.
