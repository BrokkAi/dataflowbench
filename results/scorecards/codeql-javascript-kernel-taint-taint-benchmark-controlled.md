# Scorecard `codeql-javascript-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-javascript-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `cb54d749e915208a1fa7fceaa1e5e5302c18960aebf724573040fda66c7a7ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-kernel.json` (`sha256:7ce08b4ed5b67bd711d3f6cb06184f7f80fd74c51d89c554cde8def997ce7f95`, normalized `sha256:7ce08b4ed5b67bd711d3f6cb06184f7f80fd74c51d89c554cde8def997ce7f95`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `javascript`, tier `core`

Outcome coverage: `reached` 15, `not-reached` 17, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 4 | 1 | 0 | 5 | 0 | 0 | 0 | 80.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 1 | 1 | 7 | 0 | 0 | 0 | 87.5% | 12.5% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |

Macro-average over semantic dimensions: TPR 89.7%, FPR 9.9%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-alias-propagation-negative.sarif.json` | `c7eec0da171eadd876ac767729680ce7c71fd758db4db8fee0e6cf27a8c5c547` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-alias-propagation-positive.sarif.json` | `301986352c49fe99b0a9af2ba65792b2e7abc07908af35d86e53950a834cabf9` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-argument-position-negative.sarif.json` | `e11badd88e16f5d8fe338e981f4b874188d7bc47bb92ef3582d85dd052970b97` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-argument-position-positive.sarif.json` | `3dd7933b33a6ea6148ca521219538f972077f59ee9e532c6494b4853773813ab` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-expression-negative.sarif.json` | `de8a3e82aa6fa576a785fb9a862f1b162a1a4ee8bb686d15229f68501e3c2157` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-expression-positive.sarif.json` | `5d3921f2a0c8aaadbe417b8af5c17e8fba5f18313fa84e1e0520d039e219e239` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-array-element-negative.sarif.json` | `0112649dbd4613a1199c560c18e6a15b80549c6193e75bfd00113656bbbe8fa3` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-array-element-positive.sarif.json` | `860ff8a8951452e353623a856b090fc3c27fc9fa55fff6d7613edf974d229121` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-branch-join-negative.sarif.json` | `06e95594451b42362a0e5849fb5ac5551e234876e3e0e0de7c2e03e2fee64e72` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-branch-join-positive.sarif.json` | `b8a53b707e4f7e9e2959fd281e0e73d9c0a46bda0188ae47770372eaa3cbdc19` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-call-context-negative.sarif.json` | `aaea1a9ef8d4301882141008faa36a47926fc92f4adf334bd2c7b29c6188b554` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-call-context-positive.sarif.json` | `ba5bc58fdd319d45f3e264aea9a7dcfd368753403ae0aba95212d44c3163301b` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-direct-negative.sarif.json` | `651d098665667e036cb9d6777d875194425115b97e5a45440a10d10d4f99095e` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-direct-positive.sarif.json` | `a387e40bd776703d5cc5eb818d43056754333059952b14ebba7db2a7d5d4c94f` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-exception-catch-negative.sarif.json` | `5f91373001bc5e566686b019350948720fb6357e3d6fd71c02ab1867e081b7ac` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-exception-catch-positive.sarif.json` | `ef9d458e2658f96408803e77dfebf675a06d8ffcad14333122d09c75c51f4c0a` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-infeasible-branch-negative.sarif.json` | `cf59f41617ab06ce9d1a738fb29220681355622a0969e50ba76bbb96229156ca` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-infeasible-branch-positive.sarif.json` | `b4561fe03dfed4abc1448980b37c8ccd09fa4547b76e1721c7092dfcf5d54978` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-local-chain-negative.sarif.json` | `063d81a38f671b065ef1c549163c4e3d72b07c9111431fd7619811f04f9097aa` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-local-chain-positive.sarif.json` | `c271b0a9b9c711a1c0f9bb63363fa465336b6541cdb479e5049f4461c6a69e11` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-local-overwrite-negative.sarif.json` | `227d28fd2a507e1c28ed4c6aa553ec08c60f36422dc0f2b3075ee576a917789a` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-local-overwrite-positive.sarif.json` | `c3fa3e5a4bb11ece5bcdda2c708f55a796194dcf96195f9192142e68d9127b38` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-loop-carried-negative.sarif.json` | `b6989e186d07129075c08dd58edd1f7d718aafdbc1b1ac2375bae5450e605ad5` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-loop-carried-positive.sarif.json` | `e426ebe306ac7435f5109a8c99d5f1bd6360e607016b62d4fa0e44d5ea667801` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-object-separation-negative.sarif.json` | `6f59e86cac7c0e71ba4d5755bf2d424f31462a2000f0e51faa8aa4540d6d3c10` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-object-separation-positive.sarif.json` | `501cb0b97bd50f403d7285ef395db31eb7a3cd75623beffdfb3c61bba28bbd1f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-one-hop-negative.sarif.json` | `809a6ec53de2e9ca58ab4ec52a167611a05c036b1cd1ddebff434bd3e97bafa2` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-one-hop-positive.sarif.json` | `14ee7e51beb0ceb7be9eeb6d5b9c2f783d543700a2b6f6d3ca358fc75b0b43a6` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-two-hop-negative.sarif.json` | `e2eedd528cb4efa1ebb6bd222e18d419d0e0ec529fdf9da2d42e1724d8d2de28` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-return-relay-two-hop-positive.sarif.json` | `e2c42429fbed9f2486bfe41b20c125617dcf05ca517cce8fec17471c160c52ab` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript/dfb-taint-javascript-same-object-field-negative.sarif.json` | `5763001503b42b3879c6e8c0674ae846639803f58d487a56f47c2b2c7a2039de` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript/dfb-taint-javascript-same-object-field-positive.sarif.json` | `2e06a384ea9c3429a9401d48afb404c448d071770adaa090d163514b862850a3` |
