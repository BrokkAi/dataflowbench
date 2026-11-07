# Scorecard `joern-swift-modeling-taint-taint-benchmark-controlled`

Adapter `joern-swift-modeling`: `joern` `4.0.660` (build `joern-cli:4.0.660;engine:309ff2c75b0d7314cd9003a13ae298325827a680580efad9be55d6c168363e00;frontend:d8e0746dd2aa6d3919f2f44e329014d4fcff7fab641bcdef5696a33ea6690f07`, adapter version `joern-normal-v092`, configuration `5a546670420814104d2b6a78eeb70bd75399009127da21096d0141b470e2b39e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-swift-modeling.json` (`sha256:303027208015956221c79b287546016bbd26f6aca271186337abd7554bc448d4`, normalized `sha256:303027208015956221c79b287546016bbd26f6aca271186337abd7554bc448d4`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `swift`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 24, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 24 `inconclusive` outcome(s), produced by `joern`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-swift-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-declared-sink-negative.json` | `10e57057045a41c358f35082f8ef685a0252140838c9411211bdc5c0a6244ef5` |
| `dfb-template-model-declared-sink` | `dfb-taint-swift-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-declared-sink-positive.json` | `d522b3920c061f5a04b3161da41e11f05669fa1f949d6134cbcda54bfb73e5b7` |
| `dfb-template-model-declared-source` | `dfb-taint-swift-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-declared-source-negative.json` | `887a61fc9191e9dda00049bb69f8e347969755334b3491b3ef6a6a7defb7321f` |
| `dfb-template-model-declared-source` | `dfb-taint-swift-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-declared-source-positive.json` | `96b676d01715f7c34a344750206cb68baa7fa3276e02939ebaa2648d86a2b98e` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-swift-model-entrypoint-parameter-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-entrypoint-parameter-negative.json` | `0e32055b7e14fae307913d62570a76b936c4352aa13a6ee91c3542af93d63e43` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-swift-model-entrypoint-parameter-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-entrypoint-parameter-positive.json` | `116b70c58559f6b479dcea6a8b90e2895448b77be52638467b1d8fa016c1e5c7` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-swift-model-entrypoint-selectivity-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-entrypoint-selectivity-negative.json` | `1b8120738b1710ed3407b779cc3617809424d18f42c3a8a5be09b5e1f03889d4` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-swift-model-entrypoint-selectivity-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-entrypoint-selectivity-positive.json` | `eb637ccdc4564210ae533a6b20a0142f4924ba4894118041e152cc6bb67a8877` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-swift-model-opaque-propagator-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-opaque-propagator-negative.json` | `6879e52e600033a0fe7b63993b1de154f6873a4c4eb84bfa4cc3f2e7407be41e` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-swift-model-opaque-propagator-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-opaque-propagator-positive.json` | `53ada415b3dd8b1bb6dc4a7bdaa8ac03c762efbcb8abe250d96b4cfb565f4a96` |
| `dfb-template-model-propagator-position` | `dfb-taint-swift-model-propagator-position-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-propagator-position-negative.json` | `44a58cdc29269e132bf92b00c4611980f353ca1dcef7bd72dccdbdd8ac6ab01d` |
| `dfb-template-model-propagator-position` | `dfb-taint-swift-model-propagator-position-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-propagator-position-positive.json` | `7d1c1373cd9cdbb2cead291220db776d7f82c36e6e88febc90df95276487e0f7` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-swift-model-sanitizer-kill-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-sanitizer-kill-negative.json` | `e684340a8af0e2713cb7faa3e8595fc85437ee303f31964358b966774044f8ca` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-swift-model-sanitizer-kill-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-sanitizer-kill-positive.json` | `02cc2371222b8a2a99276f152c7e2b8b931730f5707b88bcbc621229eced60bd` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-swift-model-sanitizer-selectivity-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-sanitizer-selectivity-negative.json` | `236671e6506f8db21e7abc72510ff59cdb027bc95802f208f428d233e2aeff38` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-swift-model-sanitizer-selectivity-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-sanitizer-selectivity-positive.json` | `13cd019980aad40b3f0f2685534e755379036a1e358cb626e97d953d0ec0c4c5` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-swift-model-store-roundtrip-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-store-roundtrip-negative.json` | `2cc75f86578ec21afaadd57dd522cc479b75ebdfbd81e45caa0a82d8e356f6f8` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-swift-model-store-roundtrip-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-store-roundtrip-positive.json` | `268ff9df5cac401300d4316323fb38650d247dd505dc0e1fbc0f439174f04cf3` |
| `dfb-template-model-store-separation` | `dfb-taint-swift-model-store-separation-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-store-separation-negative.json` | `3a3d80fd92ab7038900e1d038a7e92c4259231df262989e538b12e23dc10613b` |
| `dfb-template-model-store-separation` | `dfb-taint-swift-model-store-separation-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-store-separation-positive.json` | `ddb26161f7903e7d99c715f95bad5ad06e115c290890067159d87b30e7adc1f5` |
| `dfb-template-model-summary-field` | `dfb-taint-swift-model-summary-field-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-summary-field-negative.json` | `048f8373a059c5740eee165e9afa5e4c743f7fd9545db64666e0665dddf90232` |
| `dfb-template-model-summary-field` | `dfb-taint-swift-model-summary-field-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-summary-field-positive.json` | `6b93d309ea2a64524efb9b435dffd10fb5364ca6dd267d8754205b02ca2c4b42` |
| `dfb-template-model-summary-through` | `dfb-taint-swift-model-summary-through-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-summary-through-negative.json` | `62ca24fbc2cd385c692288f1763c1753f7b51569f823c3c6d717d585e01fca6c` |
| `dfb-template-model-summary-through` | `dfb-taint-swift-model-summary-through-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-modeling/dfb-taint-swift-model-summary-through-positive.json` | `5e9536894fd1867a1c7ecc0b171cdb4cf88bda618040396e6492978d87efcd8a` |
