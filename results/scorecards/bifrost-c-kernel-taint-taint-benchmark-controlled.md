# Scorecard `bifrost-c-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-c-kernel`: `bifrost` `bifrost 0.10.6` (build `18d09c57d1e5044dec49acac7635d3255ea8e89c`, adapter version `0.1.0`, configuration `345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-c-kernel.json` (`sha256:e334de9b8752daf1b0ed67bc8403232449c10805c4817be3975b2ca62643ba03`, normalized `sha256:e334de9b8752daf1b0ed67bc8403232449c10805c4817be3975b2ca62643ba03`). Generated from freeze manifest `reports/freeze.json` (`sha256:91b0008a546e6b782c1b790f174a71ce44e60039239797674eb49ebc6ac6c366`).

## Language `c`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 46, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 16 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 20 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 1 | 12 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `recursion` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `42b2516729565bbad4a923272efc07e9e0ad876422b2bb10f6fa1de659285e78` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `7a2d33e844b22306e1a08880aa13a27f291dbeaa57ccc8f3d33c09dccb1f80ca` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-negative.json` | `8245c50dbfa79dc302b196ef7a451babc31b33e2b9d211e54dd9def7acadfa2d` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-positive.json` | `820621c0630f4c34c4737f5c00e758cee3821c80c461155727264633aa150926` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-negative.json` | `61245597bc1132804fcdb7923a3c20962e70643ef92b5c2f410191f0c576a58c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-positive.json` | `90f3278de62f42e8b8082f3639b9098f1396d7a163f5b2575a33ccf12920a0d2` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-negative.json` | `ae084f97e185bf14d502357257ce1dbaefd4edcd81b922dfec9c23425d3ad3d1` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-positive.json` | `a2f4f7ad46724c64e0425bbd28d331e225b9cc275af090ce996105b75b7bdf4a` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-negative.json` | `717b0f6bac88f6219de6cb9d9c8e0d4fefcb2eb8ec698e581112ddd72acca04b` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-positive.json` | `eca05cc870f15827a0cb2fe8ab03f868a1c6c3ac83b9d81a94fcd7eeec0b84a0` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-negative.json` | `2958e5b71249501c34c809dcd58c8cb7e3deeb0d6dfc2b5343f8150c1c08b802` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-positive.json` | `a3a685cbafa96a6a68af6364987c685fdd6d5b9ef95ac7757e71a1b5b0ad1542` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-negative.json` | `ff1fdae5aa79194545f8cc2fb5e1cbfc89f8375330e589d343218aa99c3fb33f` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-positive.json` | `c112217036c9414d27ffd1bea97e73d815d2935a10b86610ce4466d79a06e988` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-negative.json` | `f9e54786d579c45af5dadae26034cab13e678a5030ea776fce8a8104695c6241` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-positive.json` | `c187e3b2ace7b08abc37d453b5b65be8507afdc4da46a18b1b39db1b3f2d5e40` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-negative.json` | `aa4457536bf88c7f8d196ff81c5c731353ad106512cefb2889427c8c3f91a7f6` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-positive.json` | `0e929579119452cd8f38e30c92cbf16d47d115ce37bd1eddae613a09e9da95d6` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-negative.json` | `8973dcb7ff59b9e727cf418013660bb065a5da63ddfcdf64f4709761076b912f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-positive.json` | `8973dcb7ff59b9e727cf418013660bb065a5da63ddfcdf64f4709761076b912f` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-negative.json` | `60572e88945a913e1e13766f0de9037e385e959c93b3089d3d87cdd199b602fc` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-positive.json` | `5afe528787060fcadc8c9f8588540faff16367befb55ead4f958e558d2bee172` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-negative.json` | `08918f01bf7ccfde4bcac3024812a2d94c8ae1c45bc07af4644a03cc9c97de7b` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-positive.json` | `5e1a717e848658a2643a3c715651e348c89c420e4221db3e5883a94ace200dd4` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-negative.json` | `b95e179aa1044b1bfa8f47e8acc94d00dfee5ce6c1ff1406a75278692e2c76b6` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-positive.json` | `095659a27d5ee7559c757e999b0dc66086329ebe3dd9d1a66a7ee274a68b6d98` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-negative.json` | `e22bc4f3e95826864e147ce1258d08924878f27832e6265fee4d0e399a726a30` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-positive.json` | `a8aa67787d651546647cbad8e9924ed062a0b2af840bf3c173141a8a4e2532b3` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-negative.json` | `f2adb9189cb9befb6799f25eae327d0975747f88d4e04292e966bc5b0dab4e34` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-positive.json` | `e2857d81426e67f9f408cb44446e82ffa3ea760a9f1e483a7fd0fd8baa067621` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-negative.json` | `a555e4280537e17bde18ce71076072314da1611f17d73e5d6e2ff202acc2c6cf` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-positive.json` | `ac0ebd82b8ba267e3f2a6cf2ada7d6c88382ea60dcaef31312d0c22e9c75f3d6` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `df42157b483b512e9a317f9c1b6918a14bfe857ee35da8decf653bbff707681d` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `e01fda2ad42c81ce7b2c0886bb6c77f7800da3f4ec95cce655c1715795c10bc1` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-negative.json` | `5050b2278dd4c5ba0e5dd0d2fc2f5842babd07cff4c6bb280b2efb6f8f7b1b79` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-positive.json` | `adc72426db322d3ce2517a808422e1d3e6a1d30654b32f2b797c6391543dd472` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `d403186acb225ebaa648d1e98146ebab83dab3a398a4bfd99a042a6b6ed610f0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `20b41f135d23eb05023530a36bceca88263def6fb7d23502618b269d0f4c5966` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-negative.json` | `e2e9e9b3e6bb3219705f14b93de48b3d5008151ce8ee1f2167f4f0fa443883b4` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-positive.json` | `83549c95eaf6c3525fbf0c433309c7456785ff20aa4ca9019de0f9f4ed25bead` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-negative.json` | `64760cc9c8e8516cabb143ef40b26809befe6d808662275808adddb6c841ab31` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-positive.json` | `b53dfbabaa19d239534d61548d31617c9566e8fa1db3328d77d696e5fb1aa070` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `3b06a75d5b3864660cb039aa9c7f798be1f676e06a1a88fc0faa25648f8fb04e` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `5df1dffe9bea0fc272f5e3d84628c7fc9cd72d938fc1767710fae501aa6465c2` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `91fee3a1eb45eda5dffacb856e2180550dff0d7da800bcdc87925829e2ebb2f5` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `86857e5a6052037f45c9ff455c5cb2195411d8f3d660043e10bfb97b86ebb4ca` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-negative.json` | `cc7150d2e859ff986a6a60565b05aef1a81279216ffa2be33a7ded59bd1dbaad` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-positive.json` | `a6419ac31d43e79620c684b2200a2539d209e9e477bd5e7d5495da9108e340e7` |

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-error-code-return-positive.json` | `25173eb71f3e5e15746eaecc95043b2d9867d3613dcf4e2411cd782491f08e8f` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-goto-cleanup-positive.json` | `3d8de63108fe8cb360497a268081a8bbd5b2248464d920bd75a9a8fb472ad848` |
