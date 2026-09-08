# Scorecard `opentaint-java-modeling-taint-taint-benchmark-controlled`

Adapter `opentaint-java-modeling`: `opentaint` `v0.4.6` (build `opentaint-project-analyzer.jar sha256:2ca93b6c33462bdbc23ceccdc5375e1a900682b33371cd906e5214dc7c48f569; opentaint-models.tar.gz sha256:20a96a50fba9ab6f6e98e8562019e5ecbe2a77de7947981eaf6e379f04065329`, adapter version `0.1.0`, configuration `e24a41d7bba6392571d3c6622e40fab227b8f72be1150c75b3f9657098be5859`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/opentaint-java-modeling.json` (`sha256:2ad1060823a5379f249a6d86e15958792f061f1e7261f4acc480e8e3d2f087a8`, normalized `sha256:2ad1060823a5379f249a6d86e15958792f061f1e7261f4acc480e8e3d2f087a8`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 6, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 2 | 0 | 0 | 2 | 0 | 8 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `b7d6d08ecb9b3b680b9681760a4f9c6a74cea4ce7329b908830682604caf3650` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `722fd6fcf694b0ad15322a16689f2367861f87429727f2fcba3412bad022b73d` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `853c1d637919cad24bc9818955fed6837973cfd8fdee0307b83bfe50efe8439a` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `5d605d3c8edf4049163dae19486b65c52061b2a702214849f42d584db3cd0424` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `e971657cce746c6424f2ca451ad95b432d39e198e7ee4d6c644fd898875e21b8` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `e6f0d97da85d689893eafea477a0cbff4ac6452c89f38189fba6a434dcdb470f` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `23ea5f1f0a0fd7bd2a6d3483e81d749b8de7bff7c82aa8ac189c058aa5b0e714` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `841501fa4a67cb573237d718ade8282d0d3dedc326a5db6d809b252756ea9eb7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `3d8474cb9176eaec8f2086d93685ba5df1dc5c81a354427d48a6d861b09b4e90` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `7cf238b339e3303585894d7bc49c9d381d4d4200e5c7bfe42854b22219ded88c` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `d0c6451473618b77bc24d048c530b005981b943a37103eb52ed11cf37e18793e` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `7a389abba9319311f4048f856220880c3f1bee6ed5234e1737f009f34741be59` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `2900308d0535b4b85fb5d94e07ffe290375535a7c28ca7b4b2f9d0b241e2733b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `44f714e7e26fdb4bb53771b29c8c7ed375481ca79a2be66930a0acf1eefc5ba5` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `8f9767be5fafae8cdb1149d72da1c58d3380e7901272e8ce4e7d078e087abcb8` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `3efa9b36af6a581ab393e784d71a5b567ff98f790884e58cbfd3b9478b253c7b` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `0fa25b5a116ffc707b867bf2818fb1ee4804062f73980352b65ef60aad946482` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `a8dd3fae608cab48b6df1d17fac915473bbeb6fc007557faf8e073daa2693a8f` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `26e66c631cbdf353df1005fb89d5055b172b02b5a5b820ac34e87b40b63f6b01` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `2c30aa3f127b667744489a405629c8fa650ef8e7e20e08b9dc5fe98090d81942` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `36bdcb753cfddbbe97e3f9ed375c5712ea91658c5298fc38382acadc4dc4a08a` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `b32d275ee0f6e04674e979620e56b1c66d570cd887bfd8d529c730c16b0f7087` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `cfe9e4fb91a433cfcf760a76356ab0eecefd7f56022555ce1862bdb2facc9504` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `58ea814929377d24ee8c4374e6f52e9314906b36c186de997d8bdbc8f7932c3e` |
