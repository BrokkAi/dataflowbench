# Scorecard `joern-java-native-taint-taint-tool-native`

Adapter `joern-java-native`: `joern` `4.0.617` (build `joern-cli:4.0.617 — 4.0.617 DefaultSemantics only`, adapter version `0.1.0`, configuration `e5e1ed92c0e9664b9124b647698318e835c57067ba610c62f3b627ccb6d576ce`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-native.json` (`sha256:5cc36ea1cb3c0e1d11451bb2bf5193e7c8912408c2c2fdd3a0184d6da61701d9`, normalized `sha256:5cc36ea1cb3c0e1d11451bb2bf5193e7c8912408c2c2fdd3a0184d6da61701d9`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

## Language `java`, tier `modeling`

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `5bbeffeb98485d14739b7f02637a1582de97cd1fc5d5ae34c1204f6d1423a150` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `ceb0daf7b1499504e836c97604529620949dba9cf7713ff1258f0408fef4533d` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `15072e0d17d3ab1dfa71e8416bc77d5b9c464128ddb2a59ee4c5753f7a89d54b` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `a929daf9f26925f240356eed2e162dd40c3630db842e33668e7984f59eb709a3` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `6a052cfb8ecc65581ab8be56c5df18b5d958ef7f67a3e8726b69d705f04f6c9b` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `9dc65987ddb8d9c12ddcdbfae3f4f83fac9ffdfd4b6dd6a31eb724e5ab8f9c7a` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `5c387b481a1de9725d3fb2b5e5f4b95c26aa815e730bac8f550ee59174567a51` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `5450792dae802cd8beb3bbb07401e17266ecd98f19594c57ef6f58125353309e` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `887b1706721953d7cb1616a34c240a61f58531d332ce8669c55a2ca261da88a2` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `32305e91f764cb5452d1e2b2b77d2428bd9221323f3bc7965b19535ab64627e9` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `d11e4ebcd444974d4e554275ac7dcab4f905e725b2920148df8108de5558d1f0` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `05ca54f49ef6d6a8a46b5ef988e8d03703fe250585fc36788b4c5c9975f3cdd2` |
