# Report comparison

`compare-reports` compares two normalized result reports or two directories of
normalized reports without turning a changed population into a score.

```sh
cargo run -- compare-reports \
  --baseline /tmp/dataflowbench-v0.11.0/reports \
  --current /tmp/dataflowbench-v0.11.3/reports \
  --json /tmp/dfb-diff.json
```

The command prints a concise summary. `--json` also writes a deterministic,
pretty-printed JSON document.

## Safety contract

- Reports are grouped by tool, configuration hash, and cold/warm execution
  temperature. The command requires the same groups on both sides.
- Full schema, tool version, build identity, adapter version, configuration,
  fixture revision, and derived language identities are written into the JSON
  result. Configuration changes fail closed unless
  `--allow-configuration-mismatch` is passed.
- A fixture-revision change is reported, not hidden. It is expected when the
  corpus expands; it is never a reason to pool old and new assertions.
- Assertions are joined only by their stable `case_id`. Results partition into
  retained, added, and removed sets.
- Only retained assertions produce transitions. Added and removed assertions
  are listed separately with outcome, language, polarity, and template.
- Counts remain broken out for positive, negative, and unclassified cases.
  The JSON records `pooled_score: null` and never emits a percentage.
- `inconclusive`, `unsupported`, and `runner-error` remain distinct
  coverage outcomes and are never interpreted as `not-reached`.

## Why the partition matters

Suppose an old report has 742 assertions and a new report has 890. The new
corpus added 148 assertions, and 18 of the original 742 changed from
`inconclusive` to an expected outcome. A pooled success percentage would mix
the analyzer improvement with the corpus expansion and hide the new
`inconclusive` coverage. The defensible statements are separate: 18 favorable
transitions among the 742 retained assertions, and 148 new assertions whose
outcomes must be reported in their own population.

The JSON contains each input aggregate SHA-256, every normalized report path
and SHA-256, the complete baseline/current identities, and the exact
partition, so the comparison can be reproduced byte-for-byte from the same
inputs.
