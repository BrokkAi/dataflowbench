# Scorecard `opentaint-java-native-taint-taint-tool-native`

Adapter `opentaint-java-native`: `opentaint` `v0.4.6` (build `opentaint-project-analyzer.jar sha256:2ca93b6c33462bdbc23ceccdc5375e1a900682b33371cd906e5214dc7c48f569; opentaint-models.tar.gz sha256:20a96a50fba9ab6f6e98e8562019e5ecbe2a77de7947981eaf6e379f04065329 — v0.4.6 shipped models archive only — no rule set`, adapter version `0.1.0`, configuration `6a4e3e10c56b6cdb2c8c6ce054229c6f37807884e6d95b36105ee48b0b66f2e9`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/opentaint-java-native.json` (`sha256:e3456ec9661c5aa7f63e53649caaf50dd69168bb8061f1473dc3f67128446a17`, normalized `sha256:e3456ec9661c5aa7f63e53649caaf50dd69168bb8061f1473dc3f67128446a17`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `e353d86a1005445a8217dcd529598343f4515bbc3ef83f7d7b7b6b52153095bd` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `fd3393f7500e1526e049186e919bc06b01a187f5130ae93279e4b5c567a129ef` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `606417d2d4fcd417aa9e60b47b84b0d272e6368fc092233e0a5547986c3c2423` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `0334b03f4fb3997fabffbf3ed59d050a0cd3b6d710d6b00378a6f74bf0374d12` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `82409527d07f188c2df490dcb9fcf49aa55d68fcf019089970c51c391a28ebef` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `a61612f8669475d28097f080dedb955fc0911da3efc8e51fa2bc63640b974d7c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `1d0301c039e006ea0287bae08774db4ddaa13377989e9f68c9869d33a7dc7375` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `87ba4c5e8b49cee8926aa3298152456ff72072667354e09b569fb09d74c1df4e` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `9077bf378e0acbea4f7c93cf583e86b3627aa1d55e140f0c4e6e0c4c26a7df03` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `34bac2e6f2721456e369f0cd1060c3ae8af677b1e962a5f7cb495e34392da59f` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `0142f419063c520e9e4af47ef70c0e979402b8a8aa2d2c53c224a9fa473a35f2` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `99eb43429731d4117702b5dad8f979ea4d360bf1414a74943a8501a6cc73b11d` |
