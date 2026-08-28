# Scorecard `semgrep-python-native-taint-taint-tool-native`

Adapter `semgrep-python-native`: `semgrep` `1.174.0` (build `semgrep-oss:1.174.0 — 1.174.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/python`, adapter version `0.1.0`, configuration `d300770a714f81200a543d80540059b932086b27ca8d8cab5b4d976669883b72`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-native.json` (`sha256:b807832c6dfacf25489c6d05669d86dc237fb09156a5bbac4ba86cf052883151`, normalized `sha256:b807832c6dfacf25489c6d05669d86dc237fb09156a5bbac4ba86cf052883151`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 10, `not-reached` 2, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 4 | 2 | 0 | 0 | 0 | 100.0% | 66.7% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 91.7%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-negative.json` | `3291df39b48d15ffaff636c1bd85d23a8866507abedebb8a42df2f90c5dc3359` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-positive.json` | `caeb32d9fb7b16692e29486a9c8f0bcd4844a7516eece57a19a98e2af0838e8f` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-negative.json` | `86d6ae9b2ce204a54c7ffa00a3326d3c481b9f3ec9fe66185e2a132990d7d429` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-positive.json` | `fe4716f744ca8f9973f33d439a77d3ba7f18b36ce78cee354607b23719bb7140` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-negative.json` | `dc8001bf0792db768c56aa3b94bf29424c927a60d4a650546ce7b95f5d7960fb` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-positive.json` | `99e5d87221fa45267abcb669c82cbf6fb6c706200d70f0770b17b9f3f19eb984` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-negative.json` | `ff7f87cc8d3ea4f3527ed98900efe61cb0e7d8ecd467b8a40553ddfff6749414` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-positive.json` | `c032ee54e52957cf2c980bcae52b9a819b76c7609befe417774b0997a0a4995b` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-negative.json` | `17a8f2980f74439c6785e8e810b74d9dd8eabcd15b62fa999f7c252a9d0c75d8` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-positive.json` | `a8342d6b2e0fbe2511c4aa520619f917da808e0f0b2794289d73497b4b7b72e1` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-negative.json` | `be1d462b1a48aba998f0eac7d780dbbad8380b37b13604a4b89eafcaa853f819` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-positive.json` | `449fe8f5bda749d5ccd598adad6a90593c1b60d6abfc3793c2a38561b3f170ec` |
