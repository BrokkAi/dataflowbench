# Private Joern05 execution adapter 04

This private candidate is source and harness preparation only. It does not
invoke Joern, Java, an analyzer, replay, qualification, admission, Git, source
integration, release, or launch. The frozen03 source and evidence remain in
`/private/tmp/joern05-execution-adapter-03` unchanged.

The independent review identified a real startup race: bootstrap held the
canonical common flock while detached execution opened the same path and used
`LOCK_EX|LOCK_NB`. The repair uses an explicit inherited-open-file-description
handoff. Bootstrap passes its already locked descriptor and a one-record child
readiness pipe, and retains the lock until the child verifies descriptor/path
device and inode identity, writes an fsynced immutable
`candidate/execution/supervision/startup-ready.json` receipt, and sends the
source-bound frame. The parent validates the exact child and parent PID/birth,
lock identity, graph/source/plan/contract bindings, token, and receipt digest.
Bootstrap then closes its references; the child retains the flock through its
execution lifetime. Startup wait is finite at 600 seconds, with no retry. The
existing 120-second child admission handshake and 600-second stage startup
lease are unchanged. Cleanup remains owned-child-only and all failure paths
write immutable receipts without inferring completion.

The history metadata reader is not an additional opaque graph role: the graph
remains exactly 88 inherited roles plus 7 adapter roles (95 total). It is now
bound explicitly as the canonical stage source closure entry:

`reports/releases/v0.9.2/acquisition/joern-post-bifrost-01/history_provider_02.py`

SHA-256: `da691ca16a4d1169e1f32d3524fb146bc4e60722dd99ea12bb9e03ac38436a8b`.
No other unsealed runtime source path was found in the seven adapter modules.

Validation uses `/opt/homebrew/bin/python3.13 -B -E`:

- `test_adapter.py`: 30 passed.
- `test_graph95.py`: 11 passed.
- `test_durable.py`: 17 passed, including bootstrap post-Popen cleanup.
- `test_startup_handoff.py`: 4 passed using real tiny Python children and
  flocks for delayed handoff, permanent-unready timeout, inode/path swap, and
  peer exit.

Total: 62 passed. The test logs and exact source/test hashes are recorded in
`implementation-handoff-04.json`.

This candidate does not claim actual history replay, native controls, current
qualification, production authorization, analyzer completion, release
readiness, or publication readiness.
