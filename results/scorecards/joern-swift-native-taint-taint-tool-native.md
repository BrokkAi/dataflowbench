# Scorecard `joern-swift-native-taint-taint-tool-native`

Adapter `joern-swift-native`: `joern` `4.0.628` (build `joern-cli:4.0.628;engine:e63635788249ef86d87bb75c9f37929ab2309fd557e7e147765b73dbd0ac077b;frontend:4ff227bc75781d846d1076221032df8b47c0ee7f4fa1687a161c791e59006f19`, adapter version `joern-normal-v1`, configuration `3c6dd3a9fb38496eea9372b20bf2eafa1f85e7f12c35901372dc30072ee01d76`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/joern-swift-common108-attempt-01/joern-swift-native.json` (`sha256:63911a187877a60ea2e9542addd6985f249dff14297aa0a25f7e9b78fc8045d1`, normalized `sha256:63911a187877a60ea2e9542addd6985f249dff14297aa0a25f7e9b78fc8045d1`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

## Language `swift`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-entrypoint-negative/raw.json` | `d11f69ac4cf61eeb79e478e2432a7164500f8dfaa4ef2fd55899a001563970e5` |
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-entrypoint-positive/raw.json` | `2517a90f0cf0a48bb6034fde9f9c83418dcd36a438d2ac6538bffa282a3ada1a` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-persistence-negative/raw.json` | `9dab4f502208c9948c16a4a21755894be51abe203d9e7b627d5ae2058179047e` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-persistence-positive/raw.json` | `132a1e9ccc0ae33144bf469ddd25b55233343c0335502ebb5c826d7a492872e4` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-propagator-negative/raw.json` | `3f3c45182f117221209dec849ac032c5fa0ee81a97fe7609110ad00d16dafbc9` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-propagator-positive/raw.json` | `7e2431d3628b11a3a0601066e3673de97cf37efbe9c8a709052802834cd21c0c` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-sanitizer-negative/raw.json` | `0def08baa138c70ff28a2a45ba5c8da6589cb7b3c05cdb03876116d263c6ace1` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-sanitizer-positive/raw.json` | `afdee9d1be61d173b972c7b57ecbd41459c2341df3209f9febe85fc6a5ad2f59` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-source-sink-negative/raw.json` | `c016c330e078819dfd602e903521fce0a462d5d8e75e56cbdac592f17278ce2c` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-source-sink-positive/raw.json` | `92e5ada738fe192bee3a2b6f6802ce7955576644e1dcc5532724d36e54c3ad5e` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-summary-negative/raw.json` | `fdcec40bd7e1e9dcdb82295f614359dd9319f8890ed77ac411093325bd42c709` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-native-summary-positive/raw.json` | `8f1b08f6accbdf610461435b518bc161c009a93190158188da084ef04b4d3b66` |
