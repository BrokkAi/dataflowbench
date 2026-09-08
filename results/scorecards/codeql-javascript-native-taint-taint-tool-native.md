# Scorecard `codeql-javascript-native-taint-taint-tool-native`

Adapter `codeql-javascript-native`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65 — 2.26.4 shipped suite codeql/javascript-queries@2.4.4:codeql-suites/javascript-security-extended.qls`, adapter version `0.1.0`, configuration `85e2d0560b288a3793078f45ba642dced845c1faa45b20c12a0acc0e3c6acbef`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-native.json` (`sha256:bdd4c464264951e8c5f89854d8034515af459f117b3e2d6b3af160c94a5e91de`, normalized `sha256:bdd4c464264951e8c5f89854d8034515af459f117b3e2d6b3af160c94a5e91de`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 5, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0.0% | 100.0% |
| `local-flow` | 5 | 1 | 2 | 4 | 0 | 0 | 0 | 83.3% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 70.8%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-negative.sarif.json` | `d9dd7cfe65ecc447b64373da1fd6902845e07b1801cc0d4d1a8dfa3d449ee1c9` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-positive.sarif.json` | `eea2a5f49e6f0fc2153d0a4d207445d23358f15cc8de57964f9dec85e06d6ce1` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-negative.sarif.json` | `9c73daba624108b79be177eadbbb34679768a40228a39bc95a1f5ab872f4096e` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-positive.sarif.json` | `0932dba142f63fe49d1daa1b6aa4e61e9d21a3e6d63893c9ed5747d96551a234` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-negative.sarif.json` | `732a04e44fded979cb08f154b7ed27ee914ba21a15a74a0adfa837db9a5ef839` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-positive.sarif.json` | `031515f173d7d9c42ce37debf24945034c5751480d2772a6709623f3ec69e660` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-negative.sarif.json` | `c1e3858ca258f7522300e68ffb837bb6bb86e80eae5d142f65e3fe2d136b04cf` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-positive.sarif.json` | `c5532e4657b89fb5fc4a62779c9846fdeeb29eb109885e634878f631354260bd` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-negative.sarif.json` | `00f289ab69c61217e028dddbc2c0e0e4dd0f920861d2a1fc09aa7b55ac9cc884` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-positive.sarif.json` | `0b8b91f4ea2f41b6fee2df84f6e5493789909909e8e21cc171dd433846cce4d3` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-negative.sarif.json` | `657397dfcd8c4d4e286ca4057e7348657df972d99ccc7c4121e42adafaa260e7` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-positive.sarif.json` | `b69aa2742654db28508c03423cb986a04a9a360c3eb3f749fbf734f793f63f30` |
