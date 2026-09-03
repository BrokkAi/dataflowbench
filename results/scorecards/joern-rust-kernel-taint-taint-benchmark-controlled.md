# Scorecard `joern-rust-kernel-taint-taint-benchmark-controlled`

Adapter `joern-rust-kernel`: `joern` `4.0.614` (build `joern-cli:4.0.614`, adapter version `0.1.0`, configuration `ab10e81860305e492a930e2c2691873b23be25e97e5b354ca785058e09a20025`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-rust-kernel.json` (`sha256:465269d73a072957b318fdac73768d5e4fb538ff9f3e31c007f88f6c96bcf055`, normalized `sha256:465269d73a072957b318fdac73768d5e4fb538ff9f3e31c007f88f6c96bcf055`). Generated from freeze manifest `reports/freeze.json` (`sha256:e3fbcae1eaf3f49192f7156616c4b2149893a8470e03ff445fcd1d5f984f9e5c`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 20, `not-reached` 34, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 2 | 0 | 5 | 0 | 0 | 0 | 60.0% | 0.0% |
| `dynamic-dispatch` | 0 | 5 | 0 | 5 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 5 | 3 | 0 | 8 | 0 | 0 | 0 | 62.5% | 0.0% |
| `interprocedural-flow` | 6 | 4 | 0 | 10 | 0 | 0 | 0 | 60.0% | 0.0% |
| `local-flow` | 7 | 0 | 2 | 5 | 0 | 0 | 0 | 100.0% | 28.6% |
| `object-sensitivity` | 3 | 3 | 0 | 6 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 100.0% | 66.7% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 70.3%, FPR 14.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `c3232edc9398281cba19d6ab675c2d70120b5caac77f80db6b6f381087692ba6` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `27bb302d7b7bfe21116e21bfe387ea7563088fb2a2544a112e65c9dbdbeae686` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `77488951fea0009eedfb1e5d828ddbd1e961a5f3590fb7013653376c79377e07` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `b3925b95189e65d7eb0e20ac5de5761897d5a078814fc312fbdc0769b8885911` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-expression-negative.json` | `5d0fac5af24d6de9c4ae83cb9b32b524fff5b92ff9ba4af2ff2a7cb4f1c59f5e` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-expression-positive.json` | `cf2df1e5fbfdec749d026d5d55359e065451afb4953cdc11ce146c818199f19c` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-array-element-negative.json` | `027423dd027388d6598af275a3862dbee62c7e59308776189648288c40baffc8` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-array-element-positive.json` | `f276fcb0a7f0f2297a98c99e4b39ebcb32c112890e65d97a88fcc0c87c273dcd` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `303a2c6caf8fdbc0fbd5b87ab94ecf1ff66cc89294b7a79632519fc39149f6b4` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `0bc0cef91b400c64b190b835004ae1d70cdb06156f56c07bad9f80620af78ea0` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-call-context-negative.json` | `38b99f464d3c73d429dbdabd204c9be80f74cb3e0aec8c272b9c084f4531fbda` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-call-context-positive.json` | `217a58b7463133f3b86f9c39e62986046fd38a22212bebd6e84ed58451d47816` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.json` | `8d618ac6da0f2b551f52cf2edd9fa6d0eba5fe26ba8bcb81a50df3258c1f25f4` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.json` | `68a78cc2f1a23d21ae2427a9e4b7bed5f2cb1f6cd154704cb2d335c031423ba0` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-callback-registration-negative.json` | `a44366f12f6af63940d0fae872948134dc2c62ab33e54d7bf4d6b881f96b0e7c` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-callback-registration-positive.json` | `ad8d2f81bdf28de9053f490005255eadc8ab96a1c509be152581628e166c6045` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-closure-capture-negative.json` | `3b28e177325def7b117082814a54825ee998610ce97b565cb0e40a91989f113f` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-closure-capture-positive.json` | `591c59cea89a2b07cc5f2339f3dee428e4a22b63cedd731a4864cca4cab93af2` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-computed-property-negative.json` | `f267102061fbf3ccc24f3fe299a86013a418e9cc972c119d35c2b75ecba3112b` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-computed-property-positive.json` | `f10112479499e83e846c061ced495adc46b31227d0c49f40d49be26ec5c35d3a` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.json` | `56922544f2e4485aefd013d48d9388862b1fe8da93f857488dbd079a56905a66` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.json` | `59842a0a40e56f6743c16e09d1d35a57323e92b7ac6a06496448d5cca1aa5aa2` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.json` | `7ff1b066d5f05afad42e6f92c711ce8f233e0a667ce31e0389a88164bd223808` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.json` | `02c3216bdb6da98a4267740feb59f30d82935d68d59cae7a5180b22fa4e12adc` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-dispatch-table-negative.json` | `868f41607061bb3cd89dd0e1c7ae3d35ff24ce38b8d85d70f283ab8d5dc6f210` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-dispatch-table-positive.json` | `6ab6f65f6bfabce7b249a3a6771c90e842be10e210376d2cb981dfccd53a4169` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-element-object-negative.json` | `8ad46ce8db4ac31f073da577d98bb8fa1e7faeafbedaebd6812b05701a5a9d47` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-element-object-positive.json` | `7d5230fa6c094b9a9114cc64d1200b879e14c5b437e98b289ebbc2d515a8ca9d` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-function-field-negative.json` | `69775ee3c6fd5f06c0d2ccd4723bb358deab6909b682db261d04469a03262abf` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-function-field-positive.json` | `cf74d184c4aeb6853986ea5d970c93b8ce9b8ce9456a71901a3b2545c07f1ba5` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-map-iteration-negative.json` | `b65e1176d7aa47990be58a6a24ba518ae795dc525b6314e8b723165d7eb8ec2c` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-map-iteration-positive.json` | `9bdb46a82f9aed64f6eb8ca8c8884ce46627af5f432138e18574c1e32bcf1554` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-nested-access-path-negative.json` | `baf1f084bb4c6b7ee9d1eb6477566bbec9a4c91f1392855547c404df06873df0` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-nested-access-path-positive.json` | `af6456fb6a433f231b4e1b3de5f6766757ddf949c5a8616fb93b2383d737a4fd` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-recursive-carry-negative.json` | `f589dac7c7fa505bf7c345d66af29fcff2ea079c129b190f48b920a8a3aeb6ff` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-recursive-carry-positive.json` | `cc68aae43ca76c2116e55f71fcac376b2efbb1e8d85a03818400677941e3a1ac` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-direct-negative.json` | `74155b5736f40139e35827e6d919460d58ea5855eb8d03dc951d967f8a9b85f4` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-direct-positive.json` | `e6bd86f9d349ddf488e184721441cef939fe91bfbe487f878945149c49b8c8b1` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `72e2949d3c4c902c31e02121653f9385dfc3bf084011ba3ab71d11d7e9f89f51` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `985df1975206458253a297817c0f2bb28cd672113b9f6be9fa02a3cdfb92ed4d` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `02493ce1df9fe723a8cc26442737546cfbf52ce7f0d852ed3c1fdebbd8de824d` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `81a8a49da92f7914949b564f0e0fb35130218df5b0864febffa8c3f250ba2865` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `265a9b1b152b9c9cea0df9572a8ad4a24a86befa89fbc6797bc02512c0773132` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `0cdd7d19ac51fbdd28bb870202f67c20f4ce643dbb43e09d0ec0204482cf9e3d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `d25100f224a636d6e597097cfc21defdd9f549ecb6fb032e5943469e9cb3f45d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `9cac77045c87810d5ded9e1b5823be63017e44a78af65715249ad6c71c0818ca` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `6ec8e92e24a7061c2d6a5199cb289b0d2736fc4c7c18f12a377336ba80211768` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `93ee2397cf48003ff1aab0dce90f6c605c2265adb3f2af1a7a2e6cdbe85d1616` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `2f6086c6dfffd1e3fdd87779ada9ac456dbf89879f465953365e5565d90bdc1d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `702114073c4d6f855e40aca4c2f203aa3eeee42f333e3ea0c3a81b5428d9f691` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `8a89288b611624d3f951d18b255af6b6eaed973ad0bc5482ce008019f84e12e2` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `4a2cd02366d69e69a2bda9e5c73f14974fab7092b2b1c8230c5bf367ffc0e896` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-rust-kernel/dfb-taint-rust-same-object-field-negative.json` | `b13565dd1284c58a9f6a76c1b9eb83a78265692053d8f0219a992f97bceab870` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/joern-rust-kernel/dfb-taint-rust-same-object-field-positive.json` | `5ec3fb9f4972cdc0a8fd0e2a259f7ff6896c013b1e8593158a77b7657731a749` |
