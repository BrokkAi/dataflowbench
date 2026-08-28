# Scorecard `joern-python-modeling-taint-taint-benchmark-controlled`

Adapter `joern-python-modeling`: `joern` `4.0.610` (build `joern-cli:4.0.610`, adapter version `0.1.0`, configuration `f7f9d9d53572b098556aa86d16b3e9a0b3e9c7a4226526090bb03fd61bbf1eb8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-modeling.json` (`sha256:6f7ea2ece57faf66668739ec536488c570484e6be96ec35e4a6888ad4447b011`, normalized `sha256:6f7ea2ece57faf66668739ec536488c570484e6be96ec35e4a6888ad4447b011`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `954331416dafcd18b09df71d1cea576a0c332018916a7bb002263716a32db1f0` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `e78acd77092f1bdf339625d3cd98ed0a19a6619cc54b80903e04bdbe06ce23a9` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `7fdef889147ee171aa8a2c10a3f2fa67f693f2177d715007a931a8d281fa849b` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `333ef4b6c1c799986fff43ae77680da30b79161929c3ccf7df6755d9a404b4ac` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `470771f4f1b0870b0c528de7d4205a15eadc9ee23c58d4e39a1adaf606c5737c` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `844ac729bcb67b3aab9592d7f24e614c0918d7145f3f0219b96f8e529ceae7fe` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `860bf1720c52995346f137548a44670b435b6837e4cfb6422d6ad9d672433921` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `4fcd633a5d487d8cc5b222650d6fd5e4b54218eb55383ec9c88bc83bec9997b7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `29dd4e50f654cc6a3239b9c9f8a8b16873458035b16d1cbe7109882d2a7644bf` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `1f2d5816dcd9e959dc053ef5cfe5bd3d3c8c5c3376f0db9e5eb145ec8e695caf` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `13df04c7fdf6c4b10725ffe1c84ff53b2eabb472d38a4b7b333813273946f07f` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `1bcbf88b8ac5b831d48887d99b5b56a882ee66654091d3c14d5496c66dffbb43` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `0819629cb43e6b50d2b573443606d31416e65619adaa49b15da13179bbe7000c` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `e6ad438c496049f598ec5abe93c5989143141b22b4d7d37faf89780c3c5695dd` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `a54e29e7a473d2fa08dffb2de6f16defdb238d63dc62d64de70dc777f56e3008` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `1708b94ee6af41a173dc615ec64c66ac9663db171e07b0687579df0d088d7343` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `9b95db2544e649928853fe97b3f3eb836dc238bbf2a2592428b36d6a44652c12` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `34b80ddee69157ac106a50790e24bb906002ba2019800858df8eccc2f3599b66` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `1464e22748ae6b1eb648976e6257f56647f9bf8f2b83b5a0873255b6d830df5d` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `856e6b897765896e0d6c1f60c7eb09f14cfd5e1826c1723090a09983fbb9e198` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `01d16f4a39158722de4e25bd28a39ed41aab0e96dccdea7e02efdcbb1e9169eb` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `798f6b59bf794550e0ec9d3871337572d8fbe75a2542ec96b71affb16fc60233` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `9e9be70f7c070151c7c362998e3959d553db42a452aa0e35ee2056f3377b75b7` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `76362db2ae801137214207b685c42956cdb5e6adc492ef86819e5981a3fe383c` |
