# Scorecard `bifrost-go-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-go-kernel`: `bifrost` `bifrost 0.10.6` (build `18d09c57d1e5044dec49acac7635d3255ea8e89c`, adapter version `0.1.0`, configuration `3e8066742eac91518264ef6d3ad8f99d2f6dd7159ca1c3b4114dbf5d324b4fb0`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-go-kernel.json` (`sha256:a3597db4e3ccdb2489b720eca08173100cb3220ee5db31743bf0d7a64708c46d`, normalized `sha256:a3597db4e3ccdb2489b720eca08173100cb3220ee5db31743bf0d7a64708c46d`). Generated from freeze manifest `reports/freeze.json` (`sha256:91b0008a546e6b782c1b790f174a71ce44e60039239797674eb49ebc6ac6c366`).

## Language `go`, tier `core`

Outcome coverage: `reached` 7, `not-reached` 7, `inconclusive` 44, `unsupported` 0, `runner-error` 0, total 58. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 6 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 16 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 5 | 0 | 0 | 5 | 12 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 12 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `recursion` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-negative.json` | `7a3cf7607f9638ddc44d60adddd2ed5f147d73bfeca1c16ef868ed23d63f44bd` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-positive.json` | `2e08141a96249295fb7f5e5d6c4082a9d405ab74034e32290a856f300fd76603` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-negative.json` | `ab1b463763f009ebc73cacd5383963dd21cb37410723952f61098dc2438fd1dc` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-positive.json` | `7218be38952da282a3c8329e64f373067d46df3c42fbf78287462e59b6dd0c22` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-negative.json` | `b4c52de009c305d85daa54bd0cff61f11f6ad0fcb7a17ccaff57bc10b316faf7` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-positive.json` | `73042aefc821ec640acb99593af7f7e3c7bd7979e3c757c0277f9f3f4ee5194a` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-negative.json` | `dd41fbb680bcc9d137337b43dc741030761b2fcb2bd8be557c029ba455e6b46f` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-positive.json` | `8d89f66dc06915fb080b2b4090ef84a7fc2637f2b1718d3ea9acca6e4f5bfb23` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-negative.json` | `7f12c4d784fd0cf83af3e72493da972e4462b127b0aedfe97c647379e6fbd150` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-positive.json` | `40bd82d4bcd1f40f9f0fe2ca50e57d211a70384d631f022af5d08beacb3e3d62` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-negative.json` | `c7273f1c33d3216f639c5001ca7d6a146dc6632853914408514e030494b99dbc` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-positive.json` | `e474938e114a8eb4a57f7984df8eb3b8ecdfd7899126db2afa028ccbf053fc03` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-negative.json` | `74a39de3949c6a08b177c92ce4bfe7cab4c57038c41dfdcac9705381f4947d68` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-positive.json` | `74a39de3949c6a08b177c92ce4bfe7cab4c57038c41dfdcac9705381f4947d68` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-negative.json` | `d6de06974de513f4374cff32561426d395adf2eaa303113b073c5415f7255714` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-positive.json` | `2a9defe933a83151905fe85a7b36f3f1959c2b0a5b16534585186a0795f89b88` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-negative.json` | `6bf66359af4cfad0ec77477fa9530770f6d99977ce5c2d170830fbbcedb353d8` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-positive.json` | `801cca34fe707a67807a8e07c69c0002ee53d3d8cf668fe139db64e8f2e402f9` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-negative.json` | `d68050a80f8ac2084c4971f82040bde4790cbe050232644c9223696e62e9ba30` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-positive.json` | `5a5c10568a6a0dc3e08161471a42b45af7bf9607e3548b5d378e5a65b3bec227` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-negative.json` | `dc4a574c1a45e8162aa4cf4f23f32215d7cc625e2d6b3bbcaa7e6606f9d41b27` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-positive.json` | `88e552ca49c7139e93fa78f5ea2b1f3622042e1d8b992cbc4411d11c4f55a210` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-negative.json` | `0cca3deb6af35f61f58ad4857d518652040ac4086f26af899f7a7240ad6b392b` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-positive.json` | `feeb0ebd475c7a37a97fcab2539cd2bfee5778a32265acdabc29f5de4d263e8f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-negative.json` | `981e5c1c152ec19d20f78dbf0e316fbe79596093ccca162ce7b13314616400ff` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-positive.json` | `981e5c1c152ec19d20f78dbf0e316fbe79596093ccca162ce7b13314616400ff` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-negative.json` | `4823f713bc53129c0c5aa6399215259fdb14165ed1185d56e440953cc9276986` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-positive.json` | `52dac5f2477b3c41b90b499bb8c348193ff6a741c7c955bc487621fa05c4b847` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-negative.json` | `09788f225a874a19d5d27a8f96d0effa687b3b6834f0ef3747f7a1fe9470a4dc` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-positive.json` | `39f89e6801ad55defb75f3d52fed3c6404d5de2a94982a5a4ce03eac836098fe` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-negative.json` | `97e7016f8d41ef8fe628513d225cd2b01e80b5925c58e6c542da2ba29c0f6af5` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-positive.json` | `fceff5f07653a6ba093854258edaf596e1773afb988236b022b1bef28da9d346` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-negative.json` | `159f0ca244279042342be461ee2dc618b9393b7d38bf86a77b6ee61e95926244` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-positive.json` | `7af37f1dd198d584559939731f7768681cbcdcb20f83a72370627eda2bb26d86` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-negative.json` | `f9ab3a1ec635eb72156dc3b4c8801bd9f189d9fdcfb4997f1e229bd5facc7bda` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-positive.json` | `3bfb279cf730c36a5bf203c28bc198280d99fca479c3e85fc2bb0bdf7972b0c6` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-negative.json` | `4174252c8aee3b6f1e977aaa1ac593c75ffd64d6d6d6a1bdc258d81c99875b7c` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-positive.json` | `4174252c8aee3b6f1e977aaa1ac593c75ffd64d6d6d6a1bdc258d81c99875b7c` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-negative.json` | `3916b15965217e2e6871190d6360d2b08e3a4ba01676453b0c2c13c300fa5922` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-positive.json` | `fd6c2c96387b1c1a8a439248ac8c21e4576905c604d8fcf1e2b72ac83216f8e8` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-negative.json` | `8035a06996e3fe10628d33527e28e8299c34e832724eeb0d26919247a4517295` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-positive.json` | `65088e5726fd1f9aa48330461d4e0529d1042a50c86456b5881d4cfd88a6627a` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-negative.json` | `047945cbe8c02817c8696943494d5a7cda3bf0d569b402561c5b345e3e14b8f9` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-positive.json` | `2779ef3e2a685b18602beecda6816a5e87175083e30200fa808c0af52e508f2c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-negative.json` | `3973f4205e6b893c0abbf8041e6af9b91b2f539fb9bea277b3d194b5f3ef023f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-positive.json` | `d675f6e18a57d1e37ed33467caa0e933e2e2c86b03117736cdbd3365995b6824` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-negative.json` | `ccec2d2b633df909cc93a9a20fbd45b90cc4ec77e7a397f0d74c4874c91c4877` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-positive.json` | `96513d8d04cc112a65f8348a9304eb964fc326c7e47cd4c0eba2ee0b91112138` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-negative.json` | `900b3da15ddfd4178f3d9fba795ffa22e3b2d51d520148cf96cca4c53c3a0ab7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-positive.json` | `639f7b9ffda3789b9c46c210adaeb186042c592bdd3b63f6bc82eae85ce4c3ad` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-negative.json` | `e0c3874e9b3afb6f6350258b08ed796afbebeed0fc827c85d02e1edd9219c6d6` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-positive.json` | `eb6a54a1f388808be2c775772cd604691be058163ea68dcb47adb0e9da77d695` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-negative.json` | `221528354087722745cb85ff98067f99383b2601029b23787d5edb3be7f7a3a0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-positive.json` | `02b63e0f4b09d1ff0c6370723255a7a2bb856edcf21393fd0a4ec4ec398aecdc` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-negative.json` | `c3cbad789092845fc29e790e7d1c21a0c1beb56d3e1aa4dc709b3f8c20d96635` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-positive.json` | `909473bcd72424f3a22fc6d9781f0def552f759108e237b54f1c7eb309c4b780` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-negative.json` | `117ee9720360cc7091074df575c210c7762df979b72b0b31e2b27c8f69513a4b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-positive.json` | `a9746db9c952f96a663c3b3c71fa742a8e7dc8f9da8fe53491e552f01f4c0b12` |
