# Scorecard `bifrost-python-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-python-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `8ffa260f17d570afc01df63034130d26f19afe260949b2fadee3f27af6f26a98`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-kernel.json` (`sha256:f6f9cdf50de119e72df81c2cc960e6020b7821df6fbdb3d5a725f7e5b05cf83f`, normalized `sha256:f6f9cdf50de119e72df81c2cc960e6020b7821df6fbdb3d5a725f7e5b05cf83f`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `python`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-alias-propagation-negative.json` | `1a049b82e48b0ea011b188af6e24c005788cc85914593b79262c02ea3a7414d5` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-alias-propagation-positive.json` | `28ed1c1b8c81a25041056c7261197b15d20f9c1ce23eb554575bccb8dbad0032` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-argument-position-negative.json` | `6d5220cbff1462a838063775d3f98bd08e4f4ec6693eb099aa6d49b9fceb561c` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-argument-position-positive.json` | `3ffc5cd5492adf3c2e31a8a7b30ffee98431123b7a5dc4231270ec344c4ed229` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-arithmetic-expression-negative.json` | `27413cca645ff4ddf02f4ac8f7902024e1fd53c7124c92e14be5eb4cded39828` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-arithmetic-expression-positive.json` | `326d44ec922e8e5ebddaa32127a136a6087d23147c2f613c6d94054a4959ad82` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-array-element-negative.json` | `4f1ca6f97e80e0928b06bcb8ffba5b398cbf894f430335313ae6bce7dde7ae6e` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-array-element-positive.json` | `34c63b6c44c151f1efb8c83ea677bfec1550d57afdff02910ce050afa49b19f9` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-branch-join-negative.json` | `06f94a9e1de64bd4b0905cf0c90932b023f067005ae0ac1c01a0b9463607f3a3` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-branch-join-positive.json` | `203d123ab8be793c7175c691d478fa5548567316050dd68580f088b1db869954` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-call-context-negative.json` | `a727ea9c742aa7a11ad6ef9dc853a74e0dca45d3fba14b7cca3afaffaf42f846` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-call-context-positive.json` | `b08a667e8c12397208ddf1b66d30be884a78fccead79cf9fa7962590b9937f36` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-direct-negative.json` | `8a5c016b42b8bf75954bad81aed12ae7dbf1d80da21a0631440d6fbd676f5162` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-direct-positive.json` | `8c6f7936a82625ac7a0f87b5454e4306743cc86e7bc38693b7ef7b04db5d3c5d` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-exception-catch-negative.json` | `defc9b7aba5919a8bacb58ff697d327e9f8cfc37c3469084f428b512a85af0a2` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-exception-catch-positive.json` | `38de4921d19411ca1d139ac7c42d99389ff1024037185f62eb914e63eb7eae46` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-infeasible-branch-negative.json` | `7881079a5318ff4c899e76a84045824294e82e2663842f86cedd2cd94653311c` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-infeasible-branch-positive.json` | `077c21222e824e5ce513bd32dfbc8e70e7d724ccc419f3f396dd24e7bfc38b06` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-chain-negative.json` | `1ad20f2e32153cbce15cfa1ad38d7ac3dbefb29c767d218cccba1c654d1dff77` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-chain-positive.json` | `c5b1b9a4d04c76496d108e4fea29a926feb9754b04d988ac3f23da1027fe6cf0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-overwrite-negative.json` | `934daefee5ea25b526ac92229b902ff751eab25c49e2ec1d5cf964ac75ade68a` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-overwrite-positive.json` | `1254b64dbf6f5fbbcbd2c43064029a9b884d2aeb8e5e5111208d002a8ac0de6a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-loop-carried-negative.json` | `085f79bba4420f6cfd4f0779221405f882bb338a9342749c69e73d16618a096c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-loop-carried-positive.json` | `3df643b9c9204afce77c3855db7612776780dac8c7464cf836f3e94826a61978` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-object-separation-negative.json` | `9c4945a9f481a0675a319245461368f4daf83b084963a295cf6e12b958e33d4e` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-object-separation-positive.json` | `dc3f087a6a1d0e5de0cc4b1d8f56e6368769ea457b4c72d13ce025207d6fbc04` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-one-hop-negative.json` | `e349c14988e0045aaf1641a4ad80b14e04b17ae7f4351ede89186506a0c5af84` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-one-hop-positive.json` | `e52e0551e630d9dbebf98477cbc51e19763e9b8f7c06cd6bb277ba34d16a0866` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-two-hop-negative.json` | `875a2ff61238d2ab7ea4070339c07bf61769b1326e03a1efa57e14fd59cb22c9` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-two-hop-positive.json` | `4f78ab83e123fd649cb308e99e7910ecc1cb76b21ab63b741254fbfaae88071e` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-same-object-field-negative.json` | `1fa19c6509a86ced72c67009146de0e6db5bb130d3ac6b175f2c33c1a2f4d570` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-same-object-field-positive.json` | `d4dac3f4bf3554c8c926908f52d542cb33104d955315777f262626cf9df11603` |
