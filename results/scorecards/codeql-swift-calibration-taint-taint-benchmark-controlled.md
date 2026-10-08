# Scorecard `codeql-swift-calibration-taint-taint-benchmark-controlled`

Adapter `codeql-swift-calibration`: `codeql` `2.27.1` (build `codeql:938af3639d0709b587251e45d9f8d2bdc3505696;swift-extractor:593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f;schema:a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89;packs:580ea3032d6aeb481479cae3e0cfee057ce0f8c58f0f40987269ecc7a779a4ce`, adapter version `swift-normal-v1`, configuration `e4eb8bcfa0c38e952d565142e05ffcea1ebe22c6ad39574395e59d55355ca2ef`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/codeql-swift-common108-attempt-01/codeql-swift-calibration.json` (`sha256:548917a9fddd89a021ca3d31e2ee642a7181f5e075c6464de8f1384889dce21f`, normalized `sha256:548917a9fddd89a021ca3d31e2ee642a7181f5e075c6464de8f1384889dce21f`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

Caveat: these outcomes predate the current adapter configuration. The frozen report was produced under configuration hash `e4eb8bcfa0c38e952d565142e05ffcea1ebe22c6ad39574395e59d55355ca2ef`, but this population's committed configuration currently hashes to `0fcf3516b9363bace19754a9d885df84ef0c172dd77f372d00834d046c8e48a4`. The numbers stand as frozen evidence for the configuration they were measured under; they do not describe the current configuration until the population is re-run.

## Language `swift`, tier `calibration`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 4, `unsupported` 0, `runner-error` 0, total 4. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-modeled-external-summary-negative/raw.json` | `31b918b35c0596e699eaf24e6a8a1fdbf8c936a4e894cdc84496f205adbbe3c5` |
| `dfb-template-modeled-external-summary` | `dfb-taint-swift-modeled-external-summary-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-modeled-external-summary-positive/raw.json` | `3939f22b0b7fa182ec64a1d3a50bbe1c632368163d212b02c93de86f45199df1` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-one-hop-relay-negative/raw.json` | `949148eeb31ec82df3e249795de438b4e6eb8bfd75a8efca66442f625a37f6c4` |
| `dfb-template-one-hop-relay` | `dfb-taint-swift-one-hop-relay-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-one-hop-relay-positive/raw.json` | `edf3ab5dba9d428fc23aacab92f03aad199cabb18da16f02c8e8faec59854e4f` |
