# Scorecard `semgrep-python-native-taint-taint-tool-native`

Adapter `semgrep-python-native`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0 — 1.176.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/python`, adapter version `0.1.0`, configuration `d392dc858c5fa5494c9a03e2c5f3136f06ea81bbb635573acea69bd082a74117`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-native.json` (`sha256:47778dec953ecc4350f75af9ffb36a22946523c84e877a05ca870bcf923eb8d2`, normalized `sha256:47778dec953ecc4350f75af9ffb36a22946523c84e877a05ca870bcf923eb8d2`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 10, `not-reached` 2, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 4 | 2 | 0 | 0 | 0 | 100.0% | 66.7% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 91.7%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-negative.json` | `f16327909340c9bb495c749bbe7171deb87972e14c61b92610dd6722c15678fc` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-positive.json` | `214761c1567904fff2869fad971c92c2d814c3fb69b3e7a8740cf324e2c5d64d` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-negative.json` | `3caf94be07d5429735cbd3c718c1ff449d4f8e91dc2ba2cdf4af41de45299e20` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-positive.json` | `8693c3f974d88a260d368f979f1a879939b2ff0584abb40c1ec367eeab2227ed` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-negative.json` | `1d4a7f8f692c70ed13e63e95d3cf9bbd2e594d0a85a2ffb741899c2f6841f9e5` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-positive.json` | `223a17a6e24e409fc2d010f99b8c313d5c417febabe07d25bc682df9a84bf3a0` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-negative.json` | `9ed6577d3fef6955f8bbb14901a8d244c1e7cfc3536d80f62797a06f64e9ba9b` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-positive.json` | `7db7b5a4288f94026f4aabead3c7c713d8e520e73ab7db3df119660949467a41` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-negative.json` | `9c01c3edd4f77f3b31680b290ee97b1784cb3050d2ca9006e70f23798f6e002d` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-positive.json` | `95dbc676cb67d22586262d2410a81372098beed5c2fef08fbe834d40ff312e00` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-negative.json` | `9b5da5d3bfd271df21c8bbfc5d240a95454658a086eba4b0de6865f6a373419d` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-positive.json` | `857566f44c5f2840c9490f1ea80e4fe2338fe0fc6fc80d881c5ab18bff9d58fe` |
