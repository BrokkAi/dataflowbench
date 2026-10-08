# Scorecard `bifrost-smoke-taint-taint-benchmark-controlled`

Adapter `bifrost-smoke`: `bifrost` `bifrost 0.12.0` (build `676def6c6615002002b1bb9d25211ad1476a5b5d`, adapter version `0.1.0`, configuration `2c5ababd371ee6b9f4f0596c570d2378aea79cc2e21c8a3e7e0eb0a195f63911`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/bifrost-smoke-attempt-01/bifrost-smoke.json` (`sha256:bdf965769125bc152aee4517d61f240db245fdae06ed96d089a208511156e2f3`, normalized `sha256:bdf965769125bc152aee4517d61f240db245fdae06ed96d089a208511156e2f3`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

## Language `c`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-c-direct-negative.json` | `ff81b6f8942918560ee9e41868f64be23c9a0e7e41d187139789d91e3cb3ed72` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-c-direct-positive.json` | `67c08eb5c1b99aae66383a12ed9e0297226adb9348efd2ff356530b48d76a8ab` |

## Language `cpp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-cpp-direct-negative.json` | `8cb7ec7bc9a020c20bcb8bfe2f89b05e3a99e6b90763fbe02f4973a09d1b7cb6` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-cpp-direct-positive.json` | `2d09e1c405ffeb6a164b159db0a70856a5e608ce05ea73f638f7ac44696c41bb` |

## Language `csharp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-csharp-direct-negative.json` | `565e520a0e5de38d345a36ce0fa2a5acf0bbc377a327d8f0b8f5e58d22b1deca` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-csharp-direct-positive.json` | `fb12b79a41e5d71b999bfcedf38abb22943bc96b4322c0d5d61fcd7a35c854bc` |

## Language `go`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-go-direct-negative.json` | `c6a4ef29807d4ce57e7f1b9a80a4607b410e579353ee6c45635ffd62ab28902e` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-go-direct-positive.json` | `b0e249778463b6a779e7c36af736c6c3006cf78de7efdfcac93c0aea6d805dbe` |

## Language `java`, tier `calibration`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 0, `unsupported` 1, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-java-modeled-external` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-modeled-external.json` | `01be675e06e4fa5eabdeb5725a1e06efa319ac6156f2e492cd1689c69e29caf0` |
| `dfb-template-one-hop-relay` | `dfb-taint-java-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-one-hop-positive.json` | `b533bc6fc03eeb1de94d31d67747f256df11e7ab3c8391c004e1eb12a6c9d557` |

## Language `java`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-alias-propagation-negative.json` | `c1bd708ef8b207beb8c12f22d18c8079c8ba83e18ff068fff38b63f6696af5e1` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-alias-propagation-positive.json` | `ca59b1c96d0a7c3934251d9ca29b8d8468f60bfb7b089b181fb09ae3185977ad` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-argument-position-negative.json` | `1f73402cc80501dafc1d13865e96a3d02bb61ec29b43d6245b64c1babebb7a76` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-argument-position-positive.json` | `a999c6e1e0a864837b1b50beda93f94f0abafec7cc381ff838ead6ae5d109bcb` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-expression-negative.json` | `6571f1eaffff797204c9439fa2cfcb1b33ef1e8efdf319e3e3093f05fb644546` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-expression-positive.json` | `100f7e937e6823181bb5f2a33e227c473f56e2c660b296016b5771e4b7e760e0` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-array-element-negative.json` | `215ea2f36a54dede3e5ae707454ba354600f401f9b7480bef9b65cc9821c214c` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-array-element-positive.json` | `2f25bfd5d51e042fc70a41593ee9aeb3dda84a8767d1bdb2544ef2ee9be9efc2` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-branch-join-negative.json` | `25ed11ce70fd1beb7ee5315b72eb08a680f8073ef6deedcdd64b1a6ef2625a37` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-branch-join-positive.json` | `892220f68ade63aacb4e55a6c72dfce43155d8abc0a107a9fa037858632eda24` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-call-context-negative.json` | `9e0d97954483382c47e32c7148e109093625e1552bfc8fc89eeb0125bb7fded0` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-call-context-positive.json` | `dbbd823e051226f7e45f54ee63580b55f72d66fe2fccf0dfe67c5d74ffab3a54` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-direct-positive.json` | `4599400dad13eb7c6439ed16383f6b9a3a9a570f3a44d7dc0e30c7ac8b747f0a` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-explicit-negative.json` | `7aea794fd60098b2495801ef958c0c48b4cbdc0292b5c47d85d9c1e5690e97d5` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-exception-catch-negative.json` | `eff0606f6bf3690b3c5397cf0493753ca84b2f87f71895d6d8ba27a57e43b99b` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-exception-catch-positive.json` | `38278510b0a10c0d4a09c1cc9f56201f0a2c406050b5bead7fc3a3409c7b430f` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-infeasible-branch-negative.json` | `3924d347af320954d6e9cf6043212458b846a2de87bee0383449540b1f374d2f` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-infeasible-branch-positive.json` | `063ad2f191b60a288e139e261b1a5bb6a25c173cb10e979cf6dd9d3406d6701a` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-local-chain-negative.json` | `638a078ecb909f566937e6030178db800f3bbb8c1939bcff60c7f891861c5e73` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-local-chain-positive.json` | `3a98e494c5d61e9ba929756853621e61dedd5b3db7cd488590deb18ae08a3aff` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-local-overwrite-negative.json` | `de30e9697d8d14500b1421783f80b6bb9dc7fe49e7e647ea8e32bef5d16772b6` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-local-overwrite-positive.json` | `a44f5df647e9936c9ad855eb91878cd06881c82297860e9ecb12747b098f38af` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-loop-carried-negative.json` | `b1219fb67c7149d8281153f34827d0d46ed4377e8477df745672873c2c088bf5` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-loop-carried-positive.json` | `947776566f773bfc6aed2e39f07def28e9d8f5371a2c55ed9f1521e5d08c45e8` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-object-separation-negative.json` | `d5a7253ac978013e74eadcb036ca9c842685d25a7b6565b3948b7b6a7d1f4c04` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-object-separation-positive.json` | `9f27d6d50525c1245be1b4240713ceb45e7b577014a360d90c50a4c51841e17c` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-negative.json` | `f7218225b2185118ebe0e27528bf63739ca91b3d8a73ce17aa92481390e07d80` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-positive.json` | `006c5494becaba871cf74cad3c09d4ffcb1d90621f7a8f1bb88117fae00eb55a` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-negative.json` | `080b58e9a3728492ea9743dbc782912cf6f2c054559ea1b0c2f8c4d959db2167` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-positive.json` | `55e4681b54efea9a1b03693b2a9d5a847b3c7e7427f03162b341f2344bdea16b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-same-object-field-negative.json` | `40bf4003eb44156bda10eed47ce2e8770654c86684323b1d151b9931e50f0dbd` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-java-same-object-field-positive.json` | `89414d54f490742817a8062a51068d9c92dd3ea58d7a107ed3bcb3af7cf197a2` |

## Language `javascript`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-alias-propagation-negative.json` | `32c2129e6667c26915757c8e101882990232bea4636955b890acdcadd3aba3e0` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-alias-propagation-positive.json` | `724ebca5145f5241d0f7712dde0bbec184c52efb4e6419443c1510ede40899ec` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-argument-position-negative.json` | `413c1b02c49ed2794bf794c1b0e59d1b018a4397613283d6387ff1fe1c1cbd4b` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-argument-position-positive.json` | `482904542db78a388b3c621a5bd0bb85a40dcf68552ce2cb790c57293bb97be9` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-expression-negative.json` | `101d1cc3c42635c9cbc4fd43ef6a15ac0786736e6218688ed858566c3ec97a7a` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-expression-positive.json` | `f9ce769b2609671c0b0db2792f8f8bdacd0a182653a832014d4cbf8a7d20ac36` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-array-element-negative.json` | `5fd8fd54c3720d2487126b379134f296ca09e27c308d6cbf2c64c79032f09622` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-array-element-positive.json` | `73db7dd2e0890a7fac321346d4c943c3d17a68231130b48887de0cee3fcc6e3c` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-branch-join-negative.json` | `14d6831e1d07fa91d7497c2b2586dc9bb78e70d96fcb7f422f99e58f0478995d` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-branch-join-positive.json` | `6aa4c68d0880bbfbf969364eca4f0177de75cab59681525807df0030ba5bb32c` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-call-context-negative.json` | `36c63973746c1feae37be80974c3417be99a441e6bd399a04a4cb8982c27c64b` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-call-context-positive.json` | `586e2be39622cc8b4d36692a9f756890df2394d5c0772ac58f44ed7a4002965b` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-direct-negative.json` | `0c494b457d4735c6a2d7e797bdfa607c76a05f08548415c519f29a5a8c7da580` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-direct-positive.json` | `bc9cf8a1b8dd01678de894d78022895b0159041c2958a6f6d9674202527ca751` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-exception-catch-negative.json` | `6da1ce3762e230fef339d7b10da494b5dadde8bb05113206359e52f0608d5426` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-exception-catch-positive.json` | `d1a1c4fdbe50bf4284cbd2174f3fa41007f1bcde8c9d3d3984b779610a5122ca` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-negative.json` | `a78a530eee97ae9feafc56a78a6609aa8dc8b56a8b0fa9d2a1e3c63b0ef933ba` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-positive.json` | `b1cdc3d59027e60c0c898fb91cb9785cb2f7eaeed345caa19a441ac3694ca04d` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-local-chain-negative.json` | `ca3d28015dd808eee53e47dd0645d87ca05beb535fefdcde445b716cfe117715` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-local-chain-positive.json` | `655001d9f2a227c46abcf09329d4956dd6d7ced6f712bfd76d0c4d8f7f3397a0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-local-overwrite-negative.json` | `c92441df0cf29f88ede977d6b779fbe64c29d009082d41ba95ebca9f204ebf45` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-local-overwrite-positive.json` | `58d75b76463df71edabe9a6939c4d04fd24fa89c4822401238e62d4e2b0fb7ab` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-loop-carried-negative.json` | `17a410d2d5c68760dcad2e9bee17c8d1c2a932f48c95d6c9d5093fb12ffef261` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-loop-carried-positive.json` | `3fe4fa6668bcd6425cf8f0c394cf30230190e14712fc627c237d212bd49aa6f9` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-object-separation-negative.json` | `13b7247e7be04560df91d6988b529bcb5d0fc380a4dfabd2fe58e34d97f4836f` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-object-separation-positive.json` | `7404f1815f39575ad51945013797ab1e359cc43b8d4ad5bf5b924f60530324f0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-negative.json` | `357af8b51f0d625780f68cc9d48a129d04bdc3966f9233419412343047ef671c` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-positive.json` | `154fc99399b52d486b6d1f8021c8ce05c87c969f7638d2c1020c7921bebeedaf` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-negative.json` | `6a183a298b2353eadc9d210318df04ff8adeb7dd3addfdd0f6f5fb9bb29ec43d` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-positive.json` | `bcbd2fa8405d6d7c4363652a546ffaf88fd558a61c632a2f7fa40d9c0dbe8672` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-same-object-field-negative.json` | `d76af1a528edd7d7add6f76b074faa19687ca071572d6ee23db0933bf93b909a` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-javascript-same-object-field-positive.json` | `2acdfb9fbb7ae616729ea7f1315ab47ce0040f5875f40a31f9dd3c0493a2e94b` |

## Language `kotlin`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-kotlin-direct-negative.json` | `999c650ef04652c666012135c3a95104c7647cac81acb6838923bd007b952c60` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-kotlin-direct-positive.json` | `a4d01ebff4bbe7369c1accca829cad52b7c6b93c18620be2a9babb91d8c74991` |

## Language `php`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-php-direct-negative.json` | `a002a4cbf8ab05b88b346a8d82a93687baf52dace663c44d827001d6aaf004dc` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-php-direct-positive.json` | `88590001e77e02a61a39f75b2740cd254361838a2f395f4ffb403c5b209aefd3` |

## Language `python`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-alias-propagation-negative.json` | `17bed7ffc9ad1f497ba630281ef5c2a162a4d07653a253b46082e981cbc94ffe` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-alias-propagation-positive.json` | `957f0a02fff906093076918115b9effb78721d688d62d2075f842cace0cea192` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-argument-position-negative.json` | `656fc4b4615625efeb863ee494321680b13b3bd049251fa687283659290fd5d6` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-argument-position-positive.json` | `cd9838dd5ca7a76bcc4e9fe0dfe4fdfb1912e6d1e93b2dddf1b81d08722772c7` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-arithmetic-expression-negative.json` | `7827cd05212063449f1f875288f010e96ecfe94a301c39e7df809e94834c4918` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-arithmetic-expression-positive.json` | `c916b99121ece7151425bd6449cdb317ea983debf096c887769119c692dd3028` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-array-element-negative.json` | `fe756cf703803efb44ed7c5cb35dafde74aa5c7b5d92343f9b2520b25f787275` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-array-element-positive.json` | `8f583d6dceeed8901773dc3e2a719c080fbdd9087301f16ee7a515c2fc045198` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-branch-join-negative.json` | `d8aca086f29f878084d21b55d1e19253a543908b6b90390f772a61c86f157478` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-branch-join-positive.json` | `eb6df6bd44c116b81118fd76d7e102aaf57701cef6465e0648ebb1548a7e16e1` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-call-context-negative.json` | `cd3b31ab5417623d39fc49d686e378cfe5fdf8da85de49c4b85e938cef84a75d` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-call-context-positive.json` | `3d9d350e30b870fddb83c16c6ed434cbd7c6ce7b3634f388141973744df7ca76` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-direct-negative.json` | `d2a6d74d3a688feed5e18e8b4c25eb86595fcd8f9b8aff4788605402820723de` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-direct-positive.json` | `f31827d7dcfa129be034933cbb97670caacfc5d53021d497e09ee70493ba9675` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-exception-catch-negative.json` | `2dd6aa98949546ab9648830efedda8576ead1b4f32a4c20507312be466ae26e8` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-exception-catch-positive.json` | `53717d224fdfc6933de2c966b3b1560b2c4aaf8f53f54a58b533d1f740e6ae1b` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-infeasible-branch-negative.json` | `e3113752a26c9628be41ece85fc94cba217c8f19cff15243eee77e896a5c0aa5` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-infeasible-branch-positive.json` | `703e77a3641a64af7a0551556cf58ff7ea9b023302e5a29e2132a5d15e850a00` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-local-chain-negative.json` | `583f97f021f768104b767b968a905617e4c2e1662dedd4d570ef0726ffff66bd` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-local-chain-positive.json` | `e2e1be8a8f2df8fe6eafc9290dcd543df677f14b1ffdec4b8a05323b06912bd0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-local-overwrite-negative.json` | `3268bf861ae5d7b66e51f8651e0262eac4737d7f3e71a947325c9928d8db0db0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-local-overwrite-positive.json` | `805133b4b70b139d68dd30ad13810d3780599fdcee6199a510e6a61ffda9a9e7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-loop-carried-negative.json` | `cc84bc259378032b5213f55d7162402037ed793081c9d87dcb5cbfc0222c4de8` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-loop-carried-positive.json` | `6916fa711149e6a996ab7a857ad0ed5684cb0009a67abe1d8237432a52d69465` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-object-separation-negative.json` | `da5237b8134972e43b06d8f5e7e5b05b568ac122e9c103e2024020867f379304` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-object-separation-positive.json` | `73479305fd2a3fc0d94ae314dffd9b990a81e3e966c225e52039d73140350047` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-negative.json` | `67d6d0341611d752458ef574711967eaab34a557a46ecf384f2f94c2228b399c` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-positive.json` | `979fda268ff61c44d5cd6160d253b484300645f5347ce1c2bb80bd44a1d82945` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-negative.json` | `cf9034d7fd27e4f5f594345a9b3081b3550dca597115025ce29716f8d01836db` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-positive.json` | `ad25cac7dccb6e0e12e68480bca8c44e9b57e2085f2155d37887403ee0c4e600` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-same-object-field-negative.json` | `34046aa1f1b249601b19ccc15703230aaea3b9f1c5adbadf855374a18f6a0cdf` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-python-same-object-field-positive.json` | `66900349f25788cf59789aec5451313bebed9d1c80d1274b86e2c09ba26a6c4d` |

## Language `ruby`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-ruby-direct-negative.json` | `6e9bb68456181d4f0f11965c625b669a7c06e97e62f4f50633da556efc9a707f` |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-ruby-direct-positive.json` | `f89e95add83f03447a399abdee2192138208d4252a14a096e6169d043e24d778` |

## Language `rust`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-rust-direct-negative.json` | `9873cb225a942be5ede1d72fc4a97581aa3ca84193bbcbb865603309f1db4859` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-rust-direct-positive.json` | `68e21999896181fd88bd8e4141c3fd9975b3f2dc484d0f2c6f6e6c02c64f563c` |

## Language `scala`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-scala-direct-negative.json` | `25c26cdac965c53472b66214a85cc2588975c38ff6ee1fffc121db12590458c9` |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-scala-direct-positive.json` | `9126e709c1a8e4e2685dd09a545701ed5c76256a79e1ab28256c425a781ddf73` |

## Language `typescript`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-typescript-direct-negative.json` | `3d2008f0ad668d0de8470df30cadea0d93a8d189f2fdf17c07db69a12784ec13` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/bifrost-smoke-attempt-01/capture/reports/raw/bifrost/dfb-taint-typescript-direct-positive.json` | `56aa04169e72527610f520becf5ea1fd520c601f3b31fb97e95e8f3dde0c1f86` |
