# Scorecard `bifrost-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-javascript-modeling`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f`, adapter version `0.1.0`, configuration `49d4335a42e6893f0797bdb1735b8ea3fb40f3e554f9086595f6c1254ff31203`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-modeling.json` (`sha256:662d2650e2f14127200a025fbbcea0a2fe8729dc9c7532edf7d18f88bdb12836`, normalized `sha256:662d2650e2f14127200a025fbbcea0a2fe8729dc9c7532edf7d18f88bdb12836`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 2, `not-reached` 2, `inconclusive` 4, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 4 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `30783cc1c712112f2bbac7a5d56f2d99d00c777a42886abf8b509858a9b618ac` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `9421c326c79db281b22c474f56d693ce02144842235789c58f49d717a45b92df` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `b33f66b5626bba4545c1f83313d7c06d4177f71a1cae53be3b4b4efec230d2ba` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `9561d0cf765422b5f15ab0ba1125624cbdd3940433fbf10fd9fb3cfdcfdbb48b` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative-unsupported.json` | `192bf40bd6b7681d8333f4ce480b4b99f08cb2bd6aa0dece43dee93aa90d18c1` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive-unsupported.json` | `4de803b9613873704a638d723fb6224c414a9a31fd4c785898acf67a8729d28b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative-unsupported.json` | `83c50be55909ef6e4a11d0bd69e6104f9cbed6df42e94edf95f06f07fa2e9765` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive-unsupported.json` | `3f5279ed6316097af8cf5ddd137802540710831ea3135e235e62cfc22a431217` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `09361bf0fa94a0d40dd198bc7a3a3388e4137bfa1ac32a7336754a5e9a107ad1` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `a6dd8130191c4b01a9703d28e4d057e6015a8603aa22fd73a754b45c546b4257` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `c572a48b8276a2203cb40e35fe7804138d1c1e47e5f6e846d112f07a01036e31` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `d777eedac78f0a1aa6e3fed39e47ce134d0d3a5958cd9442bcd64107981b51d9` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `beb663356a08c39bb2b28b295f859e0c80d1658b75a81a674155a0ff67390f14` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `885d2ed439bba489225babd44ef4e730e9534a454e2cfd58a89cc81f804e999a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `a2d71e7fc5b9b06d8154623156c412def91e206eaeac92bbfd9e73d33bcf6cb7` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `1d40c612cfb0c3dd3d89b641684adc7df894210fd44dd4378cc717e29fd30723` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `cf87b4fc0d3fe6dd603f1e80312ae2152918ac82eed9dda0c6bb4dca515d9549` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `6341ac363a07ada5e154ef0649449a9fe1701b1b8bdae7542a22ef518ec4090f` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `9ba44143b3bff10509b02376a31b03b71a46cf5e4534567a18d594896d4a2a60` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `3d9d7241b227aafd4bbcb8ea49ba270ac64ae5f197b702be00cf56c46c7a8aaf` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `23a384257f8a5afa88fc43f0cac2df0a93c547f28340f0bf988fdbe1e162b526` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `f3a2059cb4b09a6b40c7d84e34f3b5b091d0058aa535e7726e41991465163aab` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `ab015cd051d866f9ab267ff4a76c7ad913ead7c8fdf37f0de4456840630bb382` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `85e66fbcdd55fd5b84e9382109d5c6af1804c583db467b8817fbb1aefc7d006d` |
