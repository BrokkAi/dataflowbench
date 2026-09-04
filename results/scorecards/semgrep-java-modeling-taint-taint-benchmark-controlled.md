# Scorecard `semgrep-java-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-java-modeling`: `semgrep` `1.175.0` (build `semgrep-oss:1.175.0`, adapter version `0.1.0`, configuration `d25d4a4058ae7bd67131d38d05d0579a642ad1841071f965719dd8cea7efd59e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-modeling.json` (`sha256:94a5eda43ab2aab5ab47b44e80907ab18dd4796a2f2a364bbac621d45cd19c63`, normalized `sha256:94a5eda43ab2aab5ab47b44e80907ab18dd4796a2f2a364bbac621d45cd19c63`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `361ae43f191c4004478f6fbb3cc5aca6fbae99ce9c067cf1f099a3b4f6966963` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `9254d00c0148d443adf8eb28af7617df2683db12dd56092fcaa38c48e69c0fa4` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `61a8c84284c0833a25c71025647e9d87ec95a740996363f833385f7d9963a4f1` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `32d22ed7e3becccf1017dfbafe29b2183521470d9c8c82bd2ec3b925883c62c8` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `1d5256fcf9a56d9cbb1f28e1006ab20c71da2d361a08d11b22c610a135dcdddd` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `ddb30e664f99a3588d40d7e878b8b883922404c283047f333d1536e761c9a5eb` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `b960398da4b6f072af55aa8e08a3f63d890172cda2680d4bf7c5b0330b421008` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `595449108c1fb78125f9cf9c4279efc38429ff85d73ec2ed843b3196a2e582e3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `78745b0b29689bd9aec7aba4e25f3bb051aff478893aae4196bbca959d069a8a` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `b24c414022d5c3cea993f3c74c024667aed8a628f3dbb56a7cbe46e17fbac9e5` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `42a9eaf939b638f1cea1e6b3a813daacb05c3858b5c6120a53f573e6c68926c4` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `f3c5e6cf5a8429fc079a277cf31219441a68d3ffb101796f16ba53c8590d8488` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `797b1820e28608ca3d71d9e36d262ce8b4ca586d5026cbac108674b18c51bdb3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `f29815ada013893e83a9f8abdedbc9b8c514c47175f1c38d4defd6bd8e5ef469` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative-unsupported.json` | `176291e6e6644dbc56714ec7290ff7a67812adafb1bfddd9d45d869788fff7ef` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive-unsupported.json` | `49a3789f73f18d6a11ab72c0a37e78a381e8e3f32a8a0b85d11651030caeac7d` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `f5149dc8096aa33b70d692bf7076faa28aa7a1e4854ccd615739793bb0b45c67` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `7e21498750c5c34d401f6e2d57ee855e1c68d72e160f4b09b926bab43044748c` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `d3ff01bfdd7f8fad30aeb9aaf6c9f6c8b3fcd8a362be7e222a2ca6909e9f235d` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `b80257bc42aeed2bd6f357b8d9f43b6affcdd7651b49aaebfa680cd890f515eb` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `3f9c795896ed5fdbeca2ce59b12b7beba99bde43d2e22beca42ba3be67c047fe` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `4a060cf9341e25ac83ab316b40d174f5cfff4abab432c41aa9cd80be70f378b3` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `c3173a9b05c51fb3d306ff884e7aaa922ccdc28c3ffc9c2646179cd9fa5f9697` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `417a0a8df8bde3f8376e99c8b7146994e5e6fc1d910e7b713cf7145c278b0efa` |
