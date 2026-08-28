# Scorecard `codeql-java-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-java-modeling`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `38acb5de67ed39a244c7eb8a9db755ddbcf197488051a5f1ec0d35b65fa30aee`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-modeling.json` (`sha256:c76aac2e4bf8ab05c0fa9068903c5eafb4b7407bf991031fac5e05662f992cbd`, normalized `sha256:c76aac2e4bf8ab05c0fa9068903c5eafb4b7407bf991031fac5e05662f992cbd`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 12, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-negative.sarif.json` | `a7307bf21e24ce36af266f1eaac2d6eb1175a87696c9bbbcb8e13ae06f090154` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-positive.sarif.json` | `35bc619b4a0ffdad9bed4f4aadd42072f60f4f5a575e4f2f8bdf329fa5b2f894` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-negative.sarif.json` | `9d80008b0b1534174630fb52b2ebaf89c36c30d9e39a7239ffe1292381af17af` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-positive.sarif.json` | `a164144bdc09b6dde6c115829d8720cbde1436ba4e56b2cda9439256ce9ae74d` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.sarif.json` | `30fb32ccb75a24940bb1b823871e573eba6bfcf49910acdddaffb793f6eadcc2` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.sarif.json` | `e43de8f1aca858ac42b758b96d648e04de7c6f7f35c977c6c069f77ef2be27e6` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.sarif.json` | `c9d1f41b1112aaac2d6d3fa171d2779c3a389096cb7bc75eef2c2623fc668f6e` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.sarif.json` | `a744d2bb2b0b90adc0eb5667d0c0462b08230f4fb85e31347a126746d555152c` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-negative.sarif.json` | `93163d73becb6d98812bf4001c2b33808c985a4d3ae1d331a3ebfca436ba1777` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-positive.sarif.json` | `602c56cec1f0a6df3b5c1bb14216a58cf614e5ba75ce0042a2747f44cb73ee6c` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-negative.sarif.json` | `319b4b15b82a1626a00f364171f9b567a3fe5746bf29b4b07333f59ee2738668` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-positive.sarif.json` | `a26b43f6ce83eb994a18769aac956ef1b3a4e4b7c502a14caa26dd34fd0eafed` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.sarif.json` | `857a7cb69177b47bb579ec5bc9c691a13753a68eb568f7807114319a95de82c7` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.sarif.json` | `1199b6f0629d9bb18b4797a92acbb42994d1e1f2ce76b72e922ea592daa26c6e` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.sarif.json` | `e1e9e0a625e7de5ad5245b49cca72d813b6dcb0d9d3a6bf2d5fc57c1b9abcb28` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.sarif.json` | `f472aed42a8aa6c62ad2959f94c749149aafa0d9ea6d8d4a22b111b0ee5972df` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-negative.sarif.json` | `5a9dc3ee6c5bec03a9fe83c4a17d102f474a41704ae44d31681f6089a2dddd42` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-positive.sarif.json` | `497cc8451a8d5c248484e211ee53c8b5630c73e187be1ed445a48fd2126ce0ae` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-negative.sarif.json` | `5ecbf1d21b7901759420f63a18e12d1280bc568a6b9d107a49d5405b6a6a5a0c` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-positive.sarif.json` | `5774d27c77e7d01ec8d2d5b8253b5c5f996e30d33005ce5897316371f2f065b1` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-negative.sarif.json` | `164787921c603150e1cdd151a88212686c11fc6d4f3ca4bb019fed93e8a4c66f` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-positive.sarif.json` | `0862a6417c5aac28c7b3db0c159b275d7c2d1c6b1e0ac22d6751fea69b60ae08` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-negative.sarif.json` | `18ea14d2409f480a2c3fcce8d06cd6e9dcb4c27e2d7201cb52e393d37f7ae049` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-positive.sarif.json` | `5a00fa8d0b7a3d93d5988e77ac7e8299f2993a1f155bb420093e42b9ab3c84bb` |
