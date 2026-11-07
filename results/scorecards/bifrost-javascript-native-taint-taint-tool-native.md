# Scorecard `bifrost-javascript-native-taint-taint-tool-native`

Adapter `bifrost-javascript-native`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69 — bifrost 0.15.1 — standalone engine; empty shipped policy catalog; open-pack acquisition disabled; BIFROST_OPEN_PACKS_DISABLE=1`, adapter version `0.1.0`, configuration `74067dbc307c0e6fcaddb5faf96fdab1182cd45966c9c81846fe63b9db23a4e8`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-javascript-native.json` (`sha256:2357dcd3895de5cdd34e34df69d351dd0647654356ef7abad37d59e310acd36f`, normalized `sha256:2357dcd3895de5cdd34e34df69d351dd0647654356ef7abad37d59e310acd36f`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-negative.json` | `79aef3d717851e20719e6e010e4ebcecd66bff4bd5c8fb7f9c8eebd04d0c7055` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-positive.json` | `b19c258e4acbfdfed6647d1d8990f2f5ff47dfda94a17f9c05343159f28bb63b` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-negative.json` | `ef740f761e4a9acc99a3cb10dae12af8b9e8a7554da21fa3bcd68fd7cee679e1` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-positive.json` | `be964e0430fc7bc3eeed1a5adbb32a47854eba696ae3cdbbca55e4b9e93f06df` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-negative.json` | `9bdf73613d4f4ff4fcd2756a9de3bddd4612f3314a956a0b201c86b1459d7e87` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-positive.json` | `5793f5935ec4ece9a5512699c7523fa2e913c725707f45e416c55034e8026655` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-negative.json` | `087b11386490a68e47099acd8008402e8f9b96cea694ebfa12585eeca5befb2b` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-positive.json` | `17626083486330e3e893916b3ed36b228571dfd3fba883a2901252a53eb5ce29` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-negative.json` | `c0c96e95cd0c55e4496f6abffc84594aa504fb612313d1ea8599836411784fe5` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-positive.json` | `a95f57a429be4997404e8fd8dadef6e1814fac24fdef3f266c28e0e4d4087f16` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-negative.json` | `d0d4e743f033f41e6ea0346edf782f70889d3f94872cc9a13ff3bed88b906005` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-positive.json` | `a8b80035aff6746aa5e6c1b28c334b56db4f1c0a16ec40f6447be5fbe7823bcd` |
