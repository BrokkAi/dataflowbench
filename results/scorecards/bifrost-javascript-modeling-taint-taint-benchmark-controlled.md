# Scorecard `bifrost-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-javascript-modeling`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57`, adapter version `0.1.0`, configuration `af5cc89e2d93f23cfcc552636c8d77a3aaae48f0901c38aa7d1977817a70b9d4`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-modeling.json` (`sha256:751d5ae5412e87dd984de6ee687c3e8a8d3e98374de203eeceacc9987269fbfc`, normalized `sha256:751d5ae5412e87dd984de6ee687c3e8a8d3e98374de203eeceacc9987269fbfc`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 2, `not-reached` 3, `inconclusive` 3, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 1 | 3 | 0 | 0 | n/a | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `eab7b23da3d85372585174820c44750450c79d64a54b4d66f303ca3ce6d03d6a` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `5737534e5bbb0fb137a3653619c7992ceeef42132316a80eab36b2ede461c829` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `b68d65aac58e5b70cc7da7d4fa7216f69a58d1822d25de8ee1f1babec16f3568` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `7cc958fa427f55183d9c0704ae66f6ab50984f708daa1b241cbe54de1230badd` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative-unsupported.json` | `22343025f48fd536c5e99fd42189dfb31c1db8bd018231f10eac41157a0b0193` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive-unsupported.json` | `2508d2e35078e4530245e3fca1b1885662f29bcecbc35f8fabeca665961113d5` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative-unsupported.json` | `a801f4761594cb5b57d74e431383e3c296c5907d3fc0e299d61f90898d3c4768` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive-unsupported.json` | `f9a6180955041af55346db528efd75f0c51c15f3c457e493e764b74e3ad42825` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `b879c789c51c92ac501032dd2bc5223d698d5f46d03876a53ad076f01a7310ed` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `fcc625d376bf9a0bce1de42798e52770b554675f481cdb3955f189694634d0af` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `db6975c8a4c8757bbd72bc2d93c1b5b4b55b1c1c3d0ea124ab16e4495a0c2aa2` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `43b57f0cf5e347b3ed12bd29212c0c5e16693dfa9282d88bb0b411aedefff9b8` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `db1c9d72cb54daa3e628fd5305f566db198ac3ff2b4110ef61342e15b6ee07c7` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `a083d827e31509be802f2fbe9d0a106347bdadedc5e235b0400f71692f560e0f` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `72c725c96934218f2b8b0862fe1f08f02da1dc536d5f335f42307e11f5c972ac` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `8be9d6b71311bd017b8c42340fe15b02a46a4a291877fe3928f71973be1a5e8c` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `ba9992a2827d8e14f91df5444a815e7eac5c0573e8d287cff2718331ac878806` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `b2613c48ba13009345802e7e1384ed5d7c583144a211d9315e74f0e406d02110` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `5f8fa7438f92868118b931f2554826ac73efd87e425d71394357108328e40938` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `fde06cd05db317a2134e053df0c9286d0d302e227647df4c83d303ada81c2b1b` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `15a91c97b9738074ca8d0ade850707b7ae398695e663a941fa4b6f8f0cec7005` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `0eb1374f34dce0a91d95e0788fa119430fb0023605c1224a05c14f78f9e7d40e` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `9d2ea558996ed27e9ed75f8cd9380feea3816ed8aa88c33c16270756a52715b0` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `1921b33f2f47d80ef135200ea8e4a042c8a5b79411b1fae15bdd37e84e32847e` |
