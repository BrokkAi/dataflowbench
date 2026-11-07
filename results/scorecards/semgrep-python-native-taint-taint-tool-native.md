# Scorecard `semgrep-python-native-taint-taint-tool-native`

Adapter `semgrep-python-native`: `semgrep` `1.181.0` (build `semgrep-oss:1.181.0 — 1.181.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/v0.9.2/python`, adapter version `0.1.0`, configuration `d1323ae019df2fc808f4bd7125271a04624dc53f8db621cea463cca58f282aea`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/semgrep-python-native.json` (`sha256:0cf76dba5311ca7b0f0f0532efac7c813fdfe1104bd00a9f37b3f65e35dd5ec3`, normalized `sha256:0cf76dba5311ca7b0f0f0532efac7c813fdfe1104bd00a9f37b3f65e35dd5ec3`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-negative.json` | `518f99dda74e66d15c8ec4ee4f89fa40ac4a341e1dc51d4289f120b3c45d2a65` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-positive.json` | `27f13ecdbcf5128cd68e5866f8a7d602e495859a47d6c38d62d18658a736a6fa` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-persistence-negative.json` | `e081f366c7e08f23bc081f9ff2e1f3d6803fc1c18ddcb12693e4b4f6252cadc0` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-persistence-positive.json` | `6bd4e935e835d3e170f9684ef926de493f5841f5f6b9a222443f4eea46f14e18` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-propagator-negative.json` | `3c8d0b89587876c6be3578cb9006ad23d1fe3d0bee20b08ed727ae129f476cc4` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-propagator-positive.json` | `1c416769e5ac7a29ec974a2ea72604c461581c6da563ac30c0b39abbfe3fe247` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-negative.json` | `b3da5399a5737f0c606272906300dbcf85067fa153190456d8882dea4cb886fc` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-positive.json` | `40956926494b533e7e0bec59c174150ed80d3fd10231fa12007d489eac07dfa7` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-source-sink-negative.json` | `2ab5619d853085c92a89d03f8431a2a13a6d4e0f3673fdee8985c03923a5d781` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-source-sink-positive.json` | `5453ab8748bd7141427f4d035ba3c4371a2c280758098ed596e8afa72bb361a6` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-summary-negative.json` | `49a19c5fe0e96be06c5ac245f113f1986d38aef5f9c9bd41b8c97dcae9b5df2a` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-native/dfb-taint-python-native-summary-positive.json` | `612511fb6a58478cd6b98ddd50c130e51b602b99fba7a82bdd99f27ebb9a1ea3` |
