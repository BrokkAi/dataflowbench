# A32: Joern launcher dependency recovery before a fresh diagnostic attempt

Campaign `20261122-06` dispatched one timed wrapper and one Joern identity
probe, then stopped before any benchmark case or analysis phase. Joern's frozen
launcher calls GNU `greadlink` on macOS. The dedicated controller's restricted
PATH omitted Homebrew, causing `greadlink: command not found` and an incorrect
`./bin/repl-bridge` location. The fast failing probe also failed process-start
identity capture. Preserve that failure, elapsed cost and uncertain inner
cleanup; outer tracked-process cleanup stopped all recorded identities without
signals. Descendant containment remains unproven.

The retained successful controls and immutable parent timing plan both record
the same longer PATH. Restore that exact value prospectively for fresh campaign
`20261122-07`; do not change the Joern launcher, analyzer JARs, Swift/Java/SDK
trees, fixtures, queries, configuration closure or expected outcomes. Bind the
GNU readlink 9.8 binary's resolved path, symlink, bytes, mode, version and system
library dependencies. Its historical release digest was not retained; do not
infer an old helper-byte identity from the current pin.

Before timing, perform a separately retained, version-only launcher preflight
from an owned directory outside the Joern distribution, using the restored PATH
and same pinned Java/SwiftAstGen settings. Require a successful 4.0.660 banner,
unchanged helper bytes and tracked-process cleanup under serial ownership and
the existing disk/timeout gates. This is setup evidence, not a benchmark case
or latency result. Do not weaken process identity checks to hide the failure.

Bind and retain all four closed attempts, including the genuine failed
invocation in campaign 06; do not relabel it as a zero-invocation preparation.
Include its source, report and cache paths and the new preflight's working and
scratch paths in cumulative accounting. Verify sealed membership and stopped
recorded identities. Use new source, attempt and evidence paths.

The user's [A31 diagnostic authorization](latency-v092-20261122-diagnostic-continuation.md)
continues unchanged: fresh complete admission, no new settled window, raw CPU
and contention evidence retained, active invocations never interrupted for CPU
or missing telemetry. The 1368-second command deadline, all resource/provenance
gates, serial ownership, genuine failure stops and strict frozen comparison
remain. This is a deliberate repair and fresh preregistration after a retained
failure, not an automatic retry loop. Settled timing, full model qualification,
successful-analysis certification, publication acceptance and comparative
performance claims remain unasserted.
