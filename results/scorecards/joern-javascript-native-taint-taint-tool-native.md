# Scorecard `joern-javascript-native-taint-taint-tool-native`

Adapter `joern-javascript-native`: `joern` `4.0.610` (build `joern-cli:4.0.610 — 4.0.610 DefaultSemantics only`, adapter version `0.1.0`, configuration `21936f4b5fe760f2f4ba8ffc27c440c664cb7df00ef48374d47c74e7b2497e25`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-native.json` (`sha256:ca750185e576994faf9e23e7d44ddd3f1ca18134a4eae818eed2c8edd450d703`, normalized `sha256:ca750185e576994faf9e23e7d44ddd3f1ca18134a4eae818eed2c8edd450d703`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `a20d6c953d3b6e2a26ff2fd088c5f51ce56c04b2df77e947b68c61a42caf8da7` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `2009a5ac87b9fbec2ffa693d4e0960da12a8fd926b991cf8af08c98ad69949e4` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `af51b353568ce63f742416b618d96fc141f7191c4afe7ee71991516c314e0724` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `7dfa52c55b6b5088b07e15545d03311f01cb1dcc1eced913fe8d32ee27246492` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `07ea9041af0ba917ff05d6936e8f9a6ae33524b662192794120e3a385c01b1ab` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `5fdc194e75fb329e877727825b3b9c963c3bd0832f1ba5dfd6d0b6e6032198d8` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `51bc782b48d003a505990095b3f9e913075b5aba85f565315475423bfbe4bc4c` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `5d5c925a21079262b71bb9ed14547caee81e087cdccd6aac007291df91318e0c` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `1b8916669c7264ed9f848e652de00fa7d7d86d621eb744aa55add7fd271b70f9` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `0c04bdb97d8a4df78b6951e6db1625f8a385714056950127358ee34dc5da1d0c` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `692016f70d0ff1b949b1b3f00800bbb7a6cbac5e323e9bd1f22a0f413e78fadd` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `64a3ab38728fb2a21fdd44c298644063a5b07a46e9be6779ca443a78e4e8f37d` |
