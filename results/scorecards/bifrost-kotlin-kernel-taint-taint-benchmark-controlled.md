# Scorecard `bifrost-kotlin-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-kotlin-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `26c37db9bdfc1d848a47052d3753e1d29040f004874290641cb6b706b3a03d61`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-kotlin-kernel.json` (`sha256:29eab6134dbd0676e36db4656daa588fd6bf2be3b4dc42548f9711ab00b117df`, normalized `sha256:29eab6134dbd0676e36db4656daa588fd6bf2be3b4dc42548f9711ab00b117df`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `kotlin`, tier `core`

Outcome coverage: `reached` 12, `not-reached` 10, `inconclusive` 10, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 6 | 1 | 2 | 5 | 2 | 0 | 0 | 85.7% | 28.6% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 100.0% | 66.7% |

Macro-average over semantic dimensions: TPR 97.1%, FPR 25.7%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-kotlin-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-alias-propagation-negative.json` | `a9f32f2a8c88b8e2bb4604fbf991999ed1ed2756fac51624b6c5c6d93327094d` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-kotlin-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-alias-propagation-positive.json` | `36bc87a80119ebdc98f4f3826126ed91bfb0e1f6b0427d686a596cd584c6de9b` |
| `dfb-template-argument-position-separation` | `dfb-taint-kotlin-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-argument-position-negative.json` | `76e2ce243021c9fdbffc72c152578209a88479f26c0d9fad1dee89d8c3812657` |
| `dfb-template-argument-position-separation` | `dfb-taint-kotlin-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-argument-position-positive.json` | `a46364d5677eae1c37ed5e710789a28ee88276f73e0685c7c29f63dbdf40f3c7` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-kotlin-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-expression-negative.json` | `0922985621b2d680cf9c5808ceced0154a83f8841e4e78bb9904a566f021859a` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-kotlin-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-expression-positive.json` | `b66bc174f49de56cdb5cffc2eb56cb91cd9fd0f2537c2eefe91f3aa8cdf259ad` |
| `dfb-template-array-element-separation` | `dfb-taint-kotlin-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-array-element-negative.json` | `0f7e29b89196d0a69b6c1bce7ae6fb29d6d8af22b44580a399a3d0e43ebbc52a` |
| `dfb-template-array-element-separation` | `dfb-taint-kotlin-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-array-element-positive.json` | `c44cb6294e3f88f8585fddeba36dde9bf094cb1e0dd881add1a388e91ed2bf5a` |
| `dfb-template-branch-join` | `dfb-taint-kotlin-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-branch-join-negative.json` | `4f03a4a4441987b4593b5fbd2305553ce6b96656deff8cd106531de9ff02b5f8` |
| `dfb-template-branch-join` | `dfb-taint-kotlin-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-branch-join-positive.json` | `2651399b7fbf00ffab74462d7bfdd70a6e66e49624f16cafb29840351da4298d` |
| `dfb-template-call-context-separation` | `dfb-taint-kotlin-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-call-context-negative.json` | `b4e958cb1b0ba8fa9eb37d1f7421caf0e5722e81aaf2a4319468f12300f1bb6d` |
| `dfb-template-call-context-separation` | `dfb-taint-kotlin-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-call-context-positive.json` | `a98f56944edc791b6df28d26dc92896dd68561f6425513bb2a8e9f91b719a7f0` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-direct-negative.json` | `495ac6621f19ac000cadc09b4afdf9030ab56533f0361ee89ff8f8d73330257a` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-direct-positive.json` | `5827f76fefa31e72dec47d04e65c7ee6d550a6c819fc84ca93db0cd811b968d0` |
| `dfb-template-exception-catch` | `dfb-taint-kotlin-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-exception-catch-negative.json` | `5b6bbfda1f1363f2f03d0e8e712dbf59ae6d03d8c7be3cf4eed1f58c292c3607` |
| `dfb-template-exception-catch` | `dfb-taint-kotlin-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-exception-catch-positive.json` | `b867b75142f530734fdde230e16ac8a2b4749ffe02aa3a44925d6eca31c2a436` |
| `dfb-template-infeasible-branch` | `dfb-taint-kotlin-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-infeasible-branch-negative.json` | `ce33a13698a613aacb8e141e60b33bddf99655bd41f340d560376213adf1f2a5` |
| `dfb-template-infeasible-branch` | `dfb-taint-kotlin-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-infeasible-branch-positive.json` | `ae71b5fc45e8cbe89efc119510e52d827320b466840202304b1ea5ec9bb9dbff` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-kotlin-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-local-chain-negative.json` | `cbcf03a13c5e6101ee90e655fd88b4b79f1e53f3b700fd7c19223ed6e1419a01` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-kotlin-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-local-chain-positive.json` | `851cdcf44ce48a78c365bbeb8dcec2527b0b856abb834f8b622fe01a3144c5c9` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-kotlin-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-local-overwrite-negative.json` | `232c2d174b79056728e7984065cfdb0fa80cb784dcb31a4d9851e10a98170878` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-kotlin-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-local-overwrite-positive.json` | `6127a3b9b086e4db21a4b0aad528b0fffb210d58210c388ddeb5ad2516163237` |
| `dfb-template-loop-carried-kill` | `dfb-taint-kotlin-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-loop-carried-negative.json` | `13caf4bbc8826ec25a721b7572e942e71955f8eb4263021778fcb4d593b6aaaf` |
| `dfb-template-loop-carried-kill` | `dfb-taint-kotlin-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-loop-carried-positive.json` | `4f54865acee780308d6e90bc45f80533385854528f30af99a23d40b2577abe02` |
| `dfb-template-object-separation` | `dfb-taint-kotlin-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-object-separation-negative.json` | `20172899fe3d055d2dc11e4b348e610f86d7662c71a3427db9f7522299341313` |
| `dfb-template-object-separation` | `dfb-taint-kotlin-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-object-separation-positive.json` | `f10d54eccd333e9f09b7a91024335917987c46b0d624c1285562034530af0234` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-kotlin-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-return-relay-one-hop-negative.json` | `34c8fde708248fc2ba1d8f819e497a664d77d4d6b48db52d222596c07b9a5922` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-kotlin-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-return-relay-one-hop-positive.json` | `de5a091cfbc659b2228bd9957722f74c7c0556da4f001c9f9953f77623654a38` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-kotlin-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-return-relay-two-hop-negative.json` | `ab5f95a286bd248bfb49327623b3666f2b12fa4b8ac215fbce1660433448f4c5` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-kotlin-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-return-relay-two-hop-positive.json` | `10d6b1a0a5380d10bcbec376323e2196b23c4c5abebc6cd9376b69dd9d253616` |
| `dfb-template-same-object-field-separation` | `dfb-taint-kotlin-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-same-object-field-negative.json` | `6e782c68b6547405de0f7f071139c9377bf91b7ed5e5b23fd21f362803447708` |
| `dfb-template-same-object-field-separation` | `dfb-taint-kotlin-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-kotlin-kernel/dfb-taint-kotlin-same-object-field-positive.json` | `e503ac4d90a73236cb9808c0d2e2dafd3f47f9a7fe69c74a64e3e41ebedcf0ea` |
