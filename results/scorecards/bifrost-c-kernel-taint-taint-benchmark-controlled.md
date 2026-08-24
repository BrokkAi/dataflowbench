# Scorecard `bifrost-c-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-c-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-c-kernel.json` (`sha256:a3f0b31859ec2a935b0b9a3fa31f3a50004af6dae7e1f721deef0bdb3aab9423`, normalized `sha256:a3f0b31859ec2a935b0b9a3fa31f3a50004af6dae7e1f721deef0bdb3aab9423`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `c`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 28, `unsupported` 0, `runner-error` 0, total 30. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 1 | 12 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `4e064115e2aba422c8586b738d7eb657b312ede7cdb5ebebcbc3a38b582f55ec` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `eac5c7db65fbbf5b6032500ce2b388eaa2653f366cd7dbd29144e1c63898f891` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-negative.json` | `4177c5773ca89003c85ddc9099546b237fa1ecd55087548e3b0028f21c046037` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-positive.json` | `abe03708befd29913a799ecc7c4beff2a794e869e4fc187c1d4b6fa3ea196613` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-negative.json` | `d904d24bfb0360c4ef959d20f7eeeb85eb0b0d3a8e6b6d252142229f42366d13` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-positive.json` | `1caf13fb87048ece609055a6dba6e601d64ef4aaef5b7f7a362219385d99ecf3` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-negative.json` | `0521a4060744c468289c56089f0257b4dae0f582ff465421def8a252b0c52b29` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-positive.json` | `eb7a0d8e59674ddc56fe74c4166440aa9663d6844ba31fd0c6a6b84b063e69f9` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-negative.json` | `dc35afafae6a973d98efc838aa6d74972ee32dbe96f969b8743b0ba4aaf44ba7` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-positive.json` | `bdf879356e578ee2891c97d209a6aa144b5da59c3301c594f4cb5863de881106` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-negative.json` | `61ef0bdacec9815d6fd65719378c56455c38cda0b9ecec115a6b68d9fe373114` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-positive.json` | `05c07dec0f19c0d4cb0ccd36f0591d83c65eba1a461b320aad49f51537f41079` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-negative.json` | `51b151c1be37399f9a261f0d9c3d77533c26f08f3b911556436babc9d90adc51` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-positive.json` | `bd8468b2fe4bf9da353487504bc834221defd76d81709975ec09a2977016de2a` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `b1d59b798b3a0635fcc06a7a7ecd5c50b2b56bc587fa49afe2c1313328e1b0c3` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `ec5f9f32ceaed3f4e5079e44b3ba8d598aaf87a9dfaa5f225ab05b8bb2ff5750` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-negative.json` | `d82d9972c0a3443af64a7ce7a80e3e6b61d80c9fc57205def29ac92e8e4a4797` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-positive.json` | `89789c985865842594ad2b675141666d009270d3b153bb42d310697c57248f38` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `9d4366b0846f5b34eabd81f9a181e9e99899c5eb80ccda468554705f0731efef` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `3f92d4561239ed917b93c264817a70295ff4ded0254f9e7f16fa0914e1f3c88b` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-negative.json` | `0c98bddeb9b1a69a788a885efb7bd0e9258300fcae36cd4f33b2b21e605b9974` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-positive.json` | `2974e695a3e7864ffe87985e36ed3cba6b4ef11b2ed99fb7c46b16b2542edc9c` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-negative.json` | `0b0a01ec19d67a3b9909847092b5824f15c7753c1b6e7b6c5bd392a2eabb3718` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-positive.json` | `891cc1b35605b3abcd158c6d6059ae2263cc3a5c5f84950df42c01ed6684dae7` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `81065bff00adb556606a966df515d5e5372e0c5a132149de8036be83796ac763` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `21f9ce19ac4815c561eb379f4b15884c0bf0f809f3c22af2fe7241f0b6f80c7a` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `edc0271c6ef7d818f6353343561e7e47d7ff60b5907ad80d46ff42053a82eb73` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `32bbbcaee46242314713d3e2d8ef9a07c6047fea62121cc5a71986ccca56e97d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-negative.json` | `7604d246f9b64425e2d5629b836f3e982c37ce96958882dd2d20c35fb3a4932a` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-positive.json` | `dc3651ddb294fe638ba89c5dfcbfed6ceef6b8bd2caa43713b21d76c4cfad4f8` |

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
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-error-code-return-positive.json` | `b7bf3fce78f4e50580acbcb04e951fbf8d2e7ed49961d24b0af92ecfc3f393ac` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-goto-cleanup-positive.json` | `fe0d5f15e48b582bb28b62718c13265e0f9e9971c4c759a40589b3d2704ac2b2` |
