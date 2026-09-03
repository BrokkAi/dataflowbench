# Scorecard `joern-python-native-taint-taint-tool-native`

Adapter `joern-python-native`: `joern` `4.0.614` (build `joern-cli:4.0.614 — 4.0.614 DefaultSemantics only`, adapter version `0.1.0`, configuration `44be7a7aa2af4289b8665c23929d0ca8aaa046f4b1db3a43f973e31a610ce7fb`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-native.json` (`sha256:d7015cc6c9b14ee41ba7c05f547909c8b67a48df076d76c00758401ae4fb296e`, normalized `sha256:d7015cc6c9b14ee41ba7c05f547909c8b67a48df076d76c00758401ae4fb296e`). Generated from freeze manifest `reports/freeze.json` (`sha256:e3fbcae1eaf3f49192f7156616c4b2149893a8470e03ff445fcd1d5f984f9e5c`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `ffa1c1747f6efc27812bc19b1543437842985c8974415616d6de012ec2fee25f` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `9767632f559fadd3198207166e2f0e20563271289a19b578a17c4b7654a0a741` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `4f8dda40cf051e1213c360b9c6f1f5b16e1a328c23adf1ebdb54acbf9667706d` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `77d9c3e424c56cda2f162b462d2ce455cfd263450727898ea4314a0e2525fe3e` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `9d854ea113ed2c7b32f14c94112d07693b8bda5ea01f9e5fc7eedb7151006750` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `ad1e8dc631b18e9edc42c52422b427cb4f372fdaae5c2a2e2d97b13b70fc6505` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `dbe6f0964a30364f166fc1140d60db1f7dc6e9bcb9695b8891d4bfc00cb062d5` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `fd770a8498d642ecf9b7bef086211c47e0fe29a48cbbca79c133fc74022c3ec6` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `e4e3b3705c9be0436463e4335bd91de3476742d158c1636ca6bc3f2446b50511` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `81f30682a2e45ab7bebb3f44ef45357e15b91ea7037978e4c39cfaf6314ddf03` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `924d13acd9a586be763454f409a550124f72b0723f99955b9d03b88d2ad305b3` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `9872300096f7e41795b7bfed94af065450b352e5977cd49949e7a5b16428754a` |
