# Scorecard `joern-swift-language-extension-taint-taint-benchmark-controlled`

Adapter `joern-swift-language-extension`: `joern` `4.0.628` (build `joern-cli:4.0.628;engine:e63635788249ef86d87bb75c9f37929ab2309fd557e7e147765b73dbd0ac077b;frontend:4ff227bc75781d846d1076221032df8b47c0ee7f4fa1687a161c791e59006f19`, adapter version `joern-normal-v1`, configuration `3c6dd3a9fb38496eea9372b20bf2eafa1f85e7f12c35901372dc30072ee01d76`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/joern-swift-common108-attempt-01/joern-swift-language-extension.json` (`sha256:7237eb7e55d85040e2c052f4820146ebd10610d30274fc14f6d3422596077546`, normalized `sha256:7237eb7e55d85040e2c052f4820146ebd10610d30274fc14f6d3422596077546`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

## Language `swift`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 2 `inconclusive` outcome(s), produced by `joern`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-result-error-propagation-negative/raw.json` | `375651de25f1137eb40600c90fe01e716da4801adc9cc4e97be21c2d7ebf0652` |
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-result-error-propagation-positive/raw.json` | `0aaf4fddd1428828d9e1df73264c40a5d965d190536bc369b17774d65b9653e8` |
