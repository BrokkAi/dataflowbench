# Scorecard `codeql-swift-native-taint-taint-tool-native`

Adapter `codeql-swift-native`: `codeql` `2.27.2` (build `codeql:d7b185e374bfe18c0484dac07a521a810eb9c4fb;swift-extractor:593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f;schema:a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89;packs:fb47dc786441189213937dae9638efe8b0878e04e0be56c3d349ce03d6ceb4bc`, adapter version `swift-normal-v092`, configuration `ab028dea2a0c1addd6851b625324e8288b290a6a65d5e8ca58c9092147e4c3b8`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-swift-native.json` (`sha256:1d4061904335db35b62eef2725502f4b4861490ef8fc30c86c2440a053367bf4`, normalized `sha256:1d4061904335db35b62eef2725502f4b4861490ef8fc30c86c2440a053367bf4`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `swift`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 12, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 12 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-entrypoint-negative.json` | `e8c0809f3d2d2531e9d9b6bab928435263a1491e0ef593532fe6207e314f56af` |
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-entrypoint-positive.json` | `1744d20e040176ff53dfdebc292aaa768a995e08e353fe0d769689a5c55be1fb` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-persistence-negative.json` | `670d4a505ed7ac0c6265b8a573f1859d2a2644c325a318ba5fccfb22b45afa03` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-persistence-positive.json` | `10eba33cb61f49c9474eb278247ae6cd908fff5569f639649cf22ff442d37955` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-propagator-negative.json` | `12fffce719d00473bc4150912a81217202a005c516e3a6d0b1ccab344ac5fda6` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-propagator-positive.json` | `8fbfde94cf03e2e59daed03004adc0459a9d82e06614c24a36e2bde86f554520` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-sanitizer-negative.json` | `c2c3c6828a4828cd47c6a5770ef63e739b4f85cac689dc61fa6d58edb10427f6` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-sanitizer-positive.json` | `724c892676c7ba398b5aa50f6956b5bd66216572ca9ab6e5c62e81ca36f71aba` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-source-sink-negative.json` | `51f36458a56ce58027e963082aee5aa1f5a1abab1882872efb43256006d72250` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-source-sink-positive.json` | `3c0e7328b081edfc8c5d1f5e21b15100f7395a4c6b3c36e01ad5f2b84782482a` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-summary-negative.json` | `2c54a3e481a43085467ffbe31f184be4325f54fccf3bdb79596074197a9e1b2e` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-native/dfb-taint-swift-native-summary-positive.json` | `e1d2c6bcf56e3a312f1ddde0c8c6594d4c0ef4670ce15e1d64dafb811a2c50eb` |
