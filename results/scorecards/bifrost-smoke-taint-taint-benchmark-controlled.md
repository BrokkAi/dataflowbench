# Scorecard `bifrost-smoke-taint-taint-benchmark-controlled`

Adapter `bifrost-smoke`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `2c5ababd371ee6b9f4f0596c570d2378aea79cc2e21c8a3e7e0eb0a195f63911`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-smoke.json` (`sha256:750aac6c3b9ae24acc9b3b656c80bb9b5f40001add6cb345798c71f0fd335e54`, normalized `sha256:750aac6c3b9ae24acc9b3b656c80bb9b5f40001add6cb345798c71f0fd335e54`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

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
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-c-direct-negative.json` | `f250fbf2760eb7ec94784a348c906e94fab67e1ca9f2f29fd81805bb448f499e` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-c-direct-positive.json` | `4b2493d7f09ba4ac2f0d85a07f0e67ceca9ca67815f6a0fc2eb4bc2f19fc6dab` |

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
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-cpp-direct-negative.json` | `ca4f1bae08a26f08d7caf84ac803f9ac04a19c7fbb48b0e43ec66504645c6ab2` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-cpp-direct-positive.json` | `d9ae45704391bb262b7311d9b0e11c695cb2cec3e0e0d587a432d1866d722f56` |

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
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-csharp-direct-negative.json` | `3fc97dfe72991227a811e9b4039503df658e94a77d1b6fa0c9079d512b831501` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-csharp-direct-positive.json` | `cc7ec0532053a25ec4b9a25028e5ae67a046211a3e3325d6ef84cc8bad20a620` |

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
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-go-direct-negative.json` | `538ea6994073a2a5efb2285e39ae0da5ebd8dc1a20aa3f0faad77c06a1a13a0e` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-go-direct-positive.json` | `4470ea080f6f763d6f27eb744bd0eaea181e2306c5eeb1e84460f5c0aaed55d0` |

## Language `java`, tier `calibration`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 0, `unsupported` 1, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-java-modeled-external` | positive | `unsupported` | unsupported | `reports/raw/bifrost/dfb-taint-java-modeled-external.json` | `01be675e06e4fa5eabdeb5725a1e06efa319ac6156f2e492cd1689c69e29caf0` |
| `dfb-template-one-hop-relay` | `dfb-taint-java-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-one-hop-positive.json` | `2b795ee9bf844c1c3fe5a10e3e9b6a7f9068cf8bf59ec01bf69d0b8b23a7149f` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-alias-propagation-negative.json` | `577ccbd8d520bec0adff3fff6ca97bc79b986a29bb276b09a6a4aa604d1b3bfb` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-alias-propagation-positive.json` | `46c5f17158abffb3f6e254f400cc32cb4c5e86297d7d232251d962a446e72767` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-argument-position-negative.json` | `c93d329e59cccc4761f87063338075b56db1ff244e67b584d09e9eb897f02902` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-argument-position-positive.json` | `d5bc50ed1f7c5d0ca89861513c3ea189bb5bb5b427136aeb3517f9f671414688` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-expression-negative.json` | `2f08a94f4505d6251acbbcad016082ba7fde325eecea4be950846a239d1ca11f` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-expression-positive.json` | `73ffc351fb9b5ff120d66cc6aac24e9ba829aa5dd3a3f43c5553bde99fd49ca0` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-array-element-negative.json` | `11b39db7359bc318fd3f8c018f48f6b9ce3203475d1bb12efec3d4b135da660e` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-array-element-positive.json` | `960c3b72723fe344ed90049732d1b845326c2c7b6fbf06d2f2666f31372e5cf7` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-branch-join-negative.json` | `e9aa2e7d5bc00a113620857d1bd91eeb0d6b173ba0433168c5de6ace44bb7a53` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-branch-join-positive.json` | `78a727fbb90427710086e845380bf14818b3d3484548e63309454eb8c231ef95` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-call-context-negative.json` | `52c1732a84c2794c4a92194d029a02cb174069787b8aa38999edd62519a62745` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-call-context-positive.json` | `6f6919702a4adaff37fc5fd7380a61fabb99ba247349efbf7d9fe139b825c3ef` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-direct-positive.json` | `3a6823e94794e4650587786fce2105b48d9d6aeed780db0cbc348c75b3c28b68` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-explicit-negative.json` | `09ecd35c4c47745594773d65757020e31221b5b6deb8f43bb948395e21b8ffef` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-exception-catch-negative.json` | `7125d464e54317711235ffb6d10275469dbccc662c735e8166870d325d738eb5` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-exception-catch-positive.json` | `02e48994c2c677f3c9471aa1b49a6bc590ef2a4967ee979baf0fb0e219285aaf` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-negative.json` | `99393245fc6a7b8a43bfc4b7c431e493d47578bd8ef3d806f0bb16a7af1d524d` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-positive.json` | `a232a70fe9b6ff76b980fb9f2dd86d9abd37d3f8e0b3804462609301b3015c91` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-chain-negative.json` | `c51fc9127d85530735bb635bea9950bbafacd032cad2052cdbaa9cede36e3797` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-chain-positive.json` | `6aaf9b586e20aff78110aa68432ca1aa1a7db85bbb391ede0320b35b22f47dcd` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-overwrite-negative.json` | `4be6c96beddee715139924ddab4257ed3f23b83f0262660d3d47eaa4bd2a02dd` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-overwrite-positive.json` | `f703ee4a5786395d0b90b4d70146288389b7903c9d871ef9955418f861952468` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-loop-carried-negative.json` | `3db5578f04b019932e9bf934117bcf2f06ee0388ed04fdea3d8fd881885c27ec` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-loop-carried-positive.json` | `bd1befb63a9ec9d5ba4aee357ff9f186cc7ba8015798f69072237bcc8f048588` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-object-separation-negative.json` | `a141e122c4473721a855ab5d17656f067d60f792a534b370ce745d6a540a9d36` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-object-separation-positive.json` | `1c8e37069bb261eab6a0d4bfab2d43b7010365f44afb724a33f76e4998f980e0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-negative.json` | `06506eed3e86a5cbfe5cd291a3b028ae87b2273f0d23fe7b1993a5b778e0f54a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-positive.json` | `e94085c098c39b1eb46926b8ddde8b9c04b27835f209ea977066984ab4b80829` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-negative.json` | `3a3fedbfa6c4f045a7282cbe8ebff07dc75b8f474a4d429c0ba0e8c5dcf058db` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-positive.json` | `5770a645019602a2b521128c3029bf4d7f526ed2ceec8c874085a4436d5bc851` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-same-object-field-negative.json` | `984d622f22992e505b35834aea0d34a343e772b98a26742c3bfa809c742e17aa` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-same-object-field-positive.json` | `823ccd51853b9cd51ed4eb27b71d7e55cdfe96ddacee9d61bffd2291706b799f` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-negative.json` | `ca99ac7be536339eb4e92d76d2a88b5b98fed4e3319252fb86711b2692115b2e` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-positive.json` | `71bcc351c9b37c273d9ad66b760ba0fdb2e5fe0dac771c4dbef9fa8ff5130197` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-argument-position-negative.json` | `15f7428105c05a819b133788a14690be34a613b29038caddc71ea5b4ef2131ec` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-argument-position-positive.json` | `3f79b149d3d77777860d1c18ae2fc5cb405b989e9c7c291e0c13c88d4edf603c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-expression-negative.json` | `da389165522a83b9a8ce82325609408c67eb5a2e26a303255e44180f819cf52b` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-expression-positive.json` | `50406ea269ad8f93a7d1f7d731681ab1bcf90c924b57dc7351d7b370c1c1db26` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-array-element-negative.json` | `e93f22a4e8c0ceded3dfdea991ff666189cd3384720edb31b7fa2411ffb8949d` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-array-element-positive.json` | `c6f15b0eb661b38670f532e85c4d800eac0022ade60983a6512ef8f78cbba006` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-branch-join-negative.json` | `761dc63fd73bf76cbaca56b8b921358c8ad89670bfac7efbf6da77396abed1d8` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-branch-join-positive.json` | `85ea3cb72965cc34fedead29e4370373e1696ecf96fa90f85b5c78432dc7e96c` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-call-context-negative.json` | `5d1d65e2d809090212a971c5fcde7489b72720cd45c3b4c179b650f7ed084cfe` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-call-context-positive.json` | `25dd72ef49520d69e9012f9b6629c10bb8dbd65bd59e57ad7563952652439294` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-direct-negative.json` | `31ec1618a1e72f507aeecb8b284dcb2bef8fabd3feae058735df84d333851fac` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-direct-positive.json` | `75ba3c13770d498a7d39977d222217f09197f77bb7da10b6b5d1537c4dba7577` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-negative.json` | `a9dcce91f8858f0b7033f5eb73c97be0b649c4d677d837306b21e30db8706cb6` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-positive.json` | `e11aaa4c7b3bca10085f09607ab2e229229f02dc2a99fd6eca3a6bd1d3317465` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-negative.json` | `ebaf85a8f240b29c90ed5fc6db08b3ebc68b1352dd3d7a9b84b143d05c023b77` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-positive.json` | `a437e69a5c10929917366afde61f9cd6382cea3a93908bfb778a49150e02785c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-chain-negative.json` | `cab103dcfc4ff41362c6574b39c88ff7485cc88852778eea590b30f236da6b7c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-chain-positive.json` | `7453179a337024e7244d79b75fe33ce94f8a68f591b912b1b916c385304d68bd` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-negative.json` | `9de01038e6694fe6e2ef7b9034b968264ed0b0685255605ad03eb3a953af51bd` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-positive.json` | `00ed366117dcb1aa2cca6f1e14fa45ac0ebb769cf9317e89f31f7c0fa645d303` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-negative.json` | `5b02379f3aaf20270c6f6ac9eef83ee2f98f15799f11b15b3ff8f8fce0eeb9a7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-positive.json` | `e0340c808517e373087a2a52cf228c7c3aec5de93ef376c6169c23286a5ccf00` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-object-separation-negative.json` | `d4d0d8fc23d60f92ee51da3f718d23769b4b606606ed034020e494acafcd883e` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-object-separation-positive.json` | `411e906af474fe292e83ebc77678fca30eff574411d21b84556b671c03e528f7` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-negative.json` | `5563fe8e3c176739ed43e85324dd33f5f1bfd33a281d0535bcb35756937ce0dc` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-positive.json` | `07a9fcbb2b96e2ce34cd780c43dfa5f9593153a6e0de442a76be7a7d46c073c7` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-negative.json` | `6b741285ff207571cedd3185d9e79eed994eda74a9a362a21dd9fb6efb8f825d` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-positive.json` | `033c4ea224c9a10c8c74b8f35496e1912cbcc580aae3cdb2343fe2a44f26ef17` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-negative.json` | `06f586ec1966cd11a1bb03d600a357ce4a7c259da7354f1d27208da1c5e9445b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-positive.json` | `32344d9791ce4bcccc68a20bade3e4973e1562d34b577139d988f0ed7faed712` |

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
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-kotlin-direct-negative.json` | `e5c25aaa49aa30e5ffae984893eff740ebd467528db20e2764351192f134c342` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-kotlin-direct-positive.json` | `b9e2bb44c4c2644b51a8e080480035bbbc645d7bcae3db3c5d945ade5c1437e4` |

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
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-php-direct-negative.json` | `793d72d49ae88c46f28919959631d5f547822487dcea13576c731a4db77436c0` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-php-direct-positive.json` | `71ec5cd0282a5ea601c67d3f6d47728edcd3bef9b6a833f1cce5a3d52c13082f` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-alias-propagation-negative.json` | `94085ee88380721d51d835a8e99e0b6659136d1e25981bdbd4ae32469478ebf6` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-alias-propagation-positive.json` | `0d544b1297276e9eab242f2fe56cc46d9f519489dfdede72809145249ac95341` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-argument-position-negative.json` | `51d1e1a578fe1651690f8538cd6930a96d723efcda57dbcba743b6acef4ee5eb` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-argument-position-positive.json` | `b1bed7d944ac808c1ff6cfa511bdc7b50f97736b6d31936afd0bce7ec6ba33fa` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-negative.json` | `60e7a511fa5c2575da56da6526330a0c2faa2e5a897e19deffcddc1022e2101a` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-positive.json` | `8273920be9a71be46beac84a47aeae6d19733a1566d8e0d48c0bfc2e2ce63c09` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-array-element-negative.json` | `175bf4dba09be907975fab2668e4992ca2ad5d3f68ea0d437eaf1e8cb2cca6f8` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-array-element-positive.json` | `386101d64255031aa626549781e647427ed2bdf2450cfb0c673d51012e9cc597` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-branch-join-negative.json` | `a0cb8146d8c0c04f60e75e5d2715d785c67f43e50de4b09c7af888ca2452b2a1` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-branch-join-positive.json` | `67f03998542cad4efaf7b5afe4573a984612ec03edac6c5fea304bc44fd71012` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-call-context-negative.json` | `0d4486c77cfae9b700f51d54580ad67120abaf3b9ff2bbddc9bdb2e809dde6be` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-call-context-positive.json` | `6391928b86028cecb1cc3f4119390bf76ebc403ceb4db7e9338ee3c6d1cb1593` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-direct-negative.json` | `954bae0756d739052601b72ba82aae75bc1983978af4d22b4b292cebc74a781e` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-direct-positive.json` | `a3e2d785f507e27387cee05518aca84bb10506661349777c037a371b2a44eb94` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-exception-catch-negative.json` | `ba0b3affa267afdcee0eeba82004ab85ef3fb68a3971f2b05263f6f16b890de7` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-exception-catch-positive.json` | `dad59df3b3ac2a549d4aa64d89141f9533a64059ff900a32de46f4b34d076607` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-negative.json` | `b217ca1267637a2dcc3d3f00ca9cc58ac2f2227b46c21bf73732f46ec4b54cf2` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-positive.json` | `d00763f02e3affbf3aa571f0bdd1fd989d4dd3ce4ee74c0183d376aa5a59f641` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-chain-negative.json` | `5cab06d54d9ba6da1006ff42168936ed6cf72b38c63bb3ac5f98a9ca38a228ac` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-chain-positive.json` | `c65192339eefd2a68015ce8529abd54f89fcc5d1fb11b235e62f5ad4b00bf53a` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-overwrite-negative.json` | `d99060f6589ce138eb49e40fbb788c91ab0a9c94351530e75447abc7b51fd3b9` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-overwrite-positive.json` | `b5b8be96cfde083258ecdc6dd87e2699a898688a0dc3a44ff5d557157b87a32d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-loop-carried-negative.json` | `235c48ef9f3b2cf93a0832a8ea75e7421ad6ab6d6f3faf2adfff355d0fd58b2d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-loop-carried-positive.json` | `dc634e3a65bd29cd2002bdb1a86bb7b6b7659525dda0f35cf37a4961b8ad0ab3` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-object-separation-negative.json` | `c484fec360c9a264e09c0f7bbc1af02b9f375cc40fe44f0750627fce2a5b6732` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-object-separation-positive.json` | `e74e92944ebe2501fd98898907ea8786c27b823dd1b289d5f746f8a22e8b1b5a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-negative.json` | `d5419469d6dfa827a1d59b5fe8295998abf55fe19a3385b9adfe16302ff89add` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-positive.json` | `0ffffb0521607d9579fda745846a482a59730071f19343de670296ccece2f32c` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-negative.json` | `5bdb0132d72353e7dcd88965fec260e3beb28061370f06e6a3bde8a3ddebcdb9` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-positive.json` | `46df676451fb8632bc718e16d844ad0e0cc6e0e486127ae1e1e2efed0d7d6a90` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-same-object-field-negative.json` | `874485807760638b7937d1e4f5f41e4461f7ec615487bc671f567fbe1fa38ea3` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-same-object-field-positive.json` | `23c91b79a5544cb2b74a9569c7e1bea73a49532ee1211299fb919c1e68a84209` |

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
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-ruby-direct-negative.json` | `fb6b3b05c065efe2bd79af9cfe27c196c85875be4143cc53f60d55c34553e87d` |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-ruby-direct-positive.json` | `7cb70f0166a7499b65caea2ef3d75d73d07c5f0c88f2ce2e8cdf892e4537a58b` |

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
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-rust-direct-negative.json` | `f9c64a3ce358887b424427d85067e0f89812299643d7e824662cbf5081759189` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-rust-direct-positive.json` | `6e91025269043ddca88ede420bed12f7a2f3b14ace3c44141570e699e5680aa5` |

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
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-scala-direct-negative.json` | `b8f8a1ff13b489e8cbee2529d26c21e11795708725ecbcd29c30cd66cd8e1e15` |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-scala-direct-positive.json` | `87337792213fee9eb97152a728aee27824183e51b8f354e8947f54cc1e069711` |

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
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-typescript-direct-negative.json` | `e9ead6b0cdd36c41a3e12cded73d50c8bc6534dffcda6526b1fb936a9a5559fc` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-typescript-direct-positive.json` | `f5794e213d87e1c99346604e80d5ff13fcf02c38375350d3e4e4f3dad2f20576` |
