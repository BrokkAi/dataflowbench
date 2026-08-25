# Scorecard `codeql-rust-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-rust-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `cc2c728b66e0c273545e3531a672c0987473f3830f5df80b0839f5d04c33600b`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-rust-kernel.json` (`sha256:30882a1c1aab9919ff484a89166f10ded6050e9b3ffef37f1568c6cce605195f`, normalized `sha256:30882a1c1aab9919ff484a89166f10ded6050e9b3ffef37f1568c6cce605195f`). Generated from freeze manifest `reports/freeze.json` (`sha256:91b0008a546e6b782c1b790f174a71ce44e60039239797674eb49ebc6ac6c366`).

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-negative.sarif.json` | `65e21b676a514e6c8564103b2d009c40759c87808545bdca74bcb7ef6e64006f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-positive.sarif.json` | `bbef3414e0fdbd7f3e858ebd4f8b478fc04caaedad333159dad062a814ff332a` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-negative.sarif.json` | `c1a56188202cdddb7ce1e81f31105996038ea5f68f2ff5abd949f8a42c3daa57` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-positive.sarif.json` | `8171aa15b20e837409603ad8da87c4a8302554ee19b63fee8754e0dcbec2dbf8` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-negative.sarif.json` | `f514edb18a73b8cdf7806d435449278b0b3a7dca549e99b41063627cb9ff41ed` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-positive.sarif.json` | `450bd39f707691632421d4dd5c7bc9341ae0e1a1811647312b1508cadcccb024` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-negative.sarif.json` | `1f03b301a5376a336665175195aa20dbd41a12888ea1170adbaa0ff8cb09ba20` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-positive.sarif.json` | `880ba6992fb1787b7fa4485df4a02b3bff8635d0a2bf101f60609817991c2946` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-negative.sarif.json` | `5a68d6f61e59fd93d0bc464d40b4d11234badf856443f62b19dbe25be546c9f8` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-positive.sarif.json` | `c5d489001479b11bacd0d1a05649f28805762ff21f9d805f468bc4385207c6e0` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-negative.sarif.json` | `e39be9f23da38ce384393be81fc12bc65fdc4fe59cc6d019ed2c554aad485326` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-positive.sarif.json` | `7346e0aa7451f17ee019c353492910ca42ed800211c6dc0640dfb5b541dcdc3f` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.sarif.json` | `96fd1fc75f2d95d346e8d63b6614bc740682fd092c25b9e2c482a2a2e583a97f` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.sarif.json` | `0fec5c17279dcb6d4c02ecce498f73421c0fc7697e1609cdba66137c982f6817` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-negative.sarif.json` | `6b9660e3e6c2d57247938d63c4aad90ea08cda5370a63b6b762d1ed00f1682dc` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-positive.sarif.json` | `50640f04aaeb4d8eee62ca4e2c6e172548fde9c1ad9d47c065eb63725b7f0628` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-negative.sarif.json` | `8d8dd5171d3b43904942981e9c2fcee3ddbcdaed4a95471dfe53020600edaa62` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-positive.sarif.json` | `88b0eb59e682fa7c4bf9a7ec484e1f99c2955b8c8ce807069d840acca2bb1cb4` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-negative.sarif.json` | `4f2999c094087ffb5ff6bb6a70498f0515da6706d3c194e9aeae78ec0a551b67` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-positive.sarif.json` | `811bd258775ef045c3f24ef44e50e161bab9b3f2967046a4af675937cc3a0351` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.sarif.json` | `445756ecefe6649a7e1473eae5de7d2e7c7a9951435cb1f71d287b61d65057ba` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.sarif.json` | `d9ba62382f725dafddbef44523383ac7e509b1a5c7a6f32e408d19221994aff8` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.sarif.json` | `03757d7a099e83419b87010378dd3277203572296d6a428871a3849981a8ca08` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.sarif.json` | `37ad834cc21ca7a04394dfdc1a84b92cce349a5fcec8a64c17528b8453c4ffbd` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-negative.sarif.json` | `0dce04c26b6335a399d3a9a0d251fba0c5bac85fdc46e0c76bde5f2e411be835` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-positive.sarif.json` | `94a04ebc93c23e745cda4437119cff93e09135699009afc05549149d96204053` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-negative.sarif.json` | `360e7917d7fb1dd742388276f3ea83081884686ddc88c6e647c606e9cd95e6af` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-positive.sarif.json` | `ae8135616721b99f03bfd458c2179ae517ee81beb504507bd5e3a1d7ce6ed9ac` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-negative.sarif.json` | `75d782037051211a303b43f1e1689c0e333754fd29ebcd79d0c3751690e11c9d` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-positive.sarif.json` | `7a9d4d14daf4333cd50d63d6faf6749d029c076f05c952280a04afd2bb2bf359` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-negative.sarif.json` | `086b72914e8990fbe8320ff4c13946533b41b142f72be7d82f34f76f20dd7172` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-positive.sarif.json` | `7f7f0c7db0d15bb0123c803225eee9afd48a923c7300f336ceb27e8ad4f54a81` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-negative.sarif.json` | `4a35b8a17e24041a179f009376cc146a5e92febf1dfd7a808ff098bacfcfe2a2` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-positive.sarif.json` | `6252b5001bd6476b23daf27d30b6971b472ff99f00281fd94593288ce5e4c11d` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-negative.sarif.json` | `4f8bd1cdab571051c85bdb22214f1eff07dc0b7664d5df1fb3859acf17a69231` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-positive.sarif.json` | `47eb8661707b2eac0486262b81bc7ee60e6889a6b4582c1eec30ec35b86021a5` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-negative.sarif.json` | `b562f57f613b74ce984efe64405c304f48f545a88103936dc18d4a6a6d2eb491` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-positive.sarif.json` | `e8980c2a01f1145029c33592212bee69c23cdac1bda3e9b9bc14dc76d0a13f1d` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-negative.sarif.json` | `f977fa8758eba450f1d22879ce092626303fd7f98a486b35bc7c1d6b58bd5376` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-positive.sarif.json` | `db299d413586e062b954b1f9a0214e5ccb04c0e02dadcdd16174e2f9876da1e4` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-negative.sarif.json` | `2609ed3a0ac40521035568690ee19affae529b49439d1965ab5077e93c88990f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-positive.sarif.json` | `37ea12526b69ffad5722fabc2db8dc02c6a391e291556aad472f2ac4382a86f8` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-negative.sarif.json` | `74471ab1796da863f4fd41a81a5a4578964a9c0a66948aa1702ce70361244daa` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-positive.sarif.json` | `6d80cf64aa8c91c1cfa6cfa59aa4315bea4968fdf958001c1fb8e06354139345` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-negative.sarif.json` | `8b8a4bdee1d2092a9beedd91cf649ec2dab0b56a26adecfb707cf460813660e0` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-positive.sarif.json` | `317a0ddfe6c882976e9dc7bbd9ad72e521d610de6adb053f0cb0eae8eeee1866` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-negative.sarif.json` | `ad97cac3ba774f5c2b47b6bb4bcd23ccc35c417ae73b7854bc55c4cafa423caf` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-positive.sarif.json` | `25648402820fb819b1440bf50cf3675ff4953dff138a5b11fdddc463b33d6125` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.sarif.json` | `17818630829df7cbca350a3b4c933eba8886ed38a20535ca79f080fb220cfe2a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.sarif.json` | `31f05231fa29ad156d05a60a85f4549e5c79fae98192e21b19e860c69bf05ebb` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.sarif.json` | `55675739c2fea69487c764b78dd1e1058fb0a0f7fc8ecdf8170b201d8216e902` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.sarif.json` | `82c12fa53192d58fdb609932e4c6cada776d64ddbb9ad729a495ac190548fc2a` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-negative.sarif.json` | `02cdb79d4e5d1fe7b7134e73f88a69bb322d46da0a52a2195ffa071580d364fc` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-positive.sarif.json` | `2851c15b3de4d49e59eba48da015fd055a38d200e62354f8f69cbe79184de146` |

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
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-negative.sarif.json` | `565863b76e6af981d8635b81ab8dcfa632fdab574847fcb82de51c3181e54a59` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-positive.sarif.json` | `ee05d5b4fdc3549632f0310d04ebe5ff911ceccf733c879fabb17bf7800e4a68` |
