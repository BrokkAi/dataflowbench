# Scorecard `bifrost-go-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-go-kernel`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `3e8066742eac91518264ef6d3ad8f99d2f6dd7159ca1c3b4114dbf5d324b4fb0`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-go-kernel.json` (`sha256:b9e8c94bd0333c23cee21935de3c78968dda9506634023e19a7aaf144e1aed18`, normalized `sha256:b9e8c94bd0333c23cee21935de3c78968dda9506634023e19a7aaf144e1aed18`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `go`, tier `core`

Outcome coverage: `reached` 18, `not-reached` 18, `inconclusive` 22, `unsupported` 0, `runner-error` 0, total 58. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 12 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 4 | 0 | 0 | 4 | 8 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 7 | 0 | 0 | 7 | 8 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 2 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 2 | 0 | 0 | 2 | 8 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 22 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-negative.json` | `288d3264452021015b7b8ee327a9716ffc90b781b3b8fd90fd7a0075979c206f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-positive.json` | `ab0791411ae68f8b572e90673bfd274f8e49f005c7fcb0cdb0b8be98877d0aa0` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-negative.json` | `5666f7eddaa64f153298644217b8979300b5cae5640c2074ff84b7b263837ed1` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-positive.json` | `1eda6e36a098182593101138b96501340500040fab9c30170adfd8b18c162b4c` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-negative.json` | `87082fca55da0083c8741f604f23ee42af2ad4d507751b1cb91fb50c17245c45` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-positive.json` | `d673dd40bf3a88bb6172a79ce309a652335fa4e9328fc36fb989fddec94b0b84` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-negative.json` | `b86ff3d5da9565c82fdb66f13a27171a411515f9bc0c3501bd9ca4c3b7cd2071` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-positive.json` | `e45746ab0ef1114a33314ca82d9d635fc5de5af121a291136e706543e5c0c04f` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-negative.json` | `98ada52ef10b5e559b1eab7c4ec6615b8096f2b57944bf650609c3b313f64ff9` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-positive.json` | `55db0d314291f4af11eddf0123e39f030d6d2fad10c4f99005b713e75fad1adc` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-negative.json` | `68338faf545f237bb98b0ba6101f791f8aafe1dcd8705dc14a93015c00bd1f10` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-positive.json` | `8027c63a77430c3e86d6fffd6bedb249fad6d3effd987caa39ffc993f6f0b3b3` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-negative.json` | `a3fd157590b4fc336a1f65deb33a2ec01c76184638579820db521c7f42660f57` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-positive.json` | `409b31182d64f194c925ce9a5752f0e640a884cd55e932de518fe64c2d96d664` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-negative.json` | `42e51b3eef48baee2c8b1c4166b0430c92f965a69745eca7f5064d4ed947e6d1` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-positive.json` | `c9358c21a8301fdf21b741a3ae173f4c0e9a2381c3dbb6561ca750510438fbff` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-negative.json` | `1a1faba96c8c276a93ab64d0c49183be53f774e0d0ed77b80b3d4c0c1fcfd382` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-positive.json` | `5ce70bf734ce4ded8f89966b1b2b4d52eb6db57ee6a9168bf16198b11ec42369` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-negative.json` | `6367633c5d95c1c77cbf3112d6277a6d3d100396cc5244b31dc1c5bdb1f909f4` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-positive.json` | `340959da02fb59c2059714f6cb18a5ef58c93828b8f775f38492cab70bb35f21` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-negative.json` | `a43af9368fad443d95a6d3c9c3610e11d98f7050e820096fe8d15e9c201aaa60` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-positive.json` | `5a5a84a705445b75c12dd8b9db27eb1bd0386f9c2a54681953cc2abdda611a47` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-negative.json` | `1b1786283a565a84f2c3c52aa58da8629204b88fb29a2957b9f955447a7d836e` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-positive.json` | `b2614d740417e48c1dbf7258920bdcb6de83d296a9f11acae2f070acc9f3febc` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-negative.json` | `e9a9c231311f927b75784a7a43f8656eed82eb371ac91e473324684418ad0a50` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-positive.json` | `dae64af158a7e78e83670dca1b47d212e90dde4d9981cbee26b7d38eaffd03da` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-negative.json` | `56648ca1f541581d0031fa004b166a435a4870b774817a2b80597a1449e4f088` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-positive.json` | `b3860ad69e08ab994beb09d2e19ccefce8906eb295d805a39680a50c4f20dd91` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-negative.json` | `8d2229f4e9f1fd696e0d79c79759007e362a90c1e005f72de29ce3ea5efcb41a` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-positive.json` | `6adfe18712fc3832e33c458be2cba6e1e4a7e0abd6d28a3ee9a74a235dea8b9e` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-negative.json` | `744800963a8e389a27387b4088dac93e940d0b0907eb45f43beb6f49f6f424bd` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-positive.json` | `2f1f716eec2c4d829c32952e5659e036dc657949267a7dd57f6bf486b597729f` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-negative.json` | `c9ec27f8c62dd213085d81489a51c536f9d0a9465f3bdbb53b5ed49dfd6304cb` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-positive.json` | `fb9fa502de518d347b1d3c64c312aed7a55258dad3121a1a4cb330e72080a0e2` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-negative.json` | `5cd8bf155fac860c3d423c773907675f003a36e88e2bf56da5c8397305234abb` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-positive.json` | `3fc28a5bd9fa07fdb7843345fca2eb349b9d12378974db21927bfdcaa3e47c37` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-negative.json` | `e0c329766fd7ca8899f044829774a6d4576da9182d04ef74b385365501292566` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-positive.json` | `bed06006cee0a0bde301a51905f893448b7f8ab261a7f2b0dde4127b63629fbb` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-negative.json` | `23898049f8fcba24aa6daa6875ca069e10438dbc247b745ad090ecc922128d32` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-positive.json` | `de57dc3870c18cfe26d9ac3e3274ce579e262e602c43d33bcb1da00b0867a0eb` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-negative.json` | `419f08d8fb123931406f90fd43edbb7b63906029a9be8b95a670cc1f9e50fe44` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-positive.json` | `2c4cb5f46d1da1711216c2d3d56c6ab873fb890a51ab6d457906893ebfd86b69` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-negative.json` | `ab7f5b5b38f88d53f324e85289c32fb1480514fe822e3cd4e8b792f243497d8e` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-positive.json` | `59ef4604b4744889e323f933b204cd27d64441fc557f82702cba794726d4525e` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-negative.json` | `d515cf2e30975946ef0bfd7968582398db4ad24cb9e2f460c61d569603d1416e` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-positive.json` | `b273fc163a4567efb988d6bcfc401ed93f5ea2e9ef72a95a16c9b0d5846b7ba5` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-negative.json` | `c4c288323c3e28d5882b9397b855dd0b35c3df5a4bd9678d6b804df8f20c2071` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-positive.json` | `9ecc86c38349910cf25230a1d4ebdae8ee2559540a28fba8a9cd6bfe8db0d120` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-negative.json` | `1b5c9157850775fd08642c7a4a77cb3fb9d97521145b4151efcca7ed9c3ff3cc` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-positive.json` | `5ee46712a12954edef0b7baaea0b22db7b1797088f21f42414b7f7fbe303429e` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-negative.json` | `493808408232f363716022c2c2b6399040bcf28ab12ed25e7ae4af921a4c78ac` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-positive.json` | `b7a97a390e0223284964ad61dd097afa95846d067c1a649f70f3f3e58e328228` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-negative.json` | `228ceb99922dbcc31c1abd91c5b946443367475d01ffa9988525c18c7f376fc8` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-positive.json` | `a6486b246752c514ad2f19c6e8ed404685e4dff61a7358574dbec32226c9fa05` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-negative.json` | `0e6ded32f72c9ebdc4ec2e829184975f02cff3f55a77244a818ea3a4869e6d79` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-positive.json` | `08519ea752d7344219a2dcbd6e48bf06f40e9768af327a0972ac8047be231d7c` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-negative.json` | `5929792366d084979697dbfeb03e36c43992291a263c7c1db224e6148bc05486` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-positive.json` | `413d1c2ae115890441f4cf58593e89e1b2dfaad32fe603917110982b828f9768` |
