# Scorecard `codeql-rust-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-rust-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `9416cc90fab7a0f6200bb8063304db65de24b7fd96185d237bb0f34d4c049502`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-rust-kernel.json` (`sha256:8415b80fbe4b86e528ce1a065fb5c5924421e4e027cd48f6f137e1655780b18d`, normalized `sha256:8415b80fbe4b86e528ce1a065fb5c5924421e4e027cd48f6f137e1655780b18d`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 21, `not-reached` 33, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 2 | 0 | 5 | 0 | 0 | 0 | 60.0% | 0.0% |
| `dynamic-dispatch` | 0 | 5 | 0 | 5 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 5 | 3 | 1 | 7 | 0 | 0 | 0 | 62.5% | 12.5% |
| `interprocedural-flow` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 6 | 0 | 0 | 0 | 100.0% | 14.3% |
| `object-sensitivity` | 3 | 3 | 0 | 6 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 71.4%, FPR 10.4%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-negative.sarif.json` | `869d90502abd3d0a27fbdfd6150937d89afefc7bf33f757dae115820bbe1e458` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-positive.sarif.json` | `23fe04f69bb2c7c3fba65b0ec227f5ead3ff4f1505745c0fd699249c97774320` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-negative.sarif.json` | `7fd9badfc01f87b3147e2d0bdf93a55ecc843d1a96c7a3e374119511323d6a3b` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-positive.sarif.json` | `ecbaef2f9adfbd88ce07519682dea2454d56845091097e32517bb82b619d2663` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-negative.sarif.json` | `7c0e6d341c4fd357c2533a56f9f478d4ddfbc1e7c82ab2e83368b4647bd1be13` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-positive.sarif.json` | `634a45ae3431e626f146a728f407fec862f001b7b298c5d1782c77fde7157791` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-negative.sarif.json` | `c1736b9ed32158e019b3272346c98a0c060af7a0e29d3b45f820698451c9f48d` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-positive.sarif.json` | `6b7bdac592d454565962479952f4762fdc474b6639636aa56b6177acdb37b900` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-negative.sarif.json` | `35ea88d28c6fc90a80152fd8ae04e182965e61d3344d1bde07652d10bce1beae` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-positive.sarif.json` | `5507f725387ba5fab24f95899b06a7ad3bfd0b75e13ebe358d57cdb555da3de5` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-negative.sarif.json` | `629dd24c5b31efdfe414199bb6dd6bc0ed7e3378647af8278e0f4f9babd01220` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-positive.sarif.json` | `656cb223c51dc359ea110e302f32b5b381185d6942086cdcfa85249a0178cfd4` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.sarif.json` | `6345578424e1d454ca95a9897dc1d65abc972e9dcaf6176e220fa2daf1c9f2b0` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.sarif.json` | `46944b8151388bed6fc25a84db76ad3d86ed20e8b315121bc1c2481b5b2df251` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-negative.sarif.json` | `b79e74aa5f54e8f5dc9a1519823f4daa21f0d6de89d4367e45c575787ce6be86` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-positive.sarif.json` | `a0c87254751ef2f8c09e8a488d84c4044b51709146fd61958caf51727c69acc0` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-negative.sarif.json` | `59cda31b7b09ab829078d8bb892098e87f6e6936529f31959faf40c4cee2acb2` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-positive.sarif.json` | `c39898958bda13d5fb8dbbcd8b5be6dd3b29b798cc8795a918ada91e06810b1b` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-negative.sarif.json` | `e3555fbcaa5ffc9a563608d33fc8c733eccc52eae82852bcc00b4dc1995e4566` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-positive.sarif.json` | `d675b10c87752b4f800e67a373e29d3d742e587a94e77c0df8b4f4691a358ddc` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.sarif.json` | `f1b078671bf710d383ed8915e79532f1906112405a299e97f8e632231ecf3aa5` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.sarif.json` | `22199453416aca78dba7a9945f5face67e9d34eb0bab4d181f48359c46f21fe4` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.sarif.json` | `7493419229cec360be266de33615e2004366e969dc2832f64e445a3a71f3f368` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.sarif.json` | `f8ffc2efff895efd44a4b0929202d3a7a226a66ea0ecc4cd08d89e9d1624b683` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-negative.sarif.json` | `bea1dbc4c414177bea5c8f6e07b7af7fca7b614a301ab0fdccc85681eafdd746` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-positive.sarif.json` | `06658cf8ef86d70759308d9b125aee6fec9459fae26ef00cd46818c3acb3a40d` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-negative.sarif.json` | `7ebcb676e933d2e0a1ecfa822cfa7342fe5225eb00de39ef7618692fb0c5d413` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-positive.sarif.json` | `94ebc5efbf24f4fcabd8610870c8da3c5f278658befdc3d5414926aa1f1aeb17` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-negative.sarif.json` | `84a6e2fbe3cc22d8115a6dafc7676a0f355e4fc522a800f47169c0b4e10dbd17` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-positive.sarif.json` | `2e1d886630cd7adf8f702363c52601088ee940faec39f6fb3113fe09331d4b4a` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-negative.sarif.json` | `6131e69da2df5367815ace4d2b8a1671257833054ed3ac6bf296e41f26575138` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-positive.sarif.json` | `51917bd1aecf68c5708696978e3a9ae5b3a5f75e157ba8015a20183c2669561f` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-negative.sarif.json` | `3a227578a67459339eddc662a79dbff8a995c9f53052b408c5d67bb67ad02cec` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-positive.sarif.json` | `e3d090217ada1c2ed46faef9c2a58bc5dfad95b560186cbc77bee71fcbae2ded` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-negative.sarif.json` | `62e42fa88762dc3ca34d4ec7ea4a18a8ce8783fd21e68677699f4729c8b22bde` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-positive.sarif.json` | `6cbc57a61448d6006dd19fd635e3a15690e579b1de2188615e4159d4e900dde7` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-negative.sarif.json` | `11a6d851fd06fe0a3697f42698d1ec6494d6b3dc02f30f42ff8d35ce891c5e92` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-positive.sarif.json` | `9a120abdc763c6a71ffb9edcea34e57825b136212916972ec8830e8b37f6a91b` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-negative.sarif.json` | `d3ea74d7db63b0b5086f4a72f98024ec67f86d5e216c9569ba9612272abb50cf` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-positive.sarif.json` | `bb5f0839e946e3c9d90d995c98016d9c9edd1574972f5f4f17b3b63348d3bf32` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-negative.sarif.json` | `0b477e4c73c6acde7138bf988562e8b7ac166bceb0fe9c510e4c0d0a87f14442` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-positive.sarif.json` | `d97c60293f8e3f5f226dd5a26320c88deedd03eb3a1d23e28b63f688065c6770` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-negative.sarif.json` | `c7e54816366a0837409f7b3b9336ca7bf364beb42654bfd36c181ac8af5226c8` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-positive.sarif.json` | `4f4372d81a3a7c212694612a9b78d1195e822be75fb67eb32f30d1d5906d0a54` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-negative.sarif.json` | `207c3b35e3261787e11c32833b4ff2f0832084acbafb5e7cb38c14084309df49` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-positive.sarif.json` | `e40e9a560e050af58edc7f70155cd7dea0ca9679dfbb5c5e448b573c144ed635` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-negative.sarif.json` | `df1d66df7abbc05ef00570ed6577efa9c6a20bbdfa96f1b8f68d303c15665627` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-positive.sarif.json` | `dde352a337b283f82f2a0a80a317fae8e7477b7ae8c939019ef2bde9a886cfc0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.sarif.json` | `825aaec3c46c6dead54b26501d5c18952b604676f17b6cdb9cb5e7807924e33d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.sarif.json` | `01218d876e914b237e14738e8d02ff9291731cbf898307ce5404a722c44c3d1b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.sarif.json` | `7773b9452ab9cd6493a074625270e18b54784f72d38c1471cdbf1deed171dbf2` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.sarif.json` | `00b09fea03b68c40f3d63a3b32dc8ff0f96bd4913d761fb16975f863c3602c78` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-negative.sarif.json` | `5be5abdafab1ca38c851487bfd5d144dc95e05401347dd5d5046d437457aecc2` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-positive.sarif.json` | `157987a10d3139c2ea7c1daa9ac1b07d0c93994cfafd434343e2688ee9ae7275` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 2, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 0.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-negative.sarif.json` | `a4a48fce03b3b5e36c04a3fc457ccdf373d3a181ed0a6823a8dc09c33c32883e` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-positive.sarif.json` | `1f3d69d5a46d94146e925f1f7641a287dd0907d0704a7372025fce032a012154` |
