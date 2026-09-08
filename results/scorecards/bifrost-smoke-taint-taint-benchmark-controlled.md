# Scorecard `bifrost-smoke-taint-taint-benchmark-controlled`

Adapter `bifrost-smoke`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `2c5ababd371ee6b9f4f0596c570d2378aea79cc2e21c8a3e7e0eb0a195f63911`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-smoke.json` (`sha256:40430c845adfe1a4dd3572758487e67538e862979104e3836321c269d6c47650`, normalized `sha256:40430c845adfe1a4dd3572758487e67538e862979104e3836321c269d6c47650`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `c`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-c-direct-negative.json` | `41e4429cc9dbf74a5528e90db6b87a1c5ef7d8cd1ab553507e54062ecb37043a` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-c-direct-positive.json` | `a4ddaeef10a7129a03ede4ee83e2b1f645ee8cbd01f6c65bdb351d283a9b2e2f` |

## Language `cpp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-cpp-direct-negative.json` | `285050f45610d4ecd499d64624664aa9bbc7d4c005fbf29974b5fcda83fd82ee` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-cpp-direct-positive.json` | `8b2dccf107ab8cdf27e1ab9696f8e4e27cd99b25cad4b2297610d85eb60b5444` |

## Language `csharp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-csharp-direct-negative.json` | `36b18fb8f2e621c05bb60ad3b2e4055fba8bfecb967be0fa1df40b2aef7b24f2` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-csharp-direct-positive.json` | `0a6dac11d9c3eea25fb871552d091940216cdebec55910acd5b50e0b13f0e30c` |

## Language `go`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-go-direct-negative.json` | `23898049f8fcba24aa6daa6875ca069e10438dbc247b745ad090ecc922128d32` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-go-direct-positive.json` | `de57dc3870c18cfe26d9ac3e3274ce579e262e602c43d33bcb1da00b0867a0eb` |

