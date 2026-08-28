# Scorecard `semgrep-c-kernel-taint-taint-benchmark-controlled`

Adapter `semgrep-c-kernel`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0`, adapter version `0.1.0`, configuration `865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-c-kernel.json` (`sha256:8b1978f8a41803f0341ff7778eabc0fa6665ae97edfb6468883fd93d4b42ae99`, normalized `sha256:8b1978f8a41803f0341ff7778eabc0fa6665ae97edfb6468883fd93d4b42ae99`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `c`, tier `core`

Outcome coverage: `reached` 9, `not-reached` 5, `inconclusive` 0, `unsupported` 34, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 0 | 6 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 16 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 20 | 0 | n/a | n/a |
| `local-flow` | 7 | 0 | 2 | 5 | 0 | 0 | 0 | 100.0% | 28.6% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 10 | 0 | n/a | n/a |
| `path-sensitivity` | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 100.0% | 66.7% |
| `recursion` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 42.9%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-alias-propagation-negative-unsupported.json` | `c401c8d4682f9bb60d1911e337ace09358fdb06eed1c5b77ca01b4e5a3fc722a` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-alias-propagation-positive-unsupported.json` | `4cad0deec7933d47f999bfbc8298d8eab5e429e0860eb310de76c3d511e0ec7c` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-argument-position-negative-unsupported.json` | `d10b40361f25d828e3ceebd895b2707e2329cb80749a3dca333c02eca093b963` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-argument-position-positive-unsupported.json` | `0ce809439d98a122235c927f630debe92ed4275bf9767b1fd3f0f5d8f267e81b` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-expression-negative.json` | `164dcc7ec4e4fe98b8e88ef7a1bb9591184b9b47093081ef61ebf28247ef06af` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-expression-positive.json` | `f3d90aa5076d05e69fab0b68d40f1392177cc2a283df4a24a01255daa7db54ae` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-array-element-negative-unsupported.json` | `daadb8492497376f5a8752219f6523b43ebfb99209fc00675364f8ade3206263` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-array-element-positive-unsupported.json` | `e34842d933b123c91821a6bed41a63d55515e625c9e9d6ec000297ccc441576c` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-branch-join-negative.json` | `76ad0a13c9af9553f01b3c03d2bbc5ad918d018b434dc916cdca09ce937a660e` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-branch-join-positive.json` | `7cba9de88ecee9025f29b8826baeb232009687ae997c5f9be22626adebc9b5a4` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-call-context-negative-unsupported.json` | `3bc51eac7ff4d3d07f082265847fff5aff2a7c0556bdd62518221a7e51d1f47f` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-call-context-positive-unsupported.json` | `a0f6148f2c745d15a43cbb9f92052c1cb288f1630e49b96297fcd22fdd650259` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-callback-registration-negative-unsupported.json` | `ce954d503f16c6ec3555b41c65ef47df696c52314561ce579b056942585da8cc` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-callback-registration-positive-unsupported.json` | `15605f64cc8c917fa3fde6b4b489051b0e4bbafc03db94b38efd56777076334d` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-context-pair-depth2-negative-unsupported.json` | `d5484967afb4e59d4848f318fd58b53238495b67d9d58258eb3336e7fbe1c2fd` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-context-pair-depth2-positive-unsupported.json` | `c7939fa8ee6145dac155689ea958b3467f897c74fc77afe4e5217c53826ae575` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-deep-relay-chain-negative-unsupported.json` | `44788ac8a38600c14189fdd8857cc3ed09b687a56328a882b9403604f44351ff` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-deep-relay-chain-positive-unsupported.json` | `128c4c70e0659c39dde7f278ed487b9c8750a77e3082bc953932519d5f978c14` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-dispatch-table-negative-unsupported.json` | `e6afd79548e136d2bb5d30ec0758a24172032cc32b9c04e7e259be29c6eb1723` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-dispatch-table-positive-unsupported.json` | `42e695dc4d337043634db821b9f96757ef2882560243b8744d0e6d6c8db6e731` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-element-object-negative-unsupported.json` | `bd72b6782cc440b766e8d17d266148450efcc4f48b897bd21af5b2ece36e7615` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-element-object-positive-unsupported.json` | `db4f67fe4ef5133af22a39fa849e73fee560a738a90d7d087501fd8b7c27d779` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-function-field-negative-unsupported.json` | `8e829f8fa946b6f20adec38f79bcff40d84623716dfe135e25cd4c8d20e84996` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-function-field-positive-unsupported.json` | `1687a9f24244cfe8a5b5fc1ac646960b4db35d9438022abc30d2469b623ff5b5` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-map-iteration-negative-unsupported.json` | `6c47b2e88084ae76d9006c2ebcb4696ce7a94d7f6ce19e7f579feb168f3da143` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-map-iteration-positive-unsupported.json` | `ffd37b6acbf4a1766440a506db78b94f6fd911c6237f3a2967c4bcfee6975d34` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-nested-access-path-negative-unsupported.json` | `35e3d568b102ed4e95a9828ad08cfb764817aa84e608e89a1b86e1cf0b5de892` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-nested-access-path-positive-unsupported.json` | `5ecc7b1529c8ed4b294756f3dc39e81872f8b4f82faca3e14e699e372d82a3ae` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-recursive-carry-negative-unsupported.json` | `09c05f27efcf29d1e41b0d62e18510da479b300b3cb0389f2a431e8a223c958e` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-recursive-carry-positive-unsupported.json` | `c2b49cb98d8722b7229373dd8ab977b88469d6c880a28be819ee0697ab9b4f82` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-direct-negative.json` | `95cde27c34cd9598518c5f355052762a81fecdd78007c54a62d0dc6958446988` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-direct-positive.json` | `16acf56e89500f3c562f837910ef60e42f6edd3712aac380c25852f75bf22fdf` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `0f3d048d68f7e92f8f54d687bb153e33774661463f6da57b3088d946dc1d5e9e` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `aac4e4d243f1f8a19a161010add3f43866d7da86a0461bb5d5a5721d51d405b7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-chain-negative.json` | `69035e7aaee4edbe19eff9691db1b36f89f8d3c5063be5a42297d8687aaef956` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-chain-positive.json` | `fe0dd0d9b826b46911fe779b7e456f34940bbcbde7feea5ce9d6c20b9ba99249` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `e3b9e48fdbe76a40c3e56c43832fa5bd0f1e439f37e66288c7197437be809137` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `af1100d6c071f96d6cae1dcef9e1ebb8c2005e19f2b16312f4346736d3257893` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-loop-carried-negative.json` | `cc9147ab1d7e2decacd2e9335f2c738184c2eb4627d778c5098677480f4f50ec` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-loop-carried-positive.json` | `d103fa5aff1c0ba25b030704db9b61760af2d0ddc27f3ddbd175f806069cb076` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-object-separation-negative-unsupported.json` | `20ce69dab214f3eb86cb375834adad41ce185d6a842e0092485ebf42d3ee0e7a` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-object-separation-positive-unsupported.json` | `7a95e8945251e6edebc950cc25552ea8241fc0a503e46c860f9d23ab2cfb6d79` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-one-hop-negative-unsupported.json` | `d5d942949884c402cc96284101dee93d3b9a74e56131f989b99ea1688a8186fa` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-one-hop-positive-unsupported.json` | `318df048c44ee1cdbef9829b87751e836e78324872dfeefa697a29c3d1049e6b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-two-hop-negative-unsupported.json` | `3499826b732de831f38a3152cf34e656f4355e80fee98fb5214eb5f86af85426` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-two-hop-positive-unsupported.json` | `5dbf7dca24d4ff27c08de96b073dde41353dfbed4f14addb9142735f64c36c5f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-same-object-field-negative-unsupported.json` | `863e198ceed7756f597700da4c1305ae36709ca53676ed151a96cb93c21553ff` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-same-object-field-positive-unsupported.json` | `49741f60a69ec573a427fb890edd490cef7bb73757d89dff0fb449a39f211291` |
