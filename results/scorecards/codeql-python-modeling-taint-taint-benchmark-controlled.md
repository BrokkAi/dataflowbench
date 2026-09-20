# Scorecard `codeql-python-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-python-modeling`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9`, adapter version `0.1.0`, configuration `cd3c4feeeb3473e72d9c35a582a32d0b65d281d759bf77f9a2e0c0411d3a7262`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-modeling.json` (`sha256:9a60d102412a968f1ab61abf5687b750b1122d974978d5ad7a4558db2024f675`, normalized `sha256:9a60d102412a968f1ab61abf5687b750b1122d974978d5ad7a4558db2024f675`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `python`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-negative.sarif.json` | `fb2a1e7402788e98484480fa9ae43a7f6968b0a0ea27581a341613776d06138c` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-positive.sarif.json` | `59f446c75282f8634ceefd037e018d0d12bb58b6b570e54c86d0e6d952f23c25` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-negative.sarif.json` | `0aa326b306eb289072dada1649ba8304b3abb50af5b108bc6ede39fdb9938021` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-positive.sarif.json` | `33d08bc4c28e8d11cc458cbc43026b46096d25b4273bf402583f4e0daa7164b8` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.sarif.json` | `8a202301b6c7e8c3f931308c986c977fcbe9e4cf229c7c2a372a5492109e73e0` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.sarif.json` | `e362d0b008e568ae08e564b71a520e15bcea2e24ce01b956aca5791e4028a2a8` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.sarif.json` | `44aae7de90ed338c3fd4cd023b7549f28a2dd8f711c3b74f64ddc4205003cd07` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.sarif.json` | `8b6c478ea6e61eabde6321ac8f81f66cd682073b1808facb61a6fee678260307` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-negative.sarif.json` | `08b6e3ed53e89891c07c2b27d9e578740e937294e48611ec70b8f9dd31421d78` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-positive.sarif.json` | `beebbf8b3a4aadfb57da854733602040fcdafb81e076037a962012a9b4243ebc` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-negative.sarif.json` | `b9fb4a6a2c6cbbcf42dace636b2967446291195d16ca029dc6931f5457e45a40` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-positive.sarif.json` | `50caa58b42064532a6cca4004d17c02aa3f1d45092668b589c98ab6a2222dd2a` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.sarif.json` | `21f8c9e09932a289c7d932090a80349af2a4b5e4c8cd10f39bc147736b75961d` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.sarif.json` | `45d4243d275177fd5f020457a6f337c6c42cea8dc777b7cc44c75e885bf0503c` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.sarif.json` | `57800fbae3879392b065b4f38365551e89762ac26e0a8b8246cf8302b9274ec4` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.sarif.json` | `1097900a307e94f6f79aeb00b52b8e8ad7893a38265b04bfdd20361f8274a7a5` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-negative.sarif.json` | `8175beec856234e857a89aec3560481c08fbedff36952a5f30b7a7509a224ef8` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-positive.sarif.json` | `144796c86d5f7af3d63aad0986c11427424d7f55676099ead79e2e3bda0c5db1` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-negative.sarif.json` | `f306c411b055436b4941fc44e002520b980c7012770f8ca07fa0825a75e7fc34` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-positive.sarif.json` | `b15f0367a7b3793673a9af6fc364dfd07e5c275d7e4113f0d2f78aa437b78bb0` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-negative.sarif.json` | `5fbc1e13a0f3c4be6d3b3f7efe66b6aa8588e1fc79107f142842845bb55320bb` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-positive.sarif.json` | `f872c51fa6bbd44373af78f9efaca1b64326b780e19ef9be447ae83ab0c64305` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-negative.sarif.json` | `8cda79453ea87d8dcea09135225f9d036dfbbd1aa804709d764bf3c76d16e202` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-positive.sarif.json` | `02395f0ee72cc8f193289cf0c3e2933d1c3933e0b0d709cb043662e0337ce458` |
