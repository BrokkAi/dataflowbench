# Scorecard `codeql-csharp-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-csharp-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `cd5f68b8ccb2e4de27cf1606b0c9f2ee8981ce5dfdf8ee2fea08fe977a0c56c9`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-csharp-kernel.json` (`sha256:61146506ca07d1e1bb1025b3c341574da1f64fc0cbd63e15fc46e13d3e371d46`, normalized `sha256:61146506ca07d1e1bb1025b3c341574da1f64fc0cbd63e15fc46e13d3e371d46`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `csharp`, tier `core`

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-csharp-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-alias-propagation-negative.sarif.json` | `6c17ba6beda9edf43f16b9d9d714f14446af0f94292a90af3141f736dc560a9f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-csharp-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-alias-propagation-positive.sarif.json` | `5de0dc0d09ca3cde0b2119e684aa2c8a954f5ce806fa9bb2371d09b38ceb1236` |
| `dfb-template-argument-position-separation` | `dfb-taint-csharp-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-argument-position-negative.sarif.json` | `1250512b9fe4964c48d7b6d0d7bf867e9d85daacd9570e0be2905e273ad3e8eb` |
| `dfb-template-argument-position-separation` | `dfb-taint-csharp-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-argument-position-positive.sarif.json` | `a4fd9c34402caf46a4aff653b1717f271c0506d3d16e7f5b4cfd620e4ccb2d78` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-csharp-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-expression-negative.sarif.json` | `e991cb36f7bf047878754100d92a288372ee4376822a798bc11421c5150d11fd` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-csharp-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-expression-positive.sarif.json` | `ac86b9f5f0acfe56ce4dc0ee1f3fdf604686a78a490901edea26bc57b1cfa52e` |
| `dfb-template-array-element-separation` | `dfb-taint-csharp-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-array-element-negative.sarif.json` | `02c5c1edd2bd02ba10a0e72af5b9e605ab3eafa062cfd8432c47140af6fa0da0` |
| `dfb-template-array-element-separation` | `dfb-taint-csharp-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-array-element-positive.sarif.json` | `2a583681038b1fbc553e54eb14d7d9cff5d382b3355f0b16d4dc5bc3fc1d949c` |
| `dfb-template-branch-join` | `dfb-taint-csharp-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-branch-join-negative.sarif.json` | `a314dacb102b1fb466c64662c2947167a9d7e679c878968761b72495d09352c4` |
| `dfb-template-branch-join` | `dfb-taint-csharp-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-branch-join-positive.sarif.json` | `48d4a1318f49cd24f1183f382135df2d1ef62a0cfb24f7e817f39fe6048166d9` |
| `dfb-template-call-context-separation` | `dfb-taint-csharp-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-call-context-negative.sarif.json` | `1f89138a048b65050b694e6228fa89e48c51595dd8f6b8486d50410859d0463b` |
| `dfb-template-call-context-separation` | `dfb-taint-csharp-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-call-context-positive.sarif.json` | `51bb1dc7b4dc74d5f1774ba852d61ab9bab5ada93b96f95db32aa5725532d550` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-direct-negative.sarif.json` | `c5faf35d61c13ccaeeb0a478c033f43e067efd1403d3c337e5881d51c7aca194` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-direct-positive.sarif.json` | `4844745b082c02101fff232a7865624fb8e6c5e4533147cba2080e490f0ed931` |
| `dfb-template-exception-catch` | `dfb-taint-csharp-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-exception-catch-negative.sarif.json` | `173d331f22a6a0dbb36c25ba536071150c29f2afb07a6a0a2f76267e1afde38f` |
| `dfb-template-exception-catch` | `dfb-taint-csharp-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-exception-catch-positive.sarif.json` | `6485f0cef7d5a22dd4967064736bdd2ea4b2048d0311d1f7f6c0a9ed97dc1075` |
| `dfb-template-infeasible-branch` | `dfb-taint-csharp-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-infeasible-branch-negative.sarif.json` | `d8dd9f4e085b85d61fd9db7bc1c423adf959d7ec6b37bdc89834642e296e14bb` |
| `dfb-template-infeasible-branch` | `dfb-taint-csharp-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-infeasible-branch-positive.sarif.json` | `6253ddf52f0447fe3347438caf1c19ffab6df311830e6fd7404ec01c68e82584` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-csharp-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-local-chain-negative.sarif.json` | `5b6bf9acc0e06055ee4228615d26abbb0ae2f47cfc15983cd1fd2fc78fec0c71` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-csharp-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-local-chain-positive.sarif.json` | `cd7eb03d18fede52d601c28d560c266ac3288c646a6e6d7cd62e381b1b3bae5d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-csharp-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-local-overwrite-negative.sarif.json` | `8462e9a154dd2a5069ba4a7c28ac4686ee892ad83c4715e4bf392a46a8cbae91` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-csharp-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-local-overwrite-positive.sarif.json` | `67f3acd9ac884925732ca8c4bf071d52cf052e4062701e8a8fa5acc51fa9c6b5` |
| `dfb-template-loop-carried-kill` | `dfb-taint-csharp-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-loop-carried-negative.sarif.json` | `91685cc427146aa1f71f351fba9ea9a60422606d4757c6acc18b30976aa8d3f1` |
| `dfb-template-loop-carried-kill` | `dfb-taint-csharp-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-loop-carried-positive.sarif.json` | `96d7fbed9c7735b3dd827cce7c6bb55e3a7069150b1fbece0e02115444839467` |
| `dfb-template-object-separation` | `dfb-taint-csharp-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-object-separation-negative.sarif.json` | `52d59536e35f2953ef947140d45d480494899be8de53cf5c0c41fe380794dce6` |
| `dfb-template-object-separation` | `dfb-taint-csharp-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-object-separation-positive.sarif.json` | `2942ee5c261343bab42269b3ca7c67c3e00e86a65b9317428600c169bf19c55f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-csharp-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-return-relay-one-hop-negative.sarif.json` | `7ee5a0a4cef004c8b7f8e7c99359b7b005eed8e88e12800f56a43caacebbf3c5` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-csharp-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-return-relay-one-hop-positive.sarif.json` | `46f5dee43336a38d7f5beb0ec50d3478ffc64df155799f4edcc57fa2ee1423b9` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-csharp-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-return-relay-two-hop-negative.sarif.json` | `40f8d2530bb1c10008252bec72547c654f949ac8f6432c3b8e3e1af83cbe80e7` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-csharp-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-return-relay-two-hop-positive.sarif.json` | `1d5914028210495c53a01f7b9518cfdfa244b6360cbe4148210ba455dfa03969` |
| `dfb-template-same-object-field-separation` | `dfb-taint-csharp-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-same-object-field-negative.sarif.json` | `9b9894b95e47757d4256eb2772e67bf2d79c983fae0b23eaf5dbe4c9965a1b23` |
| `dfb-template-same-object-field-separation` | `dfb-taint-csharp-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-csharp-kernel/dfb-taint-csharp-same-object-field-positive.sarif.json` | `2470a229011ab733d7616fd384897caa9107c2412afd48d4a1fd6c09d9f79969` |
