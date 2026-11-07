# Scorecard `joern-swift-language-extension-taint-taint-benchmark-controlled`

Adapter `joern-swift-language-extension`: `joern` `4.0.660` (build `joern-cli:4.0.660;engine:309ff2c75b0d7314cd9003a13ae298325827a680580efad9be55d6c168363e00;frontend:d8e0746dd2aa6d3919f2f44e329014d4fcff7fab641bcdef5696a33ea6690f07`, adapter version `joern-normal-v092`, configuration `5a546670420814104d2b6a78eeb70bd75399009127da21096d0141b470e2b39e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-swift-language-extension.json` (`sha256:8a3939b797de79ad028f34a76a8afb1fbcb361c223d1aac460befd77796cdfb4`, normalized `sha256:8a3939b797de79ad028f34a76a8afb1fbcb361c223d1aac460befd77796cdfb4`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-language-extension/dfb-taint-swift-result-error-propagation-negative.json` | `071757dce66cc38b5a5907610594c8ccc069e212122005e17612f08d18733b65` |
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-language-extension/dfb-taint-swift-result-error-propagation-positive.json` | `6d6a0b6b067927198bef64f8c9f770e1ccca1c4b3730ca7d1494fcf3dd31fee2` |
