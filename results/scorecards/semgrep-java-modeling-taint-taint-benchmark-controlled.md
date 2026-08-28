# Scorecard `semgrep-java-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-java-modeling`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0`, adapter version `0.1.0`, configuration `d25d4a4058ae7bd67131d38d05d0579a642ad1841071f965719dd8cea7efd59e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-modeling.json` (`sha256:8af4d45c830f0f68e15474eb5f67b599e825c0e94b748cea6debb66d8d42c2c2`, normalized `sha256:8af4d45c830f0f68e15474eb5f67b599e825c0e94b748cea6debb66d8d42c2c2`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 0, `unsupported` 14, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `80cd47cfb011f8232aa168636370720cd9c6983668c3cb073dd04bfbc4ab5329` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `63b206105ecaf610a57784e3f3f831b97f304a083a1268b51686a553a38d0958` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `7ae1e22fb6960d877e2a60885b7f223b586a21185d01d6935ad6e01f74ae9281` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `287d8b03e43d3f0d36c79d98405bbd9d56efae22778da7bffa4b4e3b5f7dfae7` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `b782ae65c73ca9a39cafa4518df84bd50a48c27b1639517b12df5e04eb47637e` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `f16d3c4dfd8531db8bc2c87e4362f9d0c3e8c7c16eef8fff9a737166a44ff6df` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `aa8c37f19a4a26fe508ce36406e5e56df1b136f3569f72d6d243aaf6b2bbf678` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `a4091e16c21820f8182f24b0032a8688e9c2a35e582800c7fef4c1b41de638e7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `c3e639ed9ef65437766f7e815fcb1696fd87f172ac5b56339fd66958d0f728c0` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `654744a3b50101a7f3b8fe522c66acc386f1e6d3fa04a8326d9f78aee0d86cfc` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `341d65f96e2c8a37d8ac917e1c1673e5069cf865b607f4dedecc6392ce2c780d` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `3c7de2657b63ff84980f972781b4333301c55a0cf28e4f5322c403956eceec5f` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `9385f4c65326370d42ee8263a32f121b75ef4262753ab5f4f9385a9434739a71` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `3d838c0951b0ba30a1f3af5ad2911c39f6f2abe3b1479ca1b03e262072b266be` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative-unsupported.json` | `9cb899a3f5ac82e08af9896e503f019e5369445d5e0980af4d3c473a9f9015a7` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive-unsupported.json` | `61a5cf86a323977c7bed4160557daa8343df86766b5d0b8b4d3c18087bd3ada2` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `eafffdc47e35d903eaa2a52640603fd205c20420b712faa30dc1542a103eb3e1` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `2267af32eb29ee1b3f1c9971d8a003cd96063267adaabae096e7db2cc584c6e6` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `9ceaf6c7d8eaab490f9eae466cd5ea64efd70f9a4e77088ff2b977f170028f1d` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `acb784f79d74f5fec8779db2c0fe4a5333c9733b24699aa000eac647f88e53a3` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `3b8ee6d5948ec4c0a5d945a6ec02729e9ca90157f787dfe97291f727446ed28a` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `324fe11e1b7d94d6307837b2a3a46a5764cc5656eb18a58389cf1ec47f01f003` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `7c303421fd925e324494cc13341c9b879bd40511eda027ae4f248f7ec4fe73bf` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `1a8e94c4d6c4a7dad5a45efce9cd511d71f8d9d35d21285ed1975f8e0d3ee54c` |
