# Scorecard `codeql-python-native-taint-taint-tool-native`

Adapter `codeql-python-native`: `codeql` `2.27.2` (build `codeql-cli:d7b185e374bfe18c0484dac07a521a810eb9c4fb — 2.27.2 shipped suite codeql/python-queries@1.8.12:codeql-suites/python-security-extended.qls`, adapter version `0.1.0`, configuration `153ba44c287f9c9b984287ae3dd6ad16ea4d7ce1c2f7550c06f9fc511a0d3cdd`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-python-native.json` (`sha256:980c4c82469b31e60f2a1ceaa557daeae1a7141857ea00a4875f2c8eada20009`, normalized `sha256:980c4c82469b31e60f2a1ceaa557daeae1a7141857ea00a4875f2c8eada20009`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 0, `runner-error` 12, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 0 | 4 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 0 | 12 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 0 | 2 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-entrypoint-negative.json` | `3e49ba8a303bdbf4777587d6042e6a96652749df21b9a2c02338d45924519033` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-entrypoint-positive.json` | `bdee5d632c28ecc47e671d90c7f459e3d188a83438e2d9c26845b1571119bc59` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-persistence-negative.json` | `ae7be52e4079d561d5f509a1a4b5fbe173b3a4a3ad226532eb31986def07b98a` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-persistence-positive.json` | `0c8e94f856a003f91cad52ec08dcdffcb6a190d84a450ec08b54d9119ac50467` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-propagator-negative.json` | `ecba07360f57e657f83e1cccf3b71699504dfc054dbc875fd0d22a16cf5ac506` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-propagator-positive.json` | `048b4505fe38c278244bb774b5b4ced9f1c4a644f02c359a0626f3852544a173` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-sanitizer-negative.json` | `103a61ecc41276ad9c27a2f7d05d6356957cb12214a9775321b0742cd58f9101` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-sanitizer-positive.json` | `4468da4ea9b3212df27fd4dd3404fef4c9b80d20d27e71f87b3c2d430ad67144` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-source-sink-negative.json` | `763aad96bea7a40af06902b94e0c7cba2411057dc7ec96010be3298a71b5ab72` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-source-sink-positive.json` | `34764814671191f91fab3112af662a30861a7ee465d460e852d1727916f827fb` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-summary-negative.json` | `a83210128f2e4e200fb9da86f633b1894589677854dbef96a76218021437e8c8` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `runner-error` | runner-error | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-python-native/dfb-taint-python-native-summary-positive.json` | `2ad55a75eb0294c6f566c8d7f022aeed106cc142762a38d85bbd50e95987a0ba` |
