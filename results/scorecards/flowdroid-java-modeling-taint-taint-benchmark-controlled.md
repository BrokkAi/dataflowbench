# Scorecard `flowdroid-java-modeling-taint-taint-benchmark-controlled`

Adapter `flowdroid-java-modeling`: `flowdroid` `2.15.1` (build `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218; android-34 platform android.jar sha256:6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad; dexed by D8 8.5.35 (build 2c176ec131a9edb97721fb8578b7fbb462376632 from go/r8bot (luci-r8-custom-ci-archive-0-gths)); r8 jar sha256:4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294`, adapter version `0.1.0`, configuration `1dfd4bebb5426ae7524ceae88e5f7b4588f807a48c83ca66bb24664f45b88377`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/flowdroid-java-modeling.json` (`sha256:b54c7a9827d2a8b45bd3952e42fd516ca2e7a9011d932aa240232d43d6100b83`, normalized `sha256:b54c7a9827d2a8b45bd3952e42fd516ca2e7a9011d932aa240232d43d6100b83`). Generated from freeze manifest `reports/freeze.json` (`sha256:c543ae4ebd11ed6f3495f4461b5b4bd7c84d0874997f1b62044e9df62817b28b`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `2fddd81a1aa2467cbf3d83d509f93dcb59de4ed16420f8e324c5c34e1897e194` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `3d6cdaa090120b64391c2ccedbc949eeea02db02ba696cb376d590463e62ff2a` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `3e8e911350044d4252e82566528961a4b0109d96dd6af2f4c94de3dac99f0d89` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `2701910c758b1aebade5b599a389460574fd04f3ce382cf0059bc0b8b4d45ff8` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `2863ad6eaff0116f18166bf6ca56ff1ca76c024737e0e139a6eddb8cef6eb529` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `92a733deb54a21250babd37a9f7d8b82fcfa3ba604d6345576632981a86d749a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `f44355431f9e136062f29284c8052315f8e13649b823ec9f22aa9447e6af407a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `fafa0aa47432f43a201a67e08f0b6b8896dac6608553caf76f8f2b36e10539d4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `ab5b007b2722cbd4a35473fb94dff41889aafe5efd74a859dcd1b5d8b12b4a99` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `afa80678d3b138090e8cdbd5de3e847f7c9cb05e02d07f8b1a2d2355f2010116` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `1b4894b881339873bc084f6dc0b656c3e268227aba729699e23c0f04e58c0f62` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `792cf1ec8c91ba9823b289f21e21e1286aa3d2bd580a0323027561cc2243babb` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `fe6b51a889982bbf2ad01216272ad25b072f409d2fd71280728e9c1c516bf512` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `daa0eb3875294b8ba5258e60968ca08f8cedb4b105e8d16546b287ffcea4737b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative-unsupported.json` | `53296be3130002c2aa4fda21e1c0578bbdb5f91cfa407416e1b833985ab448ed` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive-unsupported.json` | `fd286cb3d7ee0daa3b8b3b9afcc8a347b93bb0022b487f22e0636c5a77b0cbfc` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `0f05b99a0ccc1ad6613a5d0ef432b05dfbb22105e9e686d5b4a18bcab4b3cfef` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `a8d69db556f3dcc01ccc10643d020f077a234354fa64572944bb0cb6777b73c1` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `d34b5ed1be84c5fb667b045b4fb0fdaec3e0f3beb1a05ad28d1fda5dcdffe33e` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `8ffd2bf727db5a970bf8c893083d5aeef389672de98ebebe82a862b9e4686d13` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `90214605d2da36e10d734522ec5995e06880920abaf2b1f5c5f839354a2b3c8a` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `7d76d5f07e9bcf5890fe40d4244cb70dd265af36d3675a28de4bc1b56adda133` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `aec04c3320daae38526e2230aa7a9d0478e1199958679a74a8d672fd5132ab24` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `8398b02b50f9ca3c275c5ec5ab66968fe9d8103467a860123f9c7c5b1173a1e4` |
