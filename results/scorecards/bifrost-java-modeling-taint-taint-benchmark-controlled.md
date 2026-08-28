# Scorecard `bifrost-java-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-java-modeling`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57`, adapter version `0.1.0`, configuration `f84f51766cf26ce5665df0281d649df8fdb9ec64ab76cde675f790b8c0644ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-modeling.json` (`sha256:2e6e38e4cfd5436598081866e27bbaf98c01da8c50090a513b8f53d71b483eed`, normalized `sha256:2e6e38e4cfd5436598081866e27bbaf98c01da8c50090a513b8f53d71b483eed`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 4, `not-reached` 4, `inconclusive` 0, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `bee4c75be8fc039999596bfe233842259eb213107ce751b6d1cefae109d940ba` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `70f2eecdcaa119218298e5124da256b15b41ac4c3f63ac4f8f25bad691594ad4` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `23652279f97a4718f5b8a74212757d9957612dc879dea2ae6d995b6e84a76d4e` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `dfc39510fb423e3c9571b07e11bc1e6b7a13bdcec0f167ed49254ecd3e12a2c2` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `459023bb8ba0a3a1ee3b6432a509adeadffe647ebbb539da1f13567a470735e5` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `aec7feefd689729ef7fb629a1013ad9f57fe38a1cf8ec50dcdb52947cef85f52` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `cdf6e17caf40db335ad9769cde40691f47a382d63560e31242959f1f36c3f03b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `26f5a614a1866714a69ece480f9f3d93bcc8afac86b3f53823d2866d9cdca784` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `9184e5725723883ae4107b14cdcef29164c4868c95a20baec3de8d6c125d8e50` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `e649e140e9cbdec28c76046fb9ad93c69ad4fc79561a3c80e1c713a3f556094c` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `d5fc07de7181bbf532e64f546be0c40569c271e733f8b937d36caabd63a299a7` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `30b55c389fb8f67f315763a6e7b4962ab83ebbae35622301cd0dc64774c2e406` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `09778809609ca4ca9df1f30fca9040968817730d32a73391b892b50cd1a5958f` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `53476632da3503c4209e67e407f985e5ccc5256775c7e9790f52a667392f118c` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `f59f1ee95cc650a42f02eb5b5e929226b60cec739ef49b5350bad19e1d3788f7` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `babaff35588e25bc063ebd4a3316e92dbb9ff83b265dd7e1f51ffd95942cdb83` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `9bcea792b1fde9687e20d68b1c62c81ddd1f17a41391935ce1acf7cdb313d300` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `8694120f6e7a7e3be3ed9a342c00de9bb17c92628d18fcc336f0568b03cc7746` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `04f8d32627e7f4e6d23447db68c8bf4930db66f56b344390b1b5caaec2393e96` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `0b0d5b5a0466d8461cbf0ceb04ebdbb34731ca129cdb0d208767d4de5cbeaaf9` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `86d9b22a417a0f0883343f443f617d35c28b3fed977157d2874ae4b7f9d2a2dc` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `0d1939c55ad555b15b5dec23911298bee61e4d037ca5684e3e9e70a9433c7148` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `eb4c10bdd701cc1e4d5cf9fd4777db81cb5210d3533edbbdbfe045477bb6d239` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `228dba8c5dd60401bdd4d904e9f442c95e57d2f0a373c54084a8aa0b2c3ec691` |
