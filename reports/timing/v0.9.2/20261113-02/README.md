# Auxiliary continuation of the 13 November experiment

Campaign `20261113-01` completed all 21 staged cold groups. Its next command
specified Bifrost overhead in PHP, but the registered A24 arm is Python.
The existing runner rejected PHP before creating the overhead workspace,
constructing a policy-analysis command or starting a timed repeat. Binary
identity probes and a fixture/environment stamp did occur. The rejection and
every completed cold record remain unchanged.

This independently source-reviewed correction dispatches only Bifrost Python
and the not-yet-dispatched Infer C overhead command, each with the original
three fixed repeats and min/max range convention. It is not a retry of an
analyzer failure, and no cold group is repeated or replaced.

The new plan binds the same release, fixtures, analyzer/runner digests, source
projection, resource limits and per-command deadlines. Parent execution
consumption is charged against the unchanged total budget. The helper admits
this continuation only for the exact pre-analysis language rejection, verifies
all parent cold completions, checks that Infer overhead was not dispatched,
and requires the digest-bound parent initial quiet admission.

As part of the same already-started experiment, it inherits that initial
admission. CPU activity is recorded without another quiet wait or a CPU-driven
abort. It does not claim a new independent quiet qualification or A24's
original inter-adapter settling qualification. Genuine resource, timeout,
provenance and process-ownership gates remain intact.

```sh
python3 -B scripts/v092_timing_campaign.py execute --campaign-id 20261113-02
```
