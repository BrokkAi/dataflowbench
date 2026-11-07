# Scorecard `infer-java-modeling-taint-taint-benchmark-controlled`

Adapter `infer-java-modeling`: `infer` `v1.3.0` (build `infer:v1.3.0 bin-sha256:17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62`, adapter version `0.1.0`, configuration `dbaf52e6df1492a80324e8da387d463a12d584160a04bc8c668ee49f0a39c758`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/infer-java-modeling.json` (`sha256:92dbb8015856070e3825df957ab82c5b29b806174efdef30af4e0ea64decf262`, normalized `sha256:92dbb8015856070e3825df957ab82c5b29b806174efdef30af4e0ea64decf262`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 0, `unsupported` 14, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 1 | 0 | 0 | 1 | 0 | 10 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `843aed865706b00b565a06d47708e6e74127e7b69d9653739d08929c47d6e457` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `9f20af41235728d3f8201921cd4e5bff5b0ab99f7ecdfe0f8aa1b85305b00afa` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `a3b4aaf205779de1c62c77c8183d974614b7e4107d71f83f19f58617a4659a35` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `bbcef10265621307912dfe9008a7b0efe57a2c1e0d933f016538c7801dd0a962` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `eeecac6d8a91f9cda5c40702b119fd5e0988c3e20ffa05d4979b9893abe408e9` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `f2819146377e200297283ce19b4be73242ba06c2c105d38ff829720cefc7b7a4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `c87f4d5bf051bb72cd6db1261d3f11ac0c2358c78fdb0db1c8994bb2418b16fc` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `48adab15c9412b510a623f744eb8d28845b294dbdb94c72fd27d942dd389deb9` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `9dffad3228e86eb5e12e64f8bc20f2d25a555fa884929fcb47caa9e0f23599d3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `a8cf6bed182224e1a098c89bbd5b3287549a41431c7eda1993304a362eb8ee74` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `3ceb6cd4c66687d6a5b47fcedd81d9c36398dd0b0d2dda8300e0b058e08c6c82` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `53286fed973d44e42b30238243a124f4258358841cbf1a09d9e16adba6eef557` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `5ea4e870e724ebd55bb330e88b04f5bef7ddb083d7e29fd8b391d9e3eea397c2` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `1e3ce187a2bdffd75260d8807d4a1dd2769f48b211d2dfcc8caf3c5425a80cce` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `0724dc022a65a35f54c9e54d136155bdf93cc1dedaf343de920f4ff0894c95da` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `cf3f8524453eb6304aaa190377fb3dd14f708e09def86f0186e09938aa087431` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `5cd20cdd2ab391fd962d7e03741e7aa9bdd217baec4357b56b9fe36db385b78c` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `db5df960bf5bc4e9417b109d88902c9220c58edc8bffaea68833a31d68beeb49` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/infer-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `43eb24a988daf942600dcd4923c19d06042cb226a8372ee790ec9fa5bc696a4c` |
