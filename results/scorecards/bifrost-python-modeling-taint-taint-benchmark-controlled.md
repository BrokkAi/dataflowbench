# Scorecard `bifrost-python-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-python-modeling`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f`, adapter version `0.1.0`, configuration `7c35450fc275271a167e8e257eae83e8a58ed870bc92015cde34e4f64cb8b500`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-modeling.json` (`sha256:7a1152378263ec008943b4fa23d289127d30de56bd88d52969e8e7cbdcdf9d93`, normalized `sha256:7a1152378263ec008943b4fa23d289127d30de56bd88d52969e8e7cbdcdf9d93`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 4, `not-reached` 3, `inconclusive` 1, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `fb02e8c1ae959b443170e5ca65a3fa6bead9f67d499defd9dacca8f333ec43f6` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `44d328f38f1c82b5bbb252937797883d37c0814657d53780f43b86d4a8deff0f` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `8b627b3db1b8d8e01c15960c4364e91e1ece2af49fc415fd16fbe216f1c452f9` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `d9f08186591e9e7e803084a39a27b64bb42651013e29390244acf5c5f0c0e472` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative-unsupported.json` | `ed648492d87bc1184e00b67b4faa6cc6b8a66ea33a4342a42b5b844b6dfba9c7` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive-unsupported.json` | `9f0b28bad1b6ed4f1fa63f9ec4f9b39b6cc31b83664d183462b06301bbfa89fc` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative-unsupported.json` | `9b10cb73fcf9ca6fbd80551916959dbf661c6e92abb838f0d3f7199d1c084d69` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive-unsupported.json` | `7defdac8c37f3ffc4437c11a31537886fca56e98a83892144269d690e4ae2e53` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `413d331d50fb5f808fd30584cb5e72c6a48910645ad8e10638ed77e9a8dcdde6` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `8b13db756733f126a6320108088d154206455ba84d4586dd9a471a36484ce242` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `101f5c6978e757e2a5370d6a0b16fcbfea60291f16b12a7949f789a44331b323` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `0a196e7a98856f9e82c81c8c24cd3c58611539cf4a114869a28b8ac31e7a959f` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `f6e88a0fc6ae21f563f7e10613b62aa0aeb4e04d079135ba9f06538f2fae6189` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `6ab5204eb8696d187f4d020c96919fbe5326618b082e7b5edb77300d9a7e618a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `76564a73da2f632c87f8be5fc904f9662b5db3f355effa81ac69de532c0ef8cc` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `64f27f3d658758d6c91b423b5c729a1cee0c0e5cdcef292c3f424c1f317fd983` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `e4c2fdb44dbe8b2da6563cd627c017f079ac495221467bc7d699b1e39f69a334` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `e7d397af9057f4230f464ffb09f78e1bf4490bfd4b69a9e27c4112e611131f48` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `065999477049c524ff1d838cdd7b94e9932355cff2c75a8ec80aba5674b047ef` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `428743eb0680497b972b30e5986ee9614dd88375f7fea0122313b0d284240d2e` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `e6fa9bc6985d148d083208280be91e823422f39cba66b732f9b6dcde373cd870` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `33ace5be2932d1f5207ed2f4fd73db95f1e76fb8bc2b01c1bce7bc6bf3d9a64c` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `bdc097819ce8b95eaaebbbe48c2a5f133b0a6193669a3d5fc10cf99b54398240` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `6e58c2714b4f9819595c6867f393d210d1d99021c3158f55ad094ed3cdbd34ae` |
