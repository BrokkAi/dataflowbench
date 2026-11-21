# User-authorized timing continuation — 21 November 2026

This campaign executes only the 38 commands unfinished at the 15 November
user-requested pause: 27 cold groups, nine overhead commands and two warm arms.
Its committed checkpoint preserves and hashes the 55 completed parent commands
and their evidence. They are not rerun or requalified.

The [A26 preregistration](../../../../docs/latency-v092-20261121.md) preserves
all A25 resource, provenance, timeout, serial ownership and qualification gates.
The expired parent 48-hour window is not extended. This continuation uses a new
source/evidence namespace and a new prospectively authorized 48-hour bound.

All pinned inputs must verify and every command must pass a fresh complete
quiet-host window. Active invocations continue despite CPU contention or missing
telemetry. Genuine failures stop the queue without automatic retry. Existing
unsupported, inconclusive, runner-error and unqualified states remain visible;
the two Swift groups remain blocked. New results remain candidate evidence.

```sh
python3 -B scripts/v092_timing_qualified_campaign.py verify --plan reports/timing/v0.9.2/20261121-01/qualified-plan.json --require-ready
python3 -B scripts/v092_timing_qualified_campaign.py execute --plan reports/timing/v0.9.2/20261121-01/qualified-plan.json
```
