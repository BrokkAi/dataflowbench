# Scorecard `semgrep-javascript-native-taint-taint-tool-native`

Adapter `semgrep-javascript-native`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0 — 1.176.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/javascript`, adapter version `0.1.0`, configuration `b967e681ec7440927e1b11617873ce746c12ef7beca50b90c714a57fa851c4de`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-native.json` (`sha256:417dab4e591b42003bca6ec418f4196a0f67c7d1970f6c97a6b1b51d379e93e4`, normalized `sha256:417dab4e591b42003bca6ec418f4196a0f67c7d1970f6c97a6b1b51d379e93e4`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `0c4a411982caab1f1a257cceec82a3f94da1b38829e48f6f024b1e51ab5b7591` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `f7f938ba00ded8c1ffca515de5de052a250d0f3716f1a92bed0f1ba4b6f49944` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `dc2f9f6af4c608c8fdea9ae990b4a48a322b8af95286938bf2e786a98e2c105d` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `cb585ff54461a6b95d024103138651a90b83bcc65fba1e5e7aa0b076ddb23ac2` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `4032e960fff7a58dcc7805242bd50a01549706e83fd661b8b2c1b4c357bd8851` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `c2723d128563507053525b632a45943878cad63e4a61c6c198bb7518b49419bb` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `adbf987243836da1b47a8823e81061e4a56b508abeac3a8b31bbe37acdebf6fe` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `bf678e35aa339c547a8861903d4b57c506535fe19601641ba856b68cdd2dad93` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `2a2d50d95fd5a8c28e5d63bca195c3518a0c7831f5e0d1adea17339a2b392983` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `23f8a5d045c08571d997a182234288d98e223b7288f3901e79e33f8ede6aa804` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `1ec1d18b8a605a419a00262b823070b179fd7a8a855e6bdc90c87fde20627f18` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `0aa80fc846cee02e2148b85b02699f74c93d9079234325b87fd74b33b21536d0` |
