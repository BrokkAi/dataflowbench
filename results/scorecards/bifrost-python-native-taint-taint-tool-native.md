# Scorecard `bifrost-python-native-taint-taint-tool-native`

Adapter `bifrost-python-native`: `bifrost` `bifrost 0.12.0` (build `676def6c6615002002b1bb9d25211ad1476a5b5d — bifrost 0.12.0 built-in policy packs`, adapter version `0.1.0`, configuration `29a6a062e94d60c5674ca6aa2ea2cea7770f2bce26cc2f6fb5fcc1ad7de2130a`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/bifrost-python-native-attempt-01/bifrost-python-native.json` (`sha256:ffb01f7a6627c6ec03102fc52f49bcf3f7630ff5f378888f1b76773874a01d3e`, normalized `sha256:ffb01f7a6627c6ec03102fc52f49bcf3f7630ff5f378888f1b76773874a01d3e`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `1380b8b1a1eb87df5ee4ab71faf2f56209c751902988821d2f55cadb00637da2` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `c25299c3aa4ab6ec0733d84979cc6cd91472df64a47b68657496e79c8b2565dc` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `b69e5555dda62a1883a12021d4dab18a67893125058f7bc9910da971a3783663` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `90f911d647f654d94313212415f6b9176d6127284d262acbc1916e197dd15ac9` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `4aee453ef09767c117108c693c41818ec27591da3d38059adbb7820d0f51c4c2` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `a1c5080e60f72f1bb56aa6c3deb81554cc69b8aabd50dfcccf305cde9bc53156` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `b696c98a3f0348cdcbc733e678d1813f7f3a41489a9f42ff9f1b37426bbac245` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `b5bd3bbf38218b0ed4f58a1bb6429f6359accf5501211fd8dc7e2bc5aebaa151` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `46e67aaccf9114522756e9911f8e288fa17f26dcb1cb8447c78d274990fc688b` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `ec9985375a88c6747e51f3ca481211b36b4408fb71dd09cafa01b022df9664b2` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `21be0e5b95af7e13ba4b0cbbaeb4b7f051acb408fa7d4cd648ce70cddf7fe2d5` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-python-native-attempt-01/capture/reports/raw/bifrost-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `8bcb5ee3849b4e1ceaf64cc44127eb01560e65ad9e16a951dec3aceefe06a236` |
