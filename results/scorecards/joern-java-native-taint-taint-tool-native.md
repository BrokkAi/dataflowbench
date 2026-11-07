# Scorecard `joern-java-native-taint-taint-tool-native`

Adapter `joern-java-native`: `joern` `4.0.660` (build `joern-cli:4.0.660 — 4.0.660 DefaultSemantics only`, adapter version `0.1.0`, configuration `d74a06f0e2f9b5bb5f7c2965043c3f92417bd53847d85d0470140130a4cb1243`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-java-native.json` (`sha256:3f9d0e8ff9156c4a61d94546dfd5fff3ba6e87dcfe6899e41d90787c8dbfa570`, normalized `sha256:3f9d0e8ff9156c4a61d94546dfd5fff3ba6e87dcfe6899e41d90787c8dbfa570`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-entrypoint-negative.json` | `825923a89066af16eb741060b2a597e51aaa3bedfeda36ac81dc37e8bb8411cd` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-entrypoint-positive.json` | `c6949c7a4fed3c04e0f605bfdf61eb63a1976cd0d5fb4a5eb5ada270237ef5e2` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-persistence-negative.json` | `370f45ccef23481208f76f43fafc87659b8a102ea6e627ab708caea6cab4151f` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-persistence-positive.json` | `7c95f1088bc14a6eb4c87d6f4153a64aa35e6e9deaad010f8adc27c665d4dc81` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-propagator-negative.json` | `4b2f1ab063cfa65eea612c9e11d1f85b16a70fba6aaf6ff12ac1d7d27d095060` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-propagator-positive.json` | `ce4a170da61b2261357935e51986e541fde56cf6b1e02cf8d42582896af2165f` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-sanitizer-negative.json` | `c9d086b9fe342b887faa717da8bddfee04d0acd1ed147e875f4caac6866efc8c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-sanitizer-positive.json` | `7bd55fc153b137ac7774dfc54d6fd23b69611d49899b267c0b713038c40bc4ff` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-source-sink-negative.json` | `64679a66b53533f5737dfc97d90752f5712573989db3537d0894a23ce627511c` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-source-sink-positive.json` | `82f6e01f93c87f39fe44b67b6afc3ccf0e3f3e9e6adf39706347870bb2d7a86b` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-summary-negative.json` | `9f08a0752821809179a0947331377f9ffb74696f5ac4528e90f25fdbab065c96` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-java-native/dfb-taint-java-native-summary-positive.json` | `d057d1e1d4dd261bf7a3540e5d36e22407ff0eadd9c45f9d40e77997307fe53b` |
