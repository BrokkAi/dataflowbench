# Scorecard `semgrep-java-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-java-modeling`: `semgrep` `1.181.0` (build `semgrep-oss:1.181.0`, adapter version `0.1.0`, configuration `d25d4a4058ae7bd67131d38d05d0579a642ad1841071f965719dd8cea7efd59e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/semgrep-java-modeling.json` (`sha256:d9de1a8820503925446307905d99b98b7a2e669daba766c91971746a3f0dbe2c`, normalized `sha256:d9de1a8820503925446307905d99b98b7a2e669daba766c91971746a3f0dbe2c`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `dc4803b600a290145cb85affaccb7a8b525c2ed0fed56009f09f10d28a35687d` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `5832c3b0d4cb41610cdaafef8e463d8c31eba09307324c0a56e1a8a3c3ee9b8e` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `ced6f3a258f86a4f55a6df03349104b0c4a512de524b1b6b350660d1b85e3965` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `97705bdc541cb9882ba15f3e21e08e3f599deff2c33d7b1e44995929277437fd` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `031a4ff81e6783a77b31881cd849735cfba5b4f81eee614ef87560e654c30848` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `618553ca0aa931f026deb4972e503e542a85c75dd8184f58eb710a83f53d6e89` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `f7969f12e1635891f92e8d8eed38b3dff81d11aa70e893c6fa51fd8c3060167e` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `bab6f67048338720b55dc9ccbf875e68501d0b94c1c2774674671493b42e3081` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `a5a0ffdee803717d8f5ff37ca3b5cc6e093ad068813e1a8bfffb3b3c18d7b472` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `67a220da96df35fac26b0ea2b23e09d8d6a18b1bbf72cf6a9baf6bd1c74f5f0a` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `a894ee4f98c21ce78a3bf3ea3e6c379953899bc6a9d8155f51f9dacd9d03b6aa` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `383c0d574773c1a605636b612b9fe8bd5502ff3e76c6cdb12bcbded1bcce8c0b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `9598907abf9db8429ca2b40b9d74c70a5c2062f81a9fcc5072ac9d67fb698210` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `56933070ce1eb816af73dc2ebb3ea14ff85ef599b83ea4a383e1065c043296af` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `aec5ef3299478cde63e555edfd020db6e2d493faa5ece1655dfae2fa799f4296` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `dd922b1a3d6b20dae42ba618fc58f3a93f157bb5cc144676d807341bad5487b7` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `5c55c9f7b8c7e79c7bfe704134955bac3800dfb7faed8e54e783f1cb46414d80` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `8d64e4c9e6de2963e47b297f578c7ba4f6e900e49a44a7a1fe8ac1977808aa1a` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `2b815fa5486144be9e26c2361be3a16afc8aed56c91585096323cbbedae983b1` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `8a8b8b660aba68fbc1c68c445c38ffa0b4e1809bae22ba4531421beaf2c5da27` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `e36db90b05a7961037f2dd5b64816614188b6e79d836a2c853850c2cb09afb0c` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `0ecc684b35935a4c3756b542c387c24a7e7deef48da7fba99b35aa69b03cdc5e` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `e5834610abe6f6b72274df73882dee0949e1a6d561e88cccccd3981b38b78310` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `43fb6fcaa200fa346ad914ca3e3897078a6c988650763b3373df660e5a7c8855` |
