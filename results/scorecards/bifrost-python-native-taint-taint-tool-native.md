# Scorecard `bifrost-python-native-taint-taint-tool-native`

Adapter `bifrost-python-native`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461 — bifrost 0.10.9 built-in policy packs`, adapter version `0.1.0`, configuration `49e759faeb792e9e8d8edb06895079ec4116b30d922c4b08e7401bc103472d8c`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-native.json` (`sha256:af7024b7bda9a820d96c4460a6816c3efac6d81c21d3c5a68eb6e86969ae6225`, normalized `sha256:af7024b7bda9a820d96c4460a6816c3efac6d81c21d3c5a68eb6e86969ae6225`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

## Language `python`, tier `modeling`

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-negative-unsupported.json` | `c84a0c620e5c193071364de6e70a8fafc01539a39fdbe62175ec10f10559978d` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-entrypoint-positive-unsupported.json` | `00c56efb23c47b21b95a11088ac9c606a9610e63ece53ba37dc5d47be796099f` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-negative-unsupported.json` | `2cdf6151330ac6a4ae0a8ed007287052072ed402c1a1abcd563d6edcb9545196` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-persistence-positive-unsupported.json` | `d61692f558c45398a36269d4941c94b5d4e3197315c0b358699d9b63ab9e3669` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-negative-unsupported.json` | `d07cccb1d3849e84799ea8d6e396f63b8a11b358a204f3194039a450e6d081ac` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-propagator-positive-unsupported.json` | `c56a96bad04d91c085bf27f5de5783c60b2b030d52604aeed929544bed08a3db` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-negative-unsupported.json` | `1496cbcb418c657905dbe98d0c34b07f94660fca8f9a63cb63b6c5a720dc6fa4` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-sanitizer-positive-unsupported.json` | `7129a8982cbdd3b91ff71d1a9796688d563f0ef2c0df14a009c2b58d3d8135de` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-negative-unsupported.json` | `a8fa9e0a517500950491fe77b71706cab327e9fe77c9240ad24207fd0732b9ee` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-source-sink-positive-unsupported.json` | `e7c1bd44adeafda5d4953e0a9b91fdeefea297f85c9eae3cd2c164db64bfcb07` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-negative-unsupported.json` | `046624a666e5d88f205c37ee0b3b6c3733d3b10ad21a3fb9670c8aefc316c834` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-native/dfb-taint-python-native-summary-positive-unsupported.json` | `e2f3b62da39ba289adfdc0cd9fdbec79c05ca1674b2803df6f2329274036827d` |
