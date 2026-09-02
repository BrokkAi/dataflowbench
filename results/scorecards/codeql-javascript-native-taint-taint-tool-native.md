# Scorecard `codeql-javascript-native-taint-taint-tool-native`

Adapter `codeql-javascript-native`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65 — 2.26.4 shipped suite codeql/javascript-queries@2.4.4:codeql-suites/javascript-security-extended.qls`, adapter version `0.1.0`, configuration `85e2d0560b288a3793078f45ba642dced845c1faa45b20c12a0acc0e3c6acbef`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-native.json` (`sha256:bd5fe87f32f7fc30ea5deb365de613d2d49b5db3db57dbe724fc8625007d6db6`, normalized `sha256:bd5fe87f32f7fc30ea5deb365de613d2d49b5db3db57dbe724fc8625007d6db6`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

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

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-negative.sarif.json` | `23880ad5fde0869a8b27414fc86a700e1a6cf6fb3b1f7110d1941d3cc7ea6f62` |
| `dfb-template-native-entrypoint` | `dfb-taint-javascript-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-entrypoint-positive.sarif.json` | `06e184261c49c7f5bfd60a22fd2ded55c24f229f3d73d8fe371d8b08e2b8e945` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-negative.sarif.json` | `c6621b7ff54678bbe2cabb39373e75d14ae4464eeb360626133a4931bbcbf556` |
| `dfb-template-native-persistence` | `dfb-taint-javascript-native-persistence-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-persistence-positive.sarif.json` | `b4fcbcf85f185efec5700834af8f0288f0d41ae32a7ab9a7a5e1113a048492bb` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-negative.sarif.json` | `bf71a8316dee9dba27287c63c5a98ca7b7ece12be61553006d99a3acddf87b97` |
| `dfb-template-native-propagator` | `dfb-taint-javascript-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-propagator-positive.sarif.json` | `f017709c450353684770af41b27d86c5031ed4e8aaa13680480afa1212bf8f41` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-negative.sarif.json` | `ce0ad31036703f3c87e106c443f4aa47159889c7322383c9d93a10994459ac3c` |
| `dfb-template-native-sanitizer` | `dfb-taint-javascript-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-sanitizer-positive.sarif.json` | `7746e571900b1c768f30f818891a617cc14430417cb2621714def522496e9e96` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-negative.sarif.json` | `a2d95afa923a0f295ef2667a9a518d19b107f46074071bb0b9f38c1ed58c4f1c` |
| `dfb-template-native-source-sink` | `dfb-taint-javascript-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-source-sink-positive.sarif.json` | `cbba13fc993255ef16a68b92bf455ae521ef0539b1f8c7079c433766b080db7c` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-negative.sarif.json` | `9101b1b838945f25a34b51aed231874d75715383af5d9ff4bb4853507f2a88a4` |
| `dfb-template-native-summary` | `dfb-taint-javascript-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-native/dfb-taint-javascript-native-summary-positive.sarif.json` | `b2232d5fb1b3cc4aeda0922d7d30c60d9b3120ffcd0b2ccc48167d2aa8d48e92` |
