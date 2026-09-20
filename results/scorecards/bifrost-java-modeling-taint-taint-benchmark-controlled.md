# Scorecard `bifrost-java-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-java-modeling`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f`, adapter version `0.1.0`, configuration `f84f51766cf26ce5665df0281d649df8fdb9ec64ab76cde675f790b8c0644ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-modeling.json` (`sha256:55105ad6a1558d54e29c5389ca9e96ad2bc14d48c8a0742fb02f67fe8fac20cb`, normalized `sha256:55105ad6a1558d54e29c5389ca9e96ad2bc14d48c8a0742fb02f67fe8fac20cb`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `java`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `34853698df2306023c5cd9af9b34cdc489ff61e8ff8f6e83e819e44cc3735d03` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `775987587bd9abfec0b4d0fa6a349069201e846a44be35d07315b304ca68210d` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `621b798d954f956d87bd6ddd2db68f002973cdb0cbf10e394fb5d86f62f36191` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `a183f6d96b7cdc560a0862077f2546051326ddeda96a0b51e18d22b2de9481e1` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `bedaa28d225d645d0bd99e77623d3d666283f960b268bdce81d8efdb2aa3d986` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `fa020e8729c4a36286ba713931491558c382e5c3bd58efcc62e5ae800f307822` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `2e8c30ecf48ff9d318e0953003ebc5c56c64e09832ad5ffdbcb3badf8738f8bf` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `29df9e46b50792593dff20aceb65c345dc23b60cef7c5318a22cd2091e8498af` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `e724e8c6f60b2b88376039183846a3689aa07f63076e4203e66ac4f249021a68` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `72185d106edee71d42937776750e957cfc4f8c900c1236402f491cb91ccf0ae1` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `93e8cc38a1c9e03792c2e927e558cf254ebdba149eea3e598b6542a898ac6313` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `6a74e5319a5f22efb2fc5f5ed6050f1cbbab0b21e1cfaf576e8069dbe5446ddc` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `250a57acbf8c7d850865588b688a4313892d9e6cf01343e8fd67d7e92b947124` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `f8904c5cb98547ba543c27589441af814936b7e77ab9f90fd7c9b6da9296df2a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `8dc76cbfebe2e3c5564ef490a5672a2f829cb2abd5ecb3569b979fa31ca88beb` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `19396325053c7b9b11620634fdb8c9b447936b5f9bbb34f4acc765cc81d06789` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `5bdec52be2cf5a0df16caa10c8b8c7f7c940ad1ed652ed5790e2703b07d2cb6f` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `60e2c9481988760b6d624c6805ab51f4e1e6b41906cfc4f571519cbfc4deacba` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `6c50cceca6b8815ef9f9df03d4e6f361f127ed8722e5f6766910ef412b306119` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `084262d273e30a72345b0f8201b72d7d89a518c2c34daf1e489d7b8a54b3d8b7` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `964df5ded9bdd4c1d13779a0595aafc6dc9e719aa524d3d10e614a9e87ff5f10` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `71caa2394420cc29b442a0d452373d54eed44d393f95aa593c88ca9a09d5920c` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `5651517cc157a4b1262a4f0b6d8700e4cc4d0353cb382dfb6a0facb88f19aa77` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `fcbb6a6095d0ec66de9c02e8195cafe157e517d4e35a008bf08f12275c53e5cb` |
