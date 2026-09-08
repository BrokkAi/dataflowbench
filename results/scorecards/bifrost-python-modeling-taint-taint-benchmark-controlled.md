# Scorecard `bifrost-python-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-python-modeling`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `7c35450fc275271a167e8e257eae83e8a58ed870bc92015cde34e4f64cb8b500`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-modeling.json` (`sha256:258e3bfb9823b971e3038f8a3af1cea7abf6d8ec673b9ab7d7c7022d55dbb6dc`, normalized `sha256:258e3bfb9823b971e3038f8a3af1cea7abf6d8ec673b9ab7d7c7022d55dbb6dc`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `39997a13ae7518f2243a53807498ec3262d141159c3793ecd69a1c18c68b775f` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `617fb6cfb3b47aca7a50c1adb2e4bc4330747b1d3defca901711ba693f4de673` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `514089b385debfd3adc349ad3d303d782971d7a40df88a041f5b42d1455f74fb` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `64dc479f563e470a8d882387b831252ffe44f69c2759b357c38e0f5a3fd53511` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative-unsupported.json` | `4599b00a0e8f139edba0fe5f61abfd610782747d7e303db73cb42d71885adafb` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive-unsupported.json` | `4c74d29cc69a18187b227872db377b658edb602e2fded255fa08f8a6f8e8a248` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative-unsupported.json` | `412b4b6e58f3fe0db0879db3970151610c7b7e00cae84be5903e50d83ac58013` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive-unsupported.json` | `91deffc4c8d973d86544cfa67a9eab40454ed603b6306d5b7eddf3b0fbaefcae` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `677f8e21a5dd40722b8483a73dd76ad197257865073a143bbaa3ed344366e035` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `c836a421ee6c31976f9467431dcb1c9d38984780977441b840bb8881f97f61e4` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `cf13e7f14c77524f6818910b1a94f35b4cb5a919fc7a79b37b2fd0942c19f6bc` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `b8aceb0064e2822cf3a45ddaae1ce2d0fbcf20638bb33f123216c29a4e92ccee` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `792146ae5b878f2eaf80877a5c129bb647c1e536fa59c0fdb4e269602df16ee5` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `06b4bfa4a8ac95816c5d46ae3fdaca33daa613066489b3f67d4e442fb3cccb99` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `1ae1700ceef1e47bee4921e1610b537f37933bc7d57dc423f0d0360235d35690` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `60319968af10b882f990d5748c1f85196fd9aa4aca75aa85522a572ce5127cb2` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `5b14a66ef4dcb03fd6db9014af30e276e7d21a4ae6c9ed2998d039e85825ad70` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `d1a93900b9869a8d3d8340c0b32f32bc7782ce04473c81b15e992b45460fc86f` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `e4c00903ef4d9d85b7bc196be8a9564846aec4d9cf26e8a9f058bee7458b653f` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `b22e09af0a1259ec759546108ab3c70c9683886bf665a837c4d7a0a0a98d2e74` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `180b7c0326aafbde92f5985b3c39cf8a9df45a1c17bcaeff70c031bdb18e5d30` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `884935b0e7cee56a9cf9d7a5602badc6eebcf362b2dbac60f91b5c6520f6dc55` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `592aef43a9131c7277c3f126232321a46e67c5af4a9019dbb7dfe08351584053` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `c9908442a6c9abd8864a065cba6b2fe771340837ce568ea0c744329a6ef10eaa` |
