# Scorecard `codeql-javascript-native-taint-taint-tool-native`

Adapter `codeql-javascript-native`: `codeql` `2.27.1` (build `codeql-cli:938af3639d0709b587251e45d9f8d2bdc3505696 — 2.27.1 shipped suite codeql/javascript-queries@2.4.5:codeql-suites/javascript-security-extended.qls`, adapter version `0.1.0`, configuration `b79ce0c0c9b42f7ded700c3c0b2e11f18d6476ee0b9febf427943123d977c85f`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/codeql-javascript-native-attempt-01/codeql-javascript-native.json` (`sha256:899bfe02839421646f5bc14488049e3d660cec8ee997be9c334b324b737f877b`, normalized `sha256:899bfe02839421646f5bc14488049e3d660cec8ee997be9c334b324b737f877b`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 5, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0.0% | 100.0% |
| `local-flow` | 5 | 1 | 2 | 4 | 0 | 0 | 0 | 83.3% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 70.8%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-negative.sarif.json` | `54a267127e6b88c119f7cf7e474047f105d5d13f3a179cad931c0d138b12805c` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-positive.sarif.json` | `f03bd2be088e01d57717962d55b35831e495823d47998305f212132821019447` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-negative.sarif.json` | `019258184919c5c12da3affc9238a8c45091365552a8374358a3b379ceee2bb4` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-positive.sarif.json` | `6fbc2f15ad148e775acdd808e7e8b7f6c6fc57b4829f309e898a7f2ce6b89fa0` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-negative.sarif.json` | `7267599e138e9968c2762ae5d56676a35cc8b7e5d674f06921e925930e9f4d23` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-positive.sarif.json` | `363a51c3e77b754d8d02ebb22e3e40e54f191d3ea5084b97d658590920f4a118` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-negative.sarif.json` | `6987d98b1acbdaa89b5beef8a4622b4e609aea5c4a63fe48a5a62aa455887e15` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-positive.sarif.json` | `5737709300b010202a3c298ddd44782833faa02b68e6a32dd1f821e8735685d6` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-negative.sarif.json` | `ed7ffa9f2d55702d63cba6a7c476a029b3534b9a525ac7cde3f1bf50e650462e` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-positive.sarif.json` | `9470decf840f60f235cfae1ff4ebe4604330fc1a7a93fda8aa1470c757abf653` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-negative.sarif.json` | `04cf0d91d9ecc6ad355cbb86aa6ad9ace22519d9c67171e0cd55034b1560688d` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.0/attempts/codeql-javascript-native-attempt-01/capture/reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-positive.sarif.json` | `0202246e3519d9435bb9def8281ae4283e9b885d531f0a80f05db1fb59bf046b` |
