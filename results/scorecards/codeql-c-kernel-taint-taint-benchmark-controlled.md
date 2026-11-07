# Scorecard `codeql-c-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-c-kernel`: `codeql` `2.27.2` (build `codeql-cli:d7b185e374bfe18c0484dac07a521a810eb9c4fb`, adapter version `0.1.0`, configuration `c2dc474762ebba4f22866af23dc328b6fc6b1b10f0adefc5cf610996642a4100`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-c-kernel.json` (`sha256:8b298f7b4f1056119143ab235fe95160170c5ba9df9288bd716662792afab5b0`, normalized `sha256:8b298f7b4f1056119143ab235fe95160170c5ba9df9288bd716662792afab5b0`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `c`, tier `core`

Outcome coverage: `reached` 28, `not-reached` 27, `inconclusive` 1, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 75.0% | 0.0% |
| `dynamic-dispatch` | 0 | 3 | 0 | 3 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 7 | 0 | 2 | 5 | 0 | 0 | 0 | 100.0% | 28.6% |
| `heap-field-sensitivity` | 7 | 2 | 3 | 6 | 0 | 0 | 0 | 77.8% | 33.3% |
| `interprocedural-flow` | 11 | 3 | 1 | 13 | 0 | 0 | 0 | 78.6% | 7.1% |
| `local-flow` | 7 | 0 | 1 | 5 | 1 | 0 | 0 | 100.0% | 16.7% |
| `object-sensitivity` | 3 | 2 | 1 | 4 | 0 | 0 | 0 | 60.0% | 20.0% |
| `path-sensitivity` | 3 | 0 | 1 | 1 | 1 | 0 | 0 | 100.0% | 50.0% |
| `recursion` | 5 | 0 | 1 | 4 | 0 | 0 | 0 | 100.0% | 20.0% |

