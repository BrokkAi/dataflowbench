# Scorecard `codeql-java-native-taint-taint-tool-native`

Adapter `codeql-java-native`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65 — 2.26.4 shipped suite codeql/java-queries@1.11.9:codeql-suites/java-security-extended.qls`, adapter version `0.1.0`, configuration `ec644de36febf5bf3883833c856cac3448113b0a61d64e2530d333e90911fb72`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-native.json` (`sha256:5d7d7b152c9366525b8362438cc83a8c0cf6008b519a9c84f200eca711acee31`, normalized `sha256:5d7d7b152c9366525b8362438cc83a8c0cf6008b519a9c84f200eca711acee31`). Generated from freeze manifest `reports/freeze.json` (`sha256:5e57a5ee0dab3929cefa42edce222acbfb0ba0ee34e25e39e9ea882eaa66b724`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-negative.sarif.json` | `10d2f0f19176014f1b33706d3e0aa830243ae84bdf96ebf0365ecfbe86378503` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-positive.sarif.json` | `163bc73915422e360ce6fa39108beecfbca55d09d4ba13da45298102c9185015` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-negative.sarif.json` | `dc58e3e100a26e1a80408160c39f2452eac9bd937313d18357a6d9c7b2e540b4` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-positive.sarif.json` | `7dc3080ac59fa8ae8d1a06eed3fda02f500b037379b08073a40018b977ec4041` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-negative.sarif.json` | `9e1bbc583ee7b2efaadded3551b7c20d6fe2f03b382ddc50d57f28f296acc9e1` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-positive.sarif.json` | `51cb7da158ec5605c536888b9dd6bd5b3ef887bf99376dbd4dbcabd942653783` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-negative.sarif.json` | `6e5959d1b43feeb4b250f698a23f3ea52f921d0e97207946abf8a8a017ec6e12` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-positive.sarif.json` | `3c60cff3e0791a011f1aa3354e68627d66a66410193dccf39c7a8450314bb678` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-negative.sarif.json` | `1faed4e02cc786f9f3509f818cbd53b85cf562ffcce09f14bc3fb82d66462e7a` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-positive.sarif.json` | `eebf7ac0310ed68571bef3fbcbce657113441226db015ce101a4b5f592e934ae` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-negative.sarif.json` | `43721309a600c3c760be58481e20d7506cb66719c810e4d9e950bf07292a5b5c` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-positive.sarif.json` | `d5ce165bb1ededc0465cb79f1b3733a1946b4b830c4d17ff69698f30afb93cfb` |
