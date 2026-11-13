# v0.9.2 timing supplement — 10 November 2026

This is a new timing campaign against released commit
`86092336d8f9ca32fe9e2c4042c2dced76c1feb1`, using the unchanged v0.9.0
population and fixture revision
`sha256:7c8619b2d4a93467fd0a502ed03668bfc8f3b9878a7bd5e9271c7aca31f75f62`.
It does not resume an old execution series or reuse its expired reservation.
The existing release tag, freeze, selected reports and raw evidence remain
unchanged.

`plan.json` preregisters the measurement boundaries, populations, commands,
identities, budgets, quiet-host criteria and publication limitations. Before
dispatch the plan and execution helpers must be committed. The campaign holds
the existing exclusive analyzer lock, creates isolated source snapshots from
the release commit, and waits for five minutes of CPU observations with at least
90% aggregate idle and no competing heavy workload before each command.
During execution it retains host observations and stops on detected external
CPU/build/analyzer contention, resource loss, timeout, ownership uncertainty or
command failure. It never retries automatically.

Preflight found persistent Bifrost MCP/LSP services with zero sampled CPU.
Their presence alone does not establish an active analysis. A prospective
amendment permits a service to count as inactive only while its high-resolution
PID/start identity, arguments and cumulative CPU time remain unchanged across
observations, its sampled CPU is exactly zero, and it has no descendants.
Any observed activity resets the quiet window or stops an active measurement.
The 90% idle threshold and five-minute window remain unchanged. This decision
precedes every analyzer dispatch and is recorded with the underlying process
observations; unrelated services are never stopped.

The first executable frontier comprises 19 Bifrost cold groups, two Infer
C/C++ cold groups, and two invocation-overhead commands. Bifrost native groups
retain their empty-catalog/unsupported outcomes; a group that does not dispatch
analysis contributes no invented timing. Other cold groups and the remaining
auxiliary measurements are explicitly pending restoration or verification of
the exact runtime closure. The full membership remains in the plan; missing
measurements are not exclusions, successful results or unsupported decisions.

The historical 9f01 worktree and its task-local runtimes are absent. The exact
Bifrost 0.15.1 archive was reacquired and its archive and executable hashes
match the retained acquisition. A new optimized runner was built from the
release commit: production inputs match the final Bifrost runner's retained
source-input manifest; two test files differ. The new binary has its own
digest and is not described as the historical binary. Cached Infer, FlowDroid,
OpenTaint and Java runtime manifests were checked. The current system Java
launcher hashes differ from the historical bindings, so affected commands
remain blocked rather than silently substituting launchers.

Preparation receipts and validation are under `preparation/`. New attempts and
their complete streams, host observations and process-ownership records are
retained under `attempts/`. Analyzer outputs remain in the task-owned isolated
sources under `execution-state/timing-v092-20261110-01/sources/`; no runner
clears a frozen evidence directory. `progress.jsonl` and terminal records
distinguish waiting, started, failed and completed candidate evidence.

All timings remain candidate evidence until population, outcome,
configuration, environmental and publication gates are checked. Timing does
not affect correctness scores. No cross-release or relative-performance
conclusion follows from this campaign. Polling does not prove complete
descendant containment, memory qualification or attribution of all I/O.

Validation before launch: release harness build (`--release --locked --offline
--jobs 2`), released-population validation, focused Python guard/reconciliation
tests, `cargo fmt --check`, and `git diff --check`. Runtime manifest checks and
build provenance are retained separately from analyzer measurement time.
