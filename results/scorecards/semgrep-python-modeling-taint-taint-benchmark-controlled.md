# Scorecard `semgrep-python-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-python-modeling`: `semgrep` `1.177.0` (build `semgrep-oss:1.177.0`, adapter version `0.1.0`, configuration `a2eefdc01e1df0c60b7aa2ceb0967814426f9211b61b79be0cf11de92f0b9825`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-modeling.json` (`sha256:f1bfa6e777fb748342c1d55de8cf887cf77843f840ae0a518a040cddb9567591`, normalized `sha256:f1bfa6e777fb748342c1d55de8cf887cf77843f840ae0a518a040cddb9567591`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 5, `not-reached` 5, `inconclusive` 0, `unsupported` 14, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `dd316694f6e736166fd0da460d5dd21cbb451d61948b8a3edc5965480f59c577` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `42430d5f8bf3bfaabd96930bfb7ece2e031157bcf1f8ca91004e11c3102384f5` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `8afbd6ad8749a1afc11461a86caef1179746f7a2f0626701d1dfbdd290b704ab` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `a0022bce81e09354157883760f94cbe46548532fa663d4abbb1c6aa2cf8d4855` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `ff4ccacb2f67e9a5c7a46c7dc873c62a05a633d4f3401407bcce076d9b554fbe` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `c5837c159fcdf8fe4b318e785614978470b50e1c9bbef891ca46b33696b7bf31` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `8e841344f1232770597241da0801dcb6031e02430e396c221c0853a765bcc3ff` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `c2e448866b4bed2e0f68903377196cdb52ba255c7f645f4526aaae0cab45bd9a` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-negative-unsupported.json` | `a36874216543186166c3ec83f9186e699ca2a8c3b101a560af915e3fe0b5e8c2` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-opaque-propagator-positive-unsupported.json` | `f6bff86c0b80389d2f66e7193626170cc5af581f047a1963ab0e5f4174d8098d` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-negative-unsupported.json` | `d8f1815b0aba336ec92c61cce7cac8bfb92072080f889141ea27e8935739b867` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-propagator-position-positive-unsupported.json` | `96e9f2109492a856f0430fe79f21e052f4b25d462b9a3673cf19d32d542a4aa9` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `cf998db5c3f5c65b9c32fd3fa4ae8fd68da1d60d4b38f17c470a5afb39f5d8c8` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `936138a3cb201019cacff10dc9f6064069aa10009c97bf3bd435508ef5805924` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative-unsupported.json` | `b3da3e684e2f6a434318661db553d9179fd20d4c195f607060a25034fbe112aa` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive-unsupported.json` | `2d3587815828f3384da39e6e0fbf297e5d592449e5883834081737fc2597f777` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-negative-unsupported.json` | `0fe26d9af22d11ab2d68b2278862ee31e06a03fa49e726d5c933aece33f63d94` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-roundtrip-positive-unsupported.json` | `706520dc7f6bc0c697ae6d4ccffacb03faa028ff134420513c96d2697cc279f0` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-negative-unsupported.json` | `13db2645903c957794182653ce2515bdc7a7dbbed3a683d60ded2737f1018deb` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-store-separation-positive-unsupported.json` | `d66cf0cf95698a16b79c7be91597ab86956ac64bdb9185d801d52af92f53601c` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-negative-unsupported.json` | `c1cc1624d72c40796287e86b7db9bf14417f62c3d29250eaa511d27a5b9c23b8` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-field-positive-unsupported.json` | `4d565104f26947f4605996f9e5c51f941549690bf85cc70106ff0297672bcd22` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-negative-unsupported.json` | `607040a53d0853e069dd2f1a5d86c5ef79249c9a7c34409d01e8cc9df6bd1019` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-python-modeling/dfb-taint-python-model-summary-through-positive-unsupported.json` | `96b696b4a15a71ce76c1558174d470aac6b43ab514f6ad763636bf799c19b4ce` |
