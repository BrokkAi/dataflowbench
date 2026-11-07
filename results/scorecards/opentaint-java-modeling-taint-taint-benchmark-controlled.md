# Scorecard `opentaint-java-modeling-taint-taint-benchmark-controlled`

Adapter `opentaint-java-modeling`: `opentaint` `v0.4.6` (build `opentaint-project-analyzer.jar sha256:2ca93b6c33462bdbc23ceccdc5375e1a900682b33371cd906e5214dc7c48f569; opentaint-models.tar.gz sha256:20a96a50fba9ab6f6e98e8562019e5ecbe2a77de7947981eaf6e379f04065329`, adapter version `0.1.0`, configuration `e24a41d7bba6392571d3c6622e40fab227b8f72be1150c75b3f9657098be5859`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/opentaint-java-modeling.json` (`sha256:56bce727b5a83edb1cc2becfaafc074b3fc76c3c65df277cfbdf1bf2267b3ddd`, normalized `sha256:56bce727b5a83edb1cc2becfaafc074b3fc76c3c65df277cfbdf1bf2267b3ddd`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 6, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 2 | 0 | 0 | 2 | 0 | 8 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `617ca554f68237c8c0e9b5fbc8d8cb7b32992cc1bf9254c6dd914ecbba2f7237` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `1b38ef5e62da673330a8dcbb4055b7f823fc0b196b40cb9270aff321ce253bd8` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `70a499ad3e1ea6dea21b40dffe987d7ac9aea2134aedadf2f934ca4807fc01f4` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `0270b3481fa3b503811c0cecff07537bde719901a96e637b50d01af76d0343c7` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `e971657cce746c6424f2ca451ad95b432d39e198e7ee4d6c644fd898875e21b8` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `e6f0d97da85d689893eafea477a0cbff4ac6452c89f38189fba6a434dcdb470f` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `23ea5f1f0a0fd7bd2a6d3483e81d749b8de7bff7c82aa8ac189c058aa5b0e714` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `841501fa4a67cb573237d718ade8282d0d3dedc326a5db6d809b252756ea9eb7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `10d7fe06e734639c2655ff5f48e438156d420daa1dc7fa91c1d9d4d9d14759c3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `ce342fe87b07e9d3f3b06728495968e18c634a38ce60a07df852713a37c84f08` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `d49071d994508b34b292bcf9b1d932cdf153ec8b4ba8ba3b50c4457cfc98e8f3` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `92d55d4bc4d23f539b2e23a10d655ed04668ee4e6d8461bde552c4ff02b722ad` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `fdfb0dfc00aeb3ee812ebd5a8ba84bd1159d69dd119aef611e66a5b21131019c` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `6939be9216dc0d967d13cc58daa86fd95eec13145dcefecc0d81969bdb9eab1b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `629c9537ccfefd7501c16d83c86e169d0e92ce1266140a5691af4a2ab05ae48a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `8a4776e1f5ea27c3368a65aed9f2678f859c02c6b2d0acd7edb35b55c2813a20` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `0fa25b5a116ffc707b867bf2818fb1ee4804062f73980352b65ef60aad946482` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `a8dd3fae608cab48b6df1d17fac915473bbeb6fc007557faf8e073daa2693a8f` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `26e66c631cbdf353df1005fb89d5055b172b02b5a5b820ac34e87b40b63f6b01` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `2c30aa3f127b667744489a405629c8fa650ef8e7e20e08b9dc5fe98090d81942` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `36bdcb753cfddbbe97e3f9ed375c5712ea91658c5298fc38382acadc4dc4a08a` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `b32d275ee0f6e04674e979620e56b1c66d570cd887bfd8d529c730c16b0f7087` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `cfe9e4fb91a433cfcf760a76356ab0eecefd7f56022555ce1862bdb2facc9504` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/opentaint-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `58ea814929377d24ee8c4374e6f52e9314906b36c186de997d8bdbc8f7932c3e` |
