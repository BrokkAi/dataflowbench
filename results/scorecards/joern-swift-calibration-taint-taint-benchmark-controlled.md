# Scorecard `joern-swift-calibration-taint-taint-benchmark-controlled`

Adapter `joern-swift-calibration`: `joern` `4.0.628` (build `joern-cli:4.0.628;engine:e63635788249ef86d87bb75c9f37929ab2309fd557e7e147765b73dbd0ac077b;frontend:4ff227bc75781d846d1076221032df8b47c0ee7f4fa1687a161c791e59006f19`, adapter version `joern-normal-v1`, configuration `3c6dd3a9fb38496eea9372b20bf2eafa1f85e7f12c35901372dc30072ee01d76`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/joern-swift-common108-attempt-01/joern-swift-calibration.json` (`sha256:14309f833036bfd0b3c3d3da95e6cb8b35c1b43c7cc01333a8f2b6a1d9dcc4c8`, normalized `sha256:14309f833036bfd0b3c3d3da95e6cb8b35c1b43c7cc01333a8f2b6a1d9dcc4c8`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

Caveat: these outcomes predate the current adapter configuration. The frozen report was produced under configuration hash `3c6dd3a9fb38496eea9372b20bf2eafa1f85e7f12c35901372dc30072ee01d76`, but this population's committed configuration currently hashes to `41741ba370001c1b7ccb03a87cf41b8d3839c6fb770adefd011aed9214aa2527`. The numbers stand as frozen evidence for the configuration they were measured under; they do not describe the current configuration until the population is re-run.

## Language `swift`, tier `calibration`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 4, `unsupported` 0, `runner-error` 0, total 4. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-modeled-external-summary-negative/raw.json` | `e95ca44bc845c739589df5bd62a55bd7f9441b4eef81cb69a8276e4af50cd2e3` |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-modeled-external-summary-positive/raw.json` | `79059b98fd3cfbe0b1e693ef82761f095ea11ffeafa1f4729f16dfa46103f273` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-one-hop-relay-negative/raw.json` | `bdf09f54e852d174b91ea32ca0ec24ec4df625c2d61664396d8cf1b853af8b80` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/joern-swift-common108-attempt-01/capture/reports/raw/joern-common-v2/current108-v090-01/dfb-taint-swift-one-hop-relay-positive/raw.json` | `e7b253796a4742adff9637c911807f632c6a0dcb5e0caee7e7269e4548df79d0` |
