# Scorecard `codeql-swift-language-extension-taint-taint-benchmark-controlled`

Adapter `codeql-swift-language-extension`: `codeql` `2.27.1` (build `codeql:938af3639d0709b587251e45d9f8d2bdc3505696;swift-extractor:593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f;schema:a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89;packs:580ea3032d6aeb481479cae3e0cfee057ce0f8c58f0f40987269ecc7a779a4ce`, adapter version `swift-normal-v1`, configuration `e4eb8bcfa0c38e952d565142e05ffcea1ebe22c6ad39574395e59d55355ca2ef`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/codeql-swift-common108-attempt-01/codeql-swift-language-extension.json` (`sha256:c381ea80275cae026eed8f91708ebe244ce88b8c4680ad84deac073c5fae3bc2`, normalized `sha256:c381ea80275cae026eed8f91708ebe244ce88b8c4680ad84deac073c5fae3bc2`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

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
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-result-error-propagation-negative/raw.json` | `d0c6c97193983032e2987e7f2e147888bf7a7e4be250357b9658d1043d14f96e` |
| `dfb-template-result-error-propagation` | `dfb-taint-swift-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-result-error-propagation-positive/raw.json` | `74ae581918ecff972bda5e0cb6f3a687af8102d3097bc94563c81a4d79d2655b` |
