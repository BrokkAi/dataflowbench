# Scorecard `pysa-python-native-taint-taint-tool-native`

Adapter `pysa-python-native`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.3.1 pyrefly-sha256:f1cb9b8abc85199e1f5ae57f6943c8cbd412b968290023099996cab8fc3ce096 — Pysa (pyre-check 0.10.0 + Pyrefly 1.3.1) shipped taint model suite lib/pyre_check/taint with --no-verify (suite-sha256:1c2e41c525178d9f332e0b749ecedc5e4293fb570d0a0ab1708c41da7e49594c)`, adapter version `0.1.0`, configuration `ebd561ed95f259823e896819542ad787770b923b374f861a6422263f0a9b6dcf`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/pysa-python-native-attempt-01/pysa-python-native.json` (`sha256:72c41e47101e8b82b7e208e6ab6f2fd7fb898b973bec751ca5b2a5999f280387`, normalized `sha256:72c41e47101e8b82b7e208e6ab6f2fd7fb898b973bec751ca5b2a5999f280387`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 2 | 0 | 2 | 0 | 0 | 0 | 0.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `local-flow` | 0 | 6 | 0 | 6 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 0.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-negative.json` | `a2d22ba7aa654d97665797c08687d0bfa2d4ad8f7ad980b281f7343947dc10ba` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-positive.json` | `f58f517a7da4844acc12f185589008eace25159283f83041a62851754e6d3e88` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-persistence-negative.json` | `6569d5af2b8c9ecc72aa614beb8b7a1b3e93d47162d6cf61b8a50881873ed2de` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-persistence-positive.json` | `64f4e4060de725c7c32a8baff1e34c143d5d4b257e1d329cce392565f52432a6` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-propagator-negative.json` | `278a9a8eab2baa59328b6d2207b8fc55fc0d88200342ff88812dffdb05b36e34` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-propagator-positive.json` | `bd8aa8dbef28ebc13903d2a2fcec8cff46c9483353464811d569de1a320a89d0` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-negative.json` | `39a554deb2c3ed39fc17f00eedce18817fcec2058fefffc945264c8ebbd102e1` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-positive.json` | `5ef23eafc4f063bb9d85656e925011eaf5bedfcf60f60b5ed4366812fdc70c7a` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-negative.json` | `c1f951d548864a8c15b75115339c2ddeb08549bd6ef18974c203ba4027fcbbea` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-positive.json` | `cfb56677da1b734a9f9098b6ce11b7d13a92f2040266c57413571322e61e8171` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-summary-negative.json` | `ccd224609757d529f45f0dc17acb4bbca96ab68eaa7cac62b5bf24b78d9444d9` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.0/attempts/pysa-python-native-attempt-01/capture/reports/raw/pysa-python-native/dfb-taint-python-native-summary-positive.json` | `a82926605fb5e75f624a65776e6cc45ffbf19cf1c5ca9e5033411db132e06533` |
