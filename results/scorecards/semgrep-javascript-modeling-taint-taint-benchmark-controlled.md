# Scorecard `semgrep-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-javascript-modeling`: `semgrep` `1.175.0` (build `semgrep-oss:1.175.0`, adapter version `0.1.0`, configuration `290c40474a79073ec319cc1b9a265efd100b050a4c238fb048118f63e151d557`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-modeling.json` (`sha256:5745951d82b9dacfb339ecc9aeb44af4975bf1162428b3a3d76cfb3e096739a7`, normalized `sha256:5745951d82b9dacfb339ecc9aeb44af4975bf1162428b3a3d76cfb3e096739a7`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 0, `unsupported` 14, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `ff4cd3c1fc5de2943061366c5cef7a7a61f39a2f3b8f34a8eaff7122982a171f` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `ac2cd786606f141111e4ac1ccc3e6c331f82258c0b4d9c9f65f217c259d9281f` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `878b604f8649eb5fef7654b96b12d99042756e48e2bfcb7eeaafcfbf9c4bd072` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `94ea0860c64d7efe5981fb8b5c163106f377351c1355bada9b9f1b56b33ddfd8` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `b392d4e81a960b3f1e1defff79fa3757a974b0db4bffb23f3d3b5e018fc60522` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `dac236a41f4e7f0fd252844a24808e1238f82120396bc397e8396f75e0471bd6` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `6dc5cc36510fb928d3ef13fe62093bb10448acb5db3d071bc93f8d9ecd44c897` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `b82ea889417b6bf4211bfaffa2986d3bbbab254e6036e68d75a416b98611aea1` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `e0ace6fa182fb7289e187387dce6c7a3de6dbe747d8b89e5829c18bd4feb154c` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `0886faa8f86e2d91d5054b9acd4d28bd5c13093fff5700af83c952a794c7f2f6` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `7e3ea9b760a22339bd8f947df72a30c5d458cd9e2cec113b9295bec96422461e` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `cb0abd6e0dc38dfe93db64c206508177f655259a80f3df099110ec1223d021c3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `6d132618824db1109d9e0a3d7fa63817b1144a9a7fa88e28c5fd936477df7666` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `b16e71e397f95bae543660b39ebaee738f4c6e4b3cea4bb37b0a847c82a6cb97` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative-unsupported.json` | `4761aa428c973d077492389a02ec35948fbfe0685935a50fe652d65ec5b6040a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive-unsupported.json` | `08b71458750f40219dcd68f90e535c9dc4acf1eae9e39e657e6604dca9da87ac` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `7808b4e8d044298964d7a1baa77c9f8ccd1fe9f2d5e00835edce1bc7dc804e13` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `28eee569ffec5addf7627041bdbf085475e9287106a4c4049d40f6c0a5acc95d` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `558f7ee1bc5316354cd7d285df02fb3acb697f6b83fb6156ca60a61d30c21a66` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `29ff609919ef0fa780d8392a42ea2ccaa25f020ea07f8cfec459053ebed5669c` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `f9fded76f13d8452097d4e420a681b9063f867ed838eedfecc01ac635643f04d` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `d73be5b88e73418c06a6316067d6f6e3b1b5ef7b06fdd571106ba3bc26794627` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `dfbfb98f75d6f49d476c5319ae33f1298d92c552e7dcc267a913c183aee8f019` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `1d8596b2f7946728c2c7e621583d50e20e36fc5f96381b379e100a0761828a6a` |
