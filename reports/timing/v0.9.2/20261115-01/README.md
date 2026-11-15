# Immediate qualified timing retry — 15 November 2026

The user requested “Could we try start now?” This authorizes an immediate new
execution attempt, including daytime measurements, after all existing gates
pass. The earlier daytime restriction applied to preparation for the scheduled
14 November launch; that blocked attempt remains unchanged.

This retry inherits [the A25 protocol](../../../../docs/latency-v092-20261114.md)
and the exact v0.9.2 release, fixtures, analyzer/runtime identities, cases,
configurations, queue order, deadlines and resource limits. Only the campaign
identity, earliest launch time, authorization and evidence paths change.

The plan retains 84 cold groups: 82 prepared and two Swift-specific groups
blocked. Nine overhead and two warm commands remain separate. Fresh full
runtime verification and a new sustained five-minute, at least 90%-idle window
are required before dispatch. Every later command gets a new quiet window;
CPU activity or missing observations cannot interrupt an active invocation.
Genuine timeout, command, provenance and resource failures still stop the
queue without automatic retry. Never kill unrelated work or clear space.

The original release, prior timing captures and blocked launch records remain
immutable. Completed observations remain candidate evidence pending acceptance
and publication review. Process-descendant containment remains unproven.

```sh
python3 -B scripts/v092_timing_qualified_campaign.py verify --plan reports/timing/v0.9.2/20261115-01/qualified-plan.json --require-ready
python3 -B scripts/v092_timing_qualified_campaign.py execute --plan reports/timing/v0.9.2/20261115-01/qualified-plan.json
```
