# Scorecard `bifrost-javascript-native-taint-taint-tool-native`

Adapter `bifrost-javascript-native`: `bifrost` `bifrost 0.10.7` (build `44d9a5be416432bf8ed414afd3ea0031245ebb57 — bifrost 0.10.7 built-in policy packs`, adapter version `0.1.0`, configuration `6b12ed91fe6d3178ea24e9be7feb9f230268987949ac7a0e724069009265be05`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-native.json` (`sha256:0a2ca366a08c571fa1d769e4f974ede005e19be2d1e4512f6bd9552aeaa3ec77`, normalized `sha256:0a2ca366a08c571fa1d769e4f974ede005e19be2d1e4512f6bd9552aeaa3ec77`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-negative-unsupported.json` | `6ebc912ef34800e3b4d985248928f9d74c0c86629846fe67d63c5d4158a082db` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-entrypoint-positive-unsupported.json` | `fff49974704573d411081504d9daa89116fc405ff93189eedcadbc5fcfa8ca66` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-negative-unsupported.json` | `21cceff3817f1a8830259db33d928627da07e9ce51b88881eab96b4ea11cf622` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-persistence-positive-unsupported.json` | `bb4a554a6d6c234a46d4ac694d86e5cf28c5f3b8034b85cead8d0911db8ace2d` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-negative-unsupported.json` | `5203f36c7cd8f43cea856df94a89d52d95a8e1bf4630e604366b87fba91fe119` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-propagator-positive-unsupported.json` | `cbfdd0dce23dd3a34f9826ce91c106f13554da2f3e411e0c0dd73cea04fd85ca` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-negative-unsupported.json` | `5acb1b4f10bf8191d1ce8e8e7b91bdf6005ba0eba3eb6d6430fa28eff8564824` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-sanitizer-positive-unsupported.json` | `4f523ad8299a7425b69f49ed499fd5e90297267092475853a1a0e763eac9d9ea` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-negative-unsupported.json` | `89a18417e50b92861ee71390f518cb0b5b65e1df94a47cb4bef0b120c8ca1405` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-source-sink-positive-unsupported.json` | `44d29b252fa6729354cfbffe786b42e89f06d54b6c416dab558aed62bf03a929` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-negative-unsupported.json` | `e056868619d0a07dcfaef3338801dd178a5771a36bbb14949accca32a479e201` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-native/dfb-taint-javascript-native-summary-positive-unsupported.json` | `f04cafb6090f5f3096f0b24be44c09b3f2efaf1c0d948d60f6074ce72c2086cd` |
