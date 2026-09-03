# Scorecard `codeql-java-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-java-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `eedf28b140e6aaf2c27cac6369ee552803cbc7b7674abd70583e3e962e1ef8b6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-kernel.json` (`sha256:50418965ee291047161e4fe06d5c765f2f0fad492d6288c585be047276677ddc`, normalized `sha256:50418965ee291047161e4fe06d5c765f2f0fad492d6288c585be047276677ddc`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

Caveat: these outcomes predate the current adapter configuration. The frozen report was produced under configuration hash `eedf28b140e6aaf2c27cac6369ee552803cbc7b7674abd70583e3e962e1ef8b6`, but this population's committed configuration currently hashes to `2c0ca1f64427b38325baaf87a897fdc543ddd1e09346999c3be6f13e7e22226b`. The numbers stand as frozen evidence for the configuration they were measured under; they do not describe the current configuration until the population is re-run.

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-negative.sarif.json` | `842655fbfcf8c858fc7e4e0b985c6e5b85c1e114547bae1517aeb35862b7a44e` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-positive.sarif.json` | `7c215fe90ff411c86a1af078fa36ccabe21578de3ec378d1e1f6761ec7f263c0` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-argument-position-negative.sarif.json` | `1670722342662854073548e0da8dd44cc7b44a4f69135fa9a3a9571e81891eba` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-argument-position-positive.sarif.json` | `dbf1a0be71bfc2da6b18aa6884d5b24b6890bd6fc8ae6d8d170b4453583486cf` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-expression-negative.sarif.json` | `3a2b7416a698fede43d95007bd05e9ac0e8b0123c4a4ee7c529a95e952231e9d` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-expression-positive.sarif.json` | `7eabbcc2311baa0b2b489153dfcfccce5c1b792390a52b91b4288d1d209c1622` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-array-element-negative.sarif.json` | `0786165b0587578a93416ff69c838de9f2e7b6291b82146552a59483034eabd8` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-array-element-positive.sarif.json` | `421bfbef90cd70eed013cd4b4560632c2c1b1603d77c67845c5c445865a3769d` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-branch-join-negative.sarif.json` | `3d7ee62e6f9db82615e589524ef99768942bd367a8d9547e1ae1dc42ed5cf6f0` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-branch-join-positive.sarif.json` | `9a69e7015f02eccf53a7f63a982c3ee5d0506305be250101a88482e69cc76f51` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-call-context-negative.sarif.json` | `abe7307cfdeadd429a63e11fb0f6614c177944ceb5aecde5557f025224b33dfc` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-call-context-positive.sarif.json` | `52b2476cca73b96537c7682027388ab52f7f411b85bbc6e14f73bcf4772a315b` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-negative.sarif.json` | `726a814f6bdb860ab516fd391f18eadb8d00f8381a38239dd3de5218c1894a88` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-positive.sarif.json` | `fdacf2f40cadb9c0f53f166b1dfd1e89c8ef06023741431a13cf418c113f712f` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-callback-registration-negative.sarif.json` | `b79ff34d01104ef4c8eeca86f295ed892c88e421d60cad9db2ea4700a92510ab` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-callback-registration-positive.sarif.json` | `0deb31f2129e5e593c613ee7eb8136dc0fbd9c1219632e3909d5f1830526bc8a` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-closure-capture-negative.sarif.json` | `af1f2773a33b8967b0a867252b6a8b4334e4facabe83b12be2b959702ee1b1d7` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-closure-capture-positive.sarif.json` | `ce914b719d1957037dfd49aa8cc375c16ac71f12525ef25db015f4114e1e59bc` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-computed-property-negative.sarif.json` | `be52bb6dbbc360b5c739d6dc47dc6acda6e98495dead28f54ab9d98998e9ee69` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-computed-property-positive.sarif.json` | `b49798d9aa16cd1a28be1d4d84cbb695e6aa6cc66bfc83f1c5ea2ad9c3eccbc2` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-negative.sarif.json` | `0d60b0e08931d6a3d7db6aa74f382497ed2a829e296cccd44bc9771cc247ce69` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-positive.sarif.json` | `fd52a047e52219a5857f4923e299357bef7b8d319072fece61fc7e9ceb2157c7` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-negative.sarif.json` | `2a2d7e88d20e722d45bdeb48a38030208b64a2e6b5f116a364fbb07cac4286c0` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-positive.sarif.json` | `261f96f29ea5cb075981d1afe4199c1de13af6218edf17ed68a115f1bb0cc0ec` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-negative.sarif.json` | `40e7af9932edf4c7bf336a96d743b664814e802228856e3a908fa54c1b87c90d` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-positive.sarif.json` | `890387f306fb22f72c91fe80bf6c4d17b88f8e93d0c9eb7e1027e39d66be9ee1` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-element-object-negative.sarif.json` | `f6f72fd7d62d5d998c79c95f43e26d80386e0c09d026dba49637b7cc06617753` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-element-object-positive.sarif.json` | `562801cdc098f4c34844b588d8348edec6f4045fba67b70426530307ba0977a3` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-function-field-negative.sarif.json` | `f60d21d3cdbb577a5aa5f5acdab9ee8c0d1f0acf77dd719bef04ef3922633bb1` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-function-field-positive.sarif.json` | `dbbd11516660d80e44c167a8d8e707fb2137fe3ac5c5a4cce218c813a9b1e479` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-map-iteration-negative.sarif.json` | `03176f6492a4dc78f61560e4eb23643fcb2c482bc82142d03d9c9ec8b10d92ac` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-map-iteration-positive.sarif.json` | `fdc9e5f4bd65f6d2a8143e933326993939a43906828106b0b784bd509e8e6276` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-nested-access-path-negative.sarif.json` | `81e333c91a0734d81d01aac6051129774306a975ee82f01d2c76c92978a2a8c7` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-nested-access-path-positive.sarif.json` | `d87fddded399973aa8670fd0397d43aeba441e6a9bb3b73e66f1a066809dd010` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-recursive-carry-negative.sarif.json` | `927fac979fdffb37a802707c77a5407cd3cda096e716c3fa288521eb78810735` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-recursive-carry-positive.sarif.json` | `0a8c0e781fc42d89117eedc2b1775ef16784b0e9c6d57e7e098475b6a3a6aa9d` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-negative.sarif.json` | `af583ebefaf5dd059899f730bc8ed5ddfc24e7de0db4626f44353fd861665952` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-positive.sarif.json` | `b1e98cdd3e7765ff20bc5c71a71bef2d49897ab2133f78b6a435a77f4e26b57d` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-direct-positive.sarif.json` | `5440d4723f3bc466e4b1f1ea9e37e143ec296cae2fcddca5433cc02bb28b0ee5` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-explicit-negative.sarif.json` | `4537a21366706fca18f28bc85ef2e1310265f3237f1c5f9dbc68ec850711c0f7` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-negative.sarif.json` | `47f72b002d5143bcac3a4e250d6db7139bcc71e9668bcc0ae106e28ceac0aa76` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-positive.sarif.json` | `6fed0c554c5ea4e2dc98a5ef7a8d6295b056afe065cff1db7c4555c047ea2179` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-infeasible-branch-negative.sarif.json` | `1dd65448b181f3353ea70bc9649ef0838ee4a9fbd4cae6d1fa52a2fb2c0258b9` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-infeasible-branch-positive.sarif.json` | `9940ffbb248046a014867ace68bd629ce83ab856f9c1756657f6ba675d6aa343` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-chain-negative.sarif.json` | `2be4e7cc945b55d2f7e79c2fb183de4020854673cb0122e54673f247b9c0d3f1` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-chain-positive.sarif.json` | `c013fed689da8c30402eca2512c15b7a427fc80e81bb1f7c34e3245b2cdf67fa` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-overwrite-negative.sarif.json` | `a7c4373689501812f9ed2636c8c0e07912e4e079bbaeab58c763891b2bceb2b0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-overwrite-positive.sarif.json` | `81a3de03b898649f2b873d649e17baff8009fd563191d058999706e153f0cd61` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-negative.sarif.json` | `c820e30f16adaaeec1b74e84010dc01ba775593ed5a1f9337d3250f21b84933c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-positive.sarif.json` | `4ede3247ed63183d33720b454dc8194a25637c4c6d0611099d6748dd3facb257` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-object-separation-negative.sarif.json` | `3f88660b7b2da9ab1ecc346bd8eb453814d687c2cd26eba6a8520b0427baf212` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-object-separation-positive.sarif.json` | `26819849a32b94600395f9968336636e5ac27e659fe41bcb004f91bef57df40d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-negative.sarif.json` | `c038dac5a79050e2f9e7a71871056bf7dcfef7f256e96120130780592e9bab69` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-positive.sarif.json` | `eb3a307d881102120105f2747ba3e275cf75a284e72a490152839052508d4c27` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-negative.sarif.json` | `c3bd763aa88a6a8762b1efa2185ab019c2d38c074553acd66f110b7bc3fbdfb9` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-positive.sarif.json` | `ae9ecf6a77594e53cf36dd31cbeae6004ed319450b78d4037b64edb7e2bace83` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-same-object-field-negative.sarif.json` | `b36ac3d8d4117d4b60331d1ae3ab576553512db183ad703f6c52b472a9f38722` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-same-object-field-positive.sarif.json` | `697f707b7ac589803180c4a8159bacb515e3909b1b2aa22c62e83543788f5e25` |
