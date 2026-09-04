# Scorecard `semgrep-python-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-python-modeling`: `semgrep` `1.175.0` (build `semgrep-oss:1.175.0`, adapter version `0.1.0`, configuration `a2eefdc01e1df0c60b7aa2ceb0967814426f9211b61b79be0cf11de92f0b9825`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-modeling.json` (`sha256:a269705d853a642979a357b9a03fd698cf2bc3e853c9afff1513e9c4b0001086`, normalized `sha256:a269705d853a642979a357b9a03fd698cf2bc3e853c9afff1513e9c4b0001086`). Generated from freeze manifest `reports/freeze.json` (`sha256:5e57a5ee0dab3929cefa42edce222acbfb0ba0ee34e25e39e9ea882eaa66b724`).

## Language `python`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `ed933a09e8d32d4cf78d1152d60190548349cd3389034bad4066d3d8f93461f3` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `485324a97c471456870ab139b566347c1431425ba532e79169d4c052dde108ea` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `1c556a294a7468e5e25a8b08204efd1ed4ca213201a93b16b40d029731253a43` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `f4b469946bef59f4d85615ed2b68bb3991f06870d619a8f2d3785d9193308bf9` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `4a22355171178c7ceb8bfdde53912f5b12edb2f03698682509eb09f906e25657` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `f35e04be6801e42e5bd4e08608a8bffa1b10c4563e1bc2b3cd5acad59730f2de` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `230de226b5cd29e384a911779c521ebde221c79c8e4d9c3aa59b50833c73566d` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `c4486121eabcd8e044e79cabafbd32972686da6c10b10665efe5613e219d5f1b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `b7269fba3bb0f98c9b10d2db3a2f243697a1c34f625075e2f44cb17fda0def93` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `fea6e753d36863bf081f57e3c42a277df0b30769777a67fb75e9b51960ff663b` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `b4fca19ba84c24a7034a3be05f2207bb2303ea97b3d17b2e4feb752ec501406f` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `c15d19a68496b2ad91af42ce3d6cf594c74215c71fd96cc9232d79c0c1f6875b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `e1f721af8710975bb97fb8ee5bbb7936cc91fe1f7028f8913b530e3157cfa041` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `c7980235697c385f4048239e28218ca2c4e26fa460b13fc8a536dd7ddfc80df2` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative-unsupported.json` | `ac85612856c91d6d70e77c4e1253dedc86f4e8b94c387732decb229ebba74fc6` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive-unsupported.json` | `9880836148430e683a122528d4bdeedf5bef19287267966e600de711213c3a3a` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `622988e9747ec2237000b9cce9e99e4bdd3659fd81e9571a61e2f63326198971` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `88dc330c27c21d189f7f0a7d79eb09901cb4bf749774c7bd687557c365ce9e7f` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `af70da1de72c30704dc572ca1ee84e6ef0eb131d768910f75504c8f0de79d2f9` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `d839bf2d5ecf6674c0b2320771edea96bb98554700e2b4853a50bcd550442b6a` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `980cd5cd6258a9088dfb0ceb235029ed0193665ad9bae2d2b64c50ac87056844` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `53bd012727b0d1c91f91290a55c7e0add8b2c04046bc8a1f825ab6249f9119bb` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `f2c95d933b485bb2017e44f78ee3fe73bb57377649734737626ba7c9972a608b` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `f291d1d0beff8b534fc05e3f4bf8e5abbc91334bc56dddd5fb35fc53a42625eb` |
