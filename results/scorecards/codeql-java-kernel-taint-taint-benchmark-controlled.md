# Scorecard `codeql-java-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-java-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `eedf28b140e6aaf2c27cac6369ee552803cbc7b7674abd70583e3e962e1ef8b6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-kernel.json` (`sha256:04324829ae3a39fd11a8f7de499af30e365a5fd4380eb55c0249d88c2aee6b6c`, normalized `sha256:04324829ae3a39fd11a8f7de499af30e365a5fd4380eb55c0249d88c2aee6b6c`). Generated from freeze manifest `reports/freeze.json` (`sha256:c9429463e39aa4d4c868295a2025b4d192cb8d5add5bc9e36265eedc5e1838cf`).

## Language `java`, tier `core`

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-negative.sarif.json` | `170be0c73869966167c11847748c78126c742702d18f1436954d1ce0f45126ce` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-positive.sarif.json` | `7b962d3c6de328725fb176556ba2935e046e5a5442b00d14d27244c7ddf314b0` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-argument-position-negative.sarif.json` | `935c8ca3342415f1ce3b2ca3928ff282aa546f6898f643e9e538ab046d56b6be` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-argument-position-positive.sarif.json` | `02e1415cb18af5da9b70eb2554934d9814c2286bd8e4eea4b7b74e720411578b` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-expression-negative.sarif.json` | `7599031a9c955d55a6357e3981637085a65b853070fbc3ab49ee9a0d7f69e2f1` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-expression-positive.sarif.json` | `b3a7b143ac5641bd61cb2893e5bcfcd6f5c37f018e10970deb283fcaa4cbaf81` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-array-element-negative.sarif.json` | `ada868602679b5260387f268edf9390f8aad8c6f3715b596b4fa92f6711235f9` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-array-element-positive.sarif.json` | `7fd459e5e51ec81fd14592551bc4b33ccc78423425311063d2a3803a276c11ac` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-branch-join-negative.sarif.json` | `112c5a72e1a2092cc8953080517971411f8f2786f13f7a437235adc6a225b8a8` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-branch-join-positive.sarif.json` | `15217738d3a55aa9475b2d90dd5ec4e40650205348f7993f6200083dc71fb005` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-call-context-negative.sarif.json` | `26b002aa612ed3746308f9374c2f8eedc835d6f0a0257d4eca026b4db9922a50` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-call-context-positive.sarif.json` | `752d628e4147e72b99faa80e03c70edcf41984216e7312fe827a7c05711eaf5c` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-direct-positive.sarif.json` | `a18353a069fbd9476cc35a26f379250526b969b49304e52ce336cf8e64c32d54` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-explicit-negative.sarif.json` | `2c4f7af99cec473326474c1db9e4259115a4b0a97f7d08bc2d13d95ad6e04911` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-negative.sarif.json` | `7fa855da3b8b8ab5d68cc9e3e2ad0f2284fcb5e99ffa69f883974833392d19f3` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-positive.sarif.json` | `6a9a4074967fdc89b9094cfe1d58432aa6ee5782aeb37238031be85dd1a5c377` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-infeasible-branch-negative.sarif.json` | `f5aeb95dfb243c708320aa378c771637135d3a9756b17830189017d09c4259ca` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-infeasible-branch-positive.sarif.json` | `170a893c43ffd23c6735503f16fc3dc0916c99813cbc78997162dc924d1684d1` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-chain-negative.sarif.json` | `3ad0a4cb80a6afad67d4918fb9129f285f26e88c451c21572631018ff2c46e81` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-chain-positive.sarif.json` | `2a05661d1af41d0a862f5cefe945b4d7fda244d7db0e40ada0a11d82489405ae` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-overwrite-negative.sarif.json` | `e372b78722b8c6f6bc9bd6f6e29c1de007f03b7eb183165a507243a98210eb84` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-overwrite-positive.sarif.json` | `b1dbca4c4a9ddeccc8cc7382ef8d88467c816fb40187493d4abfcfdf31dc1d8e` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-negative.sarif.json` | `169333412c8a7c6f25ff32aead896f7643d6aa0b24c082d5586f1e823f953a02` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-positive.sarif.json` | `ec2f1d4f69df3dcc9c63610b0ee483e89f3b9f55c290c754262c5f5c72a983a5` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-object-separation-negative.sarif.json` | `b1e8c9da8f6584190e57f75e0fff3f54d9d5f80459c083805f22c7b235693191` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-object-separation-positive.sarif.json` | `8a937bd55cc09c6c5710f1cfce31f674adf460a7ca9e5c0088489c09a9655f05` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-negative.sarif.json` | `767b69ae3c97ab8bf58a24bb0aad0a2fbbc67d8b53f8e21b403dc146f4e73631` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-positive.sarif.json` | `ac3957fdba5fbb06f0939d4f6904d41ec4db4136b2168bca5741be84035b85c0` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-negative.sarif.json` | `7d54aa33c746b06db95264805a7db1956f326d919eb83bc85e39d401ee2c953f` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-positive.sarif.json` | `acdcd90df6c93b1a5d5accdf8ff8b9145c6bf6769eef1360951b0561cf4387d4` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-same-object-field-negative.sarif.json` | `d44c84934e63a879ab8cb730cb98bf121f27ddf6719ebcfb6ba8704a81e9c511` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-same-object-field-positive.sarif.json` | `21e712502bfd73875c7eca57770f95e8f401d65872f5ceae8729faeef1dcce86` |
