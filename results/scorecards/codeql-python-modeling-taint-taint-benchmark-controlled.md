# Scorecard `codeql-python-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-python-modeling`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `cd3c4feeeb3473e72d9c35a582a32d0b65d281d759bf77f9a2e0c0411d3a7262`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-modeling.json` (`sha256:60ff9613a8e5deedd2c1b3f787911ce6fdb94430c3caaa34eb724695b82bcd4e`, normalized `sha256:60ff9613a8e5deedd2c1b3f787911ce6fdb94430c3caaa34eb724695b82bcd4e`). Generated from freeze manifest `reports/freeze.json` (`sha256:5e57a5ee0dab3929cefa42edce222acbfb0ba0ee34e25e39e9ea882eaa66b724`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-negative.sarif.json` | `60e9294ae1985dba37172b95d751968e455139a6c51e7300562afeefb393e9d7` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-sink-positive.sarif.json` | `7cf9d5f9da3498569eefbc2eafe7b7c0668e5fd5a7eff9a91c54c48524b04052` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-negative.sarif.json` | `fbc278b1e53677739de491d248ac109499cde05f3867fc4c208dc338fc85aa49` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-declared-source-positive.sarif.json` | `31871f8f5e1a43bce7a1f8a925dbb0c7afc026fe8016524352c263fdf10e292d` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.sarif.json` | `745f5d9ab4a9125fac4650dfdf75efde46b52060e78609875d57d250603836bd` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.sarif.json` | `83199d35b3e7673c33f188081e1c352dac8bb682cad114fcbb9cab957b0cdf2a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.sarif.json` | `8afdd464fc48b1b32157d40346b76edcb5954548146a5a0e01fac64064ad8e20` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.sarif.json` | `2f429768770bc3fd326003a5820971f194c1d0f05684ff77eb460881ca7647c7` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-negative.sarif.json` | `e8b8f466b2e0e902e1c1d9241a50968fdf49da28dbf243574830745fb736b416` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-opaque-propagator-positive.sarif.json` | `ef5de2b84066c6aa3b6c1c60985a742809c693b0362d6ae0c29ccaa9cb0cbf9f` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-negative.sarif.json` | `1f978ef33cbb69fed1a68f12f081cce00bc07869ba8a8015142e7a909b623550` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-propagator-position-positive.sarif.json` | `da061d9c187842d91236ad60d2e42e487bdf8143f0ccf02594771a88a806499b` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.sarif.json` | `556ada43d4ae7bd58371d88b4c8c171e23682595a5603aa719c03659a488455d` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.sarif.json` | `b9589b2b45fe88100e213aefe4774e2fad21278ea35fc1e222ff601a7f6b9509` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.sarif.json` | `5ec741821109dda9c5f67439d1bfac3091bb97a53d21ff8bd94b099c1598a018` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.sarif.json` | `bd010f160979a07f4409156d3ab833f28ca4c62b24490fb8d62055da649078d5` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-negative.sarif.json` | `9e054edb1c7dbefd208e30ea20905b2e281592291768bf1b841da1334e1c4acd` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-roundtrip-positive.sarif.json` | `ef73e08db6efbcaa94fc74177c64f271ca7af9bf191b5ccc8bfb4a2aa6186a4a` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-negative.sarif.json` | `02951f927998e964a4fc1ee4b8400ba3900d1b22cc2fa705bd7708206dddc33b` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-store-separation-positive.sarif.json` | `3e4ebc7d1de5da02cf5f3677e8a1a9bdd75532998cb984eb4b23a9a728a771bb` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-negative.sarif.json` | `34d04d836fad27d6fa64aaaec28a15ce773da15f7dedafcb2f439ece772cfdc1` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-field-positive.sarif.json` | `82685d59ded3a08f9f54b60c90efa4297df6e8c1e009fb9b202d93fa3d7f69fe` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-negative.sarif.json` | `4d50b3f43f598ef5e440d180d0bc8297992075e9ef96e5f2f11c97ef348a28fd` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-modeling/dfb-taint-python-model-summary-through-positive.sarif.json` | `8a44ca008c982fd893faf4dba3c917941731b7ad55556659f9ba53387d071852` |
