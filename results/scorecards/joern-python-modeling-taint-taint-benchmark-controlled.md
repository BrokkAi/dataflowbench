# Scorecard `joern-python-modeling-taint-taint-benchmark-controlled`

Adapter `joern-python-modeling`: `joern` `4.0.628` (build `joern-cli:4.0.628`, adapter version `0.1.0`, configuration `f7f9d9d53572b098556aa86d16b3e9a0b3e9c7a4226526090bb03fd61bbf1eb8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-modeling.json` (`sha256:1e09345fcf8c82e04eaf58f4d4c90fa9a5832465299e633317a70cc88b735221`, normalized `sha256:1e09345fcf8c82e04eaf58f4d4c90fa9a5832465299e633317a70cc88b735221`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 10, `inconclusive` 0, `unsupported` 8, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 2 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 2 | 0 | 2 | 0 | 8 | 0 | 0.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 50.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `46720524b40195d30f97fad629e9168341f11825fd2df75ec4bc382f2df46a0f` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `7e4dfb6f9a1f0e07436a9c161dc7567435d6176a5e570138005e8f0479eed562` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `0ae74133e0b45801a72270cde79104ac6366bbfe705dcb2ae8f2c5f38bc16d84` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `90fff9e3f9f07bef54fc9790119d8f469605a35ba91ad3ae62c36bd2f4cb6974` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `0dac096e2660de6b1bb8385f295e00c182a14ea0f4ccd4fdf6e02ec7964c62d6` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `63b0a88829f493c5dc340045494c6de26c9e0af8ff142a161343541b9e8d4a31` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `da5eecea916c07cb8bbb291a4a6950a8824e484b4e3fb80e0d299568cb4cbbf6` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `32f70dc177ccb3f674297ec3a90b6e12f0457d8e8b9eaae8a90509bc499feffc` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `e9075cd2943f108e41c100b5cb34004dda07a0ade956e1087c3478054409adfa` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `e60846266fbf6fcb593f1c6787db1dd8562ab7ad1e8736e2b0b927f68d827289` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `32bec5b6b3da29f21eb86947b0463c099e5fcfe2a642d4fad89c9a24f02754c9` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `0705843048fece7b987696c4041552ae0103914ec11299172106a11a74f99e67` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `3f35186b87a7eb3efbdfb0d771bed0eae7cabaf3b4f78cd968ae9cae64f90341` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `b9008802503d93e044aaceb73bef795c671d8028c6a717d0262c87a95f426577` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `79d6584594014c0bce2b8a5bb2137933fa353d1c288e4ff7cc20ea8b69b46609` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `b689b7634dca6515545e5c34f9bdaa1d0ad68c835596ecc604a56a919313409f` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `23a8f014b9ac5d19e8d391137e758896e870712574a43f3137069c50d72f04e3` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `7be1ad64807bbbc353f66c538843e90c790c44a5733b97e20ab58a120facda74` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `ec761abe0d2f6bb70a2746613e2cdd8c2ea35acffae2ef02caa94269eae4ef69` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `be926a10a86fdcbc40c588a31b760777f6e6995b086279d97d0742f513d46fd6` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `88f75daccb933ac4b1d4bfb38763fd96acf15b6ef8d38f8ba73993781a3b4389` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `1f8b320242e4ce6ed7d36c35975f439eee2daa935ebf1dd5b062dff34211efec` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `3c0103a2aaf519f3833fbcb80665efce187b7cd97f48a6faa38443459737678f` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `d7fa7fcc7bdd4a7a6c16a7e626f5972f50091d12b0f897db30095d1debd238a6` |
