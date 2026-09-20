# Scorecard `pysa-python-native-taint-taint-tool-native`

Adapter `pysa-python-native`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.3.1 pyrefly-sha256:f1cb9b8abc85199e1f5ae57f6943c8cbd412b968290023099996cab8fc3ce096 — Pysa (pyre-check 0.10.0 + Pyrefly 1.3.1) shipped taint model suite lib/pyre_check/taint with --no-verify (suite-sha256:1c2e41c525178d9f332e0b749ecedc5e4293fb570d0a0ab1708c41da7e49594c)`, adapter version `0.1.0`, configuration `ebd561ed95f259823e896819542ad787770b923b374f861a6422263f0a9b6dcf`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/pysa-python-native.json` (`sha256:13a3091432ec44d986faac3ccf2212a265dfe15a81a719d45d70eeb939602e19`, normalized `sha256:13a3091432ec44d986faac3ccf2212a265dfe15a81a719d45d70eeb939602e19`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-negative.json` | `e633ffe4897b52f1716721b6e1b62e32db4c099b08706035b0f251bf3b053e86` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-entrypoint-positive.json` | `c4b2030f35bb109c872f62a5f98bdc7f6adc12a94cb4444d353e81aad1a12132` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-persistence-negative.json` | `c94d0a4336d4a50b967fee8b6660a66f5cc8989e065d08538b696edfc0ee5314` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-persistence-positive.json` | `92762d12a715a7a7a3a58c7993061fef196aa4692697faa5f4328d85cc89a8fd` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-propagator-negative.json` | `acb9311d60474d96fab57a3bb684d7d9756916dc4bb55854fa290b9dcc94390d` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-propagator-positive.json` | `324b404ea5927ccd3f0b85ba89a9bedb2715eb0305e7e23e406bbc60987b683d` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-negative.json` | `77bd9cdb4ca051da71a3610f1b9f67f9a63d105fb665286191abc5fc36837798` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-sanitizer-positive.json` | `d8b0eed06cef21fa3cb1a6256b9e13975024fd0363b95f2d3ad191e5487df6b7` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-negative.json` | `9e20ca2c4ae049c96bfa6bf004822b479f85c4cd1e8a88b556f6c5df0f8e0b9b` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-source-sink-positive.json` | `66995e45031680ccf6e9eb78a36ab196fe5321986dc33052974152c849a110d9` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-summary-negative.json` | `fadbb181d229eaa0fe63480112265cd81af0c2e9a6af07abc3de7042b25e5e7c` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `not-reached` | false-negative | `reports/raw/pysa-python-native/dfb-taint-python-native-summary-positive.json` | `d2128c33adfa3a69b22180d66a3393661b940918aa5a7dbaa8897be948a0ab20` |
