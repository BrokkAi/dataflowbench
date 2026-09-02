# Scorecard `infer-java-modeling-taint-taint-benchmark-controlled`

Adapter `infer-java-modeling`: `infer` `v1.3.0` (build `infer:v1.3.0 bin-sha256:17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62`, adapter version `0.1.0`, configuration `dbaf52e6df1492a80324e8da387d463a12d584160a04bc8c668ee49f0a39c758`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/infer-java-modeling.json` (`sha256:8045827d04ddda46dd17d261468099f56e48471fe9ba7cd589d577913c1c4ec7`, normalized `sha256:8045827d04ddda46dd17d261468099f56e48471fe9ba7cd589d577913c1c4ec7`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/infer-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `b9143a076bf9f89f6ebc0fb4edb5ffe878cde1c6303e4e004b24cf3f1c07bc86` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/infer-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `8fd3c8340bd26c7d42fe289fd60ccf5bab18e06bb1993c9ea8f6a34916e74d35` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `a3b4aaf205779de1c62c77c8183d974614b7e4107d71f83f19f58617a4659a35` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `bbcef10265621307912dfe9008a7b0efe57a2c1e0d933f016538c7801dd0a962` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `eeecac6d8a91f9cda5c40702b119fd5e0988c3e20ffa05d4979b9893abe408e9` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `f2819146377e200297283ce19b4be73242ba06c2c105d38ff829720cefc7b7a4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/infer-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `15fa69ef36fcfded5c17b9600335238522b9b7cc6f4291280603746322153ec2` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `48adab15c9412b510a623f744eb8d28845b294dbdb94c72fd27d942dd389deb9` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `9dffad3228e86eb5e12e64f8bc20f2d25a555fa884929fcb47caa9e0f23599d3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `f182475152e68ede2ce660bacb3ad7af05156072d29e6a121e64a18c2bb2bd1f` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/infer-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `ca57e7747d40f78e4acf20a4045931c174e149c830db8e14732323aa4d369254` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `53286fed973d44e42b30238243a124f4258358841cbf1a09d9e16adba6eef557` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `5ea4e870e724ebd55bb330e88b04f5bef7ddb083d7e29fd8b391d9e3eea397c2` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `1e3ce187a2bdffd75260d8807d4a1dd2769f48b211d2dfcc8caf3c5425a80cce` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `0724dc022a65a35f54c9e54d136155bdf93cc1dedaf343de920f4ff0894c95da` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `cf3f8524453eb6304aaa190377fb3dd14f708e09def86f0186e09938aa087431` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `5cd20cdd2ab391fd962d7e03741e7aa9bdd217baec4357b56b9fe36db385b78c` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `db5df960bf5bc4e9417b109d88902c9220c58edc8bffaea68833a31d68beeb49` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/infer-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `43eb24a988daf942600dcd4923c19d06042cb226a8372ee790ec9fa5bc696a4c` |
