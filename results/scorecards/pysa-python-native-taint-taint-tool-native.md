# Scorecard `pysa-python-native-taint-taint-tool-native`

Adapter `pysa-python-native`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.2.0 pyrefly-sha256:6b460273720d857142be562d2c0c607e8ed8e5e752ab575b5c00ea3f735d8caa — Pysa (pyre-check 0.10.0 + Pyrefly 1.2.0) shipped taint model suite lib/pyre_check/taint with --no-verify (suite-sha256:1c2e41c525178d9f332e0b749ecedc5e4293fb570d0a0ab1708c41da7e49594c)`, adapter version `0.1.0`, configuration `6cc8640410e0e1c823bb914e6278dd49b8415a0f2977ece68e27618fe903e684`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/pysa-python-native.json` (`sha256:c3ad2ee142ea248c4ecfd111dda9efc98b2c83972f68d4570d889d0946e4fbc2`, normalized `sha256:c3ad2ee142ea248c4ecfd111dda9efc98b2c83972f68d4570d889d0946e4fbc2`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 2 | 0 | 2 | 0 | 0 | 0 | 0.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `local-flow` | 0 | 6 | 0 | 6 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 0.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-negative.json` | `da533a70e4c37ff0486a87111a8457af0674d95b3c28dd06a73bbf32b4ed88a6` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-positive.json` | `4aa4a7227c2678258f928bc7ef04a20d9057c15df2fa4b1eeff67795bd0c8f20` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-persistence-negative.json` | `1a444f46fa2a965a45aa1d0ed5339df8c8b0ff3a5e67169cc5e3ec4bcbfb36d6` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-persistence-positive.json` | `6b0ad43e374d41f9cce677be1f496839956cdf591b5f6d4eea0932c3c73380a9` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-propagator-negative.json` | `9f52dc0de6031d5addd479e480cb892fa05e4d0b45a73d67977443db52d063a9` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-propagator-positive.json` | `2624692b9f3fad37743331ed3affb9a57a6153f14c735e3b8a44ac43721d126a` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-negative.json` | `f0db05c5131f9638b2de0dbfcf5045d8441d7f1b0df431e73ff4d5bdc90d64ba` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-positive.json` | `0ee2cee9262fb387ed47b488a3808741558a48838d8920be5ed0a9d97d883aca` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-negative.json` | `367494be3154928109c7733815383ea1b77b2b5fecd540c9dbf73fe1fb05e0a2` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-positive.json` | `6b4610f8b68542773dda100a0b9fd37769bcc906043424daad32f4ec1496332a` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-summary-negative.json` | `bf9687adbdc46fccd3a7d989d39dbbbc620820b06e9344af309fcc59dd4b0074` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-summary-positive.json` | `4c2c6923ab961221b871c0a0a7271918b556562e2a177efe337419e0aac0db84` |
