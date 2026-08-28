# Scorecard `codeql-javascript-native-taint-taint-tool-native`

Adapter `codeql-javascript-native`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7 — 2.26.3 shipped suite codeql/javascript-queries@2.4.4:codeql-suites/javascript-security-extended.qls`, adapter version `0.1.0`, configuration `eaa9f34789782b46a2a72057bcac81ef226f25dee827d4343d7016b6539c0190`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-native.json` (`sha256:a9889691d7da7837e6edbc23b894492fe237a5dcd62d4bdd73b5b598eb4a2d9e`, normalized `sha256:a9889691d7da7837e6edbc23b894492fe237a5dcd62d4bdd73b5b598eb4a2d9e`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-negative.sarif.json` | `2634b336dc62a6b2ecefc90817eec2b9703a0bd81feb717bd30f1d9fa3b29619` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-positive.sarif.json` | `2f0d8f61ca97113e0b4338c2368762663aab1021495c963d700e954d7aa3d9a8` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-negative.sarif.json` | `912d12ac3603b6347ae8ef9b36ca692bcb033a216d20a8219d865f0ac60efa5e` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-positive.sarif.json` | `2f8c50a843a2887b639f7d61f94a0580268766aba5013c5d8e6cf7097a58ba4e` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-negative.sarif.json` | `b631b5160199ccaf63b97d24d56669e0df7646698a6dddfd8ffd584064cca5ae` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-positive.sarif.json` | `265df01fa27b11b03974db6cbe60ef4ef1b545a7ac79eff6e63a6b019edae87c` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-negative.sarif.json` | `6cc8cc63e4a85ac9c00f77b31ca8a6211fb7f21aec4a2cebb6e0d0aade8b0470` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-positive.sarif.json` | `0443cc93663c32a5a15d715a705f404ecb3043623360edb920b48e8f1ac28dec` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-negative.sarif.json` | `51688043eb65ddcd9789d91e05df87ae6eb35161e5f10f716cf6549dd70e409f` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-positive.sarif.json` | `ae8e1d610b3c2090bb29c4d1dbf62b7b75bb637b1811e4983136f2b9c9a87e73` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-negative.sarif.json` | `dc0c16abcf177949ca84eb4bd6fdf0e5ef5b746fa344a993aaaf57acb03c1e06` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-positive.sarif.json` | `fa1b6acfad71707506c6ff9eb6afe4bf0af2371617bf1cec59020a0b133a2064` |
