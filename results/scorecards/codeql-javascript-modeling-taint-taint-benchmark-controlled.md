# Scorecard `codeql-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-javascript-modeling`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `50f4a31741fd93420f8bdad4cbdea9f07dacda897641e12fdcdcdc8d7810e910`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-modeling.json` (`sha256:a3e6f90dd6f068b723ebcd6e9e73c3300452eb1d9ccbf76d617f82af1c5f5525`, normalized `sha256:a3e6f90dd6f068b723ebcd6e9e73c3300452eb1d9ccbf76d617f82af1c5f5525`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 12, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.sarif.json` | `c734c17c1f446c75943c61d768fde7b780fcdd9f770c1e3a597b18ba04852377` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.sarif.json` | `d786c1a6df54b14ce760b6c9557259f2b848309b8fb925b2904b96c1465bdfe6` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.sarif.json` | `9baf30d00192645a7e0876b364e4ab7639b34cdeec9284216677512940e59804` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.sarif.json` | `f3fe589f6e3444c3ed3ad725c8c771d6e90cd8b340ed6b32a1f9a4a453a2ffc7` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.sarif.json` | `2c0f23bea189de5f3dd226c3bcf35095122cb340a08d601008f293bbf9bd2322` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.sarif.json` | `57aa63e2ec59784ffa25bdb06c4796baae62d3d2fec118cebc103b2c75008ce9` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.sarif.json` | `ca037810536565b17db9d358c4bad0d401dc91a756c8fb68e13e81fbdadb9ca7` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.sarif.json` | `49f86810990d9d3509520a157c244f3f011ef343d34d17092392f8ce5b50f841` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative.sarif.json` | `ad2a7e9a7996adb99c7540cc8c62cc497d5d062d7e4979e68489d718bdfa963e` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive.sarif.json` | `e9bdf1ecbea5c344e75b770c87025840c4d2dd0f479237dd8cb9b89eaed33fcc` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative.sarif.json` | `ea7c63d1ca7fcecd6e62cf284fb6a0030c4cc8efb4746bb41308453d99d0853b` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive.sarif.json` | `7226df1c521fdf6d21ddf119a9fed8a2f0aa98011a701a934c6630720d5f3b9d` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.sarif.json` | `433f95e262f19e158485942060f11ee52fbd33b1a55ccd1f66096d7432c3c111` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.sarif.json` | `feca2122893a3f1f1cc9d4a08ab42a58ed2ea4a351604b5156a1d6ab627e3bbf` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.sarif.json` | `ce048815bfe923dcc7931dc6e0c305967f9fdd4d2cb7f01c4ce3e270d6c8109a` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.sarif.json` | `f1b112c88ad24dec3d5fd8f8d5478b3c729bbdc941c7f9e95954020e9fd6fd58` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.sarif.json` | `2f5f9080b70f9b85a8b5feb99e97844559e9bccbb5c08541fc48b79142638f93` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.sarif.json` | `3fb6175926c9c2018c5ab024347caf463939c07b8a37f2a8b1ea71fc4f513f2b` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.sarif.json` | `ce9ed9bca2b58beb8aa3ab8e1ae516010da738b460c59d216ee023986e77455c` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.sarif.json` | `5e444f767792d3bfd2a12723cd2110b12b7f74821eb3bfa0babb45ae5d02246f` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-negative.sarif.json` | `a7ed1a5267e36259b32b2ad918e8e9bb926b6356c393c89f2da5fc29fa7df543` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-positive.sarif.json` | `d6d35f5bf4b2ce95b2806e72d08be2367a6f1a4bd9b008a3fc6f424aa6965448` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-negative.sarif.json` | `f4728b0fcc5132e0309f61b05e102594eb0beb0e0e757e9a179858f80e47a555` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-positive.sarif.json` | `91164587b160c0f0937e59861bd0d6af58f32f34986d0d4e1675a0938dee9f34` |
