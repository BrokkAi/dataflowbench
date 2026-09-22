# CodeQL Swift v2 preflight

This is non-scored identity and catalog preparation for A38/A39. It does not
activate v2, assign unsupported cells, or establish analyzer correctness.

The existing CLI 2.27.0 and `codeql/swift-all@6.8.3` bind upstream build
`c6baf479093fafc81d4655dc2014dc583360308e`. Reading that exact upstream commit's
Swift query-pack manifest identifies `codeql/swift-queries@1.3.10`. The downloaded
pack confirms the same build SHA and library pin in its manifest and lockfile.
The CLI resolves 34 shipped queries. Full per-file identities and retained
commands are in `evidence/swift-v2-qualification-220/codeql-catalog/`.

The shipped `swift/command-line-injection` query imports
`CommandInjectionQuery` and uses `CommandInjectionFlow::flowPath`. The shipped
flow-source summary queries actual `FlowSource` instances. These are concrete
vendor query entry points. Their existence does not demonstrate that the A38
environment or argv expressions are sources, that the exact Process overload
is selected, or that any of the six native pairs separates correctly.

The new non-scored `catalog.ql` enumerates `SourceModelCsv`, `SinkModelCsv`, and
`SummaryModelCsv` instances through their predicates. It declares no model and
is an inventory probe, not a native benchmark query. This CSV enumeration alone
would not cover direct non-CSV FlowSource subclasses or all query-specific
barriers. No catalog rows were obtained in these attempts.

Compiler-only AST dumps retain all 14 v2 additions unchanged and identify the
real Foundation Process signature, environment members, mutation/summary APIs,
and Result failure constructor. A separate decoy input retains same-name local
Process/ProcessInfo declarations, a fixture-declared wrong-signature overload
on Foundation.Process, and incompatible dfb_source/dfb_sink signatures.
Every input typechecked; no fixture executable or shell/UserDefaults operation
was run. The derived index points back to raw compiler AST lines; it is not a
production name-based model matcher or proof of analyzer endpoint resolution.

## Retained failures and resource boundary

- The first declaration-query prototype used unsupported QL declaration APIs
  and failed type checking. Its original query and diagnostic remain retained.
  The corrected prototype typechecked.
- With `--ram=512`, CodeQL query checking explicitly raised the requested RAM
  to its 2,477 MiB minimum. Measured process RSS was 1,486 MiB for the catalog
  check, 1,290 MiB for the failed declaration check, and 1,316 MiB for its
  corrected check. These are unqualified preparation observations, not
  512 MiB-compliant analyzer results. Aggregate process-tree memory remains
  unproved; no clean outcome follows from successful query checking.
- Two native Foundation extraction probes used an explicit 60-second
  non-scored extraction-phase deadline and `--ram=512`. Both timed out before
  the declaration or catalog queries could execute. That deadline is not a
  scored analysis result and establishes neither unsupported capability nor
  absent models.
- The first timeout left an extractor in a separate process group briefly
  alive; temporary-directory cleanup raised `OSError: [Errno 66] Directory not
  empty: lazy_decls`. The subsequent process check confirmed it had exited.
  The second attempt uses the new invocation-owned process-tree runner and
  records `verified-stopped` before scratch cleanup. That historical label
  overstates the proof: only observed descendants were verified stopped. The
  raw record is retained unchanged, and does not establish complete containment.
  The reviewed runner now reports `tracked-processes-stopped`, always records
  `discovery_complete: false`, and never authorizes scratch deletion or a retry
  from polling alone. It fails loudly if the root identity was not captured.
  It retains parent lineage, kernel PID/start identities, TERM/grace/KILL
  actions, and explicit uncertain-cleanup errors; identity is rechecked before
  each signal, but that check is not an atomic signal handle. Fast double-fork
  regressions demonstrate the conservative boundary. The probe retains scratch
  and stops before later queries when containment is unproven. The old v1 runner and all hash-bound configurations remain unchanged.

The next qualification work must independently resolve analyzer endpoints,
shipped model roles, and separating controls, including the Result extension.
No v2 prospective scored partition or report is created by this preflight.
