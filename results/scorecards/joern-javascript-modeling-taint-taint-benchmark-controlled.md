# Scorecard `joern-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `joern-javascript-modeling`: `joern` `4.0.660` (build `joern-cli:4.0.660`, adapter version `0.1.0`, configuration `44faa326bd6f6b0d37fa963f4342d0e498bc2e617b34709a2a2e6e61aeaf07e6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-javascript-modeling.json` (`sha256:525254f824b96e898df0f0d2d409411082bca75c9586fdaf2fa268bbef05de28`, normalized `sha256:525254f824b96e898df0f0d2d409411082bca75c9586fdaf2fa268bbef05de28`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `58ac18563bb5e89f951c45142785fd717634690318b192673e7fabe0b860c4e0` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `ed18551067d34d163e115a5745b5ca617542792f3ad45cb375253137e41894ed` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `549eb0cdfe4a0e369ab067e2dfbe37f588f8d34db4d2b0aba32797bb066c0c79` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `2b3e686c53c2daa4b1b2f38c074f489f27f00103d76acfa6017cdeee06b3e36d` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `58e3fbf6118a282847efcbda675366dc546ec69dfa8066a32b7d69370e75e2f5` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `10a0c89b22b2ee66cb50ca405d3805dd14fef8be59f8cd97c11ab77131e59934` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `16466bb85c30b4df1d131567f845a29ee34c2572c9810be431e9f8291d92b671` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `fd4bfec03f9abacb68728ceaea3307f6fcafc28040d326ab84fd629eb52cd6d6` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative.json` | `a3bdd9b771983900f4515c0fc5d9e516e5cc29bc6a5e3037f97b4b0da669e1ad` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive.json` | `8ca39a544b4ee1a1266c53fc93a255f4349885c8b1d7f830ec8265fe76a51b07` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative.json` | `dc481bc8c1cd13d04095385135bce74879266309610a332cefabefa3d7d4133d` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive.json` | `c1531f214fc70c725367d0b09c09ac05b5b52540ab7846f42a8b317df3c61204` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `c976737bed3a4709d58e91fa652705b86de682bc84752e29ba0488265e7803ab` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `db759a2a18076ba1fa7a7fb3ddde3ec36fb6afb7ef235d065976a867546838b9` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `573d80df19659f819cf2ea535c11bc01918ea48325e21efd9319d62a95991e6a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `8248f3b3f596d27beb9fe3b1b6c34dfbe3b66bd3e52e6501c5eb08ec590fe724` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `889c0b1a5eaad504378fe833ba3e0d0fe39d44bb87fcb346ba9bc85b2db4c27a` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `03f2a5e518be944d21dba74e418e7151b66191bf414a07eea5b8f88dff64da0c` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `0df7e0cb0ea2d46efb5e1aaa4083ffa1fccda9a04a90108470467a74bca16605` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `9401e3b0df868c59e5725743aa295418989d0d1a5d568e3167ff2ce84c774f30` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-negative.json` | `342f99f23d86d8a826d57a1e4eddc6e9552107e32fe177adc4ea488a17860859` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-positive.json` | `9f9b6d85b7fd09691dec87c4f5ac355008667d74c37151631ffa1582e4f23188` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-negative.json` | `a0d4653f988bf00337bd535ccfe6dfa75a6849c7c8bb3e904e14fa3df78d7733` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-positive.json` | `a8c5edf038c529a17c341d7fa32bb16b526c360cb2698c3272c83bc7a4f6093c` |
