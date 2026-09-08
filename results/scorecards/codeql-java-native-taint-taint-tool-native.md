# Scorecard `codeql-java-native-taint-taint-tool-native`

Adapter `codeql-java-native`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65 — 2.26.4 shipped suite codeql/java-queries@1.11.9:codeql-suites/java-security-extended.qls`, adapter version `0.1.0`, configuration `ec644de36febf5bf3883833c856cac3448113b0a61d64e2530d333e90911fb72`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-native.json` (`sha256:d6df797021b68be094eba029397330032add560d5a89342d2a6fcd5396d6c711`, normalized `sha256:d6df797021b68be094eba029397330032add560d5a89342d2a6fcd5396d6c711`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 5, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 1 | 5 | 0 | 0 | 0 | 100.0% | 16.7% |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 29.2%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-negative.sarif.json` | `9f2373d32fd4dd1bc72f5b644de306a2eb436e73280c3fba5d30b385a9f0aee7` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-entrypoint-positive.sarif.json` | `d035b6bea399d483e1efad2e8396409cfad8d257b7172105b0d9f6aa992be51d` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-negative.sarif.json` | `cb11ae6006d7cfef10e5883166d549ff0f10ab4d303d47b941404efbc84286a8` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-persistence-positive.sarif.json` | `d0e1aeb930b4742c191eaa17193d896679c5bc484339503a61eedf60edbd6389` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-negative.sarif.json` | `37696c755c7d960e27ac34b1a709996b93d351e6fb12fc04946b9930b7ffbb14` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-propagator-positive.sarif.json` | `069ce066c055160643afa7f935b5deb5235fe3fca2a8a399bb1f54af6ae864b8` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-negative.sarif.json` | `7d8fc19cdfdb64e313b32ccdbdd0d2b9b8fe61b845f9c2ccaec718bbf3682721` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-sanitizer-positive.sarif.json` | `345ec993908862730e2e082a1fa7741d8c64d6bb976fb5d98ae0623cbfdc791b` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-negative.sarif.json` | `e551915ae8406c4a99e206853a20f4ab172ac0b281fe7c18a7c660981e9d8f3e` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-source-sink-positive.sarif.json` | `fbb337e7c8586c11464b86e9bcb1485ff30744d94e413bccc1528ed5f887356d` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-negative.sarif.json` | `9c0cf3bff945e0f61a14d41617cd0cb3a6a2a375c3969c4182460ce821a194f3` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-native/dfb-taint-java-native-summary-positive.sarif.json` | `d3317c6ce0facff1a623ca6dd276ffde2b6d71272999250cddda08f320817b98` |
