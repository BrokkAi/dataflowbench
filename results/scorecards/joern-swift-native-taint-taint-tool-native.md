# Scorecard `joern-swift-native-taint-taint-tool-native`

Adapter `joern-swift-native`: `joern` `4.0.660` (build `joern-cli:4.0.660;engine:309ff2c75b0d7314cd9003a13ae298325827a680580efad9be55d6c168363e00;frontend:d8e0746dd2aa6d3919f2f44e329014d4fcff7fab641bcdef5696a33ea6690f07`, adapter version `joern-normal-v092`, configuration `5a546670420814104d2b6a78eeb70bd75399009127da21096d0141b470e2b39e`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-swift-native.json` (`sha256:b4dac12ed09b006969bd834b8349eebc932b17fa7c0639728d657658331499a4`, normalized `sha256:b4dac12ed09b006969bd834b8349eebc932b17fa7c0639728d657658331499a4`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `swift`, tier `modeling`

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
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-entrypoint-negative.json` | `1834e49d302a31e8501bac0abba4eed956233d151419c67a0342213a9bf2da12` |
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-entrypoint-positive.json` | `69d95adbdac1966095e942bb107c5db743049c238eeba4b6cfee01d26fb013b7` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-persistence-negative.json` | `7dcfffa4b8c2aba47cf18c056bf5c6d76bdd7039e25cecf6f05a5f29bc173339` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-persistence-positive.json` | `c9880f28e718439966f083112e76cb65c806d2329b815f4adfbe8ee38107a6c9` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-propagator-negative.json` | `e3b306e28de6c1ed1c1e24a49c0c22369586d1d0b8554f7c88d0461219d98838` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-propagator-positive.json` | `1527998a4ff2a0c6615df7c8c764258594fb2863c0cc9aea12984465ebefa917` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-sanitizer-negative.json` | `2948591f9f6450398d2f233c1a2d30656bc72048054daef1f6398abfacee2d83` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-sanitizer-positive.json` | `39c8ef308d9e5090ca1e837c6c1187f97bba08ee0ea97ad779634028e51bf208` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-source-sink-negative.json` | `c56efce37afa37c4f789f4f70cc36c746d4d70103272bd9e15181251e03c3b64` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-source-sink-positive.json` | `6143ac14f447234a0d3d30221f7d9298ed9221cd1cc363736e70268f8b1e2ef4` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-summary-negative.json` | `cde8a882f06cf9a6747a125584e2f40d57ed58c8389a023af27ce3165e6313ba` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-native/dfb-taint-swift-native-summary-positive.json` | `2f660df923384b9c6c6a1f4c227df09da4cb8b89b2207ffcf345549badd0bd8d` |
