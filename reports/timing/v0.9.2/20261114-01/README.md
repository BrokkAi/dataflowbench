# Qualified timing collection — 14 November 2026

The active preregistered input is **`qualified-plan-02.json`**, derived from
`../preparation-20261114-01/runtime-bindings-v4.json`. The earlier plan is
superseded preparation evidence and must not be executed.

The earliest launch is **02:00 SAST on 14 November 2026**, conditional on fresh
verification and a sustained quiet host. All eight analyzer families have an
eligible first-frontier cold group. The queue contains 82 ready cold groups,
nine overhead arms and two warm arms, run serially. Two Swift-specific cold
groups remain blocked: the recovered Swift compiler package is unexpanded and
unqualified; CodeQL additionally lacks its custom extractor files and entry2
query-pack closure. The full 84-group denominator remains in the plan.

```sh
python3 -B scripts/v092_timing_qualified_campaign.py verify \
  --plan reports/timing/v0.9.2/20261114-01/qualified-plan-02.json --require-ready
python3 -B scripts/v092_timing_qualified_campaign.py execute \
  --plan reports/timing/v0.9.2/20261114-01/qualified-plan-02.json
```

Each command group requires a new five-minute, at least 90%-idle window.
Active commands continue through background CPU activity and missing CPU
observations; those observations retain contention/unknown flags. Genuine
command, provenance, timeout and resource failures still stop the queue without
retry. Only identity-proven owned processes may be cleaned up.

The 48-hour bound is checked between commands and during quiet waits, rather
than interrupting an active command. The entire queue may extend past morning.
Every attempt, partial setup, fail-stop and missing group is retained here;
source copies and owned caches use `execution-state/timing-v092-20261114-01/`.

Preparation validation is recorded in
`../preparation-20261114-01/readiness-v1.json`. No analyzer measurements ran
during daytime setup. Initial quiet-host qualification must still be observed
at execution. Completed measurements remain candidates until independent
acceptance and publication review; unproven descendant containment remains
separate from the internal quiet flag. The frozen release, reports and prior
timing attempts remain unchanged.
