# Scorecard `codeql-python-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-python-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `f97f0198f19f2d1d8630b48ff5d30d947e9f83b940de38af425076cf73e82230`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-kernel.json` (`sha256:a34862d20f12280b7836a3016cc30a3ae7e621d016a14ad5195df86dee2250d6`, normalized `sha256:a34862d20f12280b7836a3016cc30a3ae7e621d016a14ad5195df86dee2250d6`). Generated from freeze manifest `reports/freeze.json` (`sha256:c8ba343f2db9a8c1cac5570a414bf497c85bbe11d29730639575c9ba3bb70912`).

## Language `python`, tier `core`

Outcome coverage: `reached` 14, `not-reached` 18, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 2 | 3 | 0 | 5 | 0 | 0 | 0 | 40.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 1 | 1 | 7 | 0 | 0 | 0 | 87.5% | 12.5% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |

Macro-average over semantic dimensions: TPR 72.2%, FPR 9.9%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-alias-propagation-negative.sarif.json` | `7740b055911b9152cbf23562c886f4ec2039ffbab9498e4a9751d69a7246a620` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-alias-propagation-positive.sarif.json` | `b6c06f5a9435c45c3ab44b5f5b98c51ac9cabbbae5d00ca56fc2173307640740` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-argument-position-negative.sarif.json` | `7bccd62ff3d54c7bf6a491d7a550bcc4b81541d19037b018602d38838aba1640` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-argument-position-positive.sarif.json` | `6a791ccdc0c204fef017d473b8661b6f457c78843b807e1cdf0eddf45f533d2c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-arithmetic-expression-negative.sarif.json` | `d5f966618db08741d1fac7384523af94cc3eb9605f008781607b6aceba74f430` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-arithmetic-expression-positive.sarif.json` | `2ea91de80058fdfa0c684b80587c043b91bba6b8eb9e75790eb9b30d4acddb9d` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-array-element-negative.sarif.json` | `f80cd057a453cdd99adddcb00afe829a17e33341b1492cd712c6e00c3fece2ea` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-array-element-positive.sarif.json` | `ec1ff55586d91b4647827f1dad533d8a1b3a0012037c8499f040ca48ecab1fe8` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-branch-join-negative.sarif.json` | `227677827cb90f76f38f5ab1cb83d036092dcd80f7610d488731a3a19351a305` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-branch-join-positive.sarif.json` | `3ef8ac1c409deea71e17032d0c0bb73f5f24129494af823d5796487271cf05c3` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-call-context-negative.sarif.json` | `76559104105633ef85c58ae510071d851554234e0d718e91949ad6c39c6f7b36` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-call-context-positive.sarif.json` | `fdc7349dce9bd77f910c26f3de41aa8cf7941fc61d2ceafe8fb44a6c9cdd7731` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-direct-negative.sarif.json` | `8e880f7edc920b3b4bbd9e18d69368b9ee51f6f14d9db355871bf5ecbac859f3` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-direct-positive.sarif.json` | `480b966b2af2266fd837c7c8f2dc6754ab80c22f483027a786e340f6eb55a2d0` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-exception-catch-negative.sarif.json` | `15bc5ec8583e4615dc7b41378b3bbc16806d62e4cd1bb4cfb6154ec212f6f694` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-exception-catch-positive.sarif.json` | `7dd0973561947b8714ab72cbac7e0744627c981996287af9b0e8db88fe0bcd8b` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-infeasible-branch-negative.sarif.json` | `15a0f7a71110f3e9980ef20a1c0f119b0600cad7751c8aa38b0697589b89f9f3` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-infeasible-branch-positive.sarif.json` | `37e3384e7f6106acf27714cd680923bccfec223e4cf8f54b4eac5a8dfe54ed20` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-local-chain-negative.sarif.json` | `fcb8949a9cc58c0117b05c3df951b7e49244c14847e985a4eebcde0695b3a699` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-local-chain-positive.sarif.json` | `17ae05d9a1b1a3546a3c7d144a629af58a8e49e8e68fb810c8e5995e8bdea0c2` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-local-overwrite-negative.sarif.json` | `d7538291dd5b6dab3d4d668471af48dfaba5b573ac3cb91bedab17a065820382` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-local-overwrite-positive.sarif.json` | `fb78edeeed2d4111d3a31efd913c43a513a1a3826d906ff6a5f2b457c137767d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-loop-carried-negative.sarif.json` | `4b6288c9f51d628961abdf5c46ba9475538094517395dd7346f0197179f0664a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-loop-carried-positive.sarif.json` | `0296643aedece05b2fb33895f69649302e48f6faaf4932bd1992b2b22e6d9583` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-object-separation-negative.sarif.json` | `563ff586931668616b127173aa0859e6995c123491a228c6139c4b727c940ed3` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-object-separation-positive.sarif.json` | `28cee08f2affad0c6ec030aaad739d44e20f14ded0d3bfc37845fcbafd769d4d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-one-hop-negative.sarif.json` | `761ff1db2ba10cb17715abedc82be20ab6c109ce689a352fcd457f6f076e5a47` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-one-hop-positive.sarif.json` | `47b03362e9e93da727a0b995392eb11172d2d255e3d84a6137aca75dc63dffcd` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-two-hop-negative.sarif.json` | `fe2a6844c2491c5448480b25232666a8b6c7ac1ffd4c61ee6decf0ffd98c29cb` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-two-hop-positive.sarif.json` | `bdf224d3a2630caf768ce11349ebe9a60fba40b9a648e6847a1c3d56f29c9dcd` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-same-object-field-negative.sarif.json` | `476f9d96f3f528d1bb962652d8af995c7a1a7a49e15e87be76546183c0d7b987` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-same-object-field-positive.sarif.json` | `35d9310bcae726717d9b87046b1c6e5152dc02bb88debfd2717a949159a644d0` |
