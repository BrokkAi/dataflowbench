# Scorecard `joern-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `joern-javascript-modeling`: `joern` `4.0.610` (build `joern-cli:4.0.610`, adapter version `0.1.0`, configuration `44faa326bd6f6b0d37fa963f4342d0e498bc2e617b34709a2a2e6e61aeaf07e6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-modeling.json` (`sha256:b560ae830e00453dbd7e089bbdcd005a93700274aeee0b1b1853be1820d6218c`, normalized `sha256:b560ae830e00453dbd7e089bbdcd005a93700274aeee0b1b1853be1820d6218c`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `2b188b5692bb9a649413c814e3904e2dffc5a5d0285462dd4bbafc6aab2108e0` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `3daef7a05c17a8feb46abad0d084c8c470078b2093c9efe53d19821c7a356386` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `09c2bec793e0476cbdcabe575f157a26a73040578d919f11de2a689fe672ff05` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `3931f2b977f6262ea1585efbb716b82f66309d949ef933b90a721760c77cd099` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `6babbe1f744f476e9ebcbe031bb61324e96f637c9d5de75d401f4b624224646e` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `cdb0cf61da9ec2b8bcf0229e9758e5d38e190dfb0168272be1938fd65b936191` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `eff3301389ef654ce57d0830079e154495b03df42574a27efe5791a1602ffbd9` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `6f3da5d81062a459bd9796e0a405fa9a277ccb3577d3e8112a96289b4ecb32b0` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `e083550668816c42cb703068f51d96092145c9ce4e0d12c0c3e72a97759bf011` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `8e9e1f84a6728425c057579fc2ad7f3561562f083a8f4f0385d09087f46a2192` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `18cffab6c7eec0609a29e39583fca39989c3c492214d29fca934ef358c07096e` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `daf216113ed866e1a2e3fa3397ec408acee04e3c013fc0c96845ac3609c328dd` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `be8b0b5df1ee609135fa16b3e41fa96624d9619a4a707c1823f6baf6c6784d99` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `2db3345311451ad810d24828359aa4c348d6dffdc64fb22afbefc2953be005ec` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `20bfe351a42d3c645f622082347896879f1bfb86c02fa472bcb4bb1ae7cdba66` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `77245622a78530e056bbebd1472bfc1b09309aefd0d59a030fd27670d7d0b8f4` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `5a3d795d161d901c12e535c4d8b935a4e2a659956c60c36589059c4291dec820` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `4ffa5a434ab3b2f17bd3346fe93a66c3b69ecf241562775fd9a20fcf192df423` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `512b6d32165a11166596fd88f6e4e7164d56d0a1531a89a9dad0c0d38b91da03` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `cdb6291831e4bfef84b65a35a7f5d17b6ed4a332ad8a56a21f16049379d08e56` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `eaa9e0730108761dc976572749f3d428736111399e2ae667993213e67a0a41c5` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `118185955245fa8a1728ded651e6c2f908d074f6bf3da72d351fe883a785bd77` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `3cc0fad43037e53d48e74291b0b128c8c01603c913b4a545c583b3c28a5a5eea` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `cd47f4d7fdfde095e4c9b36fe676c0df3d6c5cf705727d55f2827b3b7502e34f` |
