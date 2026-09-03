# Scorecard `codeql-java-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-java-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `2c0ca1f64427b38325baaf87a897fdc543ddd1e09346999c3be6f13e7e22226b`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-kernel.json` (`sha256:6a28544561053b71285c220fcef39bd3b73de724c4a5fca44d8b7f5db29af4a8`, normalized `sha256:6a28544561053b71285c220fcef39bd3b73de724c4a5fca44d8b7f5db29af4a8`). Generated from freeze manifest `reports/freeze.json` (`sha256:e3fbcae1eaf3f49192f7156616c4b2149893a8470e03ff445fcd1d5f984f9e5c`).

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-negative.sarif.json` | `87031556144a41d87368e108d28de26825b7b04ad55079f843c2cf17fe3486fd` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-positive.sarif.json` | `0c172ffe26e7e762254d799f14c150a4c6887603d10b70a92a8034ca833d9352` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-argument-position-negative.sarif.json` | `5d5a385217099faf8e82c6359ad958eca6530aab1d267aa7cdc59245fd8e6d6f` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-argument-position-positive.sarif.json` | `df719253fab48ab723f904f70d0baf0f585d9c2b4a627648cd462d5279d6f7eb` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-expression-negative.sarif.json` | `ce7765b1a54b43b8cf5ccb93686367a57c2fdced17344a44aeebaf400254ea73` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-expression-positive.sarif.json` | `e1dac28130341c03929a36940c14d7472aa037a48e768047de11d50cc9a788f9` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-array-element-negative.sarif.json` | `3ecbfd091ce0bf24e5a6e3e61a2af9635ab27e8b179bde5d47bc07e00283324d` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-array-element-positive.sarif.json` | `4594269366f61ff38760fac2afc074f7224a770bbfae02eae485a9ff498bc956` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-branch-join-negative.sarif.json` | `576f874ff7a0c9e439b2985d474269c265323b3743d49298e927f64291ccb536` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-branch-join-positive.sarif.json` | `7e8a71bbf3869435ecf876dcf5ba8d443c62b97c97b4e81948d78f04f5c9c6db` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-call-context-negative.sarif.json` | `d7af55f96ee5a0c18549ce0991ed55347b4ddcb4d3256868f0fa8e6fdf70b3ef` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-call-context-positive.sarif.json` | `7548f669b34b9951ec1277da13973e331165fc0e4bc0b1e17546d834ae5a4fbc` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-negative.sarif.json` | `8021797e52c4f213ceceea9a6c7597e894a58c5aa4e2845157270502c76d1868` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-positive.sarif.json` | `6c9815e625ad18c80549f1b26ce6298ef6728f88409f51809194c4efe229f0a9` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-callback-registration-negative.sarif.json` | `8472fa77348a4b03a9435a3b0f7117111df13c7a765987bea7c4045bbf7a9a9f` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-callback-registration-positive.sarif.json` | `6c5f6158e70bf8e5134a0e56931cd57ea47d086a06ff6566d8dbcc2df6b8091a` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-closure-capture-negative.sarif.json` | `e5ce10ed5f7b3212a7fff621c19bff91cc55a99f9461acd2d8e68545c14a82cc` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-closure-capture-positive.sarif.json` | `b3b33c7ab246bc2e89182ecb8f9f11274c322e5c0be8587b8a654a0423843708` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-computed-property-negative.sarif.json` | `ba50b4b9773b0f8d39123bae82d7a77b4efe60674426eb3a4f2ec8639041feab` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-computed-property-positive.sarif.json` | `231218fbed84fcab00df2afc453b0cc5f762c0da814a881560ac4e543b81ef8a` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-negative.sarif.json` | `e9b87152edc06093729c5f5285369dfb34f7e26f70acc0eeacb0e754c1bd4d47` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-positive.sarif.json` | `acb4cf726846661fbffe84f5640775856ee20368faf03f0f303c224897d61943` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-negative.sarif.json` | `9cddf5c511fe876eaa9f0a742c0a7756a9dec20fb9d0e67917f4d28565ebcfb6` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-positive.sarif.json` | `f30e15222ce0e36c51d6b5a2a3441569ca8f3f0a177a419750964b4575eab1d4` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-negative.sarif.json` | `f633009b42c372e93c1daa34321b9018db5c3fbeda872038d5c6a0e965075148` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-positive.sarif.json` | `bcbc94659c36cf3eb193d655327a2c4a555cb5610e07ce134400d2d289cd0d1a` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-element-object-negative.sarif.json` | `9332ef1baa29c78a8e31dd742b571533cbc9b6918f3dc6c5b73ec774da56d46b` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-element-object-positive.sarif.json` | `5f8504c1d41e33daa1fdc133df6f784261b64d4aead665218c6aa859ff1f358a` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-function-field-negative.sarif.json` | `8150d5250c267e6cda0e9b25fc2f50983b210bad424396bc64e45a2e9bbd6590` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-function-field-positive.sarif.json` | `3a3a9e71d372681739fa51532fdcdcf376bd68d08d0bfd8e7cae1dc554134b9d` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-map-iteration-negative.sarif.json` | `ee18a8394c7354bc1bfa37bae77d73477b149c081d160631d9fc1ea3e8d880fe` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-map-iteration-positive.sarif.json` | `a2f02a7e45ec49aee2c6444c94ac4476e7e2f9f5e4c5f3419486c7ea4a06d49d` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-nested-access-path-negative.sarif.json` | `0956fc7eedad98e23d9979db6be286a630cbc90e4e9d93d2996a5d8e8a6689fb` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-nested-access-path-positive.sarif.json` | `a5ba16e1b8607df2f62e80675dccc4f1747d606dacc9a7107ce43962579d4091` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-recursive-carry-negative.sarif.json` | `c53e427610c4f068d9592ecfe1118b17dfd96d1f65eee6eb3d3dac9b542f7bee` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-recursive-carry-positive.sarif.json` | `33ccc85df01a8418fb9f0cee97fe473f1dee0e8184565a34ca477043b53d3acf` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-negative.sarif.json` | `3fa088864202c6ea313ddce5b1210ac33cf542f9fc794f6c9807f1fde84ecac8` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-positive.sarif.json` | `c79d59f3e1bec48730b3e45f2c725a6c6ddd8fd1cf547f44308d05ce5f48d116` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-direct-positive.sarif.json` | `f7f82da685c8723378ffe8e1f2298b7194fc320a9ea186db13be3eef2b95d589` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-explicit-negative.sarif.json` | `e3ac24e8cea9ece5851e989fffabb470f568f49d112fa377b8ef137403353973` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-negative.sarif.json` | `18d9351b2214a7e11ad344eeb7acaaea3b615865808f92496404d478345ec2d6` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-positive.sarif.json` | `8f975f132d42287241f066b990b93e40cefc19eb257c9d22c5d393548f67daee` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-infeasible-branch-negative.sarif.json` | `c230eb4f50c41e43a7b9c3317f0aa1a63ab103454bd14d32f6326b7ac1386c86` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-infeasible-branch-positive.sarif.json` | `47b953f1d67ab53eabdb038b1f6df0d0a3d087692f7d7e584f8de7073adb403b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-chain-negative.sarif.json` | `170321cadaef3bb14ce2e8bc8aefd095f4a0b87c773c48fec28f0b30ace62e2b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-chain-positive.sarif.json` | `48e12117f5ca2ba80c3f27ddb27dd30eebde3b5a7adc874fa67cc81b19a6810e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-overwrite-negative.sarif.json` | `fae0cc27d94d3db9e289c42133334b4709619e7799a207280ad8eeb978df2d0f` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-overwrite-positive.sarif.json` | `34bd6a2299523b2967dc5c14dc0042b21cc32cfad605ec8521baaf8540cc5ecf` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-negative.sarif.json` | `4c6996ea5016b71967417ce06ab01e8225e61bdf69235de27e265ecdee5b8289` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-positive.sarif.json` | `84e8ee77b865a907cdb670672e6c6a8f94a07e8d295e57de287438fffb134acf` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-object-separation-negative.sarif.json` | `1f350360b35853d663cc56514169feff17d73a095a912e57d34a1ad09596770f` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-object-separation-positive.sarif.json` | `e7e4de2be1b7ef4242c0d3c938de192008f333ed0ab5b0fbe01ae1d72001c576` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-negative.sarif.json` | `965d43410fa5d6b9e807bdd8fef7187c591de43b9db85da30286820ad28486e7` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-positive.sarif.json` | `8012b82f69b087792e2a44094127d5fcacdb295954bdbfde2306ea951ff6583b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-negative.sarif.json` | `769e0630aefc012f7bbd5dc8f110fb342ea44b5a45155c2dd564723236867e2a` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-positive.sarif.json` | `cf45819473767d6bd6b611cc731d404eeec129d2fbcaecab37e4ee9b7047963e` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-same-object-field-negative.sarif.json` | `b5cb8ea208c72a094ced17c79e34bc974c4aba3bae6b66363c7860eea86c78dc` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-same-object-field-positive.sarif.json` | `c852853d00bc594763ca7f90cb69323bd7921ce62ffabc32c54d0451bddee26f` |
