# Scorecard `pysa-python-native-taint-taint-tool-native`

Adapter `pysa-python-native`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.4.0 pyrefly-sha256:2076955b92a092dbe1ffb751fc4c92b904a7391269c591d6e489cddd2fbe88d2 — Pysa (pyre-check 0.10.0 + Pyrefly 1.4.0) shipped taint model suite lib/pyre_check/taint with --no-verify (suite-sha256:1c2e41c525178d9f332e0b749ecedc5e4293fb570d0a0ab1708c41da7e49594c)`, adapter version `0.1.0`, configuration `1cf76e117c0883b4cac571fbd9232413a6e750f67c50ffed05035b6a8c0d3b16`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/pysa-python-native.json` (`sha256:00051d72ecd00c2db1e76999083cef3af0f1cc4632d64e08574ff5a5872be281`, normalized `sha256:00051d72ecd00c2db1e76999083cef3af0f1cc4632d64e08574ff5a5872be281`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-entrypoint-negative.json` | `d2b50ffa3b389dc67be14b814833066712a03bd76c924638b05df3addb7dd8c3` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-entrypoint-positive.json` | `acce812c0df1ba99b1133748ec4c3bbed3d7b1dd112fecb8926407ac0d6e0ee5` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-persistence-negative.json` | `3fdf31386cd91af425b49061056fecf7b0900524b423d96848fae0d00a7334e8` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-persistence-positive.json` | `57010222a18422b99babd126faee4a6819eb3ee19b99fac4e5c4a1c98282c894` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-propagator-negative.json` | `12fc4f070f61a309d73f8cf279a3d8e9296d4d0f2c8928366d8ec7ae9182a4e1` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-propagator-positive.json` | `03dc90036262f87fceae5bdb5c6fed48691b9682e5f7209c5ba4b25b3e055762` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-sanitizer-negative.json` | `4adbda47863cfffc1fcdc5f0169c9c921b50139e32871974b0246da0fce5f14c` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-sanitizer-positive.json` | `f1cf4f8e4ab767adb398fbf56c64ea4e81d9d05599b9707867f0fd3fd29d5970` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-source-sink-negative.json` | `d4bed2538ac42615462fcf26be8262b5334759f8927dfe75bd98d82446b23720` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-source-sink-positive.json` | `2d4c9a6a7d17e393d27a5d8375889be5a9c99f62f40d703dbe46b076c9539bb2` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-summary-negative.json` | `a4b65a480227afe6309b27719ddcc6f60f59ffedcb01253a5413ef9305e941ac` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/pysa-python-native/dfb-taint-python-native-summary-positive.json` | `2ac597382568a07dbb957ca1a48e0448a79b9e55e55fd3c0eca12b478c7b9d54` |
