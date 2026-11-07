# Scorecard `codeql-javascript-native-taint-taint-tool-native`

Adapter `codeql-javascript-native`: `codeql` `2.27.2` (build `codeql-cli:d7b185e374bfe18c0484dac07a521a810eb9c4fb — 2.27.2 shipped suite codeql/javascript-queries@2.4.7:codeql-suites/javascript-security-extended.qls`, adapter version `0.1.0`, configuration `1d53c98769c63fe4ddbf227513538071051aa70da0c1a4e3de0d1675f658cf1a`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-javascript-native.json` (`sha256:a049223ddb448898832cadea4b47d37f96c9081828090750fe6064ea25e12214`, normalized `sha256:a049223ddb448898832cadea4b47d37f96c9081828090750fe6064ea25e12214`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 0, `runner-error` 12, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 0 | 4 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 0 | 12 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-negative.json` | `f2fc537f7528b889f69ac1ddd70d054f177118ae30d6ca6d82b75b741ca972ab` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-positive.json` | `ec22d26393d6eb918db894c622406cc32c179011a41f231130352385d537ec61` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-negative.json` | `1d3b14593c417e3c93cd3ec4905eb030bee725de48fb329b3a7892d82268add5` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-positive.json` | `dbb010c8fe3b56e2cd8e7c306916abc4b7256c01df98347b493918e1ce39d081` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-negative.json` | `b27ebb8ea483ea9b4f040ff6ee0a3674a8e82df5ac1b6ce323cf9dc2ef14ab75` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-positive.json` | `3f50e469d143fdb2c765ed5eb97cb2294447fefc5f7032d71a36ddaca79e4cf8` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-negative.json` | `a2305940ff5da41c707556b13a702bf8742b790d59911e80c0e5156cea746583` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-positive.json` | `0921a6ea19c9371e9240d7a90cba22fa5068db94fc3e701a4d398912e4d1ee90` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-negative.json` | `4b316cba52d9ece3b98bdfca285d82f32be2192dcff85c1558ee55317b3e3ef6` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-positive.json` | `7f8034b9156402b0622abd5f54e9e6b260766b12ef7bb0db83d74daf93febd07` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-negative.json` | `930707f0a56b81143df1084355a5de9e5c0f7e8d85502f0a250af4840d8289ab` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-positive.json` | `53a679e3e6a993b1b0518e715f775ad12492cfdaf4982ad1bf2ed841f044c8a8` |
