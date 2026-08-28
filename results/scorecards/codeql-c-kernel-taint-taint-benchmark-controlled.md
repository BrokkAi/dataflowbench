# Scorecard `codeql-c-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-c-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `719415b9134dfd43390ffdb76eef45f7ed022f907f22913226c22f93277b62f8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-c-kernel.json` (`sha256:9ed3846bd073c4078f81a8702fe6d71010d9dc2a6dadf4338765daf804fb5651`, normalized `sha256:9ed3846bd073c4078f81a8702fe6d71010d9dc2a6dadf4338765daf804fb5651`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `c`, tier `core`

Outcome coverage: `reached` 23, `not-reached` 25, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 75.0% | 0.0% |
| `dynamic-dispatch` | 0 | 3 | 0 | 3 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 6 | 2 | 2 | 6 | 0 | 0 | 0 | 75.0% | 25.0% |
| `interprocedural-flow` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 6 | 0 | 0 | 0 | 100.0% | 14.3% |
| `object-sensitivity` | 3 | 2 | 1 | 4 | 0 | 0 | 0 | 60.0% | 20.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 75.6%, FPR 14.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-negative.sarif.json` | `417f5bd5309673643ace3c67909ab32daf99eaa5dafe12eddff7319e789082fe` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-positive.sarif.json` | `444c18d70d79ac26a32ccd2a0dfcdbd76e54f557c33e9741cce416153d448bb6` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-negative.sarif.json` | `3c4a61545ff062e4f85e21268112bb9b76d224146f3ba14a8f6c5f4a6b77be13` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-positive.sarif.json` | `13aeb88ee986d707e7cc9e70c9acc2d978ad59e216ec91cd36e20f25ab6c18f3` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-negative.sarif.json` | `ea4ae5e22fb60487f6be7d2ce79cf646e6accd89e7ed1a4017a0c3b82bb96652` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-positive.sarif.json` | `011c42837598f90d88ae7e3d6b402979e203ae975657c2ba975620f3d76af1cd` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-negative.sarif.json` | `2caaadc43da96c0f185afe183df2e5a573276464c42c877ead34c3e009a1e9ad` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-positive.sarif.json` | `b1de3900cc1392a2954d4eea9f97ffc9525c2e666f64ce2344160c3bdcd8722b` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-negative.sarif.json` | `241b6b076b5ed0c1392cd939f4ef56f26c06571fcfdf39be8ad7762be1cad3fe` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-positive.sarif.json` | `f2e85aaae525e651c102116a740cfe42bfcd6cc2b10d13ffdd500af1526a437c` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-negative.sarif.json` | `c434d7ad1be0fa001fea9002614393474a7fdc54859fadc7581f0a7ec8661212` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-positive.sarif.json` | `7f5c79ccc56186ec7918bcfa9b4acc335daa761d44d97f04fbcfabd0eddc4bb7` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-negative.sarif.json` | `4f469e8bfdbc0b49bbc561a522d6502b1b1915c27ed44b3fc964f89df6873b78` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-positive.sarif.json` | `0ab57745bff45f24394224a605aafc5263fd141ed3f56fe0f53704a29a4e0fdd` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-negative.sarif.json` | `d1a49799be2f33ebfc329400f944833b098cc8c849678d0552ea8c81c9b9c223` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-positive.sarif.json` | `4ed8d141db54450d67da1084188fbaad49ab35fd59fa3036a542279629c1246b` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-negative.sarif.json` | `ffda61637fb99c9f0d9a440391b29ce3e05982521556a394fd703e0123a9d413` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-positive.sarif.json` | `9f520c8a393f5621fd35c1ad7ee13185da957fdb482a6a2b0d385709d44ab5ad` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-negative.sarif.json` | `45aa28c84246840ede88ff915af4738d78ee03e041286cb1d7424ab1be681e3b` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-positive.sarif.json` | `7d8d81f61afd4ac2e523dc9b9af34bc0ac790673be61bcdd22a992702d5b4fe6` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-negative.sarif.json` | `fdd60cf83f0a4083e764314130e8e36449487618e26aaa62ebb32902bfd3780b` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-positive.sarif.json` | `58117ddffc76a998019a5f12432d35b7a840525c3f91aadfd6b15baecd16b910` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-negative.sarif.json` | `d76743134fdea37599317dc149cfd357b2c65870f608761c109e3ea11298804c` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-positive.sarif.json` | `1202351358617716fa7348332c21ae03eb6dd8fd7f538252ba695175d270d251` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-negative.sarif.json` | `c8cb5780cacdcc98bba1c585a23967eb9762c72be5339e9535d03dda168ce53d` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-positive.sarif.json` | `850e6460ebb9cfbc879d32072fe726c1eb8091c486f4f90b35b8ecdd6a8b39d4` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-negative.sarif.json` | `4483b1a38c636c30c1ea3218b29d2d98b93e293d2d931163a8f19e10f3a0c9b6` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-positive.sarif.json` | `e4c3229958ab454d01f42caebaeb0a4c9dde18ee236b6de3238779cf72ee09fe` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-negative.sarif.json` | `14864285c50211e721493e3ed336342947778e2b238cacc53ce647aec2141760` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-positive.sarif.json` | `a45443be7e4ae0ad9a42a4384d4f6b521043868c371a282f614b95e7cdb550ff` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-negative.sarif.json` | `f3ce7cdbc17b85ade3ac34ab7e06a9e0b9889bd55995280f398bc0be46d0b3c9` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-positive.sarif.json` | `c226652d41185ca691395feff67252f66f4c7a79530a28907dc5b15801c4e750` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-negative.sarif.json` | `5e0dbed519a54aa8725cb542b92d93dc0c2f612d99027257591871549cb4b9fb` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-positive.sarif.json` | `50dbcc9e598a4f5e4706a0f330450416afb0e96b9ba262e39e279c5a505be7bd` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-negative.sarif.json` | `e33e3be7e628476d8cc7ae704c2d4cc8cb5866451209dec70f9e3750be6390bd` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-positive.sarif.json` | `8c68f90dbeddd6d213568335c9b00eab4c329941471c1e24e141a017b4070c36` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-negative.sarif.json` | `a1177ee80d1f881449b94ecb36c9f9bf3e258240af4800739d30536ce2d1e580` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-positive.sarif.json` | `e1765fed1c78fa30ad3482015fd16378ef358b246f89a389ddb6b084dec69d78` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-negative.sarif.json` | `eee3c8f0a41e1e177db499993c0d5fc6472066a013b507e00db0524d2a985bd3` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-positive.sarif.json` | `7c4d541c2927080fbcea38af9a7a7135ddeca64457c39ba15f9634840bd06ed5` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-negative.sarif.json` | `37e7855190dac3d883616ea17ec17c76f2e50916270afcd52b6d88a6d198a042` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-positive.sarif.json` | `62a4dd7fade498a8ce1d12fdff50ddf7530e00ac97031354ce2c71e91bc59f5b` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-negative.sarif.json` | `fe2add9250c62a0a0cbbe0a98194777df31b75c2e06256677f69157ad854549f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-positive.sarif.json` | `42906cf110ba5e0804eb587bfa7a82be03018dfd23140db311ae7bf23fa51cb0` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-negative.sarif.json` | `9433ce53c033dd80cd4f153e2f975382a2e8ce8356aac3f2589f7df187ce88be` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-positive.sarif.json` | `9db13788b59a86c2597f5b7d10d70adee4166f73e158065b403c7d51fcb2e98f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-negative.sarif.json` | `fac906b392cfa1ad71e8479ca565c0cea24ff6d4c8565f135dd2760b803dffb3` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-positive.sarif.json` | `72874dd24044705c4e6fe8e16b7668fd5dcccf01d1af22d30f932fda3f93e3ea` |

## Language `c`, tier `language-extension`

Outcome coverage: `reached` 2, `not-reached` 0, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flow-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `heap-field-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `interprocedural-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `local-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-error-code-return-positive.sarif.json` | `860d02b2574adcbf4a2923b31ce290189292fba7b221f7434c210ef6c4442533` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-goto-cleanup-positive.sarif.json` | `c10921d0a238026f265b5f3b82be14931cd7fa77d91f044e72ebe1451f599697` |
