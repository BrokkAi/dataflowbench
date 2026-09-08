# Scorecard `joern-python-native-taint-taint-tool-native`

Adapter `joern-python-native`: `joern` `4.0.621` (build `joern-cli:4.0.621 — 4.0.621 DefaultSemantics only`, adapter version `0.1.0`, configuration `8d7d26eddf19914eb56e53fb55524843b61e6bad772bc00cb053b686c53e60ee`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-native.json` (`sha256:a6a307052b7db0ff7f4e2f2625e4d539820d95b4363ce88220cd3b05a55f3a8c`, normalized `sha256:a6a307052b7db0ff7f4e2f2625e4d539820d95b4363ce88220cd3b05a55f3a8c`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `3954579da67841424e1e71fda830e4fe9f2e3f81758e22e52a065e2e32ca1ae3` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `d2709cf0f57fe1293f452f39bec4d5d3c13bfc197ca35d7d2665e541734eb964` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `ed3844baab6c8b977e988a0d9cf8873971a8fab1ef6c5d5525dc9b10e814784f` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `4dd9197d576f91f7d9e33cc042658978bcbd626a42abef9346d45aa7d59224ef` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `5f6425bc4679d2ad49f8aa15aa58b48eca463088b6d6c4faaa96f72ac1ec0a9b` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `08524991e2ae52a937b4e5b56a86183d489d5ff8cf07601accfc430d27b993ab` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `a76605cc6a37596ccecccfec137fa64ea983702d21bbaab0a3ea53eae8c5aea6` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `f11504779d22f40891f28318d603fc6683894602fe149cd4ffba215d810227f9` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `abdbacb64f74f38b7ca73b1233d252c88749e3b1448b90732cedc48a9aa2b745` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `6dc97af400fc4c5b5aa1948cba0964a8c6337a0b564b19a20f6745a5b6624456` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `8d3ff590f6fc8678353e04de61fafa8060f24476c2f4375e3ca99cf70765c24e` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `88824bc60a7dd8fbbeb14f38184f65352ef32c3c0a58035ac9e161cb09b14cbe` |
