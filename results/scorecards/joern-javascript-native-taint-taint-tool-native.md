# Scorecard `joern-javascript-native-taint-taint-tool-native`

Adapter `joern-javascript-native`: `joern` `4.0.617` (build `joern-cli:4.0.617 — 4.0.617 DefaultSemantics only`, adapter version `0.1.0`, configuration `e5e1ed92c0e9664b9124b647698318e835c57067ba610c62f3b627ccb6d576ce`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-native.json` (`sha256:29e90f0eea407eead14b08852a1bd716ad2369442863a2fc63720620920d94e6`, normalized `sha256:29e90f0eea407eead14b08852a1bd716ad2369442863a2fc63720620920d94e6`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `a32ef7b5c51a3423244091e081b6de51c94eef8dec0c35d7d2e4ce2e48e32bcf` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `412aaa630c8e05bf346baaa3949ba06fdee1a4a854a4e26c12b57cf6ddc03f2b` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `3fcd3b284271d7ddc87f62cbbc97f1f0b6171327fe76dec0599d1ba9e2202aff` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `9f55efa38b72ae1324ec268ba458b60f7f32816e70f8c9556745fd54416c79e6` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `f9cf319876357f8219093bf4fc9de6e1f6de41db33aaee8f7eed1b6ad9220779` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `caef1cdee52cd47b851d8c2e2e57e2de6dbf096a529c003f39b86a54d8de8533` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `5a63754e7f0818861455a655e042f80be896d87b9b00c4041f4e7058b753746b` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `05266acbf767b3f0a912314656caf9692a501b7c34bc570894c56ae55a7f5129` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `6d7b3dc393ea04db6359abd9d9eaf795907f8ec1b3f7ede2ba962a8bf55a4d1f` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `1d320abebf1e624186d2a568624dea5f9535b74cd969533b9341884ec6401a31` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `cb28c0aa17ce2cbc8c8e157628b69f045a6c5b06382fabd0b87633119aad3dd1` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `da2d11d45872c6347ee7b2a253fc92f2717f70d6d254c81b07755524c42ef119` |
