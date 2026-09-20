# Scorecard `semgrep-javascript-native-taint-taint-tool-native`

Adapter `semgrep-javascript-native`: `semgrep` `1.177.0` (build `semgrep-oss:1.177.0 — 1.177.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/javascript`, adapter version `0.1.0`, configuration `1d0f9e22a5498e46b83fa635f2cd880d015eb5220c9ef1a606c249a5e04c95c0`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-native.json` (`sha256:5bebf3998de2ca550155686718ed911dbb0c604e598ac4c3f036e57e6edeb894`, normalized `sha256:5bebf3998de2ca550155686718ed911dbb0c604e598ac4c3f036e57e6edeb894`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `ce28ed58234266fc5f6928f93ea55c54eb22f32cb20310b72061ff19a7854c7e` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `0bf2200522b31b8ebba6acd1249b63f88905cb4b05889ee105820369eb0e4266` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `1f697fe135f9fa5baffa6a989aa621dd4b781e628ed2a5e0bcb610c129a6c323` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `0e59675eb2865ca051fb3b35fccaf1c2449b7101fddef8156678ea5e320a0d04` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `47fb42c0b8ffd21d16c3dbb1b0e1dd4223025769ced901a6137a942099253836` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `f6b6e18739ffab483a26541cfe3f55c0d3d5968fe96a1736810dcd66205719ff` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `75c783067da658d221786b8e970bcff5ea84c55edbc09936c6b7e7fb8ae55727` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `f23ba6b749fd20df38435c4e4422867ac9b2e59c26954ba896296d31a5a0e734` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `c62490321973c2fb960b169b08cf3e9e52b19919e5dc1129950e4dbaa9eaf89c` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `2fa621317d76b196466750f62648babacddb652c57bf56891e99be354293fb88` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `410871f55f8ebb74c4988a36403b214df43325d848debf1d0c09ba8bb7563ae9` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `a3f71497072a2d84273b6b371cc8cbaad4d71c2bb71e55b2c7b72ae16341027e` |
