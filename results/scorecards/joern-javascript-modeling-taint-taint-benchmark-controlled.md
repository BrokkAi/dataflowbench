# Scorecard `joern-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `joern-javascript-modeling`: `joern` `4.0.621` (build `joern-cli:4.0.621`, adapter version `0.1.0`, configuration `44faa326bd6f6b0d37fa963f4342d0e498bc2e617b34709a2a2e6e61aeaf07e6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-javascript-modeling.json` (`sha256:5c652110008845c6541438bac4d213eecc0f95a551a0ed5c01d6c68b544bda9f`, normalized `sha256:5c652110008845c6541438bac4d213eecc0f95a551a0ed5c01d6c68b544bda9f`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `javascript`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `d4ed051abb98e6053130371440f75e8dd909aad8a02e107bc372f24780bd61fd` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `0e3e17bdbf94d3ad0239a1cc0761e6edbe27b769fedcd91243c7d4ce13ef0103` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `0e0aaf62c10432c33820825e0e5f3ed6b6a09883f211d411bab06e34bcfd3e09` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `f078c1eaaaef376233b1a353940e582a5778f720e87c4128d2b6cd59cf47910f` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `14fda24a605e15ea06c1ec781df42bd8146a60a8c5482d705c022f659a1c1656` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `fdecf55f643940a9f75508fbf669209e71cc92ec98651274e77c785bca58f29e` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `4fa15191226a2c461685d462efe3a4534cf24c151a7f945dcf6e9cf530b60f55` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `627d939897c825a6a88d55d1fd161498204f5906c78b2ffde111dcedaa19eba5` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `81a019ac5db518cf4069c1078c33aa2987e574ce00d10223ea7b0b740e7be60b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `a563609b7dec932166eb425bd7099300306b088da30fdf9a30cf6e02c8814900` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `e62d3cfe56c6b7f4737affd68ec99cf4a8ea3379809c25adad00710416fd641e` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `d7477e3e2643025cea7d3d34e4f94e4c38d77264bed4d88548aac97bec1a1d72` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `9bd8bcc2747b83ab72bc36c2bdd48833287b27c6554148d1dc618ce3040a9c36` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `bfeb26dbc35879860a36fd65b8f45aa2c2c89860f2978761e64a22a70702ebcf` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `dbbd0c0a6f82499584fa715eb3753044a7cb5ada60b193b1b3ff3955cb06570e` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `434a3cf3c37c5e9e81bcf30e610bf225ce59a584a04bcab7ba311fcd58c369cd` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `b479e03512d11480194ea6f79302f8a6a22d279824d7498cb24f9f44c6a72f2c` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `c829134fc48bbab58f4823fd2c448f1c6ec75f2a9e0d196aeb295d15e2cb2ecf` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `dc805d4d9ba364dd29e88e87961dbe91fcd6ce66173f65be2dcf3ce360c710a9` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `0bff5d148170fec42a93fcd95863f62451724719625b59c6130830b550808906` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `289ae6d254a33240fbbeca870a19de374047474cc913bdda11a8ec628c5f0110` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `9f84901f21835df3a82a57920c6e78850268c65da3a8fa3ec9eae0bf5bb3c269` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `5a70890cfc26635d587e1ca2d367fa06942ee87ce40e5bf22bca0f412c437a89` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/joern-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `b9d6d0234a4e0f23e987d46cb1eda7d47f322c9c526049832a6f37b76e1180a0` |
