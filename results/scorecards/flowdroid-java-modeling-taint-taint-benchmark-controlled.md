# Scorecard `flowdroid-java-modeling-taint-taint-benchmark-controlled`

Adapter `flowdroid-java-modeling`: `flowdroid` `2.15.1` (build `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218; android-34 platform android.jar sha256:6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad; dexed by D8 8.5.35 (build 2c176ec131a9edb97721fb8578b7fbb462376632 from go/r8bot (luci-r8-custom-ci-archive-0-gths)); r8 jar sha256:4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294`, adapter version `0.1.0`, configuration `1dfd4bebb5426ae7524ceae88e5f7b4588f807a48c83ca66bb24664f45b88377`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/flowdroid-java-modeling.json` (`sha256:27e1eae529406ce4e1819442e0a986e60c3fd48947725a91202d859915b0452f`, normalized `sha256:27e1eae529406ce4e1819442e0a986e60c3fd48947725a91202d859915b0452f`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `c1f5e7783ff1c09c7cba152c136fd549cc887eeb2ffee261b68ac1f2b6617da6` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `60b8e8d6a926c73a1acd38648f787c55c68256c9bca950648a4802145e1cd9d4` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `ae6200486759b6d9384a143f1db3fc859d8b7ad9f4d42c3de2a2971c978d2a56` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `5203bcdf2583f0f178d3cff664abc9c8cda1680cda5e7588939a90480d2fdeef` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `2863ad6eaff0116f18166bf6ca56ff1ca76c024737e0e139a6eddb8cef6eb529` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `92a733deb54a21250babd37a9f7d8b82fcfa3ba604d6345576632981a86d749a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `f44355431f9e136062f29284c8052315f8e13649b823ec9f22aa9447e6af407a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `fafa0aa47432f43a201a67e08f0b6b8896dac6608553caf76f8f2b36e10539d4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `ea31a33e0498cd2dc55d95b0fca94c9e180ac1a9e8459d4df67cf913605f6d07` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `d185645e9800997b7967fcb2319e1e31c4494d97e68085caffed70c82e05ace9` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `3acbda2ec96e6e2dcd1220fb9325f403725fe0435e1b59aaece8fbb5d8154a65` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `47b76fe4c3be63963acbb0cb186ccef53a0c1d5cf797bf6d7652ef1cc5ff8261` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `f0b2cb4b5fa948b3b00757452fb7b4abd59f34e2176f5ac32ffcda78013b4051` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `070ffd39211ea1c9edf0ab4360cc89d5dbcf8c9dae8949aed822db219f9938f1` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative-unsupported.json` | `53296be3130002c2aa4fda21e1c0578bbdb5f91cfa407416e1b833985ab448ed` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive-unsupported.json` | `fd286cb3d7ee0daa3b8b3b9afcc8a347b93bb0022b487f22e0636c5a77b0cbfc` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `0f05b99a0ccc1ad6613a5d0ef432b05dfbb22105e9e686d5b4a18bcab4b3cfef` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `a8d69db556f3dcc01ccc10643d020f077a234354fa64572944bb0cb6777b73c1` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `d34b5ed1be84c5fb667b045b4fb0fdaec3e0f3beb1a05ad28d1fda5dcdffe33e` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `8ffd2bf727db5a970bf8c893083d5aeef389672de98ebebe82a862b9e4686d13` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `3a5a0bf5d3388f0a89ecfe140d19b61b5c69b513ab2300548e03a41fc598a3d2` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `31c513a4477fc1e1278522bfbd5643340f95351f69fee269105e143df94158a2` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `b0389a55eaf2b184f3bc638682da514e2a6c7ed4a0e8e225727b03d176e5b50f` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `63db6f686eb69877dd7c7da3637429218e4e3b148a0c41786929c9ea48e1eecc` |
