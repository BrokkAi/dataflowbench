# Canonical Swift source/sink qualification

This non-scored run uses the unchanged positive and negative
`dfb-taint-swift-native-source-sink` fixtures from `swift-synthetic-v2`.
The [pending configuration](swift-native-integration-plan.md) and
`adapters/codeql/swift-native-v3/qualification-plan.json` bind the selected pair,
runtime inputs, runner closure, policy and separate query lanes before execution.

`run-swift-native-qualification.py` stages an explicit diagnostic control with
byte-identical `main.swift`, retains the original case metadata and population
entry in a separate canonical join, and invokes the existing bounded probe.
The probe retains its control identity; no witness is relabeled as a scored
population run. The compiler only produces an unexecuted artifact. Neither
fixture runs a shell command.

The runtime is CodeQL 2.27.1 / swift-all 6.8.4 with isolated Swift 6.3.3 and SDK
26.5. Extraction uses 150 seconds; each analysis query uses 60 seconds and a
2048-MiB request. Canonical 512-MiB metadata stays unchanged. Raw output and all
failed attempts remain retained. Command maximum RSS is not aggregate memory
certification; incomplete process containment and semantic completeness stay
unproven. Observations cannot activate a scored profile or enter a denominator.

Before execution the runner requires all configuration and execution inputs to
be tracked and unchanged from HEAD. Runtime assets, compiler, SDK settings and
all resolved pack files must match the committed identities. The output directory
must be new. For each case, it verifies successful extraction/query/decode phases,
raw extraction logs, the environment declaration, source/sink/flow row joins and
byte-identical archived source. Both vendor-native and adapter-assisted rows are
retained even when empty; vendor silence is not an unsupported decision.

Example invocation (absolute installed runtime paths required):

```sh
python3 scripts/run-swift-native-qualification.py \
  --output /absolute/new/attempt-directory \
  --codeql /absolute/codeql/codeql --packs /absolute/packs \
  --compiler /absolute/swift-6.3.3/usr/bin/swiftc \
  --sdk /Library/Developer/CommandLineTools/SDKs/MacOSX26.5.sdk
```

Only the preregistered pair runs. Other native families, the two unresolved opaque
modeling identities, Joern's binding blocker, and release qualification remain
separate dependencies. A failure produces retained diagnostic uncertainty, never
a clean negative. No full-corpus run or scored activation is part of this work.

## Retained canonical observations

The first pair ran under prospective commit `7cdce9ad`, before its results were
written. The retained package is
[`evidence/swift-native-qualification-v1`](../evidence/swift-native-qualification-v1).
Both source archives match the canonical bytes and the raw extraction error gate
passes. Every extraction, query and decode phase exited successfully.

| Canonical case | Assisted sources / sinks / flows | Vendor sources / sinks / flows | Extraction seconds |
| --- | --- | --- | --- |
| Positive | 1 / 2 / 1 | 0 / 2 / 0 | 89.54 |
| Constant-command negative | 1 / 2 / 0 | 0 / 2 / 0 | 87.58 |

The positive flow joins source line 4 to the command-array sink at line 6,
column 87. The separate executable-URL argument is recognized as a sink but
has no source flow. The negative retains the environment getter and both real
sink arguments without a connecting flow. Vendor silence remains an observation,
not a newly emitted unsupported decision. These measurements are diagnostic,
not performance certification or scored activation.

Run `python3 scripts/verify-swift-native-qualification.py` to verify the portable
raw package, configuration, canonical joins, source archives, phase completion,
query provenance, and separated lane observations. The source archives are copied
from retained databases without modifying the original attempt manifests.
