# Scorecard `bifrost-javascript-native-taint-taint-tool-native`

Adapter `bifrost-javascript-native`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f — bifrost 0.11.4 built-in policy packs`, adapter version `0.1.0`, configuration `5a713cc1f51d45f3b62536a12775c297de1279ad8c015e627ab5411cfcd41bb1`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-native.json` (`sha256:722f1407989d33a7ba4d5a7cb3502d1f7222fe5e529d4742cd7301ce3204f24b`, normalized `sha256:722f1407989d33a7ba4d5a7cb3502d1f7222fe5e529d4742cd7301ce3204f24b`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `e326537f90c0c46c6e76d6b7fe52c74f765d4416a2bdca7b70ad0aba6ec499d6` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `8d363f517a3b05de88f9008ccc9ff1aed063e9e5cc2b93211cf1f6ffc21b7f75` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `92458a3cab623e7bbcc4e680ffb599f196d14942b434ee421d56b4a045265e90` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `4e4760b5d0565f03f1c657802e88c630efc9cccaa7930a333a23655f6d4d1d20` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `1dcab3e7aa84f9913f188633c271f9eacf86beb043c40c014935ccc4dcbb9e96` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `8f65a5668534efee961ac12be184cb3af5b5555499067d199c80b6da7067e9aa` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `2d71d67710faf4c31039e0838b583d2625c7d978c57163e340f99b562cc80d8e` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `33433d7e2343aae67a3a3b9ae93256595f0f8f5040dd614541819cc8f29d2da3` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `f1df4e0e24f8e5ffa37f2040891bbaa410df5ee05d5ee2fd46b3507043755bf2` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `ba668288a56105dc3312fb649af2044129ee0638cae5755ea2e70303d261612c` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `2dbf279b342c989538cb7f979c2213dd4f0534962519cef20854084e36f4dd24` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `77ae2329d6ca906c76783a8e3be98e6bfcbabe9b38c852594d5242086410df5f` |
