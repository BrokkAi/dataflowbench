# Scorecard `joern-python-native-taint-taint-tool-native`

Adapter `joern-python-native`: `joern` `4.0.617` (build `joern-cli:4.0.617 — 4.0.617 DefaultSemantics only`, adapter version `0.1.0`, configuration `e5e1ed92c0e9664b9124b647698318e835c57067ba610c62f3b627ccb6d576ce`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-native.json` (`sha256:c2ea3397a8aeeef458351ef14161a7f24bf5ab1cb040ad78e44ef5206098181a`, normalized `sha256:c2ea3397a8aeeef458351ef14161a7f24bf5ab1cb040ad78e44ef5206098181a`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `5aef02e4eaf21a9e700407e21c3fe8c33575943bd48611d98ee05f435edda29c` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `753b8f09aae96a405ec54374391b13fdd9a8902d421c0ab0dd7efb1baf592b91` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `319d65179bf74e696eeea4c7ef0e79405df1de12cec668c2d09a0991e97c6227` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `eb72630677ea237db7de0cbee6d6f99faf8786f03c311c865ad53d955cc565f6` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `2d38fe3355acf885b106451970e8739b3e7675f36ea898f3373be6ea4aa698a5` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `f3b1a46a9d19b51e66c214677b97aae837ade9483f2b0a891a64e2f3dc4cf7f9` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `56d59628df6146efce9a7776ec30225359994ec1d5121374081c39c3ae6f354b` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `a517280daa38c2cecf87d726c52644ce119af0831a8972e78cc4f76e590a6dc9` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `fe4b2b73f288e42ad201342d9f03ec1a91983cac2ea3d689168c72c01c09ac01` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `0f0ce31b84f2a971cc68f3d77d5f4cf754b727ab6b35dae1e80b7846c6c2e4c8` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `750aaf4fefbcd2d11efa56d8e26eecacd0dda1e8b2ba2f4be69d9148589e1714` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `b599386fe0a5b5ffde5502c9f3655e37a2202b953cda11330fd95d24081c2ddd` |
