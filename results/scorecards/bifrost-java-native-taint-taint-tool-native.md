# Scorecard `bifrost-java-native-taint-taint-tool-native`

Adapter `bifrost-java-native`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249 — bifrost 0.10.8 built-in policy packs`, adapter version `0.1.0`, configuration `e41194af5eab6972b704081180c532e016cf061d92664a04384394883767a39b`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-native.json` (`sha256:280bc95ddf679abc57c89d439f0b74d183a633f4862d6d97fd1651651ad3112e`, normalized `sha256:280bc95ddf679abc57c89d439f0b74d183a633f4862d6d97fd1651651ad3112e`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `900d5c2049584f1422789f97f618276831e84c5e651c8bc67cb897de58ff1227` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `081581f76a87307665df9bf469a99a2da45dc74e9ede69990a6f7127de92601c` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `4005bc148205d89b2be319c3ace82474b63ba6fdeeab5071eeed7ffd0e579cdb` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `20fadc3ac0c528bcf2b0aceff7cf45277ea362b519b2e5b1e62f8e99c5c1bc6a` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `13ac1e07d70f1e9f2bbd562c911c2d3398333c867df48725c694b6005347a5c6` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `98bd4927196c7baf2eb2085832c2e869936bbdd72b7ac601ac288c7107c62183` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `8bcbdaaff550eb9408e6dbf653b8d70554885e300f92e01b2d12946258917f29` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `34bf8ecb0daffdbd385723e9e3ab8a27cd8de84ebd365dc79c85f85e3e804626` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `690c82a0c82e1453c446803228ab037154679f8d4fc6fc1b602c3a21b2de1369` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `0571e79130394939167b421066aa876cd23305564202e0bd522afa23b6e38793` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `7ba51274c20c906e5b2b1cc89df759858f63e711bcb24f57ab45ed994678cc0d` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `97ffe3add7d0e4a00647e5d4a44c7ee7473c52e351acffbdee647b3bcc4c491f` |
