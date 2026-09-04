# Scorecard `codeql-java-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-java-modeling`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `38acb5de67ed39a244c7eb8a9db755ddbcf197488051a5f1ec0d35b65fa30aee`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-modeling.json` (`sha256:14c991ee939e1d4aef3e2850551166cfc3d5de606919aa186a577e4938100975`, normalized `sha256:14c991ee939e1d4aef3e2850551166cfc3d5de606919aa186a577e4938100975`). Generated from freeze manifest `reports/freeze.json` (`sha256:c543ae4ebd11ed6f3495f4461b5b4bd7c84d0874997f1b62044e9df62817b28b`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 12, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-negative.sarif.json` | `102ee8547ed5f2ab27431f3279fd7d286f84c4b9c775525b7581b1cf4ab74d10` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-positive.sarif.json` | `3f08567938be5c3d418065c95c9cf7ad7abed4543752cd080ba12e18d4efe53a` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-negative.sarif.json` | `293878064222c178bb1210bea97643b841d85b03b9289563a0ea557ae7256a5e` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-positive.sarif.json` | `acdf515c72308c70a29f8cbd95ff8df8523c6963fa6b301177a2535559fd1210` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.sarif.json` | `a5ae7000b8236f0ef68b100bd50f1ebf89752cd5b4ebe9b5da32da0b43503a7d` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.sarif.json` | `9a395584e926e17c96f0b77011d248e9e953f5519ed67a782a15d715b9b3e5e3` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.sarif.json` | `77494238f8e5b1a21c979501661fb496defe1582133fbbdde689da0158d2ff97` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.sarif.json` | `16067246d7e2d749e1995c680187a0128ea5582e5c939a1c699f426855a7156a` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-negative.sarif.json` | `1247b247bfb5ddfcbd9a4dd3bf477c9f244585027690353dfb359673e3848035` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-positive.sarif.json` | `4be1de9bfa67f6bbab973112e9a368fc021bca0bedb6ec9ad7164b450cc2160a` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-negative.sarif.json` | `5da62ccaebb0ba5bbb0a129580c0ec4956a41eacb5d733c5cbd28de3f3b06a54` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-positive.sarif.json` | `79904de73ed6e98ec2fa7078bb78516ad234fc1d47e92720570e66a4e3977321` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.sarif.json` | `d667ab53520e54334615acee48940f8d7b3cf7c28cca49355478dfe6fcc220d7` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.sarif.json` | `111d633f7f0d942e1eee0f2a9a2dfa2f61e7aedde9f8aea3f18a5333210c536d` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.sarif.json` | `79980779a539be34fc31f89d5605c11816319c480f14984c4b32d25a6c2e3a60` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.sarif.json` | `4eadb7a1a4c2e902f64b0ec9346ba01b7e74227e7423c5ee0999bc15a75a513a` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-negative.sarif.json` | `1914219994dc823f9ef7af237acdc2eeede8c44a04ef02c050aaa3f7c3daced5` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-positive.sarif.json` | `5ca0645b073592c9a69530e5fde1185ad765006a2424f358d504050d5f9a71ad` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-negative.sarif.json` | `7dd3bd26882a9dd8376507cc3cf1cb9849f4133073f2ddee92d3638117b39a0f` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-positive.sarif.json` | `ca711d627986f7d8131c2d971f62e2c832da4a5f848ddb24da9ea26beb015e68` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-negative.sarif.json` | `010fabc4bae28bdf60cb98f382bb5e4a5ec59505abfacd180b1856c1e9bb7803` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-positive.sarif.json` | `e369be55b796eb6049482369bd7956a9c9c35ad3b14b7fade638839fb2100994` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-negative.sarif.json` | `142e200e827351ae8cb9520b93ca8186c780b047e92231f0f940092a7d9f4ce1` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-positive.sarif.json` | `c0454e6e07d8957912c378d03a668f23f56ff2f63895c8d957ee08e539035f8a` |
