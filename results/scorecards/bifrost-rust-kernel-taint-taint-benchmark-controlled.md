# Scorecard `bifrost-rust-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-rust-kernel`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `36412c558da0975fe3af755c8de8628b735762f20680588b1b2ac87cfc206298`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-rust-kernel.json` (`sha256:54cfc84db71e56e5032e965f0bd5911ea43c776422559679f7d5550c2da08a8e`, normalized `sha256:54cfc84db71e56e5032e965f0bd5911ea43c776422559679f7d5550c2da08a8e`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 19, `not-reached` 19, `inconclusive` 16, `unsupported` 0, `runner-error` 0, total 54. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 5 | 0 | 0 | 5 | 6 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 6 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 6 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 16 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-negative.json` | `7dcafd1115560c471ca31308904d16468e655efaf8b969bf65d162b8bd0c0fee` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-alias-propagation-positive.json` | `be9516ea6380198b54473283ba803864e254ead79df1d4dff02de7533e114993` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-negative.json` | `cf8f01980bb5e60150009ac88712aaf709d3dfaffe643ec94a55bada1f330799` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-argument-position-positive.json` | `7e9acf1f0b86d3d40b557f3a8c0363ae580807c521707f0a525bbdf7abeab736` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-negative.json` | `a05f0571e3137bcf6be311b09ea6127ad1af81ece150924e240ba311f459deb8` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-expression-positive.json` | `97d212f3166978e3e0f5d68ffd88f9644e8a78f42041ef85b59b7a607975e889` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-negative.json` | `0ef244bda4778da45e006ce3e6e548886c03bb1a85ad9e0cd45ba91494eb25eb` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-array-element-positive.json` | `9d9130c3f43f7f9482983e586b8ac9df49d08138cfae491a8fe1f516fd353621` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-negative.json` | `77682c95e6cf88b6312c2a088d999c34499d14a562f88c1d73fcc6e99af38e99` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-branch-join-positive.json` | `165b76026fb97dce5f4078974ebd09641109f9073dcfd42b76dcc49282e013f5` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-negative.json` | `fe33f33f7d9ef17cccd643ce36e5bef06ec761f90bb78f651206215cee7ec8c1` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-call-context-positive.json` | `be477c21a03a6f1b871784f9d9df2700f44781cb70922a93ffbdb92e63ec6df1` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.json` | `9b2489900ab83a8d276bd5590e1f388fa65b1ff9cb866830491977d86262a320` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.json` | `6d91594bcdf0ea9ea18a5fbf68376e26a6b91a357d550fa473054ec789e1a37d` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-negative.json` | `faa26d6a8974ed2f29d2d6d165adc7f3460c28719721174efe0884fec820b945` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-callback-registration-positive.json` | `117f51ec5bec214478a19ad930a8860436cca4795131a82ca0b2ffa773f48f37` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-negative.json` | `b2ad343b307f6ac8de2d0cee63a420fd6a9ec58f41d30324f2de3252edc0f843` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-closure-capture-positive.json` | `55a08fca8229718c3b53ed19adf2cdd784ebd305843741dc9578e6ecf05abec8` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-negative.json` | `cfa810fa37ade44aac417011033cb6881116713353ad19fc30c59b503ed07ca7` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-computed-property-positive.json` | `fc4c192b72d39c0779b323ac7b01e86ff46e662852122155026519dc7dcc9e41` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.json` | `29dded097343a1bf4cd044840441e8cf58558f5934fdd65407f1f2ef1ce07649` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.json` | `f1620ec938963157abc5bed66e870ba256e6b827241379661e134f7df5faa3f1` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.json` | `ae4f915e076199c2028916490eb1cad92eaef8b220ddbcbdb226310f58f050e6` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.json` | `a32611f4eceb6b19f781eee4d04f26d453bc0c7e5f047e27db31d7a5833fb65f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-negative.json` | `0c074170e80a7784c9326fb706fc94f4f2dd3842313c672e8159e97dfcbe6a7f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-dispatch-table-positive.json` | `ffe649d6239a34b358ffc42fd0227dbee7c0ed555a057e77b54575d26e305971` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-negative.json` | `34399224a0cc2276a3aa523b62bdaa39e2e7bd3909a2601138eb204aed597251` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-element-object-positive.json` | `4eebf02d5b20e1f7357733fb789ba17df1bb1d4c38922b99e53e5619a629c4e1` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-negative.json` | `f8ab3e531b07d3693743c3aeaa014edeb8d064bd93691fde1976c4c168ad5c14` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-function-field-positive.json` | `1b505d1415fcc3d80b9c1e76241c1327da87b5bb992584f35bda240eaae06ce9` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-negative.json` | `400b0436db92b79422bcc037228582298a8dbc3c1fa0ceed05f08f60fb0e4aca` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-map-iteration-positive.json` | `28a53bca4790fd53a8bf4dfcd8d0de85de35fef011d42ffb9938d824f0d65fb3` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-negative.json` | `a4eca6bbc7ba4ff5b709645515f7049ae69ec6a5b3106fbdb66d92fec8080b74` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-nested-access-path-positive.json` | `18bed63e9f80f0ea4edca12138f88037d9d85b2c265d4781b44a7b3beda6ae43` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-negative.json` | `1d37af9ae84ab2393842619e7a50e023529b4f65d411a5ad41c4ea48a8a5465b` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-recursive-carry-positive.json` | `a3c92708aae2a5013477d119ec89391eeb8c185e8fcfec2c3aec344654582f4b` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-negative.json` | `1660d3719db9faf738005672fff67d2ddd132a410c540590c7b621c3a42cce72` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-direct-positive.json` | `61e1b1d6f7e2a16030717a61657036b6ec7492a6ec39c6efaf2552f4855c1901` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-negative.json` | `4a0a673741e8026639010cade4866fffde49f89a518f252b68f69f405bb50740` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-infeasible-branch-positive.json` | `cfababc55620d3273c3cc8349bb8a6795c2c4b3c3a6f0881c8b3371eb75a745f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-negative.json` | `eb33eca8b1abe2077b5d79151ac374770409473a1d3af771c94aeadc1fdd5d49` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-chain-positive.json` | `21d008e8adaf47c7e5b92c859de52603cd11a207918c81c93ab9504e50856469` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-negative.json` | `cd86c55330f14f9e3922e24302027c921f9f1207ad9c855d6bc0417de1a5feff` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-local-overwrite-positive.json` | `86dd30752cb5669f3b689e3c19b59ef05ee07a2cc7aa5ec6be68840e7c94023a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-negative.json` | `6ff56d8a17f0b53eabae8f05eac2af141a552318902f3766d3bd8c36ffffce57` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-loop-carried-positive.json` | `b4caabc7b2d43f5efb01b1f2c04d939af12d5164fa71f93a4cfdb50b2a10053d` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-negative.json` | `d659ec48b806fd9dc5bd4fd5455af25cbf22d11decb1a133e3b3912c2db40966` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-object-separation-positive.json` | `4ed50b4933b0b86d827a1b130e3047f0b1e2b2ad1407b979013a5b1a59715064` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.json` | `09f66ba5ea0ba300736b1d24901ec10e87e06938b5372f3f8f95e8e7f218f99f` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.json` | `67bfa8c31f04c9942d9748a48dcc12e9e3f7468f087c8e6154fb7fdc7fea4387` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.json` | `25f1f13ff89f7d640db11aa41f7f49065e934f40a263bfb4228efbb3bfad4722` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.json` | `5e74cdc625039ae22da68766072921c6bb6304523f75858232f7982da8df5fc9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-negative.json` | `7589003a04828f54e2a80595c394bc136d3d2d5922f1f82b9a4a5a3907d68c8c` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-same-object-field-positive.json` | `d453a82d7584a940e9a2b4388e12c774ad2cb877f2774297f118b8bdfdb28598` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 2, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 2 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-negative.json` | `72ec8a31a7dbf434d6c9ff9bccd49d6b94bf011fc02f4032a0da720d335accdc` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-rust-kernel/dfb-taint-rust-result-error-propagation-positive.json` | `0b1fd57967847cccf08ce9f7bf3ac786cc7e72cc8aa66b69a2a990538531d21b` |
