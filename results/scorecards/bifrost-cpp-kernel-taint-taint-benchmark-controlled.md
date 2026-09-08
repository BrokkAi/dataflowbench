# Scorecard `bifrost-cpp-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-cpp-kernel`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `b29775f28c44e0830155def3030cb36f7c7f8906c440dc18af2be6f7ddbdc22e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-cpp-kernel.json` (`sha256:a6f05a8fbd87f6a0ade9efb37f0dfab284c058ec39301646f1a1a44155155d02`, normalized `sha256:a6f05a8fbd87f6a0ade9efb37f0dfab284c058ec39301646f1a1a44155155d02`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `cpp`, tier `core`

Outcome coverage: `reached` 15, `not-reached` 15, `inconclusive` 26, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 6 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 4 | 0 | 0 | 4 | 12 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 14 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 2 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 6 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 26 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-negative.json` | `fabbe994e4b4b92f8675d4c592f25b3fdbbd67f5278b3f3a16f55c43e670c5fd` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-positive.json` | `46f9396fa4e623b48c351c0cd2b12124d1c8fef52e10233727fe9380a0ea2714` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-negative.json` | `5e775507c3ca85bc8e91bf0816662c67c27f7c86cf1e6a034ef579c5f54f7eca` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-positive.json` | `00ad5760a66dcf80fdb05b709131c9444fdf0736eb76ddd122af247f2e1bef3b` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-negative.json` | `e94ba1d84064793f04d1b92e9dc94ce80fec961ea60e02a40a87cffe9d6be818` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-positive.json` | `457b0400f1431f9340f809bcf001717df674d13917b7c9e273b3fbc5a0b3f844` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-negative.json` | `65f4e936951d823393aa96cb122e3de84068592cf82e25f1628a02dc1c426e1d` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-positive.json` | `23ca3d9fd427b21781be2bf75f521d8b75735bed5368182cca091798ef8908e1` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-negative.json` | `e9c0736658ce23c1e955dc1a1db560b69409da1c8fd04ac1fe4849c51e72fcd8` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-positive.json` | `5ee903008a7d29bd5127b55536b6c9b3694cb274dc76de8cc8e03d0b4a5d2eba` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-negative.json` | `21b456c5f0b188ed24d66d4c86dae3d2e952952bd3c15deef0d1cfd512bff138` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-positive.json` | `79979af04d128e3cb24d8d30a2d2c3c6592c5b9f65098d4b1ab4494c89653f63` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-negative.json` | `860d1ecaa955b0aa44e7e0a8e07158bb9df85c9b15e3aacefa89e961c6d2f84f` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-positive.json` | `e7c64a6b3c72ac84ae6602d7b0efe186dd2268fc0e13eea870fa5f21b7d5973b` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-negative.json` | `e3fcef58153da070e2bcb805d56c6d192eaeab55a275769d8500c8dcd1ae2856` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-positive.json` | `900ffa44f9d573b17beb38219b878d01eee8f8adab819306b191e890aaa46d7f` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-negative.json` | `7054fd1f56d7ee19cbf0a34988f14f499cc9e8a114870d52ed32e3ff8b6d9f21` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-positive.json` | `b62766942aeedc780c44ded02ae9248055fcba78a3754deb5aed0710eb4338e5` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-negative.json` | `55c31b6d7974d0b2e0e45e7a1e7b15476551aac6781416e492c9018f28be7f0a` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-positive.json` | `a7f6ada39bb27d72b7e3951b6e7484d6451db659cd96ef941b2162d62f66301c` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-negative.json` | `6c774bcbc3fcc51de60b417d3777d5212e1330add2bce58f8ad3c01acc63d54b` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-positive.json` | `7452f92508a275b74fbd185a848afa5c3ec2435fe54c7e7f3dfabd53f869745d` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-negative.json` | `a939ac8a8ed1dc783bf76e39f3f58975e01e18b00618749c7185ea66b99f1b9e` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-positive.json` | `f5a283f17d3059cabfaedd67e857f203770a0471d209cbedebcd096828e1e788` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-negative.json` | `8dbad027c966f029ca7886f5cb86e17596e0eee29051e879e6b67abd3246230d` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-positive.json` | `79663af26791f8687c629be9271e829434f7e87a14cba86284db45e975d66157` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-negative.json` | `1651752e1604c134ba065aea4cccb7f17d525fa498647010275d000984031a24` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-positive.json` | `c3ff2844295c2dc3ef501902162fd5167f73c666a91bad211710142d4d90e33c` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-negative.json` | `faee5dfa97eb6e17c193204c78a6a8caddbd6de25a50917e1c1d84ef973fc56b` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-positive.json` | `e3b1625cf1d152064072768e21d798a792759a8e2dc2c8d42fe6919d8e8e5b96` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-negative.json` | `187850bec28dccb8c760e0370487ea8797c9f110781466080e7b18978c1a85a1` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-positive.json` | `5131c466f792fe1fbc2d4ca83d23fa991c2bd2d9d9725f2fb9540088ed24d24a` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-negative.json` | `a17fa7c4935ace1037d3a62e5f05b686e667ec211b108872540343db2f2d6120` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-positive.json` | `706bdc2def9fc7d3bb56d19a7f1dda243f4fed439431df912679f373ed091926` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-negative.json` | `8acde9e80eab562962dbfe7652f353c9cd21f325dd70e403b71baff684a4c3b2` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-positive.json` | `c83f4022a12a6032d5e2046217d7df3b6ab3e6cf7d819ee3813b35aff808759d` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-negative.json` | `285050f45610d4ecd499d64624664aa9bbc7d4c005fbf29974b5fcda83fd82ee` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-positive.json` | `8b2dccf107ab8cdf27e1ab9696f8e4e27cd99b25cad4b2297610d85eb60b5444` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-negative.json` | `a5f4036c1b6e8d0ed99835ea938ac229415daae30ddc4b7793bb3809ecea1bb1` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-positive.json` | `41ad8c32f889c809b7c8ca1feea8eb252878429927f0032c6ea509000b91f983` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-negative.json` | `62deae2e47c34aa179321bc0f1b921cce8449b964bcad2a7709390ec5d794ad7` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-positive.json` | `7400a5688265b60f711715a509096421d965525e1fd6cc2c091e70fecc45f245` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-negative.json` | `e0a9863747cfcc0d0fb5384c4d854307b0e64bd019c30c26e5a768ff9f6f94b6` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-positive.json` | `b628cd10e1484425a47f4f50669ab8915637e4eb6ee15fc0ef75665848238786` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-negative.json` | `7c74552017df428edf47e97238e03bb2f0160b31c45ddf635a942c3185483b7e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-positive.json` | `4ffb58d44e60b812d85bdd71da16c0f6c548fec62f378e14fa23f3c6f67eba90` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-negative.json` | `3de7d3c6eaa6a9534c166b0574c3fb86a43034fb2665318b2d046a42bbce8396` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-positive.json` | `0497d9412b51e9f9812fdff4f0ad02a5884829291ce3d87b83e2f873a54ae837` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-negative.json` | `f9dd7db125f742d6854abb7087b92784ec326455e7a8252ff707798d84047d3f` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-positive.json` | `b77f1d12199dd1eafcbbe0980ccd14635da51ad4dad4530b2f83e241032adaa0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-negative.json` | `a3f8d33282de483a39899cefdde8bc4485fe4aa1a20605ea13592d91498cd0d0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-positive.json` | `1739c2418273c8f8284e61a70cb97fa3a78ddbfbef5399370c0466a666e5f58a` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-negative.json` | `dc8fc4f7c5e5083c86ea82e85dd94e688760c481f268529910d0081e36271335` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-positive.json` | `2f10efcfefa15fb7402207a8d89666fa8c316a4c67eabf1c67c6a34de67fa7ad` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-negative.json` | `ee5a410df080c56cac83d4ce8348767bd1ecfcd508e7a0ea8805faeaf68ecee8` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-positive.json` | `8c5ac1a26009185e431fb16f73851d0f92228509c55edee3eb95e91674662350` |
