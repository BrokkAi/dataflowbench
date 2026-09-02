# Scorecard `bifrost-smoke-taint-taint-benchmark-controlled`

Adapter `bifrost-smoke`: `bifrost` `bifrost 0.10.8` (build `419395c8066b9eddfba06aa69c8a151ef4968249`, adapter version `0.1.0`, configuration `2c5ababd371ee6b9f4f0596c570d2378aea79cc2e21c8a3e7e0eb0a195f63911`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-smoke.json` (`sha256:65bdb4c1e0c3849feb085f445092e5ffe4103085e7cde0e737dc2bc182a8f82b`, normalized `sha256:65bdb4c1e0c3849feb085f445092e5ffe4103085e7cde0e737dc2bc182a8f82b`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

## Language `c`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-c-direct-negative.json` | `7010e1a9bef6879eb33e99b04e29a35727328e0834a7831c53de10484c1f1905` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-c-direct-positive.json` | `0bd7f089f7f3f567329165ee0e1f6783b735703439456a3315e9f10625fea0fa` |

## Language `cpp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-cpp-direct-negative.json` | `86f8e77df11722860ece5a54603d1a3c0e4f63a54c931fc93294b8e3b7e820d9` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-cpp-direct-positive.json` | `2c81b6a77552b473fc61bd23a19fe1e8192b4fe7f5f7d65bf5b5d91125cb590b` |

## Language `csharp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-csharp-direct-negative.json` | `1ce2f82baa87018c363140c3511bdbc34c362780079b22a5c906521302a265f0` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-csharp-direct-positive.json` | `d87d97ffdf6dd8e0655bac49e925663ca0fd267ac561a2913ac2ba870cf7c9e3` |

## Language `go`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-go-direct-negative.json` | `4931061a787a9f2aa709ccc5197657e647539bf392360bb46c18e32da0d43251` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-go-direct-positive.json` | `3091f95d33169a63a5375b125c92555f402f36499e773d029eebc3744628850a` |

## Language `java`, tier `calibration`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 0, `unsupported` 1, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-java-modeled-external` | positive | `unsupported` | unsupported | `reports/raw/bifrost/dfb-taint-java-modeled-external.json` | `01be675e06e4fa5eabdeb5725a1e06efa319ac6156f2e492cd1689c69e29caf0` |
| `dfb-template-one-hop-relay` | `dfb-taint-java-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-one-hop-positive.json` | `a2306c46fe4503c2e507ce86d37da6e781529c467023fe04aa850a77af89dcf7` |

## Language `java`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-alias-propagation-negative.json` | `ec22a4fedac60f7a94b53354a374cd5932e14d9f4d3665ffd80a178d2675e264` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-alias-propagation-positive.json` | `a8a781c05c4be33c3ae20bb050c283987a31d80857aca1064b5c07218110b7b4` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-argument-position-negative.json` | `f382429a3486bd2fe9fa83179c029dfdec9badc5e1f01064b57ae9f0eacf6bf5` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-argument-position-positive.json` | `569ee5de1e410f6bcbaefd33b20d5737b32663f330ba99c834ae475be100e3f5` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-expression-negative.json` | `4eadd7f224a7e9210d94fe0623fd05d1bdadbe8952be66f0f040741a37d52784` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-expression-positive.json` | `8c282cc2e8510356c29c144f7c194e467f2c9f0c844adce047e17ad1f24c927a` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-array-element-negative.json` | `8df79b1ff7798b164375c90d9b15430da6f113d6067165582b9b615737243b45` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-array-element-positive.json` | `3bdda41e485c7ccbcc0af39ab67676ba8adf7d3a801a0b5e04c2e1909fc12e17` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-branch-join-negative.json` | `3fc10a44b014ffc318162571f8a42203d4f6da51c5f1f20cb5423d7a09fc6bbb` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-branch-join-positive.json` | `1266687abdefc78238988d81ac69dea79befd82c9e27ac42781694807fb8d55e` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-call-context-negative.json` | `82efc48b4ffc8060c084ee579d7eb1545d9bf8bce12f724c1160969f1190bd4d` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-call-context-positive.json` | `0886babe45828fbd9561ccb126716bd36359bb084eff10f11bd9ba919e172808` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-direct-positive.json` | `5bfbc9c412d10bbcf530959908f32055eeb015f5d9d94b1acf802bcdab14b6aa` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-explicit-negative.json` | `2ace20034b6a6ff86f61d78840cc420a68b64c0506726a4f0950e8e72a714a30` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-exception-catch-negative.json` | `640a224a177a11d29473e77b495564543afcb3aada1536a704ac9d5907261d68` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-exception-catch-positive.json` | `af41768e04fd1e2e3bdbba31bc3157ddfc3c8e93e37d7d3e76ac4711b096b781` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-negative.json` | `aee05561aad938367e2f7f9ff567db559c265c46de6948ad90c742a91c8852a6` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-positive.json` | `419d6b7ebccb3099b3e69a9282b44e8cc3ae2bc620aa9a017936fa9e58298b71` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-chain-negative.json` | `c23862b47975d12d97c5f95b0446020c929903bde335600ba0b03af7fa456265` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-chain-positive.json` | `078b3e7b95bbb9f67eef7193b198b4d743ca8924a807aaf35b2d133087ca0ec7` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-overwrite-negative.json` | `a00d05ee37e30d78688b2fef1cc64c07462049cc3a32c4ab6c4e7aeeef0062c4` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-overwrite-positive.json` | `e14c61ea21bc8634bc9f4847aff2259e582dcb5f57d98c7eeef1edd916c54591` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-loop-carried-negative.json` | `3b9851836fee91b9fc264f26608d0f24d39abb96da9fc16c38756ff0c3c8d348` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-loop-carried-positive.json` | `66220fd5fefa97ce9500734ef5d9ace351564e4434097ae439b6f41949555f1d` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-object-separation-negative.json` | `9ca712535c141375be3cec44200559e3335855c9103ec1506f2caa9ed1ddf4b5` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-object-separation-positive.json` | `5a1c4d00ce627f8379be6f5c71bb62beeb0ae3466d620d04f9d37e703c11a156` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-negative.json` | `05a1164ce8f664ca009d3d54b572c5823e9b878830a8d725bd939da7fac2ca18` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-positive.json` | `aae18c852008661a8d26437cf93137bd6e6d9d2c3023f5e7f12ec14d0c243371` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-negative.json` | `b0b1abc9d8a3367be6dce900733e32ca328b360a8f7af2a9bc6be4086c370923` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-positive.json` | `6679b96b949caf22c39376debaa0c7f8e10e0fd35a52a1bceae7228460733e4d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-same-object-field-negative.json` | `5ec47065f8d7aa81b277de7e55828e89950ebc91a4c747777418e2d10ed657b0` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-same-object-field-positive.json` | `23cfcfc34050fa84c1b900f33c13a34d66c64b62f59e7f97ffeed5ee83103ae4` |

## Language `javascript`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-negative.json` | `0e76b50efe8230a37c721ee1ee8bd3635f783e5217b90a5f6a2f5fcc6d013ce0` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-positive.json` | `b4a3a225a8013103293c97d018d44bf6d58db7782ec3985757826946cf7fd793` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-argument-position-negative.json` | `6370d2e76bc1333edd1f6dd0e52e6425c3f4d0ac28f5a781a6b141ec20f56b82` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-argument-position-positive.json` | `73d305d14be7a88d826a319cbce3099818e20d56eea83ab009c39cb12b63e195` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-expression-negative.json` | `149d3c49f8f756c96ebf854e00719cb21e079b17d8132eed0aa51169f3a351af` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-expression-positive.json` | `46e9bd57fca47cace6a294e3ea979001e80a1d6fe60eca188f37774bd950e544` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-array-element-negative.json` | `2cd38af4b7c42b6a24b34e882b4bddf05966ef98d1537e123750f326ad0ac8f5` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-array-element-positive.json` | `46a9a144d135c1b55ac0577076b303fe479cc9403318a0d5b35bff36279dfb1c` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-branch-join-negative.json` | `8a1a6305d35a7b842ee023a52c26bad40c85efef2696e445580da3aad8d6bff6` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-branch-join-positive.json` | `288b7e73c5cfca16eab297ea783ed3e568c3c233ca0e19075197f5da1e0038f4` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-call-context-negative.json` | `7f811d87340b8da65a3fe7418699a6b94de699f565c0de78ee89797415b8d753` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-call-context-positive.json` | `a0ee76cd1f5c36a75bf3a9037c582305f6fec1539e37aa265b8b18f9f3791a33` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-direct-negative.json` | `f1efb180b699a167a3bbf660b105b30ec93374669827b2b7cc1dc2f8e0aa7307` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-direct-positive.json` | `a63a95d6c7b97453a3104c68dd0f78245d255655b7f114a2fcf808167b8aac8e` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-negative.json` | `4c314295ff38b5ee85942e26ab93936987fd1e9ddb7b44619258e076e872f196` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-positive.json` | `3499bac0180c53cad58bfcd44c41aead9dc18fd82febbcd5b66f55b1f36b081b` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-negative.json` | `b0ca0397e82d8a192ecd6c80011616c9196ddbf16cb11f7d4bf72a555ff2161a` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-positive.json` | `7c007278b96c690ab38acd7a94698bad88e9850a703cc8674a797b7ca5cb58e3` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-chain-negative.json` | `62447e2ef516b637ceaaf21a3e2d3c3378ab116460c72811082361ad602d87bb` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-chain-positive.json` | `3f95ae8b14204f0fa8bd992a536751b17b4aa1c5c3180ed503d9cc7358bc64b2` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-negative.json` | `7e128a8235bcd3d4aaff6fe053af7a1d1d6f83a9ec05be51dcf9067e3bc47352` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-positive.json` | `d0e30d5299bc5c837ef9d72a1f45fcb51967f7560d42976013c64c3c120ec823` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-negative.json` | `1c518eb6629386b6d9283222d9e6285cb5e937424eb34e71177f96c51b2a1b97` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-positive.json` | `705b6d91a4d81cc1f5d637a423b084ead2e42f77b7d3fd37a8a67a10a91b6461` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-object-separation-negative.json` | `fac5059b1774d29fe8d9a48a11cdd29f825cc7e264d1128a469b09add69270a8` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-object-separation-positive.json` | `57e1fa74b9417d04a67cf9f8394a8c4d1a2c7496c79be8dca279818a7babc6ea` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-negative.json` | `4548fa98074834fbfa3112552ca829e1b6d42e7a587ae853b2e533965ee9d864` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-positive.json` | `ef4c9192b92dd5ca268b8a8a5ad637071452887e87d0c3d8c407b5825c9b94f8` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-negative.json` | `1b706d2b886d697dc0aa3955f9ef4769fb906437d2f32cb7bc05e91b7dbc4358` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-positive.json` | `94c52fcc72f99f9e64a0da9a2db239281864f905ca093f9b8aa2170c1df82249` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-negative.json` | `0d2881933e8e0e0986de63333a2de0fa0b9e876cb67751ba5658ca94b36fa5f9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-positive.json` | `ffa9655fd7bb05ebf1e749acbe97431c315c1f1b8226369922ac26af6c93f640` |

## Language `kotlin`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-kotlin-direct-negative.json` | `016f90c45d3f8607d6115e581ab38e3a102911c28a2335525ef2532cf39e3922` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-kotlin-direct-positive.json` | `620401270ebeca8b90ff2ae1b75f36948e12c3e362eebb3a03693aed259e92d2` |

## Language `php`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-php-direct-negative.json` | `60c8ec6a89fbe7e7c3fa5867ba9c0e11cba92ebffb2fb5726c155356b559a878` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-php-direct-positive.json` | `466dca8321dbcd97516588c36e8494abc17323829783e289c3b61abf792abbee` |

## Language `python`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 16, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-alias-propagation-negative.json` | `bde78c543e2cfdbfd489fa89de549fb6773e0a7769eb0ac6a49a548783480a9c` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-alias-propagation-positive.json` | `95c3b82d3957a8175ee8c92a1c3a6657dd34576a59cbd4db557d26066f01c748` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-argument-position-negative.json` | `fdcef41581418b3ebf1d7ffa53a2beb64f62a934d799deef28ffba38b73bfb8e` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-argument-position-positive.json` | `b37a8212cd9b17241c295641d3c33794dafcb3df123a41070afdba35a506c79d` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-negative.json` | `4da2ab752141e9d27193914feb7960ee0d33f2e373e9b227233c63426244a8ee` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-positive.json` | `52638571e7f9894eaf15d2b5354155a2d9f086a942688c73c67ff7ec8e54bf6a` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-array-element-negative.json` | `36b7e6e08e099bcd48f61f90f7df4789fe59b70aae4e149780f16619383f787a` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-array-element-positive.json` | `bcb6724d78f1913bdf06131e7b8077cf14dbf1a4126ac3ade82f59d1977df068` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-branch-join-negative.json` | `8fa3609b7db219796f958548e5991bbefa4ce95a39a954fe70dedefe1abcb36e` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-branch-join-positive.json` | `4809c96af18b6720c13a2d7be668536ae30f0540ae235fd7e8c0a2791b0da432` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-call-context-negative.json` | `8eafc04d49153ba7cdade780bec1be9c72c6d8c551b0bf3856aa2a24957555c3` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-call-context-positive.json` | `2aa9be4a7446a5e339c8ca5dab3881a366b28caafc43e0557b9bc5212ac2ec4c` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-direct-negative.json` | `fe4ae4fb0af819192c0f1ef642df0b4ac06dc696787f5099c15e6567d81731b2` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-direct-positive.json` | `8f4abc95a2aacb9889a684cfe37ceddd21d79284286a7497ae3fdea60e4e1cdf` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-exception-catch-negative.json` | `5539e102c1e0fe8f5807268b6ce33abbe7005e8f2c2414a22cb4b80e2eb27444` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-exception-catch-positive.json` | `55cb688371847826080c9c8e13c58adf466ecc2d742d3397f87ccc23018f7a9c` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-negative.json` | `26bc42a55dfaf94b1140a115693b4a0f9e6d3971777cef0bd00346d74bc37bda` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-positive.json` | `49c787bf85ea1894241b597f4a75a8b84c875524acf94d696016d8e3af65c140` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-chain-negative.json` | `35e2a5c0fefe3151ac926b5e0e9a27d8e895a9f8b00aab6ca90c58f75137d14e` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-chain-positive.json` | `3a7f8ecb1d2394f70e7236f172c1417c06b46cea47dbd93453e4926d3878f27b` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-overwrite-negative.json` | `5697f33ad65811a1e4956545da8897c531f13988795204bcbe8f4d8e6f03151d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-overwrite-positive.json` | `09b987e70e9595819da556f81a0372f8ab0ad07b440aa552556939e66fec04a8` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-loop-carried-negative.json` | `c727c7444f855f275701da68f0e29f2f3f7faa1c94a806d6aa0f18a3fce1ba25` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-loop-carried-positive.json` | `7011f173f8f2725951d95aed94108ef788520f736ffafea26b56deb46c5a0450` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-object-separation-negative.json` | `397b1c2ee2955d473a7a17f6fb14700e97f34b4245430d2fae28546e71431ea6` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-object-separation-positive.json` | `b618e9dfcc25c49516ee85be476dd556d01a2d62c04c3d220fb88cc12c254a7a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-negative.json` | `21cfdfe79bbf3c894e48e5c310a05dea3cfda150c80179abe588249769590632` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-positive.json` | `4a26e7a206a1e3230fb7df23120896421a86b726ca1a67837e142d2fcf45dd8b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-negative.json` | `69bbe250a788e0a463b2ff81ca8d6cee6dcb77bc61947273266a135cdb08fade` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-positive.json` | `b2b586d474cb5dfdc883e502c7a825b1aa9ab5192d5355d22602d863ad8226a0` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-same-object-field-negative.json` | `a13e54d8b8924d61e1463b9739e2670580a3fa9840e549fbf010ffeb57bdf587` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-same-object-field-positive.json` | `8fba63c20d573235ebed517dd4edeeaadf5c38c706baf50729fa8453fae0bcae` |

## Language `ruby`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-ruby-direct-negative.json` | `d82bffbb1f2c366f2e7c32c27568b27b453ad5ed75c7bc127028179db43b85c5` |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-ruby-direct-positive.json` | `e77ccf75876e6be5a7a18e497abba503bbd639c5c0e0ebb0a566d695f317c8bf` |

## Language `rust`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-rust-direct-negative.json` | `42a6ec4c96971854472a3f2c544dbe2392c91668e4ba95449fc57baf03780a8d` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-rust-direct-positive.json` | `9d7cc3303648e5a698a56af5377e725d0b7cb3edd3463fe7eaf919b160ff2a80` |

## Language `scala`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-scala-direct-negative.json` | `3229824f0a7f464e87f85da88d124372cdc2e4620fdc633f39728c328d8000d8` |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-scala-direct-positive.json` | `8fb86b5b3fc1682b2161c75f2b2570c9a2579545b68de6cf2d2a07c54a029026` |

## Language `typescript`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-typescript-direct-negative.json` | `f732dba8729d8184141c390e5960c6df9c594704d3936aa69a548024aa38b77a` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-typescript-direct-positive.json` | `4220b977bc5cd7c053bb154388d39d1ef066e2d44879c06c8379c3976e513e96` |
