# Scorecard `bifrost-python-native-taint-taint-tool-native`

Adapter `bifrost-python-native`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f — bifrost 0.11.4 built-in policy packs`, adapter version `0.1.0`, configuration `5a713cc1f51d45f3b62536a12775c297de1279ad8c015e627ab5411cfcd41bb1`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-native.json` (`sha256:d230d03d85f1da191d492ca26bf83668d6f3761468339acc5f84997321045117`, normalized `sha256:d230d03d85f1da191d492ca26bf83668d6f3761468339acc5f84997321045117`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `9c861d280fb9e36f8b12b0e2f62d66e69840f1d3d5e3495b9261e038bc7f9651` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `f278c2839f3283cd9d0141800609df7b064ed80a3758c0e664bea2456ea5d9ef` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `3d150b8bec39d616823697ee75bc372d010f96bec2ceb38b33fea88be763383b` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `f9e4df91bba0a516652ebc2088c98bc98accd8049bf6fb80823a84e393da35de` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `761caff675b5465a42fed0e4f51a57f9ad331f3b66e6e1a67bef6196a5198a98` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `8b42af37639a3256c04d27390282f120a51c15c25171e503f6c5a47492684de3` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `c524ad73305e4fe8c26abf897da708522cd445f4bf00c9154f2a3367f9014de3` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `4a385d7d3e2d3fe2995fb3e1c07468551e8467534454b530243544b21146b534` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `b306e511d916ba61549e2443adde5bb705b3a009b52643d72070b2b1c7ec25d8` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `93dea4956bd930afe7e9b2e682fe6d29a0161cb6c3e8354966a09828011d2beb` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `52fd575eeaa1119378fbba16c274bdbb319a1d128da959c71dc19d54965db9ae` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `61055664cd196997fe630fbef2b5b01342c5313de7eb4eff13a586fd984b30af` |
