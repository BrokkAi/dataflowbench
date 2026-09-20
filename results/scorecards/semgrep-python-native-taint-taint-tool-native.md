# Scorecard `semgrep-python-native-taint-taint-tool-native`

Adapter `semgrep-python-native`: `semgrep` `1.177.0` (build `semgrep-oss:1.177.0 — 1.177.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/python`, adapter version `0.1.0`, configuration `6432ad3e9c124ff9e1fafdaa7e1058523dfe0bb388d184424fe8c090dda14d88`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-native.json` (`sha256:c6ee8d2e41c04c112e225df3501bafade817b6161fb09996e848d66b98d45a9b`, normalized `sha256:c6ee8d2e41c04c112e225df3501bafade817b6161fb09996e848d66b98d45a9b`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-negative.json` | `7b960599fb2a9d943d2b829f4c9dd3a0e6f8c9d92f148f19f68597a6ed7ad305` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-positive.json` | `8606dd96e26ae6ca33f9d1db20e1623ad9600e123149f6fdde2ed3f6cd45e470` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-negative.json` | `1716af3f50f184a804040a1128e7892b34c82aba3c019263b616e18db30a191e` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-positive.json` | `fead05e059f49157e0f92e85fce9d6acd7a305c40a7b4df17182588eb0f99c29` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-negative.json` | `608b70304525e1ca08f987227d6b3cb5e32bb685a535679be30f9e6d5bbd0246` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-positive.json` | `b7549ab44d0da70ec513cacda2085bb223cbd7b2f1bca6a2c78ccab868840494` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-negative.json` | `ddf7e952ffced93111025d6ee953d94824cbdfed188a66f1a13f99a1c42bf08c` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-positive.json` | `16bf63303cfe3da14f6baa628a2e4bd52fbec1ac1210b2cd7d68807e52f549c8` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-negative.json` | `65f378032fe7827ce3dbff2d26c2084eba8848ec2bcae809f0e9117b703d8d2c` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-positive.json` | `56a510e933036dd1cdece8fd8e0de175a8a8c18ac7dcdd0e4cc78cefb74f7a6e` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-negative.json` | `56512f56a7cccbd7e909e29baa0be8c20adb5f0168074baaf559ea74f65242a0` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-positive.json` | `57a181b701d492c68e31bbff5ff4bb6ddb464aa5489c3d48073bf5c3c8814bf1` |
