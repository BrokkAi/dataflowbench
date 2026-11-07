# Scorecard `bifrost-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-javascript-modeling`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69`, adapter version `0.1.0`, configuration `49d4335a42e6893f0797bdb1735b8ea3fb40f3e554f9086595f6c1254ff31203`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-javascript-modeling.json` (`sha256:b8359130b671660a8933b7ca0554cdaf78c4a706020cd83a67ae76a6e3621f1a`, normalized `sha256:b8359130b671660a8933b7ca0554cdaf78c4a706020cd83a67ae76a6e3621f1a`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 2, `not-reached` 2, `inconclusive` 4, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 4 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `19ee96cb4c3fd87c48ffdc747e72e064bb827c3c909a5801ad71613747464b4a` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `99d249a61222ed0eae9db80c715f56e32a4fa5784d316f5f0cc5f944130c7b45` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `524dfe2572e90451dc992ccd74d00ea3beba17745ece186a0b33ca24a5f14735` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `af1a370a76584746f2192a3770edcf3b1bd1823d2e44aaaeed66def7bcd20304` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `cf975ad431df4151d3b2bca805ce09c74ada6b929d61471d34508b1d44563141` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `9f7373baab0fd795db75d45291383728c42a061d33880bcff37980c79c8a20d6` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `de93e60d7a3302026c420e049dd53ba3a2d9d0b5fee0c662fceb03bd9257cd1b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `8c4fd57e9a3a152dd4c8261a9a979263bfab42853be3a7b1b7cafd0b194be9f8` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative.json` | `3a7d88a02295b1776bc3c54d2fccb32adccd55684960dbbb08e92d3fd7ee8f03` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive.json` | `c63bdaef5d6f4e73e34a0f10a346e05451a3159a610b65e03a4549d3bd1e2426` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative.json` | `04891aa02e6a343bdc8aaa485fb5267b7c103f54e2deaf518a6797062885f352` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive.json` | `2db089bbd637339871deadea804f17eb367a6b5376002b1e315d86bc492406ae` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `06ff5176646fba0b27857ac198b50f0d841e6a29f9c1e4d0c87b9e700a6d06df` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `3206acb38e302fbba03c66f22c8398859eb4d5f47cfb38f68cf7454ad10fc8e0` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `fbba51726e85fba1df548d3c36a69b0221b9aa0f7ee935cda9b153babb1afd9d` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `6c913bcca9c7532d143ba031258f195dafb96764268daa246e9039ebe09d1e29` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `eb7e32233e5dd79e25948970e0826c464d4ac35a06461ea2d6326afd7ec56473` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `c231b2331f7a4b4e45868c6818c0c805116bacdb59159e55297e7b6cd052b8f1` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `d91628b44fda78a4af00d8d076ab02818eaf8b4b7b6c663559e8d0c279fdc0f0` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `9ab6b265df9b42329f8092e9ad33d15f70d4de37485f58a50a0257ae63ded6b9` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-negative.json` | `a3e477da43406f0e38c1fc148345e447705f11682b9399aaa5fbc0eaa3003cb8` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-positive.json` | `ed703297182e5589653351b9f8fcc809dbbeb37bfa604e53f7a9e811abb761d0` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-negative.json` | `ce6d4eab087069cbabfe32ef0729169cad619cc183f2fe43668aabbea18c6782` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-positive.json` | `3359e28ecd6717118e901abfaa290c6830139a7d512493795f92e8561222df14` |
