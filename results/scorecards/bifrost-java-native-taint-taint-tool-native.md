# Scorecard `bifrost-java-native-taint-taint-tool-native`

Adapter `bifrost-java-native`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f — bifrost 0.11.4 built-in policy packs`, adapter version `0.1.0`, configuration `5a713cc1f51d45f3b62536a12775c297de1279ad8c015e627ab5411cfcd41bb1`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-native.json` (`sha256:8a54dfb974cc30314caa6a0a928468c42524a6f7be31b8fde6d941638acce92e`, normalized `sha256:8a54dfb974cc30314caa6a0a928468c42524a6f7be31b8fde6d941638acce92e`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `538a57ce59c1a281ba1f4e5b17680a73c6dc67dae011a4c52c91b4e965ddf469` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `0682cba3d0922e519e391bf4a26123d2aa8412af78df36344d833cdcb2aef867` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `63d1b5e6b8ecc1572c65640c221e58407d7a3366d4c40b90d59b6899feae53a4` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `a935d067b5d933e95da475e780d4dffa843856fca8f165cbaa657174e991e3c8` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `e7cf14b1f99203a960e84b75c3a469436ce7a16171f1bfaf432133a914e1112e` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `b73ded629ca1d717ef5f9c453b3e2a09687a80a24e10add87dfe9b6332ac2dad` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `a91cdb88b8503f828ca7296e5c967373c51f48584a1ab0069d82ed223f4cf144` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `0bda5796ae531bf2eacbcbd44f7b1b81569141db29b285349b7f2f8d675daf43` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `8ce25b9f38b0784a9b6850965eee565a031458ca4be5bfb9228519c2cad6e160` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `d9d28fc2fb5f2ea8760b5169323e4b7199df9022f53772d85a05c2cfcaf0c334` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `5e2632098f79cec69590d341d829c91769c3db36362307483750676de6309fc6` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `eb6824769d5543d6c36a3cd842b422dcbad04ffdb6922cdb481038631b1c619c` |
