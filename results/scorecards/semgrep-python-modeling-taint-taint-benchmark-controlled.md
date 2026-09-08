# Scorecard `semgrep-python-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-python-modeling`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0`, adapter version `0.1.0`, configuration `a2eefdc01e1df0c60b7aa2ceb0967814426f9211b61b79be0cf11de92f0b9825`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-modeling.json` (`sha256:c52d98d574fdb514767b50a8b763360c33d98a74c81d4ef8ecde771fd0131acc`, normalized `sha256:c52d98d574fdb514767b50a8b763360c33d98a74c81d4ef8ecde771fd0131acc`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `e6161c4b85c6c1e7cdc0d16d172118f0fa54d5b1b858a3ebe8d64f57cecaf887` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `360a61e638bf56e3119eae1b47344aa9fa71c0e49c302c3c906899c763e220d7` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `77aed3792c88b9f0c00171704b151c16f6dd2f186a99f791d0cdbbfae717ea73` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `ed59e82795ef48e8a3f1ccc2a67e778af2ef81d3dd89acbe7a8602497c485595` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `18443aba3fd1b779e347987b3c1465681252721cb95757e3c099af912ca0636c` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `0929ae986d603bdb4b374a033e3cf04bb69d1b40170b83117148c19870fc577c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `ad06328c93b394b2db32edffda7d7b64c3f31b8fe0c5a68f0b85292961bcc1b2` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `276248cd970c15a21baaffb1d001aee6ab00847f550acea8932b0552d7d3ab1d` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `efe049401e86ca36b7e9738a0bf3681706637bf2af9939d71e75ad1877b59fa3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `0fd054a975aa9ec16d675448c109d7efc02802f94b5e96d0712087580fcc5aed` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `b92003a5c9c44c00df8180cbb21a43495e347e14127db3be6975f5c141bcfc6f` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `1d9be2c57260cb75d1114424baf05838f6a403ebfea886e130534e97f4d37a9e` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `dcf9f366643e95c1d2bf42eba87ee27b8eca8ce25a8a5e647eaa0f9d598aea3e` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `f114685ce852296e5263b642a49a1020b81d62b1f4ed4f12f0a1ac9635efd1fd` |
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
