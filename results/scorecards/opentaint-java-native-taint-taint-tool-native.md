# Scorecard `opentaint-java-native-taint-taint-tool-native`

Adapter `opentaint-java-native`: `opentaint` `analyzer/2026.08.27.17eb0fe` (build `opentaint-project-analyzer.jar sha256:811bdb22786e539c9aabdce5bef91f0c6521cc099adbe2720e6a840c09badf54; opentaint-models.tar.gz sha256:c2a8fb0bbc3b6d59ed6db0c62732ff9a6f0f491d515cc2247932f2dd78cbb9f5 — analyzer/2026.08.27.17eb0fe shipped models archive only — no rule set`, adapter version `0.1.0`, configuration `c1f839e5cf8d4bdfd1d509456115d39cad49d44831399ed78664f1c53a59f00c`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/opentaint-java-native.json` (`sha256:70525abc5a69f7dbb7354e393d864d0e0bf388be1888cc506670bf30ed345647`, normalized `sha256:70525abc5a69f7dbb7354e393d864d0e0bf388be1888cc506670bf30ed345647`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `00705be87e70180917bd5ff0e4eb3fecef1fdb0943e3eb4f670ee5bb1ac8d5be` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `003ec5275fcfee7011b59533b8c68b5f958b43d0ac7b67ab784033558147761b` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `650d7771e5ec131aef1eaf5398ab6563c9b1ba6001853b2cdabf12a5330678d0` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `566123b0afbfd3e1b2fcd55e8cbfbdde34ad7a8f4e242c1efbfc5dbb7996efbb` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `2677d4f9cac3a55454b43de77c3227739003074b35b309e74ce45f87340c3116` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `daa0205f0f09311fe5cedce77ecf6224d6720256209a83c3c427a8ee4ffac40a` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `b4f7224d2e539b16920c90e6872272f36d306fb6134e9bfa398c179c3d25f421` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `8093a40f8ef5662f03b1ea97ea761fb995e796d3b54fd356adae9d52b6438f53` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `225c762979c5bcf6979786dbf39ad628f87d04fc83ba87392a94fd3164d9d604` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `f939ba25c6bd29f09220f3fca6efa7825c5877a34d9d6da802451c62bcca5ded` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `295e61eb304ca7103bf6505360cc9faf44879aaecc16806d6142a981077ea422` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/opentaint-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `30d31918eadd097171a9d714d563674fc34f3e318728a89a35ec0562b2736ebc` |
