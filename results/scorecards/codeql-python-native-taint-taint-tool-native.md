# Scorecard `codeql-python-native-taint-taint-tool-native`

Adapter `codeql-python-native`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7 — 2.26.3 shipped suite codeql/python-queries@1.8.9:codeql-suites/python-security-extended.qls`, adapter version `0.1.0`, configuration `6b86a8295a374ef35d81c9b0411da6f3c1daec240845b5e3da395899837a3e4e`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-native.json` (`sha256:21a2e4136756bb640d0f68ba6850d8315230df3f7a6622d538d858f83116ece3`, normalized `sha256:21a2e4136756bb640d0f68ba6850d8315230df3f7a6622d538d858f83116ece3`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 8, `not-reached` 4, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 2 | 4 | 0 | 0 | 0 | 100.0% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-negative.sarif.json` | `57046791472ec05be562e2df42047e4cef978551ba4263aef1ae5d4b9da23ac9` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-positive.sarif.json` | `a4f8415a48f77f34bb46ba344a0da09008589b9ccf1a0585c9cc3ee92108aac9` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-negative.sarif.json` | `fe1c3d03f610a1f465585d4b329191d33d72c5acbcb629d8c3e2b86b43af983c` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-positive.sarif.json` | `795238c0d6abae5c3f98753cd06a1cf40c3df712ab2167e04c0077d419137d8f` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-negative.sarif.json` | `63e4508c9bcf2761779729a3a31d4a223bda3e11b0a8be1ec8f4e0948fb95784` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-positive.sarif.json` | `7687a27a33b2a90dc7dde220eb5b723446ac966174d8a073b7ef35856fd8ef71` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-negative.sarif.json` | `49db4a221a55137d1c3d658ca4c5bb7aa8cf567783468fa6536d107bd588922a` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-positive.sarif.json` | `1896e54668774a523913bdcd17210866e802092b8c2f4192fcd3c6dea116c107` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-negative.sarif.json` | `41124d19f079c12eecd65b7985702d26130637617f7d70417e5d7789c31c5023` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-positive.sarif.json` | `10dd863f72793e54992918d6699604334c5e483ff7152fb8560f03c89763fc57` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-negative.sarif.json` | `4ef74efb07b4fcc54af26ad345e1bf3406fe2d948981905e8fe802678c11479c` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-positive.sarif.json` | `32689bd1a34dc38ae14fbd6bd79127b003d49843ec5f74b73c22e02fcce9bf06` |
