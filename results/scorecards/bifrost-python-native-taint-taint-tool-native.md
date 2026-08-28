# Scorecard `bifrost-python-native-taint-taint-tool-native`

Adapter `bifrost-python-native`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57 — bifrost 0.10.7 built-in policy packs`, adapter version `0.1.0`, configuration `6b12ed91fe6d3178ea24e9be7feb9f230268987949ac7a0e724069009265be05`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-native.json` (`sha256:ae24e34efe49f7307d571e9b3c42de1d5f829fb6d965cfe455ead4010bbaba56`, normalized `sha256:ae24e34efe49f7307d571e9b3c42de1d5f829fb6d965cfe455ead4010bbaba56`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `8173bd9374d7ef9403357267ede47f7dd57bfba6d4b794cc4ea334677a6fed6d` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `826b325fe1180929ec2eb6a5a136f68bab4ac59997bcaea98331ee8f98b70605` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `80eb2c4eae8d1c678c4d4b4949e06a25483a8bd4d1b0895ee532671a5b4e6ffc` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `46740719b6dda9eaa2f508fff6905eda910f187de8aba19ca6501bf45bf11b42` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `c4f0983f5aa8d5814523a24ac19a59ac7104b73ec95b7793cd042bd86e571776` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `f60b293521d47ad9d68b3f662ec8572e091f922a3aba9233e4b528247f47c3c5` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `debc733126012163a6be7e707538e005b21ac3cf9884427dd8af596eb65cf7dd` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `de7e5c5a915fd017ed15d1bb19ab7850edcc1034554855e62e03a3c7b7055633` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `206f286faee3d5fb80d2d333b8413e9bd0377e8356dc823241dcaeeebf300724` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `ffe656031b1b3583f7c13459a790dda6c192d4d835367fdde94362cf366037bc` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `b1579817a273742bc9813f1e5b31e02c7c1d2347e059364cb50c37fb987a747c` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `fe7cfdee6b3b4a16fe19be336bf6145c9f1aa2001582fa57f5181e4aa8bba35d` |
