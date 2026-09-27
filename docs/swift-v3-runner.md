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
