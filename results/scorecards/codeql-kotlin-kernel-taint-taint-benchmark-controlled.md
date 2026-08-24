# Scorecard `codeql-kotlin-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-kotlin-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `25b92ad6190d65fd76c67da51c3ec0d638cea7699e976941c027a48700b9096e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-kotlin-kernel.json` (`sha256:779b945d3435b7c8144d932117bb5483f16520b0c7b285ba477910faf489ac3f`, normalized `sha256:779b945d3435b7c8144d932117bb5483f16520b0c7b285ba477910faf489ac3f`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `kotlin`, tier `core`

Outcome coverage: `reached` 15, `not-reached` 17, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 3 | 2 | 1 | 4 | 0 | 0 | 0 | 60.0% | 20.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 6 | 2 | 1 | 7 | 0 | 0 | 0 | 75.0% | 12.5% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |

Macro-average over semantic dimensions: TPR 73.1%, FPR 12.4%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-kotlin-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-alias-propagation-negative.sarif.json` | `ff7f5f7a1e0ab63b21ac2c23ce58e8121ab5e634b4690d9cd456cde299c2804b` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-kotlin-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-alias-propagation-positive.sarif.json` | `1ef08aa5813e4ae7713b75eea3a3e3edffbc249bba0f3d756670e92548cbac18` |
| `dfb-template-argument-position-separation` | `dfb-taint-kotlin-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-argument-position-negative.sarif.json` | `7352eb69bd7ddcb82551a4aae1778b6dd5c83ffc6b8652a344cce85301b7f17f` |
| `dfb-template-argument-position-separation` | `dfb-taint-kotlin-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-argument-position-positive.sarif.json` | `f38e7e81d953326bf521d44180b3452bad64fa4b63f42857ee1e43cde240fd4f` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-kotlin-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-expression-negative.sarif.json` | `d2b0bcb97af735d4df412d8643f31e6e8e4af35ac92b0f4eaad10e9ec58775a1` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-kotlin-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-expression-positive.sarif.json` | `b894a1f642c67f46c31f9f3f47f26ff7c21fbfde5f72d7eea90db1d01f516d31` |
| `dfb-template-array-element-separation` | `dfb-taint-kotlin-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-array-element-negative.sarif.json` | `b2a9d9bb07cd659d2f07c5ff739e4f7215d5856c5c58ffd441248ece719e9b45` |
| `dfb-template-array-element-separation` | `dfb-taint-kotlin-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-array-element-positive.sarif.json` | `79a68bb08b3cfb527f8e6f83885e8925c9fa74dec0458d04b1ee020c40fb21c0` |
| `dfb-template-branch-join` | `dfb-taint-kotlin-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-branch-join-negative.sarif.json` | `bedc96922d46c632a922a4d15161e39507036a8f8de777e68a06e030f0577c19` |
| `dfb-template-branch-join` | `dfb-taint-kotlin-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-branch-join-positive.sarif.json` | `3db8d10636ca41f6aa636787ecc3df0452fdc1cb6dda754a6c1b465f027d4769` |
| `dfb-template-call-context-separation` | `dfb-taint-kotlin-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-call-context-negative.sarif.json` | `6ad54ef229a28c838771027cfb48e3b16addbaeb9fc764fe290c21b8c68abbdf` |
| `dfb-template-call-context-separation` | `dfb-taint-kotlin-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-call-context-positive.sarif.json` | `87ad1b348e372a7bb4d8bc320f7dbc3af4d06b6632cdb9f09e5debc254e4c94c` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-direct-negative.sarif.json` | `f492baf3e3e796ee78983fb3e98430783ebd91b434c2b029cf2d618f58f7fd56` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-direct-positive.sarif.json` | `d684794899587990e9a4c162b781533eb204799c57250e86cde3d1f239262705` |
| `dfb-template-exception-catch` | `dfb-taint-kotlin-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-exception-catch-negative.sarif.json` | `fce991d46927f0919025fee2e748faf6e62645879ff8caf4b08a31c7572dae14` |
| `dfb-template-exception-catch` | `dfb-taint-kotlin-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-exception-catch-positive.sarif.json` | `7c65484955569e67faa1e352f0b958ec656f8a08bdf644aba67e0b740cbf6a0f` |
| `dfb-template-infeasible-branch` | `dfb-taint-kotlin-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-infeasible-branch-negative.sarif.json` | `5a6826a5976336040294b1d57ee5b59bbe323b41c71e8dffc929a4ed11878a35` |
| `dfb-template-infeasible-branch` | `dfb-taint-kotlin-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-infeasible-branch-positive.sarif.json` | `f6ac2f4af1f27640344c790f783f6b0799346f19b275b0dae350e34886a7d39b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-kotlin-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-local-chain-negative.sarif.json` | `20f6ba5f0af998d962c5c2665e6cf01a58dfe1ab0d523cb012cf753bb069d6c7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-kotlin-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-local-chain-positive.sarif.json` | `ab0c32b814f464dcd2aef618b31fdbdb0db18f1e19f74a56e9a2ccc27f1b90ef` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-kotlin-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-local-overwrite-negative.sarif.json` | `965c71570d2d5e9e579e59324d33f450f50f2d18a720cefa3e14d7a4d204ed76` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-kotlin-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-local-overwrite-positive.sarif.json` | `580ba5e43bbffa9df6bf3eb0828987536824c45a45dfa8163ba4b709f6330693` |
| `dfb-template-loop-carried-kill` | `dfb-taint-kotlin-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-loop-carried-negative.sarif.json` | `ad8b044538456988fe23ec45d3d347764e6266957eb002e0c0db649c2774d3ab` |
| `dfb-template-loop-carried-kill` | `dfb-taint-kotlin-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-loop-carried-positive.sarif.json` | `cc0d60d9aebc7741d836152303c439d07ef6058c04d9795765138ff5da6ca900` |
| `dfb-template-object-separation` | `dfb-taint-kotlin-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-object-separation-negative.sarif.json` | `beba22378abb7d9e53862335701bf2eaad7a2700b73dccfc2f4fff0df3f10ae7` |
| `dfb-template-object-separation` | `dfb-taint-kotlin-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-object-separation-positive.sarif.json` | `7429d724b40d19f377052b2252fec88d159cb1916d499b193d4a71b9dd39a659` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-kotlin-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-return-relay-one-hop-negative.sarif.json` | `1912bb615a5e6fc979502691bc747fa704dc076a5c8349222accde1d4e24016e` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-kotlin-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-return-relay-one-hop-positive.sarif.json` | `8099755e4b9debe2e89271ea011658d8b4ba74bc4fe6a61a364bfeb7a7040ae6` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-kotlin-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-return-relay-two-hop-negative.sarif.json` | `aaa19b675000e38de835088520a75dbb7c60b9887e75c7fc65c4bb8dce5c4e9f` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-kotlin-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-return-relay-two-hop-positive.sarif.json` | `69ebfa64fb585892e17df1e1d6bff794ca4954b5d5ed81131a83eb5e81e79bd9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-kotlin-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-same-object-field-negative.sarif.json` | `854232030a539f42f4f5be28dd059788c2964675df08948aa08c1731f90189c3` |
| `dfb-template-same-object-field-separation` | `dfb-taint-kotlin-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-kotlin-kernel/dfb-taint-kotlin-same-object-field-positive.sarif.json` | `b9612f3f0bb08e9d5785ea9cc84a4fd5a32374776a28f0f8088f037f06ae29c4` |
