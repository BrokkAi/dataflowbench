# Scorecard `infer-java-native-taint-taint-tool-native`

Adapter `infer-java-native`: `infer` `v1.3.0` (build `infer:v1.3.0 bin-sha256:17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62 — v1.3.0 shipped Pulse checker, no taint configuration`, adapter version `0.1.0`, configuration `751e6ca8c79a2cc269e26a2c302b8fe8035780127b1b5f9e9753565f51368114`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/infer-java-native.json` (`sha256:13e3be0fab60b02426efc4113446f6277c4a141c43029be50d078b8ec87531ac`, normalized `sha256:13e3be0fab60b02426efc4113446f6277c4a141c43029be50d078b8ec87531ac`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `0391403add8c5a7704b04d82d894843d103a8bcb708e2abdb3412c79c1264bfb` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `22c0c971d56cceafb33ffb94387db5ac4f6681d6a728e7ba5ad4f250e4714905` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `ef226cb9d58f5bc33221ac42c3604e7feab7e1e8b00c50afd458a3296056b098` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `3da620e7992a60d5d6b9e5b5bd42368b4151d5b7046c8794466cbdad7323d413` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `19f3abdf2032b3b2c5441e362235ac262611dc42030d67fcf241de349d53e8e6` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `230864e679977f456e0c1ad5f847494faed1549e969037968721617b7ccd849b` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `369cff4cc4bbdfa4d0db3b42616ef1cebfff392c71b28a9ec7ed7fa1294171e7` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `56db0f206f98cbb168a3a597ebc5d5cc8c2e682d37c5a199070cc2ac36928645` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `b8632f61dfeafa245649a0c7545d06f141599b9b46b929f27094d6b7c0756f86` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `a698edf2a571e0fa233ad234b1a2d3991ca147bf069fe41281367e31ee564d20` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `5065a8e0e2be205090bb1d80a7eb48d54ee680065f7e9ad119e835713f931fa1` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `4d733c1c28bb951d690816dbf1f2a2b485e1e467a7f44a436ad20a1dcda99912` |
