# Scorecard `bifrost-go-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-go-kernel`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57`, adapter version `0.1.0`, configuration `3e8066742eac91518264ef6d3ad8f99d2f6dd7159ca1c3b4114dbf5d324b4fb0`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-go-kernel.json` (`sha256:919e62b265d16b69a8288c39d5be0eff12ab7d878df3d42e116895403c4f7382`, normalized `sha256:919e62b265d16b69a8288c39d5be0eff12ab7d878df3d42e116895403c4f7382`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `go`, tier `core`

Outcome coverage: `reached` 19, `not-reached` 17, `inconclusive` 22, `unsupported` 0, `runner-error` 0, total 58. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 4 | 0 | 0 | 4 | 8 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 8 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 6 | 2 | 0 | 0 | 100.0% | 14.3% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 8 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 10.1%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-negative.json` | `0594dcb7a534386cfebd9b91bcbb7204ca2067caa4063c94266c2ac291e4b4f1` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-positive.json` | `eafcfb2bb953633f4cd041d044f0e8063916241abb077ac605ab0fadd023b862` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-negative.json` | `5673e8427f0d2d44942461789143ed0ba3959d6e241262f9a36b6f18041edfd2` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-positive.json` | `7ed97fe96a7110fbb14baf27d71a8dc20d392ef10934640acde7bfc35264f6b4` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-negative.json` | `07d5329c2e188d2791903fdcff0ea18508d4f08493af8f24e890c50e5959d3ac` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-positive.json` | `69ce66c7f7cd193ae94076efc58f9f70fc09f18a6bc558fb32e04dade5516d0b` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-negative.json` | `2271bef7446aff4194df6c0425a007badd5bdc8c99750f477d794c6cf6152b5c` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-positive.json` | `5b965297068b9212a46e1b4292ff6ebcec52c6107c12b372bde761f774c7eee8` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-negative.json` | `279be5b05b20b993a3c3f1a8b9189daa08fe55f94244da0388a863a340e7926f` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-positive.json` | `377cd4a0264eca28a8f04f4d1c30a2c2139112bdc52fb6ca6f31f16896132e33` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-negative.json` | `05f8ab65e4ff5dc8e89402536b058a6e7c99a96589c717e15ee7bc577b567989` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-positive.json` | `d292a9ae49160b3c7d539e7657ac8ec7f5c2441290db75c24decf772576de2b9` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-negative.json` | `a80fb59e4b8732369028bb31330a96eb47221641a6d480a384172371e2cd9db5` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-positive.json` | `a75b8d719d083126f763c48856a1bddcdd33ffda08ce718e81c5f9fe8904def4` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-negative.json` | `368512f5d1683c70972f1c5ff128da2f48d1067f242da968fd2dc1d552c779f0` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-positive.json` | `1c51b9425913fc3e76cd0515c134ca3e96d3206660b8ec56179757d0428f72b6` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-negative.json` | `605f9fe148fc7b49d6c34ba85683918f776bd58141e11a3348c02404a9baf880` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-positive.json` | `08b70ff04649b882a49611409e9906acac6f990d0c6da8095898491a12a7413c` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-negative.json` | `02eba4f77f0435b0568907eef33c7bb3382e0355b327a781f4a6b6e639fa42aa` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-positive.json` | `ac0c44a966cf7b68bce38af0aa55577372af60879a3b5f790d1642f43151de21` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-negative.json` | `732e16955633a519969fdb7be8eed133b2198fa40106073213774703f6c4335e` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-positive.json` | `9b9bb729e51daf01ababf7c4b7548f3b1ebf7ff6a12ddd2364d303d8ea55319f` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-negative.json` | `07b44de0fdbc01e54ea25819a0e95a624adc12c48676931b760e5e7d104f0a12` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-positive.json` | `c89d45a128f4dc33c50e90a812ecb22acec14f0baa69856e369f10626ca889b6` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-negative.json` | `62071987598f4c600ad9064e3304d50d3298c3fd2eaa3fa9fb762f3ee1436010` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-positive.json` | `62071987598f4c600ad9064e3304d50d3298c3fd2eaa3fa9fb762f3ee1436010` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-negative.json` | `5aca2a15bd2303d6ddfac061d50036a78538e3947edec4bdca74462fd7ada36d` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-positive.json` | `d414a0f3003a92170827dd9cc174ce2cb4ef5f481657c1ad8a9e17a6e477caac` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-negative.json` | `7fc588e1bf3576f7e436ace09468dc305cce465a40c7d4f7d62ccfb000b06671` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-positive.json` | `bb79e6e05395deccb9da9fbd12bf014ef88c5c56533d2cf653df7b837394fa45` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-negative.json` | `a4bb6801fb16881870338d7119b256369709a5d10551e5b508e72c231644ed7f` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-positive.json` | `303292c4a41d935c0ed0c01ee036e9330c97d7d362591694a8d3077de4e3c2f3` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-negative.json` | `f5b47a24a05902d29e99f7285b0dffb6dd33cd19eb0078b2c2e016b058216bc7` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-positive.json` | `5e479289d362b3bec41135aa8dd3465f979c8285f529458468c572d39424988a` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-negative.json` | `ffcd065e0a044a6c76f43ef27b7186897135d91a574e1f94fd71a18811b90345` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-positive.json` | `2ad9af4b87f2c48cb52d5a8c949583c5d4e7fa01916b3382eed689b612e8d31d` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-negative.json` | `127d24f9ab72c399f35beb5d6ad7b835500753fb9f2186ec7fe020e846fab9d3` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-positive.json` | `127d24f9ab72c399f35beb5d6ad7b835500753fb9f2186ec7fe020e846fab9d3` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-negative.json` | `3a60ec867d86eb12ee50e6cae2b49735d661cf4a2d8b7c4fc1ff7940df29f74d` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-positive.json` | `ef6d44f3659d4c282fadc4bad0e9f79149d4d585e5aaf1fe104dea345fe1a53c` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-negative.json` | `61a69ddb4270a4c59c429a625275afcdf81428a8e9ae0f1f4a3a37be5c7bac0e` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-positive.json` | `9aa3fb9a00d86542a68d781a9c21def04c8bf6eab71901c6ba1dd9efb740ed07` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-negative.json` | `e984b72ef33ec50a47207731dbf0c704e072710060bd51c552bfb3b5edaf6c3e` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-positive.json` | `a75cd8f2046eca8b39945c9646c15068cbca9ad32b3eccf77e7953939ddc00cf` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-negative.json` | `d17778c97ba7fd755512df346ffdb43031afed0404866e7bf36e0aaef9b9320d` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-positive.json` | `ec0ffcf73553ff078fd5061a4fe2264d754f28f4bd0d0c641e9445b483dfa749` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-negative.json` | `9a5c173655a07060ba4f7384ddb22ce69a3e33d9d13e3be6196072e0800933f8` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-positive.json` | `89a30e5982c088913d147702d0428bec32efa8bfe035461fb7ec753bd1378737` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-negative.json` | `4033dde5cc413fb155d83897df27719d48179f3453b84cd805d139602cfeba0c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-positive.json` | `73470e0e2cc29241b2b2bd8b95f25558acf1647804af19e0cd2f3543f1242059` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-negative.json` | `d2edcd759ae5a2f234c9dfe5b38862a20d4bb0cbccb6154c60b0ee627bd5c819` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-positive.json` | `829cf74c30cc7d9ca51ce9523809d314a2624ef1558e94ee7cdf6f545206ec1f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-negative.json` | `2ed9289525833da24e3a3278f234e93f2058b2d289ab304acc2d4e39cd6c7632` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-positive.json` | `830a1d91169080b4fc2bcbd7959229fb802538d4984676a94d75973198153ca3` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-negative.json` | `7521dfcdaef1d6fe815a965e28d779a83f57bc827b54d66300a1c432796b97f4` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-positive.json` | `cf31684e51e36d444d8e002afff92ec6044f1f93a94b734a26efd6b51d8e4081` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-negative.json` | `0d8d939f7ad9d6839bc090867fb8203158890307a1083cc29011d6099bbfbcfc` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-positive.json` | `61ea589218f9166d4a33c0f0c148184940e97448933e91ee57280823674e4d46` |
