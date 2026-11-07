# Scorecard `semgrep-javascript-native-taint-taint-tool-native`

Adapter `semgrep-javascript-native`: `semgrep` `1.181.0` (build `semgrep-oss:1.181.0 — 1.181.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/v0.9.2/javascript`, adapter version `0.1.0`, configuration `aad8d5ebc99315071a882a84c6cd495ce47088d52a36141876501f85ae341795`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/semgrep-javascript-native.json` (`sha256:af50061f4e078ad3680ca89df6d2cb74ca0b162d2fbf5f1fbb84966dcd7c995b`, normalized `sha256:af50061f4e078ad3680ca89df6d2cb74ca0b162d2fbf5f1fbb84966dcd7c995b`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-negative.json` | `950e6e475058b45a4864b0c0e796dba0082101a246dcf24d0d761cbf53568a17` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-positive.json` | `c7427b27a9797a0a65c5d5ca5161856781254533a0bae5cbf934c1d5f6aba5d5` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-negative.json` | `b4ab65228d0438257b0b08fde971982e1b49d478ff2e83f1b3528f9feb98e914` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-positive.json` | `f12eaf0d01077cfc2d4410df428d87a4dc9b87b820f996fc8e133ee18202f3f3` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-negative.json` | `ed1c4d9f11da3894321ef9609dcd60d011658522ba90cee63566b65efd561de4` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-positive.json` | `f937cc34513bd023eb01109bc74c707b8f0bcfffcc5fb83d38a36f0ac4e97662` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-negative.json` | `ae8bd2176797b0cbcf046b857d2bd1c22f6f7e1044b9fd1e4ae372ea9f78c207` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-positive.json` | `e3470fa06281512b9d337a2ce6e3a21de47c826e043e15c3a66413726af99ad8` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-negative.json` | `49c7fb06e6a1a92b8fae5d258651fd9817367ddcfa6cf1bd9ced92ba5f656074` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-positive.json` | `42bf569946ab2bb1eb68a722257037c193ce0921805a69e77d0693851345f0c2` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-negative.json` | `cf032fc488025d68d53b686b48d082d3e0bbf35084059b7314db43041a7ba4f5` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-positive.json` | `54596315ed248bd0a4a16d4e360c08003c7805a441b61ff1d913208d2c41b08d` |
