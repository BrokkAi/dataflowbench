# Scorecard `bifrost-c-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-c-kernel`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57`, adapter version `0.1.0`, configuration `345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-c-kernel.json` (`sha256:8148bfd8f2b9f0b0155dab3b0301d00612aef085dc330a6a2a2aeb8fc29e9662`, normalized `sha256:8148bfd8f2b9f0b0155dab3b0301d00612aef085dc330a6a2a2aeb8fc29e9662`). Generated from freeze manifest `reports/freeze.json` (`sha256:3228af686d09f8666989368483bef375bb28b94025b55e31eaa7a0bdd29506ee`).

## Language `c`, tier `core`

Outcome coverage: `reached` 20, `not-reached` 20, `inconclusive` 8, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 2 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 6 | 0 | 0 | 6 | 4 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 6 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `74eb208617d725764525f6497a9191c56241143514a6f7e4a7ce030566bb403e` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `ac9f147ea4cd007056975810557630f0c036666eb5454fd3a3d81ccb68a31c0c` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-negative.json` | `65008c9a2dcb5947f26e7d818b801d9d547e7a0d1e53f93a4bc7091e483176d8` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-positive.json` | `9d9d7de3b9fdc3c0f9b70d9f514561ee5eb36bed992cb5af2bbf63f164237940` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-negative.json` | `6eccb86ffde9b7ca7716f5f11846a7e373e58123ade3a6037bed526c6cee9d6c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-positive.json` | `94ee91ae9a97513293343d77aea491656f890e52fede7d96180f835611089693` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-negative.json` | `27796c4ac4600117a65b172ea4b0ccc64710036d26a1c66049c95c0418be11d1` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-positive.json` | `989806d41c52ebea8c7e9ce57db479723bb12a7a923ae6d83c75b39b8b773a8f` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-negative.json` | `29471f7335b81a099b3d420a262009acf1882cb4a513adc814a51210086b644c` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-positive.json` | `435a9028ddc3c689cefb8d28f6723a513b7a507d795b20a16c9b91fe51a632a4` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-negative.json` | `08c82e88705cadd9761ed574db51261b2abcacc2375e2d3155ed6442f7a98695` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-positive.json` | `99cb3096ac1ba19fbddfafcfe6c9f02dfb9cf1512e0d22dc850eeb917cd973b5` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-negative.json` | `efce0026757844d2c1b1ed45d99a064d567adb52aa1dadf661fa40204cb77196` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-positive.json` | `feca7590bdee3ac3048cc2232dc76dacc1e10abfaeb2b9b44cbd1ef2760d2465` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-negative.json` | `765929d24da864657f7ce51d8e4bbda468484d5881485149eee9d360d41b8745` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-positive.json` | `26cb2a47f2bfaa009ec8a9b8d0f6ea27afcc3267d75f72b9e405268296d0835d` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-negative.json` | `01128becb26d27cb7bb9357433ac51f0f18961338f3c9750287edea109fb475a` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-positive.json` | `4c05bd719cbc1f328a8a4e30bac47762991fb9ce15e706daae576995688f2e91` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-negative.json` | `9a9f5083c3cfd031a4dcae132f15af17709cd6549fbf87e80481e9da5fed93f1` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-positive.json` | `9a9f5083c3cfd031a4dcae132f15af17709cd6549fbf87e80481e9da5fed93f1` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-negative.json` | `c653abebd86bdb2be6402d253a540cf99d7dde70cfb5559d56fcab3d46bc656d` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-positive.json` | `c5aaeb9e77d5bb115520bba86c730c97e45c21ab74a7d6493185775ff1d0824f` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-negative.json` | `a5c6b6837750976bb78959f6d6b1ffc820623303bd1bc0dde5b2f4e268f45e64` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-positive.json` | `593f92d219befdff361fd5bb660095d70ff4132f7a224d73f977c770be450d88` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-negative.json` | `a6ba70ceb2ed82e672b61a4cbfe87ec3d3ba8c644f84cf01b839e0b47a6aa06a` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-positive.json` | `f130f9444e6ad26ef7bfc7e5942d8b44707d86ed81735ed6fee63a693415d25f` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-negative.json` | `75b60d15cd664c3a614c2c0521810ba694ab8a112247c6170ee74ad0214a0f34` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-positive.json` | `ba2b7e1334c960bbcf3f0b074214df560dfdeb9b5dee978eeb2e1127a94fd230` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-negative.json` | `907e90e21a55f56f70671a9238a69b5a1a49b34f79ff3f67609ff71c1519fb96` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-positive.json` | `ad13ff94635509e138111fe56c07e78f9e7ee9f7e86ca57108cc679a8b31a2f9` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-negative.json` | `7010e1a9bef6879eb33e99b04e29a35727328e0834a7831c53de10484c1f1905` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-positive.json` | `0bd7f089f7f3f567329165ee0e1f6783b735703439456a3315e9f10625fea0fa` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `3554e6537c524eb085ce05f3d00e400f3f6f48f52f7e197567cbcf8c7403933e` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `f684934ccb3d53b8961b656916cc6f68c90816e2d5b86dadd1c2fa664698bda0` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-negative.json` | `9b2f6dcd33c410ebe5cd1e80515bddf3049e81326513a8c520fe2eb1514d36d1` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-positive.json` | `cc1b796ee56954b5fc62270ef67a7fa3a161a5bd575b67acbb2de1227de83e00` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `457decb8a0289be91ba328dd39b6fb933c08672067dfb716ea14f539b15dacb3` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `89b9ecee53720f3317f133568c6d7a3b75b9063fbd7ea750bac9d1e75393a1c7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-negative.json` | `ef00e8545bdcb0cbe91121283803e36364a0d81c75ce6dcde2abe4b260d13aac` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-positive.json` | `10052b9e075488823d34d9c48d548dbc41efd0fcfde52165583dab48a1108579` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-negative.json` | `375d8dc7f7a83eacecb0fd9f6f8dc02dfa31fdebd9fbbd1e3c4de690f48d2e2f` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-positive.json` | `71940b6b1a8418fe27e0ddeba6e8a78dbd3fa530098bb003618366e3359c88b4` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `354d204cdc7c21161f5693e9a350c2611e425eb32f6766813e3e605156537fb5` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `cd80a923d906ea2c5a3ba0fee3484d350524d4ef8aa2e449d3179bb1fddc6818` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `61666dd7209535109bf9cf6bbf346720491b228c791665c11db777ce36222f4d` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `a4b85cd095d97f6b4d935ae3862d2a74d759b9a5bf1e4e6f47d409d7034100e2` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-negative.json` | `bf7ee8d8d63fceb2121d38222a6e133787d85355299f932cb1ec2ed4182b289d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-positive.json` | `f84e9cd03fc8f2208a78406c602babb720b56b5a32ed49c3ddbeb38ac2c86526` |

## Language `c`, tier `language-extension`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 1, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-error-code-return-positive.json` | `13cc2526d603f6ae779f09f3f2fa2810628075f14f4cddeacb43ac0dcfcfde79` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-goto-cleanup-positive.json` | `082c71b1b14a63ebd1b9fff1139884d96fedad6673cb2092b04942c4eb1cdb6d` |
