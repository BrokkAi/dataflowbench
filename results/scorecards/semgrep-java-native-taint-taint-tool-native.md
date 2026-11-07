# Scorecard `semgrep-java-native-taint-taint-tool-native`

Adapter `semgrep-java-native`: `semgrep` `1.181.0` (build `semgrep-oss:1.181.0 — 1.181.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/v0.9.2/java`, adapter version `0.1.0`, configuration `2b367e8b510a0a345841be713ee53d14c7d7c728d4823da25b3bcfcd10bb2bbd`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/semgrep-java-native.json` (`sha256:3fc6187c004404573fb23e418862a30808dc45e5eab5bda3c00785ef730ee374`, normalized `sha256:3fc6187c004404573fb23e418862a30808dc45e5eab5bda3c00785ef730ee374`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-negative.json` | `0e61e90f5cc48db07830a73433792d75eef900a1c93d8b38a39626a76642841b` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-positive.json` | `5ba1b4adfcad4785ae3c5789195eff65d8934a0552a2a5dc71e3f05461ff8794` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-persistence-negative.json` | `4520d18dc0e3b35bd5af7b2ada2a89d70312767a49735635923911fd3d2357a2` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-persistence-positive.json` | `da3cb50e4458b518bacbfccaa87b47e8c2f3606b1f4d0d5c6a752f54b7d0a8b7` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-propagator-negative.json` | `c4f259c7e5389fc580d0b3d1a7693d217f3107ce766e6866e11bfa6c123dbb7f` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-propagator-positive.json` | `8743a58c7e131c68d81122772aef5290073f8ce584259cad5ebb194c26c65f6f` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-negative.json` | `41df55997fab92cd76b639231e9394d70ec44a4553c620bec7c1fe737ef571c8` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-positive.json` | `30cf04e94bf03512eb9407af8be492210aa394dd4546f5211ccabcc51fbd4e59` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-source-sink-negative.json` | `d8964ebbd6233975f7a422452ed2e4ace9863cad41f7a95ab7ef3baf730e8823` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-source-sink-positive.json` | `731de7c924964f2d527c57af1455edb03dece8f17f74af0bdd973a076820f923` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-summary-negative.json` | `ca7c9ba84eba4e1879334db8d092a5ca2ef116571b442abaa7fbe048ba3d9334` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-java-native/dfb-taint-java-native-summary-positive.json` | `1bd4ebf4acd2ff60eaf4e6d489c53b6a006805b6a5f2bf6aab359c8d5afa6e23` |
