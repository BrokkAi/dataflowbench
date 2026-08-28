# Scorecard `semgrep-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-javascript-modeling`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0`, adapter version `0.1.0`, configuration `51a89f8648c6b87fb33259285ebee7b7de332f213ea00cd6e0accb737ba62e3c`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-modeling.json` (`sha256:c11bf5343af35301963d064a90207ee142e06b4f5664fcdba88cedb2aa64904c`, normalized `sha256:c11bf5343af35301963d064a90207ee142e06b4f5664fcdba88cedb2aa64904c`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `9e4d04b25e73fd3ec1e026bc7b2453ec7139e89c75d386a6fb47af5210ddca1b` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `d8f6a50bc6d38f8b0d1a3fd0bab122e75e961676da0c5ae62a3f40732ef88404` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `fd803f5182da3dfdb35c37c395bd5b80f5c0478bc8aeba60cf80ce2fc4c0b81a` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `2556343e3b31d8b528f7498500128c813654e63d620e52f3a04c533da9603ec2` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `987f89e300e4fc30a5b577435c909607d8bdf81c7e43c3689e95c6f23581583c` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `b5b13d32de3504d3bf137b7231f9be6db155f78accb7f5b0802e2ea642d9226e` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `7686d9d31cb83742a1e67887a3408e0a8dc798fb983e35fec3d9570c2c9345da` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `aa09dc4ce995110ee9e988d4c8dec7e7bdafccfb7fd45b6200497f3abd9b6e41` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `b23c32e79cd96ce37f36ce25f57d2415074571c008ef24cfbd798fc7b3c53274` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `8f5147646e09d0da0978169f6c4b69d01717aa7ac0e7203d2b668228a2609f07` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `382efeb1021aaa170058e0d9b4b69b9734e791ad2f3b8b24600b50ca2ad55366` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `6c4a7063f4d12c027b998fd77e015b52d33ff141a235dee4d27ce581c0dcd94f` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `c9134025e53a8a0571fa0c5000d1953db8c64dd107c4e193a3e21c1d46061eca` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `be8664c4c5d84965e127181ff4e3ea5d7a3531605ccbc8c45c9e9430abfd9436` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative-unsupported.json` | `f5bb6492c0ccc5d984c7c8eb8be8ca6983223a3716211b912edeb9fbef56907a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive-unsupported.json` | `db18aa96097d128b3aba5a532ab928238bdd7e1c2b58f27608777e09cb37ca47` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `66072f67a0c8de9060d532317dccfde97433c46581b3590018003b33db81fe4c` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `8e72d9b42641d1f2513b6053cdead4ff7d51bcd0715876086fe04e7277a0c8f9` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `bf8a6651a6ccc5cd34da3eb090ca7fe78a96abadbdf26511035ce572d0f8cdeb` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `bd3aaa328aaf68ae55c7ee5bffd954705de709586b43d251ed10e9ce90b6ff3a` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `f7c989c221fa78f85a3c8542ee20fb6c6568ee18a2c0a65a31baab5cd70e8a90` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `f8554bdeb1a11368650f8d913174fba158044240f276fdb3e517a940413a6241` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `0d2b1fc7301174574e43907152c17a1b129439dc3d320e16c3c49ddba2866f91` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `2632c9876632c2850e999d72990db0a4bf62e51ef07bc047c1744db13b07da36` |
