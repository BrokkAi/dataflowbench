# Scorecard `codeql-python-native-taint-taint-tool-native`

Adapter `codeql-python-native`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65 — 2.26.4 shipped suite codeql/python-queries@1.8.9:codeql-suites/python-security-extended.qls`, adapter version `0.1.0`, configuration `718f6dd466a0a14ff799e87868acf6e2f88a0a641a4eb6b12d042dfc4551f0c8`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-native.json` (`sha256:2958f4e44c4075463079503bd7c222860076fc159475f76532a258f1aa0bf49e`, normalized `sha256:2958f4e44c4075463079503bd7c222860076fc159475f76532a258f1aa0bf49e`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 8, `not-reached` 4, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 2 | 4 | 0 | 0 | 0 | 100.0% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-negative.sarif.json` | `4502b577cf4fa6bd42a215835d390be4fd38ffaa1ec29228e65fc676bb3a32fc` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-positive.sarif.json` | `a8f26060a2641f0aed78128ff7a694fe92aa99766f66109a3dc55f448bd949c9` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-negative.sarif.json` | `04686e32da51024ea598f27ea9bb608554635dc3f17da4aed1e7d3a2d8c4f067` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-positive.sarif.json` | `67cabc69c19720f59994069c6d4132f4c53193d45827777c6eb1b1cdd3e98fbe` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-negative.sarif.json` | `ba891bbfa897f16aab17e92339e14bc60985fd4179c24840a54365f72d8c41eb` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-positive.sarif.json` | `50fd5559aa5cd6b18eaf0249829d63c2adb27c8076ef3d4400e74d7b5d979296` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-negative.sarif.json` | `78a310b40a996dd6756102931b183f42cfc2d3d588ff1f1cba147ef1fdade830` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-positive.sarif.json` | `d216a33d1b00ae2bf3131ac2c49af85ee31e6cb1902e6b416a2194b8372182ac` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-negative.sarif.json` | `4723708c856ba507f2cf615f0be30cbbe28f94401673c34c83ac698646bbdff3` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-positive.sarif.json` | `dbe669d691a4211d51007939ac81a78e1ea9b94b95e94af490658e0e43626706` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-negative.sarif.json` | `642fc9e13f5de0b3058b3195ad257c800745517d9721d1c00c203aa7bd1b540b` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-positive.sarif.json` | `1d6e9fd1ca8c02d472d40d7a1e7f2f14e2e525a0fc3b34788d5038f16c44b7c5` |
