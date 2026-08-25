# Scorecard `bifrost-rust-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-rust-kernel`: `bifrost` `bifrost 0.10.6` (build `18d09c57d1e5044dec49acac7635d3255ea8e89c`, adapter version `0.1.0`, configuration `36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-rust-kernel.json` (`sha256:2ad1e552b00c7c6370b26d948e2e5e850f38adeff27a87b6b1f72aefa15f4119`, normalized `sha256:2ad1e552b00c7c6370b26d948e2e5e850f38adeff27a87b6b1f72aefa15f4119`). Generated from freeze manifest `reports/freeze.json` (`sha256:91b0008a546e6b782c1b790f174a71ce44e60039239797674eb49ebc6ac6c366`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 40, `unsupported` 0, `runner-error` 12, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 12 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 20 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 1 | 12 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 8 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `recursion` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `ebeb91727bb6030c899768d4bada6475482129d3a2472cb262f295543db67298` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `fcc65813080dc46e42200520f6e12daa318242934625320c7854ed51bb6cec19` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `3911db452a7086a6eca91ae80a37476ad5e1d01d1d6cc1b3598c43983aec8cac` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `7d3ad25f8ce9719d1bde24ef8af3a64816b8ec5e315c7c1df7ddd5b412108464` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-negative.json` | `759b5d77d05c5244fbdec159d899a6cace22360328a09af2aff4d55bf459dea9` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-positive.json` | `c4b718ea42b1adfc59479f8bd42a7ff924732ef4fc93b240464eccf5bc38c88c` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-negative.json` | `16a9770650c858d134a820031ef7f748fa9cebc6190c449b016033f6bc9b4907` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-positive.json` | `16a9770650c858d134a820031ef7f748fa9cebc6190c449b016033f6bc9b4907` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `1f0b9a83f6e2910e95c4719155f6559634691379134c7eeaaf4fae8ea5c19c26` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `52772844a96a3dd7aa52e0997ae62219b75027920764214db5b5a5df376503da` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-negative.json` | `f1a886083aca6541bdaa08e7ac42a68a8ec2d06aaaf5ed88e083c5bf97e18e6e` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-positive.json` | `9087598c55c633d65683d9a8bb0f35215ba48d52abc601592067fd8603cc62f6` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.json` | `205bdda72511eab674fe4e312a6d06985e98af54e2028d89b68c32e675d2fde1` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.json` | `205bdda72511eab674fe4e312a6d06985e98af54e2028d89b68c32e675d2fde1` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-negative.json` | `2f947a9ce865ed9ee3389712631d00ff1adc375d5367268fe73e275af34206e2` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-positive.json` | `23f9bd1e437e4c91ee031bbe08932e6ba5f8efee1e728f26f6325ea93a9b6529` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-negative.json` | `dbd4931bab5ab47ec5458334062bcbd74c078362c3fa5a71a9a3b6640b7bdb00` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-positive.json` | `983b6eac192613905ad130b58835c49044b9860f6aef35e49a7a6a5c2040d99c` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-negative.json` | `c025615073e239cc3fbd274e849990460e10d53bc84d96a66df4a8278127b293` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-positive.json` | `6b392df002c622fd8aebf03b5d17cdfe11f144482901e80f222b32445f99d552` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.json` | `25bc78eb58acbec4d26fca2e6280be40a0d8b6681b09df560d9f72d986f476d5` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.json` | `8b9eb12627977e973cf9f4282f4d2debc2ce7cfae367df75de0e5c41fdd3ead9` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.json` | `22b1706bd2028f7ca093b7c4ca0bb74f39a53cf74eeb9b2034b41de9c3c0923f` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.json` | `7a8e1581e67d9c69d2c7fed3b99bc9f278f7fadd1fb216ac5f5e0ba7129789b1` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-negative.json` | `aa0049731e3432a749f45ef38b88ec6e02d539f23b8c9b0c6a98a734088bc091` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-positive.json` | `aa0049731e3432a749f45ef38b88ec6e02d539f23b8c9b0c6a98a734088bc091` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-negative.json` | `ca7d49b2b108abe8dcc271eef8c27d94cbdc67ad613f4067f67527dbafa0ed2d` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-positive.json` | `ca7d49b2b108abe8dcc271eef8c27d94cbdc67ad613f4067f67527dbafa0ed2d` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-negative.json` | `a35892b957ae28aa9db576caacec5eed16de01d5fcf28aebbf9e35319236ad95` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-positive.json` | `595a9b9f188d8c4a17816f4c0266b1d37cec9dc25bfcaa9e65f1b5c665b7d592` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-negative.json` | `33831768e2a5a28ccfbfbfc1333be12b569853166802331287b4c8c57412a056` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-positive.json` | `48daccd6a21b1224b1aa16fd2f12afbf5443b6a307a0569e22d40572fc7e5728` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-negative.json` | `76dde6f24fe6ce1f32ac725eb4d1266a9cb69eb0b2da04b1b1e73c0663e5ec33` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-positive.json` | `76dde6f24fe6ce1f32ac725eb4d1266a9cb69eb0b2da04b1b1e73c0663e5ec33` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-negative.json` | `9a09e22508b6084524ab545e80302d4bd03e23bcbb5f394a3ab231fa4406962d` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-positive.json` | `335f8ca9d516ae19dfefa021e10c3c3cf96d159a2899d24072d5b805ad2410a4` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-negative.json` | `4b788079edbad2b3854e2a0542184bdcc85e736c07f28fb5443c54b4d6c68c59` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-positive.json` | `172e67137fd7f919f633236698c7468999c4102ca2b6beb346c7b847c78a84c7` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `bf08a90617b41fa9c2947e5cdb68277732e9dcae114216cd869e9f1c560059b9` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `12f7782aee05751bed236aacaa85eafd2d37e96208eae485bcd847803eaae6d4` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `0bee4496e5e714013ea8d2ad97a92b446f678e0b3bd99d7c319e75d9ca13110a` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `56fec556791fe5fbfc5421b040e1b47d109f9f663b9aa71b4fc4a545ab78bddb` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `52b9f916729f2b1b9cc8ae63950b24ab20e143fbac5e60ca58af51f5e64e22a1` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `128f4984ee9018f60d579d7bbbf57a5ef176d0a9f01b56bb21b4a39210402140` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `89f6e24f53512fe251f590ddda8c8ca803a396d7d265e3fe898eaa242a02ea36` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `605edba44a9dff052616ac5df3c0b915e1afcd1e039a267b0e1f7af0cdd0db48` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `eda240208e3d04735e6fa58ff2f29ea967e69a12c7f8c8b3d9c58f3afdf5fd04` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `a4236358223227ff498e72349c5d7fdc68dd019823c13b8a447ad6754880b298` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `0bc565b18ba5c94271ca48258b24a60c2ace02f4e5d88fedd06feda7f770f95a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `0cbc4b650e2c9e9410f653213ea6aba73b8a3726b57e1d32d2d4fec12b7f0915` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `a92297a1c86fbc997f940d215543902f05b311d72f241ed9f198c8245782d2c7` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `00240760909ff2cfd3bd6d19d5add55ceabb22ca5af3d634cb20d68583a3cd45` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-negative.json` | `d1049743e5c2ca35130310a0ecc06a17f1267b0d19af28373b28f0f912e5efdb` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-positive.json` | `00189151f77db06b90d906b46d01706e346487dbd5fd4fa06dd114bdf8b5c04b` |

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
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-negative.json` | `2cbaa3a49cc0fd7cc79dba8ad03a16ddb2b977051f756d859648e124f23a5f88` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-positive.json` | `2b0125d048476e374cf7daa2f66672e4dc78783a640f2b66ccddc1e7750357a7` |
