# Scorecard `codeql-swift-calibration-taint-taint-benchmark-controlled`

Adapter `codeql-swift-calibration`: `codeql` `2.27.2` (build `codeql:d7b185e374bfe18c0484dac07a521a810eb9c4fb;swift-extractor:593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f;schema:a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89;packs:fb47dc786441189213937dae9638efe8b0878e04e0be56c3d349ce03d6ceb4bc`, adapter version `swift-normal-v092`, configuration `ab028dea2a0c1addd6851b625324e8288b290a6a65d5e8ca58c9092147e4c3b8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-swift-calibration.json` (`sha256:a0b976fb626d6de6e4502ce041a32eb1b0ee02560f78d323f40a87c12ccdc043`, normalized `sha256:a0b976fb626d6de6e4502ce041a32eb1b0ee02560f78d323f40a87c12ccdc043`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `swift`, tier `calibration`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 4, `unsupported` 0, `runner-error` 0, total 4. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-calibration/dfb-taint-swift-modeled-external-summary-negative.json` | `6a3669cf3a9c7583dad4b406164a5028153456361ebb4f1d739aab058c7f4103` |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-calibration/dfb-taint-swift-modeled-external-summary-positive.json` | `a7f32aaed0fbbf56b875ba03c4cbe94514443ecc7a018fd06c68057367714a07` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-calibration/dfb-taint-swift-one-hop-relay-negative.json` | `77efc5f74dcb6dccbe07c7ae149758763f140980a6dd88a1f8651e72ecb4d1be` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-calibration/dfb-taint-swift-one-hop-relay-positive.json` | `40dbc1a2bdb34a992f95292a1b85de530b79b32cd33bc601c1b56242dedc41f1` |
