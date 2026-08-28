# Scorecard `bifrost-java-native-taint-taint-tool-native`

Adapter `bifrost-java-native`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57 — bifrost 0.10.7 built-in policy packs`, adapter version `0.1.0`, configuration `6b12ed91fe6d3178ea24e9be7feb9f230268987949ac7a0e724069009265be05`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-native.json` (`sha256:5add3826fa45f30c92ff890e52c246843ec157761525309a34d71af24692df41`, normalized `sha256:5add3826fa45f30c92ff890e52c246843ec157761525309a34d71af24692df41`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `22ec06944f94765e7c337b23d904d113df7b0483de93c726e8b76fe2efd6a714` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `79d7dadf7e7c557816e323e3a498c523359a0e4984bfea80034601bd27b05208` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `18747e7503371f25d89bf04fe450393cd15600ac09c2dfeb73ac35b854c74fbf` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `b2bdccb738a797dae57c19bf97137079d9fa1ff60d03504591f769163bea741f` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `8e5994a53f1e6f743cbe07050f273cbc3caa6cb0da4ef777c8e613b7fd36166b` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `06079d7edfb6d506137bac19415d389b007ffced0d0fabf544376ff0e3914d72` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `a181db3fa65528c47615c2a354bfd2d85533a7bbffe0237b9115f33b87f7eff1` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `d3925c12266173d15f35ba6573e91b2c19d2dc63bab520bd72a0fc5c90016009` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `9d264153544a16cedd9f9e580762d56215d05005ecb503bca08ba295215829d4` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `0bb9d64e549942de2548ba48af4eafccafcc0981ff7ac3bd329d55ee8cc45cb5` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `a7ec3579d5969e9549c5aa04803a3784a1c1a9f651eb406e49d1a23aacc279fe` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `e39617939e83ccfb9d65a01e16bc562be0643e7750ef10b6a5d81a57abfba7b8` |
