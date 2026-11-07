# Scorecard `bifrost-python-native-taint-taint-tool-native`

Adapter `bifrost-python-native`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69 — bifrost 0.15.1 — standalone engine; empty shipped policy catalog; open-pack acquisition disabled; BIFROST_OPEN_PACKS_DISABLE=1`, adapter version `0.1.0`, configuration `74067dbc307c0e6fcaddb5faf96fdab1182cd45966c9c81846fe63b9db23a4e8`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-python-native.json` (`sha256:141b49594264ce95e037229f0ea16ee2faaa57afeeae2ddf01f5e06232a5b34d`, normalized `sha256:141b49594264ce95e037229f0ea16ee2faaa57afeeae2ddf01f5e06232a5b34d`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `python`, tier `modeling`

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-negative.json` | `c69a023439f1d66ac93ec261bdd1627325917d83ac3d62d21d6b72bdd3183f30` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-positive.json` | `ab949ac2cb767c977317ae55ab2c0d0c12dc8505969aa276dd974b9949ba6836` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-persistence-negative.json` | `9628f341a3c35be0bf9b7211392a7e6ee187224bdb5960be4b83348e1f79304d` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-persistence-positive.json` | `f092540d2ffc20e110974c513b4ec9db29d422a72c1086a50e8099b1cbad7355` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-propagator-negative.json` | `12d55a76cee9084fc570625bbc9fcc1a1c27e8d8e4967089a7e96f08cf2cf98c` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-propagator-positive.json` | `8accbb1845fea3a94aced33d8c312d552624e245a9df18836f8b7e5bb5cf1893` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-negative.json` | `8d190c1398308b5bccae2aa363f0f1bbe31567b806bc54e679cbc2434771ccc4` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-positive.json` | `109952cdd13c26ebe116ecb01559da7e7c72ee13be1d6a3fc610c0f7314b5f13` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-source-sink-negative.json` | `58ed709fa2354e249dde269057d78e8228de5e47d8e5889c91c065d42c954e6d` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-source-sink-positive.json` | `232a100054e3d65123a920b43a8f7d9d5ace69ef197ccbbb542324b22a234ca3` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-summary-negative.json` | `5d99ef8010d09e462206742436b71423a29ffdc3cff15ce4a86e733ca2db2d41` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-native/dfb-taint-python-native-summary-positive.json` | `3ca51122e4bba13a530b23292f2771e0b8bb4d0fa608e82bab8c34e941740fff` |
