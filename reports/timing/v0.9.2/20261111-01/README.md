# v0.9.2 overnight timing retry — 11 November 2026

David requested another overnight attempt and explicitly instructed:
“Don’t interrupt the experiment once it’s going.” This prospective plan
implements that change before any new analyzer dispatch.

Launch is scheduled for approximately 02:00 Africa/Johannesburg on 11 November.
The initial five-minute quiet CPU gate remains. After the first invocation
starts, the serial queue continues without CPU-triggered aborts or waits
between commands. CPU contention and unavailable observations are retained as
metadata. A successful invocation under contention remains completed candidate
evidence; it is never certified as uncontended.
Continuous execution also forgoes A24's inter-adapter settling step; these
observations cannot be represented as satisfying that original qualification.

Disk and source/retention limits, exact tool/source/population identities,
per-command deadlines, serial analyzer ownership, process-identity checks and
genuine command-failure stops remain unchanged. The plan retains the same
23 staged commands (19 Bifrost cold groups, two Infer cold groups, and two
overhead commands); other analyzer/runtime limitations remain explicit.

The failed `20261110-01` attempt and all of its records remain unchanged. The
new campaign references the earlier digest-bound preparation receipts and
verified runtime assets; it uses fresh source snapshots and new attempt/output
paths. It never resumes or overwrites the previous failed campaign.

The committed plan and helpers are executed with:

```sh
python3 -B scripts/v092_timing_campaign.py execute --campaign-id 20261111-01
```

No measurements are launched during preparation or scheduling.
