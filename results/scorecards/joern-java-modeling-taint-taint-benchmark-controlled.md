# Scorecard `joern-java-modeling-taint-taint-benchmark-controlled`

Adapter `joern-java-modeling`: `joern` `4.0.614` (build `joern-cli:4.0.614`, adapter version `0.1.0`, configuration `55282607023d6902aebe9e2e4199542f04b407229ac0ab04eab9b70dd4a6980f`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-modeling.json` (`sha256:21fb1d444a2db6dd5dbd8c1aba56abd2d728a1aa616f049a417ebc73e3fee7d8`, normalized `sha256:21fb1d444a2db6dd5dbd8c1aba56abd2d728a1aa616f049a417ebc73e3fee7d8`). Generated from freeze manifest `reports/freeze.json` (`sha256:3228af686d09f8666989368483bef375bb28b94025b55e31eaa7a0bdd29506ee`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 10, `inconclusive` 0, `unsupported` 8, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 2 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 2 | 0 | 2 | 0 | 8 | 0 | 0.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 50.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `a142f5806c051d0e1b0af420355d46659a3f9c8239ba1be36b215d51ed1de2a6` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `f848ff38e7c6385975af43ef43e951d4e840e4172411bf8babd7ce1e852bca3f` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `e8b565850fc494ca062830a64b1d1385243b06e2f46fda1939160e0c78f82422` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `ea87f5a3ddbe1115823cd66c9d8d66c537d6036b3d6e3fb1cc221f3416c264ed` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `396448b31c4e50406ce629f370951e015af80e87a5366d988127707b7f8a6889` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `2f4bae6e696f8f261f8e6804f169f63470b32a7524be356f1724d1a69d59480e` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `723c11468d0ef319f815471a4dd52681ab46fae73b35cfcb990824ad67839f9a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `29bf63e6edc980bc1ad2963a0a5538eb8c428a4a39b004a49365327170608a73` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `93a3a20f56515bf87d5eee6c1bc297a1ad04ccfdffb9d30b62346339f3528bc0` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `a428041d4e481e5cc9d73e21b73cc7822c4f412332584f975b5ed2624152f1ff` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `d885e47c79de5beb5a426dc10b2c2b8510134dfc19af5ccd795b41510f83c8d2` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `30f4f03b89d43bc1f3c32d4f7b774316238a9721addad738056a19dd62de48b3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `8d42a4b1bdc7f2a090393dbcfa3db1740397dec7067821f819c2c84264af2a37` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `ef5f9a01766059b6dbcf55cfaed6bfe7177a139f1e597ef20fe5b525f47b3e78` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `03c26a9417b80ebe9fc0fa2e3f3848293798501408c4d3c496a484c085fe64ac` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `6e4259ab6fb02ada895d9030acbc3e2b5c15880acb9a7b0e367e09cf6eec87a7` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `ef61e1008204358dd8f04b02967a59fbf1b501aa93e1e744e24108e82f6489e3` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `cdaa826b4058896c205d9107157c2ceff2ecb6cd614f35da775f10477dd3a96c` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `bdd35a5f8e65b1d95ec7f9230e055b41739156af186418962dbcacf2f3f6163e` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `eb7b9f4d9b0b0dfcc5e4ff35fb69cdcba88c6a3e0eb11312e078384233f1cfad` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `841784505e8332ff90266283aae8c36d42442d8444a90c91e98fd3070822787c` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `9920b8cbed90a3165f8d46e6ccb43bfdd66cb3bdfba31d0bc06ef7809e12e688` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `1f7b2395a504d0f871c869e46e34223e669a86967f051d76b432d493192fdc5d` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `ffd0da0d6ea5f1f8066670bad2679b6c7de295247152ca4b4f06a5afef5d5c15` |
