# Scorecard `bifrost-javascript-native-taint-taint-tool-native`

Adapter `bifrost-javascript-native`: `bifrost` `bifrost 0.12.0` (build `676def6c6615002002b1bb9d25211ad1476a5b5d — bifrost 0.12.0 built-in policy packs`, adapter version `0.1.0`, configuration `29a6a062e94d60c5674ca6aa2ea2cea7770f2bce26cc2f6fb5fcc1ad7de2130a`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/bifrost-javascript-native-attempt-01/bifrost-javascript-native.json` (`sha256:87401d1d69218ced1a7b31bb3f8debebaa7f64c95aa77441c28ea611c6b822a0`, normalized `sha256:87401d1d69218ced1a7b31bb3f8debebaa7f64c95aa77441c28ea611c6b822a0`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `5be6ba0e9b1a2df96740cca97c5d97657c9153b2d5aace993b36354a40574a2d` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `4a343d23d2fe193408763f5ca19aec59935847ee6c86d39efe31958f2932f1a4` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `3f9ff67906e4f179510a7afac5c3a06ded479566a59d48da89db502559f9c2e3` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `8b4de446f31ed8fe52d54e7b83215a3a30adb6d3dc8a9a5423f5f0624874e389` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `db6533bc472f17ad7c67bb9e48bb6a6c66cf86c4cad8934a6ff802564d4388c8` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `56a2b542d50a7ff2a91bfdb6ca89011a82102abe03b1973e5733fab4e9296987` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `cc9e53cf09e93c5c94e39ff93f19eff7046bea2ed3fd647f4471d137c11e238f` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `aa2e137d6ae4a1ed393e8306ec36d7077fbb7052d03b8f3f778d673838295108` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `bcec930c286e9fbcc52da1679d3975cd7f8411b9c7fd70a4fabb5d534721e3c6` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `a11f16205ff3d3820f01f359d38547f4f4725de2b06d875fb6cf59332be54683` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `983d31d35dd830fec17a31ae4e6c1c08f0478a9694c424de85b648c929a52a79` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-javascript-native-attempt-01/capture/reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `d68aad88ace829bcd2c55a975b2d5eb20bf1db49d92359b9d0c73d5ca59cb922` |
