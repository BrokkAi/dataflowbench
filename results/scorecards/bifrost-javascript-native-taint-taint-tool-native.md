# Scorecard `bifrost-javascript-native-taint-taint-tool-native`

Adapter `bifrost-javascript-native`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2 — bifrost 0.11.0 built-in policy packs`, adapter version `0.1.0`, configuration `9dc6087e1a19bf137d603043789bb6d9bebc945fa5ad54ac4e0aee6113fd16a6`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-native.json` (`sha256:062f96e4537db6602ae5e6c1c8fd4caf270e8bb93e303f84f51ba17c8e4152bc`, normalized `sha256:062f96e4537db6602ae5e6c1c8fd4caf270e8bb93e303f84f51ba17c8e4152bc`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `ecde09019cccb902d95be0124c591c818b206340bc36b50d9ea040abaca249df` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `eca99fd6a4762122f996f9771265521dff10bf9c83a51f6da0217b57b94fbe10` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `02e7f64e0ab946c8c01053d83c9ed9c8b02ed583259831e783cec3265b2693b7` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `e1ecf453e3ad8db7e9ed4529504573691c84621d72fabaacd129f96c5660da49` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `a3f03f85eff2e4c5ca7c4ed14bf7896b07b2636e33f74c05e83cfb1fade60b97` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `b21f5a3a2950b196d3f13cb247915f6c644553534354e1c93f70b0cf73c174ac` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `3d1ed598f42ca222edf352ba948694927ab8466c2797bccad89870511a744828` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `d024d811ad795485ed5a887d9c8a4f568ccc4d55af740a1d41edd3629ced99d3` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `c2bb171db071d793771d52e1f03b5b72ff10e7031d3bccaac6278d9a88aa3c60` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `e7a31299cbaed6f1a3fa35af2ace487db2122360217226fdcca4e971cc0cdf1c` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `38a4ce586507daa49c658841df0bee63c5253f99f70f3173957a7e4d2d363ddf` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `d0e79a95e738094944a85a44d20a7520eb2e0cdab052a7ea21062f5fff5a1814` |
