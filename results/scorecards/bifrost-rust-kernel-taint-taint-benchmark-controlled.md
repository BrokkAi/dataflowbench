# Scorecard `bifrost-rust-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-rust-kernel`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57`, adapter version `0.1.0`, configuration `36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-rust-kernel.json` (`sha256:340d6104d3ecdfba2de9429cfdfc4380bbcb30e708180644dacef588b060ca02`, normalized `sha256:340d6104d3ecdfba2de9429cfdfc4380bbcb30e708180644dacef588b060ca02`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 18, `not-reached` 18, `inconclusive` 18, `unsupported` 0, `runner-error` 0, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 6 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 6 | 0 | 0 | 6 | 8 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 6 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `75ec6e0291666680fe88a6e5bb37d3d9d820109917f2bd582af811e6dc851a8a` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `470eebc4367a27c5ba7fda6e53e16afb24ec3ddb53ffe47d419a8098894fadf4` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `4327aa4b2895a184671146bab202ecdbedcb6e5c3cd7b0675adf447942b98b30` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `1514f5c05c44e1866ce0510f9e28148a8de9476349ccf30bc3694f258f7aad50` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-negative.json` | `178fbfca3f8e533b7c8537ee71db6e92b4d217526dbe81fe2396527ed738651e` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-positive.json` | `42ebeb39f796f8ef5857181ae1b616eb27da3b6fe1bf7849a072bb4461e2fa20` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-negative.json` | `71e0934a4a8e711e381e031aec640788335e6772764801822399698c91c88a41` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-positive.json` | `d1c42e799fd8c9906621d43e386f202925afd54f4d3992f773ca219e6c80f97d` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `172c4e026cb921194abc91de117b75db79f8bc59d272388dd580389ce0d7e813` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `b32bb1f81e8f1200616df42ce37967ce37d0142ce3c1712c532ea741b94f8b2f` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-negative.json` | `8e9537654288c51c1e53daa2931062bade6669c446a8bef5eecc4603e13e46b0` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-positive.json` | `026a5e6392189f53543c5367d89b00ce58d20f76bc599833310a8eeb47e90ea8` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.json` | `47d56e12fe6591d43ca1011fb1417a8104f0384c9e407b099b9217b2a5486a3f` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.json` | `91dc3290912b90d058df8f069da030640647a8373c63a2a59c3355f850afbf14` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-negative.json` | `27dc7fbc4ab3a116f000ae4a1fa0bb168120ffc9462286845385faf5f10cd8d4` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-positive.json` | `c59efa2c4ac96a50f04cff38ac7354e01da19fa43ae32058f965a18eef1b042f` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-negative.json` | `c0d44a01591f947eaa37e34278ff723bb9018314b0d26ca66c758adad7734e30` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-positive.json` | `240907b1fb9b2a88e0cf530e5f5324edf0bf954ef3a4b60662b0533dea132f6d` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-negative.json` | `16bbc30db1392c003124f09bf2f41e8f8cbb6c4e95df42f42268e4b5ea87e01b` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-positive.json` | `5e29094acde0c68479dbf162b01604cf9990aa45097f1ed381414e24a66ad8d2` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.json` | `f8bcbeb045884e1ea04d643e44f6c15e57d4cb98eb4cadf02c99956e4797f703` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.json` | `a91ed257acd72ee9ff13c74ccd5eeebc89098a000936ae72fa56a288f8f915b1` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.json` | `02e8d54829c59a83b994da5d02f9af215d2a4071ad4dd40cdd08717e9edf4ab1` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.json` | `8c41636640209d9c2d1de4588820eec578562498f107cf52d05c501b2f78869b` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-negative.json` | `461d985e5aa5ade20f6f1d53e5fc639e03012576f41c423c330b17b69eb44387` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-positive.json` | `461d985e5aa5ade20f6f1d53e5fc639e03012576f41c423c330b17b69eb44387` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-negative.json` | `e6a1487a09cfeddfb168d1570b6fdca9e43a33563ac75952a5ff1094c8c353b6` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-positive.json` | `92e6cbf603235dfd7cb8d861125404e77152caf3792a425ef80fed39062e00bc` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-negative.json` | `a5702abd31463e80daaa18463adb8f18a5b498dc0bc7ea90a7c741ddd4c76797` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-positive.json` | `227c8feda9573673b65089f006581d3b842a084446872cfbf158d47340917378` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-negative.json` | `b51bb3a83c28ab0c83ca636c6ae279264d5945a34778501ee844313559562b47` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-positive.json` | `87e10541fd6badfcd8ee6ece8f78c988df1e139d1f57db4f9e4bdcc57385dc2f` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-negative.json` | `73718a8def63dfb36a9c445cd2ac6c742ec011324b68aae18e33906caaed7b98` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-positive.json` | `37330929d043627f07a061293989651d3e877370ec6aacf0ea52411ba8e1fd2c` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-negative.json` | `fc3f327bda8446db10913e386d9a8ad7ce5c9ee8dc55942a4ebd7007549bdbf2` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-positive.json` | `d7d5b2dbc2a119a99c98cab6dd09f339178189a1ebe44abca6fe609d77b4c736` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-negative.json` | `afb07077d447bae1a63cb2ac6b8148970a17361580ae193adfc70de258641ed6` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-positive.json` | `3e0d4e194873eb369d14d6a3dcb97a5678bd27644c7593d3b7609a45e82574cf` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `208d1b0ea27f495bd6127f921fab11d133e81788db31ab52d3d9c4c56f111075` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `d47ef740fa994284eed82be56f047d2e37038fcc0db8e8c01c1507a7a2605e7c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `a553f695eeca89430480f151779a4df7d655de645ed22dd9572b7a500f0c59da` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `6f5a4a85554580fdb9abdbfeca4d43ddebe77421f661c806b4e4abd6050415fd` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `2e0ae22240d67594880ecf0187cb0f385bcb80db01bd113f71d1c1dcc4c218fd` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `9a9f70d520b6f7523c2bd7f24978a83fb83cb5b401ff8ad0cee763455a5a4d02` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `b69582bb8de65369250c6ffbcad5bc843a64570e4e651bb62ba79b5dd31539f9` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `49da362fc19bd1a1f6abbdc8ab1bc92da7911f56e583753fcb860fe2fbab27e0` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `63b40a968f9481720898f0ea1877f6229657505df3d9577098dcf5e45fc3ac59` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `584f6fef798ffe57264439298a92a5924491dc309ad6e43f24b57998ad0ea92b` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `271b3d3077645be4100fd9d45a0ec691beff74f6e08f096f7c562afba83d2d31` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `001476dcf9ea97a2543bb059848f9d54016e0359451869341717906532cda29e` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `330a63a7ad20c27fabd2fcd5ae5d6e8a453450557361c5975acdd3919cc58e89` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `8b1beae708aa7ad2dcb2ec8d1063a1c0073873684b968b338b6a257bf4e00283` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-negative.json` | `a337439f9187be3c3dd8cc578649d36488e9a8e24ffa6cb6f67acdfdfd6d0558` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-positive.json` | `e17ff15b08321254a2a5891ebc6e077eb4b49e516a3c83445cd5beec9debb016` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-negative.json` | `5e0cd83c37907676efcc299049f0fb95d1b1e58f96b7e254a344e3a07fbc77d3` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-positive.json` | `2c0d3977a596be420c475b408d35509d7f2b8c45e65e4ea542620f810667a84a` |
