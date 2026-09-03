# Scorecard `bifrost-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-javascript-modeling`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249`, adapter version `0.1.0`, configuration `89af4c967890cbfbf2055be7fceee44f3c296bb89852ab2c142242254647e546`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-modeling.json` (`sha256:703d20a6b566378ff0a2292fc03a5e69c8bebff21e0490e9e732fb0e3c104167`, normalized `sha256:703d20a6b566378ff0a2292fc03a5e69c8bebff21e0490e9e732fb0e3c104167`). Generated from freeze manifest `reports/freeze.json` (`sha256:e3fbcae1eaf3f49192f7156616c4b2149893a8470e03ff445fcd1d5f984f9e5c`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 2, `not-reached` 3, `inconclusive` 3, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 1 | 3 | 0 | 0 | n/a | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 3 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `50966a58701e92670749fcf43de4e11b897f099b7baa860aeb8052fbe81564b1` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `308dd9b492fd697ebc65b3ccc9bb8ccdc3facb7c68d9b67a2893567a2787e83e` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `a6f6932896b4da66a4541a17d6ff61c92beda44e56c2b129d87c706dffc80257` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `c80e9b46fb9f8b55ffe916679dc6457dc65cc196e48728df6919301df6d92125` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative-unsupported.json` | `874e14f2842333bdc1a744c3300a60350ee0c764b31d8d030f3befe2928d734d` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive-unsupported.json` | `0f7e9b6d919d2f5c836816bb08cffcd945d55a0cfdf9e8329974234e27110644` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative-unsupported.json` | `ea6d67abcf56f164c83f11cc64c85c00b55993b9e3c2fb4fb7972b67bb44991a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive-unsupported.json` | `c257dea5d543e581fca38195bd34678bba6db94dad6aa6de5c4a2a836eb6da48` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `01ad72e5c6c6e811fcfdeffa40276d688a5a9cd3393c3f8c98b5dd60599ea958` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `8f86de7f9c963d3772b665fca22e145f53ca633ebb3e252619bad9bbce5dc100` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `3dbb7268f76677d26fa63f7346408452f4a009916364f4fee0f10537560f9ba6` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `b62dd50e4e9fd1c2b8ab2cc10c7d91c55d2467a615810fe92b8135d247e6cd0b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `d64aa557ce90a55d3c2fa9d90d73230eb6d143f7726aee9c9e96d469d7489ebd` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `d9d265bfab1e032e763bbfabe65ef13f0892c339c7b96e8d0b6e92e5ae1cef23` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `8a033f81b98a20cc4e1aeec7ca1ab135377eddbd27f76acf8c70262c0a084038` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `9db6666e7ed776e74eb79c2b1372ca7a4eb70054f88f93483d237015d4d893e2` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `7b938285ad5caea350dae66df679cfc1890fd7dd879144f0a425a70d9f2b4764` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `81137d67e062f0621086b39b0965551305f11aeec6b158fadd688d735e5b6f1c` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `96c97ec469d6780cd62a15eff02a45dd2b4a1f398f2eca04c4184050b0a0eb13` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `338b5328d1e46aef4878274873cecb8fb3d0673dcea37e39e1fb5908b5826874` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `875c741ec96fddf5facd3bb76810195fdb025c5fb52673eba91d898038788409` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `88eaa9eb8b7c22ee27760eda7cc3ce5a1b2baff23e1d38f7746fb68e6c1407e8` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `8bf44bc11a0c7a7f12246bdb8bf86e354a5b8b2f270cd4bd7c924ce69c9244cf` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `2705357b82252ee5ef906317729fe05b0531abb4ce39e70f21ef9fdeced28395` |
