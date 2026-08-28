# Scorecard `joern-python-native-taint-taint-tool-native`

Adapter `joern-python-native`: `joern` `4.0.610` (build `joern-cli:4.0.610 — 4.0.610 DefaultSemantics only`, adapter version `0.1.0`, configuration `21936f4b5fe760f2f4ba8ffc27c440c664cb7df00ef48374d47c74e7b2497e25`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-native.json` (`sha256:d9612e60a43983b62bf218cd022acafc51db983a6c90a732eb4c8b59849f5444`, normalized `sha256:d9612e60a43983b62bf218cd022acafc51db983a6c90a732eb4c8b59849f5444`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `21524705fe64233674e55d9f01bcb25a67b4377f2307b50dc5a2bd80684c926d` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `7d6b17d2e7a8c42e22445b5c829694482b7fed1f058428d9f6f5125d55a0e500` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `72ec0a1072d585bb816791e97aed7d2b59c2ffdc20f409e7a25f8fec88f2840f` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `94d99bb1d96e4d64871d724e11dbd7c824bb815b2601614236f42362376b6df8` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `003e0d4f975a606375aa22b5703c732dac7c50b57d73b9351477f79733afe597` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `1329e1c1cb4ce3bba1138fd2ab0d6aef651f3ed2bd9d3581638b48e2e1e71b2a` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `28b319b0150a8aec1712c87da2bd4470b5d6f8aabb00e9ff6bb2b98268f7e276` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `1267aaebf2f8f32c77ef37efa8f0f550d8af97ef4efd2d201f2b35e190454365` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `d78014447e96c14b851344e5b614766cf90793cb3569e8d187c4f4c2ad0d054c` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `32721caf081212343ee947f797fd2774e1110ec8f66553206ecb082a3053fa0d` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `79502f5c6e648c2b3484b54b4bdd5811f462ba546c42933f22f47f52b02b1366` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `c2a980edc18d5907ca964e28362824452645cb569a7ff5da64b9084009434125` |
