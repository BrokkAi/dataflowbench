# Scorecard `bifrost-cpp-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-cpp-kernel`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `b29775f28c44e0830155def3030cb36f7c7f8906c440dc18af2be6f7ddbdc22e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-cpp-kernel.json` (`sha256:19f918df7d89028ff8edbaaccd6da6cadce58aa751d0f55615f78e79ef5b2e07`, normalized `sha256:19f918df7d89028ff8edbaaccd6da6cadce58aa751d0f55615f78e79ef5b2e07`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-negative.json` | `441128df6257610dd5c42512af3b4e1e3052e8e8c6eab68ed842a15275dc1000` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-positive.json` | `3af181135a5e9ed9339ec3231730a7f36b197747d43bb31bc8e83a2ca459e462` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-negative.json` | `8a626fa3d879d06d649173d6c6851b178c88a44f2ed4aab8d3ee5150f9d56bb5` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-positive.json` | `340023b7da97882c11cd0950f3e87e920449497e5fd3c4e526282b01be6fece5` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-negative.json` | `d99fad941b154b0c686108d59c0994f63b50ea9466bab929be7e213207893d1c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-positive.json` | `3dc91e9233d8580492fa261d81dc9028b1c0a139b78b8a7811d2d73930b7579d` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-negative.json` | `8b6d9788d2a2fd2e27f4692682c534c516f79c22d014d320d44f815c1cbe0131` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-positive.json` | `4fe44ec02c78ee211f3efe09b67203a4203e58ffddd33ae9b94b9f36d38ce532` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-negative.json` | `58bba185ec11728dcd7fa0ff1ce6d4e38a5cfc4ba23a2c2a61d4e29bd4a40656` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-positive.json` | `fdb55c03635491ff958fdd3588682ad6bd95c462f3a6677bc4ca50ed32844bdd` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-negative.json` | `3c96db9886c58c4fd44e4f465835b99fa2c93d9fbd050e8756bb4c7a620e751c` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-positive.json` | `1deb658324dbd416447ff659a4bad9debc9ea6a9e7760168259afb555bb5f672` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-negative.json` | `7f00f2ab2c48105a9377a11fcd6112a11893324e9c3d852ea334177df15d7eb9` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-positive.json` | `89d0295738a7555d7b74826736b26c52092f1a85d360311aceb480016a4a2ae0` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-negative.json` | `c90648b54d9767707c5a144e19cd214d282d4eb70e1588cf8ffb652207c4eaf2` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-positive.json` | `ee108644b22518dc5d8a677aea3c3044615ea3c1c0efd892f8a32bc49f3a6556` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-negative.json` | `875601bed46ebad9ededdf9c39b6e1c61d0f40af7892ac59d1573c066cb5c7d3` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-positive.json` | `55d7605b39cf95d0d44a4cf721bf0a7a0690a27107bbc2356ca9d81a41f0670e` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-negative.json` | `96f02e6aabac78a552427d93f7f16c9d17017e6bc3d8fe5ed98c718e3222dd12` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-positive.json` | `fb76bc843ea9d7268ed73b4d5b1758046d15b1acf606f3bb6cd55c3a01e6ef90` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-negative.json` | `aeb4e7499084fb9f01a07786e4021036812bd58957c51da408a0b561febbf406` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-positive.json` | `3651ed0bd136376ca19e6224dcab3f44bb337922904c5310ed55def38fc3b7e1` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-negative.json` | `2c3dca4209cea5eb24f2a8be1b976aa6eed2dd57059cfae2449409f882c77d0b` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-positive.json` | `5e42aeff593037c879b259c242484de0d5a5575fa8404ec9c34245a2bbb0dd3f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-negative.json` | `dc20eb5275d1aed22f2b01573c8cada96ad915b2336f6913bc3fe651f2baabdc` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-positive.json` | `0f97c12c868936c420e9cb7340cfa5e0d0e53aae2fcf92654b7b9643a2b48e2c` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-negative.json` | `0eb048781e95a1898aae88d249624e5ea47b1f0f091c4389387ad046034368a0` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-positive.json` | `6e603c68b17a7e5ae9e200af60f279eed3b506288d803f16a0c875c56cecd345` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-negative.json` | `9618420c0d4e49ce316c2f59ff54bd486b8a675134b032b1e45062ad9f0e935d` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-positive.json` | `b120f5022b004cdb15ee2691ce5aaaf003d796f7cedfa3cfc93a1b7f0895b95f` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-negative.json` | `ec9cb374eae5aede25531b442bb86a9d90ad0df8e1154eb6da3f58f9f3878027` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-positive.json` | `6d98792665b85b644ac19201ff2b887456ab1960562e01dca52b8c0b5476136b` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-negative.json` | `33f0a1413c8eb4eb93d8ae178759352b2304469c02d37cc6b008effb7fd60353` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-positive.json` | `1401eb55ad4e29cfb657161ffbc9b57dbe63816e47f9d34e9013e411a88dd6cd` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-negative.json` | `acf3f2a4ffa8560463b5956257fb3b69285571d3288028a9463600a166015ffb` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-positive.json` | `a0d0c737cca36afff6ee996fc54773daebdb26218a180737f0952d8cc8eb80d3` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-negative.json` | `ca4f1bae08a26f08d7caf84ac803f9ac04a19c7fbb48b0e43ec66504645c6ab2` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-positive.json` | `d9ae45704391bb262b7311d9b0e11c695cb2cec3e0e0d587a432d1866d722f56` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-negative.json` | `3f334f0d01e28c3829733d41e29f64539ad7e74a4b6bf604f8813c9e035611ba` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-positive.json` | `efcdc33384bcbd749d9e0279e3ea9c61ec5febd6d000837f2c3455e52cbdb33c` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-negative.json` | `2b33160401d12357d317ad9d859de51307116dc9cd37118be2633ca5bc3d2e4a` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-positive.json` | `b7f4263e3479901dfe836fc4dc2f6706027e95b3b6ca89a143a727fcfe192442` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-negative.json` | `5bf39f500135c2c7ed02bdaa23733a0afa28281ae3a81e0ef127ab5bbe0776aa` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-positive.json` | `33c6e636e225127c90ad93cc231e848de70f066f09390473b7b0b7edb35f2c03` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-negative.json` | `46b4613637ba0f7bad79d5b33eef41fb76311ee17741f0ca6fab637b32c33ff1` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-positive.json` | `4c695446d23a2a478f0aa12f0f95cdc4e26708905b954b663093e9b93c0be216` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-negative.json` | `8e2147497a7b71ca942b76b76b1ef553b17e88ec7518a9cfa03e36b51b5d12e5` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-positive.json` | `a7cbb0e61142520bc82dd9e23d170e22f707b061390f88e5cc36e86be7089bc7` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-negative.json` | `c399565652bf28920ad93668a57792ec1e47f69207fa6226eb3154e69067ff04` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-positive.json` | `73ba25d1b22ab3f2f3ecbf9247cf20d0a863679f634e6ae2c9d23c5d112b1cc7` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-negative.json` | `764e9dcd5be410ab3e05e49dcdac5afcf7783bf43ddac6262aa19a2318a5f7a0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-positive.json` | `7d9d8588483973495e0a87e267f6fc06109b0aabeafd190aae68da74dccbb0b6` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-negative.json` | `87356d9710da64e5c79fe9306385898dadf0fe1ad5807dbe4c6ba7a423d612a6` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-positive.json` | `91b6619fa4e8b145d45d9c30ebd6fbc8f922baefa3e08b9ae9d6a49d95b148b3` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-negative.json` | `6a9145ca84dc4fd3e35fda6a7d784bed0faa43adc26f6cd9a5d13bbbf7230a98` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-positive.json` | `08fbba4509d6615a7d5aad06063abeb177d99034d7e7319d30c2b72035daa2dd` |
