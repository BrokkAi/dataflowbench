# Scorecard `joern-python-native-taint-taint-tool-native`

Adapter `joern-python-native`: `joern` `4.0.628` (build `joern-cli:4.0.628 — 4.0.628 DefaultSemantics only`, adapter version `0.1.0`, configuration `47cce57071af2d33a8c7cdf27333dd615a77098d9ddbbb9d30c9b2ea1fdfd151`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-python-native.json` (`sha256:3acc8c28a78881375af56e22fe7bd5f589c5a23c6241cca0bea61bc63b1c94c7`, normalized `sha256:3acc8c28a78881375af56e22fe7bd5f589c5a23c6241cca0bea61bc63b1c94c7`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `9c6c41867822e79fa34549975ef2c716f4d8100dadcb585bd64b9825c92bf8e6` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `4c3bf28a73e37acddc9a0b2898a3afb2a7cbb73126c96c0d6c36e3d3ed7240b0` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `28dd839beadfdee85af439baad715ce2b76e8cfd97040eb6813e1197e7ba1f2c` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `cb7674e4be6c1dc204713a32914c6f213cdd24b25e4c442b764c6c802457cca7` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `744b7402cf0fe784df665f7ee528c7df2933b9c80a4604d7f8dddf3ab12795e9` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `6c95121d707e334d4dfd7cb7c5712b4cb15b1841991e5f76062de24e5136c9bc` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `e3886b9b770893dc9927b0d6b607e03b6c343789401f79db450f170d09cb7bf1` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `c91e26814c098c61ec915f7d2643a3f3b5ae788360b7b85b01fa4014e34d12ad` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `cd8d9f3bfba7cffaad4b6a472410abda4f485717c5673b8e77010c49396abf90` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `7a15f686f2559ff44dd6bf3e440c8e7a87c4e5ec9c38a0817a71e5cc11227906` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `cd531ec84fa967bd09d457fe53b9ac76449e6bf953d4a22d91fb012175515631` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `254cfa8b06656d152afefb4619c0c344dc243dfda648d33afbf34641e8a30ba5` |
