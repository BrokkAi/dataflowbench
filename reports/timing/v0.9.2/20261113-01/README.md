# v0.9.2 timing retry — 13 November 2026

This retry is scheduled for approximately 02:00 Africa/Johannesburg on
13 November. It retains David's instruction: “Don’t interrupt the experiment
once it’s going.” The initial quiet check remains; after the first dispatch,
background CPU activity is logged without aborting a command or pausing the
serial queue. Resource, timeout, identity and real command-failure gates remain.

The 11 November attempt dispatched no analyzers: available disk space was below
the launch floor, and the pinned runner was missing. Its preflight record and
the earlier failed attempt are preserved unchanged. Free disk space now clears
the unchanged 127 GiB launch requirement; it is checked again at execution.

The missing runner was rebuilt from exact release-tag inputs with Rust 1.97.1,
one low-priority job, an offline locked dependency set and an isolated target.
A verified read-only executable copy is retained at
`execution-state/timing-runtime-20261113-01/bin/dataflowbench`, outside Cargo's
`target/` and the MBX cache. It has its own prospective digest; this is not a
claim of byte equality with the lost binary. Build provenance, source hashes
and validation are in `preparation/`.

Bifrost and Infer executable digests and Infer's full runtime inventory were
verified again. The analyzer pins, population, fixtures, configurations,
resource limits and 23-command staged queue remain unchanged. Other runtime
limitations remain explicit; this is not a complete eight-analyzer campaign.

CPU contention and unavailable observations remain attached to candidate
evidence. Continuous execution does not establish uncontended timing or A24's
original inter-adapter settling qualification. No timing affects correctness
scores, and no frozen release output is rewritten.

```sh
python3 -B scripts/v092_timing_campaign.py execute --campaign-id 20261113-01
```

Only preflight/build validation ran during preparation. Analyzer measurements
must wait for the scheduled window.
