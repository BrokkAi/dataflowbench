# Scorecard `bifrost-go-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-go-kernel`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249`, adapter version `0.1.0`, configuration `3e8066742eac91518264ef6d3ad8f99d2f6dd7159ca1c3b4114dbf5d324b4fb0`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-go-kernel.json` (`sha256:57dcaa2fef4f989c6da2f781aca6e016e9243801603edd0079d1f23d7697f4b2`, normalized `sha256:57dcaa2fef4f989c6da2f781aca6e016e9243801603edd0079d1f23d7697f4b2`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

## Language `go`, tier `core`

Outcome coverage: `reached` 17, `not-reached` 17, `inconclusive` 24, `unsupported` 0, `runner-error` 0, total 58. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 3 | 0 | 0 | 3 | 10 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 8 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 2 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 8 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 24 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-negative.json` | `7616554505b467725a92fc417c168d419c5de2b734cbf25d907c40622c283f34` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-positive.json` | `5c01ea52bbc906c15aa7569abc0c542b72b9e4d4f8dfa9a9220f210c83febace` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-negative.json` | `8e2e07d9caa6b9592b3306a622c25734c23cd3d3387e345b6689672bdbe472f7` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-positive.json` | `abd262442422aff3f066808e896123cbb442f61318114ac46a99e3df8bf7292a` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-negative.json` | `11ca48547d0205924e41deec4e15923ddd982acc1bca3707a42408854ae208b0` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-positive.json` | `ba5106adfe5b88334e71d603be656392866f86617ebea1c6d3f898c999dc634c` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-negative.json` | `617ad9623b147a537da554380263ee086643467d7ffe8cf1bda0ace5799073db` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-positive.json` | `313c71688510b7378d40391fa8e23dae50cb03383dabfe1eccbbf3a2b5671fef` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-negative.json` | `ae4ce100e817ff12b8662031a3aefda446579d133d2196cc66b74d5c88da7796` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-positive.json` | `4c41921e189a424cc4bbe15efe6105267dd3ea1dbb32e22f6200c6d199188af3` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-negative.json` | `3f73879e315fadd6db78d8659dc18d4c49ac6e24a42fee8adb86343ab981b485` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-positive.json` | `6ad6766b79f612fb1d856c0a75256dd462203693aaf47453cebf10bab6ab2f86` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-negative.json` | `621ec5b60f9b3ba45c35fdf3b3ebf60d11c60c231409b18f93e2276c6cda9eed` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-positive.json` | `a99c01dbbb7f1487cbdc82296c8875a4b22fa6c6d613f5e9971480b2e057184d` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-negative.json` | `9ac2625e829d03eed404a53ead627b260de0d88327ce038e096baff4a50d767a` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-positive.json` | `2852231257c0f17804561bb9bc11ed3c3c8550a97afb1e608a4c2a5a27b4cead` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-negative.json` | `f9989fad4061ded6dd6e5ddd0ecadd541a2cdfc887c2c47c9d33d43095545245` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-positive.json` | `0f57253c442f8d7061ffe61933f425a9c2f311e518c03c6960e0629c58c377a0` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-negative.json` | `525542c0b1b1b31a076d4d388ab20b94694d4f76048520946c393423142cb99f` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-positive.json` | `8f588143a7ed51f8da5e11ccf6f6272e25523e79828c2fd89b0ac12427b076a4` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-negative.json` | `3e0592b062bf75540f921c9cd71f7ca77665c023adc35cbe6b462ece6531cfda` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-positive.json` | `707d7f9adb12c3e614c2751c61b4796834ef851c41cfc3eb50a875385e6619c2` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-negative.json` | `1e1b99af21f29c5248787ca46a1fc09406505096607c110d7c4fde0466ae523a` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-positive.json` | `078912bed6f59470560e31df2650a75839032d2aaa43f666b0f925de9bdf3482` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-negative.json` | `2c5d26fa28c47b0d60c2a2c2e2b58234397c57e1f5a33b9658e5d4ec850fb930` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-positive.json` | `2c5d26fa28c47b0d60c2a2c2e2b58234397c57e1f5a33b9658e5d4ec850fb930` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-negative.json` | `5c60816e5049aed15f9aba226819a3f626185f390fd02d6ec0d0981fc2a6c112` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-positive.json` | `944a607dde12e2e5a5f71213be33461c4ac4ff500fc9c7f0df4386a9ec3c6b62` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-negative.json` | `3c437473214d185ea159e0727d730483106246120e80c70ed7f95c38a8a8618c` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-positive.json` | `93220865ccc22639fd79b1459c0abe97fedb369bf2661d434e9f35c0c868db3c` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-negative.json` | `c3073d21f2c954c1a328af579c938cc1ed4495738b679f707646d228cb63b360` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-positive.json` | `5ba68f057fa02fb15e0cb729d54423bf24327a048aca2f79108a445020d962e4` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-negative.json` | `69036b59ae867305506119e9cd7cecfdc56b00bb29ed19fbc63f65f15fec249c` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-positive.json` | `233405537520fba28942565fdfd74f905e08d358bfd72e85b7130a2a3126619d` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-negative.json` | `3bd7833cd71e98dcd41d936e0357f5756f7c4ba663c4afc116b7fee451c6031e` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-positive.json` | `80b4f5e20df7d551a0e1e2784ac6b634209fb9cc9f7c69e75e3a658d9ceea2c7` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-negative.json` | `2c62acf9fe9b47e75a13fc7d17571f108ed849fd5e57e62c4e9e2deb9bd0b07c` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-positive.json` | `2c62acf9fe9b47e75a13fc7d17571f108ed849fd5e57e62c4e9e2deb9bd0b07c` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-negative.json` | `4931061a787a9f2aa709ccc5197657e647539bf392360bb46c18e32da0d43251` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-positive.json` | `3091f95d33169a63a5375b125c92555f402f36499e773d029eebc3744628850a` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-negative.json` | `e4e1b9d47175bfde0d64b709974444e672e557134839f893f542ff6575d06af7` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-positive.json` | `1d5263582ac8730b6c99a93f85138a755e4c0f349dff707233c3132140ea54b0` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-negative.json` | `5783380ec11f1be7f299f3416aa70df77a5d38495149fb82ae1273fb78c519ff` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-positive.json` | `64aae9440a298fa9a03e0541497d6e9c09e8bbbccc81f1007b0ba25f56d4791f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-negative.json` | `b055296848635de78f06da5b7ed2fc8b699345b05344dfc188c674167787119d` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-positive.json` | `93622f881abbce8811926e9381e71508403954f0f8124f108f157a0ea1f78420` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-negative.json` | `9f18c1a9a52651b0e00b0d98848a681222854c79ec3537000f8cb7598b9d7d7e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-positive.json` | `7e447801bdb97884e7269412a0e8f53b08dc9f195271e6bbe100f63305cacb6e` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-negative.json` | `7c7b67f97dcb0ca44932954b515b97dd9bb60404f685afea68f289745a3c3942` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-positive.json` | `d227940937420ade9e0a9a65d8301ba24d9dae23699a46bbf19e6b317e18db84` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-negative.json` | `a3c0ae3988a44cee858a459e5d608c0889afb91b035230d9165f7433a41ada69` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-positive.json` | `9bae2cdbd49b2b26f99fb47c3b23776715f2098385ae2b3cdd483c8e11259cfa` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-negative.json` | `71cad6ff5a94c11cd8c22a90feca90dc4cfd6c50fd1cfb211b965a4b086f09db` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-positive.json` | `35d78123a74cadfc0c6749fdae258c3b49b1dfeb0e2a50f0cfce1b4ab8988341` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-negative.json` | `d5b1bbf90a6e0471adbb38a99797b62e22152b1b29c1561e2b66e9c6ad504056` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-positive.json` | `afc80a4b714790e0502fcfd97db45e794bc4adf4cd46e636c1698a430d7e467b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-negative.json` | `110f7811c6405322946b5d5367789686cc46cd3980b67d6b848980ecef6144b0` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-positive.json` | `6a916f5b2d5b7b4bf34d7e8c93e007cc51214ea2c91b50178317020ebda25126` |
