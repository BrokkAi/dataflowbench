# Scorecard `codeql-python-native-taint-taint-tool-native`

Adapter `codeql-python-native`: `codeql` `2.27.1` (build `codeql-cli:938af3639d0709b587251e45d9f8d2bdc3505696 — 2.27.1 shipped suite codeql/python-queries@1.8.10:codeql-suites/python-security-extended.qls`, adapter version `0.1.0`, configuration `69dc9b55bb2dc412a2c441784d87483c16e449ddc809d05198c44dccdfbb5201`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/codeql-python-native-attempt-01/codeql-python-native.json` (`sha256:402f18cd98eaeaabbfa35cc1e76ef4a527096c020f0a7210c6f893527aa9ccf8`, normalized `sha256:402f18cd98eaeaabbfa35cc1e76ef4a527096c020f0a7210c6f893527aa9ccf8`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 8, `not-reached` 4, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 2 | 4 | 0 | 0 | 0 | 100.0% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-negative.sarif.json` | `f30b231d511ef12238ceea58dc008c57a699dd1713db47c751e965397a85d73a` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-positive.sarif.json` | `ff6c782f51cc82935ba7ecee4171b8547d9848fba9d7fee26d6dc9a4cc6614ba` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-persistence-negative.sarif.json` | `6d0a147810f7c867fd7c36b90b4f1c92462949e4c44faa11d3f4e65873f440bd` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-persistence-positive.sarif.json` | `a6d1b5e21cc6ecf7d919d16d6bc5004fac62ded6076dcc4537ba4bb937edf237` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-propagator-negative.sarif.json` | `b980ad7209c9cfb6272701fdf05ae81fb3e110b4091ce7bd3f2398c3199b9671` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-propagator-positive.sarif.json` | `9343bd881b4fcb3973d63a83bf944342268fe126536c768df91f7a65024a6002` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-negative.sarif.json` | `a431f7ba9c0f37d27ed6878c79ab4f0b506df9ffeb996c2c637c1179d399c867` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-positive.sarif.json` | `3f4de6c45c9dce78eae5da6628c174318a971a492dd71104eb2b9d34bb4af922` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-negative.sarif.json` | `9ccb6499837867ace8cf8ca9c81e23cf6767c9a5273c906f758b0b2328cf8128` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-positive.sarif.json` | `fdcbea2e8fba47feabeb5a636af75fa7da83e59b6a14b985711dfb76559d1437` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-summary-negative.sarif.json` | `4470b301982bd4d65c1bc188dbbc3f1d6f767f129d1a3a5cbf1f2b0efc78ff40` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-python-native-attempt-01/capture/reports/raw/codeql-python-native/dfb-taint-python-native-summary-positive.sarif.json` | `59a43069027862f8aabb6f7948f93fd49158eb69e7b953016d67fd6602912bc9` |
