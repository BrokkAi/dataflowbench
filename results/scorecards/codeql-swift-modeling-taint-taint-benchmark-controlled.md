# Scorecard `codeql-swift-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-swift-modeling`: `codeql` `2.27.2` (build `codeql:d7b185e374bfe18c0484dac07a521a810eb9c4fb;swift-extractor:593eb7afe23d63c57d04461bd046e45672555bb0586353edcf27a0313249841f;schema:a976c843fdba75eb23400266f7b95bba21712fa199b2b7725a48a4ace5793c89;packs:fb47dc786441189213937dae9638efe8b0878e04e0be56c3d349ce03d6ceb4bc`, adapter version `swift-normal-v092`, configuration `ab028dea2a0c1addd6851b625324e8288b290a6a65d5e8ca58c9092147e4c3b8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-swift-modeling.json` (`sha256:361e2d665731324691ae18476bbd9745ce0666bf1b46448c160e1a699d79c0a6`, normalized `sha256:361e2d665731324691ae18476bbd9745ce0666bf1b46448c160e1a699d79c0a6`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `swift`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 24, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 24 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-swift-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-declared-sink-negative.json` | `5aaf3ac3e3af989d538165f986831f169165c26e76d12921052ef88ba235c6a0` |
| `dfb-template-model-declared-sink` | `dfb-taint-swift-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-declared-sink-positive.json` | `3098f64c7b0a75d060052d245f4a6e55fa8edbba0605c2a4315430a8683fa330` |
| `dfb-template-model-declared-source` | `dfb-taint-swift-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-declared-source-negative.json` | `a3df201903e49214d8543e306d0f582f1297c50b27cfd495e7aeacf6e0941911` |
| `dfb-template-model-declared-source` | `dfb-taint-swift-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-declared-source-positive.json` | `655bf55aba910583043ea9aba81e264d62a2c297313373d0143769dc8803ad83` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-swift-model-entrypoint-parameter-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-entrypoint-parameter-negative.json` | `e1ca26cbcc6c3f53450b95117fdadb1c545a4e29f981ff21900438cb6692746c` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-swift-model-entrypoint-parameter-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-entrypoint-parameter-positive.json` | `80698571023f6cf8660bf39fb07ce83a963a8f44dd53d460fe189e5c481adc02` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-swift-model-entrypoint-selectivity-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-entrypoint-selectivity-negative.json` | `7cd5211e2ba99878111beb153e465f23672f51b59e4697d95e2f9602fed957aa` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-swift-model-entrypoint-selectivity-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-entrypoint-selectivity-positive.json` | `9f44f3fb28ea661ca5077b300f43f07ee841a4009ed6a6bec622660eb7f9b61b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-swift-model-opaque-propagator-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-opaque-propagator-negative.json` | `69ab88ae7fbe2b3e80b173630dc258b5b7c8e9c75e87ff6c039a047f0d2ab6f6` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-swift-model-opaque-propagator-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-opaque-propagator-positive.json` | `b3d7aaabe1a5ff03d387343cb574866e8f50744f19e1875f474fbc861f430835` |
| `dfb-template-model-propagator-position` | `dfb-taint-swift-model-propagator-position-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-propagator-position-negative.json` | `1aae1282859ba9c2ffdcd57d95ac2a807fca6df433098b890d078bc17b3b0547` |
| `dfb-template-model-propagator-position` | `dfb-taint-swift-model-propagator-position-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-propagator-position-positive.json` | `71c0aa0cf9b270dc9a163f6b4e3af4b46d53c6395ee73bcc539abc9198c152ed` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-swift-model-sanitizer-kill-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-sanitizer-kill-negative.json` | `8819cf36ca17684216e2756aa5ec1a5bb0d5fdd5299d97415365960baad0c081` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-swift-model-sanitizer-kill-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-sanitizer-kill-positive.json` | `55b4ac67c823c4f4e3aacca0760d51b2f726ae1577af2ae43d71cd873e13ebda` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-swift-model-sanitizer-selectivity-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-sanitizer-selectivity-negative.json` | `a45ea274325d92fb69bdfa139e351e9e6642b1f294507bbc284af7d9881f41df` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-swift-model-sanitizer-selectivity-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-sanitizer-selectivity-positive.json` | `83fa23b955dd13c63e28faf92674dd651ee9022a724050a704d9c03808ccb917` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-swift-model-store-roundtrip-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-store-roundtrip-negative.json` | `7ae2e6f4b69ddc7f01aa31d13d9e8bdc0729d26aafd7aaaf73e74416345fa114` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-swift-model-store-roundtrip-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-store-roundtrip-positive.json` | `15f92b357fee2889291cc1b47578b615e4fec28fbe2ad2a5f380df0864c47a75` |
| `dfb-template-model-store-separation` | `dfb-taint-swift-model-store-separation-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-store-separation-negative.json` | `81b5faa9c149dc815b031e8ad4d670581ebad04c18699a5c768e227ab43fe457` |
| `dfb-template-model-store-separation` | `dfb-taint-swift-model-store-separation-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-store-separation-positive.json` | `0fd097f4d0e0a3c4f6a963e8359abad43a41148462bc017e9d0a067659d2f6b5` |
| `dfb-template-model-summary-field` | `dfb-taint-swift-model-summary-field-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-summary-field-negative.json` | `78dbd6fe23f830ae2b43fa2fcf26f29da3410a29bfb1ba3197f938b64a5eab26` |
| `dfb-template-model-summary-field` | `dfb-taint-swift-model-summary-field-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-summary-field-positive.json` | `74cf4c6f98ee0c8291d3a54ea3b680ca7d2b493486704cb7b6bca52eb33bc6b2` |
| `dfb-template-model-summary-through` | `dfb-taint-swift-model-summary-through-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-summary-through-negative.json` | `e47ba9cbe968f1e16f0d96fc341cb2dd593059cd1f12bbe81d34a5bf616538b2` |
| `dfb-template-model-summary-through` | `dfb-taint-swift-model-summary-through-positive` | positive | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-swift-modeling/dfb-taint-swift-model-summary-through-positive.json` | `76336091c72bb29931754843f45e58bde7580f6a55e877772cc68cb2ef555deb` |
