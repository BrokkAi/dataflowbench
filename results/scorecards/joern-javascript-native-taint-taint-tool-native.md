# Scorecard `joern-javascript-native-taint-taint-tool-native`

Adapter `joern-javascript-native`: `joern` `4.0.660` (build `joern-cli:4.0.660 — 4.0.660 DefaultSemantics only`, adapter version `0.1.0`, configuration `d74a06f0e2f9b5bb5f7c2965043c3f92417bd53847d85d0470140130a4cb1243`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-javascript-native.json` (`sha256:7e8b157a701fc06614732aceb5c6c9f7a00f770252bc64429fc271e7ed2f320f`, normalized `sha256:7e8b157a701fc06614732aceb5c6c9f7a00f770252bc64429fc271e7ed2f320f`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-negative.json` | `4881f5bcc4dc6e466d8f9eec0e236034e2e001f2eac7d279be97bdc5fb6c21f4` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-entrypoint-positive.json` | `75194ab5912700985d63b57eb569b3ecae7e77c006b8b5ce19e1f46bae0ac28e` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-negative.json` | `69cd13387f500187fc4baa604ffa1fd72e42033ca4516b7d98a106fec6e1315b` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-persistence-positive.json` | `c5db32b62931adf45ba99312d0f2e72e2e9250486361b273721d8842155e9543` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-negative.json` | `e701dfebfda1c856dad8e102b198a05b6e7fc0e31bdacc106cc73c1c83ccd5cb` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-propagator-positive.json` | `f1033e6958a0181bc66c50539dbe740d38a828ba26f1122859db2185fc064ee0` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-negative.json` | `61f7584494893738b880d8cfb58aaeb78dd91427a12ce46f70b048b376be14e2` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-sanitizer-positive.json` | `d99c19f134fa50b30c37c6537ff1934bd544f69a8be9bf337e9993696d13ba77` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-negative.json` | `4cd2f363fd83142b8423826ed0d6cfd8bed8c484f80555ab61f3c11a63a7087b` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-source-sink-positive.json` | `fa97e7a53fbc2fbd65dc890e509b13a9dc26b1048d9b6840c4c1351b8ec8b6ac` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-summary-negative.json` | `67e6e9e578a818afb247ec4a98deb830f3c4e14f01171fb3ab6b3ed5c5caaba4` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-javascript-native/dfb-taint-javascript-native-summary-positive.json` | `e594aa1dba59aae148c94260051caec471ba514594395c09493feb28da6652e9` |
