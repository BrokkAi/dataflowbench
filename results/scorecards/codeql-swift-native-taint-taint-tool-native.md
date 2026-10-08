# Scorecard `codeql-swift-native-taint-taint-tool-native`

Adapter `codeql-swift-native`: `codeql` `2.27.1` (build `codeql:938af3639d0709b587251e45d9f8d2bdc3505696;swift-extractor:593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f;schema:a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89;packs:580ea3032d6aeb481479cae3e0cfee057ce0f8c58f0f40987269ecc7a779a4ce`, adapter version `swift-normal-v1`, configuration `e4eb8bcfa0c38e952d565142e05ffcea1ebe22c6ad39574395e59d55355ca2ef`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.0/normal/attempts/codeql-swift-common108-attempt-01/codeql-swift-native.json` (`sha256:2b83e2436da796229939ba7b14d7458f61139b55efc416112545bb80525b8574`, normalized `sha256:2b83e2436da796229939ba7b14d7458f61139b55efc416112545bb80525b8574`). Generated from freeze manifest `reports/freeze.json` (`sha256:e63dcc483d3000c046816c595811bf35ab494544fb6dd6fff2608d43e9bc676d`).

## Language `swift`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 12, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 12 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-entrypoint-negative/raw.json` | `2ee632857fc3a544f7a2e965baef6d63a2f0c3ef92f8430de0fe96f1a5998161` |
| `dfb-template-native-entrypoint` | `dfb-taint-swift-native-entrypoint-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-entrypoint-positive/raw.json` | `2abd47921096825610f732712b15c2d586d72972d69f48d5cb287d4b6de3b18d` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-persistence-negative/raw.json` | `08e888eacf47db13624e064d1a25d7bbca7b2b8d9b492f91cdab81431b6a6c1f` |
| `dfb-template-native-persistence` | `dfb-taint-swift-native-persistence-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-persistence-positive/raw.json` | `adbc793a96c6c6835a5a4752ebd7d4c2363d3e8bc0fe9a5392c1407386ed418e` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-propagator-negative/raw.json` | `1246543d42d1ad0015ab61219062ce817dd90b8782b1dd4f8b86ed12d294730f` |
| `dfb-template-native-propagator` | `dfb-taint-swift-native-propagator-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-propagator-positive/raw.json` | `5631724c4338921d46e6db963f6cd4cf220b5c5aceb09f21b37ca4980f5e644d` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-sanitizer-negative/raw.json` | `bb64e9645370bfa1f58715ea39c038ea5b7a69b80e36c8173e5b21054d18f8e6` |
| `dfb-template-native-sanitizer` | `dfb-taint-swift-native-sanitizer-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-sanitizer-positive/raw.json` | `4b6835a2327bebf2da3fd881df9634a359edff2953025b347c474446a9c18728` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-source-sink-negative/raw.json` | `10f26784a227f4e67597c0ad19aa284644806adb9c635fbf542cc18ac95e333a` |
| `dfb-template-native-source-sink` | `dfb-taint-swift-native-source-sink-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-source-sink-positive/raw.json` | `05076f6e7b33e1b324d80aaa95e2a4b41caadf37550bfbf1ebbb87a3fe0ed2b6` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-summary-negative/raw.json` | `a051d0138e5f013660940647b527d233f26ae3162f58fb45e81a62d3ea343f55` |
| `dfb-template-native-summary` | `dfb-taint-swift-native-summary-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.0/attempts/codeql-swift-common108-attempt-01/capture/reports/raw/swift-common-v2/current108-v090-01/dfb-taint-swift-native-summary-positive/raw.json` | `535e91bea1a228e61e0879c4cf2313d550246f6a932ca078272eb55a3fd46999` |
