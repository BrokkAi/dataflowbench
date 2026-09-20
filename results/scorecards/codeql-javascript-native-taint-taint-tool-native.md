# Scorecard `codeql-javascript-native-taint-taint-tool-native`

Adapter `codeql-javascript-native`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9 — 2.27.0 shipped suite codeql/javascript-queries@2.4.5:codeql-suites/javascript-security-extended.qls`, adapter version `0.1.0`, configuration `9ea3283f06644e746abc95e75d7434f022aa5a31712f83bffdaa3ba1f5ce1c44`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-native.json` (`sha256:b02fb1211af143487337b4e14cc92ccbc4e457c236770ba112e214febebb31c0`, normalized `sha256:b02fb1211af143487337b4e14cc92ccbc4e457c236770ba112e214febebb31c0`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 5, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0.0% | 100.0% |
| `local-flow` | 5 | 1 | 2 | 4 | 0 | 0 | 0 | 83.3% | 33.3% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 70.8%, FPR 58.3%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-negative.sarif.json` | `a584ad6c205e638dad606d15159c3e7b935d43574ec41efe05f9040ae6d3ba9f` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-positive.sarif.json` | `3ae668cd899ca58c17f1fe50d06242eff6e80648a3aece6fbfb1ad02d1e1a28b` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-negative.sarif.json` | `757e3628405f922efd6d16e136057d2f6d1c9b9abcac9b0bd3544382077af4a0` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-positive.sarif.json` | `0853471b5135ac58c268ee218c58070399e08263bca9df774582f2362315a27c` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-negative.sarif.json` | `1d0d8d2ddf3123db0ba0f6ecc36e69380d085ef75221ef99b73de575c3d54340` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-positive.sarif.json` | `8abd469e5ef64d0780ed2591bb347d1d142775fde8b700855aefc26c6136c830` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-negative.sarif.json` | `219c685408a76f1504c777d1411a8d22f7415b22afed1da5f3b295c32b6a499e` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-positive.sarif.json` | `eee9594e86f5bbd85893e9c3a81eec7c4760c6ec86e4eefd0d4bdb74bdf9f6fe` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-negative.sarif.json` | `a752f1f5720c10112181031fdbf7944e9ef88e4e2ae8601eb17a42c668a4f209` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-positive.sarif.json` | `6f36aa4ab5eb7e6ba06efcdb06717b5adbb347f5f763d013eb3e33fd15f8e1c2` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-negative.sarif.json` | `fd35a30bd77ace9efec1693c42dbc74fce19b86ef92cbec7359264d5a6070954` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-positive.sarif.json` | `edcbfe3fa905e0a92242d3baeeb47b4f47f8486586586d83c02ed5837bc0e005` |
