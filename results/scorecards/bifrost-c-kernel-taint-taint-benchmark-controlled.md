# Scorecard `bifrost-c-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-c-kernel`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69`, adapter version `0.1.0`, configuration `345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-c-kernel.json` (`sha256:12b612376f2f3b5b0e4413fbe0a0f86b5abe1c9f445cf7a89969179c1817480a`, normalized `sha256:12b612376f2f3b5b0e4413fbe0a0f86b5abe1c9f445cf7a89969179c1817480a`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `c`, tier `core`

Outcome coverage: `reached` 21, `not-reached` 21, `inconclusive` 14, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 2 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 4 | 0 | 0 | 4 | 6 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 6 | 0 | 0 | 6 | 6 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 8 | 0 | 0 | 8 | 12 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 2 | 0 | 0 | 2 | 6 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 14 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `417f4c68170055bece096820fcf1f8cb8d67bd9b2fe73826593c489982eb0ff9` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `c15f559bb237665a411b334c93814fce9c1c0e2aced57b03bbd12f4845190c8b` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-argument-position-negative.json` | `37ddeadae71bb9388b714fd8832b8f5a570dbf0008dc8b239343d43bc2959b76` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-argument-position-positive.json` | `e31f2d7bbcc9c167a3e995bc70f56288cf917e005a6e40940ea59b18af934ac8` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-expression-negative.json` | `3cd041ebca29d2b03b80d779a5c576be85dae670739da1a10c626b8b8bba9a6b` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-expression-positive.json` | `af0096f308b2e1528fd48b463ed5fc66530dbeca24f1edeefa11aef105ad127d` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-array-element-negative.json` | `aa2c06254ed1a894fde485f776610ea36741c801faac9dc90e4c831e016f550a` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-array-element-positive.json` | `e29f1e89e0f487641c0aeae205cdd4bc3d4f197eaefbcefe2cab22367851239a` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-branch-join-negative.json` | `f642ab55a76561ccd216b86d6a54127d3f089fa5bb55afe8dba7a294dabc89be` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-branch-join-positive.json` | `a192e09cb3478a0f97865c7fbaa58041f1c42946ccbb9e9b4db20037639d5e7c` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-call-context-negative.json` | `5e933e3d88ff5ac0a1fa1b6ce663e63fa4028f406376de59170766bf7897db86` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-call-context-positive.json` | `d77912a1248c54ddc2d325da13b966da510f0d70b661f3792d77dc710a00ef76` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-negative.json` | `5cc1fd5eac3c80f2b3c440a76c5a1a10a7084e929ecede298d50d85ae9081d47` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-positive.json` | `d758286638b0672ed51e7ed0bbcada63a6601bac9bcc0ccc13408fd889299391` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-negative.json` | `17cae9829cdf83afac9abc0a1cf62828557251a31812f7694f0a1d01a24d0ad9` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-positive.json` | `bbe7d4a0c5fc1b07b2982f14c226b42066c0ed5ed21f483a819620cbe0179638` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-negative.json` | `f00561f869b0ad869ed14461b30c3f12e7dc45538687f917de0d411c957c6f3c` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-positive.json` | `b4ab3c95de39ee296b48d0e8d6cc5d9e734895b9a7af6a46688ff0e24c823074` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-negative.json` | `0b713309c102d2808a7e3c0bd2d57bc57f84e53162cab24e21ca816b59e3bb50` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-positive.json` | `6fdaf25ec7a341cbc9ebb0df2bdf7703f49804a8d394988c3539ca19666ff8c2` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-element-object-negative.json` | `e47eac4848db88203485e5921ccfae3cb59819e0e4e70c73d57abf5bb4337211` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-element-object-positive.json` | `d33a48cafecd238ac129cda355e7ee419bf02b67bc6c0d9679a51d012bb4e33d` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-function-field-negative.json` | `56223637d2a6abe45688082c26864a5a1ab9a189fb0dd877977e163e0dc3cf03` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-function-field-positive.json` | `d690db2b65022ed548cd460e71b6cde25f706aaae73a4c8943e79e7817d556ef` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-negative.json` | `407d621e755bbf37e5b035b9bb8fea4329f2530d9311392797cf7794a651a149` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-positive.json` | `5d475de697928e615522091eea64e05a7d1c4b912d42a3e26ccfee6b79bd20a1` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-mutual-recursive-transform-negative.json` | `9bae5e361a956e84ac453f36c8996f2a8991e929afcccdebb295151f31c1ec94` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-mutual-recursive-transform-positive.json` | `c23a605af3db08d032bc20852a7e75be21676f99fb9df41d2470b0b4ef31fb9e` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-negative.json` | `e420752976b34119e06fd649000ef196237be2213637676739d4d98f68b55c35` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-positive.json` | `7eb1ca31e8f0bba6646f7fd3e16617e38d13d92af4e38a9142e9d855d52bb549` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-callback-transform-negative.json` | `54c29233780dbfa3efb58637ebf4e119cac359476aae0b66681e9c11e85a2c84` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-callback-transform-positive.json` | `06a2023ad3cc360975057038284434ca3e6fe0a9b0c2d0f1412d261b37d51f46` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-negative.json` | `ad9a8add9f1240fc8fe5f27e05e33e52bd72ac611afb8507b217205ef7215668` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-positive.json` | `d67e84b7b4826000d27d7bf7c932ee203c693f959fe0353a66d34f4bec1f72d6` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-heap-unwind-negative.json` | `e6699f2f62e295e28d4ee59a5d54ad0bdd8dab0a69b56356803472af60de9f89` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-heap-unwind-positive.json` | `44c1cb4903a952692dd18ed14a0f66778bbcfc232abcdff0b2c8605dfd58ecc4` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-payload-transform-negative.json` | `51710ba674be7640f1a0c532e918323934c619805a468bc55a21c4e50a397479` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-recursive-payload-transform-positive.json` | `5e9863ce53cd4d8a281b89a970849d3c1f02a15b768dba0664c4df1925dd9486` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-direct-negative.json` | `3091b7f4db8fd56d537cc35901017b05e5424a0aa5f94a12c9122d07bea39f14` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-direct-positive.json` | `37553800d3022a811763a39b13e3b34cbea1f5d97489ac9f6d2003ec2816897d` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `9b5272beaec1897d8eadbb71b4a488b96579b3d1d72832100963b5b7b6aedd59` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `0c8cc9f982e7f4f253ab96a0f8e9b2145bb2026a342f4e143e3abcb09ef5fe48` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-local-chain-negative.json` | `739c754f44895c15df9b1d828d6ee907c7ddb6051a76a16fae50bbae4f21f885` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-local-chain-positive.json` | `806049a912d991b020c119a83ec61b47a44169c769394418e17c32c09d193926` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `2ac038c1737db267b4fc96496e4cd0dad40a10f3205c9303420984ddd8675e25` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `8dd304cbd6869eaf6a4187bbf50e0773e4fc7641a375d93373e85bda360313c8` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-negative.json` | `8f57dc2c93df4b8bcac5a516a129d5429fee1eb0b13d5e4601bb711b091220f0` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-positive.json` | `19945b8a877bf5da69ec684b72c7811de700658f77fb4c9603f94c5b29daf598` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-object-separation-negative.json` | `0d9f5020317c34ccbdca4821346ab3b8fbf0dcbcc44e7f6755414cfdc252c759` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-object-separation-positive.json` | `23ed1e4b6e6d4aadde8c7f6556aa04e4b70d269874c0e1c6066a88c54abc3111` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `205d86bcd169277f587feeee48b04e0dd60a88939ba99634bc08d290d29b4afa` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `05cf703e947f9d35e76424a57d8ac46c4bd0aff86c9770131c9c9d3c3b5d2645` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `a3898c1c6b88decffbed55486df88950ca191d0697440ddd07b1caa89e33852c` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `6429fdb320696be86718aecf0dbf93efcb7a5d4c8ad3a9bf9b2708ea89fa54fb` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-negative.json` | `078b2bbb0bff3c35e9de1029a2ef8e102ffb1de4517c2e7f56cb20147a55c82d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-positive.json` | `293a148e46da06234279d07a5fd30f3ac4297019f1ab112f42cfc6718095d4ef` |

## Language `c`, tier `language-extension`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 1, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-error-code-return-positive.json` | `d4ee4180db1d248c65dcab81683a69681f09e2e8770d7698a8c252ce5cbe3e7f` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-c-kernel/dfb-taint-c-goto-cleanup-positive.json` | `32aab6eb5d879eca657574e3b53b18982517e33e85e9286fc4b4be526bbd0bbc` |
