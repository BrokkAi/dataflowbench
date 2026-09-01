# Scorecard `bifrost-python-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-python-modeling`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57`, adapter version `0.1.0`, configuration `7c35450fc275271a167e8e257eae83e8a58ed870bc92015cde34e4f64cb8b500`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-modeling.json` (`sha256:7c60420cf77a827a448f41977b4d083e492e6a9fd9809d186774f54adf5d13e9`, normalized `sha256:7c60420cf77a827a448f41977b4d083e492e6a9fd9809d186774f54adf5d13e9`). Generated from freeze manifest `reports/freeze.json` (`sha256:3228af686d09f8666989368483bef375bb28b94025b55e31eaa7a0bdd29506ee`).

## Language `python`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `e8fdd2b0059870a5c367368c0881bb24b0ebcd1659fece00b051656a502245f3` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `e46fca1e7a90ca4b3344f1e02b681497699811a1b60ce8cb5b455a4fe720e83c` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `30056d77d3710e06c96a953b0f6c516869d2c495d32c34658d02d49a5e208f2b` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `d61cfac1fbb3ad857827e65ec41aaa778e56641ae42b9d3b0bf52eaa11813ad1` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative-unsupported.json` | `b6d079e512ac1dd5b84e0f68e38925700cd341c5568536f535972b894703930a` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive-unsupported.json` | `2a56a0ee6855967dfd7d5c51429222a6114deef4f3b7c935b2cfbf4fabc24d11` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative-unsupported.json` | `0831dea64e76802db0fbb307b6faad93bb97d8aa5bca6cc508874979153699b8` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive-unsupported.json` | `c9e79890b9d062e05a29b639078f9d9cfe69e33b7f791979335dbbc9df740be6` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `07900ae6102e8828be4428a5ae90d927acb64bee23d75848c1922196327ac3ce` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `413c051dc17fed3a1f329e80a791dad7d7d976cf497a06898000471e8c2cb001` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `360fc0d07b9a03124ab920146a1f51da018663cce2451e685824c2dcf69dc012` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `c05dd21368c9506ce07be44faba80e53a049604ffa85413490f6c5dd697f7894` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `1fa3aad9fe3c8cf72db6cc6ba94ef42da7c2f36c5dc733f782fa8c744a51b777` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `ba27dd562ac96b9278d93a2e8dc3ce217e18be7a50784c184b89107af9b1cc4b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `a9353d13559364dac393d2cacc671a8b3451e5dfc6a6194b2dd6e9529770fabf` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `aa71df15681772bbb1b3e07c23423816854940246e1d7992a132e6cf02beec1e` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `4f0291996640c343013770b702376ac984ced2d7a94a8fc97ff5d15998f7ad2e` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `1f366f201b9d0b5811e3d165f0a8d9db6c9ba182dfb37475915c07043b2d7b22` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `4ae385a03e73db19c75f6188f49735113821191d808d041942e351240240d1ec` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `930c22cc2eee65d0e36729a415c21a4cab11147137ad00b324ca1f7117438b12` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `43c5d627c675def6dcc41386778a67baae8786adce909a272307ef7d00fe995f` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `e0e40caf71c070b75923258eb9645998fdf71aa2c7d34874b56306a2e4bfbbba` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `47da0a0ec5ffcd5108fc71211d020ae838fd0ee2c383fb1043f92b1e3457b281` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `eeb58ee062237f9c76ae3d2897e7155dac6dcec46689da4382d214ef8689706f` |
