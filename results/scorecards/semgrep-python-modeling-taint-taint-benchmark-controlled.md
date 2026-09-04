# Scorecard `semgrep-python-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-python-modeling`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0`, adapter version `0.1.0`, configuration `a2eefdc01e1df0c60b7aa2ceb0967814426f9211b61b79be0cf11de92f0b9825`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-modeling.json` (`sha256:da47b6ec6eecb9b3f26ec1b5c4d8476b030e2fefacd4281d9e83048a03e05749`, normalized `sha256:da47b6ec6eecb9b3f26ec1b5c4d8476b030e2fefacd4281d9e83048a03e05749`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

## Language `python`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `1d19f67ebd8b5799aa335389e8797db5a9734677a55dd2832bdd18083c16c939` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `ba38af03adb4cc862d453c507410ed8d620bd6f2e663e4482b6d0c456d70c10c` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `c8d7dd07de37f6379a21241e52f4a48fe0b758eb39939b7955e0642a76e62f42` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `edb94404c88efa6a6d7555ce2e9d69e3cf1d461001aa41f12c26090c25591137` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `99fafc7057d078b10fa1209e9b3b2c6d786d42a0c4eaaec72a840809e0a0072e` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `1547b85f8b520e98f14e746caa87a226f24e8bbc4e76ccc2325df7fc865c822c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `48f8845ba9c540dff981f348f589eef609059e1623594624410ecba730d657d4` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `a09be71aae99e8a59320493f05ded55b956cd1220439633f4a42989979811255` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `efe049401e86ca36b7e9738a0bf3681706637bf2af9939d71e75ad1877b59fa3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `0fd054a975aa9ec16d675448c109d7efc02802f94b5e96d0712087580fcc5aed` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `b92003a5c9c44c00df8180cbb21a43495e347e14127db3be6975f5c141bcfc6f` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `1d9be2c57260cb75d1114424baf05838f6a403ebfea886e130534e97f4d37a9e` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `22738d75461925551d58706a2109b2ee9f0ec765e040f11c00dbc1c022acf0e6` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `3772b88b623efec86d4f5e5d3a642c8d01f9bd747d52646a74f78540f879501b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative-unsupported.json` | `f2e038230dbef128dcb240f7987320b05b142ce22a5d7054eb52cf78178d2bdb` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive-unsupported.json` | `72b95a66551bf26d53fe1aa49376cafab85aa1417e3e7659599fec45931d932e` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `4c1b5b22bfcabc96609fa6418708996f8ea8374c73801a4576c048061ff134df` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `57b82de9b5b0693e766849b80b9c18403f63f790f3acc2a6e9d5634bc53f4a68` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `ecbfb1cbc7b2910a0caba2e2daecb87aa07f68583a4bb207b57557f81bc50b3e` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `969e838c9861b0b96dc0769ba2bc63f6367cc410b60530ede7b84701b580c5d5` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `9f1610dbf60d1b99ea764cac0fd80385860c25b2b1374b2b59e0bda38ebc07e4` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `c750b165282915df205fed81629ad9490005e46faf006383d96424e6d6c233d4` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `d90153bf830787b1bc7706ea3da41ed1b393cd24cb8f7ce9356ce409481a627e` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `81d06eabd80ea72d486195f625415de9422eda073549a1011bdabbeac2b722a4` |
