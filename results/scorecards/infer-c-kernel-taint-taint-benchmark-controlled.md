# Scorecard `infer-c-kernel-taint-taint-benchmark-controlled`

Adapter `infer-c-kernel`: `infer` `v1.3.0` (build `infer:v1.3.0 bin-sha256:17ed4818dadda60124e083a1e82124f104092e70c5e6d764551581a375eabf62`, adapter version `0.1.0`, configuration `724dccbb7faddf35386aa12dee397798f30e9d3418aa97566aa5c13a585b57e8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/infer-c-kernel.json` (`sha256:35a5f9de818f815fb4b682643a3f0f512784043ac0962c4c6e30e05abe19110c`, normalized `sha256:35a5f9de818f815fb4b682643a3f0f512784043ac0962c4c6e30e05abe19110c`). Generated from freeze manifest `reports/freeze.json` (`sha256:3228af686d09f8666989368483bef375bb28b94025b55e31eaa7a0bdd29506ee`).

## Language `c`, tier `core`

Outcome coverage: `reached` 21, `not-reached` 27, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 4 | 0 | 1 | 3 | 0 | 0 | 0 | 100.0% | 25.0% |
| `dynamic-dispatch` | 2 | 1 | 1 | 2 | 0 | 0 | 0 | 66.7% | 33.3% |
| `flow-sensitivity` | 2 | 1 | 0 | 3 | 0 | 0 | 0 | 66.7% | 0.0% |
| `heap-field-sensitivity` | 8 | 0 | 0 | 8 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 8 | 2 | 1 | 9 | 0 | 0 | 0 | 80.0% | 10.0% |
| `local-flow` | 5 | 2 | 0 | 7 | 0 | 0 | 0 | 71.4% | 0.0% |
| `object-sensitivity` | 5 | 0 | 0 | 5 | 0 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 2 | 1 | 0 | 3 | 0 | 0 | 0 | 66.7% | 0.0% |
| `recursion` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 72.4%, FPR 7.6%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `736d6511eb6b1c0ac3604c732084a5a141670acbd14351200f13a38d921eeb27` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-argument-position-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-argument-position-positive.json` | `69a9663fe29dde98ca55dce124a267940de794cc530561dc36dcc8620ea144b7` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-expression-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-c-kernel/dfb-taint-c-expression-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-array-element-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-array-element-positive.json` | `e3e44e05ca6e041e64f0c54f6a512e10d77e7bad1cb962e2577edd243c456f34` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-branch-join-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-branch-join-positive.json` | `f8215e270821517f562111c98ac06a46f4aade64a207a2d9df8c2edd160a54c6` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-call-context-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-call-context-positive.json` | `cfb09d2331e0ac041a8e47ade970587bdecda2874bfaf0f2ce2259dc8e0ca950` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-callback-registration-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-c-kernel/dfb-taint-c-callback-registration-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-context-pair-depth2-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-context-pair-depth2-positive.json` | `04d85d1461fbfc574460a015edc422d5c3a70eaad14923c3e44602c888d21ca8` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-deep-relay-chain-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-deep-relay-chain-positive.json` | `ec6dd5159ac352504cc2f079405146d30609392dfb01798fe60f45ebe8533170` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `reached` | false-positive | `reports/raw/infer-c-kernel/dfb-taint-c-dispatch-table-negative.json` | `14f55897a26873086305b8a663e55f5bb445610c1b5b357936390f997fe20289` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-dispatch-table-positive.json` | `6eea20fdb5a69dd786bdddc3b5d132792f58feeeaad48e5480c62987dd7629a4` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-element-object-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-element-object-positive.json` | `abf8c42641ed2b138231bdc8dd6d319b6fd387191778e17398cbf19e41667672` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-function-field-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-function-field-positive.json` | `75db72185d8dfab64e78d6e5aab0d94bb538cdf22a2cc1abdd5ea04359182575` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-map-iteration-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-map-iteration-positive.json` | `055631f5438eb198ffcb36597f80b3caf62585d81ced352e91a629121780621b` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-nested-access-path-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-nested-access-path-positive.json` | `9bf111ba7e40d732fe076500dfdb789234bcf149ff0c03017789df4746ed4b87` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-recursive-carry-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-c-kernel/dfb-taint-c-recursive-carry-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-direct-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-direct-positive.json` | `72187de570b36757c0fdfe035f93c5c48ae50c3c92912859310adc9e62526781` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `0f29ddf90cfb343702d8f5a4c6bccbee3fe5cb5ba5acf79095a7533d8ea52cf2` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-local-chain-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-local-chain-positive.json` | `5416b45826b5c2eae80f33451dc23552b3c089aafb3ef01ebc413ea022e22642` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `30b885b325b87d1bf3c63d20cef5061ec0df131de954b18c3cb27cc775793ef4` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-loop-carried-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `not-reached` | false-negative | `reports/raw/infer-c-kernel/dfb-taint-c-loop-carried-positive.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-object-separation-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-object-separation-positive.json` | `13c5fdcde78cb767a55e8bb9726442a70be120c28b4e6ea7e0d1fafc03ebc3ca` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `1acdd9fcc2b064dcc5967063d25d3e7a2c1e54e592b7163a8f9459a943cea8bc` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `1e8e62447750b86062a437e50735168df521dc5e2f3de9e79b072266c9fddc04` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/infer-c-kernel/dfb-taint-c-same-object-field-negative.json` | `49d8adf951f538b74d10e1909a986ca4e62156e081b048aec3b5aa13e89d0811` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/infer-c-kernel/dfb-taint-c-same-object-field-positive.json` | `d7592d7bd3455d8554d78d6ff8e58666b4299c968a337bdb8c8797f4f3dc1f7d` |
