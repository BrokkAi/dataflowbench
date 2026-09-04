# Scorecard `bifrost-java-native-taint-taint-tool-native`

Adapter `bifrost-java-native`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461 — bifrost 0.10.9 built-in policy packs`, adapter version `0.1.0`, configuration `49e759faeb792e9e8d8edb06895079ec4116b30d922c4b08e7401bc103472d8c`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-native.json` (`sha256:56967b512b5379e08628aadca1a39806eefa2e3565e87b8cd2da1cfa29af7cbd`, normalized `sha256:56967b512b5379e08628aadca1a39806eefa2e3565e87b8cd2da1cfa29af7cbd`). Generated from freeze manifest `reports/freeze.json` (`sha256:c543ae4ebd11ed6f3495f4461b5b4bd7c84d0874997f1b62044e9df62817b28b`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `77e78ddeee869f9e8a8a3497cfbc8e654bfbf54581799caa03cb793d45b0a524` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `df1762c1229971b8ede95b5c7fe9f9082fee7cf58e14efe8bb8a4703a3d148e4` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `e77d6a75ef764564993e2817cc449fa90b195b7d733f4af7c3c602b54a65b825` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `095cf0e0303f789e83b8f8e537df288e4978e9f4994211a3e304e826b638f9c7` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `e5dc0b51cf932ee0eda5a127c3af1594966fce8322aad94caaff34f25a2a6b22` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `d06764897c3c27609b4c219301248a7f75e5bace9937ac7bb182780ec8337c1f` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `74742629887ea6874caa94eac35a2c63e57050e4dcc7482725d83f8324f93c66` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `8e4cef0449f0c029d6861402089bb997ce53ebe2713ff3d506275e67e8a5e0ce` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `660e39b8d9024194e18d7a3fbd5146e1850e684cb652b6d66f62280626cc4577` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `42fdba8267da91261991c4029acb222eb1ef5aa37437f6d91145622c03875c29` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `fa49e39f1c65cbefabb3a1bca98dc0a29f5fecba83f03bfbd68c6faf2f67bf82` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `a9dbd5137774fded4d41818e667345c20bf4b03424dea07dd0963f568c262945` |
