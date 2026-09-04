# Scorecard `opentaint-java-modeling-taint-taint-benchmark-controlled`

Adapter `opentaint-java-modeling`: `opentaint` `analyzer/2026.08.27.17eb0fe` (build `opentaint-project-analyzer.jar sha256:811bdb22786e539c9aabdce5bef91f0c6521cc099adbe2720e6a840c09badf54; opentaint-models.tar.gz sha256:c2a8fb0bbc3b6d59ed6db0c62732ff9a6f0f491d515cc2247932f2dd78cbb9f5`, adapter version `0.1.0`, configuration `e24a41d7bba6392571d3c6622e40fab227b8f72be1150c75b3f9657098be5859`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/opentaint-java-modeling.json` (`sha256:c5710db993b1557f8d1e96a1bd459cb6404a0d2ae74554bd83e2a945bd537805`, normalized `sha256:c5710db993b1557f8d1e96a1bd459cb6404a0d2ae74554bd83e2a945bd537805`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

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
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `66c7d79168be303694b5965ba1078d6a0c7d305f0e13e0a23732a5c9212a7fa2` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `d322de4b785b33dfa70dafd8dc323fb9085d8510cfbad6baf5d12947ab24c790` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `b071bb693c7f1d28eaa87b216795d13efcebeb6af0c04c8caee222e47d4a2e20` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `7a81b9341a9739be03c37048df21cdea0a71ff94fd05b90dbfa19b0b7dbe4c08` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `3d8474cb9176eaec8f2086d93685ba5df1dc5c81a354427d48a6d861b09b4e90` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `7cf238b339e3303585894d7bc49c9d381d4d4200e5c7bfe42854b22219ded88c` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `d0c6451473618b77bc24d048c530b005981b943a37103eb52ed11cf37e18793e` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `7a389abba9319311f4048f856220880c3f1bee6ed5234e1737f009f34741be59` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `2900308d0535b4b85fb5d94e07ffe290375535a7c28ca7b4b2f9d0b241e2733b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `44f714e7e26fdb4bb53771b29c8c7ed375481ca79a2be66930a0acf1eefc5ba5` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `8f9767be5fafae8cdb1149d72da1c58d3380e7901272e8ce4e7d078e087abcb8` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `3efa9b36af6a581ab393e784d71a5b567ff98f790884e58cbfd3b9478b253c7b` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `f56c42482a43b1dd66dfa353bcb27bf82e203674832167d840778fd612c5c9ea` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `f81e1bd179bcfa9790ee8bdd62b44d77a1a531aef5d49a87b3ae0c09ce4f8d48` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `b6e9beac8680f905b3f1becaa7ef0dfc2d2982395363dbc908e25ebf6604562c` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `346e788fcb360c76be7620704434a7a450fbd300b807f22b8b3970d8af350d01` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `978356877f685c5bb99c79ed9669bb448ea032ac746ce9be4aeea669431da554` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `b79fbe3842060fd1898b50c61ce1d96141f582f9fc2fcba6d488d40d56575066` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `0453bc7ee4979f3c8ed3e7e79f02a0813ff812a83ac611549d54b86a73927b5f` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `2c219856c486375ea73f7867dd12bc2d472e4ad206915e36e85bc5e581037e93` |
