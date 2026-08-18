# Scorecard `bifrost-smoke-taint-taint-benchmark-controlled`

Adapter `bifrost-smoke`: `bifrost` `bifrost 0.10.2` (build `c2116609f5fc1be318c8fb76fb83763cf326bab6`, adapter version `0.1.0`, configuration `2c5ababd371ee6b9f4f0596c570d2378aea79cc2e21c8a3e7e0eb0a195f63911`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-smoke.json` (`sha256:aaad007cd17bce497c4f0eba63e2ccb0a96ecde6f861198fed2834ac9090b579`, normalized `sha256:aaad007cd17bce497c4f0eba63e2ccb0a96ecde6f861198fed2834ac9090b579`). Generated from freeze manifest `reports/freeze.json` (`sha256:c8ba343f2db9a8c1cac5570a414bf497c85bbe11d29730639575c9ba3bb70912`).

## Language `c`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-c-direct-negative.json` | `7ab433125c5f8ea44177f4d7a74b21bd0317581ae97a52743d79911d6aa05b68` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-c-direct-positive.json` | `29433519b59c7c606d5b5e683d70de0f5a17e583702bd2afe6a6b76e3b36af62` |

## Language `cpp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-cpp-direct-negative.json` | `0617ec23020f6ac2a6a3c9fb9ddab6308b98253784b6c2034ec0678c347c7b5e` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-cpp-direct-positive.json` | `48c7f6678df018952e686ba1f0853fe57bd20b7604f3ba56931c019883f8e544` |

## Language `csharp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-csharp-direct-negative.json` | `4ec8d9b68aceac05422b1ac8c99fad8fcc69cc2a85dc79020ed9bffd53b74a5e` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-csharp-direct-positive.json` | `9c8fb039ad801a46c492516b1545c1a7489f4208382afd337ee4a304f0ac2ad9` |

## Language `go`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-go-direct-negative.json` | `052950876f8faedec31f08c7e15343b2302425f382779434b9cf0ef60126b063` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-go-direct-positive.json` | `b5ea9ffd048e011d0225168064dc4ea2189d2a182a4e64fcc8a09c0fb274b603` |

## Language `java`, tier `calibration`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 0, `unsupported` 1, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-java-modeled-external` | positive | `unsupported` | unsupported | `reports/raw/bifrost/dfb-taint-java-modeled-external.json` | `01be675e06e4fa5eabdeb5725a1e06efa319ac6156f2e492cd1689c69e29caf0` |
| `dfb-template-one-hop-relay` | `dfb-taint-java-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-one-hop-positive.json` | `5ef17072241a68fb5cfcfa6ce880fb1e4dea0e3886bba61d3fc61f709cd69863` |

## Language `java`, tier `core`

Outcome coverage: `reached` 14, `not-reached` 8, `inconclusive` 10, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 6 | 1 | 4 | 3 | 2 | 0 | 0 | 85.7% | 57.1% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 97.1%, FPR 51.4%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-alias-propagation-negative.json` | `ee9fd3a8017499731fea7b1ef08f9a20128ae38e003e671a8654022adce7788e` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-alias-propagation-positive.json` | `8f7ad1be5b9e16a030c55c6268651b1da066282ad97753f6c353ffbf62c20dfc` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-argument-position-negative.json` | `36349c73c1ad37379c6a5804a3e1d528a95f2e4dbb65fef11ecca0d6507fef3d` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-argument-position-positive.json` | `fd6ab4d9a1e7e36ce86e9f78a81b6ef1736015dbac5a6af46c21eceb589c6e53` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-expression-negative.json` | `73e626233b2356cc42fc89f7c62641b66bc9e74c56216d2c785bea4636586c11` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/bifrost/dfb-taint-java-expression-positive.json` | `40c5c01fc0eea392c7652544352de722bb09143a0993e888ea4eaa0f6ceec70f` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-array-element-negative.json` | `a048bc9ac18d68789f3f9436947b39a9b3e45d4390972687c30d0198b70a7353` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-array-element-positive.json` | `223da170d7146cbb09a564488b2d1bd764661ec22788b49d519b5755e3c393b7` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-java-branch-join-negative.json` | `3e2aaabe7ef93807b9085d4ec52cdceca8e0b932a5c08c47dbb88147c96ac7fb` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-branch-join-positive.json` | `5e369b8887893c2af1d27937ea8b55834487adfd6473bb200d8a09da8cdc4f2e` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-call-context-negative.json` | `2c75f52a5c8895f0544c8990c9a0a52c0ad12fc49011d77be305ad3429b2fd81` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-call-context-positive.json` | `8cf3b8cab9a313227afa70e49040dd6318ae8c5fd2d6a79aec4a8b5d664da30b` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-direct-positive.json` | `946c0e71e6862e06e50a5fd1868ea22fbea48d6810f16d8b4e8fb9c11c96b02c` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-explicit-negative.json` | `c1465e0e0c0a47171a848fa6db19c17189ebcae833ca760e13044321df6516e1` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-exception-catch-negative.json` | `4eac62c9c8a4869b684273c2fe1b4a69f53ff93b298dfcad767de367cbef9964` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-exception-catch-positive.json` | `3c4fce0fc60355f472b42f670f7cc3c1961b0fbbe4008e973c46f0bf14b0a5b4` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-negative.json` | `9467275d91abe4bcae74a25085852b42a702c8c77de886eb688b66c4240f05e7` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-positive.json` | `31c49f1ade3803228db67039e348b3a8cdb329bc3ff09e40830106d31b408337` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-chain-negative.json` | `83b72489e9af1e9710874c54af47f7c354106e46024072b54bd1300744cb92ad` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-chain-positive.json` | `1050d203138103803d1fbe2f73da5913c14b18e0ce1c6080ae699afd8d39d86a` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-java-local-overwrite-negative.json` | `c447539d7f07f5009c41220e938bbcfa2a7fd9095eeca96b33948ddaa4ff052c` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-overwrite-positive.json` | `f7d7c445f30ee06508340bd3b74955b94965f12a1e561da4a36d0fa4fc6141c2` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-java-loop-carried-negative.json` | `49a91f72b1588c5f9ab637e7285b32581cf4576f1486b6d1ae3863c8acba8c31` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-loop-carried-positive.json` | `d394de2cd081f8c24c851581ca61b0429f6eab620aeb6db9f391822872c63d95` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-object-separation-negative.json` | `acd315614b958b95338fb4b0509e736a1a94f35209234a67867c756abc47b8dc` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-object-separation-positive.json` | `053a1af368d159eb5654efb8028b6602be0d46fb17095bb0bcb4355049b31a16` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-negative.json` | `e542962577774861cefd96ba204f341138c5f65b6657a09610b2e7ccd15481a9` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-positive.json` | `f1d8cd23f235acaca6697350ac0c272f5d9f07afda89e2061d0fd458774db567` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-negative.json` | `2a0d7a4dd6b6fc8e148cf13344fde1ec3de35ec87be9333817cdb166b8afb747` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-positive.json` | `3ba0e61b8a3c560423083840882637b936eec6c59f991bb59fba49a08584f6cb` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-same-object-field-negative.json` | `7a6894903893a1338ade9459bfea5ab514348b35b3e9f28daa4f89e10b9d1cf9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-java-same-object-field-positive.json` | `2ee7e44b23c91c2a814c0dd6a7c3f264cd97589e7c5d615edac6ad8b8115c42c` |

## Language `javascript`, tier `core`

Outcome coverage: `reached` 14, `not-reached` 12, `inconclusive` 6, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `heap-field-sensitivity` | 0 | 2 | 0 | 2 | 6 | 0 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 6 | 1 | 4 | 3 | 2 | 0 | 0 | 85.7% | 57.1% |
| `object-sensitivity` | 0 | 1 | 0 | 1 | 2 | 0 | 0 | 0.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 3 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 69.4%, FPR 36.7%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-negative.json` | `196a24d9bcd1005da90c9e4df0a908a76f449e211603849680871e3c67eeeb3b` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-positive.json` | `0ec8dda2bac1aaf0864f8167d89a1ba6db4e0980bae1420e35ef162f463ebf0a` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-argument-position-negative.json` | `d36b266852aa0c3fa334aeff8ba1f726651b22f1e7747edffc6c81d59a0e7649` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-argument-position-positive.json` | `3394a8dfaca7aac0fce69d6abc48cc65690fb9e53ade276a82e89e1286c41919` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-expression-negative.json` | `0d8df4cbe8c285274be750accc6375ab562196f928e85474aa4c42f92f4c9fa1` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/bifrost/dfb-taint-javascript-expression-positive.json` | `42a753b77c9e24336c168f012e1a9c808ce9143460a691c4a92493882d0d2327` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-javascript-array-element-negative.json` | `5ecfeb606e945d4d888432e599b566cf20b8e398588f12c477a0c77c6b1be1e0` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-javascript-array-element-positive.json` | `856a504b980b663891357f328d2d515b1b08591b670c995d50ed0fc558c38145` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-javascript-branch-join-negative.json` | `36972dfb5e0579589e0bb7ab6cf846e3da6345eb938e68c8874ca167e7a079c5` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-branch-join-positive.json` | `19ed5d4bc54b62e505988e6e7901d6a490420e9b0193dfd05aa15b1544503efb` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-call-context-negative.json` | `377e100d3752d12ce59aa65d957aa343f5d2e0ff54fcf2e4d5906e027508e4f5` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-call-context-positive.json` | `43d668cdd2603c8feb347f7dec014564ba68b6672dd16402957d2dc77ea3f855` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-direct-negative.json` | `598e4457c9f683061c9722105908cbb1ee428f23e88d05c8cd46d08966ba002d` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-direct-positive.json` | `5cdf3315261af94082ef8421437ee76b4eaa9c44eb5e67423b122c0000fa19ae` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-negative.json` | `e73d4f5d9543fc3f0d3a62f7433563256055562980d4bcb9b69cd9e745c72071` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-positive.json` | `1537fd0da26d52a1ef43f5ce88f107b351d2edd6037ad7e0b3e6a47d135ab83b` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-negative.json` | `8a392f7803b3269718cd8091065980f24ddca79ca113d430c0d05af7fc02d1a3` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-positive.json` | `5b9e6fe1f813db759e43e3df7152d29307d45f97265b6a77e465a3223a110b1a` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-chain-negative.json` | `bccf75897ba2d8ed58102653d36a2f699228897da0693c189511ef4dac39993a` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-chain-positive.json` | `e5f7e72d905a1a4972057abd598b06938bf1c718ccb0cd9b5ad635ae8ad497c4` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-negative.json` | `9a532997e9b75413503f9495bb13b1f63d8f7102029672d8f5835d0a5829afe0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-positive.json` | `593df760eeac7d30467f695b24e94ebd4ad9c290613623a2da38274728afa819` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-negative.json` | `7e1238c7565d742183a62e402b17eebf2f1b52c8d2b8355452c7095e338cc186` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-positive.json` | `d9f0529fbe780116139caa18d4ad64a3b8a9cf6025e04c31e3d371e6c1feb85f` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-object-separation-negative.json` | `a52f2dd3982f430e415d1a1bc221add55bc79e07f0a166db128fad715d273627` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/bifrost/dfb-taint-javascript-object-separation-positive.json` | `b02f04ce59d2baf78ab21a32375f57b5cc388b4afb4601cc3ca35931ba3108d5` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-negative.json` | `9f8d1addcfbca569dca9db695a849bdfbf8bf4505828fd5aa9b443e730925473` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-positive.json` | `6592817f7232cfd5fc3894d21e46f720a3478279a38f589f90c5c750ee1ae88a` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-negative.json` | `74df14047d77cda4220dd91fd6cb115f0d05f2f47cffc9d29a0306fc3b8abe5e` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-positive.json` | `ccb6f17dd230198fe9c88e45ed21ce3581c52de1fcda8a0b04aeb72f1c221024` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-negative.json` | `d3ff468dae944cad068cf60a566fc60149cc25728e2f1ecc89bdcacbf7c69590` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `not-reached` | false-negative | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-positive.json` | `69fe79e71ca3e8c3da2f29c756088f3fb4536d26c09f3b95132f5994a2b652d8` |

## Language `kotlin`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-kotlin-direct-negative.json` | `35ea9b3c1b3aba626a5b5cbfb0088ecbd503c8cde5db42e1815f7bc1f7821976` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-kotlin-direct-positive.json` | `e3f7bcab6cb2f63f235971a2b3d2f073f880c051d291ad851604cd373b092f6c` |

## Language `php`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-php-direct-negative.json` | `9c3983f8f3fd42cfb49122472b725574f94dbeb2f057b1ba095fa2c747b0a216` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-php-direct-positive.json` | `887427f0f43822489bc2448933798321f546e5de50c5d65a2f0f05908516e38c` |

## Language `python`, tier `core`

Outcome coverage: `reached` 12, `not-reached` 8, `inconclusive` 12, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 2 | 0 | 2 | 0 | 2 | 0 | 0 | 100.0% | 100.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 5 | 1 | 3 | 3 | 4 | 0 | 0 | 83.3% | 50.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 2 | 0 | 2 | 0 | 2 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 96.7%, FPR 50.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-alias-propagation-negative.json` | `d90226375a17fd01647811acd7b9d9417d6409fbd6cb2248ff21a95a0519dc05` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-alias-propagation-positive.json` | `a057e168f4480377aa483516aaf547dacfb1d554cac09a290e69710b602c7031` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-argument-position-negative.json` | `052b5304c6745b113abf0a8f075b285746a646a8c1d1ad659ed0220f4108576e` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-argument-position-positive.json` | `01206377029072f8ac1b5d66093e8253c392163d7acabc294c5993e9c85034bb` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-negative.json` | `7383c7125a347772ea86062c7f6f43475159f1fa402518af7adeb58bcc07c157` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-positive.json` | `594837ba6b0035b36c8cfce9cfcbd0d51bc192d5d5523c1c5761bddec1adc7b2` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-array-element-negative.json` | `cbfbdd064b3793838ad30afff79c6637bd847eee916133a46581150ec4805513` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-array-element-positive.json` | `cbfbdd064b3793838ad30afff79c6637bd847eee916133a46581150ec4805513` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-python-branch-join-negative.json` | `2e9527bd6a69c257079d1c596cfa31d47b2c891b66a51c86b13d00e679aedcec` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-branch-join-positive.json` | `6fe8d582f69901a825a1b9ebb4ddcd85274a3e2d553f6e455543a13f164ac17e` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-call-context-negative.json` | `c1b45142583effc7f910c987a234cc189bd680a282286ed21c60c76762fb43cc` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-call-context-positive.json` | `6400757e544e6f12cf34baef7b7a0a5a5e0f81e0e1515600dac0d7bd6c0a9553` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-direct-negative.json` | `70a7b78d8ad4a1f11788d680c4d35abd28091ab4220004bcc9c3643a595cd196` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-direct-positive.json` | `a3647ed1074deba833fe38d289fc320bd22277e18280584b1647a85819d6cf32` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-exception-catch-negative.json` | `b282fb595820ecb9470b3d8beac2c961685fc49799d3d33e08fee2bbf6fe472c` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-exception-catch-positive.json` | `1b564092afb543c1c40a8c1f406977fbc8dd2b1c8bb25ee4c4edeb3dc9685072` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-negative.json` | `62c76b450925b9968a99fb74a8ed7993dcc6a0d212f9bf3a9619d62534611ae9` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-positive.json` | `9b34f8c804845e3f83b84dd64b6b51e59e745eb866d90665403ba04a3e990a72` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-chain-negative.json` | `6dbeea9a8fbbd6d106f0b12c883b784979a322d5ecefa1be1396b1afe61c7ff7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-chain-positive.json` | `ac2655fdd5777591cd2a8f734cb8dba9acc0bcab19a70a930300607d560faa71` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `reached` | false-positive | `reports/raw/bifrost/dfb-taint-python-local-overwrite-negative.json` | `550f11f167a4ce5c7257f560f8132980a1a488865ea939e817745ce1854b40b4` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-overwrite-positive.json` | `d2242223446db4f3c4f8f2c3a6b0781bbf5bf55bcff66cfe68bf4f0507cbd1d7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-loop-carried-negative.json` | `ec776385a6fef024b49d48bd3b8c5f59a112cdc69cb9ef2612cd9274c98ff76c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-loop-carried-positive.json` | `a80ae6520d6c84335d4902fc94c0ecc98bf00da98b5d84bc6edf88541b911c1d` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-object-separation-negative.json` | `f3e3d5641b6a1581d6f4f2b741fbb8d410e985ec5f0ec0c346e657162c258689` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-object-separation-positive.json` | `eb0d22e3f1b44d809b98d1534fd362457204eda3530fb5866db1ecaef69e48e9` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-negative.json` | `55a47bebec3438d775576c298a5ff02e125f561a9bb90ea8890a10beb02a3076` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-positive.json` | `2cf3ee39b212e2357b436195d21e367a5e7484b8ac2caee048294ffad74bb49b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-negative.json` | `f3aa91484b3ea0fe1b958528a472484fe834dfd665089261f2291c6154b33a53` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-positive.json` | `e5be9d1ab62747e00dd40cac3d4434624ebf72c877d837ac2c7c39ce29b7dfbd` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-same-object-field-negative.json` | `5bff7c7d8452c45bbaf6938b2b63791a3b4d751b814896919577d3fef6f0650d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-python-same-object-field-positive.json` | `81d76dab61f37f0ee416d26ddaeff4352f376fc4c4f1f29ca6ba03a7f2de6886` |

## Language `ruby`, tier `core`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-ruby-direct-negative.json` | `fd22b9a33fd48b1948e9b2cfdafa85e2b83e78c0aa60bf02d96fab9e5ae8bc20` |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost/dfb-taint-ruby-direct-positive.json` | `8401aa048236c1d240285de7c5a69615fc01a78c9e81f37f4a4a08e0d227d905` |

## Language `rust`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-rust-direct-negative.json` | `f84301bc65ebe461cd7f9e8b2ab5a44c28346b77f9c1ffe375e1e8574b1c6678` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-rust-direct-positive.json` | `01d215e9d28b8564cc2e3f06b24da7f784af6b642ec9ac6534c4f7ab6f59c3bf` |

## Language `scala`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-scala-direct-negative.json` | `5043395dbdccb9a82f371ae3e2204becb12cfa7affee4129103129819981e4b4` |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-scala-direct-positive.json` | `57bd29932e61ef12a150882f8ab46f50cdbb4ee69279ec06ea5fa7de46395067` |

## Language `typescript`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-typescript-direct-negative.json` | `4e2a7e0ad011757726494cb7e89f99ebdaf469792b0a2779be93ed32a7958e91` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-typescript-direct-positive.json` | `d80674b54ebb05135ece212dc89ca9697714d119c0792607aac92c11303003b1` |