## Language `java`, tier `calibration`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 0, `unsupported` 1, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-java-modeled-external` | positive | `unsupported` | unsupported | `reports/raw/bifrost/dfb-taint-java-modeled-external.json` | `01be675e06e4fa5eabdeb5725a1e06efa319ac6156f2e492cd1689c69e29caf0` |
| `dfb-template-one-hop-relay` | `dfb-taint-java-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-one-hop-positive.json` | `e9b89c4b9aa3ffb991e4773160864f07b199b92e07b0a3b85a96bf187e142746` |

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-alias-propagation-negative.json` | `43635c635048533f0c453921b94a51c4b4f3a26729c072076996d55828c6edd8` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-alias-propagation-positive.json` | `3edf03d54f9232aaacd991d5fcfb4308bde5dc570ca8ccdc821c46617a6113db` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-argument-position-negative.json` | `e39ea9331b36b1938de989d0c20c6ab2fcdf1bd8a55a5f8fa6cc1a820310c0e3` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-argument-position-positive.json` | `3ab82e428039ae8364eda02f443bf013fd503e957f98da17107fabb5cec1d6d9` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-expression-negative.json` | `01d26313ec0cdef4fc6e0571e9dcc816faf5c40235da0b097214d60d662effdb` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-expression-positive.json` | `47f684333bc4890599c31bf869829799351dc3fcacfbcae177753d2061db6b62` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-array-element-negative.json` | `525cbfcbb651ffb78eb6633c48f51892a9a8c0ba5df7f81c4c83431713e75213` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-array-element-positive.json` | `0a20c6e5f6434bef3426c421139de9fb1878dea9619328dd2d1350737c6c5a93` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-branch-join-negative.json` | `b4a15ee8a1e5bd3be41e4ef7eac15a5383952305025d8837f80c5bb02dc18bf5` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-branch-join-positive.json` | `39709ff95d30f1962d348d39880646e3461e7c52e745cb13042bf37ad52688ab` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-call-context-negative.json` | `89243baedf713a02fd231b78f6e06b1e2644d5e46d96436b7944a228f8f4824f` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-call-context-positive.json` | `61e5b0eaf91769b47f85826ebab1a4fcdcf7965877f8693a22fdd178cb3c0f80` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-direct-positive.json` | `dc2f085e18a4b893625a03e59aad8958da4743164f2ec452f1d4946bb9fb1672` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-explicit-negative.json` | `63f95b48648a4c405d0e344a494291c89635d7500bb90e7725dec14b8693fff4` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-exception-catch-negative.json` | `b060db1bbc425a5ac5040f1238b5a4301604618108aa78ffce3a1164c6deb073` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-exception-catch-positive.json` | `c3623e4ab967467fb0d66ba76b6ede2a6304417099c75107524a5957957a86cf` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-negative.json` | `0838b176a482664a17d0044076a78eeea62da6f646e9d46a6686c750285d36f4` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-infeasible-branch-positive.json` | `4d3d8c8790148d21bce5c43a3d2b0aa504aa1e26e91cbdb08deac6bdcb2638fc` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-chain-negative.json` | `431b6874ba08205d6ea9ea2eae7fea24d3c77494f047e140e0d3412c52efd142` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-chain-positive.json` | `4c66585efd7cf38be2ca238909dc6eb8947082054b6522275cde12fbb13c7775` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-local-overwrite-negative.json` | `3a17ed8c34bfecd4e9211bed5f665980a9e80c878773620b494d641fe5018566` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-local-overwrite-positive.json` | `c4043aebfabae5eaf837e8773952f6637d68c1b7ae546cc5a7d568447abc6fd2` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-loop-carried-negative.json` | `b281722fb4387362eae40a08e56c70f9b4bc0f305becabaca76cc19976d0d434` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-loop-carried-positive.json` | `9da0d87a6badd5c7ebc38b564eba9bcb7816c91b5990b41c10ec6f57811b8509` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-object-separation-negative.json` | `096d7e56e624feabb2accd7066ecb1b10236c376264a2c0c14def7e664d7c115` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-object-separation-positive.json` | `4134d73ef5f760d04b0c92286fa852fa516c7024aef18e4d5afc9500af3a8346` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-negative.json` | `d2a0fe422c4c362680d8ca5571104dc8616485f59f7611119dd9cc88b7e683a0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-one-hop-positive.json` | `a4b4976b73eeab995b730aea16c39205daa96e3d50c2d79c855a4e4a711f8016` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-negative.json` | `c0f127e4cae31bca70fff4fefa7651faf726c7e2b015d88fa402d624d424af41` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-return-relay-two-hop-positive.json` | `e579942d5ccb9b14e7c1cd701375b1e5a9c44a6833f0565c06fe99f2a562bb00` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-java-same-object-field-negative.json` | `d816a450982ea9f0df2a4199b261b43f5be025394c27db3662e747ef014a1199` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-java-same-object-field-positive.json` | `7502c46605da8ab5fe09a87eac9565908800aefc91ee41a50329e6ab9fae1108` |

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-negative.json` | `6f859129075e916f11ca7ba6fbbd0fae3ff4f73c59fd273e88fb019d1abfb1fe` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-alias-propagation-positive.json` | `a8321099cdca5b2d2db88c81013e61928a63d08415186a63d4214bc9f3dac930` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-argument-position-negative.json` | `ac7c4bf2c454ef69a7dd313f385d90d1f9cb73533dbe32be5d64f68884b7a15a` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-argument-position-positive.json` | `030e77aa6165f41856651704f52be862cc630a192cb8994defe156d08f8de0c4` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-expression-negative.json` | `e510bedc1c81b105ff74865f887899b045e1d35d3546986b806c37489babd131` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-expression-positive.json` | `a29f045d08c87c5b5217b4820ac5aeb10114b488949711fe8b7844938589aff2` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-array-element-negative.json` | `57bbb72bed9569d4dd92b2885795791646f56874a8dd140867a718d796a32e58` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-array-element-positive.json` | `0a93c53dcaa4cbcb20baac05ed582b6dd5a2ca91762507388a7a1162bf06725c` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-branch-join-negative.json` | `02b6dd8cfd26589ce6309df0f9cf4ccf4acde340d330e72a4d15a56835b6b98c` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-branch-join-positive.json` | `0c62f1909dc844266092998611359598d13bb4a9e67d9b1da66342abc9c44abd` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-call-context-negative.json` | `f46ea216ecc861060e556e0aa4f166172567e63a8bd4ad9147b85577a3734770` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-call-context-positive.json` | `54cdaa29e891eafcb48dd3040847bc1ffb42b4c967d82e8094b1d45a9121be2f` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-direct-negative.json` | `0506fb37ee8858bb4f47212172a3caf611bdc9af38b31c94958a255e61152fbd` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-direct-positive.json` | `4150d72aef9a6c0987b436073300322cd5f55c418728df759f3a1849ee08f4ce` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-negative.json` | `cacb07a3587d94d1c7fff15980b9bf88b4b8e865264da36e2e2a5a372222c3c8` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-exception-catch-positive.json` | `08bdc04ba7274f6b7d1b97ee6d4e1c6faa3866704b60ce91fb35601618af946e` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-negative.json` | `bc9e67a0e24371c29f917b799abb637f8a0aea93bdc6695eb46d9b084886d0b6` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-infeasible-branch-positive.json` | `056c036e4db9f9a8fabd39a4f37c35ee039dcc8f57a48a0f72bd4d538d8a3ca6` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-chain-negative.json` | `1be2a418c395feb65bf2339a4d8f0fba2e29662fd71a15c55d9d41d5ebe92512` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-chain-positive.json` | `9d5d0730ae6c360bd0612540fccf40561fffde6104d557e0eaa4b054d7e23240` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-negative.json` | `ce377fa2b05a0ebb565430deaaf426363070eae33ef8cdb9c6c80a3d7de11169` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-local-overwrite-positive.json` | `98bdcea4b30bc784829150d271d3f5296eb35dcfaffa3c7cfbab28478d851df1` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-negative.json` | `a847d0dfc2145163fc3e588221bf94c06528191c86450daa050366ee529bd498` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-loop-carried-positive.json` | `4139c484df59aef6ba967fd5fd5e422c13237c9719991caf0a9a690f78c270c7` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-object-separation-negative.json` | `8b5ee10235d02870b352294b6f94bbf84de2b2215e1f43eea6cb3f6bbb6f8de3` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-object-separation-positive.json` | `ac9b118c1817944e9db8fd93eb0e17de05dbb24ea02c7c7bddb70e34e4add418` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-negative.json` | `0a188803d7993f60c2123ed46ec2b75c984fde3b7037a6e2cfbcbd8d3ae3a918` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-one-hop-positive.json` | `1066f8b34a004db289cd2c9d088759ec6feb80381df558d2b5d4a707a3c04f6e` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-negative.json` | `58db5d96f9c83b04ac67116d8962ea9217df9aba2db9ca57200647a9572cd3cf` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-return-relay-two-hop-positive.json` | `a1ca8f879d7a15f8ba2a3fa70fb01ecab34e8723b5cf1d30b411d28385e22a59` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-negative.json` | `0f6ebb4ac090eec98f38ecfa77e6dbef8da57ebc5c746f9ca42953a85aba4795` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-javascript-same-object-field-positive.json` | `3054efe019beb1a70e97cd1feb79ea55a6a2268302a1c63038cdc07fa9ef2b64` |

## Language `kotlin`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-kotlin-direct-negative.json` | `211ededa5977c304d30b9d61619d1dafcd2323caaa4917671e767f4b7e8aa0bd` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-kotlin-direct-positive.json` | `45b1d02a7e71969b02075bf798641c69ac804e2236c24113610caba4529c824c` |

## Language `php`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-php-direct-negative.json` | `d80647c59cf002b7379de75f465d247332b7f59bfd578b418758d868e6cc02d1` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-php-direct-positive.json` | `e63145a9344afec081a6e47547488ea109f12b043b76845d636a345a13147c1a` |

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-alias-propagation-negative.json` | `184d639fe4a3ca920448a79d0a92cc59fbd13df3d39d3b97b8fe6c48e7a7d518` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-alias-propagation-positive.json` | `3e427493ad5f169a7eaae230bb81401a0270f1f82c1d5129b9ea0dc9b6e8031e` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-argument-position-negative.json` | `c3cb1777ba91dc4ee5ffe2a75de2add2ddd65d0777a4dffdfb859a513bcfdf34` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-argument-position-positive.json` | `8f960325ecbbd1e22dc78cb880760b14fc6f19abb2f0c4cdc93c6490057abcc2` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-negative.json` | `a672bf03d39335b3c6a2c8ab77ff1fa6226cad2ecb98652abe550049e29cc745` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-arithmetic-expression-positive.json` | `07b2e96ccf073e8d80c489025cb3a180f118d2a54a1021e58be394fe46d000b0` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-array-element-negative.json` | `14c46aca8aca3c80eb6a19d849f4da5ab6a6ab7dded09377b921e4c49bba8ca6` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-array-element-positive.json` | `4951a472426bb59979b56bc66741b9a7916aeff2ac8d0c3bbed807d0be2ae7fc` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-branch-join-negative.json` | `813f4298eaa62943b05472d4bca297e1cb4e2c5f4b0add3c992b9a0b7887e83f` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-branch-join-positive.json` | `f9ee82db4b50a1a9f2a5a80ca63ece3c01e71d83102bdd8de6ed5169965ce5bf` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-call-context-negative.json` | `9df27ff767320afb87576e0fbfad53f688dad317e47d4d7517367958f6e257d3` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-call-context-positive.json` | `77e33c8894ee5843dae7d3d72898d449b85ec1b2f83e38139b867f840066084e` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-direct-negative.json` | `9b3bfe657fdeb36b341af497cc4a803327da1dc476a889ae48502cfd6091efd8` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-direct-positive.json` | `93e3bd219a7739eafe094e515c9519dc7d4e9d6d4925d1ae4139a4ed5f1fdf8c` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-exception-catch-negative.json` | `b919ce377b4ef333e3a8f1ef3d6a20461198c70b045b6a640bb8d6a4c6ed4641` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-exception-catch-positive.json` | `c5a1bd5c04286c6f73af6e622fc5fd61f1cf7d8b008b36ab36adaf4cfc2dd1aa` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-negative.json` | `4176f87da5edf8f7ab0987a41631cb889d8565fa74aa2c961388a3d7c54e8653` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-infeasible-branch-positive.json` | `363ce164dc04f17f0534cfd0b33ef3eeee8a5efcb36592ab35201010f6416560` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-chain-negative.json` | `77d95542c113cae7a0da97eb2cf3a4fe75b74fb94f24a64497616b4c6d245a4b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-chain-positive.json` | `d34bffc735a949a3187d22a1133dd59ada5b6db6767503c225c32cbfb5690654` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-local-overwrite-negative.json` | `f676f1aba2c5e33de271ecab9676c1e1b2f0c93cffdf01f47cede83cd410c069` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-local-overwrite-positive.json` | `2c44e437ce99ed4d7af6df76e17b5b4367c91b6fb25ec701f226297b18a7cdfe` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-loop-carried-negative.json` | `e03ba025f4b36118124235187b4363327824cc0cf8be9fb7e0ca3c2069a928da` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-loop-carried-positive.json` | `080be57bd5b4739287014643e3a1daebf6e3681b102d813fe334270963124186` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-object-separation-negative.json` | `3daa4ffdfc181ac13412aa10808919ff5760d9e64cff7b0c8ce00415852cde71` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-object-separation-positive.json` | `b491c0b30f22ae35c3e5463eb93904e1feb0551a39170a73c8a8971f18d9c369` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-negative.json` | `d9f0a87f9e0dfbe992744ffa528100b62194de31985b519955250721ca10b754` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-one-hop-positive.json` | `92b0693cba9e43be417eea554965dbda990062b2007b0cdd794dde236ea69adf` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-negative.json` | `4a28b9c289d56c3a6dea922d87ef90c63cea937b3eb2b584222e5202feb6fd6d` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-return-relay-two-hop-positive.json` | `0c33412ba7e1683847a70baacb3d50a7f4dad329fc5c81c7524475af0e419d8c` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-python-same-object-field-negative.json` | `f28fbb587c8fecd245e5b1dfbecd9830c108aeaec7cebd458a9d602481509bc1` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-python-same-object-field-positive.json` | `3fb4a6c3b1278c023342030d0ba2e1d84484c039fe31e5e91ee3ceeb34eb8579` |

