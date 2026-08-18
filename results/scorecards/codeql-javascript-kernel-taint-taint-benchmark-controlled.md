# Scorecard `codeql-javascript-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-javascript-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `cb54d749e915208a1fa7fceaa1e5e5302c18960aebf724573040fda66c7a7ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-kernel.json` (`sha256:89eb5141248eb7c339001643d8031b2b30c5bf3eef60b8b745f43574f2e4f25e`, normalized `sha256:89eb5141248eb7c339001643d8031b2b30c5bf3eef60b8b745f43574f2e4f25e`). Generated from freeze manifest `reports/freeze.json` (`sha256:c8ba343f2db9a8c1cac5570a414bf497c85bbe11d29730639575c9ba3bb70912`).

## Language `javascript`, tier `core`

Outcome coverage: `reached` 15, `not-reached` 17, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 4 | 1 | 0 | 5 | 0 | 0 | 0 | 80.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 1 | 1 | 7 | 0 | 0 | 0 | 87.5% | 12.5% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |

Macro-average over semantic dimensions: TPR 89.7%, FPR 9.9%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-alias-propagation-negative.sarif.json` | `e6dbabc9b0e51fd61b1b06dd0b1e7c3e6a00e66adf43f621abee3af18e1eae34` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-alias-propagation-positive.sarif.json` | `08702c365308ade57a61bc87eba36297c23f7319941b5fc7cdc3a868f594ef02` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-argument-position-negative.sarif.json` | `8d756ea27f0399b7b4dc9395bbe531f7fb4c146c510db0b28d18c90746185638` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-argument-position-positive.sarif.json` | `d248cca4d47c3c82468da8c5e669cad178561d27ed022b7b4d49da48a3544e95` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-expression-negative.sarif.json` | `6511065753f24af54e759e1bc14eaed87c97c28f744f3003cc56ad7ec3594e86` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-expression-positive.sarif.json` | `6decd56bb5ab95e3f15506763cc8baa7ab73c347290fb9cd1346fd82bc987206` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-array-element-negative.sarif.json` | `8784ca43ba8041611ab6b88b742de13ed80b31529c84704f5f80d5e852698f65` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-array-element-positive.sarif.json` | `5b9a17d7da3704f5707b5872dfa088f4b2aeb3790d930f4a057ddec0c75e69c3` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-branch-join-negative.sarif.json` | `56c25e0c15841c39924490e8952c84cea65c2435d14314d7f1e5702953c23d9e` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-branch-join-positive.sarif.json` | `f68bfce987323a1350fa656f422f193b9f97b6ff6d08d1ab56e83092c4f26507` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-call-context-negative.sarif.json` | `1ddff06b8d2aa9276fa152a3dcd7958dde3d982a17abc13232952ca0edcf4b77` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-call-context-positive.sarif.json` | `9bb789caccd3ff344fdc71afe492a799b1c769fdaa452d905b254042e60227b4` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-direct-negative.sarif.json` | `a893a80f27f13c7d473bf07975f61ac4343e44682b1a4442484cf4de859effd3` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-direct-positive.sarif.json` | `c1f6278fda22ded12eec5a6a64b1b51325a6560c776ac9be2738b8f2b840ff9f` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-exception-catch-negative.sarif.json` | `db3b5ea3b86724d0b0eb4b47f086eebb10d2ea31e92c394e9862f7b20341b3e0` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-exception-catch-positive.sarif.json` | `e3c31c4db3b21e18dba9ad3039524f8798486bd6c646fe290c29d3ec62c550e3` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-infeasible-branch-negative.sarif.json` | `025ddc6e21514221de44bb843d17b63a183874ee75b7a85233a57b0b00656a91` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-infeasible-branch-positive.sarif.json` | `e174396d03c6d77f72497215be9cadaa96446e961601c009c9617dbb4af5fb52` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-local-chain-negative.sarif.json` | `2e385e3cfdf54a32c7c6e3a2bb5ea919799691db0835dede3cf71b0aa7883200` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-local-chain-positive.sarif.json` | `77ba6db00e7e1139befc9d57acb158a36f3027eecb62a0d7278ebb24f9b81e80` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-local-overwrite-negative.sarif.json` | `f07efe06cd4848932a26eceb12a08692a11d29cbb4c30901f2cec5527372b671` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-local-overwrite-positive.sarif.json` | `302024e2999640024b8125b334a93613238bd7a5612ae3172a7c96f8c28e9da4` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-loop-carried-negative.sarif.json` | `13c0ddf45743fc25ff8b12d64ac3496c3374b650c78970009fc5d10e1b3941e2` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-loop-carried-positive.sarif.json` | `271052c8e6392335e8f9e3cda2d5071bb2c6086fd925a8ab576f1715fcbe033e` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-object-separation-negative.sarif.json` | `45337daa3456fc95e9584c0dc6b45a82d4d3df55dca92b11220762c0b9b43cb4` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-object-separation-positive.sarif.json` | `ed28f2a82fb897eeb3ef2a42444ac7e50b1b06cb6fe71d70966caa8550ae9135` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-one-hop-negative.sarif.json` | `ff571f4a0803e4eb4a2bfcbf4b3b51618cf257a34a68c01fb1ec578214bfcbe8` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-one-hop-positive.sarif.json` | `c18113f5931ffcc3c169f7fcc4d01e52d71d6e17f6507f257e22df2a35fd094e` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-two-hop-negative.sarif.json` | `828be82240deddb37564d3e5a33fe46890c0d14c0930efdbe15ed68652d38e81` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-two-hop-positive.sarif.json` | `856f033fc0062ee89869cdb5614666a1ec9a052508f3e4af449e8a8acb0328f6` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-same-object-field-negative.sarif.json` | `5f07bfa701dc1f080cc3c1f347d84661ed80d5568d3ae54fc9fb74662abb9ffb` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-same-object-field-positive.sarif.json` | `0432283a0a1256d155453caca166d07d14eb47fd3e371ca098ebfdd68e45385a` |
