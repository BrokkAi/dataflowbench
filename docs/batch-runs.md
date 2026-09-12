# Resumable batch runs

`run-batch` executes one analyzer over an explicit set of language kernels
under a resumable execution manifest. It is orchestration evidence, not a
freeze or publication artifact: each kernel still produces its ordinary
atomically published normalized report, and final acceptance still runs the
ordinary `validate-reports` contract.

## Scope

The command currently supports `bifrost`, the analyzer with a single
kernel-command contract spanning all 13 languages. Kernel names are explicit;
there is no implicit "all" expansion. A reproducible full run is:

```console
dataflowbench run-batch \
  --analyzer bifrost \
  --bifrost /path/to/bifrost \
  --manifest reports/bifrost-v0.11.3/manifest.json \
  --kernel java --kernel javascript --kernel python --kernel kotlin \
  --kernel scala --kernel typescript --kernel csharp --kernel go \
  --kernel c --kernel cpp --kernel rust --kernel ruby --kernel php
```

On resume, repeat the same command and manifest. The runner reruns failed or
execution-incomplete slices, recovers a slice whose report was atomically published just
before an interruption, and does not rerun verified completed reports.

## Identity and safety

The first invocation records:

- the benchmark commit and tracked-source dirty state, excluding generated
  reports;
- the analyzer path, SHA-256, witnessed version, and witnessed build identity;
- the adapter version and derived per-kernel configuration hashes;
- the whole-case fixture revision;
- the operating-system family, OS, and CPU architecture;
- the requested command line; and
- one typed state per requested kernel.

A resume fails closed before any execution if the benchmark revision/dirty
state, binary digest or witnessed identity, fixture revision, configuration
hashes, environment, requested kernel set, analyzer, or manifest schema
changed. Delete the manifest or choose a new manifest path to start a new
execution population.

`pending`, `running`, `completed`, `incomplete`, and `failed` are distinct
per-kernel execution states. A valid completed report may contain
`inconclusive`, `unsupported`, or `runner-error` outcomes: those remain typed
analyzer evidence in its outcome counts and do not make publication incomplete.
`incomplete` means the runner did not atomically publish a valid report, while
execution errors retain their diagnostic as `failed`.

After every requested slice is completed, the command runs `validate-reports`
over the report set and records `passed` or `failed`. The manifest's terminal
state is `validated` only after that ordinary validation succeeds.
