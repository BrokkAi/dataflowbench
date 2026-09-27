# Full Swift v3 execution runner

`run-swift-v3.py` routes all 108 cases: 68 kernel/Result, four calibration,
20 controlled-modeling, four opaque and 12 composed-native inputs. It pins
runtime, query, population, contract and pack bytes before creating a fresh
versioned output. Fixture binaries are never executed. Each extraction has
150 seconds at requested 2048 MiB; all analysis queries and decodes together
share one 60-second deadline at requested 2048 MiB.

The collector uses file-and-line anchors and retains observed flow independently
of polarity. Persistence adds the final coverage and scope queries. Command
records, actual source copies, databases, decoded rows and artifact hashes are
retained. Every selected case receives a row, including not-attempted cases
following disk or cleanup stops. Unknown coverage and resource status remain
explicit; no historical diagnostic result is imported.

Use `verify-swift-v3-run.py <run-directory>` to validate retained source and
artifact/command binding before consuming its report. The command is a new
execution path, not qualified analyzer activation. New query entry points have
compiled under pinned CodeQL; no full108 execution is claimed by this change.
End-to-end execution and independent evidence review remain required.

The tool-lane inventory distinguishes implemented-but-unqualified CodeQL,
unknown current-v3 Joern qualification, and unsupported Bifrost Swift. These are
availability records, not fabricated per-case analyzer results. Joern's old
partitions are not silently inherited by a new population.

## Measured launch plan and blocker

Four recent pinned extractions took 84.8–88.2 seconds and retained about209 MiB
scratch each. Extrapolation to108 inputs gives roughly2.6 hours extraction and
22 GiB scratch, before queries/retries. Phase ceilings total6.3 hours, excluding
bounded metadata checks and cleanup. Execution is serial; no full run has been
launched. At implementation time35 GiB was free; the enforced30-GiB reserve means
this host cannot currently retain a comparable full run without stopping early.
Recheck live contention/disk and provide sufficient dedicated evidence storage
before launch; do not lower the reserve to force completion.

No independently verified enforceable aggregate Darwin memory/process boundary
is available. Descendant polling can miss reparented processes, process RSS is
not aggregate peak memory, and JVM heap flags are not process-tree containment.
A macOS VM or host facility would require proven memory/swap and lifecycle
controls plus fork/reparent/memory/timeout adversarial qualification. Docker
Desktop was installed but its daemon was unavailable; Linux containers would not
run these Darwin-only Foundation/Objective-C fixtures unchanged. The runner
keeps aggregate qualification unavailable and scoring off.

## Five-lane smoke (2026-09-27)

The preregistered `--smoke` selection at commit
`85ddcebb150fab3f077c5213f235368a4fc1c06c` completed all five cases.
Direct, one-hop, declared-source and opaque-propagator positives produced raw
`reached`; the native persistence negative produced raw `not-reached`.
All five normalized observations remain `inconclusive` because aggregate
resource qualification is unavailable. This is neither full108 execution nor
scored activation, a freeze or publication. The full-report verifier rejects
smoke input unless explicit smoke replay is requested.

Extraction seconds were 40.38, 38.06, 39.03, 84.50 and 86.98 respectively;
analysis seconds were 6.48, 6.51, 6.64, 8.55 and 58.38. The native lane has only
1.62 seconds of observed analysis headroom. These are diagnostic timings, not
performance certification or grounds to change the contract budget.

The compact `evidence/swift-v3-lane-smoke-01` export retains source archives,
command records, BQRS and decoded rows, extractor logs, observations and full
local artifact-closure digests. Run
`python3 scripts/check-swift-v3-smoke-evidence.py` for portable source, command
and observation replay. This does **not** verify omitted database/cache bytes.
Full local artifact replay passed using
`python3 scripts/verify-swift-v3-run.py reports/raw/swift-v3/lane-smoke-01 --smoke`.
The complete local closure remains at
`/private/tmp/dfb-220-extraction150/reports/raw/swift-v3/lane-smoke-01`;
its availability is local and temporary, not durable public evidence storage.
No full108 run was launched.

After smoke, free space measured 32.54 GiB at 2026-09-27 08:20:27 UTC. Against a conservative 60-GiB
launch target (a planning estimate, not a proven hard bound; 30-GiB enforced
reserve plus scratch and headroom), the shortfall
is 27.46 GiB. The earlier 22-GiB scratch projection alone requires at least
52 GiB free, a 19.46-GiB shortfall; actual full-run demand remains unmeasured.
No cleanup, provisioning or purchase is implied.

An isolated macOS VM with fixed guest RAM, bounded swap, host-enforced lifecycle
and dedicated evidence storage is a candidate facility. This host has no such
qualified facility established by these checks. Availability, compatible Swift
SDK execution, whole-guest accounting and fork/reparent/memory/timeout behavior
must be verified before treating it as an enforceable boundary. A speculative
VM option does not qualify this smoke or authorize full execution.


## Remaining acceptance map

- CodeQL: five diagnostic lanes completed; all 108 current-revision cases still
  need execution and independent replay under the unchanged contract on a
  qualified facility. Preserve unsupported/inconclusive/runner-error separately.
- Joern: current-v3 108-case qualification remains unknown. Establish current
  lane applicability and execution outcomes without inheriting old partitions.
- Bifrost: Swift remains explicitly unsupported; retain availability metadata
  instead of fabricated per-case findings.
- Reconcile every applicability family and all report/scorecard joins at one
  common final revision, then validate a new immutable freeze and publish through
  the normal next-release process. None of those publication gates is complete.

External prerequisites are dedicated evidence capacity with the 30-GiB reserve,
a compatible pinned Darwin Swift/SDK environment, independently demonstrated
aggregate memory/swap and process-lifecycle enforcement, and qualified boundary
behavior under fork/reparent/memory/timeout tests. Facility availability remains
unestablished. Pause further analyzer execution here; retain existing artifacts.
