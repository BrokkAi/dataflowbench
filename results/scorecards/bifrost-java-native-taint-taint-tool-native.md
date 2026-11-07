# Scorecard `bifrost-java-native-taint-taint-tool-native`

Adapter `bifrost-java-native`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69 — bifrost 0.15.1 — standalone engine; empty shipped policy catalog; open-pack acquisition disabled; BIFROST_OPEN_PACKS_DISABLE=1`, adapter version `0.1.0`, configuration `74067dbc307c0e6fcaddb5faf96fdab1182cd45966c9c81846fe63b9db23a4e8`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-java-native.json` (`sha256:4b4cd2fb66aab0c5491b19f6dbeeada8a12d6d41ddb1f4bc88aecd43093989fd`, normalized `sha256:4b4cd2fb66aab0c5491b19f6dbeeada8a12d6d41ddb1f4bc88aecd43093989fd`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-negative.json` | `8c724d648d8e5dc0c91205990437a26ed2764bfe11bc14a9b3c430c46dc68cde` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-positive.json` | `c55bf8d7ff0fb9a75d66bebede31f60c9fca481d611f3564f916fde501f9b6b9` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-persistence-negative.json` | `ed455e1f71c1abe1983334c8889d5a6dccf95cfa2e32228588c8377898af91b1` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-persistence-positive.json` | `fcbd9778a26ae2e9829159af1faa326499c73383bf8f9dbe21c770a34991972c` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-propagator-negative.json` | `572702f246cdc537efd7e1314bedde448d0ce998273be75d7f43ec96287c7e72` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-propagator-positive.json` | `17651be4ae4ab30a762d9145ddb2f6210fbbd6213887744334c4a525cbde693c` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-negative.json` | `dfffc0b3a93f0976134ea201773ff0bcd5c83571eff902664ee219112369ae2b` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-positive.json` | `bd9e0906150b5541fc3df042741a50ce4dfb2d7bf6b13d6b8fe90c19642072ba` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-source-sink-negative.json` | `58f5ae1dc7ca500e944ab3160f262101071886467863b19b40f201643da2b37b` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-source-sink-positive.json` | `227c4b114b60fd9e43175593184286845833cdd8a5b717ae9124be3fb77d76bf` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-summary-negative.json` | `2f771265af02e1bc88d0574ec8c6318487d5b650397261c143ff10651c1e1c88` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-java-native/dfb-taint-java-native-summary-positive.json` | `108cba247c847fc119c83990309710fb79e70a5cb71add9de8f2c6eae0d667d0` |
