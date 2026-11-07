# Scorecard `bifrost-java-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-java-modeling`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69`, adapter version `0.1.0`, configuration `f84f51766cf26ce5665df0281d649df8fdb9ec64ab76cde675f790b8c0644ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-java-modeling.json` (`sha256:51baf4f2e076e2afd315ea58a4be81a553f9e6dde7a9e33d766168e5a0dd3d5e`, normalized `sha256:51baf4f2e076e2afd315ea58a4be81a553f9e6dde7a9e33d766168e5a0dd3d5e`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 4, `not-reached` 3, `inconclusive` 1, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `f717822601cf0872ec00e844147dd72398abf4d85ab66c5e5709fd71147f8bd3` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `f7ccc7841b6baac6922e3fb983f5c3076a314999a1473e86357f535d776a065a` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `71c84dbfb14af1485203916af663331116f33c45a8a9a25bd35a2aabcee275ca` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `10b70fd49c85583bda1c72b3d77573c601edff216cdc7e631c17518f7e5b2585` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `2a6828e4ed79240d79f2cc8a88c22d799fef54c829163ce5ce537112b2568e3a` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `4ec1758bfb76139e3a6ebd449b2b4b8d6df22da4679a1d873c3b16efa67414b4` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `062f9dd975510d67e7f4bc22383de25cf4e12ea832c1fba5ae2b8a6d05b9b0f5` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `d436e5535e5b8bcd829dc71716e4754e13a5e1b1b54611bc3985b449d80fdf48` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `0bc20b68464a0e502a4a57547f9edf6bb44adecca7fd8c6acfb936958aa5e4e5` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `c2adf32214154a3f070ff96a717df12a7e00c6d46466fdc28387acba1a11e4f5` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `a62183d167dea81da94d92304d9a2d2d4f42f37185418740822cea2f117d21b8` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `15b7a2546102163508d657970ef8aa7602d11e8648562471b5ad9e5d9ed568fa` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `21df394b37258516567d06dc4003e3cd79df4ae663fafa8edbc71f61e90acd09` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `0a3ecf756f25c1abcd2813da9facfff2334843db8d2d0f566acef2d40bb46a72` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `b8d90ceec27a1346f6c0c5563d6125ad04212052a758276f6b0c85311abc674d` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `ce7665825cee268132694d19718be766d23c31a3c3493fa79df8356ad58dfb41` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `f760f89ce61b19a065c5245f772feac913e2e13e3847d87451b4ec4f8f7078ca` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `7f963e0685db3042211612af44b07a6e54bc56a7adaaf168ed59452bf51d4953` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `2be862770113f00cef18b1aa2bccdb2b83c4aaaf52e920cd6097b4645e45510c` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `b45ded1e1ff21f0525e866b56e93d798a3e1dc288b1573167c4e2f305e81cf11` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `d5c619be5133ba37cd1040acc43909940116de92ff0e177561954a7409565127` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `6fa7ac4c8c3c61e1e17d6a3ea332b8108221b95120675f8900186518bd2b7d3d` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `77e244c2243ad9adf181bd1d25bb4960769208b20a4f28b8463e96f92d632833` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `245a72ebbb21476b9286f6187fc9ed244eb359afb19f2bd698f8cbea3da596c7` |
