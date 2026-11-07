# Scorecard `joern-python-native-taint-taint-tool-native`

Adapter `joern-python-native`: `joern` `4.0.660` (build `joern-cli:4.0.660 — 4.0.660 DefaultSemantics only`, adapter version `0.1.0`, configuration `d74a06f0e2f9b5bb5f7c2965043c3f92417bd53847d85d0470140130a4cb1243`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-python-native.json` (`sha256:995a41f6dbd096a4115b5d6371b4170d6ca9d1bcb66bdb3afe03a244ac81b23a`, normalized `sha256:995a41f6dbd096a4115b5d6371b4170d6ca9d1bcb66bdb3afe03a244ac81b23a`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `python`, tier `modeling`

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-entrypoint-negative.json` | `8c6d60f88aad902a5a2f1b5a09e412363d3573b8444f9e2d2db7152e1cee1d01` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-entrypoint-positive.json` | `2b858e3c9dd4b40e96f111e37a91b3703edb39001f44283bd3a47fd0b48f5d0d` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-persistence-negative.json` | `06498ab1eeeecf9e3b25cca3b922a6fa82d9369f56b4910713fc37cb10151050` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-persistence-positive.json` | `62d862bda1d03454fa779baead7cb053cca53b4951cac1e6641576ff2783959b` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-propagator-negative.json` | `b526bbfee734a5c25972c6e60ad67ecddbe40861a75b0c10e854896bfacd377b` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-propagator-positive.json` | `6aabd80934b51942ea819b5d339dec318c32313029fa57c4b7c08371cfb3009e` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-sanitizer-negative.json` | `4ea87216d908e361f9a065f34ff66a213f92888858773e86049d1494235b37ec` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-sanitizer-positive.json` | `b1ac3557fb2e19137df88fd35cf646eeefc013481fdf393574e7c69977afdae0` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-source-sink-negative.json` | `4a0b528ee29d17989c22396cd9efc65ad0e16e3d0dfd4878673fd03bd8941435` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-source-sink-positive.json` | `1aa8690e39fed7f7612b79063b08f21a860329288937b441bd0f1c114ede2535` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-summary-negative.json` | `5b77829ecf221f67879850b737afd7fd4fca712e6f15650a2d9608a44e9437a6` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-native/dfb-taint-python-native-summary-positive.json` | `6d54e2edb27d3e45a5315a6a97a520b776e47d13b987f62fdedaad4c2c597a94` |
