# Scorecard `infer-cpp-kernel-taint-taint-benchmark-controlled`

Adapter `infer-cpp-kernel`: `infer` `v1.3.0` (build `infer:v1.3.0 bin-sha256:17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62`, adapter version `0.1.0`, configuration `724dccbb7faddf35386aa12dee397798f30e9d3418aa97566aa5c13a585b57e8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/infer-cpp-kernel.json` (`sha256:fc3b5fd70a89dbe9bd400c3a1f7d8eaf44f461fd02a1f3cf19264ec67cd98199`, normalized `sha256:fc3b5fd70a89dbe9bd400c3a1f7d8eaf44f461fd02a1f3cf19264ec67cd98199`). Generated from freeze manifest `reports/freeze.json` (`sha256:5e57a5ee0dab3929cefa42edce222acbfb0ba0ee34e25e39e9ea882eaa66b724`).

## Language `cpp`, tier `core`

Outcome coverage: `reached` 19, `not-reached` 37, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 4 | 1 | 0 | 5 | 0 | 0 | 0 | 80.0% | 0.0% |
| `dynamic-dispatch` | 2 | 3 | 0 | 5 | 0 | 0 | 0 | 40.0% | 0.0% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 2 | 1 | 0 | 3 | 0 | 0 | 0 | 66.7% | 0.0% |
| `heap-field-sensitivity` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `interprocedural-flow` | 7 | 4 | 0 | 11 | 0 | 0 | 0 | 63.6% | 0.0% |
| `local-flow` | 5 | 3 | 0 | 8 | 0 | 0 | 0 | 62.5% | 0.0% |
| `object-sensitivity` | 4 | 1 | 0 | 5 | 0 | 0 | 0 | 80.0% | 0.0% |
| `path-sensitivity` | 2 | 1 | 0 | 3 | 0 | 0 | 0 | 66.7% | 0.0% |
| `recursion` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 52.9%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-alias-propagation-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-alias-propagation-positive.json` | `5f3feda6dfb406454b0a6fcd3072ca4675309ef497377efc7489f39439c71643` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-argument-position-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-argument-position-positive.json` | `9df3ef8759ee63414e9e2ad59c080569610879ff9599880e0b1276fe57b39aba` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-expression-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-expression-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-array-element-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-array-element-positive.json` | `b1f5dd125a53992e14e4e647d1805dfc4fe15a263617ea71801a46c4e850b671` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-branch-join-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-branch-join-positive.json` | `c46f35bb99d00d25f746c4f5b270a90b4a3f25478718a0d3b47df34723ea6266` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-call-context-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-call-context-positive.json` | `5a59f12b25cf214192bdbd6884ccaab1c04b45cbbc3ab3642dda5d95dd378845` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-anonymous-implementation-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-cpp-anonymous-implementation-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-anonymous-implementation-positive.json` | `c86e22f2d6a5e6aaf69d5709720fa76edf1a949b6ec3c138b769b01e2b30d456` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-callback-registration-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-callback-registration` | `dfb-taint-cpp-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-callback-registration-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-closure-capture-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-closure-capture` | `dfb-taint-cpp-closure-capture-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-closure-capture-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-computed-property-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-computed-property` | `dfb-taint-cpp-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-computed-property-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-context-pair-depth2-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-cpp-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-context-pair-depth2-positive.json` | `182b4184152288c4cbfbf135336d27688d615ab24c684667c9064eda473e2001` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-deep-relay-chain-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-cpp-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-deep-relay-chain-positive.json` | `31e30c4fe24879ed994609b2a64dc78023614a25f7d19bb6810e15129dde9ef3` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-dispatch-table-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-cpp-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-dispatch-table-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-element-object-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-element-object` | `dfb-taint-cpp-element-object-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-element-object-positive.json` | `b8797bb6042008bf10f1f08924767254ccbbb385d2d32b7b745ef74897b75ec7` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-function-field-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-function-field` | `dfb-taint-cpp-function-field-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-function-field-positive.json` | `d50082fe205e46d50fb49e163a9bd2bb5ff0d102e7a8813ee8a21dbff47cf531` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-map-iteration-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-map-iteration` | `dfb-taint-cpp-map-iteration-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-map-iteration-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-nested-access-path-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-cpp-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-nested-access-path-positive.json` | `daf9868da69bba5cecf95fd5f3c110d44a38a904c1e66165a789c33702436310` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-recursive-carry-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-cpp-recursive-carry-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-recursive-carry-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-direct-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-direct-positive.json` | `fff2b7fd04ed65f2afa4e82fc9e092eb0dd331a59b1095f248bcd8eda129d512` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-exception-catch-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-exception-catch-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-infeasible-branch-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-infeasible-branch-positive.json` | `9ce5615a495932c4a55614dd7077f9f430b984ea93169075bed70c7cb45762c1` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-local-chain-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-local-chain-positive.json` | `6937f52fc357678cb3e2207045037d7fbd7f7c46c6a67637f5432cd3e5ef6f17` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-local-overwrite-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-local-overwrite-positive.json` | `6b5c2d5a3b76e0d938208783c262eefc29fc6a70eca68ef179247a00e6642ef6` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-loop-carried-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-loop-carried-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-object-separation-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-object-separation-positive.json` | `6bae753b4ce9325ddbef1a17922f2aafee84a56c4bc91184e79b05c6da7b3e29` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-positive.json` | `7211ac57cbcd92d28e5f4b8b5b78e7a635ed97f4e9b54a77d521b78a485cfc77` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-positive.json` | `505b08590b549b75129f01c4cd7285d9164a8317d534d2ad35fb3e4988854424` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-same-object-field-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/infer-cpp-kernel/dfb-taint-cpp-same-object-field-positive.json` | `d7025b6fa95ba03cdf9e8e6fac96ab037b51201647886d9e5d8535a599e44711` |
