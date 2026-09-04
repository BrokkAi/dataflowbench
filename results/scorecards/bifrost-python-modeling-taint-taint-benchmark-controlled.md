# Scorecard `bifrost-python-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-python-modeling`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `7c35450fc275271a167e8e257eae83e8a58ed870bc92015cde34e4f64cb8b500`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-modeling.json` (`sha256:8f4a5853d1640aeac05b3fd4c11d06bc0a72774c6a08a6f229442f73f52be3e5`, normalized `sha256:8f4a5853d1640aeac05b3fd4c11d06bc0a72774c6a08a6f229442f73f52be3e5`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `0b8a5820155f647219c60f7034d5e881c325398cfae180d8e03fb652803dae53` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `15a88629dba74dcc235961cd8228a04526c051c5203bc36878a8c4238ab546c5` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `12a4e7922340f582134bf4a17434eb574d030d7619f827db90c015373f0bf2e1` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `db0701f9ec886deccb1d7509d748cced0377fd8150adc820787c765c2f004164` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative-unsupported.json` | `4a37f4277f3829f2efaa7f3b9b99e54e39b4da417d3ea3b4accbbddbb02e32d0` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive-unsupported.json` | `5454476e48697d58899e3f44f803f59b47af4739e18caee25ebc0c701ca0eb8a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative-unsupported.json` | `f30942b56e02a3bf84092775667fe970eb08edfa576556b596c0c8fd5be70627` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive-unsupported.json` | `034d3b8edf68f6437c954f7182001de76c0f6d5fd55bdc42f3b9aa2fada83cab` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `933bfc8087fa3a9d8a4a4ae08406ee9d9c8dc00b062c384e5a1c52c07a69695b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `45c5ca02bfeb833853b2057c63edf6b7c88f5ca86174019ae0262b4485aa7839` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `91ab1809744dfa5b16c99bc99c4905a5a2ac362df9bf388785f1f077d0408dea` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `1d905ff0c9499dcf806fb9374924562742b4fb8b90d00dc40f8e4e5e38b7175b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `f1306d80d0782d2d09445f61b9fd80ba236551ce93a1771ddb9cb2d18206342b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `3141a1e42578d8d13b279989a537bbc74bf3885d752a4dd0bfe2e85819e7a556` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `6699a155ec92be5ebd50df28d08b4eccc485da63791c6980ef48d3e6c3125c7b` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `9319ce7e1eddc419566d471bf92a84cc8c5c933b67b20a2fc6bcfd9fef1d455e` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `e4a3191fd3272da509135b6e93f491ce22c7aae6c9eb6b58ea887d36489d322c` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `5c51b01ac8f18c95717cbf375154fe089ed92d3ee21eea30cec9b8c735450b76` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `e306c8678dcf482e52aa5e01895f71e147fffbc1aac385e34ecd16b5e55c25c1` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `acd285c64d60d99ea78812bbe6e7afbf8e6f4d908fa1a9721c275cd6048d0b66` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `7f4386e325d8c56716cba33344628447804a787f376a97858786b18fe89c89c6` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `e04870834bad0910483b8ce5ac1c8c8ece59b400118d308b7734aef5355c7136` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `d2b1207783e7b8a2d17e2d1adb269e6ab155946d0cecbd4de1c3d88ed6383cba` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `d94d8d99ba19ffd0cc3f738a1ad571b2e847481945f3c94646e7f22d8b970725` |
