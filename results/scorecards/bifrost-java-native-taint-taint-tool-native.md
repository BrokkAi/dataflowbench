# Scorecard `bifrost-java-native-taint-taint-tool-native`

Adapter `bifrost-java-native`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2 — bifrost 0.11.0 built-in policy packs`, adapter version `0.1.0`, configuration `9dc6087e1a19bf137d603043789bb6d9bebc945fa5ad54ac4e0aee6113fd16a6`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-native.json` (`sha256:505a1e07f16585568efd5074d100114ed05e5ac6729e705d5d5368ce54f7172a`, normalized `sha256:505a1e07f16585568efd5074d100114ed05e5ac6729e705d5d5368ce54f7172a`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `ec1345d80b95b149b25ffd83bd2c957535d237b88fa4d27d9c4c16fe623bf735` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `aca85e889c93d7e283601c9a240c8e9a8f47b5d853c471c5d1e0c7101436c593` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `c9659a59b1875d036b3c12a7cfd5180c594403294134646cf8338e0c2a1eee50` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `2f5a1613e11a96e889f297f91570e80f2e27fc190c7ff56408ec3515c3b875d2` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `99f78b1dfc93a8b5d2ca923d5f7914c19fad4058ea4c3bb64b7f0ed2db447d24` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `afe8f4a02ab691520789e3273b759c3dda105acb7519467321837b8b4f816d59` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `8e1a2d874da24bfc26ddf8b43b3d98dc511166086be872f9f916753e47babd5c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `8b2d1d3a57375b5e14162e03c18ef48a4a0aae7ce005128bc74e78ca41ce2a69` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `89ce0b211fe44bc107f35d0bda56592345db7a4929199bff6cf1d5ade6563859` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `0beded9d5c01352f9e23ce1996f90c0ac8fd7fe74690cbd41e408a67e4cdd70b` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `f429a1a14f25b8896923f2426134cd6afff3af86370fd89a0b733c6c88ab2aa2` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `2b4f839a7b4b1239b10b18b0d1e582440379aea2ba4c1f3cdea9cf6cccb55743` |
