# Scorecard `codeql-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-javascript-modeling`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `50f4a31741fd93420f8bdad4cbdea9f07dacda897641e12fdcdcdc8d7810e910`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-modeling.json` (`sha256:3a908bdc80fb84d2be7c47c75edce0950b688a71342137b8f70b98aa0359311f`, normalized `sha256:3a908bdc80fb84d2be7c47c75edce0950b688a71342137b8f70b98aa0359311f`). Generated from freeze manifest `reports/freeze.json` (`sha256:5e57a5ee0dab3929cefa42edce222acbfb0ba0ee34e25e39e9ea882eaa66b724`).

## Language `javascript`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.sarif.json` | `c8274dd5ea1fbb3f0b7e849f59a06de5b5b2b0e360740e4eb5bf0f16b31e74d8` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.sarif.json` | `9508d13ed3e0b9e095463234acaa8ca4f33dc8840417687c63f7f1971e1c41f1` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.sarif.json` | `82b310ad951ee9769e1bfd9dc5ad2029654c36c40fa5b26a7ad19b543cef6cfc` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.sarif.json` | `0fc95bd9c4886b42a212fddae7f081931e562a3e9787419f36b1dbb4ab5c6652` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.sarif.json` | `e8a01f0ebd322d6cc07c76ebee09310ca0aeea4dbfcc0b14462e0d86d74e71c1` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.sarif.json` | `ad4cddffe577dd7f0cca5a3e58502996b96f2992a6f05df6c87bf95ef1e02f0b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.sarif.json` | `bfd6e38db6e56209cc4d2ac043a9c26cb43143ee4cf2109b4685ff26e2cc7f2e` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.sarif.json` | `4a7352f2fb5fec4edacf7617b673742855c651e9bcc00fd1798a7be330ad7d9a` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative.sarif.json` | `c80ce66048ad7598ed6a0c508d0a03b7e0d844d9b48c86ba7765150ea8a465e4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive.sarif.json` | `cbd7382ee88b2fde28cc2002a3d2fa43bdbaa107c57f8474ad923e3357c740c2` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative.sarif.json` | `87b8ee9d1f05becb252d999642835cfddeba44dde72cea5272e3feba66d992b8` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive.sarif.json` | `631b6c9a237b1c4d678930456cd1224e05db02878e09f7ac50643705f46a36d2` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.sarif.json` | `c729d0fb486059e6a074fdd58c369fb4f400c322c5b1668c33e85ab205fa3b6f` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.sarif.json` | `5b8610c0cf780ea62bb4e3aeefb8118c383f8f7355c2640b06b07a922820782c` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.sarif.json` | `30cc9ece708f4acbda1fe32ecb8f76d1652f153e08a7f97a46c70be43889e436` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.sarif.json` | `91b83c39560b452800223e2d993a44cb061307a85e5be833cd1e90355cf53dcb` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.sarif.json` | `6330101be07f95c667a098c663b84ec18c65cdfd58dc9ac0795c846529cd5644` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.sarif.json` | `e11cd84c692b22d2ca1d583f3445e29965a1642d49cccd292ff160c706279038` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.sarif.json` | `ecf3e726b5a6604e3387d363b7b7b5b6ca1357eab92658ccbc3045af1963caf9` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.sarif.json` | `74eaf40cf8c58756bc92bf96d4284eb0a9018456f27e8bfe05df2201d5c00c82` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-negative.sarif.json` | `b23077f872931e014e14b81392d616dccb196f51af21d5419b3679db197d9217` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-positive.sarif.json` | `a13f19074ae0c066e3002b3af42503ec20229cbe17ae875cf6f1aae0838e2cd7` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-negative.sarif.json` | `55f6b2ca76b87533392802d7a027a2aef66f0800c17dbb3246ce609e2f8e28b7` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-positive.sarif.json` | `f3ca9c6f223e9237768dff68f7d6a762471ab1f85840feedb5daabff6852f13e` |
