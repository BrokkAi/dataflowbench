# Scorecard `pysa-python-modeling-taint-taint-benchmark-controlled`

Adapter `pysa-python-modeling`: `pysa` `0.10.0` (build `pyre-check:0.10.0 pyre.bin-sha256:035a206349193dafdac70ec4020a992add5d88e60dee76163cf39ffb0b8fe8a3 pyrefly:1.3.1 pyrefly-sha256:f1cb9b8abc85199e1f5ae57f6943c8cbd412b968290023099996cab8fc3ce096`, adapter version `0.1.0`, configuration `b6431f4bca19dcf1117b6c1fcfc4f779cd61b13c6b50db7bb0cd4539b0f11ffe`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/pysa-python-modeling.json` (`sha256:57fd9e95e58c382523f4319e7c39177caca0fee0f99586e70ec73681e8470128`, normalized `sha256:57fd9e95e58c382523f4319e7c39177caca0fee0f99586e70ec73681e8470128`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `6fc1490bafb82bfa12710f3b2ea62c345d72fb6907c6bb7918bb5dee639651c4` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `13c5f1f10f471eda94456cc11976d5f84f2ed90b2b30ce299f2ea6234259a190` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `f202950792d3c3a6cfd3d1370cfc6da2bbc29e02a5a8599fc08338076d2b8121` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `d51bdfc59fdf4764b471b5b628dc2398574a08c1a15c919d06e638a336560663` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `810a2a1d6feaaa886d4aadbab089ae1adb18a2d2b0aa19b52ba6a7fcdab85837` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `16e46dd244166b68d085ce040b0768f68a9712b423bb99207296311735f5aa3b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `a2edd8320209ff1fc6b868b4a7d7082918ccd10d8a1e56769a4d21f4ce901c20` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `63aaa7b0daee63545aba0e6650a33ddaa0b3a6da1d4185b109462c94bd045c35` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-opaque-propagator-negative.json` | `eedaad8a987295773f4575964cf75b40e9476a6ca9f35110414b1a84b4bc4425` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-opaque-propagator-positive.json` | `c9e62253248502475c21cb4b3d35818c13256c206494e9972728b681ecbf9259` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-propagator-position-negative.json` | `c45542a9a863aef6b32dad51ee0971cb03906f9d1dafd80a817cdde48995e4f6` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-propagator-position-positive.json` | `d9a9c020975a2c70e3068565de84877f44b572c6f3f1e2312d0f8f421354c615` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `185d3465863087d816126839d683cdc9d520b725a37373024ac9b7db67a3953d` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `cb794e522aa45ec38c6e0737383c4bf4eadb04aeefc401af9a15e423c5addc4e` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `a30b6326da673e555a6f41a8127fe4871cbe5d080aa5d3c6d5db1e8b2bcbd37c` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `5f306968a8bace5d50970f60b701e3c32941d1ae7bd6b317ec863a266e5dc82c` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `fe1dab00d7e5c0403fa6386524c3f6c94ec72d57999cdddbd7a60ba2e2338d50` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `2d31e51947ae569b38832c2113440c41f089666e72556e1a2cf8fdb20ed1e126` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `e235bb0aacd14e5c236e2647e34b2b30ab08ba038d6a92243bd453395cab292e` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/pysa-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `484fcb37121572d39e44b2824e164bed6cc1532a3f36a200ca18fba87d0192c5` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-field-negative.json` | `0b4f601c34444ccffe751aaf4762d46107d84788a9be5818fab60b8a73c300d6` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-field-positive.json` | `fd91ff2d7b69ebf1bdc57cfbd61a197d986468313c834a9e69250828f34fd612` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-through-negative.json` | `080522fbe7d78a3afd022697b7fc262d4bce26e2d67bd14c253358696e79e463` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/pysa-python-modeling/dfb-taint-python-model-summary-through-positive.json` | `aa00b192e0fa21cb117f53418ec2a087dff3b4052bdca00a92dd0d5a54dfdbb0` |
