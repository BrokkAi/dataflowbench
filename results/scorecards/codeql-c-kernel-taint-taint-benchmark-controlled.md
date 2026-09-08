# Scorecard `codeql-c-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-c-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `80e1c32fbd4eed82fc2c92dc4afc2c08bf61ca0eb66234dd2f621866ba2b0097`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-c-kernel.json` (`sha256:bf7d2c046e2635a8f79b7b47a9122fa647e9c0b02c43088d860a186fea785986`, normalized `sha256:bf7d2c046e2635a8f79b7b47a9122fa647e9c0b02c43088d860a186fea785986`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `c`, tier `core`

Outcome coverage: `reached` 23, `not-reached` 24, `inconclusive` 1, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 75.0% | 0.0% |
| `dynamic-dispatch` | 0 | 3 | 0 | 3 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 6 | 2 | 2 | 6 | 0 | 0 | 0 | 75.0% | 25.0% |
| `interprocedural-flow` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 5 | 1 | 0 | 0 | 100.0% | 16.7% |
| `object-sensitivity` | 3 | 2 | 1 | 4 | 0 | 0 | 0 | 60.0% | 20.0% |
| `path-sensitivity` | 3 | 0 | 1 | 1 | 1 | 0 | 0 | 100.0% | 50.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 75.6%, FPR 16.1%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-negative.sarif.json` | `1683e685f6e38274b61620e20e83dfc9483554b93203868d86822ef3985a82b2` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-positive.sarif.json` | `cb6935634bd5399e6342c75abaada39cb238a8df67ff0e20df5b04b4e86623c0` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-negative.sarif.json` | `b308daef1af32477248e43b74cc58d67bcaa0c3af66f56dee8f4fcc04c2147b6` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-positive.sarif.json` | `61e61e7c2d1c21bc9b8b86468621cb2f713c949b5df3d9e0ec56015f6ed70e06` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-negative.sarif.json` | `11c5928340383eda28c792bfdb801d2fc697aaa105d2664f424c5fa8ddd99606` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-positive.sarif.json` | `c88c84675c2b6a5396b204dd9dadc656b079fa5dd9b0620ed61340e17f5e45ef` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-negative.sarif.json` | `33de992a378c7d89ce9663ce7eaddb5b637bd49ef2c775867f8a4dfefee1ce3c` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-positive.sarif.json` | `a737a7e52d9693e5440d7e21a7502cae3452f528cae6560656d7fa8e00136471` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-negative.sarif.json` | `0debd2a1617f3935f2ee88a589124f26bafa30a9a08bf52beba3e220e07a242a` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-positive.sarif.json` | `88ec1b6a4f852633c3df8b81781c3e6850e5c4a7176ac7ca70f30aadb357874b` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-negative.sarif.json` | `e608450a02fa09010539b49e7368b2f21d12e8b1cffbdc43a62f1a61016965db` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-positive.sarif.json` | `8ee0967d038aed119c484a8490b986ee6e467ac39df6e37bd57dc0d02e2b072f` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-negative.sarif.json` | `47bfadfb8452d38ee2b78dcc0dacf4126fb205c101c38f0013a321e79cf80d72` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-positive.sarif.json` | `d45afbeea660b87a1051924564f90ff5f6bd304e323272ab92143f84a5e9719a` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-negative.sarif.json` | `35041619e28403a147d312c5a8b6c049a053b9189dbdcb6c6c0c485080f77aa8` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-positive.sarif.json` | `4a9878edaab74567049cedc3f68fc1fbc40e428f341f88d6bcf9d72160c47431` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-negative.sarif.json` | `e3821426defc7e9b361ca34a8ddff363ee4f19a02b8b3b2d7ba8c8886ecb0307` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-positive.sarif.json` | `1e7cf2a284b3a644c6b8a8992d05d29eed951116e2a483fd6f87567f9a7a711f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-negative.sarif.json` | `a30db50ad249fbae2bcdeb27598fa704439ed29becb34c6471ba099b69d427ac` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-positive.sarif.json` | `5d13a4db211bde140e5b819ad9890750d7ca2a5c41f5b4bf7b20ba522587072f` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-negative.sarif.json` | `81a4f768c598a199335879af3c1288d8602df001f269fc02f3908a9ce90a178f` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-positive.sarif.json` | `5d989990d44b9ed97a9ac65598064d7052902be220b924bc90fb092d7fb3bbc9` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-negative.sarif.json` | `7a28bd92358cd79e0a3b6d15fadbe1be398ede2998552f4dc1646b92f2caf2e5` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-positive.sarif.json` | `be8f92ec86f944ee7ed877d6fe40008362648a0c407918017f4ca00c5db858c8` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-negative.sarif.json` | `e3174090f9b4be614f2d3264fee090624d8ac5cdd46ebc50700e38b63acfc1f9` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-positive.sarif.json` | `4985df53b1954503d2588c53f82da210d27da569ec084492ec53814c3ffb8665` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-negative.sarif.json` | `3a88f4061039e09aaa1677b3af5d20e663b0be21ef0432fc2c9017ac94143c7b` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-positive.sarif.json` | `a85c9e2e3d9422447cdedc62f7f576551781711d57f85265960298b6ee6ba3b9` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-negative.sarif.json` | `430fd39ce7a7c7c36841a0be1f18d85bdfde8bae9d8c4c1ad6824a4b06a311ba` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-positive.sarif.json` | `2fcb5e8d2e51170ab152b3af4a2cce24bb7df7a5e12b89573b85a73a9ba636f6` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-negative.sarif.json` | `693ca66cad618615f313ced93230252916080a0fb9c4bfa1e9ea492b65c49577` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-positive.sarif.json` | `7faa97364665f297b84dd23daccef6e3e63be8f45e5aa0c310f91c15e9e77d2f` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-negative.sarif.json` | `8d16f758eca27166997e2a613b5d95458264feb2051c09a97a61f1c3df40b9aa` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-positive.sarif.json` | `644bfcc9d2dec190c6d302712a1d29d69f508bb20152bcfd97408bea704449a6` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-negative.sarif.json` | `c6afb02813672cde01ab57e6a930b534f733aadbe8d74c03ec71c94173fb5a53` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-positive.sarif.json` | `272dbcdfc5c868a22bf121f5397d1e1bc98e284c30db7186ddf451ace223601f` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-negative.sarif.json` | `1ec2c3b635bc44405ed8bcf26dd9332ed14508e860949db6e9632a1ad02c3645` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-positive.sarif.json` | `1bd635a6fcfb547c2ace888686c451e8f3f188a6293cd818e211c2157918669f` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-negative.sarif.json` | `444e63d360b5eae5e2ce62748023c09db4e5600cfd72fec059d7d54100af2e69` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-positive.sarif.json` | `43a1e4ffc2997f5a8fc0cc4628235abdd3bd2bdfa758cf2f4ed8cca7db54542f` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-negative.sarif.json` | `ebd5c6418ae32e8fac25e8dfed3ba5ef42eef8eb72e4bfe0138de0270d4fc474` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-positive.sarif.json` | `5a702623d841b06dcc4e1adf40d0ad4c33ba6f9d816c1223df27eb835a2c6fad` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-negative.sarif.json` | `0e7e25d3da182cceed97b4e7b6b04847d65693b1e48dae19c4083de0c615911f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-positive.sarif.json` | `4bcec110b15c7679b956c0e6249fb6f22b7c41e74767f607a9d213595f232bad` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-negative.sarif.json` | `c3d74d073a5dcea10bd989a5c369769044f82f7b4132fb5d383fcc26933a64df` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-positive.sarif.json` | `c1840ea74f62328972df4fba79476a93b392fae43b1048102501f8c1d62f6627` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-negative.sarif.json` | `54dafe5af23ed4d5743a8decb40888bb9e73f45a182e42fcec1f52c9b718c7a7` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-positive.sarif.json` | `366886590ea3ec582f5319da08e69b79b89f463c2d939702a2fb27437f82df3f` |

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
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-error-code-return-positive.sarif.json` | `35dc3f86d7ed6a2332a9c08ccf1b2e4cec6f95001a4cccc13e57561a7eda1a9c` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-goto-cleanup-positive.sarif.json` | `4eca6eea679a71d3b779c4bbad1c498a2e11aa3155b5336593df334d515f77c8` |
