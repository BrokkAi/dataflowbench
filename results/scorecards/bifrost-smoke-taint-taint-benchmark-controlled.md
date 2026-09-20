# Scorecard `bifrost-smoke-taint-taint-benchmark-controlled`

Adapter `bifrost-smoke`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f`, adapter version `0.1.0`, configuration `2c5ababd371ee6b9f4f0596c570d2378aea79cc2e21c8a3e7e0eb0a195f63911`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-smoke.json` (`sha256:a81a64ccd798b133c87da64cfb837bbe9a76a3b39aaac00509a2082a6bec0600`, normalized `sha256:a81a64ccd798b133c87da64cfb837bbe9a76a3b39aaac00509a2082a6bec0600`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-c-direct-negative.json` | `ff81b6f8942918560ee9e41868f64be23c9a0e7e41d187139789d91e3cb3ed72` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-c-direct-positive.json` | `1c30b369b11c09007582bb028ea99da7c29930778b49038f6b7396677472f3c3` |

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
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-cpp-direct-negative.json` | `8cb7ec7bc9a020c20bcb8bfe2f89b05e3a99e6b90763fbe02f4973a09d1b7cb6` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-cpp-direct-positive.json` | `ab050b32cf9765f8ec62a2136e98b9766d6715a8cecebac8fd796cbc9d70fdd8` |

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
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-csharp-direct-negative.json` | `565e520a0e5de38d345a36ce0fa2a5acf0bbc377a327d8f0b8f5e58d22b1deca` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-csharp-direct-positive.json` | `09e72d5dbc73743c1a903f7e61d95cfd41191dcb9a3ba5f189620b6eaf34216b` |

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
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-go-direct-negative.json` | `52e53aff89430755ef5b48cbf778ab1fd6dccfc15888d02373b0cac0c75f002a` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-go-direct-positive.json` | `059a11bb5dd2a17db94afd5990bbe8c6ccf9b7b1571d9a2e359c0e90ab817741` |

## Language `java`, tier `calibration`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 0, `unsupported` 1, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-java-modeled-external` | positive | `unsupported` | unsupported | `reports/raw/bifrost/dfb-taint-java-modeled-external.json` | `01be675e06e4fa5eabdeb5725a1e06efa319ac6156f2e492cd1689c69e29caf0` |
| `dfb-template-one-hop-relay` | `dfb-taint-java-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-one-hop-positive.json` | `42d585479f493c72862741aacc9d84708a43985e1a701ef704760957a6470848` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-alias-propagation-negative.json` | `2bb655ce1fad6b8ca635a015944a4a9a5e78279fb6f907bb5718c6359376a27f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-alias-propagation-positive.json` | `b93c5e6cbc85f43af314b4546d4205b380b162bb0fe61bdae72716c4b576c108` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-argument-position-negative.json` | `48a78e11e851b8204dcbaff0424489a2e269765da3721879ae230548685fead8` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-argument-position-positive.json` | `786b24078643d5838c9ae76d3eab719e7a23204646b15d1b07f9151200228584` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-expression-negative.json` | `7c3a3d9d6def20dbd424830d6caed5350589f05c8bead15adbeab7e154e21d7c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-expression-positive.json` | `a362fb69c527276295b2989cfec16f736ec6567762b70616a5ee24d232033499` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-array-element-negative.json` | `4b72f5929a9991073937c1e5b2c1909d62615cf3902791f8583854a04d0edf8a` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-array-element-positive.json` | `474f90dc85f4b08721845c4a5c093cbe870219b42a3246de73ee5db488d03d2d` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-branch-join-negative.json` | `334a7ca8531959210114101dc48f20f97d6114387f4d5bc8ee65eb2552c981e5` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-branch-join-positive.json` | `b10fb468a85fe21847782694e8f36cd5edec010a62334aca38e72b0c5599fc3f` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-call-context-negative.json` | `c7f75a273517b5bb680fbfe20de30439cec807d8f173125c50a07d5d637a648d` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-call-context-positive.json` | `7ebe81930c5d26431418710df3fb1a088a492428370cb6d287ea6ff120e1e3a2` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-direct-positive.json` | `02271349559227495d262731d13c801385483016e9826346da8cdb945d23a0e4` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-explicit-negative.json` | `3d13509442cf8848a8a5ebe4e2aec9547f95553fb9e3742628666fadb7a839e7` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-exception-catch-negative.json` | `0fac3eef2ea6ba8c4c6af0b78271c988aba1a950bfb23484de2813db82948808` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-exception-catch-positive.json` | `abddae7cfb70732bcbbead6cac47ad4f6ab2f359e07e55d1b5e55596df3979c5` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-negative.json` | `bc0ad744f870beb2c5059d426ca5fc4f2cdb735df025cbd712f9f58a885371ad` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-positive.json` | `5028bb7110ece9e8b262e3d7968b4128cd6ec8374fa382d96ccd3f05d7bfe5eb` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-chain-negative.json` | `4ef88f91a75d2f376df883ffdc94e7ce80c3c192765abeea640c77f2c496bd04` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-chain-positive.json` | `0b54225e10a4341c630e0a955e2d897a7d94e4dc10cfa98c8e0c809ccba6d03b` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-overwrite-negative.json` | `fdfacc5164f71a7bb09a57500bd73ed089d437c3d44e17bb4cafcd9ae8d13e5a` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-overwrite-positive.json` | `51e38a129dd27e0dd3ee3208840a43117ded1695e76abfc2a4e59fae84784266` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-loop-carried-negative.json` | `5d1cd2848ffbae132b0cd34ee82151e23c08515bd3208b4bdcbb0121182cee67` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-loop-carried-positive.json` | `cc4e3e90be9a30654e81675577eef4cd2adc03e2747ab4542935bdafba713d8d` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-object-separation-negative.json` | `e00acd9d86c26070f48b3ea864d765ad2fd55a4a4601069cd72ba0291e85c834` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-object-separation-positive.json` | `8777b1c85a235e2fc27ec0b418ca7ee148c03d8e609f1d52bceea9f105b76994` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-negative.json` | `c6753238f446cb910a8ddfef86bd694980baa902b9f19afbd3e4d2ba7ae72cf0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-positive.json` | `3079da0518ba9142ff8da4b4463b2af66a96745797d19930caef630fa8bd3c55` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-negative.json` | `3ce3850a6a9767f4b68d1cfae4f94a420866408274ace99e9579302e0292af40` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-positive.json` | `1c0e3eff8978f6b2db68548ef717443796fba14a9898ececbc184e4bcdfbc68b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-same-object-field-negative.json` | `1f1ac64cc2fb2567d2b960e69ed965d473620a0361b7f5f38098a2069e285cc6` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-same-object-field-positive.json` | `43ab8732ae17a5339305d68878fda66a20da5df8556b4c5f96a8f05174b2e0c2` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-negative.json` | `30b905f5ac724779311b8026985f1917a42f45d8ee3378399701ae8aa92c88b4` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-positive.json` | `cc0388b0b0cd1b200b7719512e08c17dea7ff5ef71f73e5f85d416ed27b2ad3f` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-argument-position-negative.json` | `0cfdeb3a747a1c630dc394cde49d98008e5b7c0004eb002e2ef0580edfeebe74` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-argument-position-positive.json` | `90e9edcb103da14802282d083c3edeb496d2fc14880ee214d5df7ae0606c2de4` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-expression-negative.json` | `8bbfc890d7caf1d5802a4674bf28118c76039f1b92e07923d784dac6ec9bfff3` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-expression-positive.json` | `af3cc1e1ec4d290a46c7a9af5d7dd393901762631f2c691f234454c5cc3b226c` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-array-element-negative.json` | `3b729c01920efca0fb3f2aa48aa10f875e567bc801693a3c8818f5b2234ede47` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-array-element-positive.json` | `40ecfd5fd1e3f54bf957d409d307dea4b0f735adefe99cbda9801411694d511f` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-branch-join-negative.json` | `b98397674b812bc80ee63142e7a9bada4e53950227472d388960aae3b4176e89` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-branch-join-positive.json` | `9898ff3d8eae25a2bdb81161cd2a935e0fbfd2da07c764182de792c34c5a7d6d` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-call-context-negative.json` | `7a674b4c63d782d1a9dfda401c785c06bd26caf8c7e65cf6f32ad403539d9850` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-call-context-positive.json` | `c661736289490722ce5e7c7a9fb040b63bc65f5ee42d48f99348715fbb5c1a75` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-direct-negative.json` | `b6de68a743a40d334dbe06362ec0f41e4b3aaf3be01c5ff8f865d8ca4115464c` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-direct-positive.json` | `ed2db0fe474e793edd882a5be8296d61045e97b91e61d79ba7334b9b04b8e9a1` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-negative.json` | `9f014c78b806f9594dcd577b72305ff9a8437a37f187a972ad73126f229970ce` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-positive.json` | `e2229ce93ebfe620eda709c035aaee1bd68ce1e10436e421b0bbc57c0384068c` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-negative.json` | `d937cde88e681de774a364a056314b7df96d93f0e03bf4a9ef5662da58261b49` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-positive.json` | `ffd441cda9c573aa0dc72bd27ee01c541fe0b02f10d38e092ede1cbbbadbe85a` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-chain-negative.json` | `f1427ca4c6f4d9340d22113230b1e3153caf48202cd0223e8cdbdb9ffb46dd8f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-chain-positive.json` | `645463d97712d2eb7f8ae06300a11eac090fc8055c77fffce92d16fae06d72d3` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-negative.json` | `0aacad40f077603de163be8c24a241d87a58b7c9ac15b91d5ce172b55f9d9cbb` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-positive.json` | `13bf7e9c8a96a9cc65c8cc871b38e38e1e78df2911d991572090bfdf1bb62a71` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-negative.json` | `e16350ec456109e5b213a98c68b48622929fb26da9217658bf93f3c5e949521b` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-positive.json` | `75c750cd6b1cb767cf27d63fc0182b0fd8504466f711205c0959cde5ed523482` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-object-separation-negative.json` | `45eb6d3d80c99df27eef201ae0c60d84c5aaf02403b6aa07c1a3a3de5faca904` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-object-separation-positive.json` | `82fc21fb539f1e3f74020e0266c0a3c799fa46e92948eeb2aa5187ebf2313cbe` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-negative.json` | `723753839b5bbe49995dfcbc7a7c75c86fd3385d7992dff3fd285c525a5c73d0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-positive.json` | `656f16384c9a109d2532f8defeec60ed0687a2ea97c8af02f9cda003a3380630` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-negative.json` | `3b389bdfc57fb4f090a00d3967a02f3481d6396f9f1dd5247cdb64fdb807be64` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-positive.json` | `c8ed8c9836ff9c66fd4e4594abeb7426ad8d0ebd331d5af619a9ad86cdc7d81d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-negative.json` | `f65f256da06d80e0f6c5f8638e8fb04eadc8db7b76ca766f9089dc9d83255337` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-positive.json` | `834fc917520fed3fe0ab9958f8ce7c2ea7df7cb140be61ae900c9410964566c2` |

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
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-kotlin-direct-negative.json` | `cdef89fec46828a213ca1c6603a083ded253e1fb6a3ffdb0e34f3ef4256ad19e` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-kotlin-direct-positive.json` | `cefed1b358a08c7ec4b0d8cf9cb908b67f1d9b57de208317fa1261a67ba5a948` |

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
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-php-direct-negative.json` | `a002a4cbf8ab05b88b346a8d82a93687baf52dace663c44d827001d6aaf004dc` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-php-direct-positive.json` | `c74fe42197d168e85afd1cd6f91d09628d0852ef46e549c00311bf892ba8a328` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-alias-propagation-negative.json` | `0f9f2293228b489811196754d1354b4827a7bc155d51b044fb8796863073700d` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-alias-propagation-positive.json` | `47db524ceedde996947471d5252c489a02ae5122bd56deecdd56024f6602c5e1` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-argument-position-negative.json` | `ac99c84de9994e66819f4c4a648f3567e1e8e8f60f253b949ef3669f4d949679` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-argument-position-positive.json` | `2879dae1527cd3eba09ce69e6ae21fcdcffc07532269fa87bb0e520540491d2f` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-negative.json` | `a5ab229bc4de0f441d8d9950beb860a158ff2b0f8f6d19e6a79939af581e1469` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-positive.json` | `e1831df8dbdb0dec48b3ff620ca55535d1d0ff7a0b18526e2cd8237da9dc16dc` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-array-element-negative.json` | `124b0d0b8bf3bcb884a55ff34a613f04c8a32121c573bfc6c292edc0b1153a43` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-array-element-positive.json` | `66abef07a9a870db15ca6028cb8b46bbb5c93a8d57320c1147a437c7bc71456d` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-branch-join-negative.json` | `c811100bdecbde657e4b0324eb3897e2d18e5b7cb0607f40b3d4b52efa6efa5f` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-branch-join-positive.json` | `2ab4344423db1b30c9ce62cc2074c2e4634e29a01b2f9566aa908d99442b89b9` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-call-context-negative.json` | `77f0dfada88c40bffae0530a2c268e288e142f3cac0d0474cb26155ffc368010` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-call-context-positive.json` | `62aade7ce688f1a2dc7750d0219aeeb25712f9e489e12155907ede2176e4e52a` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-direct-negative.json` | `5a9d83cd3bda980ac23e41be984f6d8ac9fc8c44442cae2bdccd520c116e5c79` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-direct-positive.json` | `4118e0efcb3396481386a9b9496ca23f98f59651318b7a656290160b7b5d63fa` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-exception-catch-negative.json` | `5de17e68e5da4e5fb8955a2b2805684adeae6079e7b3923d2549ddfd3e043dfe` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-exception-catch-positive.json` | `57959522e87fcf2136f9842b8fe6a3154d5b6843b3fcc3388c0d4641f8574c40` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-negative.json` | `58511aee657598e65dacc0732980681b6662e7beb6d5aef18ed8f7fabde60d8e` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-positive.json` | `9fbfa9e06c7c2b4682cec8642da3c45a70aa90c295e8ed6eb72ec20ddd5474c1` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-chain-negative.json` | `cb65788126d9dcd4059c1d5fdc21da993359d078d7619f9f3064c8e82bcc86ad` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-chain-positive.json` | `50772bf643b33df63a9599476d29f7d7a85a6de9357c518d090ba9cfb742c6c5` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-overwrite-negative.json` | `0ef8751cce61c0e81f7e14e828eaed5abd71118ae374765c0690b1fbe809da89` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-overwrite-positive.json` | `ac9ef2c9c10a8d9f5ae9a24983e960445f510450994ade8318eb874f27b8e957` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-loop-carried-negative.json` | `793c5535d14fde212f44cd851f339ab5411b65b08e66d39af8b07820085c7c00` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-loop-carried-positive.json` | `f5320cb178651352c844a9427b7b4b6826399c6881a4a2b866f740dcf9c2ab20` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-object-separation-negative.json` | `ff963fc6a1090a40f4cc820a0bedb85e64cdfbe3d372d8b505e73924d79eb392` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-object-separation-positive.json` | `efbd6e1f161999a0a72c0c342bd77e7dbb4806bf3181cca1f7729140fddbc0c2` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-negative.json` | `67fe4c8296ebaa4027dd3adfe89d202f106d97f55fb30ea2b9298c9dca6315e1` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-positive.json` | `183a8c108a3bc445af298374d29fa750858f7b7f40ce62de5cb3aef17467c436` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-negative.json` | `47a81666b0acce5cdf7a59212acd9f41307aa10b7f12236ad606f5320ef20eb7` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-positive.json` | `fc2313d9d1917e3f2a2feca2ee1a4448487dc77c6a494a2adeed7ec4fc020cb9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-same-object-field-negative.json` | `8f2e437b3f1bdc60e047c5368666a068106769374509e05dc84dc18dd770fe0c` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-same-object-field-positive.json` | `e241b94de77c8045515120f15df11e3adfbf52ac322ca4907f24f914d825ed33` |

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
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-ruby-direct-negative.json` | `e3434a323a223570d56f87b2da2086d1b0ee7f94381f1c663f1e69396e0c02ed` |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-ruby-direct-positive.json` | `00198a72f98ec0a5fe7ea469fc1bab6fd7b82fff46ae907d9b6512b80bbbdad5` |

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
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-rust-direct-negative.json` | `ddda2cbedc86824788d6ac2854114356ca89f6564cfe99a0fad9f110361b87fb` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-rust-direct-positive.json` | `91526c2f542c00e8ceba838620d085aa62ec1e6405c88b950a355fa1f1d5e300` |

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
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-scala-direct-negative.json` | `18909741147b8f2d6584ae2f4c1d69eabec7f70caf4211925847dd2f6143415d` |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-scala-direct-positive.json` | `4f54d390f783109e4baab706c298a5410a7000d2157d05038cef94a0fed8f962` |

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
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-typescript-direct-negative.json` | `d7c7149eeaad46c5c6c21810bc176fad87f45ca8742d48cb7132a9ed7151692d` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-typescript-direct-positive.json` | `bc85639ab096f3d3a6573cc797afb9ce433b4f370d2431caf497d0387194a090` |
