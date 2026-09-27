# Swift v3 canonical registration and execution contract

`swift-synthetic-v3` registers 108 canonical Swift inputs: the unchanged 104 v2
members and the four opaque fixtures already qualified under the narrow Darwin
Objective-C amendment. The opaque files remain at their existing versioned paths
under `populations/swift-opaque-v3`. Canonical Rust discovery explicitly includes
that directory; this is no longer staging-only discovery. The new manifest
binds all case and fixture hashes, rejects duplicate identities and extra paths,
and is selectable with `--population swift-synthetic-v3`.

Historical `swift-synthetic-v1` and `swift-synthetic-v2` still select exactly 90
and 104 inputs. Their manifests, source files, 512-MiB metadata, reports and
certificate validators are unchanged. The original staged manifest remains an
immutable historical record; this successor records canonical registration.
Current validation covers 108 Swift cases and 24 controlled-modeling assertions.
Core, native modeling, controlled modeling, calibration and Result extension
remain separate dimensions and denominators. Registration does not establish
Bifrost support or repair Joern's known identity blocker.

## Prospective resource precedence

`adapters/codeql/swift-v3/execution-contract.json` binds the new population and
fixture revision. For new runs explicitly bound to that contract, extraction
has a 150-second / 2048-MiB phase budget and analysis has a 60-second / 2048-MiB
phase budget. These phase budgets override the immutable per-case 512-MiB
metadata only within those new v3 runs. They do not alter historical semantics,
retroactively qualify a diagnostic attempt, or imply an aggregate process limit.
Aggregate memory/descendant containment remains unavailable and scoring inactive.

## Versioned report integration

`assemble-swift-v3-report.py --run <new-run.json> --output
reports/swift-v3/<new-report>.json` accepts only a new contract-bound 108-case
execution envelope. It rejects missing, foreign or duplicate observations,
population/revision/contract mismatches, phase-budget drift, historical raw paths,
and raw evidence whose digest or per-case execution binding differs. Output is
created exclusively and cannot overwrite an earlier report.

This is a versioned coverage-report schema, not the published freeze/report
schema. It preserves raw outcomes, typed diagnostics, profile/tier attribution,
and every selected case. Until aggregate resource verification is implemented,
raw reached/not-reached/unsupported observations remain inconclusive; runner
errors remain errors. No input boolean grants resource qualification. The
assembler does not run analyzers or invent missing rows. This change generates
no new execution report and cannot import the earlier diagnostic runs as v3
execution. Fresh full-population runner execution and downstream freeze-schema
integration remain required before publication.
