# Scorecard `codeql-python-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-python-modeling`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `cd3c4feeeb3473e72d9c35a582a32d0b65d281d759bf77f9a2e0c0411d3a7262`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-modeling.json` (`sha256:63a1406a605fc6bb42daa663bf1fa0ac7838a887b908e88aeca0d73679cf8ad7`, normalized `sha256:63a1406a605fc6bb42daa663bf1fa0ac7838a887b908e88aeca0d73679cf8ad7`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `python`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-negative.sarif.json` | `1aec72397ba3d6f7282853c5b989cbe43a1d29a32b7007e4e3159f51a5a9b6bd` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-positive.sarif.json` | `81549a67a2dcf8fa821b20dfc601fcd4ffd5696a40fbc49731bf00dea5427941` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-negative.sarif.json` | `51b610e9fc215cb8f6cece591b4c5b0cebafcc24d06eab306807d3cabc91de28` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-positive.sarif.json` | `334ea3b4384e6051b5288711d696c308a280281138c197b55c2c1fb54814246f` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.sarif.json` | `9d18356d82d43510cc6c1e13eeef48736c59206243a1b398c27445fe3f6bf0b9` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.sarif.json` | `f6bf34c926dc0bc63e22215be59379df61ac4b126fccc514e342ad0730502dc3` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.sarif.json` | `6be9461942129c57367a179b71750b2eec89f49f35288b6b4c695721bfc8745a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.sarif.json` | `b711d54e65320022e9df96deaad3dcd34b0830e48bfc1550aa3e7598a3b7db3a` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-negative.sarif.json` | `2e2441b50e13276a569b3377491497db93116e83813d099ac333be1b6c39f2d4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-positive.sarif.json` | `13e0bb7a5487aa6d6061f336c19249a7ed479f596b799a51c430e29546c3275f` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-negative.sarif.json` | `3a7a6725ece6cd46b0a6061e19aae85f2ed6ae0e7be6c49520e5bed96d67020d` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-positive.sarif.json` | `775b7601f8af0f02577d25d4921492988863741f3a209452a816a80116161a82` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.sarif.json` | `09160eb8abd28e20bf85f50887bb6877615efce027cafa807c94ab59a7bce418` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.sarif.json` | `ca945a0292140d9c5b4d08b2a1f9410fe3df234cd0762bc0dabf3c616da8991b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.sarif.json` | `7e771711340125a8989439ca1b7eb122623fa86db10277a919606dfbb7ddae0f` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.sarif.json` | `12872757da91d8141e41784d5d2b96540ffb6339dbb1a3d5aaf954f57dd2b0c5` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-negative.sarif.json` | `c207ec3d79c882dcf46e838562a76fd827dde54251be8c7068926bb4c6857ed0` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-positive.sarif.json` | `8e599af6c47f38f854f5154e5b1b94a45d3213e99e890bc22e4058008f8c7b39` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-negative.sarif.json` | `846d649e6dc1626a8df08a7db9d275e47127b34572388c942011f62642d2356c` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-positive.sarif.json` | `1be2d2939e327fcb6dbeaf73fc1a398efc007c4cea0e6a05ecb0c555de8ac50f` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-negative.sarif.json` | `df0366fd3651445bd1778a3773be12c254ffd159fab849d319e0e01697599f56` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-positive.sarif.json` | `2482e665dc73554a21a4396e67fb668ef511a3d4de2df9546592a2395b125293` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-negative.sarif.json` | `a0c29f85824984e79fae7dc383a0d0b025f9f3c73d4ef7424d59815f3253368e` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-positive.sarif.json` | `d22ebeb6c046b0ebb2d2b95120df901a68f4a7b84996d756aa93369c727f7b92` |
