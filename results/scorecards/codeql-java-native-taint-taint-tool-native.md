# Scorecard `codeql-java-native-taint-taint-tool-native`

Adapter `codeql-java-native`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7 — 2.26.3 shipped suite codeql/java-queries@1.11.9:codeql-suites/java-security-extended.qls`, adapter version `0.1.0`, configuration `459f201cc84ca267057c7e106dd9cdfd97eaefdfaa45d32dc4403b09fa56245c`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-native.json` (`sha256:16e2ca2ea4e7dcef4e5f4f444a33767e44c78e2ffa051e1749f3de9222037459`, normalized `sha256:16e2ca2ea4e7dcef4e5f4f444a33767e44c78e2ffa051e1749f3de9222037459`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 5, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 1 | 5 | 0 | 0 | 0 | 100.0% | 16.7% |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 29.2%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-negative.sarif.json` | `5f0b81b89035cc9c1832c3bf87a29ca99058eb63339ae96bf51dc04903ff1b63` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-positive.sarif.json` | `7200e38cedd9786d5eae3624589d56e2f80687b4b5d17e62e32f7460d8078798` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-negative.sarif.json` | `edc71dc59c22d91b0b75997455a7f0df9c4aec22956b8d2b1d9c4fc2f2c5245b` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-positive.sarif.json` | `1d75ce9ffc5cf7b88d2f6c7791e3603fa2b3b908cd5900d5ae7b060ea961c571` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-negative.sarif.json` | `9ed79a509f5f8282b6f89b4dbdb1d4587624ffdab6fe7057979ca7ec13050a66` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-positive.sarif.json` | `66f10a23b6992368ca44992d10fb6843b132b6ed5d28f21e2747c72b126d2ff3` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-negative.sarif.json` | `d3186eb42c7f2b73b8f3872fd0c51fcf4805cab3f0d9ba277f12672e736fc586` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-positive.sarif.json` | `244d7f30f182dc6e0cf9d6b511273bef34184933673907992f7d74831f8597e9` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-negative.sarif.json` | `50ba9a4612e7c9abf6051abfba3f244c9d7dba4698f63bb33e1b46226538c6ff` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-positive.sarif.json` | `a2ae3abf82036dd02b27d1d304964ee2bf873e5053b2ab0fd1ff6f8169af56af` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-negative.sarif.json` | `ea287d0a20255de84e9ad0380d76ce63c2994b27721a1bf4261920bf63e5bbe6` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-positive.sarif.json` | `6d87c5377d49df4340063db03aebf83795ac96528a32679927e1bcc71bfa9fa7` |
