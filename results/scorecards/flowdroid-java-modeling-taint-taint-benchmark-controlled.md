# Scorecard `flowdroid-java-modeling-taint-taint-benchmark-controlled`

Adapter `flowdroid-java-modeling`: `flowdroid` `2.15.1` (build `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218; android-34 platform android.jar sha256:6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad; dexed by D8 8.5.35 (build 2c176ec131a9edb97721fb8578b7fbb462376632 from go/r8bot (luci-r8-custom-ci-archive-0-gths)); r8 jar sha256:4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294`, adapter version `0.1.0`, configuration `1dfd4bebb5426ae7524ceae88e5f7b4588f807a48c83ca66bb24664f45b88377`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/flowdroid-java-modeling.json` (`sha256:51dd054808a9b3e5298f3b3c4d8f1946d655ee536af9b85d9257b8bbaf3d319d`, normalized `sha256:51dd054808a9b3e5298f3b3c4d8f1946d655ee536af9b85d9257b8bbaf3d319d`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 7, `inconclusive` 0, `unsupported` 10, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 4 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `412960c412c43905b7bbfcc23e5ed66808498672ff71dda7a0755f426a5a3dba` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `242dff5951750d5c018122a18753af685b1fb3694c73ed0b4d682fa775083f44` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `d91ee8d8ef496a46c1c6884d196b5cfde5aa53b902482918f67084e91b9b2ad0` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `08dbfa3b71148f0f4b0e925bf1a72ae8ab4a7db49947ceb3f91f62fd89f28faa` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `2863ad6eaff0116f18166bf6ca56ff1ca76c024737e0e139a6eddb8cef6eb529` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `92a733deb54a21250babd37a9f7d8b82fcfa3ba604d6345576632981a86d749a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `f44355431f9e136062f29284c8052315f8e13649b823ec9f22aa9447e6af407a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `fafa0aa47432f43a201a67e08f0b6b8896dac6608553caf76f8f2b36e10539d4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `3ca880fbf2f1a98dcc05d62f21da1223716f045691276c0894f224da8e74f110` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `b9ff1d34aa4ac7c1efc46bb70ce938998850d3e06bd4bd99059eb6978e71ec6e` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `644346a5cdc2ca1414a0141ef7555aa2b6bda7d2d1681e1ebe2cf464378b2636` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `8636bf986888240454ca7397ae78118c8bc13ddb4b7a6519376b3fe6080b722a` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `60dec0e3ae9c889af9a0296c31e1cd41a50e08696952ab7cd60dadabff1bc6dd` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `51f38f831925e529b14239a8ffbc60019e855491ec6247e67acda5e767f3cc1b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative-unsupported.json` | `53296be3130002c2aa4fda21e1c0578bbdb5f91cfa407416e1b833985ab448ed` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive-unsupported.json` | `fd286cb3d7ee0daa3b8b3b9afcc8a347b93bb0022b487f22e0636c5a77b0cbfc` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `0f05b99a0ccc1ad6613a5d0ef432b05dfbb22105e9e686d5b4a18bcab4b3cfef` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `a8d69db556f3dcc01ccc10643d020f077a234354fa64572944bb0cb6777b73c1` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `d34b5ed1be84c5fb667b045b4fb0fdaec3e0f3beb1a05ad28d1fda5dcdffe33e` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `8ffd2bf727db5a970bf8c893083d5aeef389672de98ebebe82a862b9e4686d13` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `ab8baacf9a8d7da7853a6678a613779f19b552268bc68293a6dc99bbb12cb7d5` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `0befaf77548ab5e31c40babeb2ae8f91e2124e85fa7b6cca7338535da28b08a6` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `103efa54016fd863e8d0f289dfe2d729ff96f58b0db19d651a9ab2eb8408ba25` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `3469d14d933c0d293bd83c3a5e307ad7a090b0b8e248c0cc431ba3a3a639f505` |