Macro-average over semantic dimensions: TPR 76.8%, FPR 19.5%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-negative.sarif.json` | `77a6eacfe4245bf49104376dd9329c33827aca4e027a5b1ac14c2e23920cbcb8` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-positive.sarif.json` | `ebb8ea4eadaf9dfe3f6fe00cbff3088eb9be780e263377d467be553192d69bb3` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-argument-position-negative.sarif.json` | `8a10a61b85266b3266223f12315ad9112ec030c07e60de80482bc0b4a8eae3db` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-argument-position-positive.sarif.json` | `40d994ad6a996740f0382f9bc32b0fe17cb6b011ea5f0516fb83c55ba282c908` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-expression-negative.sarif.json` | `50a25cdba622aded0486f6a07e98616d7a4c6aea00a90ae12dd233bb51831983` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-expression-positive.sarif.json` | `6911b773852a23812bcc95d58bcd06bd94935e7aeec9efdcc161bde0bfe92a5b` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-array-element-negative.sarif.json` | `44f1f2eefc7d95731efdea74ae42d465499e2a0afb59ebf4e5e36dc6770a75eb` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-array-element-positive.sarif.json` | `0a5868a610beb3b0f2e7a2b7fbea8fa68003ee7b47085a2b85f71b3cf42a0f29` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-branch-join-negative.sarif.json` | `41a6c7a648ec8577fe31828b61225996fca205f036c42501d1e64f399531a37f` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-branch-join-positive.sarif.json` | `e0202bb58a822064ff68d7ff2c8c78f33258b52d5907849b6c0d10ffa1aef525` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-call-context-negative.sarif.json` | `6bc4af128117765a7b8b8de3338c4f1a5a1ee7fd7b4b4df97c987cae3b51e740` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-call-context-positive.sarif.json` | `b32ee748487e06c190e3eaf78e081480550a017f63b6f1d80e400dde523bc8eb` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-callback-registration-negative.sarif.json` | `79f57b9fba367deab3e478ca74340ee0dc74e003cc4a46571370fc0c309bb5bd` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-callback-registration-positive.sarif.json` | `2a82c672424b74ce97262d2ce4639e1be4c86307f56e8c5c140ee822ceafae68` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-negative.sarif.json` | `615e979f20b5a635166d2bba7c9d9c2f53cabd3d81a627af4d4e966d3c94ef60` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-positive.sarif.json` | `ea3fe412fea7041dd8b7c2d026164add390a20f12c500f396cd74fcb0f2c9291` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-negative.sarif.json` | `cdd734f64efaa6c6ba996a6d2bb7909b9777b59a0967051eb1e77c112f941c6a` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-positive.sarif.json` | `19eebcf91e810965199d17cc377c5cff76a9c19f02a264839b8780cc14a423f6` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-negative.sarif.json` | `63356fb7ef9d281a5ef66ec1e4e590f3f58e87d5c54f81875b65a7dbe2a0369b` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-positive.sarif.json` | `85cdfe1dd1d6c477d3be033251e08c6a8196474f5703e317aa4331ba9362b9c3` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-element-object-negative.sarif.json` | `0977aec568b43570d4e7a18fe63d14ebc18ebd0be56c3a108e53c3e58bf4576d` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-element-object-positive.sarif.json` | `65ded11275930158184857a9ce48fbbba770a0586317da6a0f660e179404cfaa` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-function-field-negative.sarif.json` | `7b592e0d2cc23638f083249bee1b3cef5d92a3b6291360baf7b1dcf28f629e19` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-function-field-positive.sarif.json` | `a7cc592dc7fbc2ae8fff7b42cac114fdaaae58b78fc5b8b35717330db584cf1e` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-map-iteration-negative.sarif.json` | `21d186b133d02756e0caf8baaa96b2bb3ee9605837017ae55546e75c7b55d0ed` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-map-iteration-positive.sarif.json` | `9435d7f1c7bf3ca17d7042066ea0009a97466266ac86fce57453c3455d10f2ee` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-mutual-recursive-transform-negative.sarif.json` | `218563bf75fc2146294026bffde9f032bfe4d6e87eaf7b91a59b43d6770254ce` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-mutual-recursive-transform-positive.sarif.json` | `c3d8f4667062688e7378014f6ff25d2bc9260373eafeb24d89e22a907627ee5f` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-negative.sarif.json` | `d0d91579c22106dc57ac31b08933cbc839fb7622e885658f11406e8108debefe` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-positive.sarif.json` | `d968c6acdebeb89c3bfbaea27b4597f5e74d1d20f713e4bfa9f8caecfb3ac36e` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-callback-transform-negative.sarif.json` | `2ac19a05027734a6c1a8d6db19e661820f3cc8b73d8307128530542cb099f05a` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-callback-transform-positive.sarif.json` | `cafe5ae094f9e600996f4162085b668ba0e5e5ef5eba453cdea130d58fe3ed91` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-negative.sarif.json` | `3cc461474290b3d012b164aa1a7f10283422b8707a4dfda322619f8b315af872` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-positive.sarif.json` | `11a4262f40356e7717f6b9ce995d30fdc0117b3074306b05c7cc6ea500104fe0` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-heap-unwind-negative.sarif.json` | `11b47c3db4da293fd8ed4a7df20d89e24531daf85b17a46ae3a68fe37d9c03f1` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-heap-unwind-positive.sarif.json` | `eca5bbc00ae29abb774c5386017f34104ecc862149863256d558094c305469ea` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-payload-transform-negative.sarif.json` | `ce30cdb4103f6ccf1d3cd1c0e374b3dfe726b16156c03adf018c471c09817fb5` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-recursive-payload-transform-positive.sarif.json` | `c2b905ac1af785992f9c41655a3ed32ea461b999856e708be95b1c9441c51b0e` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-direct-negative.sarif.json` | `c0323cf5d4dca76f5adab359eb48f5ed41263deafd63331607f4d9d150e3f2e4` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-direct-positive.sarif.json` | `2e8e45fef9e7788116c587ce9eadbce1b394c19d31b5d0e4f357edce5bc65641` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-negative.sarif.json` | `f0a5587a177d6cbfae49126f2bb2eaf34cc64fb76942cb2e8e85f2f45ed94669` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-positive.sarif.json` | `9db58d689d42a8a6754485f2e07f4bfdcd5a7e970a665cdabb8ffe3d92ca072c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-local-chain-negative.sarif.json` | `cd53a05f098b96bd5afb57bbefd4ff37ffa95c6ab852a24e1f83ec83a83cc568` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-local-chain-positive.sarif.json` | `06342de8933c4c5c2aa8240b64831d201479f7538b344ae3af3d7a0bd0bf5fd2` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-negative.sarif.json` | `dd075d1d14400cb9d4ca6c15639eb73dfdf5ddc7ad0569f03860292c812e66b8` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-positive.sarif.json` | `be022977827d7582184884867e1a3bfe4b0ecf2d34ef714d175b919154d13960` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-loop-carried-negative.sarif.json` | `28bc4711efec196e933db6397ab53873930ec0e48da6f0e05cddabd2479f1c07` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-loop-carried-positive.sarif.json` | `b741a3e37a6a87687a699c3804f1c14eb3c117820ab784e1c997098c4fed0ef4` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-object-separation-negative.sarif.json` | `4ce881594777d3f43781756d688c07a739769907cb94afb06b7a3b40d603fe5e` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-object-separation-positive.sarif.json` | `dd385fc24a18b164570556be11a47ee3e70e932945fae95129443e52b2ec6cf9` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-negative.sarif.json` | `c0ca5fa770f541e17ddc6c72bbf2ea04f1538c63d1856584f51abd41fee26a3a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-positive.sarif.json` | `566ea0625426dd290f453733bd75bd78b3a9c3fbbace4646dcb00f96a6c24525` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-negative.sarif.json` | `63108a17a55012637b10a8aaeb9565f938fc8ded573684ca3808646e4edaee44` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-positive.sarif.json` | `bc236c32feb90b08992eca06c7d0d3771624f6eb9389f6b9e5ca877b7ba2aed4` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-same-object-field-negative.sarif.json` | `c0557c9c87b2ace66415a38dbd30109d69017f82125e02fc6b3642e00c16919f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-same-object-field-positive.sarif.json` | `b472fc837f0d741000d7926da8ea1ed5ecd8dbb65cc84608d7ff7b9cc13625f1` |

## Language `c`, tier `language-extension`

Outcome coverage: `reached` 2, `not-reached` 0, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flow-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `heap-field-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `interprocedural-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `local-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-error-code-return-positive.sarif.json` | `d10c1e88160476d2894a97b3e9f3e275ef683504e38eea7712fdbbdf4dd92281` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-c-kernel/dfb-taint-c-goto-cleanup-positive.sarif.json` | `a9f4feb3da8dcbb9886376587ba218358a8c8768cc847bac6df96be1440e8981` |
