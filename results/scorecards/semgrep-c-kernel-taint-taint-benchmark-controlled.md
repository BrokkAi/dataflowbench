# Scorecard `semgrep-c-kernel-taint-taint-benchmark-controlled`

Adapter `semgrep-c-kernel`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0`, adapter version `0.1.0`, configuration `865d0bd2989f9ddd0b90f2d6675584e86706b109a033d4a1ac00bd21a617b100`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-c-kernel.json` (`sha256:a4c02829e87cd07c478468222fd01e4fa10145ac1ac8ae1f490fa33d9ba3cbd9`, normalized `sha256:a4c02829e87cd07c478468222fd01e4fa10145ac1ac8ae1f490fa33d9ba3cbd9`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-alias-propagation-negative-unsupported.json` | `c401c8d4682f9bb60d1911e337ace09358fdb06eed1c5b77ca01b4e5a3fc722a` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-alias-propagation-positive-unsupported.json` | `4cad0deec7933d47f999bfbc8298d8eab5e429e0860eb310de76c3d511e0ec7c` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-argument-position-negative-unsupported.json` | `d10b40361f25d828e3ceebd895b2707e2329cb80749a3dca333c02eca093b963` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-argument-position-positive-unsupported.json` | `0ce809439d98a122235c927f630debe92ed4275bf9767b1fd3f0f5d8f267e81b` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-expression-negative.json` | `8f89c46033754d34241ff6ae1d6bbf1000086aa582791dd02bdce33c337c5f74` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-expression-positive.json` | `83bbe44f048af04f521d18c494e8d64388328ed833cd592113b54d6d0e3268c3` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-array-element-negative-unsupported.json` | `daadb8492497376f5a8752219f6523b43ebfb99209fc00675364f8ade3206263` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-array-element-positive-unsupported.json` | `e34842d933b123c91821a6bed41a63d55515e625c9e9d6ec000297ccc441576c` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-branch-join-negative.json` | `f8bbe725020a6331d27bd16a85b701b4df7c6ab07a9e1742bf6229a728cf517f` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-branch-join-positive.json` | `1b00558c7c7363552c032600d105b0b887bed9f2fde2724a57e17e993cfa33b9` |
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
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-direct-negative.json` | `f505fa7123754f700d2ea2594f304d26086344a7cd83025c1b582d41e48f732d` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-direct-positive.json` | `15fc58036676ddba369df59da13e02d846c2efb8997b5e71a60221461a16b6c5` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `4f209487e2d3844967d575b0788a49b7290fe13a5d3d7a24cec8f914b3cbbefd` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `1752e95042ac3d724867164b01bc8d3b9bd66305d62fa8589f3ccfe4ad964725` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-chain-negative.json` | `e261acc1a486b15b8544ab509fc8f1d61feea3ec9067bd0a8eb461d4332de643` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-chain-positive.json` | `eda0181c221c229b6699725cb279984607d73a966e7c528297333cbbf8fd1d7e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `63815b02c31b9207d5f554ca83618754117a418eba67c4e6518ea2a359a0379f` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `0167854e33dcb990a69ae5d47273b3004dfe4c2b295f62cbaebb4739438a0434` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-loop-carried-negative.json` | `ac2de61a270686922baded62e27993763f4b338c4492ea50b9c12f53484d920a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-c-kernel/dfb-taint-c-loop-carried-positive.json` | `2985798ff5bcd32c7c0d9076c1d2e4a787565ec93f62e954d29b42582e54e3cf` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-object-separation-negative-unsupported.json` | `20ce69dab214f3eb86cb375834adad41ce185d6a842e0092485ebf42d3ee0e7a` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-object-separation-positive-unsupported.json` | `7a95e8945251e6edebc950cc25552ea8241fc0a503e46c860f9d23ab2cfb6d79` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-one-hop-negative-unsupported.json` | `d5d942949884c402cc96284101dee93d3b9a74e56131f989b99ea1688a8186fa` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-one-hop-positive-unsupported.json` | `318df048c44ee1cdbef9829b87751e836e78324872dfeefa697a29c3d1049e6b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-two-hop-negative-unsupported.json` | `3499826b732de831f38a3152cf34e656f4355e80fee98fb5214eb5f86af85426` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-return-relay-two-hop-positive-unsupported.json` | `5dbf7dca24d4ff27c08de96b073dde41353dfbed4f14addb9142735f64c36c5f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-same-object-field-negative-unsupported.json` | `863e198ceed7756f597700da4c1305ae36709ca53676ed151a96cb93c21553ff` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-c-kernel/dfb-taint-c-same-object-field-positive-unsupported.json` | `49741f60a69ec573a427fb890edd490cef7bb73757d89dff0fb449a39f211291` |
