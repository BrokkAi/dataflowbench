# Scorecard `pysa-python-modeling-taint-taint-benchmark-controlled`

Adapter `pysa-python-modeling`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.4.0 pyrefly-sha256:2076955b92a092dbe1ffb751fc4c92b904a7391269c591d6e489cddd2fbe88d2`, adapter version `0.1.0`, configuration `b6431f4bca19dcf1117b6c1fcfc4f779cd61b13c6b50db7bb0cd4539b0f11ffe`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/pysa-python-modeling.json` (`sha256:6bbbf5f10f8ab78d749a00f604de0450e35cbebe82d3f4edeb3853306d758cfd`, normalized `sha256:6bbbf5f10f8ab78d749a00f604de0450e35cbebe82d3f4edeb3853306d758cfd`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 10, `not-reached` 10, `inconclusive` 0, `unsupported` 4, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 4 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `69087e8ec95dcb9e830792db8b81c14a0eb0ba23d1a4f41c450b0092bfe52bd8` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `98c9a73ea4129ccf8a981b8fd6eea1c8b2a91ad2f360adad8dcc22077228367e` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `546ca6dbc89dc0f9d6da31c7fb42bfc54d5e322925554a567fab5b026e78ff7f` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `a0913d130ca634e3340502992ef37c0cc98ebb89a3929d49e3031d23f07b2388` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `e86d82f582d4f5b94137c4a30787e0f828f18f0fe2ce9106a5d5d00ce547d1a9` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `7ac9d51820766311695f94809af9f73802adc74742383594b4c015fb1da4c5e8` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `b40390d2fb50bc95556ad655bef53dca340ead985abd21305e0e288ac1c459ea` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `23ccb541525f6cb7b80b484a498336fbe59effb3703f73cb494f39075f0e6ad0` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-opaque-propagator-negative.json` | `6a2c863d9fc3b4ba112a506c8dc0de3e6995c814f8233f7162eba78c7bf7e4ca` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-opaque-propagator-positive.json` | `9c5f0584c8c3066d53b18755bcb1798f4676aa3f2c701343e9af1138ea192f14` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-propagator-position-negative.json` | `bcbb7030a8516b2b304d66bf032d1b6bc5ad7629f1f09f70fa7c502a0b46caf9` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-propagator-position-positive.json` | `4f3c828d4959919a5d85715df59e966898a569448d89c76746e50d6dbf4b1f48` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `e68c5aae4c3efcf014de6f6d81072d19597b518bf3bc25027f48c4836d40fd6d` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `1ee3a36b9bf4521ac01a9db79d9d4af7c1acfb6fe9f796df114f7c492510dfe1` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `c1536f9c7e8817dfc9cf0bf16ee7207947544e2319866b4f40bf957239f30281` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `7962f3478abfdf018113efb44d4f477dc8161e634c61dbc40f3368b1e6b3d20d` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `d1b895f22ded06fc192b729c5d9f0ceaf2c3a30a1766b7e7972f75a1a4e8aba7` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `646150a8defcb116ee42401900d858cdf4f8a51e1d574ec57b5aa86efdaa9ab8` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `930d7cd04b0f2a79f4a3f3107e1f2fdbc31b89337f59adce69f00a49a97ab4b0` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `6d9687741f2826edd98f59ab848772c92d935529bb867c4cc228044557cadc12` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-summary-field-negative.json` | `a4678981bda8bb70632b603d53c60bc10f64e505808eb039b85cce309b213327` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-summary-field-positive.json` | `7e666b2b9e2264c16a7e50b1fb1fd2116e3bea478a33c17e8e90e6cd279e9609` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-summary-through-negative.json` | `489b2d3066ad9edbd810aa1e4491b773d807de42359eb036e7790cf1d6de4ed2` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-modeling/dfb-taint-python-model-summary-through-positive.json` | `b1d404fe45273355cf0c8455c710f42c2858ceec4541c40d4334e7cd475bb905` |
