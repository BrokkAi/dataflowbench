# Scorecard `bifrost-rust-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-rust-kernel`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f`, adapter version `0.1.0`, configuration `36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-rust-kernel.json` (`sha256:9fccc53264940aa04739632f0898cc918fc593d3fba3e91da121b4e5795cd690`, normalized `sha256:9fccc53264940aa04739632f0898cc918fc593d3fba3e91da121b4e5795cd690`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 21, `not-reached` 21, `inconclusive` 20, `unsupported` 0, `runner-error` 0, total 62. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 5 | 0 | 0 | 5 | 4 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 8 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 9 | 0 | 0 | 9 | 10 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 6 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 20 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `8b282af2daab3ea9429e28e1660fc5408dc203338fe8938198faa8cf0c432db2` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `402d7d17c47d16e49c7054fa4f95dee0b097e074cdbba16e332fc3a34cbc44e9` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `00aa985794e1983ea679219762845aa79a293cda0246dcedbda91c9e88164f27` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `4f157b12c784fa250176e66f25f35de94560eb59a9023296a0711d4d44dcc6dc` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-negative.json` | `269faa0b91ac3df73d20d77834151311d1469c9ec43abe23ff4d9cb7c28ab16c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-positive.json` | `881d723b36e1f33520079f1204226fc0de0855d6a60a4c7d7b1060a334a5ed90` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-negative.json` | `b96c996a503a0de640252fb97c48ee7bce433a64d6fc51ac2063e35bc7a07e07` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-positive.json` | `eca6b32656c9d9fe470810e2658f47e53ae6c3c2eb6c9481a140dd69b84a96e7` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `c2e2ee4dc7a025daf9ad25d3975f84555086d156873443ab581734432ef7b09e` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `b252d3f462e068992426897b13bf177909f829379466767d2b4c70876d7533ea` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-negative.json` | `490047667bd4bafd67daf2e393cf54b7d12f8a2ea59414c34a2288b84de1d264` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-positive.json` | `68f2e57f9dc6e50af24316ac880a4916effe9a570af13ab22376d999cc979bc8` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.json` | `8d2af939b9c0442ffe7012789bd2fd0d71f330cf30053623bf2cd681a47dc0c5` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.json` | `4a094705b25f8c2bd771a03891d89e508d4c6ebb5c02deac60bf24b601e4ebde` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-negative.json` | `21442ce8cf854f1dbbe834c3db40829e3cbac36deeef6b35495bcbaec2cb7ca4` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-positive.json` | `6c6fd79d3278037aae4edfec320673775afc10340e3ad900679aa84136f730f1` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-negative.json` | `b46583527351756ce5bab20b7c488c98a0ef394ff94e6079320914040e9715d0` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-positive.json` | `a5dd14ede0d99f722b2c5239ad1ba61176c52e0abba246714004f4e3f27fe7d1` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-negative.json` | `a91966b026f59a32b3037ca5d50449f45572c3559f58bd80b19dd916a0cff700` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-positive.json` | `a7fe4068df79acccbe4c7ae30deecdf30e0553cc9f04e874cc0493f660a8fea5` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.json` | `c7f7776eab4ff00875bcd55db8cb38e92d95d2f4c0f890efd58cdbf95b5d1937` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.json` | `e9fc939fa2270beb0c00046ea40e04be75f10bef67235359b747cf03b72119ce` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.json` | `e5b83f16c9cc73ef9c848e1288eb4262033f57cf2291c7cc6feba7f8b299e7f6` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.json` | `8efcf0fefb3e690662b716aa314224680b5098193d7333763ccdf1232e8dd39e` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-negative.json` | `33d1936ef5aa8ab8be175f53ec97d0db0f77f5de17064368d50d3a2ee24ee1ae` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-positive.json` | `b86d6ff7b112f63928f778f22177ec1066c1e2fb36a00267039d74bafa34d467` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-negative.json` | `5aa534f2f85887262e0dd93e9714a39594cb525f5aa3d2ca3feb04d496d15626` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-positive.json` | `fbf80d2dacc977ea02d72983c78ad104f9b75f1bb6628f9ae0b1ce0ae4745584` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-negative.json` | `9b937e0d3f126421416a62eebe8a255f9e5a7533869cea2c49cfcbb838eb2a77` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-positive.json` | `d5f771749bbcba94b481ecc458a1c3ccd8460a2e1234c5081243f477257037f5` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-negative.json` | `eae43c6e92f2b63d524cf4f53a3500ba7c5be952013bfdfc3120676d90fa99d6` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-positive.json` | `b027b3d3d9e921882118be183481d287511ccbbce3bf5b91864b1d36a85eede7` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-rust-mutual-recursive-transform-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-mutual-recursive-transform-negative.json` | `9079fe44e015e4d266e2c143b17291b30e4fca0e73bd98a938281781b945ed1b` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-rust-mutual-recursive-transform-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-mutual-recursive-transform-positive.json` | `4607c731921df36e61562c1412fb4c6166c8d38aac4cbc0cddcaea5c6e7beba6` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-negative.json` | `1ffa8ef95250f868f6ed9ada0cecc3db4d9c18407127832cf089c577829afe72` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-positive.json` | `8cc133e4f7bbdbbe34be9070aaf426f2e8a1a62a525a3166213a97846cd07521` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-rust-recursive-callback-transform-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-callback-transform-negative.json` | `a2d51d5b22bfa6d0076cfaf19bc0bc43814d8f15be29bfb8b688c4167e94d3c7` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-rust-recursive-callback-transform-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-callback-transform-positive.json` | `4496773338b99bc9fa0ab3b4faa957a80abfe883ef15fa38a62a76be6047617a` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-negative.json` | `55b9d3fa5c35c28cb3aadcd2c7f53bbe673bdc77f9a9e14a86114b52ac36ed27` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-positive.json` | `03b190046457b01c41a85e3f86fd060522fb39476f5a4e7d20a00237ce7525cd` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-rust-recursive-heap-unwind-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-heap-unwind-negative.json` | `63fefa3265661999cfb7a22f6103a22bae4cb3ef5c8d43760cdfb1c65f458dcb` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-rust-recursive-heap-unwind-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-heap-unwind-positive.json` | `d8658f67fa502a4b12307e488cfc4dfc7c25604f76bb1770f4e2a8e79e3db1f7` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-rust-recursive-payload-transform-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-payload-transform-negative.json` | `fa3dcb60c98d98b9e8a8c70ed271931e158be4adb97e27626c26cdfc56a1facd` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-rust-recursive-payload-transform-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-payload-transform-positive.json` | `e7d9bd6e199b91b6d98ef3a45302ffb75471bb106894eaec2025ea8ce0cf150b` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-negative.json` | `ddda2cbedc86824788d6ac2854114356ca89f6564cfe99a0fad9f110361b87fb` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-positive.json` | `91526c2f542c00e8ceba838620d085aa62ec1e6405c88b950a355fa1f1d5e300` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `a02b13172b9f602980442a3e0e087fe60842428b627e1dc80afb1f5c5eb6e343` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `b95fdcdb1970eb7301a6083059d35074c69f4e9957bc9049702446b0e34dafe2` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `f6a0e374c62354c9e2bab4a51fef7210d209755b1481625b7ca2b3eaee04140f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `aceebf07e9272d4e4a54d243ef2ae705e1b777b437c1b74be0a3f00d25a3d32b` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `50a256e1f963fd2351252db440bfedd74e16d2e1d558fbaaf68d8e27fc9fccf9` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `55fe070526598c3078ef50d55050e63dfe99d410afe68dc7a9e50de23f42ae7f` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `e324acb41a5a37df3d1ec37b452849e589c524d5ab6794c9c2172ecdf3df09ea` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `f23597eade4f6dffa7b26dca7d3e7544ffa4736353f976d32a27953450dc913b` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `a0ec741ca13ace52d317c31a9a8ac6a7d7a6fbd0e6093ca7814dfcae7054434c` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `bf66cebdaad75f4504600004de585390424c90675517c5454364ab9a13add79b` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `004f7be4587e0c0584ba7006b4a899490f37adf8eaabf9a6adf387ceaacfde54` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `08fc8296f043c0065d2b590220ef90f59761e4d60de868b829f949957255a6f9` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `446ce8db88d7f1ad004f967d58e190ebdf01c62f78b9addb6336ced981ca572c` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `5044ad5d2d6281427e3df4c9b1c8c774c2eb81654fffe11583ea1a80cec2b5ce` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-negative.json` | `a8eaf9b30a50a59c2dbf0cff3bb98c0a6148d481ffd5845b4de16a5b339c30b2` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-positive.json` | `d995552ef1f15a4ca002f3601d8c99e7716fa886f26291f306998635c9841642` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 2 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-negative.json` | `bf467c26182c4e57bea7a4d06aad126a52178a517b3d37eb7d14399e6f5692eb` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-positive.json` | `587736e970b204de1c6af30e6a59776ba493cf78828207afca6985a1ee00e52e` |
