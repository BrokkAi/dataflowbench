# Scorecard `semgrep-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-javascript-modeling`: `semgrep` `1.181.0` (build `semgrep-oss:1.181.0`, adapter version `0.1.0`, configuration `3ef508c524fcc97e5ba6b706195ea474602f04574d92be3ad80a4720c9fe09ae`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/semgrep-javascript-modeling.json` (`sha256:8eaa756cc2966b747793632c55d7ee2aa05f077d3b89d2cfdc11a3bc44dff1fd`, normalized `sha256:8eaa756cc2966b747793632c55d7ee2aa05f077d3b89d2cfdc11a3bc44dff1fd`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `javascript`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `da716a5cb64a35abcd98feb98a10a706f6966a1d54f0a832480bc1670ed50392` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `19fcb52768f401bbba2991d1b7936727c4d25fab198b908fad6fa0d59837fba8` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `aba63f351302b108a85bee5d449e83b25ac66ea8cea71d9af57ad684e0fc59fa` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `e2464e98d70e0071ec4e99e0c60c5f86a70133454afea0e2748f2dc648d97007` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `06917bb73aeae866224ed4ad0ec18f68e2cf89127c5f490b6c832bc77bb35f19` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `07d2b24f8202e114a4ec9958593a9d4acbeafce223dafa159ef43d4563d028ba` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `77dffa8bae078bcf83947389769258bf7b8d24f6581447711231fa618e5a355c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `f24321cf9acd085cdeca5d0a0d77594f2713a4e4113b189d305381ba764a9aa3` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative.json` | `d235f3ac29db58ec957861990e2da9146f2924ce94ccf83426866d02f3b8c4c5` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive.json` | `a4ec4da96c2923d1d49418c14fb64804bd1718eb46fee646b546628602819a78` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative.json` | `b102465e44a9adc2567dfb692618135c7da01ea440d6366d5a8a09b957bd231e` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive.json` | `a36bc4c30ab97c4c19ebada4b0e8bacb34107a919933eadf0111cd580ed3d2a2` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `7e284e6083bf8c7fc0fb65fb36e26c0e0ea91e57870a4d50273a814414f45b21` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `d44f64bf9f8339683268bb52d805a4dd09de4b1530daaa7d7f5868c7c535a3fe` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.json` | `b01adeb541045a13ebdd59323c7e8eba062fb2da65c0fa624fd67b6ccba8435c` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.json` | `c543f74c2681b49d692335cc40ac56fcaa53bf034ef3dfa671d0a62adfa15944` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.json` | `a0cdfc9911fc7b27e1512b154e13130bd3ebf3f13a587ab2667a04eed7a2e699` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.json` | `1882b99dae5f8dd3d9049e966164249945dbc5f98a7800c69c608786a3f59884` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.json` | `23c61dfcb4daee86aaca0a3a7192b20c3b9e60113020dda376232e813179e842` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.json` | `2e69cc60a28ef39f07bb7e492b4e091e5d8b84a9b6f939b2c96eeb7a8ace867f` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-negative.json` | `9c718bf86bc032f32d62130a3ce8cbe1b4229fea48580607ab025abbf7f1ce5e` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-positive.json` | `018d63242533cfdb3a8b39b3555e3197e1f874ded647e1981c595fc00f7669bb` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-negative.json` | `172813a12bdab3bc672b3ccc9b961e164e87e3a3df2744a3044d41433dd5d262` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-positive.json` | `2a8be45bfc024323195076075c49f271dd06ad2e1bdbd518b7ef870faf099f23` |
