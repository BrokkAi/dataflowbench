# Scorecard `bifrost-c-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-c-kernel`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-c-kernel.json` (`sha256:916c781a272130139cf8ef04801b6d00d730ae6577e84db9826f196f1201daef`, normalized `sha256:916c781a272130139cf8ef04801b6d00d730ae6577e84db9826f196f1201daef`). Generated from freeze manifest `reports/freeze.json` (`sha256:e0b86ebdd570afed63f62ec8fc6d49a2ca2e0afe3c3f288b904de4ddbacdd113`).

## Language `c`, tier `core`

Outcome coverage: `reached` 20, `not-reached` 20, `inconclusive` 8, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 2 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 6 | 0 | 0 | 6 | 4 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 6 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 8 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `04c1abefd2925dd2a3988686d764e3efde585b84a0fcdafcea8850d2d035bd5d` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `52d68e747b5c7a8f79ee6a9ee31f77e0230973d498f35de7db2d233df6801939` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-negative.json` | `c5742eeb362953e7a897d46f1f98babcd062b2f2b701f608bce7747a674a7106` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-positive.json` | `2e592c5b83cdb6e14edfeddfde473d83090ca11fb921bfc78675cfeb9fe45394` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-negative.json` | `11eadccf85a99b7b355e0172c9c7167aef0fe05e67f6a2be1fb584ffdce6af19` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-positive.json` | `304622f2ea2e04163157c14e1cc3d778785cd13f8846059e3869211a28be84cf` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-negative.json` | `0672eee0991ea4ce14aab2e60a9fd3f69f8029ca38eb7228e8c638807680fd05` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-positive.json` | `f77f05d7bee5087d6daed53ea6a5649e87743887252071ee4222b6f9e5528b7b` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-negative.json` | `a0d14e92e8e3bb61a486ebe4de7768917a08f7990db5fd2d7f8f450d774d8aee` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-positive.json` | `244478424dcd19859dbcc0720e405e0c6657c2c626e242eaf2dcf0a645f31151` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-negative.json` | `5d640e0790d52a2dbf3a38322ca270d934e06bb1ef3c18b50f35265beb172e64` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-positive.json` | `da7dc5ae8dd0bbdb0078d76725d41133257605ab8bff79066bf32ceda892c5c6` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-negative.json` | `084d1a3b9d8d6b0128298eb5dfbdec035ff50efad5ef8962f7dc8d913a94ffd6` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-positive.json` | `3da7dde5dadf2629581672f6365eb8f6779944e4e28d576b5c2215158757ea0b` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-negative.json` | `a7dbf1a2876f18f76fe754c959523cc3da800eba97af8490b7ddec3e23d12595` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-positive.json` | `5e6f754fc4fcebb8389c871b51a298f9fd6606603526112804f9d54aae10af1a` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-negative.json` | `48780052cec0444000177d6aeb570a3dfe6a8041d648618a462113f183ea7d67` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-positive.json` | `2d1fef015a794ba779e1d951309a76f7428f6f2dd8f5d46452a22f477df58aa3` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-negative.json` | `57c6cbbd40d83d57c109145b8e6bfff5bf45e98451d94ad8c72f8bdb49d2e8e3` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-positive.json` | `eb3018b7d6353a33f9349d104c9b96529ed6e505b41dfc059f259aa31409ded4` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-negative.json` | `7a96092020f851b18adc935fbef9bb7975cc913a5efa1f1fef47ca3cd806657c` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-positive.json` | `8de9730676f69b259768abc5da467ab49789b74c80d76092782a1e4ebac432aa` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-negative.json` | `269c81505c1c8686f4aa40870ff17875db2fb06130ee87ac9170c7a01c186ff8` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-positive.json` | `fe20049fe5419038f1ea38de9fbd64b621bcde6869dbce3afe362de27a0f1b89` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-negative.json` | `4d99d769502c6c12a911c82c75d64ada1b9f5d571304ceb06268a92db0844d6b` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-positive.json` | `f17b430ce94e288ccb4673114bea777738450b0cb47765b759b0d1b28492b921` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-negative.json` | `f46dbf0bb6df7560fe529fdce1fe266295c8c1eb3ce83310c4c09cfbd925f21a` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-positive.json` | `274c5d0349cce5425e68eff28d8e056fcbe9f6393b311e2d2459643de1e2d993` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-negative.json` | `860cc6d479b89ed5faddc064ece38547cda142e676629e201fe81f6a22b0f5b7` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-positive.json` | `62100fc7dd6a425e8b460742f5d5bfd69aff23824b0ce2e48eb4af5b68a2493b` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-negative.json` | `f250fbf2760eb7ec94784a348c906e94fab67e1ca9f2f29fd81805bb448f499e` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-positive.json` | `4b2493d7f09ba4ac2f0d85a07f0e67ceca9ca67815f6a0fc2eb4bc2f19fc6dab` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `1c072efb5fd3095fc4532516b641b5cb7c79f191743396166c8c54aaccc1a0eb` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `7e10ddac8ae78a46a0a9c8bc365c87e62dd33db7770e55733bdf3024a2dcbacb` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-negative.json` | `0f27b3553d8d227b1551842c47e8abab7b01eec6553f1d5370236b237d8ad97c` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-positive.json` | `7a460bc3be67eeeea4e0edffc313f70b1d4dc869e173925645c9b29dec2407b0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `3c90da0a6875a01a77dd6aa53a2cac41b2eea24ca5a95b18c7f1d2fd6bb54cd4` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `859e3f6f0d66a4c6d635a0cf2041a4b77c18a5d86f54638b4056dac1177b3417` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-negative.json` | `8994aeb5290875e67336baa82c4949c06dd4297991100b20a5ebc307d930fff5` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-positive.json` | `0246fa1563f7697358d626a5ff0db36ec95867f69bd0500283adfd86a31ed39e` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-negative.json` | `8c8a6b1d459f5cb094647a1e3bcbc10c781f4000ba581c22e04475a551af3ac0` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-positive.json` | `1d8a7c89e27004ed3879a692454c9f4557ce41e75ad45bd4757a68de6063eda0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `c435e79ead4c4197d1dd310cdb49379482d9a1e4fb2aabd9510c634542bc2d77` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `2d85639a093171231a001c84a24ebce26dad706682d140d86e9e40f54b845743` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `1bfd373917df2c9b6fe6f980dca3e7d7075f5d32f9e3fbd7158a8adceb0f61b5` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `d567aba4a5a282d7073b600c965022757ee64709eb019928bd0580aa4e62403a` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-negative.json` | `59f6f650abb7542bb6eafd5838622970d744b98f10c12f0f7e99827d56579dc2` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-positive.json` | `5934b0e0ce22cb8334853db2d1010b4c644702077837e652e051dc197b65e201` |

## Language `c`, tier `language-extension`

Outcome coverage: `reached` 1, `not-reached` 0, `inconclusive` 1, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 1 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-error-code-return-positive.json` | `9a05dded075ebe68efc18ff24a7d570bbb70861e841c54df625af7b9fb982585` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-goto-cleanup-positive.json` | `0ad0385cd9d5d6909a8bd1f015bb4570a97ef5ac4772959f212208168d56b399` |
