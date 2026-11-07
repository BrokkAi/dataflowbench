# Scorecard `semgrep-python-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-python-modeling`: `semgrep` `1.181.0` (build `semgrep-oss:1.181.0`, adapter version `0.1.0`, configuration `a2eefdc01e1df0c60b7aa2ceb0967814426f9211b61b79be0cf11de92f0b9825`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/semgrep-python-modeling.json` (`sha256:ca50a762bf2180d04acc95e4a2cc63b6fed87ce3eb0eb439391819013f628163`, normalized `sha256:ca50a762bf2180d04acc95e4a2cc63b6fed87ce3eb0eb439391819013f628163`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 0, `unsupported` 14, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `bff891c8069a77e111eb1b888c48c3a4b8b617b02471cafaf7674f2b29b802be` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `e18616c392fe596f747bb373b277bf5feb1a643988bb9e9476c8d5441643b267` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `e782728e35dbe0a9abd673a84a4040647de1ec64d38b7080bef596ac6c3e7b98` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `cadf77867cd6c38856f54c7dbe0df2571cf802081a6f77aadabf099bc6e8ebde` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `f3fbed809cf66a4a1499f983e83d3fe018e81e45a40fa4afee9fc02d2e038fb0` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `c323f65632fe2fbbee9eee54430e15d1b26c91cb1db1c9f59b70c3d1da5c256a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `9ff2ca33d46d1f811ef579fa09fae6dd7cba0d8fa47d6766ac0cb194a31a0133` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `7554456899f553b3e36e4015126105e45206ce3b824e561d4680f80d9e36da44` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-negative.json` | `480ce6d5118fd1e90b8f013e067c8a6cc23ff0ce3ee6b5fd57648ec998d213d1` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-positive.json` | `c3f9f723182705595daaaaeeab1907beac5d354d88fa400ef91ecee0338014be` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-negative.json` | `bf45e1aca76dcb409ca796b61e206fdadc115bd6de912bf1c27072b1bc1bbb2a` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-positive.json` | `3c7b03e3591543d3e95bd53c681fdc8dabbc2619d2f8c78a8587ce63b15b017b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `3153d9480e19e3ccf7cc364fe2cad986a4213c26a378897147780353992f3ecc` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `dff5a30fb03b0c6c76cd3f6c92e0851acef1759a9dc1c163c7e2f0489d5b5a67` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `4a4ca7be6c08e76d82196c63d3ef33f277188c7faa3dad70e6b6eb7c344dcea7` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `06000573f1c4d907ddd7db4e94d32a2a0c1eb16e6429fa104ca0445a76bba10d` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `a42e6d6a5330f1234fad812b0cd7b7c5a86726692aea348619ff69bb7dba27cb` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `481a90751a5b38edf28a608f1bbe2b04ce4888e7c3c654322c27871871b2ff7d` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `22c4d04a2d1757fcd01a56c542830a60013b93074d2af4b1ed1dc32148f687db` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `9b488319c800fbe5cf7be2578277d0f299e0bb50e52854f4fe5afe7543262f43` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-negative.json` | `7593ecf25b39238bff22e5c2c7e0de152d9ba4a02fe990d0a64a7f2ca9de084d` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-positive.json` | `adde8f9405b958a818d08669a443fe1144b6d19e78e4969ee3cfc780d99f2d77` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-negative.json` | `030544fb33e60742b6b93991a20c6854fffc646e631e35dd36903d62133af165` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-positive.json` | `928ee1a9de962638d143ff613d3d18642c39461535171f128be82fdbd331bc20` |
