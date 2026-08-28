# Scorecard `codeql-rust-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-rust-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `cc2c728b66e0c273545e3531a672c0987473f3830f5df80b0839f5d04c33600b`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-rust-kernel.json` (`sha256:02625bfd21b8609cb7800e4a55e43f57c33718b2dd8b3c07e8415404224b9066`, normalized `sha256:02625bfd21b8609cb7800e4a55e43f57c33718b2dd8b3c07e8415404224b9066`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 21, `not-reached` 33, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 2 | 0 | 5 | 0 | 0 | 0 | 60.0% | 0.0% |
| `dynamic-dispatch` | 0 | 5 | 0 | 5 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 5 | 3 | 1 | 7 | 0 | 0 | 0 | 62.5% | 12.5% |
| `interprocedural-flow` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 6 | 0 | 0 | 0 | 100.0% | 14.3% |
| `object-sensitivity` | 3 | 3 | 0 | 6 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 71.4%, FPR 10.4%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-negative.sarif.json` | `60b99def7370b6af138b20b8552cef54676e371a9be35d2a3fdf15aecee0a143` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-positive.sarif.json` | `bcbd839999c18155bae4e02b793d8df9181f50e0d98e5e3a9f903b43a624e939` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-negative.sarif.json` | `57ce61649d7d159f5673f91361ba62f3e73ee030b469a0a767baff69f4f93391` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-positive.sarif.json` | `217ae5f092a767a7799f4ed47fbcb412ac432de3f27a3db1a68fc4bba19adfa6` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-negative.sarif.json` | `4c71206658cf42ec5720943dab59a18c6db2d9967d991f47e4617c19fb268d37` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-positive.sarif.json` | `28f3c73c2fe2b4c2019e2e039a7294f7304415fe9ffcb50e08f7e3bb8ad26ea8` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-negative.sarif.json` | `873d484285d0a7cecc6dd2d58d887668303ca7572c0688c00a3d024938d10bc9` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-positive.sarif.json` | `bbfdffe06cc808ae36729d1e68ac248d545a437700debed586c37a55e32cd7d4` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-negative.sarif.json` | `30b0dc5af72017f29dd8a43b26e0b5764d24af64ae0835365a67d2e876205fdb` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-positive.sarif.json` | `7dd7a0c5bcf79b8bb57c43db2f7d9586f9cb7408369312282311c86ffecf9c35` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-negative.sarif.json` | `5c52835a56f8f4759d17f4b40962a64a8a248ee7a91313fff00144b532c3b16d` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-positive.sarif.json` | `6ec7c391303c4385fdaf146a6e32ac45f2bc7a5d8a757bbf9eac1fcb2f114d9d` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.sarif.json` | `5ec83b9ddabc73a3299a2ca617bf2dd9e689e7098c91d715b48b20a151a849b7` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.sarif.json` | `3e9c08354d614dfdfd07217506c47f4714e8306f0cb394133b4a9365ed8d6bc2` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-negative.sarif.json` | `f40c6013982d591537c81ddeed3b82d595a4d0c7e6e53fdb3aa239741ca0d27c` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-positive.sarif.json` | `44726e77bdef8f7ac3a7ca245aed49e696ebb417c6a018794e9688eb3dba8704` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-negative.sarif.json` | `29ebf34a3d8d0a9f12dc59dd2b50b4952419462337a8bb1e2d271f737c9ec516` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-positive.sarif.json` | `2f4df4293af99db2d157e256ee8caa5b1d9811a3e303c6e2c31bd91d34bfe3b7` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-negative.sarif.json` | `543be218b48720364fcd7bfb66a6512dd4ad10eded34a67f5011927cf1a7002c` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-positive.sarif.json` | `4a6766531fbf7ef6c36170fd260e5d6bff63b98876879e22d6b26df742de246e` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.sarif.json` | `242706d127a9d127c0e9f4b9d27ffce53d00f989bab0934d755db40cdc1019ed` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.sarif.json` | `c82b966d1bb2e970cfd0794f7fdddec8a389c7064402410fe3f97fabacd86c70` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.sarif.json` | `af5b0a296ca07da618b6ea32ab8eb6a83f944f2b03479738b6335c33374f9979` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.sarif.json` | `af55debaf175d54d9eac863e40022a122ec0d0021279ed5aca8c3539b5054703` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-negative.sarif.json` | `50447b0f4f1f58b7df4d0b3c82d128596a81e399b7c4ec55c7a8b94bf614f330` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-positive.sarif.json` | `44004909170a860c5675f68b4dcbf362e858b577255208e86c5b6f79dccc1548` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-negative.sarif.json` | `b99d10be51a485b9fdb52f08ae2ad2696ff8d0affd7b2ce0888b469953911533` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-positive.sarif.json` | `c06ba29ff854ed7c9e6cbcb65addd8410dd2b8a818c617f8c5f48583f09367fb` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-negative.sarif.json` | `2ad5ceffaf846e3df83590772df7d3363b81c6273c2898d2f9a1678099bf4ca2` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-positive.sarif.json` | `ed3c9f9f7e4144ef00baa5f0f68020be1d03c6b2fd8767a4b416c4776e0c6ad4` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-negative.sarif.json` | `122e5fd77c81f5e12a27bdbab04c567c54fc03b2b96921067983345067ead6e3` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-positive.sarif.json` | `a05d8e659fe251b91c8724d0a156c784d58c77631eb5d12b730df7d7853780f0` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-negative.sarif.json` | `8ef13279e139318106b34c8956b650e5239ad51bdb36fa8d7da59537822d2e68` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-positive.sarif.json` | `959fb62ebfde7e87639b25d85bc2fbde3d485c8a9e846ffd71cd38703a91b06d` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-negative.sarif.json` | `44b825e4d8da393bf230eec4696df7db2ada7b5b3f7ce809fab64c6d8178cb3d` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-positive.sarif.json` | `fdb83793d93cc68abe889fd4acc38dae7a879879fccf9766cafc78af4efaaa95` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-negative.sarif.json` | `8ba9dca3af381f2a359e5b607b09ae65ea18087e7b8fd05fc09662a3a96fac0b` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-positive.sarif.json` | `0908edf9e108876fa7703fb43b4dddc181fe127136956f4bfd81d4afe351f5b0` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-negative.sarif.json` | `37d8cc8850cc1f3a8ff9a5a986a154c88797b92386a537df59499369c77371cd` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-positive.sarif.json` | `3f67f3442dbdd04d431f867b7b9ae6243209583dd66a892214958051a16818cd` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-negative.sarif.json` | `504c15bad713baf23001356aee7046bab66dcc3efc8c807b11479a09a1b16ec4` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-positive.sarif.json` | `1da0e40742a64aefc51d787687f92b7a6a95c6e5b48f26ef6117a39b3c9ab1f1` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-negative.sarif.json` | `e443ad5fcc5a5ee45b62b08a63163edd090b1c371768bdd84dccf7c905f6d117` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-positive.sarif.json` | `10c4cba69c3caa823f5f0169ae0b55c336ceb3c4a63f0731b5e10dbe49d02e7f` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-negative.sarif.json` | `6afb9deb816e3a538a416d160b032f4703f45eafec9c7a5332543e7fa57351f5` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-positive.sarif.json` | `52527bbf0bfb4d9ad353c61bd8c1e14ef234261af8e0b55cf6db68faf9ac80fc` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-negative.sarif.json` | `4b2646dc7e72aa308368137105a16b26276f1a3c90b5e37a6ba6af34e2832186` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-positive.sarif.json` | `936d7877170e538f8adbf55a8e666e6815d50788c20011b26a91834b85b4cf49` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.sarif.json` | `c970a25ea99401417facb5c1b79080cdaedcb18a86cd392da8bcebce1a8fd0e5` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.sarif.json` | `1c1145b52a9cc753a088c5d2e41b9310d548791148837a0c0ca287cb0f870551` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.sarif.json` | `3871807d3e3ccb524908de3e4d45c5efefafd9627ada27ac5a5c7239c947aa5b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.sarif.json` | `4f482b8e4a698ec930d0c03a7ee430bf17de1ded2db657299e4245f86430f252` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-negative.sarif.json` | `e7bfa593593f3b9a363a2c197e449f64e2d72f0e03d84c1e7e0b0c97263e85bb` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-positive.sarif.json` | `197ec9a83d9a48a52f060eec1d6957cbbfd6d73211b6d04d2e5cc64f09dbdbb7` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 2, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 0.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-negative.sarif.json` | `12b99bd3a04ff8e539e0fb28c987c40a9c79f41d1755777c503366fd4ccb4718` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-positive.sarif.json` | `e4a65bccb099c3624d697776906888d57d06d9babc9d35a03f3cab9a99d22b50` |
