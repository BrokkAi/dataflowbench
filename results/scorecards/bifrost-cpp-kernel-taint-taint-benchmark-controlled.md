# Scorecard `bifrost-cpp-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-cpp-kernel`: `bifrost` `bifrost 0.10.6` (build `18d09c57d1e5044dec49acac7635d3255ea8e89c`, adapter version `0.1.0`, configuration `b29775f28c44e0830155def3030cb36f7c7f8906c440dc18af2be6f7ddbdc22e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-cpp-kernel.json` (`sha256:12353998cacf0bf7c3e74574961d0eaec9204da633a6cdf87d2c36526bd71e27`, normalized `sha256:12353998cacf0bf7c3e74574961d0eaec9204da633a6cdf87d2c36526bd71e27`). Generated from freeze manifest `reports/freeze.json` (`sha256:91b0008a546e6b782c1b790f174a71ce44e60039239797674eb49ebc6ac6c366`).

## Language `cpp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 54, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 20 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 22 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 1 | 14 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `recursion` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-negative.json` | `96a04e435239dcd5800b493ec31d3c5da3df5d551de5131c6194cf280ab4198f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-positive.json` | `7922c2ad96ca74ae5fb89d3bdf8d4a2e7a1db7f2c108f3f7491bf339335ac8af` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-negative.json` | `510e7fd990cb750473126a17570b69c14ccd673f1d21590355876672bc4db0ed` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-positive.json` | `40c67513bee7542500f206015ce25a0523e86d832b6efe8148acc43c32097d98` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-negative.json` | `83bfc117c7b7682d0428e874fce10f36cc82b3bc855db5857a4858c7ff0fcc2b` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-positive.json` | `ec0a1c83066659b9a7aca37f98425775fd0273a14a5ea0e979a9e917c9690a24` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-negative.json` | `4f3bb97eded6e4f87e83317584e93bb53a0bf58dd17c773ef67962dc9b6fe627` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-positive.json` | `36e66d23e61faad0c45f818f657bb29f9fa672bf533a37bd5d2a863e7c55230e` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-negative.json` | `ecc2070f284a117fc5e77d8b7d26accc79489ec344b694b34066c94636759794` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-positive.json` | `daebcf2b7f9dd72290a99caef17b01894410db6157cf2deb329f57340080eb4e` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-negative.json` | `8a159ecf80976f43a074b780a59152f080dd4b49daae67a7b90b68f54f124075` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-positive.json` | `3ed558b47fe37cb40ef9e6ed89676dd8e6ee8c239f9e51a46803aa1d2a47171b` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-negative.json` | `c6442e26a22d2bc60414dfa193e7c3b26e89a80c68e5b05e2b28fe5c055f4d27` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-positive.json` | `feb79188993ea9c29b8b586eac335d16e12df68a5af27abd42d168cc86865efe` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-negative.json` | `9cc1775619490b4a8d276ecb00bfbf61339652cc0973958e7da198f3d1af70d0` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-positive.json` | `a9a31dce326213e618f064ce194591854e6b89e4c351e45086dbb36650de3d47` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-negative.json` | `156cf500b9a04048686f75a80b7d0b488fdac391f56e7ed358a64d4a4c793c39` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-positive.json` | `65f8de20fdc2a6cb3bff36c62f73670490dbb23f651c024b4e1464506b3626cd` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-negative.json` | `0c3b2af1b0904ec9016800fb868ef94ecf46bb0bce83b0617de0fde13524a14d` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-positive.json` | `de56dd303b427de9f056433221ff7c4e22ad7396f99e0d30f949409f842a6557` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-negative.json` | `be7bb74b65f6df07526cd691e2deaa50d86f0a9d3643121cac0220e241d293b8` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-positive.json` | `82971da6c437029bf604aa1aea6f9408e8103136e9478ab8f45d5ab31cc78a29` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-negative.json` | `1a2d7241b516090553d2064822c3d99b448bc1bc75d626edd8bdc2691b3f2fdf` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-positive.json` | `7e763b3d8dae80924de6586bb39b015a1acbd52633c38ee002677b410989e07b` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-negative.json` | `0f07f5fa4ae45f487151c5e9fc1b321cd5d623b6b2438b2c8cb219c90540d3cd` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-positive.json` | `93f458bb703e8688ce8040dc2e158e1d69ebd33125f151cfeb193f1c64dc1e2f` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-negative.json` | `dcaf2b345516b8cad1de45485f0a709f2a77a0adecd62a19c5a20ecc524a8d63` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-positive.json` | `0b16fe8161924df64c2c509b548e10a3607aaa3174dbc996b515124eea925ddb` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-negative.json` | `5a23d1ba5fa47fb9826eb2305b8e876dd285a5f40ebfc2aca739904599d0860c` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-positive.json` | `ed5d6940287e02e80b18a4281770bdbcff875888baeeb8d1f2a6acb03ed577af` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-negative.json` | `130bc1be0a3537be5e2e860ab7ea0f492df3e834f6433cb63bc5547343c9f37b` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-positive.json` | `01ce44c9fc52b1dee0e1b18d64b6c7477c53ab37971440c502512b712a050935` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-negative.json` | `923588d6ff2bdcf1850d32a7f68e817771660d5ef85927d5ce05c7ee99383264` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-positive.json` | `32e871e259adc1067be729b83b5cbec858a4279e74f663d92f4a4087f783dd24` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-negative.json` | `e717ee297b066d7f61b8016bde92f1ae06be8c9a31b1018fb365d47f5bca46dd` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-positive.json` | `44bf206a0ee440f2735cb434adfa47398e8d7601ed6347aec1f991f5d2804484` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-negative.json` | `8d34d949aa0e16e426baea6f495c9af09ac54231704f36ea9f7d17aae5be6d86` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-positive.json` | `6d8fdcb6759838796d497e52fa4f768259c19ddd0c1d48ac89f70fc1cd4751e7` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-negative.json` | `596de700bff49ed805633aaa614e7040a56f5c37ce29f0402400aae45db41b3a` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-positive.json` | `bb5eb9eb8a1f20768f0efdb8ca52f1486db3693e65d3b72d83fd1f4204d0f5b8` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-negative.json` | `6760bbb1a8ffd5afefee5710448d9732ef0deb57c86845eadbf5057a0f1bed94` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-positive.json` | `52e4b9a10e21abc53173167b2eea301b6e0857e40076bdb716ea1194ea30a0e3` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-negative.json` | `158f541299222acad18014ac46f5e63517a9e17606272a76cabb2147ed529b55` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-positive.json` | `ed273bbe7043171e40fd5167bb6ce7321e385c44d1235944a75360cd6d83136e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-negative.json` | `a17730d62cc9c55eba5bc21c5dcb2ed8169966f67cabcb95650d662f62e8c843` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-positive.json` | `da179708c9639cb8349d68049041b9b8943a063b82745fc173b9a5bcf9960186` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-negative.json` | `76121177154e77fe6648b0b34d37ceac8e4503bdf0147953f071b8bda82c8d9f` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-positive.json` | `259d1044d948f2070f4c4e50df03dbaaf57019e9e86458ade4cff6141390f302` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-negative.json` | `67e0f33356455ff07e629b1067418fa89598a8268c19844a0a051555fad9e551` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-positive.json` | `1b071a8d2ed6b14879c3f7554fb31653fb5fc9c7fbf52273431263217494d4cd` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-negative.json` | `36e097895ab52373f804a9f8ba2a73eb7c851a74e99930a9e395685f7e591e1d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-positive.json` | `7db59f3cbf4faf1670e5a8ad1585924df16c2d41909bdaae76c9d5cea9861933` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-negative.json` | `d96500c01047da1b7d0e19e24081282b0de6d72400bb89beba6e6ae84ef3aad1` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-positive.json` | `32caf593eeabb997f7a48752af962736afb021893be865a213f2947ee0b4541f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-negative.json` | `820df55007c4d80eca2c9a138e97ee98cc8a3bc5bef8ada44a2e054d169d6ef3` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-positive.json` | `b8b3bfb3f57121f07682d5accac5064d07610e83d933ff69468025b4a6c30712` |
