# Scorecard `codeql-typescript-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-typescript-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `97949db804086b91f4737ad2e6a8ac5dab461f811a7a033250a00ced32eac54c`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-typescript-kernel.json` (`sha256:848162f40204dbdce0a25dd25014e9d82f32cc5b74551d58dd24745e2cf4a95b`, normalized `sha256:848162f40204dbdce0a25dd25014e9d82f32cc5b74551d58dd24745e2cf4a95b`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `typescript`, tier `core`

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-typescript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-alias-propagation-negative.sarif.json` | `b98671d84929c1564169a7c9624a90124a72c397ce4bdcc582a99c1f5dd9f368` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-typescript-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-alias-propagation-positive.sarif.json` | `77391cd5e0f0e010c488c35f37d5ed6cb8cfca4fef53b22e78f09a9fd15b7c2e` |
| `dfb-template-argument-position-separation` | `dfb-taint-typescript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-argument-position-negative.sarif.json` | `87cfa7016edea8c6314a2a999419a6d8e6b1d9c87d688ae3a7df1587d6eebada` |
| `dfb-template-argument-position-separation` | `dfb-taint-typescript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-argument-position-positive.sarif.json` | `113b0614cab6e9f20c484db4b587269379406f60aeb3de83cd9eb3d59b6bf6da` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-typescript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-expression-negative.sarif.json` | `ad853c6323dca72017801da39e8404524b3bd7606267738df7b50ac35dafc7c6` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-typescript-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-expression-positive.sarif.json` | `d9240d879fd5541eb2570762fd2201f8da2b61aad3df6caea13b34777a259a7c` |
| `dfb-template-array-element-separation` | `dfb-taint-typescript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-array-element-negative.sarif.json` | `a49ca90e3cfc44a8a155a7c190956e591d45bb9bd55cbbc391ef6baf64d435f5` |
| `dfb-template-array-element-separation` | `dfb-taint-typescript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-array-element-positive.sarif.json` | `63b7d9ea759effacab2a84d54532bbe7a95e5d41d258316518a730f76eee37fd` |
| `dfb-template-branch-join` | `dfb-taint-typescript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-branch-join-negative.sarif.json` | `e2f86b4d462e247818275d93f2da291abe887834a75b2582da3a77369e05d2a6` |
| `dfb-template-branch-join` | `dfb-taint-typescript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-branch-join-positive.sarif.json` | `34aebb4a212a0a4f3a70e6eeb721bd62113d3066b58c60a5d2e121d09ceb5f46` |
| `dfb-template-call-context-separation` | `dfb-taint-typescript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-call-context-negative.sarif.json` | `eb95ea1183092d2dc9da3806c1d39ca0e13fc63ee7ec7c4c73f4d869f4d8c379` |
| `dfb-template-call-context-separation` | `dfb-taint-typescript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-call-context-positive.sarif.json` | `4f0a1496d62cd50a99fb5f8dd83b04d00a758616bf5306bfa93c9807b762d6d9` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-direct-negative.sarif.json` | `5b25130fcc049aa4b8e12b6b2886f1d6570b4d7c1cc6ef0d89d4a4c469c32238` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-direct-positive.sarif.json` | `5f0c5078012eddda843d1781a9504f1157b6478e370d599bbcbb50d4f2b73ab8` |
| `dfb-template-exception-catch` | `dfb-taint-typescript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-exception-catch-negative.sarif.json` | `8fe018e0e4202073f73b2951158791f973bc3105090c6be48336eedb2a94d05a` |
| `dfb-template-exception-catch` | `dfb-taint-typescript-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-exception-catch-positive.sarif.json` | `a6f7c5bd87b5642f3ec2905a445527dde09dc7f3fb00208af0e6f4d90bcd1ad2` |
| `dfb-template-infeasible-branch` | `dfb-taint-typescript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-infeasible-branch-negative.sarif.json` | `add888198656729f6f2d958dce41a3e03a989ace6dd2ac66454214c3883eb577` |
| `dfb-template-infeasible-branch` | `dfb-taint-typescript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-infeasible-branch-positive.sarif.json` | `34cfac4799dc1b3090e4cf13803a5eeb8de8ed8cd3da712dc53a42fa85374d82` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-typescript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-local-chain-negative.sarif.json` | `297c4e2d882fd80fdf92c798e903f3cfd2279d12e0435f4d8ffeed3816bad338` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-typescript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-local-chain-positive.sarif.json` | `bbf7f20e02c8d188d9c33832ae6c5eef22478053a83645479e4148d520bbdcc0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-typescript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-local-overwrite-negative.sarif.json` | `d670dd2a249d8b83fbd07e486bd11b0a8d4cc52260b5419b3f712e45e199fee6` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-typescript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-local-overwrite-positive.sarif.json` | `aeab78d3c0c2e3ff460722991341c07afb754b228ee7224e68d34f24a9a2409c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-typescript-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-loop-carried-negative.sarif.json` | `a17fd1d70a8e8aba3fd3827a3c45353c68c34bd26323acda52c5bd4ee02c4010` |
| `dfb-template-loop-carried-kill` | `dfb-taint-typescript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-loop-carried-positive.sarif.json` | `547cdaa7aec4a723171d933377bc8d17bc1cad787417b244a05d13ee9768d103` |
| `dfb-template-object-separation` | `dfb-taint-typescript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-object-separation-negative.sarif.json` | `4e6cb67371bb29eaa8ff13ddd2b66b00af5f005224c1889fc93f33ac3297918a` |
| `dfb-template-object-separation` | `dfb-taint-typescript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-object-separation-positive.sarif.json` | `6102c1c61ddb834bf9282cb377ff25421a26d0d1f742684862904572dbcae454` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-typescript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-return-relay-one-hop-negative.sarif.json` | `7ac68ec9ad3b048e6f6ab2ad5990bf6fb1ae1a71bbc688d46360f7c1697b5161` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-typescript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-return-relay-one-hop-positive.sarif.json` | `b17e62d68280a91dd8676ab77137b16dd1c0d0777f8ab5334ba8400332d5a7c5` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-typescript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-return-relay-two-hop-negative.sarif.json` | `18b1be7af52ebfc0784497adbf3b50c5b087afaa8a4ea39753bffa465ef1351e` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-typescript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-return-relay-two-hop-positive.sarif.json` | `b9c13271829d0d7ee93d5452aa1e0d278a10b0aa6eb712d1102854913624db84` |
| `dfb-template-same-object-field-separation` | `dfb-taint-typescript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-typescript/dfb-taint-typescript-same-object-field-negative.sarif.json` | `1903f89f38497e04af654287c7d1dedccd9967ba5a7bae9cef2cbda5be0ec577` |
| `dfb-template-same-object-field-separation` | `dfb-taint-typescript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-typescript/dfb-taint-typescript-same-object-field-positive.sarif.json` | `53562c16311ce966284aad75053384f577fc450cf27041bebb0af3500c3d9ca7` |
