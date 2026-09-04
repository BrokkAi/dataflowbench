# Scorecard `bifrost-rust-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-rust-kernel`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-rust-kernel.json` (`sha256:e00bcdc488fcc645fe79401784a2209f8d14725aba8a97af8432be6503796051`, normalized `sha256:e00bcdc488fcc645fe79401784a2209f8d14725aba8a97af8432be6503796051`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 19, `not-reached` 19, `inconclusive` 16, `unsupported` 0, `runner-error` 0, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 6 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 6 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 6 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 16 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `00e18f9309ff1b7c8562822cac62d94112335e2207c696b019b2586d383e6f69` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `9b89d5b4a63eefec0b349f361dde3f70aa6bfa3c34cce99b7367b0c2b5cd9db2` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `516aaa93de52722e47a99ffd74173ebf8915ade22b50a9bae248ce39167de04e` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `79fe6007cf35f5c65605d3356cd2f8a444be1e97a558abc7a97e40349d0518fa` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-negative.json` | `92bdac09ff6f5232eeae5a1d44b45beeeacbcc401dcb6bfb64cf39f529aaec6d` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-positive.json` | `d5a6e80bc85017cea184d9a0c7ddf6919a8139ea85fb7e19679d07995db5323b` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-negative.json` | `f82443b6e82a87b53f3247856d573d652dbc2e6d367dfdd952eead8d6352cac7` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-positive.json` | `e1468729ec5a314a68887663024f16dae09c022745686af1b9413db17496dbba` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `2c96c51fb2cb79062f62d081fb6eab032110d0f3080f43a2419bbfb5797ea45b` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `cf6656ae655f5b9eaba60c4e0df18ddb2a6006571f958b539570edc8ea5743c1` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-negative.json` | `13b2952048d8c5a385b98d06cc2f713e153a308898c9258ab7bfb5a52ad70301` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-positive.json` | `322aa02f9af238de9c92ba5f3dc06d0b788ebed27167623e7ed699db4da4552c` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.json` | `03760ecd58f024042e90db15b5759ac4dfac7049afd293842ce3617bd155f60b` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.json` | `3a253465daec5c30ddb1685bad1a175f3a142c690da3354b039580678edb547a` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-negative.json` | `187f8f6633fa0dec403c2b3124cab6026d4c671326e8595a91ec82d5af018fc2` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-positive.json` | `c302dcbce0773b295d779ce9a231bcad144b6006d832d70e7b33544f2cf2adb7` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-negative.json` | `786cc5a9130f3f35a7df1b7414b668e6df24e5a42d137924396581c2bdee6489` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-positive.json` | `93bc95464cb6bb72ebe8df4e03fad7f7bff64a3931276a824982daf60d27c703` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-negative.json` | `417d905f28c52d8294e2a62671b915546254fa07fed2120e7d00fffbd1ebb53a` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-positive.json` | `ded9cc59ee9bee42e54bed141b4e5351bd95554f994213504a9521720dcdd399` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.json` | `10483c7f5764b901e4d2e2ca330d10eb6cac4a1bf0b42f051d20d07c9c84dcdd` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.json` | `d351ff3f97e1aad959c507da526b5d7d334d3c660dcfdb127c741c7a0ed73bd3` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.json` | `a2cfe3721066de72f031649bf75ec51903a75b6c0513c1b8bd7f9b1ce4a18e86` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.json` | `d18b97501733402aeefc6351552555a34fc586e91311e18185d0754a6480a654` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-negative.json` | `dcbd93335a34b27d7302dfb9045a92c77782b69b32c1af2c678431597017345d` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-positive.json` | `0a4ffda3d771f566f6035b26a233fcf5b303722a560e30b29caef9d5d081875b` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-negative.json` | `26c62afeacd75fb8c6d547ac86bf7b916011b6ebe0faac4b05d16a6488619300` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-positive.json` | `927b3c8d7797bfacbcaae99f385b05b7563610c2d57fa5fcbdb5bc24bf05b61e` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-negative.json` | `c9e6432f9d7a65f98c12b584e6de88331986f1190384fb6e6055821bde15875f` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-positive.json` | `3c3c9bee1dd2abf39c2118cefa8fc25804ef3207ecb707459d4a3a532249740c` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-negative.json` | `adedf5bfc7f9c6db0f19ff4a112912424c1e3d42698d63f13f112072ab8cbc86` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-positive.json` | `343000d7d22268a0c4e17d0706f81eadff2c0e1a5be8170ccb4272ee28aff819` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-negative.json` | `a98c27c4dfe7d4eee86efdc5c8bc28711595afcd54d2edadf02bb3b6e1e65253` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-positive.json` | `4d6f50d67388ff86808028f367ab586e2fa3e7bccd150e13c7e612d2d23e2c09` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-negative.json` | `fa55fac52019e214bca704fd8b2e624ec01177a74af0cb0ebed214268776381b` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-positive.json` | `760d728e7cad2415fa1ed69f7b128d6ef6e9a4ac17b8e1f05afb7c494d41d526` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-negative.json` | `f9c64a3ce358887b424427d85067e0f89812299643d7e824662cbf5081759189` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-positive.json` | `6e91025269043ddca88ede420bed12f7a2f3b14ace3c44141570e699e5680aa5` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `698b47ef8b978eb6b3feca5fe670965a797bc9e5c3be5291f22394b618b21b7b` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `a25b8befb07b9a2e1fbdf67df434c76c8d320c5eb3e9e396c7c19eeda3c0a3f7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `36009f0d896b17b13df23baede43f783bbce5c468b89e237ca8989c324396df8` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `3306b8dc5e77482ead79723a12eef881c3388e47ee42dc965b8c4a5e517c32e3` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `ec4f352ac9dfcb1fa2531748deb1867030badf5f936e48948a45bde36b051b7a` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `776a8f4676563071ac607dc46f423ab8d0cff494325cb344bab30bfa1d3cc9cc` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `cedf8f03f09fb93e4ac82ff80ffcb91dd847196878322027ec3d63cda7fe67e3` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `a7561c352599bd1d80acb9a735371d8b9739bbf3a0cce8519f18aba68e9e0766` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `aeeb0a4e4160cd10d11b6ccff747a521369d84b78fb845e89b8caa5a17e9c24d` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `38df2e36a647ecc5dc7d0655f3badeff4752befd4120eac25679440e23d52cc3` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `91ed54edfc4b0f13713444019de31266bfa0dcdaaaa02e3b40beae207529df55` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `9af9377e82532a69549137096bb0698de2579090b2a0fc724b10bf23dbe03005` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `7729b5df47834ad4dc6deb00b22aec9b643edff2f44639d9108fe9893a71bfaa` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `05146c3b8bac42bc35718476b974e668383f7e18c013715753518deb75e5ccf6` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-negative.json` | `9a72fc85632d6f681d1b041ddb14cf2e3857a5c03ec08e351906e6b6b5d84593` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-positive.json` | `4e4ff87068e738fbc8b76f53cd9fd9c9d1c942fb5d3e39bc79f328733c30e669` |

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
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-negative.json` | `e3abd2eca2b53dbd401f495eb317e48766fc86c38f7d516508a10d36dda6c209` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-positive.json` | `97243d3da8c58d62dda2ea25314e31c95f99c369d765720e7433e2c1e92ed273` |
