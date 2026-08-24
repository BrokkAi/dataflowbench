# Scorecard `codeql-go-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-go-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `56f44b3d983f7ea1dc2fa77a796ac547b01d12535a124f0c9975d3d0b7989161`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-go-kernel.json` (`sha256:e90acd0b0e2d40c702df2c0d70f5f3118434951b85376008b7d0e7b1dae4516a`, normalized `sha256:e90acd0b0e2d40c702df2c0d70f5f3118434951b85376008b7d0e7b1dae4516a`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `go`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 3 | 1 | 1 | 3 | 0 | 0 | 0 | 75.0% | 25.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 6 | 2 | 2 | 6 | 0 | 0 | 0 | 75.0% | 25.0% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 100.0% | 66.7% |

Macro-average over semantic dimensions: TPR 75.0%, FPR 18.8%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-alias-propagation-negative.sarif.json` | `f114d1114bdd348879ef5e7e0fb1add51a768c3783b6fefb2f277fe38c14cd36` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-alias-propagation-positive.sarif.json` | `b97f95a3cfe2e5714b4065daf481fe6af99e5cfc0c6ddc5debcecc1b85affe43` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-argument-position-negative.sarif.json` | `8a1b79a207c83f184c925b63678dbb6bc75b86ce523359dbcf1ada1cdddf9cb4` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-argument-position-positive.sarif.json` | `c7aa314168cb7d8d123fdf4daf1f30f715509cfd75f889fa1d02d68d8082ed42` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-expression-negative.sarif.json` | `3d02cb14807f8a25f73833a553f9a9c196c90688c3e344670d19e4d2bb9394ec` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-expression-positive.sarif.json` | `ec569869b6b702aae2bb56d5a73d2a6737975673b3265d580757f0f48a447d87` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-array-element-negative.sarif.json` | `dcda5ca4964eee0615fc0adc9727da197e7f3968b0901b5d4bc8f1ece43893a3` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-array-element-positive.sarif.json` | `9b35fb4299c73eb869370c443de638ed60a7b55a68a15231b8f43887dc3aa7ee` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-branch-join-negative.sarif.json` | `81d914dc15731cbde8c6a00f457036ab1b699ec3c71b5a740d140b989a966448` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-branch-join-positive.sarif.json` | `c21da578dbc577d1d9e777825312ea655d9b5b39681624d2ca3d7abdb4cd3236` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-call-context-negative.sarif.json` | `e6e6ff29ca985dbac1221bbea9cd758b78e9d294a4552b0486cc3fcf83b4cd10` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-call-context-positive.sarif.json` | `aeb4f0976b977931040cf3c91303940b7588bd5285a7d76d7dd58743d9867243` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-direct-negative.sarif.json` | `644e5e6fd24a35cbcbbeea9385bf751f28b540bbf3c4194f91b843a79343f7da` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-direct-positive.sarif.json` | `eb3e0de388c5d4ca982827331e0ab8baacd2896c2260e2bc2e0e178376bacefa` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-exception-catch-negative.sarif.json` | `521d7e43304b00d6786f821640a148873ea441bb398b67e210f09f1745d31a5b` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-exception-catch-positive.sarif.json` | `28cf1c3d37393b97dcdf80aa2e032d5a487c3eb54d76e0467c55f31f93d181b4` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-infeasible-branch-negative.sarif.json` | `820b0ecb2e37020313ea7ea4959bfbf41d2b6e2ee63685703e9a62e9164fb0b5` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-infeasible-branch-positive.sarif.json` | `d1b22ac2f78b4a3a6d0a30619951fd566e4c715889a138967b5c7f452002ee61` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-local-chain-negative.sarif.json` | `56a0c0a16f09f2d7073e3f1661f6e4587438b0640375cd10b3011936bf26aa55` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-local-chain-positive.sarif.json` | `a981362f1edd09a3493af1927acabfad84660e8481753627f1ddf314c3e88a9d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-local-overwrite-negative.sarif.json` | `7fda5478bc7337108da93abce641a99ac83f2eb72826bf32f6d7db2ba5e4d3d2` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-local-overwrite-positive.sarif.json` | `7050daad753b5752a338ba3078045a7919cb10866fc984b10d78123c85c1b186` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-loop-carried-negative.sarif.json` | `ef6b2f6d67e93e842f26cc7db8935d59ffa8a5c69c2d75c0290babb55115537a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-loop-carried-positive.sarif.json` | `8af52388d400ed1f6371788de602e36a0bbf94438fe766f31f8b399eebfbfc4f` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-object-separation-negative.sarif.json` | `61db81aac40d95c49ec949cac46ae869bb3908cb6330a38dc49b603741aa0bea` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-object-separation-positive.sarif.json` | `650cd5d0cab1f14db90e8ceb6680c5e0b97d673af3052bffb986520c7097695a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-return-relay-one-hop-negative.sarif.json` | `0b3142d2cdd9cbc3bcc41fe63487b52bb14099060d7cbefcd6541fe306186953` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-return-relay-one-hop-positive.sarif.json` | `5fb9bcec2591f040014de4cab21122e9ad3d1433cdbdff75e8ff3d6517ac67aa` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-return-relay-two-hop-negative.sarif.json` | `aa9e1f6755f90d8d338724748bebda7760f7e28ad414940f918391fe06e5c7ca` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-return-relay-two-hop-positive.sarif.json` | `438eaa97de5417b768b3a7eb2ee075f5a6f1ee9d0cc1c3d97730ca7ed627acff` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-go-kernel/dfb-taint-go-same-object-field-negative.sarif.json` | `f572bf939c9667e17a1fc353032362fd1fd11946b8a73345c160f1fc5d928538` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-go-kernel/dfb-taint-go-same-object-field-positive.sarif.json` | `e0ba27f9704ab35cf279587e65a741f3d037e5a9df89fc6ab1e1ef1c4f00dc5c` |
