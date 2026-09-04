# Scorecard `semgrep-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `semgrep-javascript-modeling`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0`, adapter version `0.1.0`, configuration `3ef508c524fcc97e5ba6b706195ea474602f04574d92be3ad80a4720c9fe09ae`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-javascript-modeling.json` (`sha256:9bc8b0619b34ca98b5b6e3044cb5ff7c0798b8c9ec19554a9f27b2aac3815d8c`, normalized `sha256:9bc8b0619b34ca98b5b6e3044cb5ff7c0798b8c9ec19554a9f27b2aac3815d8c`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.json` | `9280a739347b83aa211df20a3dac77ac7c5951a916f03e69e55dad2ebe0844ee` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.json` | `afac6a76219eddb9c796535083ebf2dcb21fa769abf17e3c38d5481f5afd16d0` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.json` | `8728958e5880460be4db30c1c6bf239458d01f2b85f5a66394ace0bf8bee3d86` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.json` | `912d4fe8f639214a51e447042513f112e36d222445a64c0b7d768ef2e7d1382f` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.json` | `94b977fe7364963b692a4235699615b46d96b053c17791479faa79d1da4f086f` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.json` | `e3220a63f017c48ba7bc06be54122f98b978d75528169529038f2d1f9c595e9b` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.json` | `9cd2659cfad6f159453682c9aba4425ab100146594ad83d8e0923693e2f9debd` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.json` | `91f8bc7f4d1d4b6d9c20c1975177e3c3c78252c36da17c78b9dcf06b42a98ed5` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative-unsupported.json` | `f88b2dbd130a8f870628d24fbf8ab09ca9280c4dff4158fffd37bb77a910e42b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive-unsupported.json` | `d490ff914536f74c860dbc50fa14d09c13de0f50009e9ea9e10ee3dced79acea` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative-unsupported.json` | `14e8a39f22e28434087880a894a0989a9e572445a355875d4b3bba0f7833a20f` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive-unsupported.json` | `d8acacb8ad26aca816c5eeb0cf27de8c5b2df40cf9e94b731c8a01d749104be9` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.json` | `153bec08fb1b5beab7f608083e73f28892e932ec4067b8db3901ed55896e1b88` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.json` | `d6223a504283e4a6b64d56fa024e9aae1efd0ba80aadb14361700b07f0791e80` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative-unsupported.json` | `05800b65a463a4f7bcde217d50bbb6ec081274dc5561e35e37147d3a6e088735` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive-unsupported.json` | `aebd58a48a698e522056a9af8f9c71faceb2a933e9ee700898fa0ef25afadccd` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative-unsupported.json` | `e0107e5db4f9af4ec0bece2940bb375e3304e317a716f86d8799dae7ed5bcc0a` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive-unsupported.json` | `9b77ac7b110d82e59288353c3cfd88f133e7c28ae3dbb6240c222659eedc2b76` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-negative-unsupported.json` | `c2f0d9f2b8f434e9f0b9beecd029a7aea807da13c082534c4c1e27b8008ef90b` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-store-separation-positive-unsupported.json` | `34434febe828d2ef80777ea9bffd3a74c80b73eca02d8b4ffcca8d91ebeb53df` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-negative-unsupported.json` | `0a61c0d7edfbec36414e25644faa808de4e3409fc4ad51de7281adcaaed5fdd0` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-field-positive-unsupported.json` | `efc538fc10e290816cf5b53d1fbdb224ad5479745aeef3567369653cad269f92` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-negative-unsupported.json` | `b412df7c48b2b95387116d6b374d93ed0cb8bef6934d7eb88fe786e44e631f3f` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-javascript-modeling/dfb-taint-javascript-model-summary-through-positive-unsupported.json` | `1ae9b17444eb6a8ba6671930b6631517fc2e553c89f6808c0f784bed9b3a7b81` |
