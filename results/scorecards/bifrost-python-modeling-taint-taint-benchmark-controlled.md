# Scorecard `bifrost-python-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-python-modeling`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69`, adapter version `0.1.0`, configuration `7c35450fc275271a167e8e257eae83e8a58ed870bc92015cde34e4f64cb8b500`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-python-modeling.json` (`sha256:6a06901b16ab53009b312cc96f3cabc8e786a37fbf7a41420205f8b780456333`, normalized `sha256:6a06901b16ab53009b312cc96f3cabc8e786a37fbf7a41420205f8b780456333`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 4, `not-reached` 3, `inconclusive` 1, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `fdf436bfe4995e92419e6bd4551d0a5c9b794f75f569b8dbb59e8d6f7d58bf05` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `ca2acd01c7a81f6a9ed245b69eae129ad2e909920f92635440f405c5c725d311` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `44fced8f9de13f934e09cd00034342852bd32574996b6cbfc11b4bc7e6cd2a3c` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `247764c41020889cb043c7d2f5315c524bd783ba169b8208d970de57e558459a` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `e235e2c2ca4c9b2ee8881433d271fc84e445f329d93fdb8d4e201718eb9c3164` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `6a1117830f094d50406c796f056d3fcded669121de4cc2fe9ab0ec27bae61838` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `f1f5bcbf9600db8e39753d1b3951063335bed2ef6bb9ff1d9da71202dc75a372` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `d8cda861832dcf8fba47d2c20d0729b97419cf6b800256e52110c2f0df0342b3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-negative.json` | `a4e67d32e4437e6dc907570e504e8ac9f8cdf57ddb24f5a3be634fba1bf8db38` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-positive.json` | `492e0704fe0575d4631d2be5b8f41364455f2faa32f20c67f49fbb621fc1f05b` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-negative.json` | `a5024246f3f1240c2e05b859c7b8591f89c3ce64a9e1d297434fd2e7788e69d9` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-positive.json` | `543c3b0185d36386680e0f1488f2ef24995cb23b9d261d4f1accf8e42a57daf5` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `5c2e136e95e5d74ec2d43425588c35e5d7dabd1f22c0b8491067530907eb042c` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `09ac1cf311665a41ee42cf1c23339ebb6c4c594ae8b5f07effcaf36cced4a263` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `82c068218e9cbfeba0e3c2da52b930c81ecba57a008e355ca46be2285aba3880` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `a3d53d09c8825e82129b70c53198521bdcf583fc3ae5ccd7e435b9a1fb17c267` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `f978fda2eb66fded0fb65f4c0d58c7633146ce566b1633c9e788d3a3f6a47a07` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `080f743296d22490bb03c7944c89a70756bc8ddca9681c2e651db0c57bfa2dfe` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `3eac58886f546158d827a775fc07664d9eaebfef2906bbb8af2bea5eae811a74` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `663ea0dc2bf42051d519c3c0d094a41a9c9b5c245c599c1ff35b657e412ebb09` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-negative.json` | `9ca6433e52a2ea6920eb12613a986cd2a954e91240e080c891b47649e4256851` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-positive.json` | `1c7f4b9a0e2fd2764cbddb57a8b47572ff30fa42c2d8b94c4beb9fdef3bd61da` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-negative.json` | `b456b122155119714df05a562894391c441c7bec999a654350fe47782222f0ec` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-positive.json` | `673493ceda7ee44ff2d2589a321668f03742b760c25270533c0f8bd2067d09e2` |
