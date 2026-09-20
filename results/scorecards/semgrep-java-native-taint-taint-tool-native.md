# Scorecard `semgrep-java-native-taint-taint-tool-native`

Adapter `semgrep-java-native`: `semgrep` `1.177.0` (build `semgrep-oss:1.177.0 — 1.177.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/java`, adapter version `0.1.0`, configuration `4fa774fa70198a34f787272ff899097173e8bb7c9fdcbad8298cd497d9ff5c20`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-native.json` (`sha256:39991c700f6b7613be737cb20817e7a19a2bdd668d1547c595ed40d91cb5a8c4`, normalized `sha256:39991c700f6b7613be737cb20817e7a19a2bdd668d1547c595ed40d91cb5a8c4`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `1fa6ce6621aa122bb9bd8fbb342f3225ce16136d19cbbc706ca03497d3221f20` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `2d89a35535c79b9b7bb1b3661a21f6cee97c8918172ced9ac1ce93808f2a3c6d` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `c7a2733bb3eee2ceb3b75b6c2ab31bea9fc40a98cf5d826a2a2c0229ac6ad52a` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `239869115e4c485b3f62fed8708844e3f6943d6b77a56fd3c8e3b66436cdcd2c` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `3d978d20a16c6585cec77f9ecaa40d7c450580b61f9264918188d018bc2d0e13` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `2f4c275205c3888e894cb0b8ab7bd2cefe2b5b7f8d863c6dde1b9a00a73a273c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `5cbc351393a4aed726f3c17175a024a393e4133117fc45e0ddccdaf54ef8dbcb` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `25da9cf93c7a420ea5391b36a9a9d13820bac3b01490f631b1be2196eb2e02a6` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `feee56fe90cd197a35664723cb81862529735e59177f7a7c20eb4acf557f3f59` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `066ca1e2b4c8b02d1cb37d9b004d1502d404c33272d3b8a39b61985444873066` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `8ff8f42d5f5c0b9f0fa9924769c4482a1abe656715f1b829ae84dffcbab5dc9f` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `75f619a0e2b02f76d301aa4629a100e170590cd1469897743781ca9c7b2e8f62` |
