# Scorecard `joern-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `joern-javascript-modeling`: `joern` `4.0.617` (build `joern-cli:4.0.617`, adapter version `0.1.0`, configuration `44faa326bd6f6b0d37fa963f4342d0e498bc2e617b34709a2a2e6e61aeaf07e6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-modeling.json` (`sha256:9912c4e6e183f49a360ee8cdd0de3afea1a153a21c2b5e06f83e5f790bdd3670`, normalized `sha256:9912c4e6e183f49a360ee8cdd0de3afea1a153a21c2b5e06f83e5f790bdd3670`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

## Language `javascript`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `42b2372acaababd0552fb0df25acb216cadb4464aba62f0fadfcfe111516f6c6` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `a67ec07ec733c19ecf11c303eac95ea03ff9d98aa58a5f3c85c0715255be1f1a` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `24c110c7a344c2779140afb395fac2bb232c67b12eb0f656972a662da61051d0` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `c39cbf34cee4d2caaac4d258e2dc96010f4bea7e2faa3b861d170861872482fc` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `c295122ba0817ab874e010b7bd181bc1637d44ed18eef2c52be816af1527f3a6` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `53dcd08891227528d993b45a9a4db668c3e4d19f965fc63ebe4f19c52e1cfe3b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `1890115cdba62911697faa5f0f494ce9cc2708ba76d6ed2b1db155154ac5d1d5` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `76b5a18c9c1ce5a47e41a1640d33134ac486b8dd99b1936adc85ab2bc6918fc3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `578af8a562583b1e03c82b9b70ac27bb3a7b4295f376cac654ddea43dab84794` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `29bd600769a35dbc85b034a1b84fb7b4dcbfbc076ce209e927109e40aa5aa894` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `ff8130d4bcf7c419ab336323fcabc7b7e343829056f600af8ddd3824c15aec16` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `55d5451a8a7a761b045712053fdddf7ff3d57b87d87648b1e795496d46fb36ca` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `43e55f58a7fbb1d68c5e293516a999085b36503c213152a74350f7a6931f2c3c` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `1990605d3794ec7b97d6f5ef39d6a98d1d37cd2189879b83733a54b4997399ca` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `f032e0fe98bf520e15ff13b059e8133c45af5dfbaab7af5eeddf5ee1fe92fe56` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `854d8104438cb33f169f5abc06bd6e4079c41e3a4d09850d7f88adc9fe816818` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `335e13ebf38bea9c962e925206d69e6083b36967511e8486d7a530f4019d310a` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `65279506acb3e8c5b46b1930b2777354e50dce766cd8b282edf398f01878d2b9` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `6f9160505ce4a59989ac32d8cffae7914973989cdd1d7c1e687915216a3d5bab` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `57cfc972ca141b4c27cfbf6c7ed6981cb656cdc733f9b138ca7054f4a481f9c8` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `1dd02dc8efa0d1f42ebeaf9ba1e9c9bfd9e44abb9ed297ce7a6ca47227456ece` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `cdb73d543297cbfc7452b36045e1828afb3498d658770737cf7eaffcde89ce7d` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `5d22934de913cb9ccad879d5a30d54f03f7a6d3b5d67524e6b289f79c1c6a24d` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `afd8eef91625540821b1131f9db714b92b2a97b054a6f4eb3e15eb1451952d41` |
