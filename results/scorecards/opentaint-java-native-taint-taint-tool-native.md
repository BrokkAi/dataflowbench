# Scorecard `opentaint-java-native-taint-taint-tool-native`

Adapter `opentaint-java-native`: `opentaint` `analyzer/2026.09.03.9752bd2` (build `opentaint-project-analyzer.jar sha256:db3a61637207633342c15ebc40b0164205563ba6446d48a8fa5c4f8fd194b61c; opentaint-models.tar.gz sha256:8746b9594266c67f04cd93a64c6c30673f98ccaeb59baed76d202ffee327a8d4 — analyzer/2026.09.03.9752bd2 shipped models archive only — no rule set`, adapter version `0.1.0`, configuration `af4205a4fb80f0cde8d29abb404f2e1630ff31e3b5dd8fc6d78c05bf7271b6d5`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/opentaint-java-native.json` (`sha256:7d3f4037002c7553d319873407064aaa4327ed3e30303e28c48cf22c79fbca19`, normalized `sha256:7d3f4037002c7553d319873407064aaa4327ed3e30303e28c48cf22c79fbca19`). Generated from freeze manifest `reports/freeze.json` (`sha256:c543ae4ebd11ed6f3495f4461b5b4bd7c84d0874997f1b62044e9df62817b28b`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `43e3399dcda7095a9b0e444f726987dfd5d682e46ed1cbe5b92cbcc1ab4c9da7` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `d5d888c916c43775c984f2f6253e8d5dd5225acb57bb3edc8d1d5cc5be48afd8` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `cb9380d0313c6fab953c5c6412d473c7433f3b2ce7154406241ea9320bf19c68` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `56ad4a6fc724fc05698a651cbd89a87cf4aea6be124d9d3cab921d37bf703a2b` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `c68c28ae67d027d1e34e37ce2ec00948fa4123dc42cbaa659f208142bbf5caaf` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `29295b8facb11f131aceca875472b62bae63298cca1f8f60cebb9a0c3ce4e792` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `9b03c9c85f610727c42433a038c0670dd40bd6736f810a7167346b44f897965e` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `d6ed630cbdb0619689bc1976b2a6066cfdd3c235cabb7cc4c67b752836c7d1b0` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `97a571ce76b29b3e0873cbe8e60bac8070b13c5e449a0efe339e8a2933872e48` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `2c6d81747fb52efa46de04ddc4fc9723ccb06c4d38cd243a5bca1b5ae1d9df82` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `81b7c9b1c85961aa3d32819085d2ff61f102d73cad405f8d806b08b49d0a4579` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `cf4406ca2b8295cf622ffb46dda698837a900b96f4acee9e5ca1ee25072d6ece` |
