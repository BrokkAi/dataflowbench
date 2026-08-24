# Scorecard `bifrost-go-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-go-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `3e8066742eac91518264ef6d3ad8f99d2f6dd7159ca1c3b4114dbf5d324b4fb0`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-go-kernel.json` (`sha256:4fe33adedb0d863a2287921e963fa0c27d9b7144aa344a0c46a1136a739f970c`, normalized `sha256:4fe33adedb0d863a2287921e963fa0c27d9b7144aa344a0c46a1136a739f970c`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `go`, tier `core`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 22, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 1 | 0 | 0 | 1 | 2 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 3 | 0 | 0 | 3 | 2 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 12 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-negative.json` | `7e9785b9f7bcb394e115207200d7e5580eab30923744f86ff777f974c34f5396` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-positive.json` | `b257ccc3733ab6d28c1b6964847ad633302726d16091c0605f88f9670e50baef` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-negative.json` | `aba91f7a8941f795aa3fd18224d224f6f60e026b549f75a62b2dfe1d601e9745` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-positive.json` | `423d834be54e7b6b122fe9de82be2b06f3ef50bca1f2caa51ce40e036a8e539e` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-negative.json` | `e177ab41c9aea121d41fced3a89120b67ada6615e72a4d03e8612cab676f87ad` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-positive.json` | `76b324e823048043e37880004c7ab351927ee0aade97bacd58602c0e5b7a5431` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-negative.json` | `25e8c7312b6d851e251b2ea4833a005ec41bcbb8f20cd0bc30aca02fb957fad0` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-positive.json` | `14e1471be75a4fef689e94d920feed6e53d6ea7335bc66f99c5c5be1f0014f14` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-negative.json` | `3f5ddd91e66f42e672424da4e5f78fd927dbc99ae1f5d75cbf5e9b4af0f0d867` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-positive.json` | `8c300f773473022d17b4bd5cb993b96de7038759a6826acab417047277e7421e` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-negative.json` | `061f5c098c729bb66dbb374f75b7f69a06b74dc60be4e7618cb1168556b28b9b` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-positive.json` | `78dd8c420841f3fe452cd29ea2c01e4234d51a9710d90c9b8df22e0c3aba3feb` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-negative.json` | `0a860572ce17575cc4cecf5eaa42abf2b8825f5f8866265627fec9fb32ada6f9` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-positive.json` | `ee361ea76ceb015850ba10586df9ee3850562cb6975d475b240a0b8fe4673c8d` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-negative.json` | `8035a06996e3fe10628d33527e28e8299c34e832724eeb0d26919247a4517295` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-positive.json` | `65088e5726fd1f9aa48330461d4e0529d1042a50c86456b5881d4cfd88a6627a` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-negative.json` | `1e6989317b92f28f2e707e310741907b125d12580066d14ad80338b36bc9b2b2` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-positive.json` | `4e7067abad48ea3f3b58d4c4af361b3c585e0cd6587b81d2f1d44cf5d04f5968` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-negative.json` | `5c72f1bb42854fec78eff951e77f5cb6b87728ef9a531eba24e441c318dc66c5` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-positive.json` | `79cff144d3241d41ec59d86e8c9c8dda8b8257e92f90e5bda27992ba88569fad` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-negative.json` | `91731c1e226c978572e60fd0390a54f7d5e2f512c8f6290ca85571a480b0dbae` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-positive.json` | `22cb49a3fc96fb388a2d892565847e8176eaae8a5c15cd73f2a69c6dff5ab6b7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-negative.json` | `0f0442434cba05c530d47fbae9864cfc972fd3e49e2d0d7e18693b7286db86db` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-positive.json` | `2e5a31b2d5f461b40e034852c6961075205c9a0638326e6c7f824c3b3301a633` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-negative.json` | `66fc911b3699002fa53c4f4769eec303b55f5c397153883bb77faf3c8b53e8fd` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-positive.json` | `9a2967752953d75721e977ccc5813e4ecfbd918ebc6e82eab81203cd8731a50e` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-negative.json` | `07a049ccb55774a3531d06f740f2e4388177728aad16c36eca9dfdac40863896` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-positive.json` | `bebddc142110ddc294fc2f326b2c3ec6cb92d0222d6767f7a21fbca2ff9d8a9a` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-negative.json` | `4913cced37ebaa9bc99cb6d557eef178f3e64a6a7230714a644167d2f515365e` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-positive.json` | `dc84a7fb841e3890d731f687206f3c33207e9951ebadabc2b0c76f9b53a15645` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-negative.json` | `4514ff6360555917c3dfea5e5f8311c46370748fc63f93ddb08c229633d3d27b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-positive.json` | `5c5acd4333c89ffe244fb585d0609f490e8ec6ad5d2e8a62df243552680a1aaf` |
