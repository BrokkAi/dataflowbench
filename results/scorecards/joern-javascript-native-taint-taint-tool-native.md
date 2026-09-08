# Scorecard `joern-javascript-native-taint-taint-tool-native`

Adapter `joern-javascript-native`: `joern` `4.0.621` (build `joern-cli:4.0.621 — 4.0.621 DefaultSemantics only`, adapter version `0.1.0`, configuration `8d7d26eddf19914eb56e53fb55524843b61e6bad772bc00cb053b686c53e60ee`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-native.json` (`sha256:db92d4b76374db9caa17e12876ed2785ea9636ae3d4b5649e4eb38d6b2c5eb86`, normalized `sha256:db92d4b76374db9caa17e12876ed2785ea9636ae3d4b5649e4eb38d6b2c5eb86`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `ea0a21d23bf4f2dc738dd03afcdd20ecba347497320a41f4743f2981101f6683` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `6a49a3971f654e63ff4372bc858de1ce74c0f5a78f9b4f3b7cbf4a6aaea43e13` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `fdad4da185251dffc95c89a3671fcb4de3208149d05caaa453d27a5750f67b09` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `2dc373c8aed60b1388e97c3086f422c873e219535aee9c34e0f23ca33add0273` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `38489b8cacc2b044be3405f73fe4b8c1014d731832846ae002d860e92e2e900e` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `1da7df58542cf16b88d5409b0b483003cb380b0653494aef454a42d26f7c744b` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `21d1d444a93bad0195227c81fbbb5df7f9ebec56eb288bf54c0ad58a9ba6d344` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `dcb178be7ce988a16dc81aad40f08ef96e7e09be8ad061c0dae261688d1cc428` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `c4deeeb19c6199c513e050bec74e9b874cf20242c0d1f95ee62c22b52c29e7d4` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `4781fcc7fcdbb09061221b14a94ece06322e84b8bd54067663db0e335d2f5083` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `0e9183c517b45860fbe267783533a3dea64a50cb87681bbc74fc4137dabc4e71` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `ee5aedf54fb4d7755181d9e930f755390f508b1abc5c1713d77313917cdcc71b` |
