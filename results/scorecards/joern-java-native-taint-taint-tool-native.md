# Scorecard `joern-java-native-taint-taint-tool-native`

Adapter `joern-java-native`: `joern` `4.0.610` (build `joern-cli:4.0.610 — 4.0.610 DefaultSemantics only`, adapter version `0.1.0`, configuration `21936f4b5fe760f2f4ba8ffc27c440c664cb7df00ef48374d47c74e7b2497e25`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-native.json` (`sha256:a2bd1c79179c5dd6a70797eb7e879581ce392131cf018daf0ec36d888da3a4d3`, normalized `sha256:a2bd1c79179c5dd6a70797eb7e879581ce392131cf018daf0ec36d888da3a4d3`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `e67c659aebc0e50f0258f79fc3f18b3a8014d2535399ddb56b852aec2ed73899` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `6a97d9121bc5a5593efcaee3eedd7a1a18c801b8990ab67ec728261b549c7d30` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `c69ddf4563749f66a0ea44a7f3bc6fc3c8563202267b845d07770818d5bb1074` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `d9645284537c6718d43f1531ffb660872327117cc5eb17fd86b0414569ed8bb0` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `0df26fadcaa0b4e19af3477481fbe4d8b8a15895deb06155be42de65e5285520` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `52e3897b598e6b1961f4db08f8c4d9a33cfd8ee018423e557b7ff65c0f6be446` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `e8082516195178e75f6d2f808f929e4d2ad0f4201b599c57a5cead225d50a3f0` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `526f2145ed6be3a9d91f33b87f7943fcc53cc1b7fe5bfa0dd3edbe3a075f6bc6` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `4fcd0808247859d13702db028f3cdc5e4127cef0d6b60f07f868bc8d0ff7a553` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `17853ebadbe4d499d2f20f2ea4f2ee6b6d5aa56f5af537aee5e29507ed45cca3` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `7c40d5969b8ce7fc7294f0afc8e4d4f40c2fcd920b18be93c9297439ea70873b` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `2dfe7e03f5889b91d25648a545396e7efd5082e339809f9ab610cc9b66c4978a` |
