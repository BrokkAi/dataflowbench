# Scorecard `joern-python-modeling-taint-taint-benchmark-controlled`

Adapter `joern-python-modeling`: `joern` `4.0.621` (build `joern-cli:4.0.621`, adapter version `0.1.0`, configuration `f7f9d9d53572b098556aa86d16b3e9a0b3e9c7a4226526090bb03fd61bbf1eb8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-modeling.json` (`sha256:300b351dbe09ef74429771ec5184488db6b95ca607215933eee9e7fb77bd6599`, normalized `sha256:300b351dbe09ef74429771ec5184488db6b95ca607215933eee9e7fb77bd6599`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 10, `inconclusive` 0, `unsupported` 8, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 2 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 2 | 0 | 2 | 0 | 8 | 0 | 0.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 50.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `11b33d73a4ac59fa06b99078693c2c9c77155da95ab672013c5f0f0cf46b546a` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `10abecb206f50257b57e4ca59959d7cf16c81feb0f8893910c87f7eaf1549eb3` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `9c60ad999b1b3ccaf76d6574b608c9ca297fd9442953312eaf6840f9533675fc` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `94142d00266c1c22b9ef4cb32ee94c3678d1a95d9fcb691b92fd142394cd4cdf` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `00c9acdf43dab92c3b7a9c4fb5d0272352f523ed177ecc5c94ce6c8bca8c41a0` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `653b270779612f78e2c4566977b9943e249c61fa804abd6dcff8d27137747e32` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `01a789f1fd7efb62ef70a1f6872b41eb1235df4d17dd28ed13e1afeffc208001` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `ee17813df5eeffb19f350a0265a3fc1bb8f2cdde6258c8ac82db1b6cc136b29e` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `9ec40c97e2e76ebdf323913c747aade4e975a9ff8605cea4c7ccb25bf6efc637` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `94d50ac4f0309c8067bdc3fe2b5408d2d30810ae0f849fe4dd73b999340cd984` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `3569b325db07086cf9240c5fb730ef2b768f1b7b6a90358c8cd463ace49ffc8b` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `d91e57487a108b4358ef2fbd14cc187bfad32d10fcb8d8c430dfd5005a635337` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `8e81ff7bafd5dd9805b638965e5285416e7edad56e019a5bcf67848185c538cc` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `258a4c1503a749ab0ec0fab426e9bdcbe054d38682ec606a3e2335e6846ef8b8` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `1e497663227a7730ed5429288ba10b4087f4c840711d27ff658779c070edb7ab` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `b2daa668a7cb050518a4bb7c6dc5fe2b6dd3f76056681b07f2c87bf70a366757` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `55e717ae63668e935ed295a37826d61f8fd12e848b524e4e46cbc570ed607aa1` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `f605c73538bdbc0a3999013d445c0387268ca1c999456d9e79f9b500c12cc12b` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `863ac43d1632fae6415fa726065c57c17cadf71acca8c2c0a6a4f626579475d0` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `f741a2591443ef851480a57dcc66db2c7149eeea976029cf1949c07cbae088b6` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `a81da1f295187d326a6188f1f537280fb3cd38816153e06234ac47340ab2fe1b` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `a5336b8361d04f1710ceed0de5e86587383b838bd1945335f80b4d3258149cdf` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `98029104498558021c7e672d86c159a0592ecdff0cff4daa0c6f4095ef069ffb` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `d86ff5b356291d402d56300c0e1dabd6384e3f985552bdbafb76f6b1c592e1fd` |
