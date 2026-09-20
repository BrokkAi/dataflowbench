# Scorecard `codeql-python-native-taint-taint-tool-native`

Adapter `codeql-python-native`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9 — 2.27.0 shipped suite codeql/python-queries@1.8.10:codeql-suites/python-security-extended.qls`, adapter version `0.1.0`, configuration `c5c44332862e6a739347ca611fe868cacdd25d3f5006f7d310b57e1c3df15a8e`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-native.json` (`sha256:22e0792a471bbf1d54a6d7b9fc737d5cd205aadd141fe1eb8148dc7119edf35d`, normalized `sha256:22e0792a471bbf1d54a6d7b9fc737d5cd205aadd141fe1eb8148dc7119edf35d`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 8, `not-reached` 4, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 2 | 4 | 0 | 0 | 0 | 100.0% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-negative.sarif.json` | `8e23496283a6dceffd0e75fdc3229117e0a1e55985467dbefbe222eded8673c8` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-entrypoint-positive.sarif.json` | `1d4e6365292b541ddaa335cb817e1ba0ea0b559afb8fc0a43ccfdc5aa11abb7b` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-negative.sarif.json` | `6dd8c114cf557bffbd95eb96c9c1a098020b198b83f0b044d715f3b70f7ef11e` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-persistence-positive.sarif.json` | `38435eb4f868a84ba2fd26864e657bb44ada45a12eacc51e707ca376f6c18a31` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-negative.sarif.json` | `264af4b8d40878f96b6d38b17afc2c2579bc6b359da36fdc908267fc2e866527` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-propagator-positive.sarif.json` | `3f75eb5a86dc37d5c0ac0d33bdd2f92067e3fbbdf06ffea468c186c0af955218` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-negative.sarif.json` | `fe72ebffc6e92b5fc948c3fa924a686a905513d326536b3583b9a2aa9d8381c6` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-sanitizer-positive.sarif.json` | `08336c55f1181767565a6da3962bcfcf3b1b3b4a57a278a18efcc138d55a0e6b` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-negative.sarif.json` | `858f983ac38632606dc12af45a0eb17d3d6b9a963169ca6457a9fb8c062dc188` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-source-sink-positive.sarif.json` | `d5b61e0a6a56219509e8ba897c50b73aa9fa47aafd94e84a14528e84aedfbf13` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-negative.sarif.json` | `325d151a239c6f5cd9ac1721b2b0f34a7c2472830a2aabd562776095bb1a6382` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-native/dfb-taint-python-native-summary-positive.sarif.json` | `0153a574f2dc1c0ae85784b96f61e473b1c9f5e9385075d4d14e200f08640e38` |
