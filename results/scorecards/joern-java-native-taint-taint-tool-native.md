# Scorecard `joern-java-native-taint-taint-tool-native`

Adapter `joern-java-native`: `joern` `4.0.621` (build `joern-cli:4.0.621 — 4.0.621 DefaultSemantics only`, adapter version `0.1.0`, configuration `8d7d26eddf19914eb56e53fb55524843b61e6bad772bc00cb053b686c53e60ee`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-native.json` (`sha256:0506cbb5fd53c58b2702b28bacd9a5046f0c5b625d88c1452f0dc6ce3429821e`, normalized `sha256:0506cbb5fd53c58b2702b28bacd9a5046f0c5b625d88c1452f0dc6ce3429821e`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `bd8823747b1b66d6ff1643aac5623f343f5052cf4a2a1a49919a3a44e3b05f8f` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `df6eab1a9f1f85d6f19e9f6ab1196a9383481684e122cc998b0eef2e145ba580` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `2391a67d57aaae22177c1d4b49726c2b93af296242a3068accfbbd95eed18fcd` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `966138c69399af8c225f3fe74dfd92017042382d8f4a2404958c566456edfe8e` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `a16cc36a493541c5af8f9963f8e099aa44977a134017c2e4456abff6671df7c1` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `5ad58855d86f78bf943840ac09f6f72f55b73c041ad6d96a2ff280474a27e179` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `56a0850e289cd16c26faecfa68f2ff4a1381cea57519855c5a81ce7838371d7c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `8fd137675c826c56022c5ede18b6ad8e086d97b37cbf7bc736437a1035a3792d` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `e738908049ead544b14765221da4733b4033fd60315ace1035ece388766923c6` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `3860dcdc5124d510f3b713b4fdc4e4ea076631fa06e69718e1e59160fc33d5c5` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `81df805baaf7e0716cbbb83bd2609023c475c1b424cf6dabc43aaa1f519e1698` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `dcf4862211aeea112657e875c06df0c0d0b5e6041caebe5f4d7135ea44976cb0` |
