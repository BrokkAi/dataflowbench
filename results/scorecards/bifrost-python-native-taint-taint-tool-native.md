# Scorecard `bifrost-python-native-taint-taint-tool-native`

Adapter `bifrost-python-native`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2 — bifrost 0.11.0 built-in policy packs`, adapter version `0.1.0`, configuration `9dc6087e1a19bf137d603043789bb6d9bebc945fa5ad54ac4e0aee6113fd16a6`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-native.json` (`sha256:e41b7689b10a92fa63618098a2b2bbd8a0de18b852308629124322d23a295093`, normalized `sha256:e41b7689b10a92fa63618098a2b2bbd8a0de18b852308629124322d23a295093`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `200c7d45d21552c4d377b603c18d7dac53b07133c238d9ecf32225774d213692` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `629680d7fb262b6c52339423406f77d422f82f2b7f789552711af614a04c25dd` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `0313e33e59df9c58f6d63047285ec5c7872817f9d24b07304f33f62a3b11da63` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `8798729ddd0a416c700cdd1e119562a657c879e143f3f845e156687a6cf1cd49` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `cff0a71f6b5aae480fab65a8aac8c4f1acfeedb24b4e6c6609aa1d13306108db` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `ee274c1a0a44c017af67e5527a199873d8a57364ffa394bc4c09e48b2df7090f` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `c63c7a8b25c8318e45143a01f8194c75f8904f1ee20e806385ab4072945e20b3` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `a17be64086665aa9b7688159a0e9dcf54301cd7e67b0cedf538a672d2efc1ca8` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `4c0192bac3e209dbaafaa9d92ae12e6fc733f634312b14cface48af3b8f5cc74` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `0974507d34cfc105df612b99ec887bf46c13efb7638c7cb3a8434aeb910273b4` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `b978f3558a931e4bf53591866dc1bb0d11f2c23d7309bd58ae0a3e60e3ea6676` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `43cca541a72d8c303ed573468837f5e8aed4481d180aeef57db6ef6e0a62ab19` |
