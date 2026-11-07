# Scorecard `joern-swift-calibration-taint-taint-benchmark-controlled`

Adapter `joern-swift-calibration`: `joern` `4.0.660` (build `joern-cli:4.0.660;engine:309ff2c75b0d7314cd9003a13ae298325827a680580efad9be55d6c168363e00;frontend:d8e0746dd2aa6d3919f2f44e329014d4fcff7fab641bcdef5696a33ea6690f07`, adapter version `joern-normal-v092`, configuration `5a546670420814104d2b6a78eeb70bd75399009127da21096d0141b470e2b39e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-swift-calibration.json` (`sha256:d141666ef28c1e6a491c11e89168abe1094c8dee6510410cfc6a5246ca282dde`, normalized `sha256:d141666ef28c1e6a491c11e89168abe1094c8dee6510410cfc6a5246ca282dde`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `swift`, tier `calibration`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 4, `unsupported` 0, `runner-error` 0, total 4. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-calibration/dfb-taint-swift-modeled-external-summary-negative.json` | `0754a8dbdb9481d5e9ee70a2c422c865862830bf54193643fc5157824475711f` |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-calibration/dfb-taint-swift-modeled-external-summary-positive.json` | `e923572fe8be408d972b941dd5538439e2de2de346f822ee193667a9f2862036` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-calibration/dfb-taint-swift-one-hop-relay-negative.json` | `e5ffd52b15ca386c889a2d5e17cefbcd87221c5d04844dae19ebfec288a457ca` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-swift-calibration/dfb-taint-swift-one-hop-relay-positive.json` | `ef61e2af0b2886ff2758e8cba02c63edaa302472153471d85dcf9b9577859c19` |
