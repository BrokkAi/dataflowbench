# Scorecard `codeql-java-native-taint-taint-tool-native`

Adapter `codeql-java-native`: `codeql` `2.27.2` (build `codeql-cli:d7b185e374bfe18c0484dac07a521a810eb9c4fb — 2.27.2 shipped suite codeql/java-queries@1.11.12:codeql-suites/java-security-extended.qls`, adapter version `0.1.0`, configuration `2d5a347fb7d3f4b9551002637a6bd3b9d9e52300f3ec99fcd0ec5d0a274b1288`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-java-native.json` (`sha256:1858e3f84d8ce4f07e476ad649cf2f162adf99854cd5bc25fe46e2a63872008d`, normalized `sha256:1858e3f84d8ce4f07e476ad649cf2f162adf99854cd5bc25fe46e2a63872008d`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 0, `runner-error` 12, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 0 | 4 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 0 | 12 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-entrypoint-negative.json` | `f30c649a2726f564b8441c5e1049325e10711c676090e0863d83dd9d0dbf558d` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-entrypoint-positive.json` | `56aa8763625c342c82e8d7c64de52b8629652f3b18f4ec78a083fe7389c02e32` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-persistence-negative.json` | `dbc6d4bdbf9bcdceb44317c681f52b5cfdb88094da6a9a79debf75325186ab51` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-persistence-positive.json` | `48c126e68545d98754f2adecfd836d360be0de04eb435206c17b4b4f7f72153f` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-propagator-negative.json` | `2c83c011b805fdca7e741beff84c8acded5350fc1ff5178d2e3742b4d2624c25` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-propagator-positive.json` | `c28cbd84b505f08c369110631de993d03b05a97cfd51977e9123595ba58df22c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-sanitizer-negative.json` | `7a411800e886d794055c60f112240ed4f897df728bc784e4ced35aec37c5c448` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-sanitizer-positive.json` | `185a13f7d20da75976d5f08d64d5e43b386124b005405e1f35863194b7c2f36e` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-source-sink-negative.json` | `974150c9c27a279df8bfb62917906f66cd19d60dfeac9208710407f128c6b851` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-source-sink-positive.json` | `4919bf0f4c6f29185af261918c1ecbb9a12d3a1d8cd5d1e25ce1fdee1a775221` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-summary-negative.json` | `15fa3c9d360576431e537f435e4bef49b8fd6b5ea43b83776ae10943130152a4` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-native/dfb-taint-java-native-summary-positive.json` | `306ecabf7b5210d75075442309a30c7162447e907a3016196bb965d7084857c9` |
