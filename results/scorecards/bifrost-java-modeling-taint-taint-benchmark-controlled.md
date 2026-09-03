# Scorecard `bifrost-java-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-java-modeling`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249`, adapter version `0.1.0`, configuration `f84f51766cf26ce5665df0281d649df8fdb9ec64ab76cde675f790b8c0644ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-modeling.json` (`sha256:89afaf65626a9d486e53bf10c6ad2d87337c0ca31a6d0a4a30491d67417d4c7f`, normalized `sha256:89afaf65626a9d486e53bf10c6ad2d87337c0ca31a6d0a4a30491d67417d4c7f`). Generated from freeze manifest `reports/freeze.json` (`sha256:e3fbcae1eaf3f49192f7156616c4b2149893a8470e03ff445fcd1d5f984f9e5c`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `82dc15a5ffb2d064e755aeff5d011ffd5202618d5d47b736b141ae321c52881a` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `f2fadc2ad15bb2ab632f2de6246283a901b1674d014bacf0cb9374ab9c0124df` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `9987b03ed886d9fca311a74fa49c52d0108c45c19a6ff794343bce4deeb83a2a` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `23dfadb17cbadce84f90b8b3b7520f00677f661adf4125812b403c39328b1452` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `ee836110c1cc55855403e6f795abd7788c59abccace8b47c2e2f81de80d63f2a` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `62a95c6f103e4d70e7597d0bfb8b4fb474521babef71c645ebdc61892bc72260` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `986ce84581e1927b275c085c5f5457b97df1428f34cd956ec15894183f0bfcbf` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `1c74e9a2eac5ba55e0b2644647c7a4a4c4776250acf40fb3c4a669f2cb487459` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `59f23825d52d78e50652027d6194860ad2ba523824a09e613f96bc20c95e6b99` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `8bc2c4eda14de1cfa367ebe777df26500661db4e396cb630839a67b0b79ac8f9` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `f16fd4dc6809571413b138c8ae32f7e678d532bd41454d4a3afe32e10d6fe42c` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `65138c68b83a931fa9e1fa9d57d0d03af424e93396f82e855da62994f6adc6a7` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `e2e24043a430bee11568e55d695472be49162bcb46aa286f433a06c77b04f10b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `e41a9f9481302411ed7b5d88b5e1ffeed45703ed77b972d3527e1ccb410263e4` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `99768ecb7ed8078ebc2afc8409e43664737355e5e231eba2318bb9f2e3d5523f` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `ce0c3de5e53e2f2b624d4f85b58e25c7af6a33372832db05a5f2655103b01927` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `afe38642fa4620c1b688e1662b791ac839b7f505af8524e2b651d6b3bf78786e` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `48718411522742d6c56e18f93cbf57ba7b01c0090f29efcb62ef2fc5e7bf4256` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `e20e25e0c7894b63aef0b617eb0a119d20571d562cccd2b0a232d7aa6ac93b81` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `2371933769880ed335a015b15d8389eb8cb010b4af6d9baacad6f15dfffe2c33` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `42d4558d14886b8ae5b98335daeed93ebe6dfcefcb991bc819104265c3cb779e` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `f66d94749ab69a9b4c3e69496d3583f2f212dcc43f4762f82beba25ae40bd2a2` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `5f00f22d64c7ec61125859e3e4e97be5382f0a462407b008fe675be0d8928b81` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `d7f0cf7b373161601ec50a02b5e83f405be1111d5529f7c1a8153976465e296a` |
