# Scorecard `semgrep-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-javascript-modeling`: `semgrep` `1.177.0` (build `semgrep-oss:1.177.0`, adapter version `0.1.0`, configuration `3ef508c524fcc97e5ba6b706195ea474602f04574d92be3ad80a4720c9fe09ae`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-modeling.json` (`sha256:7f5ee098b46a6a63090c87fe6287e7cc31ac83fdeb57c5a826b66294cd03cdf1`, normalized `sha256:7f5ee098b46a6a63090c87fe6287e7cc31ac83fdeb57c5a826b66294cd03cdf1`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 0, `unsupported` 14, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `b42fd6eb8ec3ab5d9638bcb9e3b6c07883cebc59ccdd6b023a646353350a1361` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `a2aa0cc116ae15f4179cf011d70ad26af33197cfd251f1e79057d7ffcdb5c385` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `a578b69695d41ac1e53593f24237069fdc7ef0747613352532e0594ee2f7d612` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `713a819c5a6cbb1fecbbf01dac72dcb6ace7c5ea7515d8c70c7a6d4855b0f81b` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `74767bbd64f9655f681cb3b664454ef068d82d819d5e414fca0b270caae3b9f5` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `eb44a603eed6688571ac84cd0ca3cf4d25bcd9b52a0415b64df2d48511b64ce1` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `a05e7aff4ee863eef9d48029d96d19dbf012df9d4da616849759bf6e94b13f5b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `c5e13fd091c8b4bb03c9aa8cc515781f5ec8a751125f9c3acd009ba6139b796d` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `84b3d9e01bf1185b2d50098d55c05080f16f245c5e7af0e6398525a9394a6658` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `adcfdc7a95de34a584be3491f5d930e90ebe011352be809d5ed61881e0e8f775` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `55bdd7be7f5f3d188702ec1c6e9521c732de9c04c805adca6e3da5236d4a7c61` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `9b3a57ad7a72a70d279124a9991297ca9dc9141718300eec170c21b04b8b8de7` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `1c0c7b9d9ce44d36fb733a9de473d41a4e1d187ff47b525f9f557b593e839f64` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `f6b002a9f585a58c6c53bb981c87d9967d67dee381c9a1a32c4b24e40309456f` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative-unsupported.json` | `e122dff166fcf16e1e453cbc3e235b8ea9edc9e3d71f1b8a94e837895d62e3aa` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive-unsupported.json` | `f964cec932960297512c865f0add9643e5bf77499b291d150dab35ea76c82626` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `788d03ab921d163b5774daf459ba08fe4bdc344b1ea3aa6956c7fe8f0a73a3fd` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `bb6bc9b542368d0e2de8d262ca094e6174ed46d227e5249e548a6ac699a294b2` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `2c896afb4f6983c891550648998cfbdf3a2772aaeabb3d1ddec57a9dd69c2e30` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `f67e710eca6f4db77f49f1094905590b30dc3a3eb2fb79a9c6372024f172512c` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `fd790a8bcfbafb0c90deacbb6286faedafbcd816001d311f049389689f8f1db6` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `d775110d1686adffe93e94a91f6ae1ef5e3eff8c5e301fa8d4cdace4c1a9bd74` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `87866afd64cfcd01e1d98d50d3557d7f1bd82bc35287a22bcef98c7cc73a6c18` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `191b926b2f3b27575ba332b8dba8179b5877f2f420c8cf79a9d3a687bad267e5` |
