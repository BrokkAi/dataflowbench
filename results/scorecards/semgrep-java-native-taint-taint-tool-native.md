# Scorecard `semgrep-java-native-taint-taint-tool-native`

Adapter `semgrep-java-native`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0 — 1.176.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/java`, adapter version `0.1.0`, configuration `1f9829f642c20d3521f0d991477e068e49c168f67bb7df861da14c043280621e`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-native.json` (`sha256:77f2501e818bbb6f136043d2af8316efab11582def633dff10d1448a4b93ab22`, normalized `sha256:77f2501e818bbb6f136043d2af8316efab11582def633dff10d1448a4b93ab22`). Generated from freeze manifest `reports/freeze.json` (`sha256:c543ae4ebd11ed6f3495f4461b5b4bd7c84d0874997f1b62044e9df62817b28b`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `10dba5c4db65a3ca4fc91cfb4ad6ad67f72dbf46071a20e9d19ed0d6c9a53d3d` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `b8bd208625dd56ade627fa645b6f37b33282c1f03af3747445f0d79e8591120c` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `12b72f08c93d6c3d0d9b2993d058767e6fb4976d74ae29c35a2ff0442c835091` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `f07a70326e6f1f464c9ceeb29cb93d98829a14be51775b8f13f02320e4958b02` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `53ae233a31830d41a0aab803f610c98784d234f93dc73e138bf417544666c6b0` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `9ba59544dd1c6ab25b8900661d766e4661926041b967ad4465d40864856a5474` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `0aa2216f619f5d7338f22f92e01b928ae841ecf2a2ea5a67eed1da84363dbe67` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `998eb59bbcde67b3d1a19f3cc180e90ac6c3c104c48bb80d2c1447662843e8ec` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `c2dc97613e3d8e8f3eeabf1c329f6e4c0ed0924602473891222f44093d720a67` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `d7dcbf38f731f6efbe2d04c61e7a9444299be2087b2607c4dade41dd81dc400e` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `b14a1e7fc660423bb77bc25a7b503b2e687ff92338a4de4a3da8274239715528` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `beb4527a9dd37f4ca1ab56de7d527250124fcbdc3e264b203243359c10ba7e09` |
