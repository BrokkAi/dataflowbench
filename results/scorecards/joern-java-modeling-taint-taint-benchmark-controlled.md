# Scorecard `joern-java-modeling-taint-taint-benchmark-controlled`

Adapter `joern-java-modeling`: `joern` `4.0.617` (build `joern-cli:4.0.617`, adapter version `0.1.0`, configuration `55282607023d6902aebe9e2e4199542f04b407229ac0ab04eab9b70dd4a6980f`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-java-modeling.json` (`sha256:009a5fb9f523196083e1a52ebff266ba5738dcee454b626a85a80335bb88836a`, normalized `sha256:009a5fb9f523196083e1a52ebff266ba5738dcee454b626a85a80335bb88836a`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 10, `inconclusive` 0, `unsupported` 8, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 2 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 2 | 0 | 2 | 0 | 8 | 0 | 0.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 50.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `28041c4e8050bb61de7fdcf1227408c0f4ca02e98e344c817836fbf2fd9511db` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `a36c6846bccf4041b8267b9ab1bd772f4cf06330befda2dd4e360677421b3e83` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `c33bf1e949f42c3d0c706947c9195dd97b16a8e68de5f732b93b12e5c0fe11ec` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `bd366f49368bcb27fe9f29982b661cfe11770ec6f33b36dfee04c447da218e42` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `ce6381b242cb37750752ef8d1615bcae80a39d65899254139d665f4d50031e54` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `b3a812300f53f5b7095b0073a409fe48fa6ad9a66cc9aa4368be1b73c42c6635` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `ee4f8bfc149b97cf11a51eada647db1849450794c7dae613a1219292402933e1` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `c86e9797abf932e0de92f450b7cb4d12c07b97d9dfea07815658331cded286c8` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `d371ef6086d2fd5f9af3b0cccd678cb52cd64d735f610de625818f52c89e9af7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `dd408c0f3fd8f85ea5005ef6855976959bd29792aa29ba06ebb46b0984995fdc` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `81059491319931b1eb45fe02470bb7941d1edb78649e3a239d10581dfd77a4ed` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `d519002610b214d720856f5d851648577690bd37930c4285c238ff60e648f242` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `fa2e0f3fc3b23c35c09207f01c5691d64c7876409a15148916135f7d315402a1` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `a932cacb859c13cb1624a72ac901b4812190a60560fdd5870d8a6da436a8ccff` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `c27f0cdb0b75934bdb6ba2d813082fa3a95d6da70327a79d3701575473eec99f` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `471bc64903b42d711ddac8a6d9d836577d1ca3c4d79a2209755aa37c963c5080` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `096bfc424cb1a5c0f814132e642d3bbb87610aa21257771d9112e75ffac3bf6d` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `3b64fcd9c4003a089573dc7f6ac3d714518d2c7f95c55074dfc3c65cab9d64d6` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `331a2c7bfdfee15247427e61722188e01ad78e096bec566edfab0675dd1dcb94` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `bda9b3807953ba60a3a304d5c4f89f5b0dda4fadb648d12f44684c7c831021d3` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `c6f2903ad35e1c90bd3c9e2d1d364928dbaed734323da54ef82e7a715865b6dd` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `61b9f877a3177a5a171188ea19a869569148f6c220f8e317fc9ef6f2d7baf407` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `945a624909930c393c5de5144eb7340c4814f259fd14ce0a08a58664ff14e8bb` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `7aa601b3553ae1a73a36e5e05b8b248915998046293f5695556aaff6afe9af75` |
