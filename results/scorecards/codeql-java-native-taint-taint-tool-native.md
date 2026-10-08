# Scorecard `codeql-java-native-taint-taint-tool-native`

Adapter `codeql-java-native`: `codeql` `2.27.1` (build `codeql-cli:938af3639d0709b587251e45d9f8d2bdc3505696 — 2.27.1 shipped suite codeql/java-queries@1.11.10:codeql-suites/java-security-extended.qls`, adapter version `0.1.0`, configuration `9e001de33645248f117850f5ed0524a275e2b14356073a79330cb7064e93d4bf`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/codeql-java-native-attempt-01/codeql-java-native.json` (`sha256:c939ff5472f1d21e4a5cd62f24008c7bd70d984deacb6f6371ee433d9fb6d764`, normalized `sha256:c939ff5472f1d21e4a5cd62f24008c7bd70d984deacb6f6371ee433d9fb6d764`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-negative.sarif.json` | `caf5e74c25e3df7d53358abb04a74ae212718eaa047121432660591486e567e3` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-positive.sarif.json` | `8c90d0d17f8c7c8de4fb22829b723d5816c914863fb8e4a9348aa9a11b24888b` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-persistence-negative.sarif.json` | `63c7008a3fa7dec14dca18d84bda2839a0bf3dae2b2ffba4656b5ab77ec23223` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-persistence-positive.sarif.json` | `ddf3faad2bee2e0e5ee176129e4653bb958bdf20ae2e9c71bdcaff320ff4203e` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-propagator-negative.sarif.json` | `af0f15cefe02272a4a5c8ce9eea7764f0b98ee03ecf94b8a569926fa5d785358` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-propagator-positive.sarif.json` | `b7307bb695a3a1dda9b276c3655dc63cc2052eee07371240551e046d1fc101fd` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-negative.sarif.json` | `49095eab5e397f821592d1b0e4c65f1e67bb0350649653a81adb466595f64b67` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-positive.sarif.json` | `80ef9e018932eef80e7c1db517018ef7e5d5a26dffdf4b54f5e4b41ac34c80c9` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-negative.sarif.json` | `b6ea9a0b8d51f26586da0f77795246f277d7b0e28dad860c78c600b2834ba15b` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-positive.sarif.json` | `c7585d10103e3a6db64a6cde80d3c424962b9f0945ce00df05aa4e79b2661393` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-summary-negative.sarif.json` | `05381de5ab06d983829cc94dd1c259be6577f37b800a8652c30769ba5f3ffd74` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-java-native-attempt-01/capture/reports/raw/codeql-java-native/dfb-taint-java-native-summary-positive.sarif.json` | `f4321bc01fb859ff9ef691b14a4bc75fd107f6886ea8887c012a47d0c3dd617e` |
