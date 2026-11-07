# Scorecard `joern-java-modeling-taint-taint-benchmark-controlled`

Adapter `joern-java-modeling`: `joern` `4.0.660` (build `joern-cli:4.0.660`, adapter version `0.1.0`, configuration `55282607023d6902aebe9e2e4199542f04b407229ac0ab04eab9b70dd4a6980f`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-java-modeling.json` (`sha256:f584d8ed7d98594e1fd6c1e713376317e2288fd220e4870db71a6504a16592fb`, normalized `sha256:f584d8ed7d98594e1fd6c1e713376317e2288fd220e4870db71a6504a16592fb`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `java`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `220496682a703a78480fa49cd506b605141a4d788b9aea98e2c95dbda7c7d5ac` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `948b1b3686225698c054fd58554bcea48e05293e070eed546f82574a4c7ee89b` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `6836d8e6c6e415ea4e4b31195df18a1e234e64efcc1ba942a9382cc673e31eaa` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `4145790fac290ab2b16bbcbbc03163dbac7ebd53c82d5a4626815335fb61766d` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `b48741f8f3e57a5ae2eaa0115804244afaaacf48c02f57c1016c6860e389d121` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `b917d1e6d5dfbe06acadf52f10e55100b3bf7b0be3d710eb594c5170d888b3f5` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `e6fef125eb5b4d57b0a647b444a6991ffa207821fde1aec48e8972b3e1b9291f` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `ee060be1fada8fd507d307c83bdf4b5325c7f57b362ba1f31a0074c03cfe1289` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `b718b4ed5e31dd23cf438452664eef9b191536d8f9eed4440b448eed777bf465` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `dd1d4c5e516fcd1214464d2d35305fc3239aeaa072441f6a0b49a08513bd32d2` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `abc568e4d093fae0bd15887bcdaf3080160cf43fa8641cd85e2b7e398d2dc9c1` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `d44b1583519dcfb3984ae1738922d41a9b7f5c81a046f882fa94a771feebbad2` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `34ea618e9587e786a878c7a1464d9b126d5ee033e573f2c8acebfd57b106a48f` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `9f7deda27209252b5c824bd36867b1fca753f40a1c8a885a67b0729356db7c6f` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `a84d26aafa193a9731d3a24a4f423cc4173617415223a7e0a8c9ee9240fbc95b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `3455bbb7c164fff69fa16df442ba0d8a73ff3cc3e55b0f31b80425bda1daab65` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `eebfd8c3e1b62f85a294173bd82b56cae295e8e56d3795af2ae25cef60f57999` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `a089bfdcff45182a34517519bc0dfe2043dbdc1d81a5789088d8a5e27ba74f42` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `471af5740b0520a175d09950dc77b614c951a19f8b26ac51f28eecb1ade9e754` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `9f51ea568f9172abb95bfd4adea942f21fe6cf39777918bdde7b3d5707261dda` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `19b6f2c27519cde2c5079a9ae3b312f48cbc425d63b16a3d0786b0454863d53f` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `bd460b6ab3fa933ef3d422dfc8d50627fcdcc9519421d8e8fdf91e38c03c3280` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `a38148258facc52a97f5bca8bf2371a4a774488cdac86a84eb09f6e7c2bfaa09` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `1c246249dd11391bb270bcee74595fecec81cbbdb0adcfcc79e24d0d6d99baef` |
