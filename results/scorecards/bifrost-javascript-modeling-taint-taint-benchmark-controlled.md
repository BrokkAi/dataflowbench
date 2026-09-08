# Scorecard `bifrost-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-javascript-modeling`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `49d4335a42e6893f0797bdb1735b8ea3fb40f3e554f9086595f6c1254ff31203`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-modeling.json` (`sha256:dde4c418f9d0d6a0a3b2f2e70b7838b2a11f28f1682e361d8e63cbb7ff37d54f`, normalized `sha256:dde4c418f9d0d6a0a3b2f2e70b7838b2a11f28f1682e361d8e63cbb7ff37d54f`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `bbb4c2dfd8afca13a12a3f67dcca56b53e8e36b5301f334bd61d7095b18c79d0` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `8af0ee5f42c46d245c788de1925c8a98e22ad7dcb38b73c3719dfe2319982536` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `9812486caeb383876e63c44ce9af121d46b99e181ad9797af0537e79836ff961` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `f68d962bacd942a62e30cc574677072d895e092fa539116754296268e4a8d278` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative-unsupported.json` | `b0bf565e3c64a95662bcad5cfade5d3138a1d3c493bba658dfe9750a4e1b69eb` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive-unsupported.json` | `63dee072a6f06bce2d2b45e131c4c5b7a6cf2ee545c529acd0c52016c56a1d5c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative-unsupported.json` | `a008d5c30d8ffd60277d9b71b1aa6deae2ec8502198a8e8fd7255c5d58711140` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive-unsupported.json` | `32ff91dfcb1cde5e04098bac9ef7854e21274f598e5b9d708a2d245d99acc04b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `944a2300d0f4242ccb5de8746c24efd6e645368e33cdfca6ac4324f61a998618` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `7d925688808d5e96266ed859b597f6e875dd03ed31323832ee92e151b05647f2` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `7ea43be4bc9ede3df46862d3111393f3dc4b7b80a95e6ebe223065a14810bad0` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `4fa815aa98277b47b7991560747880406810916b5cf9dbe8a6d4885492bc9594` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `0e341252c0199054dafb72a75918841e74c57e1cdc546e04d36e5eab04cdb9d8` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `c7c7c9b69a41a2bd3304d556fe9e96bd0b432a1cd4c40b50d5799bb3b8f69e24` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `3c6918f9e3c470900ad1e997ee96ad92ad715e1cf75488786e7cf7cf50f0e69b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `05e42323efad0954148fd43413f71fabacfc2725ed16e8b9b5e776e2279556d2` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `efb166dadaa10e86d9c0bad09c9f577fa6be0fd5f5a33e48a15bd7a815cc3320` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `3fdd8579d339adc6f8f1a77cf97c49c13adf70cc2955d4005a207c6aeb303574` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `e7d08e898f86921c0682901a834d7fa2451dc137a187fb37e48b0e4ab939f026` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `7b748eb9174e20ba4e7c98c64a7be8fc4316f620de4829a40bf3a3012c91402b` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `3a431f0f2fafe89522415f1f04d413c65f0f3210b0b457863a79d31ed6626741` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `23cb1f90bcf35200c0c0c45a658c476e30609f910b3759d18fe8d9674f690d28` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `be14795f2f74b9f9dd6215cd130b9d5da06db52db1ecc7920bbd0408824ef0c3` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `cf7aac6bad6170098d86537872960ab7c645868a3fa77c7b604b3ceabc453db5` |
