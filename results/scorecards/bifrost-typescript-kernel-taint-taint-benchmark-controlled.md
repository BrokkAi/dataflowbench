# Scorecard `bifrost-typescript-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-typescript-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `5b2489c75b433ac15ed6656d43394a17851ee5347a4b24cf00c7dff3531e3b26`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-typescript-kernel.json` (`sha256:c294408bdc3c9aedfddf5217144147c9250d0b036f541475e3d748cd0df2eaba`, normalized `sha256:c294408bdc3c9aedfddf5217144147c9250d0b036f541475e3d748cd0df2eaba`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `typescript`, tier `core`

Outcome coverage: `reached` 15, `not-reached` 15, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 4 | 0 | 0 | 4 | 2 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 2 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-typescript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-alias-propagation-negative.json` | `6187b10110e74d5c5c1b07f588f809c005258eddea4e4d1685dcfc7f0198c20d` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-typescript-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-alias-propagation-positive.json` | `835086dd8657ccac8f4014e18f9ee4681d86dba12d602bce3763510b9ee7c822` |
| `dfb-template-argument-position-separation` | `dfb-taint-typescript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-argument-position-negative.json` | `85c4163955f9ec52e66e1922829d656f302555bd8a5660e03bd01241a1a7c872` |
| `dfb-template-argument-position-separation` | `dfb-taint-typescript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-argument-position-positive.json` | `cf6e0e957df10653657c7362df0b3a7da2ec474c55fb01281daff86f4be47c2c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-typescript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-expression-negative.json` | `6ab2d698a7a0d7f5d6aa3d419d780710703ad31dcddafa82998dcb6a35d487b1` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-typescript-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-expression-positive.json` | `d942311573fa43a8158394a9a65667952b9e7983830678dca5109f98b10bf32a` |
| `dfb-template-array-element-separation` | `dfb-taint-typescript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-array-element-negative.json` | `e2d8788b3b9df30308c6e116c43bbb4b2915bcc169d9846bac9ed8cdbe1216fb` |
| `dfb-template-array-element-separation` | `dfb-taint-typescript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-array-element-positive.json` | `b0ed4af2daa2601a85849aa0a0652bd8d23f295ddd68e413f66188809cb34029` |
| `dfb-template-branch-join` | `dfb-taint-typescript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-branch-join-negative.json` | `7f3e3ecafbd9e84cd75a9e8aa0027b4c38faea5f202a88c2b55e0e934738e320` |
| `dfb-template-branch-join` | `dfb-taint-typescript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-branch-join-positive.json` | `62b47d9d53a009613c2d09c7a0bdcfecfe04532b95707ff97b7330c9b7570bf2` |
| `dfb-template-call-context-separation` | `dfb-taint-typescript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-call-context-negative.json` | `94c02ace62887154c4a569f0c20eb64ab5b59e323837f7589d6c921d18eeaf98` |
| `dfb-template-call-context-separation` | `dfb-taint-typescript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-call-context-positive.json` | `3093efc766bdeff2201a167c96ab9b2986a354dc734d71dcd077f054bf7d7307` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-direct-negative.json` | `52261a719ef373c0ddd8816aa4985bce1792be2d62c405d0b0cb89fcd56fa0d9` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-direct-positive.json` | `197f0840deb776db85f64152b2e0cea69309a3a4a16a40998a41a22082d84a48` |
| `dfb-template-exception-catch` | `dfb-taint-typescript-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-exception-catch-negative.json` | `735deb17149a7e18925a578ce86fe7970ea3eb3b565936488b4a8184f0b2f191` |
| `dfb-template-exception-catch` | `dfb-taint-typescript-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-exception-catch-positive.json` | `bb2059f02964c8eecb573bf9f6254345f6176813e592a110f7ef190fe5f70925` |
| `dfb-template-infeasible-branch` | `dfb-taint-typescript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-infeasible-branch-negative.json` | `f7d4817b5274d25a25bd6f94eefcc04e0cd2cf2c9817054e1b134d90a9b766d9` |
| `dfb-template-infeasible-branch` | `dfb-taint-typescript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-infeasible-branch-positive.json` | `a58f7849a55622d809dacd853b4b59303ecf9491dfd28a0337e087d1e7456264` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-typescript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-local-chain-negative.json` | `fcefb5761d21b7ee3032ce387f65a27078a3d10b33202357438528d8cce01f3a` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-typescript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-local-chain-positive.json` | `775ba189a50ab360acbacf3175463010b1c21556804730c858822127de870650` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-typescript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-local-overwrite-negative.json` | `56b01020fad7a935cc397a7b500cf2fe820f4c844cf056276b564cf14f626c75` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-typescript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-local-overwrite-positive.json` | `4bbd5a7ab7a961e119a69c4ef850efeb4d80ab3c4b715781fbc52618820042e1` |
| `dfb-template-loop-carried-kill` | `dfb-taint-typescript-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-loop-carried-negative.json` | `8cac9644ad11b5e637c53bd617faad8eb689c298c429714e7ba87eb06226a0ab` |
| `dfb-template-loop-carried-kill` | `dfb-taint-typescript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-loop-carried-positive.json` | `a6172aecda470370910845e4f11f772c168de563536a9c01e7a0c9096ba51b39` |
| `dfb-template-object-separation` | `dfb-taint-typescript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-object-separation-negative.json` | `affbcb72e5fd2abd8e0a0c38b65ed927cf03fd5db5a2bb098cf7fcbfa1fae999` |
| `dfb-template-object-separation` | `dfb-taint-typescript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-object-separation-positive.json` | `5f8dfd939502633c08b76688c987d653fcb2b84a32b5c4f7cfc448d5ad65a3d1` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-typescript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-return-relay-one-hop-negative.json` | `1a296a6efcf7c96f8b87cf3bd439f275908bd7bb3a3a5af04b7faeced5b557d5` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-typescript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-return-relay-one-hop-positive.json` | `fd460ae12c14d96178b825a11f70e9a401412e5765eca75d4ceb5e0f427c49b2` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-typescript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-return-relay-two-hop-negative.json` | `82250e30a42661c164be9d7c4b469148d67febf9bbf7b0d02206c669de212417` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-typescript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-return-relay-two-hop-positive.json` | `9f1795a1a0085aabfd7d198f17603fda7ee2db8f0b03a8f902044e65f5791c2c` |
| `dfb-template-same-object-field-separation` | `dfb-taint-typescript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-same-object-field-negative.json` | `63398359445eb435936bc3ede126bf287815d9d3a87a32a10e188aa60d4a3109` |
| `dfb-template-same-object-field-separation` | `dfb-taint-typescript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-typescript-kernel/dfb-taint-typescript-same-object-field-positive.json` | `e5f102da9a2c99ede4662427f3819be1b69bc9b5c19bf0a3586dbd5ff5831bdc` |
