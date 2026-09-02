# Scorecard `joern-java-native-taint-taint-tool-native`

Adapter `joern-java-native`: `joern` `4.0.614` (build `joern-cli:4.0.614 — 4.0.614 DefaultSemantics only`, adapter version `0.1.0`, configuration `44be7a7aa2af4289b8665c23929d0ca8aaa046f4b1db3a43f973e31a610ce7fb`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-native.json` (`sha256:a438c1ecdc09f23db4cdb14dea45fc99ba6658af4d9d887c9d7852e5d2ac2aa8`, normalized `sha256:a438c1ecdc09f23db4cdb14dea45fc99ba6658af4d9d887c9d7852e5d2ac2aa8`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `787ecddcaa02d0e7e992ba589cf25d176bce9e8622bb30711144027e5a1f03be` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `c6e6d391a4c909a6ada570f7041104a810c602dff3da76825bb9f0f8c74b1be2` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `b8490d58a963cdd6e88d877d6186b897fe67ed0d824238a150312736f82ebe66` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `2d9d23acbdd17eb9e7f15d42d02608078975d2dc4f6de12db4ae8c76ee4fd5a3` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `8e5c25f8c23f30e1de94bae38340c039be3ab1fb2d4dde755b8dc45986e8dcd4` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `4f63cd10522aae908c754086d122af67014ffe28ac7540603d9a1a4908f6a077` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `437f37a3460f3afe15927cd8ea0c911f3ed622d0f99c73c3b8a715813b2faeb9` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `e5a0b8b867720b9680fb02a20933b5a54de4ebae23271b85986fd6fb48b82360` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `45fce6914c9a0b80c726d82eb3c833cb2f18c4b445ead05820b76f6d114bc75f` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `33d3b602e81c7d0fc072bfca60b0e9be830224c02cf3deab75e3e24419298ecb` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `64bc8ec28cabe5e393e02322afd50dd4b219230c55067070a7ea410565fc18b6` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `d8eb1b3f786e9e0a349becd5fc019439c5dc3a0214d156938bb18247b7d7a405` |
