# Scorecard `semgrep-java-native-taint-taint-tool-native`

Adapter `semgrep-java-native`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0 — 1.174.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/java`, adapter version `0.1.0`, configuration `63152435248fc7778ad5177330ba6f204ba7bc08e5c783098899e3f104035580`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-native.json` (`sha256:ef0ec5c9bcb7ed7353cf485d1a02d30feea5820e9b0e15ef0e3eda583c79b46d`, normalized `sha256:ef0ec5c9bcb7ed7353cf485d1a02d30feea5820e9b0e15ef0e3eda583c79b46d`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `java`, tier `modeling`

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `1ef9c58d529b504b0087e792bbaf38f9028f96f396d5971a714f5e8a7e058a7f` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `d5322986de367aeb392269bb2e8a1cea745ce043a1702e9fcfe4fb2cfd94e248` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `3d1e9675d8ce02600cdfe6c1d0956e6c9710040647a491130e0ab848b37b98e9` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `dd642a6e018dddbc9eda3aa424a9e1b16e7f250ba59429d4a5f65fcbbcd29150` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `d34c5a5c6c5b307e03497427dfa45be0818ac453deddc48f69e2c5c530655b74` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `b340c4c9e4d5557bd8615b077eb211db7b4eeb30ddd131d5e8fe8175e3922cb3` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `71fcbd91e93fefa340cbd327d9b31329de0155f05b8cc33c204912baac267123` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `d0e075bec0c22496692c1dae040d49dec684a73b0ffa6d76d8773349fa12edbb` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `2be5cb42e0c4af1fafc20d9d42fd9730dc362c3a34925b04f316e0ab32734400` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `9d2958fb7e462b7c30359f5a3e2a1a12296ea4a9e6f243a1fbc602b886dac7f6` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `75b45f95db21b11b30e04506d85318c4e3057ea80633f962bac5b01acff9383f` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `8742efcfc31b0ce6dc93c4515eb54b8845cf0d86e17fb40f8d7eb08817b96611` |
