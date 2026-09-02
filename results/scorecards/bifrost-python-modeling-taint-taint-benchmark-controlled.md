# Scorecard `bifrost-python-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-python-modeling`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249`, adapter version `0.1.0`, configuration `7c35450fc275271a167e8e257eae83e8a58ed870bc92015cde34e4f64cb8b500`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-modeling.json` (`sha256:d3c95e9fe03f148c92aae60a3ad0dbc974ab8509a799fa75432faff1773c3702`, normalized `sha256:d3c95e9fe03f148c92aae60a3ad0dbc974ab8509a799fa75432faff1773c3702`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 4, `not-reached` 4, `inconclusive` 0, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `e8fdd2b0059870a5c367368c0881bb24b0ebcd1659fece00b051656a502245f3` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `e46fca1e7a90ca4b3344f1e02b681497699811a1b60ce8cb5b455a4fe720e83c` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `30056d77d3710e06c96a953b0f6c516869d2c495d32c34658d02d49a5e208f2b` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `d61cfac1fbb3ad857827e65ec41aaa778e56641ae42b9d3b0bf52eaa11813ad1` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative-unsupported.json` | `d42892ec88e5a8167e3820d55d15f0b7f01d0f81276b9d75646e2d5a3e5b058e` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive-unsupported.json` | `e32ede1f896822f23f3973e76d6162fc6e4354c7c875624544ce74b059a5aadb` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative-unsupported.json` | `3d344bb8b3037ce404e5397854ec7fc985fc913b26ff51131d085c802b430b83` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive-unsupported.json` | `8b72caa9a75774eeecff5ff69ff466483ba5c378ba03ab9acb2ba98ce7255446` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `1fd30927fc3ef86b647b9e04199300ef43bcfb3ca655afea0ac44986db564b2c` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `43ad742f4ac4b17faf8fbe84ee61462483324a47472b4d053754b81c387a72dd` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `66cb8e27b38ffb23cf21a5b3d27bcc651a3f701d92c8bcdab9020140a12199c1` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `191bf3c9768866ec4d89ef7475336418b99ceba9d5d7f145ce1227bcfa50a340` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `6bf1a88ef377ffc298dff43a84c6381ab462b4d818cf31191378eaf902d84678` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `ba27dd562ac96b9278d93a2e8dc3ce217e18be7a50784c184b89107af9b1cc4b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `599302504bee61907d4770c59179776581cfe18ce12eea43b961c32f3a0f086b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `b3511d8caeeef12bbfcf2c1b58aed931996d00a76e77292c35f51375191ab507` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `889f5bd8c6906311f66d92a29804b81270df1214439ae5dd891def19a7c1cf5d` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `38a51f5c48c95bd2e124a716008d68436ec42a1b8a8144adbd79fb8b7300aff6` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `21fefaf5c98073d654e4e5d2e95a41fc14b1ada0c53b290e832235d7a746d561` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `18fa447837fd35d2ce7396d301f9a8e2ecd358018aa7dcf2f7f61c067dcf3a21` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `13b960041332b2e3dff88f40830125faea6fb2926e500d475a177cb267d29dae` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `a53825813b438b789a1d9cc09bdfc705e80aae3e8a3ac2108c18280eb817767b` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `127bcd49eb95f37d7582c843196f2263f3689f61ab032468669f9e010d40dd5b` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `4b77c5c849a96d93b8e098229fd54459746a33cfdce96dc6176ac4cf78bf0049` |
