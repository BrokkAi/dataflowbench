# Scorecard `codeql-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-javascript-modeling`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `50f4a31741fd93420f8bdad4cbdea9f07dacda897641e12fdcdcdc8d7810e910`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-modeling.json` (`sha256:acd4495aadbcfd2f9ba2c9ef5f37992283f9981365ad63b28862c8eb6029bad9`, normalized `sha256:acd4495aadbcfd2f9ba2c9ef5f37992283f9981365ad63b28862c8eb6029bad9`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 12, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.sarif.json` | `fbb4ae9766a83ea0714674d401604fe7e2627496fb45b3f61a0b1dcbbdd6e01e` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.sarif.json` | `84bbfeb38bb89a9afc046444a34fa5d05ae8816f49f70da9947dcbc8578628ea` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.sarif.json` | `d0ad1b5a9f84ddaeebca30cc8556dbef8b31a4b6e21f034c434a81b6773c9473` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.sarif.json` | `4408b3480883c9b9d514974bc26d619bf5c85c8943ae43f8ff019f48937f2d35` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.sarif.json` | `d8341b2da81fe6b2d865972035c67650f5ff6067fac7147d64b292d3b96e1207` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.sarif.json` | `c6923481c1c68a58427a3b94b7188788e81b1f4f535638f9739f19d0dd8ca025` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.sarif.json` | `0ae964e277920cd691fcf51820a87b38377aab7ecf587f89a5b8160499e7a0f9` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.sarif.json` | `e92bb579567a800b1566bb6bb33b929108da2aa324d19e1eea2822555ef11f4a` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative.sarif.json` | `b9b4025a4e7bab85f2fe0b3ec03ee50616038116b6cfe5bd825b165779b125e7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive.sarif.json` | `eeabcb1caaef47cc3e9328a7e56114c34993bbf91a05dcc8d3460fa821617a0d` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative.sarif.json` | `0ba2f0f2d642b147f6630e1fca1fb20e0a64bf7de2ed093e63e1d87528253ec4` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive.sarif.json` | `5f6a68e3fc65117ff2a423e331a95b927d4f4fa2e1f768e606e0bd78d7e38ba0` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.sarif.json` | `09b6ed5e4cdcbbe09bd67b80c3f0727e2e183fe8569d10efdc0d827eb90b48ef` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.sarif.json` | `fab56c8c923b10afe4752c367a207a9a11a76836eab4347dff8005d2475712e5` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.sarif.json` | `0193b8d9756740be215143eb04c2fd77847f7444db232c92810a4f4ceb6af373` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.sarif.json` | `fecd32042460f2d797cea931213bf439a35aa7495262e706dca92762bab3775f` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.sarif.json` | `761fa544bb58c82f457e6b3ad0a27cfd79a49d3635210fd495befbe3f1163104` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.sarif.json` | `fe23509d3c0cfc58ac5a5a50f52da4316311e9123cbb965607110faa7aab75a2` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.sarif.json` | `2745d0a25070b0fa496fe94c3191b5a1cf306092386b7863e1f0e058a9028daf` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.sarif.json` | `4ff5220ec79e74878134e8d123253e429ec9828c260dccbdb3bf71aea1ed6f17` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-negative.sarif.json` | `453867e2f9775b8356f9795b1a75086ac090ea743730ffcb92d3c672888fd729` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-positive.sarif.json` | `879ee7ce1dd865075601c7254e98da0e1eabe0554d19933d50b896535a43fbe0` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-negative.sarif.json` | `b4f0d3e808d1a122d44d10438e38326435e11ebe638cabc806b7cf439fd4200a` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-positive.sarif.json` | `5c90459ba3f6b12abf84fbaf29c994ba4664a2776ad8ca71edfcff7cbba9b8e1` |
