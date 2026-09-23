# Canonical Swift entrypoint qualification

This separately preregistered, non-scored pair examines the unchanged
`dfb-taint-swift-native-entrypoint-positive` and `-negative` inputs in
`swift-synthetic-v2`. It preserves the prior source–sink runner, plan and evidence
byte-for-byte. The successor uses `run-swift-entrypoint-qualification.py` and
`adapters/codeql/swift-native-v3/entrypoint-qualification-plan.json`.

Both canonical fixtures read `Swift.CommandLine.arguments` in the count guard
and again at the marked indexed source. Retain both getter roles. A flow from
the guard's getter alone cannot establish the marked canonical source-to-sink
flow. Raw auxiliary flows remain visible, while the canonical flow flag requires
the marked source anchor. The negative must have neither canonical nor auxiliary
flow to its constant command to establish the intended separation.

The adapter-assisted lane uses the already retained resolver-backed source and
Foundation sink predicates. The vendor-native lane retains its unmodified
predicates and separate observations. Neither lane enters a scored denominator.
The configuration remains pending; vendor silence is not a new unsupported
partition. The other native families and two opaque modeling identities remain
independent dependencies, and Joern remains blocked on property binding.

The plan and runner closure must be committed before execution. Runtime checks
bind CodeQL 2.27.1 / swift-all 6.8.4, Swift 6.3.3, SDK 26.5, and all resolved pack
files. Extraction uses 150 seconds; queries use 60 seconds and 2048 MiB. The
original canonical 512-MiB metadata remains unchanged. Exact source bytes and
original case/population joins are staged under an explicit diagnostic identity.
Only compilation and analysis run; no fixture binary executes.

Raw phase output, unsuccessful attempts, source archives and lane rows remain
retained. Per-command time/RSS is diagnostic. Aggregate memory and semantic
completeness remain unproven even when observed flow separates the pair.

Invoke the runner with the same absolute runtime flags documented in
[canonical source–sink qualification](swift-canonical-qualification.md), using a
new output directory. The entrypoint runner only permits this preregistered pair.
The portable verifier and focused tests require no analyzer or local scratch
DB, and validate retained archives against canonical bytes.
