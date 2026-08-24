# Scorecard `codeql-cpp-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-cpp-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `8873a63a5898c8b6b10dc24a9fbf2fae3ed5a088faf024524b0bae50f0fc4cc0`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-cpp-kernel.json` (`sha256:d4f5b18b707b7cbc70d38f3de573caa94958adec0bd983c9c2f2938be9f47354`, normalized `sha256:d4f5b18b707b7cbc70d38f3de573caa94958adec0bd983c9c2f2938be9f47354`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `cpp`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 3 | 2 | 1 | 4 | 0 | 0 | 0 | 60.0% | 20.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 1 | 1 | 7 | 0 | 0 | 0 | 87.5% | 12.5% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |

Macro-average over semantic dimensions: TPR 74.7%, FPR 12.4%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-alias-propagation-negative.sarif.json` | `1dd53c121ba31d12e588ff007864cfe9950cb395e916c01c867fc90dc5ddaa93` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-alias-propagation-positive.sarif.json` | `2a86cd6b6b5c1a304d123c2df3145ece0d953dc0112fba2c466ed846aa9cdf37` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-argument-position-negative.sarif.json` | `0fb1f434a17d6f5571fcabfab2b8fcf610d56e9ecd6ed504675012a38248e399` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-argument-position-positive.sarif.json` | `929d734e384959fa60638ef106891eb394c685be639465e5c8180b4bb4c7af1c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-expression-negative.sarif.json` | `c48bafe5a17a763bebb472da837b75e5cf4a308d6bac4aaac4e7d18f829f24de` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-expression-positive.sarif.json` | `a799ea7a4ba3aa8cb17a1fa1a8f432d87992ed7b734bba62445b69a90556d536` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-array-element-negative.sarif.json` | `2ff11e966927612a0c8cbe50c343e7451e6bacc602988292ee4053a577ca8d04` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-array-element-positive.sarif.json` | `02265e214897eaca539495e728fd74cc16da43dcb9f444d42bd4437f057ef8d3` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-branch-join-negative.sarif.json` | `672919850fb62295987a510083262822beb1f9fca628ea4c20a1d8d6433b7598` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-branch-join-positive.sarif.json` | `37eebf09948e4d177e29d88530e94331660720cdb46c9720e9bb88254319a950` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-call-context-negative.sarif.json` | `a5225fbcdfee73c6989ee013e2874c8ea599bbee9231b3cce812ca9958ac1f91` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-call-context-positive.sarif.json` | `02936aab24e80421aed9336597ec648816a742b5b65c3cec72ce7fc0b5c51416` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-direct-negative.sarif.json` | `de0dfcff0b4dfb70c0a0ff98d710c56dbfd709868fdf2b0159eb8bb7af929d44` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-direct-positive.sarif.json` | `4897c9ea57abf6aa577fb191eb7722c01d0fa6584589c105d8cf88521270fa52` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-exception-catch-negative.sarif.json` | `b873a86e8220a2364c55488c88a255eacfe03fbff6b6428d940003298a1d1995` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-exception-catch-positive.sarif.json` | `a2b722ff9214a571f4ddc1de7ebf803328323e7bc5b5e47a789fd1b67e5c7e55` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-infeasible-branch-negative.sarif.json` | `b73fb34c6d0c6d5e535ca2a2b76dbb3bd2db9d57e55138cf3f477c090917d3f0` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-infeasible-branch-positive.sarif.json` | `a755824e710f58d25f14f93e866a3c52e093c17b600cbe56e0f13414cdaf0604` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-local-chain-negative.sarif.json` | `8836cb26757ed2fe9cd7c279e21a0efa160abcbc97c8cb3f47e6d2578cb54a9b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-local-chain-positive.sarif.json` | `ca145eee9f99db1413528b22f1a54882c9b87d841b159049f447c9d9334cde8f` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-local-overwrite-negative.sarif.json` | `42c368f48b56061036982dee5d950a2b57eb3317807d8cc36942facb191af74f` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-local-overwrite-positive.sarif.json` | `0d9cc992061574bb2f862864eafd762ec17935b324c89fdec4dd229e5a9bf0d0` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-loop-carried-negative.sarif.json` | `4612d60595730f4e1be8dbe65b5128a6b1c95c732f95411275313bc684da1ca8` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-loop-carried-positive.sarif.json` | `1f89b97044a4bfd86989982fbc1bbd6a39e1616ae3a47c50fbe3f914a2051211` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-object-separation-negative.sarif.json` | `75724823bcefb91338e450067a01d02325f8131ace7b028342e4ee1401c5bef9` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-object-separation-positive.sarif.json` | `b296f48bebe73d6de1645d5162997401e9eb3426b79720ffd0b89ab4c055a32d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-negative.sarif.json` | `f3a47dbf212c1c48250d2a3bfdffaa46e373b530c3e5ceeb055a0b630b17fafc` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-positive.sarif.json` | `ac55470f5e4333723ce39cbb46fe9c67f91a36fd8f724d3a9473a6997fd17e89` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-negative.sarif.json` | `0fca54ace5fb26667da22f81561ca57d57c4acc97b67fa1a2b9641939ad119c6` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-positive.sarif.json` | `9c81e2e2ee95344a8f95087c38532dc9ff10e0eb317143c533e95a9c521b70b9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-same-object-field-negative.sarif.json` | `cf468298d1917c9126854c2893d29571331f2160e8827303a4b03942feed489e` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-cpp-kernel/dfb-taint-cpp-same-object-field-positive.sarif.json` | `db26ae02787b8deb3be58243a14ac6cea2531d8be7d8115badc099c43cd6b007` |
