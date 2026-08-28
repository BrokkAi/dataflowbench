# Scorecard `codeql-python-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-python-modeling`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `cd3c4feeeb3473e72d9c35a582a32d0b65d281d759bf77f9a2e0c0411d3a7262`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-modeling.json` (`sha256:b9a3c13de153d28604d97fac51366f811a3a98dab740395a6eb0efca6811a9e2`, normalized `sha256:b9a3c13de153d28604d97fac51366f811a3a98dab740395a6eb0efca6811a9e2`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `python`, tier `modeling`

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-negative.sarif.json` | `aa8d1d8b843482e2578ad6d14e20e4d721eb20fd7824f54e2f33ccf546843c68` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-positive.sarif.json` | `76ecb9802740f5545a3c23f4e28561318380bad9b075c3cc9b497e95c46bb0a5` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-negative.sarif.json` | `c270f6714fa7a2e7452e1f1c1683fc51e2315b9c7111f832e981f9bce6abc34f` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-positive.sarif.json` | `110f19fa25aa5797b4e2a13a6791194bac5fc6abc0c515c3e4d2d0ad044a7541` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.sarif.json` | `af822c93dea9868e7ebbbbcf949ce75278e98452b2d6f7fb85c84e7952e9e509` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.sarif.json` | `afaa000ac0740660d0d5e6c7668a2dfed76374076a7f442889e5980566b7dc89` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.sarif.json` | `925f512ff820d72bd854e16cf06972c4ef176c4f396f87c86ed6df7afe27c162` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.sarif.json` | `bc58a7540e58a416c420b237f912aff8bcbbafd5838f20b5eaccd6cedecbd9c5` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-negative.sarif.json` | `059340b907405bc66b5ab27c86ea1e69ca76b1d4804d55220d746707105fc4db` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-positive.sarif.json` | `1a3d75677b06743fe87cc9e30fc346acafb636560d681dba24972eea10ef2d59` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-negative.sarif.json` | `10495cb86833aefb5c41b2a33d10f4e5a97cc6b56ed365042eec5d733f7af367` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-positive.sarif.json` | `72c04072f1e13bc6d7cb9e5e144c1b20956bab5027dee34c39066340b2fef4a8` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.sarif.json` | `6d3998415eddc91ef41ef8a3778d0ee36143914a72ff384b04256156bf6191be` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.sarif.json` | `6fa371d19f41f7d17b68bb0689ae19d8c0f0034a978e2c9019dc22c2a9c835b9` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.sarif.json` | `00e6332c27ae32f04ea1713743124d88222dcd68bcd735f40a83135062d1fd7c` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.sarif.json` | `aaccf940e94cf01c6f23ae25bcdfa3e0914344ec475343d00531f6c75a6caa5f` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-negative.sarif.json` | `948546fc620a9afefdecc2224f071dd66251f2ffb0e16e6f9b922bb403e84c9a` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-positive.sarif.json` | `42d33a26923e573d2247c04c35eab525e059d309903c6ca24188560609a80e66` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-negative.sarif.json` | `fa6d51f54a4fdd90ce324b0d9a870028472af21ec0dec314fece2549c4ae0edb` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-positive.sarif.json` | `74178e26ae194faafc6fedc1bc91e9c707a24d9dae478104c55f676de387f950` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-negative.sarif.json` | `210820143bfe67a18dc29734422c94e1c85b7aa72d43bc0b700b531c8b27b139` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-positive.sarif.json` | `26fa75fd4f7bda54223a534357f89191ac2c546dcaa5a0b4c4562f05d1230920` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-negative.sarif.json` | `5987f5e203e2b5f05ad1cee8333f24b98dab72eda22a20d77a5c29ccf6d9b8bb` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-positive.sarif.json` | `09ce93ed4875fdac70fd15d94a4df2c38cdb3149b4f197df6e69d6ad4c19b08a` |
