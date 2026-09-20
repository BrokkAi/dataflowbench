# Scorecard `codeql-c-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-c-kernel`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9`, adapter version `0.1.0`, configuration `d7cfd19102253acf18f8a79cfd1dcef55d4f19574c543bfc379c96ac49fb904c`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-c-kernel.json` (`sha256:e12a3deb6c98e283fdcde57a2f1e301821457843f6c063025ffeb9f40f4b56a0`, normalized `sha256:e12a3deb6c98e283fdcde57a2f1e301821457843f6c063025ffeb9f40f4b56a0`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `c`, tier `core`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 56, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 14 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 18 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 28 | 0 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 14 | 0 | 0 | n/a | n/a |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `recursion` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 56 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-negative.sarif.json` | `0c491ef17793d413582511c42de3828a3ccade3d92e8476f4493e7dc9a7e03a7` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-positive.sarif.json` | `a90278d4b762322d15d687d06c8783fe15398614ea4652f33aaa642b23c8665c` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-negative.sarif.json` | `7e357e2e59077c5e5f7154d5a42a4d8d6551f82863bc3291ef4434678f7002b3` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-positive.sarif.json` | `7e9fb7471698a560250bf0d55e9ea0434fc777406a9c4115a7efd607651947d1` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-negative.sarif.json` | `c9a7da0a75b5dec438ee39de7f04eb2700fe320f33a6ea2dfde8ffc90d71a7cd` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-positive.sarif.json` | `7ea806351deeb1ba2077406541b202e7885ef670d8a09abdf3c31e025f246971` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-negative.sarif.json` | `5eb07d892d4eb2a8ba7e2f125c4026f3713ee5876546178cacf1ed0d6a4e9f59` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-positive.sarif.json` | `3bf9e74974949c98048d6c67cada343b264c0f7bdb1acfe16655ddae6d83300c` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-negative.sarif.json` | `ba729e3e121dd04f0f54f33afe6df1a197948e807a53762fa5c9c4b54f3dc6cc` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-positive.sarif.json` | `284613b99180d96a93c77dd8e5396a41858bf3458d673ffc62dcdde1e6fdd31e` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-negative.sarif.json` | `48e5722003ec2c18b5d1f33c30989b5482cc66eccad57b01230719ec75f19c05` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-positive.sarif.json` | `c2c3cccb15f2095dec90c59f7ec6b54fc1d9b8bf573233d596a03fe5d6bfa27d` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-negative.sarif.json` | `ab5536a2b39becc3feb9c8cdfc32ff25cf3c7a91664d179ec069e28f4a6edd35` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-positive.sarif.json` | `6a492e4ad8b94e8be4896f86a736361ace1f621f669bb67630ddbc163738e9e9` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-negative.sarif.json` | `8e1821164ec00b74a8995f7d57f515fce6ad8dbd6b212f37ac3935d141e3750d` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-positive.sarif.json` | `f9efe6e6892848cbc7b08e957034fb971a0fb79f1ce5f55e802c9fe13b50a73c` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-negative.sarif.json` | `f2211334c1d4b055d75b2bd5b0aaac543e7cf86be6d9620c7b1273e51618f401` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-positive.sarif.json` | `409a0d57f77cad7ee6a7be28a2994c80b6df1018edd49820cbad3f2d360568db` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-negative.sarif.json` | `49a84945b99cb6ad1ccbaaaacf1ddabcccc66627316d9cb15778717d04ebc939` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-positive.sarif.json` | `d01ed4063fb0d1bc0b43aa9f468d926a6c67cdc1551f6639d7c9c762e5b199e0` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-negative.sarif.json` | `57cc22bd0f4a4bbd68e84c1d3694f39fe82bb28fa1057f614b78fe54a211022f` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-positive.sarif.json` | `d7029de327f0d1d981b3d960314d31d9c992e85b9e88ae8d3650115efb1a8b3c` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-negative.sarif.json` | `4e587c29cf4086fea71dbcad1947de236ef17dfc0c7fe06bf8679c7b693f9316` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-positive.sarif.json` | `a1d56bed0061cd0ae5d36616925a506ea908eb48fc0d11a59f9f73bbc5a49bb0` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-negative.sarif.json` | `7f0b74c036e8d445636ac1b61d00db81429f1e742b27d4234ad1512830362116` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-positive.sarif.json` | `33095c24721b69f0004f66338b9c893ff4c3e8c0fcefec22af5c94cd05b431aa` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-mutual-recursive-transform-negative.sarif.json` | `7d3e3bb624dba7510b877373d0f48d4d32b08209714a48354846174f3f95f287` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-mutual-recursive-transform-positive.sarif.json` | `8f28acd47039f86e97f7e5914e6f1b75322d6829c6f006d3f5bae84ebc569bd2` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-negative.sarif.json` | `0437d9ba1112fa913d7cb9ab4969f3768608f95dddffe1cee6da53a697f6ac07` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-positive.sarif.json` | `9b543b737300678946442c3f12fbb4480a30817f4df45d56fc9f1a51919f5a67` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-callback-transform-negative.sarif.json` | `e9ae574fec6ceb64e7c6ad5e821e1fde155e45eb20a1d1cbd30be07287ea4546` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-callback-transform-positive.sarif.json` | `c76521af1ee04bf6583b983427ba2751a9b7f1b5f3e77d0a85c94061f2e18de5` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-negative.sarif.json` | `a8122b636f7419227e80417a7e67307439640db76cd95ddee680ce5da574dbdd` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-positive.sarif.json` | `ddbd300fe2476e63299de4c46a0833b9f39b480b7b49aee03a62a5c0e712ca1a` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-heap-unwind-negative.sarif.json` | `a60f89ca0e2d8df689dacecd998cb655eb3d170804694b3a601e751842c9d88a` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-heap-unwind-positive.sarif.json` | `19fb46782cdd6474e7c4a4fd597338788c1bb403f90222320ba6a31cbeb1787d` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-payload-transform-negative.sarif.json` | `64fb223ec4171616c53f581dc75e2336db9389c3f621b03f46540ce0e7e6da87` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-payload-transform-positive.sarif.json` | `09ebc69ec904d387eb1edfe16bd495abbe60c2567703730812bbb34c0b1327eb` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-negative.sarif.json` | `25e999c24a3211bdcb406d388798ccc7f6fec1788610f93f38683bfc4f25e3b8` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-positive.sarif.json` | `f6961acb07cfef8d5ea31ce70e9cef27b5be515a5422c8d8b88f7071cfdb679f` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-negative.sarif.json` | `c1533cacf3a1407254071efdb5ccd83c9b88aa5dd01fa1b0d0adc105c44e60ba` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-positive.sarif.json` | `e402be3cd78cf7a11bc9c3a4260b04387f10699125cb214878d2e277de63ac45` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-negative.sarif.json` | `2bcb17509712267e5c2a260a1be267c5812751000627e973808910ed63b3ea47` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-positive.sarif.json` | `666d9e2bad93e635fbe021373cc6e8ac1471c101514f7beacec1ad8568e5a6b7` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-negative.sarif.json` | `b6b094b2097e4eba5863a24ebf15e040a9e80ab2d7c4a81d0ed8ac3b86c32d2d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-positive.sarif.json` | `d92a840f9458c51c9cad65c5a80305273f53d2c80fb125ccec69089c8d51e891` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-negative.sarif.json` | `b2285a4c9f6b1944e12d39131a8dfb343b6a8d78fbd47a3e8200b8bfc7192413` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-positive.sarif.json` | `2640cd15c6e17c7900a8a79374f9479ffb3f8833452e692d1848258840c51c1c` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-negative.sarif.json` | `d4801062ff82373fec86ba0720263289364b5990902a36e5c205615fbe985ad1` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-positive.sarif.json` | `d607d62ed06d114d05c07551696992d9be2b4382e5385ba9479e0861e1506e93` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-negative.sarif.json` | `0b0048de3759126bdb3e0b67f4eb49ae1c02aaeeaa56b923a10d8a956d14771b` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-positive.sarif.json` | `d9c1e2dc7527dfc18730de8f5bc8b1616d61b721237f85dae170bda6f022c645` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-negative.sarif.json` | `5edea5201a55014ad186b1d4e56379e3b52dbe0f69378e50afdbe8aea7d579d4` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-positive.sarif.json` | `370dd8741d63c899e34b644fadb5312f626e02b27fb4f1a3ae2dc3f1e27ed53d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-negative.sarif.json` | `c6b208f710be31ad720b71f736e54373a09d011e1ff816e290da54972f68abf5` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-positive.sarif.json` | `5d9e0c37d0659e0aae57ca298bbdc5ac9767c0f2288bc8607f0132c2bb22230d` |

## Language `c`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 2 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-error-code-return-positive.sarif.json` | `ce3343b31122caf6fcd82f1940753208a3e305931903e4b28afb191ab69d57e0` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-goto-cleanup-positive.sarif.json` | `d06585072df29e91063588156f05dd6d90fc771e32be4a3ed285bb5d7e8a6687` |
