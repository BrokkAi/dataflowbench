# Scorecard `bifrost-java-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-java-modeling`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `f84f51766cf26ce5665df0281d649df8fdb9ec64ab76cde675f790b8c0644ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-modeling.json` (`sha256:49c2ffa6b912b7f4df5a661b29b4c2315e99bb88a24a4691e90b7deafa839d50`, normalized `sha256:49c2ffa6b912b7f4df5a661b29b4c2315e99bb88a24a4691e90b7deafa839d50`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `f58f77aaec8db2f07fb89e754de3f5e7ede93b602ad4877222ef364703b585af` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `0eef6833b8035b466562de7bf6aafa154915321094a322a0e2d20fe37498bc9f` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `66c566ae686b9029af83bcc011497c44ec566f21cf28ad4b2fdc22704f26ba44` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `40315aa5f16c6e0e0ab1919a591ebb1bf66a90f2c8808bf615a5b24b24de97a9` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `dc04b18dc621a83715b1518e1ec19292b5576450fca26bb3f78ba4412097bdfe` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `8287a993411ef89ab7f739b81eab0d94cb739abc4c64cb597c2df2a559cf68cc` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `0455814820b40001824c6a271956b4c3b2ccf2d269fbce9fc1711064edc6a527` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `ac4f5baa4b0a8a03aab3a449bb46913d4ab8de377952252e046d724a41255a19` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `2a9c3a19db63e92a14158504f56d38be897a8e649fff6cbaa247dae65ce1df42` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `7451106f4fdd73b0581431f10f549ffd6dc2737bff7c529998871978b2af8130` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `15ef45d038bb5faa860e06ff6e3f05098f58d910d7e820b25f2ea3279ffab5e5` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `4be9a82b6cc31b01d6aae5b3e420f519913e07015497587a950979862fae81d3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `e00c0175d16972e7dd52d9f9b436eb43d67fc27423409e4904e925eca1fdc7c1` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `ee1f57790208c1b3256a92b2b0b5b22871170331e5a2deaed13b55038f89e3a9` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `02b783fe8087e42ae475caee7bd40380ae5b7198dff66c0f8f117743cd78cd2e` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `990410e67b8b0093f2ff1710a62b1d4c02810ef1e980f3bcb28d43f4c40b12e7` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `a75e7978b8cb7889133bdd8cf946b2ccdf57a66a1bdda53d4c4593c154032bd5` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `7cb4acc76bd209bf493e54d11034a8296caa57f1aca75532d3d37028cc7919bc` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `9967721ae5b5ff09b9a001e9cedda873583c5bbab87470d0ae4176807828b8da` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `643657b50de0b77518a33b858015a7ef61ecbc1ba6cfcb178c3ffb928a8c62aa` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `56c284c39bcf01ddb9f132aceac50e2bce073f8ed38f8d069fe54735fd126e82` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `15e0cea8188fc6d98d8393aa986ad770a30ed7fef50d9667a5318b3d5b033a29` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `7bc2d72a2210b2a8aa2514d9a55656462d1ee803783d17c75dc10c9a66d5c5dd` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `46febe0f94d0e31583dba70c29c5637fd59bddf244b06455f9533c6d11fcc48f` |
