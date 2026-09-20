# Scorecard `codeql-java-native-taint-taint-tool-native`

Adapter `codeql-java-native`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9 — 2.27.0 shipped suite codeql/java-queries@1.11.10:codeql-suites/java-security-extended.qls`, adapter version `0.1.0`, configuration `db05d851c13761b5e5480bc74577a06466a766335560da30699efc63103f5e68`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-native.json` (`sha256:39c69006aa2153236b08347bfcd0dbf263eed263d07d136450c05869b89d8dfb`, normalized `sha256:39c69006aa2153236b08347bfcd0dbf263eed263d07d136450c05869b89d8dfb`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 5, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 1 | 5 | 0 | 0 | 0 | 100.0% | 16.7% |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 29.2%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-negative.sarif.json` | `c14d17a3b84cb2e5733b5357f350bbbb7011e74ee2c31dfc6c51221dabc941d3` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-positive.sarif.json` | `90fb37f2741b95c098bf583c412152fc7042e589cbc04eda1a40dd23a1f5aeeb` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-negative.sarif.json` | `ee43d4b0d460c02abaa1f95aaaf029a579e98f00b89fc9ede45439d037807f12` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-positive.sarif.json` | `cea17d18a092c4ace9cc5e1aacc45e4d0256936ae8b29e2a5f5f722516b20428` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-negative.sarif.json` | `f0f666c13025d55cf440900fc9a1a7e9e16fbbe8274f97e3483b2ebe71e705f5` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-positive.sarif.json` | `7bc63dbe9b3e7313c06058d5c56e19785bc40d21222f71e8e558cc4fbee1ba3c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-negative.sarif.json` | `1492874e3cfadbccc32893c135476467a7572bebf36f16ed9fa81079651b0c09` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-positive.sarif.json` | `0ae258a040779f823909b251ca95ed1f26776dc99ff2f1ec6769d23d66b3d50b` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-negative.sarif.json` | `6132d2141c507d69bfc560033d215931921987ce0db590a9a184269797343ef1` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-positive.sarif.json` | `20ba411063a103b6d0d99684ad46268a98860b005b3afffd5fe9ab87d72d6ded` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-negative.sarif.json` | `952d79750b904f0aec60f85f46c40d39b58767b6043bcc498df889d423bd7feb` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-positive.sarif.json` | `dd7e28b350d456c43eab1d09edc7548887161bc3ea238c61959d633413155641` |
