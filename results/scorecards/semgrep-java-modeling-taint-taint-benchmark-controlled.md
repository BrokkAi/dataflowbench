# Scorecard `semgrep-java-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-java-modeling`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0`, adapter version `0.1.0`, configuration `d25d4a4058ae7bd67131d38d05d0579a642ad1841071f965719dd8cea7efd59e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-modeling.json` (`sha256:7cb186748186a9a97d23945f777782fc167d55b13184b44e8c880fb10ca0d62d`, normalized `sha256:7cb186748186a9a97d23945f777782fc167d55b13184b44e8c880fb10ca0d62d`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `ea8ae3acb0e591100ace611ee1c148cf660342763c9727473746dbb2a6df6be1` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `78ba8c28adf246b1d15c74672ed50f8a05948135bac30b54e226c6c7f5e00f3e` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `d34fbb66d7d1c9a2a46ea46f77bb091a1c8d027ae306cb9b3f10d1847dd401f3` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `d15b13d329bb90a283f553e5edb248fecdf823f1ccc42111262146135ae3df2c` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `aedf0dab302430dad33ea3b163a9a6264117c1d608d76340fad481f7752e5433` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `7ab6642ad67f91544b034b89cf943be70394629173fbf156138d499a578196c7` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `10c56c63198cfd21cc6bbbe24f0e0b62aa2cb6ac501e68ee8e46118c559148f4` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `9c22264383201891551131cae27eccb49eb1ed3110c79857632fd705ba098663` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `794f66c7b6b69a1d4cc21a9eb0cd4f6ecd64a781304fe448571e2d1e1ce87149` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `06a0f6fa913c76875151f27dac461cb53f135592b0b294f54c25dfd4279418b0` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `18d3a3665a2b0f86236d858d6e89a1c34d06fa10aefb5ca94acadf1fcfcc797b` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `c14b4bf7df3016e6a3201ecc94ba447f34d4023e5d6e0bbc823f494f92079753` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `195796a031cdcf22de9b807bb502a2c85a94fb19eb3a9b7a58dd3dacd956e875` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `bc741404868c37457a30fae5f327d50758bd9e67b4e269ceab7805264c7b006b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative-unsupported.json` | `1c1874d30871d4ed15c46ab40507997df73deb1ab1a60f150dd25eb2bab60b9d` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive-unsupported.json` | `fe87a10a6b3317334645fdd6c2b404c8e1ba51535681cd2fb4320b06183425cc` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `4acd51dab82e2c048a363c159eb40c56116d8f0111cdf7835cccce468618b054` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `bc07cb01322fbd825c924c23ce3ec6b6ec4ea671b403bcc73c0d7087f9350b13` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `6de209e6b15f7ca655875213f367946b205f58be4aa7bf2835d8877a5de2ab9f` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `d53369bb5e647ff3ebc107aeb1c2cd90131e219e158a13207b2ff7f6c67816c4` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `1991d1a3a03e4e8d025c72be30329f802dcf4da588277dbc32644ba4381a3e1f` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `e53e211b1e0f80c6689ec5d4c1b11e2c51b308d17f9dfb72377b6683c2a2e467` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `13d9220f0cd51972a11e5d56404b129e06370128c9012fdbe312f33458c72bab` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `29be3c6551b7a2fe7767a03521601403125ee673b0085c3a09053609ee6c3d79` |
