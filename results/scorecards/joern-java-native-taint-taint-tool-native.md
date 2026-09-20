# Scorecard `joern-java-native-taint-taint-tool-native`

Adapter `joern-java-native`: `joern` `4.0.628` (build `joern-cli:4.0.628 — 4.0.628 DefaultSemantics only`, adapter version `0.1.0`, configuration `47cce57071af2d33a8c7cdf27333dd615a77098d9ddbbb9d30c9b2ea1fdfd151`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-native.json` (`sha256:03e3afa6dbdcbe5ced6a6788e599ff2a5e9786c58b71c8b18d87228b0c2040be`, normalized `sha256:03e3afa6dbdcbe5ced6a6788e599ff2a5e9786c58b71c8b18d87228b0c2040be`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `e995299585df1c2de3bbbde1d48cdd9f7d35a88298fbe0a932e4eaccf6e2de97` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `392748ba558486d2d086aef465923de4b2dbc76dcc87d83432cc385459634938` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `49d446721309e5b54c8082522295bc19db99c4b2c58e6479a2674b35f0effdb5` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `357d7fa174b66ddbc4244bf59d5b5b7c8c1a58fd3531c41dc77d2ef23ceed543` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `767b98118c6b627501951d2fb48a378f3b2b678b1fca4ef04fba2348b1b06bfd` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `ec591f014081212cfcaaefaa2684e76a38c365f13245593946e4175dbe9ae7ca` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `11ff863c225ca3b0fe74424ca993bd6576f131d048fa34fd736f8ff447f08818` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `f8de528957cf5c5d35c4a5f084b347190113b1cf38d10e03de26ec278b5757e4` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `e2f4e724ac9e98aca135f7b6c270b8a8f0ef3d4b83e01c3497ee034a9d0330eb` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `842ece3fe3bfd69ae9db0836e15f041032114a62c74d5d7a8806a56c3d0a89b1` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `056d6271bbb827580a65d5fee9fc1ac596f4344323e79f68c254975722a3a8dd` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `6655a1b9c7ddfa048df382e0fe87af1cfcd723dfcd83dfba9b041cd6c9fe1f95` |
