# Scorecard `codeql-java-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-java-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `32ea52dcef0e7cc70ea20c2ad81fcf23a47fb1f8db698ec277c30617174ca659`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-kernel.json` (`sha256:bea06d23735ce2450cd7fd38ea32b1fcd5d718e6222da10af7246efdf15380e4`, normalized `sha256:bea06d23735ce2450cd7fd38ea32b1fcd5d718e6222da10af7246efdf15380e4`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-negative.sarif.json` | `7f95546112640c8fc3a7c160fc027c674afb572b3d6098bd3e4cd4510e825d3a` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-positive.sarif.json` | `7a90c82fa14a738fe2726f8dcaa6dd8f36a2575e74763edb0bea189e83fe0e05` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-argument-position-negative.sarif.json` | `f51c482bb4616a7f9f57da973f7b829eea82819c979de62401873ec8e5a849c1` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-argument-position-positive.sarif.json` | `a4d1a13fc22f07b8a491d0e15bdccc1ef950283dfee9f9ce0d408dfa26378569` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-expression-negative.sarif.json` | `0eb04a452f909ca59e4e4ad3ad0691b025eca40ff7e75049a0ea75e244e65bd4` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-expression-positive.sarif.json` | `4f8571b6f6d68a7d93c5a3a1d92aef2aee68357894b421830212bc5a71201dbf` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-array-element-negative.sarif.json` | `960fe79112c169b942e57fb6a6a1310313112b3ada4330f58653b773ca557c06` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-array-element-positive.sarif.json` | `45ae95291e3cccb563b879553a6623ae3e4ebc99b6b9a882c500a4fe71e29fcd` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-branch-join-negative.sarif.json` | `4e6e205c670869fdd6a4c02b6a363f305c3e3129f6656f68883d3ed994a9ea25` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-branch-join-positive.sarif.json` | `e0cea5ece69bd3dfd7f77d8310ed4955a5c557a460e51ea2cf98fb2fcf789359` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-call-context-negative.sarif.json` | `33ac7588b00744f04468e4bf1e454b8eb093dad7a18e9f06388b3f9ff5970906` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-call-context-positive.sarif.json` | `de82f3b78f9e6a634dcb158ef76fb9a8b6a4405dea7a103f9ae73d07c0f7040c` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-negative.sarif.json` | `7e188e6c93652ffed5662e5c8e26a1f2859c7ed8c7301523737102a889de0686` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-positive.sarif.json` | `7b29249e4a6e27f1b705e44cf899c5f1c2d0f4e117a643a516c530086a27d763` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-callback-registration-negative.sarif.json` | `2bdc7c4166600370f566b8b0fb4310e9e34f5924071496d8d91d3f6f56652f0b` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-callback-registration-positive.sarif.json` | `29ed6f71064a849dc2291661424158012340317495c7356847b1f31f5270f569` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-closure-capture-negative.sarif.json` | `f03393d77efde4039ca46e95c4fa989cd6663fe1eb89bf66d8cfef8ebb9f20c9` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-closure-capture-positive.sarif.json` | `2594403d6f9495738101e2c176318c237622c8a5f747c0c921d48d32486f6138` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-computed-property-negative.sarif.json` | `839d0f74d46eef16c06d25d793a996d7f85aee4c170dd7bf2d74d54a18ea9c1e` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-computed-property-positive.sarif.json` | `531b53cf4d19b494fbf6b43cd23f487d57cc4d4589335b9358b7394d51c6e980` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-negative.sarif.json` | `ea8be08412982f365d2a73515352182efcf6b15094686d7a4cfb0fd457ae413e` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-positive.sarif.json` | `3b64aac80c3ef98d1fec56c8e202ac8a32274acb0108f32882c11d97ee88c141` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-negative.sarif.json` | `97ce2ca09ab3f2c726ff7670e3af39d360357514dc1244a36768f0f0fbffc70a` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-positive.sarif.json` | `1fe403da49ff1b599cd12ea6298340b172b6bff368c135b519c3aabfbc060390` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-negative.sarif.json` | `d211123a7281c0eabf262d791bedc0079870c1bc8aad2a89b84ff6fe203745a1` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-positive.sarif.json` | `ba513848e9d05f4a1e1a50f8ee970c058da5b7d24bf868d3e873f12a55ff0a37` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-element-object-negative.sarif.json` | `de5c452597699ef3347509b7b4adf2490ff53b5b6bbf8dd05ea50e88d231fa29` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-element-object-positive.sarif.json` | `7f58a7da936b5660e1b777bf1961b6b8131ff28ce6bca51b7a43fd8a13ceb9dd` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-function-field-negative.sarif.json` | `8ae9e8aa60a91f76d7a0328667a1598660b86121815d895c3c0cd05ffd0873f4` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-function-field-positive.sarif.json` | `0dcd55de9de03c28316fb9a23f596dadfc3a3f612179f69c9d1645f5531f15d4` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-map-iteration-negative.sarif.json` | `5a47614b70845af939b5b4234625e6857b6e806ef346fd14fb60c795b0d2fa8a` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-map-iteration-positive.sarif.json` | `053e6d58fc7fc0735c0ab4abfe23270d6b977a175169faded64f874480f903e0` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-nested-access-path-negative.sarif.json` | `4e2c5e17a1da8bca4b6f3dbab564b9be618978187f09083880c34bced1fcd2e2` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-nested-access-path-positive.sarif.json` | `88d06d27a7e861ca4df44c57666e06f2fcca4f287f2d17d80cdbee6dc850fd40` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-recursive-carry-negative.sarif.json` | `cfa85d7a2ee247a9d65aa13d857fb54d715cf279dd414efeb656b1913ea5db0f` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-recursive-carry-positive.sarif.json` | `48fb96e5b5415af900d29510ea462a92f1a5aea6fe7c44f6db717dd43c61fec6` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-negative.sarif.json` | `3594483b5eec89ec7b05511469ac4d1f1b5b40d5e59e6cbe1a1c49416cff5712` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-positive.sarif.json` | `eb00380214baddddf3f9e858c9c4d7becbcda870ae587d2dccb36b3423cd248b` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-direct-positive.sarif.json` | `616010427f9a56e25454fc77d99ee789c4ad2a377a16f06f01b9964380ffc146` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-explicit-negative.sarif.json` | `5b7b41c226cfaae53d673e3e4f05075e2b5afb705bac1bc244db48240a1b26bf` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-negative.sarif.json` | `a89946c826285a998790a198d7bb1b9eca93ba89daf604164374b7d415d7cccd` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-positive.sarif.json` | `b0e59bebb47aae047db2741e613a9d5ded28cd7cd8e1c071dfe0e998d11c375e` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-infeasible-branch-negative.sarif.json` | `99b6481e8dc5fb4b76e99d75e1b800d6af3ba0853315d77c60fad331cd019cbe` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-infeasible-branch-positive.sarif.json` | `8e6f62a6a7d628d8709a6866db366616fae98f0c543b8390763781496943d467` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-chain-negative.sarif.json` | `59d123b38614d1ff7be9c6f3dbb18c5886eb6613e71592cf366c15be9603e54f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-chain-positive.sarif.json` | `6e887bf286848a329d5c99bc32cb9906512423c4a08c250135058d845851c31b` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-overwrite-negative.sarif.json` | `c1360134eec53fd3b74c08498e80a14a6e521ae42b2929a9bb036e101613ff81` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-overwrite-positive.sarif.json` | `e819853ea1bf8e23cb91d25809614be6d8b2f39f77f0247c6cce24fee6320aaa` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-negative.sarif.json` | `ffb9c577b34db398f90e8245e41fe9007f2b37fad2923191c92342b0d719afcf` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-positive.sarif.json` | `010a7983e4d24f3fa73aeee395c8b620f8b5fbcdfbebc5fbfdd172da942d8cf6` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-object-separation-negative.sarif.json` | `b628439924c9e18e37e88fe86794be7167b5bc350b5bb1b1abd33833fa908025` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-object-separation-positive.sarif.json` | `86343a579b19b3dd50bc50ae461c2dc366511353ae0a6b46f71d6559d528e0b8` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-negative.sarif.json` | `ca5a8d5b3cf19af7fd5325e6373e7787f58aa1560aac73dd0ca066abfbe6f7fd` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-positive.sarif.json` | `58b53e301d36a0bd9c8b9aa213a4456ffdd20e4c3d92ff2a075f99271acc980f` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-negative.sarif.json` | `be4373becf5604505d66c8ceb81661ebd83a08215ae6fbd333ce483726fe9e74` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-positive.sarif.json` | `9f8e08b2702bfaad894e55ec06ebb3ea9b4798526a38217b558559338bd97208` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-same-object-field-negative.sarif.json` | `52ac882350f410929c8e5b69a8ed6157046063bdad84dd51f0cbac92e43ffb3c` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-same-object-field-positive.sarif.json` | `a83597d5e47224dd102d706fa357c54f953ae47999a0d172461c4b8224371181` |
