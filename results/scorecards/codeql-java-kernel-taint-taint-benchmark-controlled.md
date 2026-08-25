# Scorecard `codeql-java-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-java-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `eedf28b140e6aaf2c27cac6369ee552803cbc7b7674abd70583e3e962e1ef8b6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-kernel.json` (`sha256:bad0469701d0f3c45825cc4ee8d0448bdbec40e9006cf78935112e09e77e08db`, normalized `sha256:bad0469701d0f3c45825cc4ee8d0448bdbec40e9006cf78935112e09e77e08db`). Generated from freeze manifest `reports/freeze.json` (`sha256:91b0008a546e6b782c1b790f174a71ce44e60039239797674eb49ebc6ac6c366`).

## Language `java`, tier `core`

Outcome coverage: `reached` 29, `not-reached` 29, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 58. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 5 | 0 | 1 | 4 | 0 | 0 | 0 | 100.0% | 20.0% |
| `dynamic-dispatch` | 5 | 2 | 2 | 5 | 0 | 0 | 0 | 71.4% | 28.6% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 7 | 3 | 3 | 7 | 0 | 0 | 0 | 70.0% | 30.0% |
| `interprocedural-flow` | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 6 | 2 | 1 | 7 | 0 | 0 | 0 | 75.0% | 12.5% |
| `object-sensitivity` | 4 | 1 | 2 | 3 | 0 | 0 | 0 | 80.0% | 40.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 79.6%, FPR 19.8%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-negative.sarif.json` | `8f17157f6cfcbb28894a17f76f2f27fbfb589d0a5cfd3a59a355480fe7fe85bf` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-positive.sarif.json` | `ac5a5139ce3ca0577badf2b5cced59744b0efcc0ff763768ff3ac499f0e954bb` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-argument-position-negative.sarif.json` | `762be32dc7af64e9973a7f5e805c1a7036bd33608fac5b3289265e3d3ecf43b8` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-argument-position-positive.sarif.json` | `63dc783fc69ef8df5d851ff4771291e15195b97bb1d6fde843e049c48e2fa1f7` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-expression-negative.sarif.json` | `8f1f7516d7525d76632ca3dabac7bc6a67fd2b42010981f16e099c7d22c969cf` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-expression-positive.sarif.json` | `513231797c23a87e4e15cdcbf7bf7647d3b59a6fe8c53dbb88ef904b4dccc15f` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-array-element-negative.sarif.json` | `153a1273b3ddb34707e6f08f99bc8736c45d10734c18553eb59619fef85b9933` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-array-element-positive.sarif.json` | `175b4a32dcdb6850653cb8229b27d46125160d56e82d04df0e47a0a1a5ca07c1` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-branch-join-negative.sarif.json` | `98d4d6ed6470732cb88741e047789517380d1fe5cb4a6a7a27182cade85108cd` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-branch-join-positive.sarif.json` | `d97e62ea5cbae9b2c9d05abdb3c3ac8cbe22ccd79c49df22fec6d69e71b09783` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-call-context-negative.sarif.json` | `f79e0f956dc913ea09b5d66c2d0d0c2621d538f2e69786a1d4f8a9e3633d6be9` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-call-context-positive.sarif.json` | `fa8275bfa28ea6fb37da2c20f3c873b318be1edc3b0ce2fb17aefb730d345904` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-negative.sarif.json` | `e547f21b9b9d296f905f0e781afb62a156a5f80ce59239d1553c704340b98b30` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-positive.sarif.json` | `5ea74fd957f8d1971f326ec08a2a086da5a3d4f24a33ec0f293a0c66075e6fcb` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-callback-registration-negative.sarif.json` | `23ce5b7269b64ab2d1d890c8e566c22ed7498dfd2158d6fd70d34514f290259b` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-callback-registration-positive.sarif.json` | `1f739b23cfce62777008e436ac5065958048edf8f2fb3a50446244a09caa0e44` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-closure-capture-negative.sarif.json` | `9897b80565c8e5bd94cf63a975e30a73b90326e1321d9567db95e11c041b92e8` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-closure-capture-positive.sarif.json` | `74a2df3b958acfba71e46ffb849df1996e68bba2f992f2da4b79ada664836306` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-computed-property-negative.sarif.json` | `a69644b75fec7f509c603b83f83c98642e6180e3098b6ca198881b1c865ea77e` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-computed-property-positive.sarif.json` | `3cf9035dd1a800f1e472d29d2c7831372d7772a6439aeacbe775a104a7decc06` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-negative.sarif.json` | `c1473879b8ff0d1895d41c290c33eb924a3f3f237e6f967ea0234ffe50457b55` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-positive.sarif.json` | `be23a3816f5217849acb1a7655a86bf5148df88d387c53cb39a6691651b0c74f` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-negative.sarif.json` | `37b2c6a081242822f33008e518fac0aab21aa5a7c54535095766381bf015518e` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-positive.sarif.json` | `e25f8d1393319578593d2571a9826506acd9819408ba93e23713c39562dd8766` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-negative.sarif.json` | `97f8a3136dd25f402beef83ad2bc897ca02901038bbf5081b31ce1c458f40161` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-positive.sarif.json` | `102dd03849fe27cf2f463a57bd7580a58b9ae7f7939f40bdfd4e5d704bf6589b` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-element-object-negative.sarif.json` | `c060d5670ac618c1ae5c3726a253c36ab7cd192aaa3d201c8214a465b30e56d4` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-element-object-positive.sarif.json` | `ecdc0f5672440883d03ee471b46ccb24caef143b006af20a581d264301a7d8e0` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-function-field-negative.sarif.json` | `3d2f3e8298eea6a43ae4a271b91bce0f0bb5666670d77c96e85f74e0a2c4a8fb` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-function-field-positive.sarif.json` | `97d62bdde763625db7844caea072718c312419e466ed19416afa1bcc3a08bcbd` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-map-iteration-negative.sarif.json` | `37ff0fd523a67891c80058cebecd000a568d4f88c13999dcbcef33094c01c45e` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-map-iteration-positive.sarif.json` | `8de0ab343312b571d2f5eb4933306b935f95e94f68d4675c0614f3fa750d5c06` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-nested-access-path-negative.sarif.json` | `4bc23ae8edb67c72c9b414ec0d8c6c37c7b1c4f3a75b382e5132b604a4bd6ca6` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-nested-access-path-positive.sarif.json` | `1541c7abcbcef598f0f3f3865472d523ca5acaab8f1ddec990e7ba976906d489` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-recursive-carry-negative.sarif.json` | `1795d69517b8c9c74b4bed23934c2fb02c2d0dfb3240db9a4408d3642fb34649` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-recursive-carry-positive.sarif.json` | `1d4d622c55245c2b91b0a3b3b2b9c7eaa64b82e71df5625100cba9198525e6b5` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-negative.sarif.json` | `45f170210be0b2c5c244ca15d17dea43f4fd795539d6a27e6b33e650c339e047` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-positive.sarif.json` | `a07fe99e4706d7671161e99427c14f25148eafbf8f2e497e2a1e2074602448c2` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-direct-positive.sarif.json` | `3a13bd433fcb93dac200f30661d5a479d5a67786378dca0c56d8e477b58e327c` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-explicit-negative.sarif.json` | `2f86a0e0fcabaa3b4d4ad85ade48169d418a75261644bed7f46a4ccbf7d75eeb` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-negative.sarif.json` | `edef5efa69af0c2e7af66858c44bc83245f7403797f703d877d822d41ce5cc5d` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-positive.sarif.json` | `be7c7dc6b0f182e1402b02afbdac05cf478cf159dfd8e1168eef98dbe0853ce3` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-infeasible-branch-negative.sarif.json` | `bbf69458a6bd6f435c8e3ac5bae3fe77009c671ff78bcb67cff1cc1ccefa466e` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-infeasible-branch-positive.sarif.json` | `87ea389535fc58b15f32a2260d2be44f8a889bfa676c71363323b08cc72f1bee` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-chain-negative.sarif.json` | `f9cd0d2fa341b55ce19f616c8af5dd359bc501dfb18b2f2376aee02f8c6c47cd` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-chain-positive.sarif.json` | `49afc54be0c38ee26aba4caccd629b94d310c3c2a652c420483f12392d224b54` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-overwrite-negative.sarif.json` | `409062fde034823107a9bb2d6d7ff742889afb40d37fc8b2c21d0d3492b032b1` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-overwrite-positive.sarif.json` | `3a2b07003ae4967edf01747863a38665257a7c47f059bab9c232462640a38ada` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-negative.sarif.json` | `f403773e82d87b962eed4bc33c0b112077c11bc7478f73a5a62d0225c1ecb425` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-positive.sarif.json` | `f8c2a99a0a746f02b713992a47cc2a1ccf4053f509814b47edd4082c1b018336` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-object-separation-negative.sarif.json` | `7497c8145d411296814b08debfefb092dc3421f9430bc0cd9e740c16d2816710` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-object-separation-positive.sarif.json` | `638a9cf8359d8c2bffb78267dd2281ef05aa24b2429f3fba67121b14baa81301` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-negative.sarif.json` | `9592fe1d60d1df3b3464f9a181471d562d9bc8700f8128280b8b46b53475f7be` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-positive.sarif.json` | `2a67c00d4863a7c70179eb9bc9fca242d38129ce2da5724e116ebc8343d12e4b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-negative.sarif.json` | `9f8ccf8aa3a9c815f1eaf4dd94a3f4176ccfe528baa3298b1f7f6af49a864f66` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-positive.sarif.json` | `f2a5c32ebb3dc49c255aca0a20bb2325781405ac990799b958ac451de4f8c94d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-same-object-field-negative.sarif.json` | `82087c8e9692e1918990f912b413dcf1cca6f4171d568fbcfe76882dde08fec9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-same-object-field-positive.sarif.json` | `253b8a56513e5b6e6a934ce4a47183b2a7c55806a751525cd3d1b353e5daf40e` |