## Language `ruby`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-ruby-direct-negative.json` | `714cd51c950fbf77d06b74de482a8d8d730e56a7fb8753a2f261486e5e499d62` |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-ruby-direct-positive.json` | `696b839f94accad7e75c74d12b0d7557f739ab3e9876c5abb009281381ae92ff` |

## Language `rust`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-rust-direct-negative.json` | `1660d3719db9faf738005672fff67d2ddd132a410c540590c7b621c3a42cce72` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-rust-direct-positive.json` | `61e1b1d6f7e2a16030717a61657036b6ec7492a6ec39c6efaf2552f4855c1901` |

## Language `scala`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-scala-direct-negative.json` | `8fd4835685ab49e59415479fe59f9876d3a04928a1657e0104d2cea88ff01a06` |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-scala-direct-positive.json` | `f1a7e583e2c6a3cd9efb5394bd38ddecf02ea61849c29707d6f8c5d3519ad32a` |

## Language `typescript`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `local-flow` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost/dfb-taint-typescript-direct-negative.json` | `786d7c08c7a33f7f1e238e2d4fdfb9d6b01305d7a601af9dfbff7628531fb9e0` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost/dfb-taint-typescript-direct-positive.json` | `fe77fa36837e3956b65368bbf01b7807d64b3af848c329b2b6e8a6b31126a79a` |
