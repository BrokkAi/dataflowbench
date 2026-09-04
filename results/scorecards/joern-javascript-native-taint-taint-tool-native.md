# Scorecard `joern-javascript-native-taint-taint-tool-native`

Adapter `joern-javascript-native`: `joern` `4.0.614` (build `joern-cli:4.0.614 — 4.0.614 DefaultSemantics only`, adapter version `0.1.0`, configuration `44be7a7aa2af4289b8665c23929d0ca8aaa046f4b1db3a43f973e31a610ce7fb`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-native.json` (`sha256:b8f493cdb3761d9ee676bfac80ba0b83377750ef970d2d845a06107d4987ee44`, normalized `sha256:b8f493cdb3761d9ee676bfac80ba0b83377750ef970d2d845a06107d4987ee44`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

## Language `javascript`, tier `modeling`

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `3c1765e60dadfbf9c7b07bc64dadf74fbf78218fd2f0a5100fa1fa6b4c28f1ca` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `55078ad42e5f2d23f4fe3e563d64edb87ccfbf2efc489bf381655d77dd8b8042` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `57d22b0297199bf4bfed5743bd1683941b778098fbf672a1ca63dedf68365942` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `abc5dfc090a18cc05e1d415080eae062c69cc345e92d4e4e35255ec439f79116` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `3ad686544996dd749cd8353404484a231b7ddd44cb22faed29ae29ffb1789f86` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `7d49910b79463b44fc1149fc6b04bca182ba23ed355b878d6fc163c11aac3e8d` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `1153bcd16fbf95c7828a127a460eb9b10127f7d75f7a94648e6061e3a923e04c` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `cc65192381e623b33b95fb5b49edd3ffbb411e12c5f35c50c7e0b2b38cffc1ae` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `a980be68fb08655eaa2da842057149bbbd02f709fe0b86d8094702bd275ff907` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `0607d04f5c75c69609e93e2a13f17d52790ad59d9c0aa56d7a70a06d90f0bb51` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `4e8c046447cf65bbfd4dcbe78f5974e3cf9d567647892d8c3e535017f81f2220` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `687f88e05266085b7e7c51a072fcb13b7dfc21ccdf57f28fd16fcb768304efbd` |
