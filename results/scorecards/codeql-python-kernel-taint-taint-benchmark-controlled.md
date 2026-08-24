# Scorecard `codeql-python-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-python-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `f97f0198f19f2d1d8630b48ff5d30d947e9f83b940de38af425076cf73e82230`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-python-kernel.json` (`sha256:fb2a40617b05170daf9a5f9d786bd961c298fdd759c8596fd3f990d33a4f4e4f`, normalized `sha256:fb2a40617b05170daf9a5f9d786bd961c298fdd759c8596fd3f990d33a4f4e4f`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `python`, tier `core`

Outcome coverage: `reached` 14, `not-reached` 18, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 2 | 3 | 0 | 5 | 0 | 0 | 0 | 40.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 1 | 1 | 7 | 0 | 0 | 0 | 87.5% | 12.5% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |

Macro-average over semantic dimensions: TPR 72.2%, FPR 9.9%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-alias-propagation-negative.sarif.json` | `af93d1a04d855b9aeaeec894f5c4eaa41d9113c46e6e6aa93c0e616c70d05511` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-alias-propagation-positive.sarif.json` | `724ea082bc6b53fb080d8d7856b3b21931ab5372d607e2b5b5e69918791a4a51` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-argument-position-negative.sarif.json` | `1b7127a680a63d9b0bac39295e6f6c097ebe6df013b814254d428e35bca67df7` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-argument-position-positive.sarif.json` | `f1b743b4abd8ca4e1895a2f2fa1e71311eb8b989c9b5dd50d99a9088ca332d05` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-arithmetic-expression-negative.sarif.json` | `a4862d26601b0159fe32c6431283cc5a108ed33791f23c765a64f7207fad4be2` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-arithmetic-expression-positive.sarif.json` | `ab1d46c189c1090fabe351e35e91b85beca5ff8f2290f2cc54227c669948c06b` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-array-element-negative.sarif.json` | `ab506c715931ad4c27e0561276c68694aefcf08b25f5b855e240c9e07579335c` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-array-element-positive.sarif.json` | `838f978130b419a958fdfd1c9cb8fdfba882c39630df8c6d4b7f96920f2e0197` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-branch-join-negative.sarif.json` | `9c09c8cf822acb84553ad6469641f683aa2216de083d8b71bde39a5cfd835bdc` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-branch-join-positive.sarif.json` | `5823e406d6a4e11b4191d3f5746b70057d29c06839f1f0bd908e7c00aac9566b` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-call-context-negative.sarif.json` | `19b347c6af9fa5baf705aff3515a86c40218423dd551c84eb754ac10e4ffd427` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-call-context-positive.sarif.json` | `72cc522ef8ac7f40f1b3632065c2affdca3f502fccee63854a96a5fbc66fd8f2` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-direct-negative.sarif.json` | `2f6b196c4c86afc10475dbe56dda2071588ce7da7c5a1e8fcb8a558d75ba206d` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-direct-positive.sarif.json` | `8b2d3128fc3d69073a93dbd9e6198913e6e38683d534c84bda27a53769daab0f` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-exception-catch-negative.sarif.json` | `30910bdfc19eed109806645e4d21df624f55d1fea503aa68199f1c8bfc7d5f2a` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-exception-catch-positive.sarif.json` | `10cc129b7325db884f65c22ee9d87799cb6b0a3e641c8dd9a623b9bac17c385d` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-infeasible-branch-negative.sarif.json` | `bca0bcc835c3df1f2b69aa764d9641cc195a916de3a11f7c3ddf348591fbeb73` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-infeasible-branch-positive.sarif.json` | `083ad8b4d28714c6897b202c71a844efc3487eacfc76c158621386fe1bfd80ec` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-local-chain-negative.sarif.json` | `9a2b0f60346c0dc50869cae0aff5b93120affe94fee4b2e8ee98cd4d762fbdb1` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-local-chain-positive.sarif.json` | `584620c31cf192ac5fd8243b0c8e60f96bab91b589196d73909ca7635c435d42` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-local-overwrite-negative.sarif.json` | `c8221606d3cb62e161f1872dfdbcd536495b8b3e150b3d5b1b65b2e42dbc1cf5` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-local-overwrite-positive.sarif.json` | `93a68ebe1dade023ed20feb9ba7eb66358f1cf1ec8474fd63ff0a7f5b4beae1d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-loop-carried-negative.sarif.json` | `4af80fe2f893fcfe5debba3efed07f350d7c1507886277805d3458a6b531b959` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-loop-carried-positive.sarif.json` | `496a735a784fb224302db2d590da409fc262d271902237113cd48112462acd90` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-object-separation-negative.sarif.json` | `c0b0282d17fd0f70b3bce6dfbe4b5f9bf550997682e3574a1e8aa4c1ed666b7e` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-object-separation-positive.sarif.json` | `69d3b3f8b42a287607d93fde2d1a6b164d01187dc8d4461816748cda954baa96` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-one-hop-negative.sarif.json` | `9343e29aaf8db1dccc334374f629f5da8d5c3298dadacf176415a6c43bb69c4f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-one-hop-positive.sarif.json` | `519746ee689600e3bd24636e54e9469aa29fff6cccc84d45ec129d9123e89b83` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-two-hop-negative.sarif.json` | `7d4c16d349e277aca92617d5d6ab4fe2eeeafb4228c34fb62c125986204b9fd4` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-return-relay-two-hop-positive.sarif.json` | `66c7bdabcdbce54e766bc5e88708a5ba476ada5e0b6950b5be06222ea65d1264` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-python-kernel/dfb-taint-python-same-object-field-negative.sarif.json` | `6064f04e216e0eaea102e3c3082c6cbf2115e2b7b3fc89bee962c803e05c6d1c` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-python-kernel/dfb-taint-python-same-object-field-positive.sarif.json` | `a4e5e746244cd1ab90b00f400cebad56f5ee5c38485680a1b5c05b3738046d2b` |
