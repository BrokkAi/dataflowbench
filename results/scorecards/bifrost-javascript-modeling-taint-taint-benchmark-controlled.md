# Scorecard `bifrost-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-javascript-modeling`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `49d4335a42e6893f0797bdb1735b8ea3fb40f3e554f9086595f6c1254ff31203`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-javascript-modeling.json` (`sha256:cf474ca44a495c5a4f7b245f17cca186f2801df6efd0e41437968fe0c00e9ce4`, normalized `sha256:cf474ca44a495c5a4f7b245f17cca186f2801df6efd0e41437968fe0c00e9ce4`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 2, `not-reached` 2, `inconclusive` 4, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 4 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `33e9607fda94ba9d5b2cf4233e29f98e51ef1cfc1cc5aec169c219525f1ebd22` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `e88f22fd772b3fe56a7a840d3e43ef81d3ba13eab6f467c121301456af3d4ff7` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `71428e05461d87549ffecec21ebb2b2e669cb4147bca2254f2e5df5c6cf92937` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `b675d4431ad33acdfddef62cb802d1f910eaa24c975cc200f35676acc6e93e73` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative-unsupported.json` | `707b6f5e984def67ec5b6422ac57939f7c272c00d9987f7e683b162d88526c0a` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive-unsupported.json` | `0bc12b8951522ee034265457577e2b351c1b2b5b03b9d19cf07a5fd5acaeda94` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative-unsupported.json` | `7bdfb5a98e9c9f588e99fe06115d2859daaac8438e84c61ec09b1b5b8e383be6` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive-unsupported.json` | `fa9e246432ae0f3ac338d10c6c51ae4d3a52d6c0d27bb71063727e3bcd047ce3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `b7b9f97a79302b97a558c86d84cbf3e93a338080fd60c722ae84ec02c436962f` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `3f68f10e55d7c7b32e233d21c5ce13d778208c544ee872de2411c539f602b7d7` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `2f113065cc217aadef57318d291e110b5d15cba9f8ef315fc97729caf0970d16` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `7ce435645843326b822d0142156dd9aef845a3c38dedab785ec7f156ffab1aff` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `d329f50f1d60256710b3a233eb397d659bc45c7f8192d27f4eacd11a8afd4265` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `06949790469552973348189f2d37c1cbb1bf6393d94f9b26714da937a256f538` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `3924985648010744db38b8f21a28f8f9a2576610cb3cf11becc48380b2f04b8d` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `36bbd66e2d4efc28a4eb8ffeb346d242a29ff25c08a05a7c2fbc2d5f692dbe67` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `716a60663e325240080f3f006082731cd277b1f11b6ec3a7b5e71a944afdba23` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `337489a2bbbe3b0f95f314919f85b5ae238501e2a099c18cd4babedfcbdd03bb` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `66978fde87fd03f12f0d0537b2406f8ed8e15b686b0160c60ad485421a14a99c` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `161002a43388d1119ddc498014179b1d800e2720451bc447ad8d0956eec69668` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `b4e96fafc3430d38e14b4fef8c153a7acec1d7754741979a0de8df9fbd5f6f7e` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `b71344896fcb2bf51fcb4a6531cd65c00e9991b6b7a7005db94af970afd57de3` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `119b1a2b9cbb2df275406a84cc55e6e3f135cb739ea651cd804af536d744efb8` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `591ae33b1f0a4609fb75b375e7824e9200534373d4319a33d24da313cac9ffc4` |
