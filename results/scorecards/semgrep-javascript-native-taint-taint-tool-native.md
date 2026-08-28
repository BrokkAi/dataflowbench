# Scorecard `semgrep-javascript-native-taint-taint-tool-native`

Adapter `semgrep-javascript-native`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0 — 1.174.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/javascript`, adapter version `0.1.0`, configuration `db250477c037087929dd8c1c5fcf06254b0488f7517b6ff64aad72d026a2782a`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-native.json` (`sha256:f2c815b3b80d5c5e3f15d8c6232532a9a9afe69cd7c3fa3eea165ee8e784bd75`, normalized `sha256:f2c815b3b80d5c5e3f15d8c6232532a9a9afe69cd7c3fa3eea165ee8e784bd75`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `50d30d4bef435f32071227aff4983133a1b733ceb8f1535753beb1808d782635` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `c0135713334382a14ff1e43fd443992badc4df96906defa0939bebe0edd8bd9e` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `a52a00789012500784b7ed9c5be91d405fa38e6b5ab532248d47dcb23acf7b8e` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `8695a0a3ab4793f9e5bc3dcdeaeef1eea1e4e6d212bdc2c718df22bd43f5a2e0` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `3f16ed73842619975416998ac59cedb98bf2b88b27633a1b40676d03088d7c81` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `56c658d70a7a753fdcfe024f8fc700ab3eed81c08f911901836969967c261308` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `8e1a7c26b03300754af16f37047d13426919db82a65026fd045b391cb2f1e62e` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `9ad627d31f2c9c880bf89d30b8fc0e58642b610d21fb6834d012586450847e5b` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `551fc5ee04fefe1026ae139917b01232cc2b59db4f20661c3fad3cb6ac2de801` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `60f513b36609f1cba1a51a4d6df075fa0e00c422c7feb11e436996667f1a5c09` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `e4ad53aafd5497c2547547c9754579c2012470835c0817506f4216de7dd636dd` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `1c521f36e75e940e48fa76c7d0262ca030a8dd91998f054f164da150fee9c969` |
