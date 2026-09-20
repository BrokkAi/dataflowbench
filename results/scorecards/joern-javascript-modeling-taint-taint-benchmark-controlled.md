# Scorecard `joern-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `joern-javascript-modeling`: `joern` `4.0.628` (build `joern-cli:4.0.628`, adapter version `0.1.0`, configuration `44faa326bd6f6b0d37fa963f4342d0e498bc2e617b34709a2a2e6e61aeaf07e6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-modeling.json` (`sha256:1268dceb8ab1302e519fd26031a230638de9e7f5126908a7f300b3aef4d9684a`, normalized `sha256:1268dceb8ab1302e519fd26031a230638de9e7f5126908a7f300b3aef4d9684a`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `c407043b860258365b275fab2e85306ec5e2c3d0e42e2ca8a1449efc36843c32` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `70959faadb3c62be8547c6b4bd96c602f1dd37fa9dddd0923992d78852d81cc3` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `32cc934f0c5f1aa14ef6e72becb9aab99f6bcddf7ee840ea2b4e52c123096244` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `975788cbe8106e6105829d77937d079eaf7c71000c4b706cd69bca7679129570` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `533daf527c635ff113ff4b3b717a6c3d93fa22662052fb6d0fa3b9bb78597587` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `09e6efbaf2d1aaaaf40463c3554ade0784bb941369857c9a0e1d6b0fc0877913` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `fd8d4b91cdf51e1ae7b6e6342ecb9c67b26020eff5c6e20e5d60a17c03db8bd8` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `06ad7d215a0721046c91bd3dcf273b03fc63ec4d4b2a54d02e4e010aafdbfb27` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `6d2c8f3e11fc3e215ce0033f25fa4921cff260ff7bab57f16918d136d2a41971` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `f786142a0a77dd115a4d8e11da17468d85ee8774bf9d2e4d78e5fc60b713a607` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `ccccb4cce132ed144777360d9e5a3657f1e478439ac0690cf3601d786f9781b6` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `cad727b4ec75a3e5efe552469f2e3830aa9db645ae576f5c727bbab6cc9656ca` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `a826cdb0d8fe12c587232e106e5beb0608285e53f9dcb45c837f7aa45329a8a7` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `7076c0ff8c62ef2105a0a9450815538865ed84738931e9a6969e2aa1f1024892` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `063098eb7b9a591af285443a55127d2184ec4990ca250baf5f7e1aa376f353fc` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `5d4d08c604bff4f9780246b167c10f356f627d5657b65630dd1bab1459faee6f` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `ca693aa2141989d73ece4998954773be82a31a5556a512f53a2a308e1c359105` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `74cff4f24a51c389b363942d5ea1737ec4dab43d4a45f0314ac47caa32c6df5e` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `3c4d5d817140352bce059f457a85ac0b6f494149714b6131342f9ed19188195b` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `e6621a3ddb1deefa1aeb18fb99c1444494ff8152ac3b5ffc98da1d887ded128a` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `227937c74b51f2ff65f53e85fafccbc3a2bf5e09e1d95a11083becd443883aa6` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `e36c78d15ca2dd80720fdbc7877b05ce0f0f5d3a19d21f98e8cf6c9691257ef8` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `75f9008d2b205744efd8dad468133efce34681fdbf628b5bcce18b5fd9ee1230` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `fd0fe8234d0eed4c7e46703af4f134d448588e294e4eafe02c102bf616aff403` |
