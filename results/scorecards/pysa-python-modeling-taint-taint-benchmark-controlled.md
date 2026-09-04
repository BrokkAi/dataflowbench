# Scorecard `pysa-python-modeling-taint-taint-benchmark-controlled`

Adapter `pysa-python-modeling`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.2.0 pyrefly-sha256:6b460273720d857142be562d2c0c607e8ed8e5e752ab575b5c00ea3f735d8caa`, adapter version `0.1.0`, configuration `b6431f4bca19dcf1117b6c1fcfc4f779cd61b13c6b50db7bb0cd4539b0f11ffe`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/pysa-python-modeling.json` (`sha256:32155b8d129bc2bd34f5ddb52f72ffdb9a88c23425fca9994d154194f37e2dbb`, normalized `sha256:32155b8d129bc2bd34f5ddb52f72ffdb9a88c23425fca9994d154194f37e2dbb`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 10, `not-reached` 10, `inconclusive` 0, `unsupported` 4, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 4 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `76db2e1ab5dce288862fb1293708344aaca8680c62e3780971adfec2430ff74f` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `368f02a94db4167d2eb5e2aa5ddc16216685701c49cb97f7b60eb1ac14abb886` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `2fe04af07a377dfdbc8bf3e42f1f79b90712312c7939b86875586245e601a5dc` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `86a72495d3bd9cdda5aa1caee755d07e98de4dda603feeff0b7d3123bc06da61` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `8eb05068e29058f925070bbf43a11fbc510f945841a6bcdfd68da75d81a8e42e` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `da25b51cd542bd8fc853a84f302e644ca82cdc684447a2f5f6dcee73e222dae9` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `20ce54c066cbf8145065509181b6cdbb293131ec2f84b258d186bcc051005427` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `de043020eb8450ace4f528869621c054db2e5ee325a6c3b438e749870e5f914f` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-opaque-propagator-negative.json` | `7c8ab56bd6401695ccf9358bcd82ce9ccfab79fc88b3649b1c771afd0b4d8806` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-opaque-propagator-positive.json` | `1a57d7802d992cff141970d1d5efd49b02a8acea3684165c3b475adc6eb5b561` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-propagator-position-negative.json` | `968381a7feef71676aed1e852c27f5e68f6c4aeffa76649098301af1eda427ad` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-propagator-position-positive.json` | `834b6bf9cb9feaf700b9ea28a1c107e6f8f9d87b235997a1ea538411c96a8f8c` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `b30d60352b3257863c9d9efdaabc003d6e52f246952c8a7dd60e6315fd66bf61` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `9f67b40eabbc142099fa09a0f3c66887320266ee32e1a600d2973921d33bf9d5` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `02cf7d146553c3400113bb6c48c00c6e7eb8f6106448c940bc98aafbd5dbeb32` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `7ca017a92e6b58038d2466c1410f299fdbd5afae3cefe170bc0260ebdaebf9bd` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `674098a0a7799347498753b707ebe70a0fbb74a9db3bd7843db26282bfc60093` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `c32534342605313247425db6cab1ef172223db6ce822743764eddaa540200741` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `7f77998fa3184e1cd99f2ed109f7a1d401973a01c7c047fee35dd9faf2b90d2d` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `051a978567b5a655bddc5463f0003e82928e4285feef9be0cac63ab237060dbf` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-field-negative.json` | `0a34f4f78141909de7df9c1061f3f8897f8631e40b252f6dca2d29e8371d696f` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-field-positive.json` | `58976bdf6c88d0777574a6b53b49e91eae95b6dedca9ea9109842dc4dd283426` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-through-negative.json` | `0e7c128f852511ef45fb25a3f1f709cadfe6d420584267912928c9d522052b20` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-through-positive.json` | `1d0c4429cd3895e4e97eb913ee5e0f09345d5f3bc0c3a679381adcef753dce00` |
