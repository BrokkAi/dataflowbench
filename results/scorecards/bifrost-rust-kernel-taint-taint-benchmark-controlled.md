# Scorecard `bifrost-rust-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-rust-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-rust-kernel.json` (`sha256:c702764b78c0edb14a90a7ccc54c3247d85a9f41a1e84e564442b7507b4b7def`, normalized `sha256:c702764b78c0edb14a90a7ccc54c3247d85a9f41a1e84e564442b7507b4b7def`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 20, `unsupported` 0, `runner-error` 8, total 30. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 0 | 8 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 1 | 12 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 0 | 4 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `ebeb91727bb6030c899768d4bada6475482129d3a2472cb262f295543db67298` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `fcc65813080dc46e42200520f6e12daa318242934625320c7854ed51bb6cec19` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `8b468de2693151f40bc3dbc2bd936d2cf6d00ddb14a3a5c74866cf1d09082b38` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `60f6ab016563fbda49996596c140b7dce6012eeed8bf0367eda4a68bb71b775c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-negative.json` | `51e4f8a4b0b85336c10c5d714c99a5fe6a17d803ef1758d3aaf605ad907ded5d` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-positive.json` | `85dc5109af2631bfe8958b7dd4a73a1940050428d7312dfc34b6d9ecdff17af3` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-negative.json` | `16a9770650c858d134a820031ef7f748fa9cebc6190c449b016033f6bc9b4907` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-positive.json` | `16a9770650c858d134a820031ef7f748fa9cebc6190c449b016033f6bc9b4907` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `7e90671d511c6b2ebd7ae1a00a54d840fa21050a8114630dec3b273054053f20` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `9008009d92bb7fe697d3ad0d0b29a2044887521bcf05c553721834eb34cca218` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-negative.json` | `a659158d7949db893b57d326bb8220af7b1d3ea275b21ce675c8cf6a4ecdbb99` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-positive.json` | `bfcc1834dba9126719b6a4c7cec26e5310ede66ca8ac93d1ff49e1f0b2644454` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-negative.json` | `e62ebdbbe5c7427abc25f7455fe902aea708626c4cdf5ff982e4da16ab4bb54a` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-positive.json` | `7055fb7b58adc708bed8f3f309aa32dd27e99d6e55d116b81a4930b83adb2d41` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `53e093a233e5a94e43a3531d53cc551e45997c0c6d3a01c1fa19f072d6f27f85` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `1b06f93d4485e403ada06a42bbc2ae2c7ad08594923724b9e8c12c204193548c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `8c969200ffd8824ae3f2757b177b6e9c47a549578636c44eaa7cbe750f500780` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `5172487937fb4cc116396617401a3132ec6868c8df117f31812f0e5496c28253` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `d163cf5a77aa557784a2d75a7f21a582f4d82836db9a981ed963590b29bb161d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `f4f8aea6fb643f3b204327f864f1c293c74b07c3001e0f4a37f8cc091863912e` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `0a80fff1fc92c31eadb84502750526d20f4c5e445a4abbeb9a4c8448e4b61e56` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `2702d4d5aa1180c6dd23b40b05b167bdb257ded83486bb577ceb2a1f2ddeea07` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `eda240208e3d04735e6fa58ff2f29ea967e69a12c7f8c8b3d9c58f3afdf5fd04` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `runner-error` | runner-error | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `a4236358223227ff498e72349c5d7fdc68dd019823c13b8a447ad6754880b298` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `ac4893efbc99840320d44a78338cb21d862701f871330a5f5114b5e043e40265` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `b7659e44ab57f3819d4261f87a4ac52063556fe5d672ae20bd0e0f7c9d8fe7aa` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `9cfe1b83b54a918a56a0748e1ac6f40c783a0fc5c3d5a9f57b185720876ea22d` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `9b70d8769487e7ee1c42aeab0d2b05043b6c84794df961d2874f88c95fee6b88` |
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
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-negative.json` | `ff37a84aefd5e6f1af6cbb037d849101e7936a9ac26b839a2c5f5293488e11d4` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-positive.json` | `d2d441982407e6b923ec92713c6409c1e033efd8f11482d1df45762351f66f4f` |
