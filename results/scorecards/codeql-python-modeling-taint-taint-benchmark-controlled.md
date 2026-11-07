# Scorecard `codeql-python-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-python-modeling`: `codeql` `2.27.2` (build `codeql-cli:d7b185e374bfe18c0484dac07a521a810eb9c4fb`, adapter version `0.1.0`, configuration `41c012c09d732ec83a767366a8889210e195c1e06ebd153dc89539cd28cf3536`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-python-modeling.json` (`sha256:c7441074c7b9d3c6f655a36d87586a40985155654acb1f7ccef8ef96ecb2ce2c`, normalized `sha256:c7441074c7b9d3c6f655a36d87586a40985155654acb1f7ccef8ef96ecb2ce2c`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-negative.sarif.json` | `991ffaa9c3467c0577ed55bf948a8ddf401904c1b3b46607f293bd54e1eccebc` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-positive.sarif.json` | `31486193c735b7616e0a5826d3ecd832d853afbc951e2d5eaf21af6a0fe16c37` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-negative.sarif.json` | `5199b1bff8b219a8f636347c83c52b9b167846b5e4194ccf5307d8fe04bd229f` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-positive.sarif.json` | `0c1b9c15a2d983f7e0fd588fb0a6bcbac40f1d5e82eaaf24050485afa18c904b` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.sarif.json` | `2ce17ad1f162e8e5f35b032ce8576fe31ac572a42e58c5a460a2bd3b3c9e32f8` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.sarif.json` | `e9ccc4d5f1cd5463aa08572823755ddcaf4ede4f4561652b16ee12e38806e942` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.sarif.json` | `7ec290d46433fd4454dd8c0a030bf781ad4c44c9c41ebb106db521b86c47f586` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.sarif.json` | `653f37699449d41d2fac541b55d0453a654f723a5b2262bb4d3cab5d20ac6e86` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-negative.sarif.json` | `f7f130d65fa0032e6b91941205d73d8122b7348a3936e26e8cc5e22958022c9d` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-positive.sarif.json` | `df2b1c775a53d80797cc6dead0a10d88cb5841e5227b17e83810bfecdacb2ee0` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-negative.sarif.json` | `7761acce77ae99e8381495cfd927c297b01a93e8b75dd6e877dfa279dfe7558b` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-positive.sarif.json` | `26c09b2f9c2bf3cf7e2e2b2d2eb3ce85f2406c0094c8a73f9326aa73422ca4de` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.sarif.json` | `1489e73084762ba8fb129dd6c2126fc5c7ce18e079dc82ce40ed8787e0e42f12` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.sarif.json` | `27ec5980315bc680fa0bf3d9cd8a5fe2f04375696c74c1f03cc0d664e47c6ad6` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.sarif.json` | `7c7acbf8f5611a01c6da44ef5b95249862c9bcf92f89e0dd49e079786d077f53` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.sarif.json` | `f44057581c240bc68154345901e6b8eb146f240b3695ede69e63a53caf098525` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-negative.sarif.json` | `b40ac842933e4e43a4a49a2da0f6c97e8090ecfb635c997d986852be68149a3a` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-positive.sarif.json` | `4b05d59feaa996ca12354553042c52fb0dec8ac95d8530cbe7ea54755541cab7` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-negative.sarif.json` | `81f2ddd923a20a6d609e4e20e7582ca91faf74c88d98c95151dc05c52fa5c29a` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-positive.sarif.json` | `3b99063be56f3629e05e85da9b973906aebabd62552a28a0cfb5499527f2696e` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-negative.sarif.json` | `1857983b03afa3739cb94129b190ab6c6087beee7286db55ab2c5e79abe80c1d` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-positive.sarif.json` | `9b54aaa5120d9e372ce62e4dfc5a1d0c6d8937918a6b7e8810e833038421fae3` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-negative.sarif.json` | `065a7d148bddd1224a77921d2d7ecf4182614b61872cbb4e8ef95a372cadbb00` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-positive.sarif.json` | `ebc7fe5133f72b09ddbe02786618df2dedd168cb840fa0444686ae843fcae620` |
