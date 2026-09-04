# Scorecard `opentaint-java-modeling-taint-taint-benchmark-controlled`

Adapter `opentaint-java-modeling`: `opentaint` `analyzer/2026.09.03.9752bd2` (build `opentaint-project-analyzer.jar sha256:db3a61637207633342c15ebc40b0164205563ba6446d48a8fa5c4f8fd194b61c; opentaint-models.tar.gz sha256:8746b9594266c67f04cd93a64c6c30673f98ccaeb59baed76d202ffee327a8d4`, adapter version `0.1.0`, configuration `e24a41d7bba6392571d3c6622e40fab227b8f72be1150c75b3f9657098be5859`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/opentaint-java-modeling.json` (`sha256:bd5030d1777fe04d5d068a83ab37ae692e9301f0e36c698c8e3c0aa71929121c`, normalized `sha256:bd5030d1777fe04d5d068a83ab37ae692e9301f0e36c698c8e3c0aa71929121c`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

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
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `c5a515d6664556925ca0cab71c8f3bf6402fbea3100df46e541fb4bffbc1a604` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `967370e3519ec096a1251e3a5140c3b1d4a391b243c4afdd1ad99d25d406055c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `5cdeef815e672f364e7c8e3b68811ec67f26e9e508ccd30d365fc2396b04bbbd` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `ac3c9ae94c660e6de8028aae7e1d2434d669c2ce9fa3fe58792ed11c0ca2898e` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `3d8474cb9176eaec8f2086d93685ba5df1dc5c81a354427d48a6d861b09b4e90` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `7cf238b339e3303585894d7bc49c9d381d4d4200e5c7bfe42854b22219ded88c` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `d0c6451473618b77bc24d048c530b005981b943a37103eb52ed11cf37e18793e` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `7a389abba9319311f4048f856220880c3f1bee6ed5234e1737f009f34741be59` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `2900308d0535b4b85fb5d94e07ffe290375535a7c28ca7b4b2f9d0b241e2733b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `44f714e7e26fdb4bb53771b29c8c7ed375481ca79a2be66930a0acf1eefc5ba5` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `8f9767be5fafae8cdb1149d72da1c58d3380e7901272e8ce4e7d078e087abcb8` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `3efa9b36af6a581ab393e784d71a5b567ff98f790884e58cbfd3b9478b253c7b` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `1e6110ae0de4062162c9cc9199118044a3d7cd22c8922ba6e8a96cf4bd6f6e37` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `2adba224b6a9d7d95e92fd921545882dd14c20d7132cc27e727dfcf2e06d48db` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `7b3afa0906c8102d6e388aa7a4913ab2f59222ae48f28f8b5a8d82ebdd74af27` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `ee66097f10f3f000bca12666d0169ad0d21af73e2db7b70c1b762e83f34d1a57` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `dad771ab672cfd138f625480587b84ed08d11e5fd3c123ffceb3f6dbc3d7b76f` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `e15a98b0c4cf221e691b7f565d2deca30637523d2ddb44ffc7d397e72ca7c4f0` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `01f82b3f117947d3e8d4412e3591119ca3b62ed398da1e0c699fa48a2f0779a7` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `9404965702a77cfbc1e549a63a731e0caa96e1415f0b43d181b9ac3071a991d4` |
