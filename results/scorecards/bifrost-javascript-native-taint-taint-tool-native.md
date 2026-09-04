# Scorecard `bifrost-javascript-native-taint-taint-tool-native`

Adapter `bifrost-javascript-native`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461 — bifrost 0.10.9 built-in policy packs`, adapter version `0.1.0`, configuration `49e759faeb792e9e8d8edb06895079ec4116b30d922c4b08e7401bc103472d8c`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-native.json` (`sha256:07588477a1d7589281e16d7c151bdc37c41aa6d3fdcb9310ac6f667069c00da3`, normalized `sha256:07588477a1d7589281e16d7c151bdc37c41aa6d3fdcb9310ac6f667069c00da3`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `805f4f841113bf4aeeb80772941d801e3dde31a0d8d0d1d0a23c9346b14b0d0c` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `db7958e7bac082ecb36024d08202e901ee705dbff0ab2a47078147070170a8e6` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `8e049935ef7b853dd8109a05264e1a34f9c225dca25e8a36c5b3a8b4c82d697f` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `67893a5bd5ae948d241ab1d5c72a01d88ddeb94e02653c851e9712a18786fcc0` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `8a4b1b9cf5f991e259f8a28d0114a6150a863c7bae2d4a1c25c4099f0c91e9d6` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `e732ef5514192bf3801874e9990affecd619ce5dd35068bbee9205dea3ccbf1e` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `46cfcae4647dcafd44ddb11cc670746890109f1a94d6c8a5bd845f489881c173` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `1af1e2aa2c371e2df2a93d90368c11e2bbdbe4d4dc2be8987af02f3d441cd68b` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `f5781e4cd538984a683359b2e9864ff5f7ae1908d1404a2a520cdf80b4daf714` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `345548595d8063ef0a3c2784bfbfca1a1ab078d830d840e77d6dfef02ebbac42` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `88fa930b64b105765975e4b1ce593d2cf27adb51f785c73d34539774021b9ac4` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `a5dc4503293d492c0e7947b1a0f3c35c4d6b0e08157b24df45b4262c5c115997` |
