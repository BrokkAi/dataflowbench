# Scorecard `bifrost-csharp-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-csharp-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `f08e35507c55aad155ac8f5e8fe587c4b48ebe507efa4e73ca671ef2bea20098`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-csharp-kernel.json` (`sha256:49ba511fc4405220f716bfad3b57d81d0c9cd724ecba703b94f117994b9e2b8a`, normalized `sha256:49ba511fc4405220f716bfad3b57d81d0c9cd724ecba703b94f117994b9e2b8a`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `csharp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 30, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 1 | 14 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-csharp-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-alias-propagation-negative.json` | `a848748e8514322564f717bee999392c6b80215961d2fb94e0e96922d927e70f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-csharp-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-alias-propagation-positive.json` | `c5a0716f82ccb0af5fe3f7edf83209763235965c3ceed65c1ab5af677f79d143` |
| `dfb-template-argument-position-separation` | `dfb-taint-csharp-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-argument-position-negative.json` | `f6ff33a8aab1e27230edc140636608eecfdcf80d814e2c1bc9001124d82d0cf2` |
| `dfb-template-argument-position-separation` | `dfb-taint-csharp-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-argument-position-positive.json` | `a15533797a58b1b0538c63a89790d59bb39bd06e0d431f25a4a64ede284099a2` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-csharp-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-expression-negative.json` | `98d19bf48a09ca66b93a726daa2a819a259d24c5f87e06a59945725e27d13b57` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-csharp-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-expression-positive.json` | `19b7e3c32fd30a1dd9cc04babb3f6189cba7b9106a2f1e2e663ad26966ba8aa9` |
| `dfb-template-array-element-separation` | `dfb-taint-csharp-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-array-element-negative.json` | `38855d255c53b2f691ff39a69783f58766c1bb04920f8028e8c3f4e9c80da416` |
| `dfb-template-array-element-separation` | `dfb-taint-csharp-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-array-element-positive.json` | `d77773d89885f0df144a413dae42e350c801890cf13ed4aeba4dfde2f1d06c71` |
| `dfb-template-branch-join` | `dfb-taint-csharp-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-branch-join-negative.json` | `1e2d130aee0bb561a9cdfcb7d3339fb9b7a296f3ea01726a53d69e6cc0a74b08` |
| `dfb-template-branch-join` | `dfb-taint-csharp-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-branch-join-positive.json` | `64ef8a2fff7e70accbc29b3091e49a66f3276d1e8fbed85d49fcdcda7234610c` |
| `dfb-template-call-context-separation` | `dfb-taint-csharp-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-call-context-negative.json` | `bc1f58739d425e385b4406ee4b03b3a794db3644f552255545d4ab49ed49fa53` |
| `dfb-template-call-context-separation` | `dfb-taint-csharp-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-call-context-positive.json` | `d7a967f6adc73fa684d5515a11bf8d30026a2f701146e0f55e910f8a6e698843` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-direct-negative.json` | `3c405efeb086cc2dce5410f515fbd14c04a3ecb3e19d8451d4b0842ce6fabb0e` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-direct-positive.json` | `de0f1f06f4417d137e9daaf7eb74b8bd30d3fab8eb02c55376e6bc8abac057ba` |
| `dfb-template-exception-catch` | `dfb-taint-csharp-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-exception-catch-negative.json` | `849901b007518b85a73f550cf408b0456a780442f1cee0fa857df7e8950d59e8` |
| `dfb-template-exception-catch` | `dfb-taint-csharp-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-exception-catch-positive.json` | `3da8d9db98101813149bca49d135c6c09e85fd9d5d2a516f94066151b9d8c827` |
| `dfb-template-infeasible-branch` | `dfb-taint-csharp-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-infeasible-branch-negative.json` | `2b2d07294fbc749e353f7c2514db7a4e0dff16e7adf9a588d479440ca3b586b9` |
| `dfb-template-infeasible-branch` | `dfb-taint-csharp-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-infeasible-branch-positive.json` | `6dd4a6463a658529c4f1c553b5910ff10174acf2e8fd911a7c7b516f5265f306` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-csharp-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-local-chain-negative.json` | `8f3e90b0334fd1ba7618f65ba36d9edd52cca2501566d65bf6a1bb856cbd6211` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-csharp-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-local-chain-positive.json` | `07dce87959640b5e4e2ff683ed95add2a278f303f38b61d6f075d9a1fe4ebede` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-csharp-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-local-overwrite-negative.json` | `fbdf4fe0c5b880db1903170e269899d54474ea80a2ac9db2cbde8b619af6a63a` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-csharp-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-local-overwrite-positive.json` | `1198963b55a25ba26a46ab1f3a6fe1f86da0a23d797c8e992da51a37d62dfd5a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-csharp-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-loop-carried-negative.json` | `dda2d6989471aa613d1b2aa9a68017db8e7abcbc75d98785ee95377118fc86ab` |
| `dfb-template-loop-carried-kill` | `dfb-taint-csharp-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-loop-carried-positive.json` | `c1a5f51ab86c8e6448847bbedea5dd1d6476286c9d80973ee80717163e4e35f4` |
| `dfb-template-object-separation` | `dfb-taint-csharp-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-object-separation-negative.json` | `1873e9e5cc4f031208714e9ace07340653ded1e0d16d0fa336f359ffd8efa48a` |
| `dfb-template-object-separation` | `dfb-taint-csharp-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-object-separation-positive.json` | `fb228227fd0bfa654762db30b4f92e37dd8b1cb1299a67841c284ea21c807f45` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-csharp-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-return-relay-one-hop-negative.json` | `d8c009138cb3c66b19da987533a2a9ce7d251a7a233f3c27d9f394a7cd376299` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-csharp-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-return-relay-one-hop-positive.json` | `6b2fbc6ac9fb24175f1a00ee798005cc1dd4958eb6fb6cbb5f771d795d59c69d` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-csharp-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-return-relay-two-hop-negative.json` | `ad7f539bc18f49ddecaf5c7b8ae0b9e125916cf401b10ac2c2af539296f08efb` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-csharp-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-return-relay-two-hop-positive.json` | `5d02c5abac3458d02d6a2a17bb68899736376e13dd81e582cc884aa0c15aa42f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-csharp-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-same-object-field-negative.json` | `08a827a05a29a5c4c954ee544eea01546236482c6477768fe87d92a6f0044e91` |
| `dfb-template-same-object-field-separation` | `dfb-taint-csharp-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-csharp-kernel/dfb-taint-csharp-same-object-field-positive.json` | `06f572f472f722a7d44e1a06d6bf81d46a621128386b6846ff171034fec1bec8` |
