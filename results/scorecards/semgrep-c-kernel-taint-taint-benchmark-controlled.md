# Scorecard `semgrep-c-kernel-taint-taint-benchmark-controlled`

Adapter `semgrep-c-kernel`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0`, adapter version `0.1.0`, configuration `865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-c-kernel.json` (`sha256:a75b5f37004166d20de264ee95ba7c6f4905ab0cc9e82c47aeed69ee35f4e4c5`, normalized `sha256:a75b5f37004166d20de264ee95ba7c6f4905ab0cc9e82c47aeed69ee35f4e4c5`). Generated from freeze manifest `reports/freeze.json` (`sha256:91b0008a546e6b782c1b790f174a71ce44e60039239797674eb49ebc6ac6c366`).

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
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-expression-negative.json` | `6cc418942ac968dc01c3e1a6e3356d9927c005231dbb1022095ee265f42b65ab` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-expression-positive.json` | `83097f23872f9d5aaacb32d45abea44a5fbccf4f30d4078570e6ba69d244cdee` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-array-element-negative-unsupported.json` | `daadb8492497376f5a8752219f6523b43ebfb99209fc00675364f8ade3206263` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-array-element-positive-unsupported.json` | `e34842d933b123c91821a6bed41a63d55515e625c9e9d6ec000297ccc441576c` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-branch-join-negative.json` | `b9243e79cdcc054d2bec41152719740caf9d22f21926b106eb13c279824d93c2` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-branch-join-positive.json` | `b6a297ba66202b3a0dc24b53c244065a6987b20ba469c11d45a1972b62ab4a65` |
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
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-direct-negative.json` | `55c36942995e92f62815a9bc287fcb2c90749fac1aacd3e5dfbc6a888779ac28` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-direct-positive.json` | `c729beb3c9c1be525d7e614900283e4d98755300ef9540a3069d042f761494e6` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `1d4dcb766fce0ef32fea574dab8fe76b4baa522b7f3f709b50b88cfc994f6584` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `e8f45ecdd31c84939c586afcec2c3d583339f44ac682e008a24bb4f5c91c5f1c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-chain-negative.json` | `5cf92d92607af0883a7c541014779b71c6d7721dca6b08eb035f62c9e8533ad7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-chain-positive.json` | `7f41c0dba337a7d95eab1e0d192bd2a8f2da70f3fd68fc5039985f9b47561dc0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `362147ef46888fc929e23a98d8209e06bedad110994ecc13f4da6cc905c3bba5` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `57f72b814de90f8ad8bc7723948585137d6c1b7f18233a0c5afae849365763b9` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-loop-carried-negative.json` | `98c12cc2a4ae584a27146b6ca5499a8b38a38eab9f51ae1e99473fa8cf9d552f` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-loop-carried-positive.json` | `8017511d5d7842878a8b5301097c547142538795f62a9bd49be5b3df04ad238b` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-object-separation-negative-unsupported.json` | `20ce69dab214f3eb86cb375834adad41ce185d6a842e0092485ebf42d3ee0e7a` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-object-separation-positive-unsupported.json` | `7a95e8945251e6edebc950cc25552ea8241fc0a503e46c860f9d23ab2cfb6d79` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-one-hop-negative-unsupported.json` | `d5d942949884c402cc96284101dee93d3b9a74e56131f989b99ea1688a8186fa` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-one-hop-positive-unsupported.json` | `318df048c44ee1cdbef9829b87751e836e78324872dfeefa697a29c3d1049e6b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-two-hop-negative-unsupported.json` | `3499826b732de831f38a3152cf34e656f4355e80fee98fb5214eb5f86af85426` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-two-hop-positive-unsupported.json` | `5dbf7dca24d4ff27c08de96b073dde41353dfbed4f14addb9142735f64c36c5f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-same-object-field-negative-unsupported.json` | `863e198ceed7756f597700da4c1305ae36709ca53676ed151a96cb93c21553ff` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-same-object-field-positive-unsupported.json` | `49741f60a69ec573a427fb890edd490cef7bb73757d89dff0fb449a39f211291` |
