# Scorecard `codeql-rust-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-rust-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `1246332117ada910bd21dba152ff37bdae202290e14f29d1959dddec658e7d45`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-rust-kernel.json` (`sha256:ba05e002a47f703e1915347b4e9d8f5e6643577dd7323e990ce5df890d33a1dc`, normalized `sha256:ba05e002a47f703e1915347b4e9d8f5e6643577dd7323e990ce5df890d33a1dc`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-negative.sarif.json` | `08a7c554cd2d7e23853e82df592e6955118f37b8554d404dec08ea2b1324030b` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-positive.sarif.json` | `b3ceabf4eb00de22d06f00d3fc9c25c38c06be4605672919a3e2b1f2904b279e` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-negative.sarif.json` | `7472742f72645e21c3135e2211659d80abc1de457b2a5a20152de6ee6f1370b0` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-positive.sarif.json` | `3ac2c1adb16cc3af5e38de2783867410319486b6697ff1e30eb0eb8f49d1774f` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-negative.sarif.json` | `e958a898e9132a7f4b9b5ac0d613d9785b71d1120bd374d9d37da0232213e374` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-positive.sarif.json` | `9b23d4577a8e21b5bfab0d875d3b10c50d77059bc0599128e8d12d87c388b9ca` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-negative.sarif.json` | `ab036cde3f6839e3cdc6b4548f5283b71ecec5d9b69185ed1f7d353fc503ee94` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-positive.sarif.json` | `4904a47b856c1444cfdf90058b049f17b0d79cad676628a5016208d7283335e5` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-negative.sarif.json` | `a72f544f946c75b3ac6c08ded4e06e4876e0b61ab4affa65fd3a812bd31ce3dc` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-positive.sarif.json` | `8c8d7b41d779575c3d6fa1ab5f783811e27f008d83b309c26ad13c03ee40b25e` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-negative.sarif.json` | `615243851bbf68dc64a119debd007c6faf06692e16741a9287b222446163fff0` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-positive.sarif.json` | `49d9ff619b248fd9eee51e4033972395f64f2bb6a7cc80335b41b7744dce57d4` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.sarif.json` | `4b2738ea26021fbb3c678c713c39bec075973f958d639c22e5168487d51af3bf` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.sarif.json` | `221284f17a5fc6c61f0877562483b6f78a9f43486cd1f642761c3623b2eac5b9` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-negative.sarif.json` | `22b2751e206d57a64bfcdc25128b9efbea9880b4bcda20ddb498d19dcf930dff` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-positive.sarif.json` | `c8765d58380070b0e60b8b72e837599f8a07b46bb33472bfa407fc826e393485` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-negative.sarif.json` | `7ad68de6a274108d14a60378978bde51dfacfa7650cd7c155fee26106c87df1a` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-positive.sarif.json` | `39913cc46ef69d72edee0dcc5c43998d309be8b9401cd8c0d848a77be93db969` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-negative.sarif.json` | `4a739d685c60bdd7c0d45e3b4cb9210f7a0ffbf37db4cf812549ba4823856850` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-positive.sarif.json` | `53ac6dfde3fe33b909242e9ecdbf1305e6e509c9d77d49a0091f35ba74bb0f66` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.sarif.json` | `cbc012cd301096ce719389e19e36b9ed8ce25750dd527e5762524664e6681e47` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.sarif.json` | `c201a869f7912a9a5915611e52ecd7eb1353062c7e87a42d604c59c6dab530fd` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.sarif.json` | `7b20fd1d288593389d27546acc60afd03370fb3bb6922eda958586012f43a594` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.sarif.json` | `835068771b1b4b78a5b10570f67ccfe71af64393e08d086f8bcb10279ddce12f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-negative.sarif.json` | `9893dd00dcee54b4ad4a57ee3ac185643d87de27cad1b57ce400b251d2707c14` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-positive.sarif.json` | `ffe0acd887edca30cf5c983900c9fa6b17f2f71436258e25b8070cac22c8359c` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-negative.sarif.json` | `d32e6f128019ef9026c628a09b8f48313712307bc90a12777d148157fe075278` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-positive.sarif.json` | `d6a3e32c88197f4a56f59e1185b2873898010b153e54e1da3aa0baa23546e740` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-negative.sarif.json` | `3adc607e662a14bee9110fc9555b13c9dd28b572bd1b3710e969c07b125210d3` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-positive.sarif.json` | `75650c1ae1529babf552e49abf4241361f5c69f474a61c8438981b8e789dcd0e` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-negative.sarif.json` | `b18ecde523be080504a742a39fe49436bf478d964de3326b91c92a80db535d38` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-positive.sarif.json` | `21f98b57cb2060926d977fb20db0c7c1df26c61e9eca0086fcf2d07855839ad3` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-negative.sarif.json` | `2690c5e8132640d2d84bcb7fdaf39fc1bc479b97fadfdd4fe87f23939ab006c5` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-positive.sarif.json` | `811fd910f4ab3fdaeadf04d81c238ed8b35b3805a35c1e9351a3579f22054900` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-negative.sarif.json` | `ac240901a659b7857c5a32a8aa5070a0aa60e1ce2a7e585693ab0347ce4ae5dd` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-positive.sarif.json` | `502372451613cd7e61166776e0560515b7343ac8e21d37fcc5cea42de16d6fe4` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-negative.sarif.json` | `5addf647ca6dd392ab1eda8c1a434bc438793857b26645c946b00e1b4fc94de2` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-positive.sarif.json` | `00fd69ceaa19398f9de2cc11f6ade301deb4ad4b610b7f0eefd840d8aabbdcd6` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-negative.sarif.json` | `31a753845289ce1f7b42afd68f4435ecaa95e7928a0f588a00703b2e1ffea2eb` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-positive.sarif.json` | `a3cef1664025433122fc62cd4d808c505615a9ef6daed0ab69d592115056c41b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-negative.sarif.json` | `8c20720ad58342536ab9c63b3ba72cd376e0575c20e02efaa19671f4eb10ebd5` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-positive.sarif.json` | `9dfdbd7138320089b9e788bdcf795931af2ba3abe3708b71157cd9e5334f8f85` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-negative.sarif.json` | `e1c94da0835cb9569d0a37cf17ba6fa52cefcb09ca976274800070bedd2e38b6` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-positive.sarif.json` | `a35182beac4d3b4db12a037b865f1e16b01ecd38e8b9da6c226a59f65e7d34bd` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-negative.sarif.json` | `4e7c9a0986451ebb67aba86bb1afc30296764a32fa3618e642de605d022459b9` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-positive.sarif.json` | `eb048a31917bbe861a496dd0733d95c473104c9ffb3f9afcf5b4283bc098cabd` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-negative.sarif.json` | `4b1c5066db9b74bf55a24355257d14956e69490f1bb429079d428412feaf7f5a` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-positive.sarif.json` | `3860afee30db80e7f73abc293a94edc393b9b6a3ec0bfe21a9cfaa1eef2a65b8` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.sarif.json` | `be801c24a80490c9b62f530e92cc504e490b22f4666e8fa5646d6ee89116c6d9` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.sarif.json` | `1e0f64212ef0a80be29c5d01de8cb9c16805cdd420d91b943e66984745361df6` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.sarif.json` | `fe62b934998d2d264c8072eacc288c3fb08456191bac076e9e947d1292f60b28` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.sarif.json` | `a401011cf74203210623c56701a26d16d771d4b2ee1c4cb58e3f05e4338c04b9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-negative.sarif.json` | `8ae63b79a23db2b3ead72dbeb4b79ffa4c3b3d43d366ee85c3bf1d996847514a` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-positive.sarif.json` | `497d82eae31426a79e7ff841c60aae2ffe40e12ac63188e0372efabd419a4b35` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 2, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 0.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-negative.sarif.json` | `979b47b193e79c5d857cb1130c51fea906071436881c589f9e0b008f7fcfd157` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-positive.sarif.json` | `2fbfafab00fcfa0a8539b2697814e2fc877234b5e2ea4de9649052d4931cd772` |
