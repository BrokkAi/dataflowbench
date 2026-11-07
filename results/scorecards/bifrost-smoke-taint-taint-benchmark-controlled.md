# Scorecard `bifrost-smoke-taint-taint-benchmark-controlled`

Adapter `bifrost-smoke`: `bifrost` `bifrost 0.15.1` (build `90d820b9ee3b1bcca9e3dd2a049b1b51dc854b69`, adapter version `0.1.0`, configuration `2c5ababd371ee6b9f4f0596c570d2378aea79cc2e21c8a3e7e0eb0a195f63911`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/bifrost-smoke.json` (`sha256:bac133256896ef2f04a885154123f4c01620a7b9c171a812e7a79ba9390a8793`, normalized `sha256:bac133256896ef2f04a885154123f4c01620a7b9c171a812e7a79ba9390a8793`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-c-direct-negative.json` | `3091b7f4db8fd56d537cc35901017b05e5424a0aa5f94a12c9122d07bea39f14` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-c-direct-positive.json` | `37553800d3022a811763a39b13e3b34cbea1f5d97489ac9f6d2003ec2816897d` |

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
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-cpp-direct-negative.json` | `9e33be037c98319c990a060b892ff915656484a5916d127d07b169c206718d95` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-cpp-direct-positive.json` | `2229dd267e782f3cb8501d60254f28dde4930b475883a42c4a156b575ce26f85` |

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
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-csharp-direct-negative.json` | `ede4838246b52764774d58955742f85bf40641854ee6bccb8913e5ac0680107d` |
| `dfb-template-direct-propagation` | `dfb-taint-csharp-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-csharp-direct-positive.json` | `ea95af29563d3535652bba178bbe411d46a5739367caf84b36df5c580196c6d5` |

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
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-go-direct-negative.json` | `550be3d2a9540af4ebbef6f8ae6bcc6d7ae59afb67f20ea406946bd9798e8a04` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-go-direct-positive.json` | `199c39444cfbdbeb4ea36218c9769201deb8c817a6ecb68b3908597315c02ecd` |

## Language `java`, tier `calibration`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 0, `unsupported` 1, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

Calibration cases exercise schemas and adapters; they do not contribute to a correctness score.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-modeled-external-summary` | `dfb-taint-java-modeled-external` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-modeled-external.json` | `01be675e06e4fa5eabdeb5725a1e06efa319ac6156f2e492cd1689c69e29caf0` |
| `dfb-template-one-hop-relay` | `dfb-taint-java-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-one-hop-positive.json` | `7284de005c87541e52d283c5657b3f1241e46f272d0b8c25efa3613000082ec3` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-alias-propagation-negative.json` | `b14837a64a3b9e33b58f09025ac3a06dd3ee4267cfcb5faf439e164c3ac8e595` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-alias-propagation-positive.json` | `e7ace736356ec5c4d912591af737224cbb4b2f3e7160b93cd7c7caac80f66489` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-argument-position-negative.json` | `29466379ccaac064ec71a4f553154340e7e47d78b58b9b36e8bf7b8991995cf9` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-argument-position-positive.json` | `48ac17e16446f6e60c5641c983b92035fc657fd8a54df6eb85f1a41bf696c844` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-expression-negative.json` | `12fa003de720f58fceb2cf2c2479204755fd4ab2043bde47e08a3a9662997f7f` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-expression-positive.json` | `9dea810e1c338d2fa7dab122c73da07b1db9a0c8912a4343fb2ed5365fc5dfd8` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-array-element-negative.json` | `9ffee1103465cc9028a789332833bd9a2f82b4505199b5229d5d8e9f6f16a4e3` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-array-element-positive.json` | `7fec3eb77730fd4882c5b2040cbd8beac478fe1f62050dfb736c743d3a697c8d` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-branch-join-negative.json` | `10e0479eca6a1605b3c71f5f5d9442dd56dc46b75b854477d47dcc23a6a1619f` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-branch-join-positive.json` | `08a987d3fbdfba05fb51d1e3ef2100dd24dc4b10eaf024e54db74694b05b26fa` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-call-context-negative.json` | `7238e5e0e099b80ef109ad75e5368270a261192d8cb6d31b0aa94576e536acf6` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-call-context-positive.json` | `3a80af0cfdf1b497bad327cef07baa1ec237c91900d81fad5e084623dd2c7318` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-direct-positive.json` | `514657b69670d1788df89c65af0a16f42b5bf92c27add42bcce4000b062adcf5` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-explicit-negative.json` | `af268f4af07452ea08ec341b6617df004c53f4bb906f6bc488196d5cf742568f` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-exception-catch-negative.json` | `2696632fb4f5d1bf7f147b307ed5a49b9e30d51f5e9f70f01c0c6b8636ff7331` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-exception-catch-positive.json` | `abe820035241af9171dc0ff467d77e2866bb4b32926a16f13070285cf42b1d3b` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-infeasible-branch-negative.json` | `f797009ae8f0736abbb3c0f00682617c8ff21a79ff5b5db59588d32591e2e9a8` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-infeasible-branch-positive.json` | `9a31e3046d3ddce485d4f44eeaee23835de542ce3052aecc2a5a3a72843fbe69` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-local-chain-negative.json` | `d5f29896d78e63b6f7e22a966ce930e4f48a25c71b45032e1258bca5b1ace65c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-local-chain-positive.json` | `d8d3d167bb0de25bda5ea189f8fdb55376af55cb42f86481155af67246e8e0ab` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-local-overwrite-negative.json` | `cbc5cd9f8e1d7b7fdbc961f2227d4adc62ff57e0033025f982312750318923a7` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-local-overwrite-positive.json` | `ed7dd30a7322147d6820304bca443aafdf02152ccb4085d52392a83e8c557828` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-loop-carried-negative.json` | `fab44c9ef0f3329e1e75fa6da3fbae28d9613fac40d94a2618dcbfcb86e5617b` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-loop-carried-positive.json` | `2c286075f54b31d9f5c728ce1dee972430dd47c20e20dc890a67301365690d17` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-object-separation-negative.json` | `6793d88fa560e0848db6d2ec809d3ad39ebc428a08bd0926fd9874f0c4b4d125` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-object-separation-positive.json` | `6104305ee2a38fb31bf6504569fad13454af2542bda7a1dc51852d9f208a036a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-return-relay-one-hop-negative.json` | `be4d3248a6178b277ecf2762e74f336d940695d4c159d832c2b3a940be4e8156` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-return-relay-one-hop-positive.json` | `717bdf160a461a58ce9b3cb9346a2630227bc4a72c5b563f08d690248d851991` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-return-relay-two-hop-negative.json` | `a4fa3258f87cf39bd921703863147d3d2959535641af7dfeefb7e65cb69837d4` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-return-relay-two-hop-positive.json` | `2d1ad67395132416be6a3e7665e6f123f1be8b0c922e2b9757c83be167947461` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-same-object-field-negative.json` | `58439da1a73991d49acc8d4be8151edc1e34e811b02d75abdc93a00a00fc25cd` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-java-same-object-field-positive.json` | `32ff45a757256da6583562541e33ff95af607c985628008b865df1ed0042ce50` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-alias-propagation-negative.json` | `7a0a59e683562b84ddfe2f75c0569c30b487ad10a3bd9d4d880fa7167276ea5f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-javascript-alias-propagation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-alias-propagation-positive.json` | `20fcbc30a659839c47404df28eabcbfe3f70f7009a4724c1039d45e6352b6c54` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-argument-position-negative.json` | `771bd1aa788e0094e9ef1262c2b7bf46e8a232f888d2af565649245061cd1127` |
| `dfb-template-argument-position-separation` | `dfb-taint-javascript-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-argument-position-positive.json` | `c43d3193ce57c96dff77422bccb6bdfe00166afdfba51bfdc3c0419ddbc2bd07` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-expression-negative.json` | `1c05ce43e15626776c0a9568fcad12e3693c92baafabe63b97184e75ea88c4fa` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-javascript-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-expression-positive.json` | `fcf583e52259a97f0f960f93535982fda1fdd1fab6df6f08d278ed981d0be1aa` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-array-element-negative.json` | `52a5830469c1e98da6f4e0be964ebd6d58ae60ae1c96c05f2046bd55dd42e986` |
| `dfb-template-array-element-separation` | `dfb-taint-javascript-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-array-element-positive.json` | `5b6514f668383683300bd0f0851b2d549b8bede0705f905a89fb025de11080ac` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-branch-join-negative.json` | `3b48c121eb0a89480a17eb7834586aa6d3a973ca8e2678461c6e1c91212b691f` |
| `dfb-template-branch-join` | `dfb-taint-javascript-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-branch-join-positive.json` | `8e1aadeff36b9d54ac9d9ba68a1cdb9a89e090fbb8a0a685f0ffb8df629dc254` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-call-context-negative.json` | `c5165b77bb3031d3927a975831ca0c80f5582505ac3bce2af12b1248266fec9f` |
| `dfb-template-call-context-separation` | `dfb-taint-javascript-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-call-context-positive.json` | `d51afe9813301595a8e2fc8cac2a2d5525949972561d457d70852f5a892a77f3` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-direct-negative.json` | `d57234de2e7281c0f0664f96f759f7179f9e4ffc09252a919ab3783eed2dce54` |
| `dfb-template-direct-propagation` | `dfb-taint-javascript-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-direct-positive.json` | `9d95821c1ce2e4ab9f638c868de3b7885faf191f31cb499b09f759cdeaf1fff8` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-exception-catch-negative.json` | `353541b0542c3726cbd0efd56781cb7cd0171a60fa8faece4325938af87aaac6` |
| `dfb-template-exception-catch` | `dfb-taint-javascript-exception-catch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-exception-catch-positive.json` | `05d24f823bb5e9a7538bf1c321f96f1a88b301137885a45363dd9cd32860595d` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-infeasible-branch-negative.json` | `fac79aa0ef912089452f27f3f05e7cd6cf4082785ea0ea7158a0d76ca1cc250e` |
| `dfb-template-infeasible-branch` | `dfb-taint-javascript-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-infeasible-branch-positive.json` | `30e34ba04a8ff4e302a742e6c513d2cbe4dd2e52810f9b61082518129342953e` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-local-chain-negative.json` | `de9715370b8dd7e4bc5de25e8b4ccfbdcdece2f81bf23bf17975ff4c8fc7276c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-javascript-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-local-chain-positive.json` | `6b86fbc3dbf70be7dde091d6147e0ae3449981cce84b8011f843a7651e4ded3d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-local-overwrite-negative.json` | `dfd808261c0e113cd258475452ba12d300186db587644244be83d5db75c259bc` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-javascript-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-local-overwrite-positive.json` | `d478285676b30336050a587a49a5771f1c4bbc57964b6ec319b7867948cfddeb` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-loop-carried-negative.json` | `002541cfe854a39b261ef1bce60f946dd3c1037d922b97154da074802e84a0b6` |
| `dfb-template-loop-carried-kill` | `dfb-taint-javascript-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-loop-carried-positive.json` | `8593c80c3ef2f142aabc1b6a609dadeaaee4c9f77af9baf8daa8c1ed51176d4f` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-object-separation-negative.json` | `2c6643fcb7d3480d52c0c8a688a04dd8c9114d4ab8a7a5a5fbb25d3e9a8c88a7` |
| `dfb-template-object-separation` | `dfb-taint-javascript-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-object-separation-positive.json` | `bb9c4d1b5e126d95a56809d26c33ae0541e52de46bf7727154b970454eb109e8` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-return-relay-one-hop-negative.json` | `232e46f0829f61b18c54015c042fc4d9dfdc2578eb0f2e58f5f5640f1e5afc6e` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-javascript-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-return-relay-one-hop-positive.json` | `251a99e9bf625779dffa74529291c71cb7bcd56b0a357e55e125d78af9356ba2` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-return-relay-two-hop-negative.json` | `f4174f30fd639d6e890e098fff3151fd3bd6fb7fb19f0b9dab1248ad6c1c784d` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-javascript-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-return-relay-two-hop-positive.json` | `4d1018bdaee58b3669923cee05ccb071297b6277cf9a03dcee5a2b651f88df9b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-same-object-field-negative.json` | `e9bc6318dac910c856538832b02521285491e883ccf1c41391eaf4cb62d3949f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-javascript-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-javascript-same-object-field-positive.json` | `5480138241c3c0fff7dba06205aa8146da2ccce18a207659d52062a0fa379dc3` |

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
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-kotlin-direct-negative.json` | `5f638165e09b8e8554d065e1ef3c8b018c17e6abb388131782fe4d535d2a39fb` |
| `dfb-template-direct-propagation` | `dfb-taint-kotlin-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-kotlin-direct-positive.json` | `e51ee13ca746ec8475425998d3ae8ad9e866cb679355170bd059281cc81a6ce9` |

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
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-php-direct-negative.json` | `a008b6cf6ca9ed35b5737929cd6755b31b61529ffd06aca364af58f7c02d7b59` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-php-direct-positive.json` | `5f91f690879c989fd6f0e0b99236589efd01c3a299f15ff692de6453ec2cb8fa` |

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-alias-propagation-negative.json` | `b4712b184bad4ba34b55f92950fce7c4e17bd12a70aba33aecea05d62b80065f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-alias-propagation-positive.json` | `fdaa4c7ba0b38b27e87ccc0431eca00e0f502d7595fa09755b1282819413f518` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-argument-position-negative.json` | `30c3fb7076c714b7e9eb27cd52f96444d1c91d9cca6717b640f17e495042f865` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-argument-position-positive.json` | `1681ee460a456bd28072c504ccf281b644bca0337783bb4eef3380b5e1c50ac5` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-arithmetic-expression-negative.json` | `9f00c71de1be4b7d753cb1ced0695b74d2a01265f88fea6bdcc2a6d32c3c04c1` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-arithmetic-expression-positive.json` | `13a6ca17a01068254e1a8dbb52771f645595b10f044dda2f8ce51ad4bbb4513a` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-array-element-negative.json` | `a12d9cbf3bd39e315acc27ce703c253c45b9cf14d757a1ce7e280c2ccd74e407` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-array-element-positive.json` | `f42461796d876e72e15c3fa66395fadc11b2244f2c07af3175c4aa0633e7e2b1` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-branch-join-negative.json` | `4fa638ae46b5e6b130e44fb523e6d91383536eb067c68288d65e707efbc38780` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-branch-join-positive.json` | `d8f5d6abae8c61a5785508cf0f5e8838dee1d3a96ae7c6799979a26d34d3b0bd` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-call-context-negative.json` | `46ca5357eb72d00d04cc23642e880c907f3f7a0b721ec4dd92de680c0185c824` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-call-context-positive.json` | `ba1b50b8d2a834dec2264fc0222bad13e6b64b591be9080563cfff95da64a225` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-direct-negative.json` | `ecca31a361eeda77625a5070c4e78446dda9aa85ffe92cd0b817463f6396e90b` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-direct-positive.json` | `402e635247bee542bf8fa0d1f74f0392f485ab29d651a81396306ddb19655a3e` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-exception-catch-negative.json` | `c58472ff9bcc1fc65233f4f98eca22c1b7d86e0a70f55e1e4c4439ea2a94c74f` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-exception-catch-positive.json` | `6edd5e62ff6cf10e0bd7f973f123bc70de3e13b10e0173227a4af8e56f5a564e` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-infeasible-branch-negative.json` | `123533f8be72a92fbae15fd03063f6170183980709470eac6e1af746aec397a5` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-infeasible-branch-positive.json` | `8d9681c13172e0fff5ad116249ea5d069df96330f9fdd3f09bffcede47393823` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-local-chain-negative.json` | `2ce6f3414ac60c0fdc4874bfd8a0c507de9f59e061dd1676ffcb57762097dc5e` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-local-chain-positive.json` | `890bc6dee96880a873fd973d23c5980b429cb9e60c071ae1e804a22a6d5fb5f8` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-local-overwrite-negative.json` | `e88ff3f8f2ab8de3be2969db3594a1b4b429503ec7062e0951817cd51f561c6e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-local-overwrite-positive.json` | `3e01efe974c14a3c685f2d5c64f8cce89e8caa1a7276eb543091c21a1511660a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-loop-carried-negative.json` | `bbc99d87172b49e8c212937494b74a1faa87fdaf3685810d526ac2e0d7259c44` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-loop-carried-positive.json` | `1922b1484def679c95f1e8dea7095f5299d9a96b16d4f3d106fdc7560218bf77` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-object-separation-negative.json` | `833c08dc13c2c2c74054733192cb303e09077fa7fc54d0bacca91226afdc8bb2` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-object-separation-positive.json` | `6597b8ffdac83fe62d8ef9db4b6dc438a81936e0a236bb2561ad7ff7388a496f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-return-relay-one-hop-negative.json` | `3e8b8d2fb81ad9984f8380e86675aa08c2b787b4a339221865a530bfb2e16d04` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-return-relay-one-hop-positive.json` | `d07e182ab4ed48607255f29d11df0b6a988170854f3babc85aec3778d6bf5171` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-return-relay-two-hop-negative.json` | `486f4b8a9e3283d956a8a93b22d9d42507ec0a1bd8c89f5e4f551f16dfb9bbeb` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-return-relay-two-hop-positive.json` | `c667556d7d0afec0ad5419baf32f5a2f0d7b2f19d9dc1a6f4c48e25079bb6876` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-same-object-field-negative.json` | `dc113b53f82979944419b95734de421a19d1b67ebb031218477d22c975361ff1` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-python-same-object-field-positive.json` | `c56c15f658950ab1057cfbb5e9b0907adf63335104fbca9e255c06ffcd44000b` |

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
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-ruby-direct-negative.json` | `ad799f4514c5e009dea34b2ea1e25de3a3e7d9d976b1f1ffe83e0a1570d2dd3b` |
| `dfb-template-direct-propagation` | `dfb-taint-ruby-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-ruby-direct-positive.json` | `ff3ab48f3953fbd990da00a959090f69277ff7a96e8d1173ac5f4d9f50ad3602` |

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
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-rust-direct-negative.json` | `6aa6af84471e330cd111866c645a833253e54b762dd6f2b20eb3386a8d3ba362` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-rust-direct-positive.json` | `3758bc9619c174bc5590715bb7b6056819fbb82195211e98db823c5a35c075e2` |

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
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-scala-direct-negative.json` | `7fd4af464a8ff2ad7ef70bf19d22ce25cd6440dd65e876544af09a7d6ca8e04a` |
| `dfb-template-direct-propagation` | `dfb-taint-scala-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-scala-direct-positive.json` | `52169ce4fc8179b0f3fdae6b338bea3727bf17c3e1136529ef54a6e195f74cde` |

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
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-typescript-direct-negative.json` | `ceab0d18c6812ab7a01e0ba235643d008820f7afa42ba37e20fb98661a5ff849` |
| `dfb-template-direct-propagation` | `dfb-taint-typescript-direct-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/bifrost-smoke/dfb-taint-typescript-direct-positive.json` | `d1e32b6aa89f8b7f0371c0fc6b46dbc6d595bc785ff19798b99332f5d9428c29` |
