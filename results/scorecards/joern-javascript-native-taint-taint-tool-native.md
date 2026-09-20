# Scorecard `joern-javascript-native-taint-taint-tool-native`

Adapter `joern-javascript-native`: `joern` `4.0.628` (build `joern-cli:4.0.628 — 4.0.628 DefaultSemantics only`, adapter version `0.1.0`, configuration `47cce57071af2d33a8c7cdf27333dd615a77098d9ddbbb9d30c9b2ea1fdfd151`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-native.json` (`sha256:3ed903e2d29af32b8f2714e224df0e49f094f6190463da70d27c133a31df15fe`, normalized `sha256:3ed903e2d29af32b8f2714e224df0e49f094f6190463da70d27c133a31df15fe`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `407e66d6f695aac9feff87233d67dc7836b22bf29c5b6fb969e24ad18b0e05a2` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `435ab10c022a8560afd1798e47d5b1a6e89610b94f8a9c6ab2a12fcac53dd60a` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `bcae98fdf1530e0eb695067e6cce11c7ace9c61c3cc34dd2be43ede6fddf9df5` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `cd98bcda081e33459f93fd33d2f1d1b57404a522e0d117ee13715b64628a28f0` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `c9f3b3aebb80e9ce3adff14e8dd1ffb73b0172a1081062ca33c03c5c7fe50118` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `ebbf7bd80b57a0748747fac7540ddaeb1b0d6890d830c75b95a4e6487941cff0` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `43946693ff47250243dfaab90f75c98368bfb87c1f61b0198444e6b661f215b9` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `fa16ca0673a8886d17cdc09de5390b6e380017f6ec5bafbe3e2876d093a7f431` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `4aee8482123d45a4f3cb5e78888522f0b84093e55d01ac79c5a2d6f97a90ca0a` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `8195ce17f23786d872c7d76bdca43988a978b3bbfe0d7b8c684a3c08f4a35c0e` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `a2e5a77d5cfd02e40d4554e797e43304f7d624c756e72607479bf20be5a86df4` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `388cace9605c6c8062d36750cc00ab1b9b2236311835dbe51f0584da4b776760` |
