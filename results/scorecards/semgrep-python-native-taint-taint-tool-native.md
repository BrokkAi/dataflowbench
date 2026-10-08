# Scorecard `semgrep-python-native-taint-taint-tool-native`

Adapter `semgrep-python-native`: `semgrep` `1.177.0` (build `semgrep-oss:1.177.0 — 1.177.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/python`, adapter version `0.1.0`, configuration `6432ad3e9c124ff9e1fafdaa7e1058523dfe0bb388d184424fe8c090dda14d88`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/semgrep-python-native-attempt-01/semgrep-python-native.json` (`sha256:22012b9e6989c46c07df4a9039fe4f0ac3b9c7acb37b2b69d7764d7511330a98`, normalized `sha256:22012b9e6989c46c07df4a9039fe4f0ac3b9c7acb37b2b69d7764d7511330a98`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-negative.json` | `fab5a776ebe3abddef3256777a77f82c2a0704648b23d28a0cd48130f39f3d88` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-positive.json` | `3a015ba317b662423c0ad699a417eb94b11c439b5e26855e12a03e4e9f580a2f` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-negative.json` | `b872f556836e0973354b43c9cd2387e59e0768317fa4447cd2fcf2e5ad43cf92` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-positive.json` | `29cae8c3fe3079682602e2c2130a50aa02f657867dedd6913699aea130532b61` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-negative.json` | `c4d3d5031c8dd480ca6c10efd244096ba5a49164a4e84302768b2df31c2e0d01` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-positive.json` | `7bfee3aae26d31708d028555ea20e1be35d5e14881273d9f316571fe761b3b15` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-negative.json` | `42e3ca41877c3dc5d449d3889de2eb48abd53ed1070ea54a10126b467c7d8674` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-positive.json` | `677ecef9da9bd42f09fa8d56f5fdb4fe29e00bd3c508a16fd97b5395585dbd4c` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-negative.json` | `ffb08893f60711ed9cee1db6c6e5add8fd88cf059d9675e386541784d2a23512` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-positive.json` | `6c1f3a3093355d7a87b3fa4564738142a454bcb00ad052dd865352070502d67e` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-summary-negative.json` | `65924cea591e9dddf648bab55ad255eb7c491ede8980bd85c7e1a7abc498bb94` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/semgrep-python-native-attempt-01/capture/reports/raw/semgrep-python-native/dfb-taint-python-native-summary-positive.json` | `2efedc8204991fc4d53df8940b979fdf511762f59f5742bff24c353f7efe7ab9` |
