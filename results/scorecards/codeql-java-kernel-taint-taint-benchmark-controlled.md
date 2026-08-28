# Scorecard `codeql-java-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-java-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `eedf28b140e6aaf2c27cac6369ee552803cbc7b7674abd70583e3e962e1ef8b6`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-kernel.json` (`sha256:f13a11290939e21db527db660bf76408ec73315a3f2f1f7a9d84fd53b82c19f3`, normalized `sha256:f13a11290939e21db527db660bf76408ec73315a3f2f1f7a9d84fd53b82c19f3`). Generated from freeze manifest `reports/freeze.json` (`sha256:43a34341ca3f818f55878bb23562da03b8fc4b1fc0c83f47b954eb22ec3f41e4`).

## Language `java`, tier `core`

Outcome coverage: `reached` 29, `not-reached` 29, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 58. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 5 | 0 | 1 | 4 | 0 | 0 | 0 | 100.0% | 20.0% |
| `dynamic-dispatch` | 5 | 2 | 2 | 5 | 0 | 0 | 0 | 71.4% | 28.6% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 7 | 3 | 3 | 7 | 0 | 0 | 0 | 70.0% | 30.0% |
| `interprocedural-flow` | 9 | 0 | 0 | 9 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 6 | 2 | 1 | 7 | 0 | 0 | 0 | 75.0% | 12.5% |
| `object-sensitivity` | 4 | 1 | 2 | 3 | 0 | 0 | 0 | 80.0% | 40.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 79.6%, FPR 19.8%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-negative.sarif.json` | `2d2894c9c003b2379e19b6eeb19440cb510c057bc2d421537f0ef2fad309d937` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-java-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-alias-propagation-positive.sarif.json` | `bfb6cf3670e3d5e3f0b462dd2bb141ea30c73a9ace04362f6951ba97d59ea31a` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-argument-position-negative.sarif.json` | `3ef2daab97b359ff9ab084d3f3c898e0c2495253aedb327eb716e7acbd24cb74` |
| `dfb-template-argument-position-separation` | `dfb-taint-java-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-argument-position-positive.sarif.json` | `70260ad693556f4aa1f8c12cd98461beb9613caa54c1cf45600bda94ce982dcd` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-expression-negative.sarif.json` | `e59186e35d96f676bf980d504ee65517fb0073032b2f1efc100d7e548d796246` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-java-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-expression-positive.sarif.json` | `a2d0e66f5217b18740e841414a62fa63ee84103e735c67e9af483062425e524a` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-array-element-negative.sarif.json` | `1afe91bb56cb6e647b5dfd4f2e2cdc32cce36b880256a92abd352168a96c6ded` |
| `dfb-template-array-element-separation` | `dfb-taint-java-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-array-element-positive.sarif.json` | `987c675af2fb010e151936bdbf47702519b70fd631624e7a2acab3a617a72f0c` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-branch-join-negative.sarif.json` | `175fc683185a193f77225fafa3cf945587a0fab7a089ba4ad65ff2d2afe93491` |
| `dfb-template-branch-join` | `dfb-taint-java-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-branch-join-positive.sarif.json` | `e16e945c192d629cb09be1a6133f10ac9b5516d89ff4c5cb567915a6695df12a` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-call-context-negative.sarif.json` | `f9c60d04262b6efb2fb7a844357f5ef1fc236ecc6ae690c4a98a3f1499cc5774` |
| `dfb-template-call-context-separation` | `dfb-taint-java-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-call-context-positive.sarif.json` | `d2b026ac3b17c0f2bcc90b1d4b27ed12dac4581d761db1a88cabb79a5b2fcfd8` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-negative.sarif.json` | `6bd3131be242fc23fda5ccf9b3a2fe706bf496e848d5d10c10d1445d5b68d9cc` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-java-anonymous-implementation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-anonymous-implementation-positive.sarif.json` | `c10088711b757d2571d65d34bcd4edf9a45124ea1b77d87c5959d228d8a019aa` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-callback-registration-negative.sarif.json` | `a292f9ed794d54eccf46437c8fedafdb3265fdc15e4007ae364e1385417bc55f` |
| `dfb-template-chal-callback-registration` | `dfb-taint-java-callback-registration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-callback-registration-positive.sarif.json` | `a7aca84b87ca002603f441e3695ccfd291b6712b9b1246a479c3f809c0e52b7b` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-closure-capture-negative.sarif.json` | `ad9b2328e20085e7cbfab6f7305ef7cc622441e29b6b25f732b0a52b72f5aeba` |
| `dfb-template-chal-closure-capture` | `dfb-taint-java-closure-capture-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-closure-capture-positive.sarif.json` | `099b9e13ac52164768088566dd643a8c8f747d7b600f8c66c3978133fa721e53` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-computed-property-negative.sarif.json` | `b57b6f240e678eb1004db55b9a8f5871300a2bfde5e5a54a5bc9d35771c2ddb9` |
| `dfb-template-chal-computed-property` | `dfb-taint-java-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-computed-property-positive.sarif.json` | `4a10051b0c76460acc0b2da78ca033aded792229d803d13c19dc863c3f3f3f88` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-negative.sarif.json` | `55afdb269b78e3d0a49f8400175351dc74b66ce85c5d837cc25f60024bcb1e40` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-java-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-context-pair-depth2-positive.sarif.json` | `caf44e1dc995a3f4627ad9d099da12d6dbf700d6dacb82b2ce4dc94891fcf141` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-negative.sarif.json` | `df2bcda81bea02be81410d4026c5f75f305598e069e19c4c96111c2ef4c769ab` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-java-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-deep-relay-chain-positive.sarif.json` | `7a4107662b1e7e4a43b1b00403d05df838d5e32c897fb6729c094043a3b4d582` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-negative.sarif.json` | `a8af36a32255b284dc10d9a3d3e5c959707ccadf3ea832ebc9e0b9ccf156f63f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-java-dispatch-table-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-dispatch-table-positive.sarif.json` | `99d8b911822937fd3854e5bb2cf782131d21b09d2ea5307f39330715147d81f7` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-element-object-negative.sarif.json` | `2c0cfc928bfa8317b39b77ef3c525898cfa9f5af1e8ff26980cb137c81cc0fa6` |
| `dfb-template-chal-element-object` | `dfb-taint-java-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-element-object-positive.sarif.json` | `83518a49b14fe547efab7659516c883d396d44808572273d959f8cd97409f077` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-function-field-negative.sarif.json` | `6601aa4a4f0924a27d292dae2af843cdb5552d1cc6cf28b98516690c6a03dbad` |
| `dfb-template-chal-function-field` | `dfb-taint-java-function-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-function-field-positive.sarif.json` | `15100ab61116cd9f52ff2d0f412cef09bb74fcc79af9b17cfe35954dd69b8d51` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-map-iteration-negative.sarif.json` | `8d9e0812035a7bbf55efe7c76c72ef590d0ca3c30877ad4871daa0aa292dba10` |
| `dfb-template-chal-map-iteration` | `dfb-taint-java-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-map-iteration-positive.sarif.json` | `674f8435505adfe8fa35846c86f2294e803375346b15d4102c702bbd820325ee` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-nested-access-path-negative.sarif.json` | `65a1b85036f7bd67d4441e9138f56db16e60dd907e0062baf706ea16579d41dc` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-java-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-nested-access-path-positive.sarif.json` | `12c97e71c0fcc0a8a23303c8870dcb7b3dca0186f635f377d0bd887a2d1c4d93` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-recursive-carry-negative.sarif.json` | `10825c0b0625f32a3fe4af8dddbcbbad1240b2ae6316da8f6d07274242844da2` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-java-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-recursive-carry-positive.sarif.json` | `0a67a13150d6aa8ef7a7eb9563e99f2cf1b3c6887e1f0a693e50fa98ec5a2745` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-negative.sarif.json` | `d7cfae2b52a4c770bd16817bcbf8ee05a7e477e08c2affa5997ec3929115c192` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-java-reflective-invocation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-reflective-invocation-positive.sarif.json` | `0310981f43bde075a12d28d117748fedadb5605fbb9c56079fc4317bdb527065` |
| `dfb-template-direct-propagation` | `dfb-taint-java-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-direct-positive.sarif.json` | `2953a109e446b76c73e56f1bff92841c233770d9e54ffdfbda04e54c18476289` |
| `dfb-template-direct-propagation` | `dfb-taint-java-explicit-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-explicit-negative.sarif.json` | `5683e2b17c0adeb14a44bffc6a0ec27fa145d1d27f8fe02a715c2c7dcd655497` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-negative.sarif.json` | `46f4ffc822585acf74a3a29c5ec6c225e99ec743cc0b19eff81caf5411a884d2` |
| `dfb-template-exception-catch` | `dfb-taint-java-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql/dfb-taint-java-exception-catch-positive.sarif.json` | `c08acbe93165ec965ebb32a0df9b8e9ad9bd74b1508ef1b49f5a038b599354d8` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-infeasible-branch-negative.sarif.json` | `033151e9e3a56b675c3cb22fcb2cf7e5dcf6b859ddf37e31739f5db5e78dc957` |
| `dfb-template-infeasible-branch` | `dfb-taint-java-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-infeasible-branch-positive.sarif.json` | `2cb59741ff3289454fc8585899cd8e93e4a2213ab0b9fc4db3792e2b2b724744` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-chain-negative.sarif.json` | `4b6daf6840b847a15515eff8a546bf26a7bd3197c198f6f41576d196253faad2` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-java-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-chain-positive.sarif.json` | `cf3efd319b34e548c4ec79ebc25f5e1848f0bf1b7456eb27e14a10d3f46d553d` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-local-overwrite-negative.sarif.json` | `e0721dff59de11256eb0a10b1466f41b4c1fd4d8d8722e8c7801bb5bd8a3fca0` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-java-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-local-overwrite-positive.sarif.json` | `cad6490d7263b3f5d29a650efc9125665d3c12fdf2e2d530f5feeeb4ee7ea0d9` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-negative.sarif.json` | `785e85710f7de7987958b62546f643a600744598a1efd38284f292b1b019c30a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-java-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-loop-carried-positive.sarif.json` | `e17745434d1438898b7401ea17e040549762e5234a15309dd26c9d9b8d7f1f85` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-object-separation-negative.sarif.json` | `3f978a00207a879011b0d7d47549c5d601948073a3b7636233a0ebc6f7ae8e2f` |
| `dfb-template-object-separation` | `dfb-taint-java-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-object-separation-positive.sarif.json` | `e8ae509e0cf5a8b0cb5fbc9ae816dafc49e18f1cc96b6e1aadc2ab9f99c93bbe` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-negative.sarif.json` | `c24474a7f644d6739bcd74508dbbc0f041dfc217527ed35ab76deb042649e379` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-java-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-one-hop-positive.sarif.json` | `21aae09a29bd488ab3a96e03ae3e7eb2c77e56bbd9824d7f233b74202fc37387` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-negative.sarif.json` | `3e1cdda36156cc054e08f51b2fefc4b719c0b089d956c7fcbb66dbd5ea88132a` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-java-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-return-relay-two-hop-positive.sarif.json` | `8bde60b3d8c5c777bcf6f755427498402c30f205bfd44280d8b3f61937ae368b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql/dfb-taint-java-same-object-field-negative.sarif.json` | `357dfffc0a385197e526f2ceff2f378fee7932b2b9c072c514c61de8b3ec3107` |
| `dfb-template-same-object-field-separation` | `dfb-taint-java-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql/dfb-taint-java-same-object-field-positive.sarif.json` | `6e99b2e5de0c247dd44d1892863d7c6e36ae4342be739170adca287e868649ce` |
