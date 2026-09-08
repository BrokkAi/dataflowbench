# Scorecard `pysa-python-native-taint-taint-tool-native`

Adapter `pysa-python-native`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.2.0 pyrefly-sha256:6b460273720d857142be562d2c0c607e8ed8e5e752ab575b5c00ea3f735d8caa — Pysa (pyre-check 0.10.0 + Pyrefly 1.2.0) shipped taint model suite lib/pyre_check/taint with --no-verify (suite-sha256:1c2e41c525178d9f332e0b749ecedc5e4293fb570d0a0ab1708c41da7e49594c)`, adapter version `0.1.0`, configuration `6cc8640410e0e1c823bb914e6278dd49b8415a0f2977ece68e27618fe903e684`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/pysa-python-native.json` (`sha256:64adb1284a96a51350af2559cd772cb6939b118e45ad71d7fdb9ea7e26525f8a`, normalized `sha256:64adb1284a96a51350af2559cd772cb6939b118e45ad71d7fdb9ea7e26525f8a`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-negative.json` | `41ae0c3023a52ef39325863ea7be01e84657355b5148e0972959ad4ebe80706c` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-positive.json` | `8107d1639a0ffba2e1b36af43f815caadd5399bb84b197ca1951ba7c987d100f` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-persistence-negative.json` | `120dd5ac1639b2e287ce6e99e37577c4645a832ce1a6eaff03771b02dab68762` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-persistence-positive.json` | `440da5287b5930b6d77910c2c60639602ec3b3dad9945e6f72e9c108a2b04c8e` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-propagator-negative.json` | `515d588a380252ee3c3781ac3fa2745c150fead7259d35e11c20dffa16dfab60` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-propagator-positive.json` | `bf5a5b646002bd4e34c088cc30fe932ceb7b604b5a20346f7275f14a05249fe4` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-negative.json` | `d1860a1e3f0c95fd174607de1d276722b9600b18633b7b4f6d7a7e7c50c2ac81` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-positive.json` | `98363bfa5f1016524d381fb1eab17aa23cb98ef059049841415a6b215475a369` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-negative.json` | `5b527147f1e7c8bd69a54a955bdc1743ba3cde1f740fd6feaf3232c38d1eb7a7` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-positive.json` | `5f3ecdbd2f20bc15640dad2cf66e169d923edb787eddb19a64ad1b95db3db102` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-summary-negative.json` | `19210417ee0a238f5cc87fd0c142c831814cc613d0167ca298b6f26b8af2452c` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-summary-positive.json` | `371bf85a7df08933d286160d15e8386d66a39a4497194482f8fdfb4b28dd30e5` |
