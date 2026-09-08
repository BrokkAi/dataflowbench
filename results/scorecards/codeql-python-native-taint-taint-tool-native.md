# Scorecard `codeql-python-native-taint-taint-tool-native`

Adapter `codeql-python-native`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65 — 2.26.4 shipped suite codeql/python-queries@1.8.9:codeql-suites/python-security-extended.qls`, adapter version `0.1.0`, configuration `718f6dd466a0a14ff799e87868acf6e2f88a0a641a4eb6b12d042dfc4551f0c8`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-native.json` (`sha256:0366d05217369a44fd879865849fba372643bb51cc0886c9d4ff40534e92f182`, normalized `sha256:0366d05217369a44fd879865849fba372643bb51cc0886c9d4ff40534e92f182`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 8, `not-reached` 4, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 2 | 4 | 0 | 0 | 0 | 100.0% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-negative.sarif.json` | `9ed97d3deb913066a2fb1caf783c9edb141de12982de5f7ba5201f168438b0e8` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-positive.sarif.json` | `cfc0b98fc2026bb0045c94e835aadb20eadcda478a79aa7aac85e8442e5d3a46` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-negative.sarif.json` | `8f36e7fc47e6196a851308d190f1c75af929d7ac331449c81cc2b01628605b82` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-positive.sarif.json` | `fff3d166d8d430b78e70ee95f59470383b5cf61a303b938a58e2679166d24c88` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-negative.sarif.json` | `95a33d30e30aa46d7cff963b13d7705c0cae77f2db418bdfb9f0f870c0adf16a` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-positive.sarif.json` | `6878b118b70e28100d1d4ef649aa886ae2bd3a7eb9942eea16fa5e7765c752b0` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-negative.sarif.json` | `9038c8aaf2ee06f98c5fb2e79265a6532d558ae5ab5e08286459e4c5a975313f` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-positive.sarif.json` | `3d9842feeb07c1ffb6d95e56bfc837371c331f436594c8b27486809e8d52f519` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-negative.sarif.json` | `f1e5e562a9cac475aaf4910416f25c6a244eb7171ac77348f29d681209461f1d` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-positive.sarif.json` | `510853a9256e5bd8a2f300a13dd4f334d0f0e492601bd017006e4693b3c38413` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-negative.sarif.json` | `88ac2c5da9caed8ef33e1f54112a2dcfd2e8fa2070f0fe8cd488b3ec62fc5401` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-positive.sarif.json` | `3148bdaa0022ca7d2f265f8652466395d18052b489b4f1a64f24eddcb4eeb1f2` |
