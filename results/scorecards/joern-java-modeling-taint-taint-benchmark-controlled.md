# Scorecard `joern-java-modeling-taint-taint-benchmark-controlled`

Adapter `joern-java-modeling`: `joern` `4.0.621` (build `joern-cli:4.0.621`, adapter version `0.1.0`, configuration `55282607023d6902aebe9e2e4199542f04b407229ac0ab04eab9b70dd4a6980f`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-modeling.json` (`sha256:9eb2e6cbb7f2ec0bb92dca6cd6d27a0acb1f9bb3bc22f4745e9de5a72190725e`, normalized `sha256:9eb2e6cbb7f2ec0bb92dca6cd6d27a0acb1f9bb3bc22f4745e9de5a72190725e`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `java`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `dfb9f35bd28e37b00272700afe8b2b790625c89f9010af897e77e364eb7b3ec9` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `09804c6ab55c69f405579318467889b537c5a39bbda550981700e32f24019ca4` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `7fed3320a385d5a4af802cc47621efc4b5f2719b443ad030eaa2873620856fed` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `605b98939c3e92fee99d8e391aa6c728657e625b90ec678bc1d4ada3a803ba62` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `cab2a8711d654a926c565adfaa78e8f447702f3fb487aeae56cc226c9f391d81` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `0ed32f9a5b5ab897ab633a2b048e5cc7ddbf19cc56efb39f78cb4fb9423b4ca8` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `28c19ac924018cfb7a2523a151e60f11996cc2d1abfa038cbac4575cce061a34` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `b9c7a2b4cb2ff6903ac87381a158ae8cbd455cbcfff4b3d57526e355aeb29ef1` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `dbde9436d0f49d6647020fa2e74f3b3a1cc756d9fa099dfb67889d6cf0fa6b77` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `4219ed6ec53466755049eee6bd2d8bd5b26faa020c3faa337c882b6842b2b170` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `64c979247690cc1ad737fbff87713c8e7fe3cb77a947307b6bad79839dbf05c6` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `7a1345d86bfe1f6ceda2a389e131b4bfc4be2b0d058e1acb88b85dba5a5faf25` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `abff4ff2da7ce3e6bb21ef83095a828c97759729c9cad44bc45e90147eeeca58` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `2fcb135dd092c9f0898e245b3505017ebff11748fde85f3334577d1a200f9faa` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `9ae526f4c66a54caee34fe25a97569fd31a2be0e307e7ee37db6db0a8bfa6635` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `35716d1ea1282740d5ead1083e7669ce163994de824f7d9e9f58ff0ee602bfec` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `152106b058f73ed732c8f36b82f19deb23e72c0c563b1cb0598c9c6b738a86f4` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `c93a5d62a2f05f67c017a4e7bd674b1be3558546aaeb202b4a2af7f962f7ce13` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `e1360154fb2b747ff66659f431d89884e2b8b9a2499ed2c93dccfd437eaa3725` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `a1a76603f8222859934c6acc7fc86e066e8fd5bfa12242bacf5764c7c007984a` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `3dac2511bb67eb7b7741d117f3715c027b778085b9b3e718898b7e8d36d62e28` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `d4467a8dd90c99bd46520d38ff30e039e94df76568228918e23666a5cc9fdd69` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `3c33c9f3ef138191e84532dc575196a38ba01574b2502e29d2563acfb14f9c19` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `a329bade5e6306a8ce6476bf5a9bc4caffb60d25a81e4cde368b9d158766a94c` |
