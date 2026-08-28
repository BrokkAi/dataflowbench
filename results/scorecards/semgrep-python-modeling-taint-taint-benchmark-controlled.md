# Scorecard `semgrep-python-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-python-modeling`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0`, adapter version `0.1.0`, configuration `a2eefdc01e1df0c60b7aa2ceb0967814426f9211b61b79be0cf11de92f0b9825`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-modeling.json` (`sha256:9c4bc7eac5d731284b8bf47f04ed3257c2271ae811a0137b912528f58eb8d58c`, normalized `sha256:9c4bc7eac5d731284b8bf47f04ed3257c2271ae811a0137b912528f58eb8d58c`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 0, `unsupported` 14, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `341c6058a54996a5db44057d0add4c6072fd6e5410a0a95c807a284f4ee9f859` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `47509f286040d7549394c22d82846e9903ccaa717e0cc9da01b2d75a271566f6` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `d8bd11399f5d17afe94b388c7359578beed66f7ad365b6847e8a0962506ecf8f` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `a20df5400ecfca7b3cd29984321e21b49e72ae32627d72e91213aea8e46b5d6e` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `8a861ebd5a5003f78a2172df988444a82110d4bbf0576ca10b7fdb886762d04c` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `6af3444d53c45084556929bb40a621d73e7d6b05ce60309ab37198bfb4bdea97` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `83cc2459ed0ea7719f18643175b25af0f645b8d344bd4e6216de02e961c57724` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `c40735af204fe12cbd289219c3b1c63cb6c9dab17ba1c8e033951de8a03d8999` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `da137220f430ee69ec253743c747138dfdd1960de1562f724d792d767dd5b3d7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `393cbfa1e271c3e44a9fb2883dd283b0d9f96a4025233a731107dd7a182a9076` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `4e50c75912427047cb9b089f5c7e8db48a4a61d09df10b641012821afd5ff04d` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `71faf50ba31e9a8b2a22837eccee0a2ed52539962b704410a67d0adc9fa2b77d` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `d72def9337e8a5536ede29b8062423c79e579e4c99cf6bbb913411e8beb22385` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `97d8e5937b12a405ba68af5fe81705c20cc49e7cec61b94974b1e107a9aa90c0` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative-unsupported.json` | `8d82cc4808e5ff890fffd008b3dcb2366cf41fc5b09b7a69fe8c433ddede0271` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive-unsupported.json` | `4993899a2ff5abf212d44c76d583262549333bdf293ad2c7439c435cc841efaa` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `c9ad37c8ebe4bbc4e8581b176c720ac2b79acd3d01040d52cd8bef2720aebec9` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `79e8d6f32ac290b1b2e03c2fc802b6e63a9245dc2790373a3a810df8fe9dcdb1` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `94e45ed9173c4f3c05758aaa96f7865f787666be09cd1e1684fd32325dbc1314` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `ee61c05a0f6cb5d45539d12b9911b3a6ef0ac24a632afa17cbf9780ec93cc67c` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `5a5d0cfff696d4eb4cf853d12fb53b044ad5d382a3abb2305b8d31faefd547ea` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `472082188283c35e9225e6dcfa388043b4e617f7d58106a34789afe6a508ed63` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `5285f30b55acf99a6cfb2b3966534ead40bf37a04d8f5953ef1c896710d1b818` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `78626fed6bc4a7bca161eacc13b73d86c4f1c8f7b790cb84167d545435ff1366` |
