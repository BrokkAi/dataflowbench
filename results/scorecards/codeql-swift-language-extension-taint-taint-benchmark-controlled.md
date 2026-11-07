# Scorecard `codeql-swift-language-extension-taint-taint-benchmark-controlled`

Adapter `codeql-swift-language-extension`: `codeql` `2.27.2` (build `codeql:d7b185e374bfe18c0484dac07a521a810eb9c4fb;swift-extractor:593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f;schema:a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89;packs:fb47dc786441189213937dae9638efe8b0878e04e0be56c3d349ce03d6ceb4bc`, adapter version `swift-normal-v092`, configuration `ab028dea2a0c1addd6851b625324e8288b290a6a65d5e8ca58c9092147e4c3b8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-swift-language-extension.json` (`sha256:62752757c0f4f74dace296e277c7543a0293976fcf065877150de6e5edb0da19`, normalized `sha256:62752757c0f4f74dace296e277c7543a0293976fcf065877150de6e5edb0da19`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `swift`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 2 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-language-extension/dfb-taint-swift-result-error-propagation-negative.json` | `f2a04e18fb574138362a033008cd3a07d438e250b433693b09e2f5596543ea79` |
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-language-extension/dfb-taint-swift-result-error-propagation-positive.json` | `69c460ed4680c4432f0cce64934d9a86674b6560ae053263d03db04a271fb7df` |
