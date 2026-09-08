# Scorecard `codeql-java-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-java-modeling`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `38acb5de67ed39a244c7eb8a9db755ddbcf197488051a5f1ec0d35b65fa30aee`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-modeling.json` (`sha256:e8a1d5d6e4c2d838f9e27098ecbdb063210770e3f45ed0a8bb79fbbdb8566834`, normalized `sha256:e8a1d5d6e4c2d838f9e27098ecbdb063210770e3f45ed0a8bb79fbbdb8566834`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 12, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-negative.sarif.json` | `eb9fa0832db82dd8a1ad3bf580c883b29ea274a822d0f4da7b9df7196ce1899c` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-positive.sarif.json` | `07f6f775ad411f1bfff9b2a9cd2a0edbc6d4aaa1bf1699416f31975f171f5f09` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-negative.sarif.json` | `13bdf1a877694defaba88c6a811cf408e79e12dddcc1931d0e5817cc7053b329` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-positive.sarif.json` | `c1164af5bab269a06f2cc85f6b5dc185dc9c5128061aafe319c617afbf57a5ab` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.sarif.json` | `9ffaff358e5c9cde6c8961b78202db4f8bce47bdddc78dac7271900c545d5926` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.sarif.json` | `1822f48b12850bf9c4c08679c52b52c8ab5f37c11f432bd2eb08baa64e53aa58` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.sarif.json` | `cb5b050fd75b691b07ed5a444274768daf531230ed7a2b0f0b1f528bec1ebe76` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.sarif.json` | `77a1d0d18ebf266aae1891d22574d37031cb03508938f8796b7438b88fad7d7b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-negative.sarif.json` | `c408be6beb343b322215bdfc647557aef35fc228f8ffa7b076b4d7bf20d69c41` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-positive.sarif.json` | `02e858a308d1ad44716c888f74d026ede48d8da5c4d004a7bdab245d3321b539` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-negative.sarif.json` | `01186bf4112b8052722a6f07041ae28d1fdef2cc379c5c76b8015a57b7f6a742` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-positive.sarif.json` | `25fe71f0c6d47a078f5faef473af6f08e88590a95774e8b0b42578667ed72641` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.sarif.json` | `d67f9fe88d7822082c09c1d7d08b4469fb710cc01f99f4d30b9daa558a294342` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.sarif.json` | `c0c3732cf8fcfb05c2e1b6f5f134d47edcd95984e8aab4cc82954d3acf535bc2` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.sarif.json` | `7f7ce64510eed91ef722a36eab8710be6d5d9e2e53e82fbfb2d81f1a8945f8b3` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.sarif.json` | `53b50cc7b572a266b65c0d8e5c2bbc617288c5f234fb4def94580f19173eb35b` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-negative.sarif.json` | `6714263a3648672e77f64223b0f00e1d0358432e228429880265061aea446571` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-positive.sarif.json` | `1b2747df55dfdd603f7663fe02289ebaf2333dad6c13a542146bf2e008a3573c` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-negative.sarif.json` | `5e7310583af09131e54e065899ac23d73e786a91905a0e6ccb9b8e267a065adb` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-positive.sarif.json` | `1241312e320e631a1d11d4eb57ea7fbef995784fc0b7a7c8901a4cf1e7ec2325` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-negative.sarif.json` | `fe7452953a484fd29289657ef555a99fe3d0a68c1e75edfb3f78c97b5d061305` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-positive.sarif.json` | `14f05ef61d46e25e9e7d41c225501b5eda1dae409f8beb819da9a03069895cb3` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-negative.sarif.json` | `a7d7cbc6d087f60e3593fe2e0d8e3b444720f3b15e4e556b4f489fb66c555170` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-positive.sarif.json` | `7ba81cfe7152d21d70fa0e1c2eb7a2cdb07893f9a8daedba0b3ae7cbfcc79415` |
