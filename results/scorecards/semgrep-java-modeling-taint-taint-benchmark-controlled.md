# Scorecard `semgrep-java-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-java-modeling`: `semgrep` `1.177.0` (build `semgrep-oss:1.177.0`, adapter version `0.1.0`, configuration `d25d4a4058ae7bd67131d38d05d0579a642ad1841071f965719dd8cea7efd59e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-modeling.json` (`sha256:35588fe1195fa766faa3c7bf8eb6071516ff0ee0d4e468e58bd96e30709d18d9`, normalized `sha256:35588fe1195fa766faa3c7bf8eb6071516ff0ee0d4e468e58bd96e30709d18d9`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `java`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `91f56167d6942d7f5c608ba4258645d3cb0e689187e516f589f45ae7e1c1e79d` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `a193259918b55e2b487deed6a3b13b3b4adc55e8058570fab9f9d730bd4158bf` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `5167dd20e60ad01def4084ccb8fa11ad5a6cef2785b777b0c56aabb5d2dbfeb8` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `9cd609678f3082cd46d53ec0269408b7d7109c43f183fb363aeea5f9c3fb926f` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `a6a25cbc638dcb78f0ce3d96d255226f29a3415667f51bc831b2ee9247c7acc1` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `d906fd54d5f7d474537136b3d94d4a1bff8cc263a1577a7ba6ee015f4f92f161` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `429865cf83332957c1703cb752ff01fc0f7702eecc56fdf5ed0f8b62701183ff` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `91211d6caa57de0a12967207454a8e6a89d31c15017231c2b395d1a80176d24f` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `b11d7b8889190acee84577f2b0e7d69500148927b8d389365f737503209572df` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `c7cf197ccc13c8fba76004a15de25100ac84c1cb622776bab29bdaa23b3719f7` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `7b7c3cd198cb43132e048a3a8b0f6968bb3b0fe800feacb803078e5481433f89` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `c737e2b9de8a282dce8850172d1e796010cbf63b23b42d161c4d6d400f340583` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `41540b2cba414a5b412770ca0d346d9b2b3f7d77c55384d9c9342ed33f30a37e` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `31103ef2f36f31917b9db320586b1f9e9ee8e59d51da3a329a45a6398d08121b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative-unsupported.json` | `ca6d004d8794350ae71497fa774ebc4486e8c921e944ac404b6e5747a5616b3c` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive-unsupported.json` | `11be8cbed07ce15c8f7cd90506aab0c9f6c1bef37d17f7adcf95cab648819697` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `d3b0279869e1bb5d33c37f9c1781f8d3eb190aa72d0c1e5e65bf8788df94d46c` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `e2ca97c91ee2546551d5af7ac1604ef7f226f1c9f5b48b796af85d91938a042b` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `c0235c80702e298844bddde4b4ea5703bdb9cc61bb27d177cb96dd611f6ecd51` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `cd95ea1b8fe03cef94f6578ddd05a490f5b35a8db96427db2dbb8caf4d123611` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `cdcd322d225f382d385fd269be706179a738d3a462499776f71d9896be337eac` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `22affff95fe235ceae5ac6f0ac07fe3e56eabaf01e564f4ed66bcc946d378834` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `76b9f6e8634f6aeba4967890f8863004170a430340d7100e4b546c5933cc3a80` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `c3c7abee23fa66fa35636b7969028437a1a8bd55ba169ef670b172a274cb977d` |
