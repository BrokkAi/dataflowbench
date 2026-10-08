# Scorecard `bifrost-java-native-taint-taint-tool-native`

Adapter `bifrost-java-native`: `bifrost` `bifrost 0.12.0` (build `676def6c6615002002b1bb9d25211ad1476a5b5d — bifrost 0.12.0 built-in policy packs`, adapter version `0.1.0`, configuration `29a6a062e94d60c5674ca6aa2ea2cea7770f2bce26cc2f6fb5fcc1ad7de2130a`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/bifrost-java-native-attempt-01/bifrost-java-native.json` (`sha256:37e712f3f2ca308d104307b0ce8dc8aeecdd3f3dda03afd5d311397a082efe17`, normalized `sha256:37e712f3f2ca308d104307b0ce8dc8aeecdd3f3dda03afd5d311397a082efe17`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `2064c751f6fd7a7aac4b530e594220e2ed58632753925055cc4289cd305ea758` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `e795cc09e4b3059e31fb3bad76ee4874617ddb23ae6977537257a186ed2093bf` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `d9c8c99e7aefa475bc9a43de5e208ab52a28f8fa4f962b2c671bab4493e7aaba` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `1186e9366d615ddc22e2957f89f323a785f8a2c0ebc1ebd433a6f599bd1d7f74` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `f048c90769f3315ed3b9af07e2bcd362e45f44f255885d914f8da4e8a4554d39` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `02dc85ea826ae63277993b21370b85171d844aa625b4a3659187450733a1e4c9` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `edff2cff7a1a26e555fa30e4bbf7fcd92d441b0774d25bf3ad691f65d279cf72` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `65b886d1af07582c661a8bf06138bb65c629aaf62f8540901ded372a2e43258c` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `fc27436d0f7fed13a888f5ab32ed718734aeac1d4612c64009864d41d378cf91` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `5a713ba9a80cb335fe25d37feb198e32c38def34c7543eaaf75cddb947660740` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `c1ef6963f75ed4ff0b391a3901fe9b84c3aeb729726e10e0a4a416cdaca338b4` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.0/attempts/bifrost-java-native-attempt-01/capture/reports/raw/bifrost-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `a51fb79d31b93a0b2c0f51503aeb502b868e9207fddf9f74b10ed6a5611c1520` |
