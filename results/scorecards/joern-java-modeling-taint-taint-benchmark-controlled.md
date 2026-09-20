# Scorecard `joern-java-modeling-taint-taint-benchmark-controlled`

Adapter `joern-java-modeling`: `joern` `4.0.628` (build `joern-cli:4.0.628`, adapter version `0.1.0`, configuration `55282607023d6902aebe9e2e4199542f04b407229ac0ab04eab9b70dd4a6980f`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-modeling.json` (`sha256:1c789f3f3b15b73f03b3cfc45b753cf29d36d21f2ea1ec1876433f2d4ca13414`, normalized `sha256:1c789f3f3b15b73f03b3cfc45b753cf29d36d21f2ea1ec1876433f2d4ca13414`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 10, `inconclusive` 0, `unsupported` 8, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 2 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 2 | 0 | 2 | 0 | 8 | 0 | 0.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 50.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `6d7b3d03c154a6aa2dcfe7af61215eba12066e7c99544c64714aa650d018e9f8` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `efde2c59f934f00abcdeff4d3347b29a171d8bf278d34e656b5155d862d3d800` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `72245d6553a6c8939eee1d7990b8ffaf4cdd4bfbe00c18f1c683b1a2dbd0dfe7` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `d0eedc7ad9b596a4899244f559b4236d5982f5853a6599778db177c2ebb347fa` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `64dfefabad326850875d0ad9f71a8e75a2d0b5672a10982122a209249d382e60` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `cfcbf465535dfec8cafaedc20fb304ee6064929c27cfd3ef9647adb1567fe4d3` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `61d88680886cd09c7618b787c1315c8c8093d57a009a24f7bcc88d3256331ae3` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `0edf4980bfb570814abd1be3aa22b950f8f9d4cc256d8e97022baa4267e115e0` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `bfe4ecdafd0c4029adae4ab3a55fe2e7292aac66cf289af646ffb7b21f060905` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `1a15b98e5ec46efd85b8fc90cf38a29d64c56604566095397675ea1a91ea7d39` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `a7d866f62377d4746206d2144b974fa9a6fd298474366d66f3cbe931e08bc95f` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `1188f142a0dcdb65c04e4f8b85112f3d975ae1c4c3b16ef16b1d3ba422594854` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `b57323cb3345e678f6a5daa415a73b1ffd3168c6e91272123c99546839e16f9b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `f9f49d9c6bc430909b883dc5fb863d9313707c275ba271d8df92eb02513c297e` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `3d66b2a5d5754ab20b8c8cc354c4e64c974046e5e14d85d252858c800e69e51e` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `641cbcb2add2676eb1610efc50566d81d48e6e260cb6966dbe45efd7fded744e` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `5eae17584062b41c08871fa20112bf1da62aa8aae98ac8e90e3dee0d48442e78` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `a3bfbb8ca9b64615caba20d9d86cccf9648a0761fcbccf2c19523515b5059a74` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `e056c3e634a0efcb7c86986319f4017a31fa2e2f1ca3c082bfaa0d88f2cba603` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `e3720a7c903f8b42e5d594bf9ecc66bcbdcb7cfe6110336bbd18fd1ef4491e4f` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `7bbb7efe2257945606758e21adf86176631519f5794723eb9b9c4cbc7be9fa99` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `85a6e7cac71236d1eadc7cdb28fde5b74a36ff6d9b27e49535193e9700a4abcd` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `b929838a3a8679fd0033c838c47faa58a164c71f4511cbd0f94e496e6dd53feb` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `20363b3f6668f60cab0f40b8b1539089a9707066503513ff194cdbb333518f13` |
