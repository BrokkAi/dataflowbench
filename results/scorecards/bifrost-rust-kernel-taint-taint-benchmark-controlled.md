# Scorecard `bifrost-rust-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-rust-kernel`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249`, adapter version `0.1.0`, configuration `36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-rust-kernel.json` (`sha256:286f53ef2d69a9661904156064312bd54d58ec2f18b5a7bef170379515bf1587`, normalized `sha256:286f53ef2d69a9661904156064312bd54d58ec2f18b5a7bef170379515bf1587`). Generated from freeze manifest `reports/freeze.json` (`sha256:e3fbcae1eaf3f49192f7156616c4b2149893a8470e03ff445fcd1d5f984f9e5c`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 19, `not-reached` 19, `inconclusive` 16, `unsupported` 0, `runner-error` 0, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 6 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 6 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 6 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 16 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `26ec5c0cf3793eda3f16f5cc3965732e323d53e88a07f9a4486ee3ef8aa09adf` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `ee17defd6521fa97361009f214b6e0c0f2ecb47f59abaa3923a8241fbb6866fb` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `5c90fd4f6f6d259a7674a89dfcc5a5c4812146ea9bfbf341856a2630ca5c7c55` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `d321962728d975692ef7a87920452f32a29724708d53cac794201b47a0b4f05a` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-negative.json` | `f9566aa5dcd793b03b934facdf60e94e9bf2dfb6fea424f7f2a89e03002758b9` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-positive.json` | `5749ec172081ad8769600b0b6a97daa46504cdc40f3c5f13beaa1e924bf348fd` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-negative.json` | `cabf6319329a135eee33113b2a80e420ec1b71aee418b68ec1d54438b6f3d3b8` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-positive.json` | `0248f364606d6cd237ddc6257e7b9d91ed185a311ac2f3246031a2edab2bf8f6` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `78bf7a6ab82760e271cb4de47f3e33a02927c120f5ce7a4effce632a53eb0f2a` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `f825919f980c9f499743fbbf5171a6c10f1509ae5dd629486e55e432ce894192` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-negative.json` | `7d307b7687b86d743d16ca05ae7b8a11c4cf9c1702f351e3df771b535113031b` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-positive.json` | `6f19cb93049415ab4568b807d46045bc7886403b7022f76f8be6afec8347f7b0` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.json` | `c3659868c87d310a6c503e59dcb38ea958e7955fc975ba86abf99dd5e5ab7ec8` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.json` | `79da0c1a306186c696eb576029501e62a4c70ee6f2a2fb9ba693dc9461ccb6f8` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-negative.json` | `c8090639a907105df2bbb1591d4cc5ba9da10bad86fc1a4480fff9a96f594e92` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-positive.json` | `cc59280334c75de932c22e9857c6ae6f8dd57def085a6137d0bc32f2a49be4b5` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-negative.json` | `b83fd2fce4c2d7643b55d8bd65f20c95f7bfae99af5845fdc433af9486b04e47` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-positive.json` | `9e342fefc98d9d891d0d6a7b29a721ce232563d4672bd2f8ead78489ef8f1c06` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-negative.json` | `b2ac9327c437f4511963b7935d000c0b40d000123803737f4c4872e36691a7a8` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-positive.json` | `7419d4aed7e9905f743337cf54c3e3deca4cf1e7d5ca12565f97d23ae6a0a1b6` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.json` | `502e7d4d8d0d13d79acc1d5197a5e7c0bab77bd44db693b3f0ee69eaf855d94a` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.json` | `eb6c92bd61d2a39c2013c09a29cc9852107a0ac3264acee9bbcd44259acd188b` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.json` | `9c5e9bff8002f6aabdebf562870f3be257b36ac91fb2a0aaa1f0cb89f4d53960` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.json` | `6c6179851d70fc2b06026b334c57af7c163b00bbd781092fb042acdd1769ac06` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-negative.json` | `24bce949009544d63e2a766f9b3f9cecb9484a5e06824440a8f1c05ef1dd8b02` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-positive.json` | `24bce949009544d63e2a766f9b3f9cecb9484a5e06824440a8f1c05ef1dd8b02` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-negative.json` | `06a29f6eaff5bfae01b671943db9722b8f75a0c8be9ea1665280347aec38d403` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-positive.json` | `4242eeab9a6c310b27aedaffe1f091d7814f8343c4091f49d66f9a21c7ef6a20` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-negative.json` | `d64182e7bfa26b89157fa40d52fb98f4e0ffe3d8756a21b977ff050b3e3a8de5` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-positive.json` | `fda3a4497af2e45ac039687bee952fe5536d71f3bb384c119f2f3dbda48dc805` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-negative.json` | `ed660edb1d9179fe24e0efbc720edf19f518b45a3defd3aca94a0262cac87e1a` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-positive.json` | `5bc142e909fe239a4c300c6819b2477c12bad716ac33cca07ba6c1ec746be92d` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-negative.json` | `147f8f9af563d2fc9108a9f6b3ce6543847a42ae6a3ff8c1a7b3b8e7249d7c3c` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-positive.json` | `28735aa0da47024ac16abaf953127db1c7e29b3ada9c35b1b56ffef6eda014d7` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-negative.json` | `ce42a80d0e9aa7d78f7c00d35df45ffd3c133eb5b477c455f7d60b625b97b917` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-positive.json` | `a4e1197416e6d7073abb3c080c41a1f4d6649eec1ae4f639e520e3b4c0411c4e` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-negative.json` | `42a6ec4c96971854472a3f2c544dbe2392c91668e4ba95449fc57baf03780a8d` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-positive.json` | `9d7cc3303648e5a698a56af5377e725d0b7cb3edd3463fe7eaf919b160ff2a80` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `d2c77a884507559804abac7d89b93334b5b8af9fdcafa030d29ca558291afb38` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `c844ab0c5c8bc044a3542df3a6cdfeb52cf3bf838baeef68e301c53af0b7424f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `05a8afa331745e7395fee8a2c319fde50a3b0b8291dd8707b617dbe32a1109b8` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `968accb3bf9501e3147851f2633acd4130dc8d59b87f09ac111836049b1ff954` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `b9bc3976d21632bc2374650a3460d55ceccf82cbb29c5d923c6de672f7f8fc2b` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `107580b539964db8b847bba657af17313a4f2b132c0db6bfd1f12635666a1d84` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `17feac5e36e9c22ef91b71523167e84450d59af8be9fa38d141c4eea57344390` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `12538942b0d990ce803dc12fbde6d0d160f7dee35afe3c911299cf36d76ecbf6` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `24c7e76f1b6de9f7cccf21363254860cadef16d03d6a5e1fbaeb077e7d9b7b15` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `b3fc65540bce7220dc9bd81d60769a295b76df74fd76f8b6790f4a676940819d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `87e263775933514a29ecae0ab80346e86f39fd1cbcef42ec5d9de486ed758d00` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `1bf78cf62824e7391c80ea90361584057e1a3476cac57d470530ef16aed3add2` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `ba178b213a1235a0ec485b2b236a43491384c1f3799f591d0e92cedd550f3820` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `5861de51bc79608be9397215d15ccf86a2e9b79723e4e4e22f18966840ab261d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-negative.json` | `7698f457f518ba73d5b4d5ba6b6cf0fb9b1b4ae11a658722e80ce59e81129b69` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-positive.json` | `3fd12d6462fb6788bd21804342d0e3a41b70629134e91d983069c9f187e9617e` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 2 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-negative.json` | `0d5102e2497dfa34643f651bd72a78940881a70abaa141ea903f1eccf662ba4c` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-positive.json` | `f07a1f000ea436f8537306d7bc749d7d9755ff60824140dd849147870bf9198e` |
