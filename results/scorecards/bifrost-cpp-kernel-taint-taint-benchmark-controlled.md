# Scorecard `bifrost-cpp-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-cpp-kernel`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57`, adapter version `0.1.0`, configuration `b29775f28c44e0830155def3030cb36f7c7f8906c440dc18af2be6f7ddbdc22e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-cpp-kernel.json` (`sha256:13995907b4422092021c89981fbbb4f923250f2cff4ddbfa7dd8d6c804c9d46e`, normalized `sha256:13995907b4422092021c89981fbbb4f923250f2cff4ddbfa7dd8d6c804c9d46e`). Generated from freeze manifest `reports/freeze.json` (`sha256:3228af686d09f8666989368483bef375bb28b94025b55e31eaa7a0bdd29506ee`).

## Language `cpp`, tier `core`

Outcome coverage: `reached` 15, `not-reached` 15, `inconclusive` 26, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 6 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 4 | 0 | 0 | 4 | 12 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 14 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 2 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 6 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-negative.json` | `78c1873f314fc123914ec081cecb84286ecdd92309e587d486bbf5e9a21fbdcd` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-positive.json` | `2fba5bae65f3b1ccaf363422ad1e66a02cad4092a5f8cf5a4f745658c435b8a1` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-negative.json` | `877ba50e7f62c5bdb3c403d971a43bd75261e74b41185f253c33e22320cc3b03` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-positive.json` | `3fad6840afeb69920d64debb88e8c635186722932d3f6950e4ba8b096780780a` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-negative.json` | `0532d87de7091066ce3e817e67ab8179a192e3b9f4ad30399153ee3da695d3b1` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-positive.json` | `e8786ab461fe03c7dd5a4e43f95384f7e2e2cc1b6bd8b5e1a55be01200cdb449` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-negative.json` | `01d1772a90d3c1bfffb0d9bbc589ef1550c7122e16d1a6038e23de6e14c51e5d` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-positive.json` | `e4e82fef51eacada847b3d14d23adaed75bb681ef6171564500e9fa266de9bbe` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-negative.json` | `88ecfb95eeca4b248d3099644b3ad36ddea1749f7fe4f7ab732f132982e5745c` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-positive.json` | `37a892006b823f9b280161a8a29e8f4d3fb45ec70ac8bb1b896b4d3b39a64fbc` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-negative.json` | `b2ff438b99c669c84a2bdc1b67ae89c43ebb6ce6caafdf82d32451f5b9385b36` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-positive.json` | `732169a2d20435f4f705d03ab7ebc2d432177c15a4f499722209b31366e92090` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-negative.json` | `e77376e7834c9fff7b0b70f76309ff864dd1e70a5ad762cb58df56920bf8a1bb` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-anonymous-implementation-positive.json` | `b739c70809b88bf19c8e2ac988ef928e8406b5a9983f34e1aeca8d5ddb9fd4c3` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-negative.json` | `e24ecc6ea124f529d53173efd9bd3966be5f2d2d5c65a1326b4bb670cd8309ad` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-callback-registration-positive.json` | `edb7080e747b54b8b334c77177fcc4ff4aac3bed281dcdfc7a3e1324b542ed4f` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-negative.json` | `9929bf5ad862fcc489e99f5e8ef9b4018f1781e1b00cf5e8969a2703a79b2d40` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-closure-capture-positive.json` | `b51c5f0df36e190c2f5c44a830607e0d0e9b20abd0981f93bed7c8de72c440ea` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-negative.json` | `0dff8cc4c49aeb55c2c437e5d27581421c5229f5177f2c8479860a782c6ac313` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-computed-property-positive.json` | `dbe2630823ecc8315f5a7276ae1491ab99304b50de83b3b36b07916607a1c9e0` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-negative.json` | `c8e73a7f5407fce7ac526d958fee6f826d472bdfc2b8d7ce9888fe500cb65ad4` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-context-pair-depth2-positive.json` | `201122cbf6c009c44f774ed5bf9e69213793183f9de3cc5b1e884c5d3603fde5` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-negative.json` | `62b12f47e43c1724d1da3d3277b2e2375afa51288435b77a47146b9e6f76c9e5` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-deep-relay-chain-positive.json` | `602d49916eced3b68d861c1b38f5983647498f06b7bd6e9da9a23a9f2d1fafd2` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-negative.json` | `cd9809ee34bedb5046de13d4b7e06418f487175dc9e6738b53192038c77240de` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-dispatch-table-positive.json` | `c9c94692e2dea842022d6d7d5daefe670112c66f7c7cda702974e405886cbe64` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-negative.json` | `a1c600f17b202e606ff57bbc517c53aefdb01edaec58438b9169797b90b80f9d` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-element-object-positive.json` | `e1d536fc7d36192efed12bcfe87f0a1caab72daa83404e1a0c9533992d2f8222` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-negative.json` | `0c74e65522753275a226481309da1d915baea8466f564dad2aace573cf7d420c` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-function-field-positive.json` | `030dcfac30e6a3bbbbb1cf8b14060cbc01488ebed0123b55000bf0c150389a03` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-negative.json` | `42f50aa1d5aa4d123c7a6ae57c7043e92df1d48436bdba6f3cd47595a8a8c8e3` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-map-iteration-positive.json` | `12287542325a1e49cd045817873cbdd2591f88ee4580fd1b05d2893b2355f747` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-negative.json` | `b7873f6cadd5b9a8c4c70313d5225e0fe47854b9f5d9a482437d9bb45931203d` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-nested-access-path-positive.json` | `ce85e61d928b0ff20b021cc1dcf2f5573bb7b116bed858a3cd9c7601cf41b8ef` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-negative.json` | `6c196a6b663badbf569ce4920161aea2e42a30f5510348bda473e945404b6fde` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-recursive-carry-positive.json` | `4fd4873d499c2e23322c6b7e7d21b1ac557b5811b945b2883ff99ddf28f857d1` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-negative.json` | `86f8e77df11722860ece5a54603d1a3c0e4f63a54c931fc93294b8e3b7e820d9` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-positive.json` | `2c81b6a77552b473fc61bd23a19fe1e8192b4fe7f5f7d65bf5b5d91125cb590b` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-negative.json` | `29cfe7efae5f7967773880d172b6da3d5d6af9633c2975957fbac6000b57cf36` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-positive.json` | `92f758581219c3a6cc067f8e048120d23b14aa72e09f8f976e7aeb91d872b6ab` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-negative.json` | `e8e93163f6d4b86e1a018d059d55c72af78c2a587f1876147d73ade134941d53` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-positive.json` | `90756861ecce5a7e358111963334d98c302b9c69a487e5437cf67f28daa05044` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-negative.json` | `bc3cfc5e1fc5bdfbd8084d2958d661f3d89d608b8d3462305017fc008fcbdaf9` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-positive.json` | `5ec15abfea73dd8d0692833e3091900decb3171ac3f9ea8fbd76be24f830833d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-negative.json` | `3881f1632577175c6cffe9f34e58ebf3f7e1a947989718551a8ea9d2fbbbdefd` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-positive.json` | `cbed5fc0a3f8dd57864ecbe10f8a8ba5ec1ba8e9a35498eed45c5fc78bf8618c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-negative.json` | `8fe8e88ea07f3a7e88048fa8035d345a869a78c9cedd5f610aef6f7e2ef4f733` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-positive.json` | `cb1c745e10a31aa60108df38a9dca96d3f04e80fdfc43aa89a3b64ff854916f1` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-negative.json` | `71bd635c5491c12a4e52efb5bb3b058e48b197119354a848bd47fa09444cf0d5` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-positive.json` | `5160e0fdc7f34ad01ae319e4a7ac15b5a8beb5f33d00464741e2de357d3cd020` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-negative.json` | `5204d1b76284ed9c5ee868ad7ac486ce796b2f52b685c29105e80e221b5adc2d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-positive.json` | `28f47ee0f6006a9b213bc2bd3998b6fc8f93b1f4d370f789bca1998aa063edaf` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-negative.json` | `cdeef50b17c86cd775cf523c80b6d860506c5a7090d652a7f631be6efdfe63a9` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-positive.json` | `58a461e475a6780b15f50ea135e0ecd12346d0dc90dd4c3a26596c36436feb49` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-negative.json` | `213fc24ec00f2b7def0f8cf6913e8e8f39e6faf22fca7a8e98cef47e55d3248d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-positive.json` | `620ca3123d81470cfb2de5db0b23edc161774be0821266740c9e2ce5a28fa063` |
