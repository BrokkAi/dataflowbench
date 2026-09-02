# Scorecard `joern-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `joern-javascript-modeling`: `joern` `4.0.614` (build `joern-cli:4.0.614`, adapter version `0.1.0`, configuration `44faa326bd6f6b0d37fa963f4342d0e498bc2e617b34709a2a2e6e61aeaf07e6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-modeling.json` (`sha256:cd6372a8fc9b462a51a460e23d344103bae384fe92cbe4e37ce641686c265d36`, normalized `sha256:cd6372a8fc9b462a51a460e23d344103bae384fe92cbe4e37ce641686c265d36`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

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
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `c1175625e3b901b1309b0bf2d9e26c3bcaffaa18c1965f4227206a48f60b6c94` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `ffba90c84ba590b16470f7db70f9fd52255bb315dc9f8c42459edbf4e10db98e` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `13ceb18c7e65c300de42c6733769960f0cc5b72a873dff5adfd0a4b40fc49b38` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `33756e2761d845bce00fa6de4d0dd6660d624ec1fc1fde6e091c7699670c7c71` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `be8b0b5df1ee609135fa16b3e41fa96624d9619a4a707c1823f6baf6c6784d99` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `2db3345311451ad810d24828359aa4c348d6dffdc64fb22afbefc2953be005ec` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `20bfe351a42d3c645f622082347896879f1bfb86c02fa472bcb4bb1ae7cdba66` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `77245622a78530e056bbebd1472bfc1b09309aefd0d59a030fd27670d7d0b8f4` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `5a3d795d161d901c12e535c4d8b935a4e2a659956c60c36589059c4291dec820` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `4ffa5a434ab3b2f17bd3346fe93a66c3b69ecf241562775fd9a20fcf192df423` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `512b6d32165a11166596fd88f6e4e7164d56d0a1531a89a9dad0c0d38b91da03` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `cdb6291831e4bfef84b65a35a7f5d17b6ed4a332ad8a56a21f16049379d08e56` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `62de810f8c8b56d066ec814a1a98e39480ce18375033c8876c1d004bc1cd96e0` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `e9049bd037c01b336db402d2ebc9776d8320ae3321703be9f7ec7715f31a9951` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `799d5b949a866dc685cef02d436d2ba29f3ad146c9e0e85c62210bb238afeac9` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `6dbb994b4296228f66bed3066d1dd4d12372365f9d6121d8a45e3d6d09fdaa5e` |
