# Scorecard `bifrost-python-native-taint-taint-tool-native`

Adapter `bifrost-python-native`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249 — bifrost 0.10.8 built-in policy packs`, adapter version `0.1.0`, configuration `e41194af5eab6972b704081180c532e016cf061d92664a04384394883767a39b`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-native.json` (`sha256:90f3d26984ca4757ca3b8aaf1548ec46974c5ad2b0c3b3718f586a905fcac153`, normalized `sha256:90f3d26984ca4757ca3b8aaf1548ec46974c5ad2b0c3b3718f586a905fcac153`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `5a130d0d723eaf76401946a8790710b9aa0095cc1f9cd13c2cb2e8f1d47c6008` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `8872a99d6190d1624921d62c18a7199d1132d8602764f1b60b31d64cda01fcf2` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `9cb44e368736e1810e1b40aae1b633ddb1b52a8da35aa763fb0b1e4a73f75613` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `262ee20557761658e3c3570c23b987b589e4ea639a0de1cedfc3caad5ba2fb7c` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `afc3dc76a35292e77b61f1c95edf21bb1f7bf582615bf7a6ee971ea49c1f10dd` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `ebb94be49cfb0534c73dabbe9c039538fa5a0c826cd8a474dbc32295f73de188` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `67fc83d917e968e137f5d757920b9c302dfa5e9258765909f7a6dd127a03478f` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `6f10662a12da5b46bb2fdfe7b10b8334193bffeb8552910aa5f1547b50faf096` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `f2a3bdb50f218996c1da859209ab726233710069a78b35b1cdf1b63b0f1f7b27` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `64185e1a494df3f27d49141c297c0d13e0c0d5c63b6cae0bd6663e7d2bf7ef19` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `cf5055f12000754f4fab4cd2f4c49ead6a5bf82afb1706f7b7b915594d04a46f` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `f12c6e10f8e6a8b437b94470a989817575fd5a5437e6ab1f43eba9ab6a884be3` |
