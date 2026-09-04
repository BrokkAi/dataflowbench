# Scorecard `semgrep-javascript-native-taint-taint-tool-native`

Adapter `semgrep-javascript-native`: `semgrep` `1.175.0` (build `semgrep-oss:1.175.0 — 1.175.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/javascript`, adapter version `0.1.0`, configuration `cdb837c39072d4ce15b174db97e455ef102148689772cec42bb118eaf4f13a38`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-native.json` (`sha256:249bd7e020955ab8f181a04ce1b257fb4a72ed93ac7d4eabaec0b572331db0ac`, normalized `sha256:249bd7e020955ab8f181a04ce1b257fb4a72ed93ac7d4eabaec0b572331db0ac`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `784ed7a4be2379704e8963a7e8e06773a1a0f0c311bc93ff39338b3d76abf987` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `bbec9bc8ca7853005817e94329b78d7c214e212ebf076b743ee9efa052a7edc6` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `2b4570fb75d26780731d75d96dddd0fcf6565b1fb113bc835e2af0ba977efef8` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `32ef88acef1761fb71319f5ee3925c3a073f58a4d281c5ad1400557ec63eb428` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `c80f16456766f6ead34b7f4714df3d29e5b6ee8ea54d542b018d62039604da71` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `026fb25bb0924b47051c8cf6b036db47493d6893fa0e62c6c2cb569a2f43ff59` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `7adb2e24589608c3cb61736f9f3dc82c64c77299b347d95a632b5e83d79e09ae` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `d91eb81453f2c1d8c3f47ae2daa8ba7a3814f3eda5b84794cf99ac6ea5b85453` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `f4e666e5a6c2e0ae1280077aeab544afc52f41f6fe8927aaac87c39105822c9d` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `8ea9cbc2288e2e0dd4c3bd950a4e962bcb933e6e650815c3848b2d1c8312c7ef` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `3df32cd4259eaeeedd1426c1910fe2598e7d1eda0671e473df02afa61d91ee0a` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `a3edaa93a7fdbabdbc92456c8c2958f80fbb7bf70cd0e23425bd57d90e111176` |
