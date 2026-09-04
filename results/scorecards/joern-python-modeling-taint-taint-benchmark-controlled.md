# Scorecard `joern-python-modeling-taint-taint-benchmark-controlled`

Adapter `joern-python-modeling`: `joern` `4.0.617` (build `joern-cli:4.0.617`, adapter version `0.1.0`, configuration `f7f9d9d53572b098556aa86d16b3e9a0b3e9c7a4226526090bb03fd61bbf1eb8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-modeling.json` (`sha256:c21908ad9580dd17301dd3fd090515682b3bdce8f7ab99bd4483498321bf1a50`, normalized `sha256:c21908ad9580dd17301dd3fd090515682b3bdce8f7ab99bd4483498321bf1a50`). Generated from freeze manifest `reports/freeze.json` (`sha256:c543ae4ebd11ed6f3495f4461b5b4bd7c84d0874997f1b62044e9df62817b28b`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `fc4069fdf3761e0bda65f8202dbe434774e9738347fbfa28016ccd422e81645f` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `f4e8628f91dcffadd0eca5e2f3826e3c008b84e3bd1c702f0644d930bdfc5f59` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `44d7eb44845ee844a38aad8f7d44e3f9e23d87df21829178725b4c03372a3625` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `fb3e4854bf6c828de01b903b1de6092bcf64bb74ea0520a6e38d5afd9d4469e9` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `58f9c89a761fdbcfb5333b31f607b8c140772b969f3b07957ef1be9b765ee2d9` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `ae4963cc1bf51e7643901d8caa7992e72730e755484f39791254ba7b7e89ecbe` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `eea1d109a168168d65dc532485e2fd214b40e93a56825e1205616e5aafac0c1c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `2023691f7f895642ec1f83269b77069710309c81c9c64267fce96cd96cc330b5` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `889cee8c5112f4c584bb485357c4d508d0b50091199009fe18ddcbb9b998878d` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `3ee24a810c50bbb1d3b9f0cee4b209372517caf162320953d743041915d846a2` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `541d2c038b9b20926c832ae7a7a66db8636404021f3a9753ce49d2bae5221128` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `47df2def66fda4a99f7732fdace17c27b72e976a02d10ce85919385cbb5103a3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `e2f6d6a6e9455278438be7bfdfd653a94683318e4cd5eedba992366c6469f304` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `7c759872595db72207eab7cf71fdcf8d07468502285f58f44eda252dfd1c5f03` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `77881d327956ae1004521d29cc341b58e411f290abed5287903e0176c9761e1a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `d1dcdeb8cc5cc4635a19c02d9374930e706b744b4729523212539350b211eab1` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `5354ef2be86884cdc6fb688f3091bb5ed18f5f0b408e0e3fec7d138a15a0384d` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `0e57ec9a40e2128e25a5238a567f42ffec5166a14987865e86eaea5fd1a34eb0` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `42937f6247f58843e7b97c2f6b688d665251ad7087601465f3f9924fef923a19` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `0fba38a1a3298f3ad1b6d8004f630e617ea80af4c1dfd155a117c19c6793f653` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `8b8c859e798d64da30d0199e9bf702e4f54096624249ec01045891477d2163b0` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `fb25ce239bd1791dd4e88a2cdc01784f3a9fbfad48d2abf2acb75f7515e57e1f` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `0044376e8ffcc8fcfcb00231b83a02bde7900752618f6b100e481942a215d86b` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `1b8f57da5ce6d1ce3be3a19a6f6b0d1c2662a67c1dbcbaa796e28831b581b97b` |
