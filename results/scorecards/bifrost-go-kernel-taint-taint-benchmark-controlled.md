# Scorecard `bifrost-go-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-go-kernel`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `3e8066742eac91518264ef6d3ad8f99d2f6dd7159ca1c3b4114dbf5d324b4fb0`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-go-kernel.json` (`sha256:ff421b409c3c4adf064167fb2645f8095e530644d4811b26a720a56dce16aa4b`, normalized `sha256:ff421b409c3c4adf064167fb2645f8095e530644d4811b26a720a56dce16aa4b`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-negative.json` | `5d0d3ac3ae835c99104e759ef2013e3b261b1cea6cfd8ca91a7108a336b9233f` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-go-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-alias-propagation-positive.json` | `ec3ac8dd99a67417a48f55aa4c78a9d81a2c42e2dbe4340c997f82a3ea029202` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-negative.json` | `73357862dea1d41e041fe944c826360522fa21c4e8b3fac45833b0e09e624184` |
| `dfb-template-argument-position-separation` | `dfb-taint-go-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-argument-position-positive.json` | `dcc2db79837cf063903d3e9ab4b79590b4a62eb87299cc99656022e5253d92d6` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-negative.json` | `3cbeedc15a10879883c442841db288f81a97f62fd983e4c6b7db9789b73d29aa` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-go-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-expression-positive.json` | `8bcdb8c7b7d6e5a0f6f580eceeb528db57d31cca779e0a299b7e7d6f73ae1826` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-negative.json` | `882dd951af332838bbf0d7166a8d8b2e58d475080184705c08daafa189928c95` |
| `dfb-template-array-element-separation` | `dfb-taint-go-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-array-element-positive.json` | `1b67e20d781363f41e6fe40b71c41c069d19f403ce8059d77b3bc4521ba09994` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-negative.json` | `6d5f21b655276791da335e23c07d07f72f875dd35038280233e7ae749c226dc3` |
| `dfb-template-branch-join` | `dfb-taint-go-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-branch-join-positive.json` | `5442adbe94971905f859fa73d2758b103a8d71b048b05940a959276675d752d8` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-negative.json` | `e67df6728f8a60862e823e47cf5b8ed2c6dd825ae7bf1a5473f18c1ed8603992` |
| `dfb-template-call-context-separation` | `dfb-taint-go-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-call-context-positive.json` | `04720f009d3a801ec8a6cb85e999b6b46bb086d9d0ff56656291bc2d53a250b7` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-negative.json` | `a91eb57f1b2622055e43fbea270ed54cb4bf82d009340b361ac8861afb8461c3` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-go-anonymous-implementation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-anonymous-implementation-positive.json` | `349071d3ac6479d844c6a096335bb9e9da41cc2e9f63bad5d7a9f67edca97a17` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-negative.json` | `7a0bd2efb4601e26dcd855f1b142c76aa3800277641ab0e93039161d1d465df1` |
| `dfb-template-chal-callback-registration` | `dfb-taint-go-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-callback-registration-positive.json` | `653dbba0e6cfcdb3fdbd9033e4b370c839fa048216256a504aef187122cdc21b` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-negative.json` | `eea308f520220f1764c7c9468fbb599e6364d81f5ac27bf000140b3992255d32` |
| `dfb-template-chal-closure-capture` | `dfb-taint-go-closure-capture-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-closure-capture-positive.json` | `651802d7baff4df03a23c9f09bb4c4ba3952cc1d059f6fefe805f4588dcc1fa5` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-negative.json` | `be0276759cb2f31f10cfc63a6f4aa63a8f90cf5e75c79de53e9f1bb0cd293680` |
| `dfb-template-chal-computed-property` | `dfb-taint-go-computed-property-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-computed-property-positive.json` | `e38d53f3b9bc9d00a61e17d723b4261c47120b578855bad909768d814c90df7b` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-negative.json` | `55b038db6b792c6cad52990793b005c8a27f5670798d4ed5b030031feb3127ca` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-go-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-context-pair-depth2-positive.json` | `de780ac0750705682e57af71a55d75587b7d3ee0c1600b97043f41368b98c593` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-negative.json` | `bd53c69be27cc83a301bc0c821fca715576a7c4af741dd1b8cc8e69071705b6a` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-go-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-deep-relay-chain-positive.json` | `dbf5b80af5afe09f6df3f05cbc1a8e959c7580c39b5f6cd8594c95a4091aa730` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-negative.json` | `5518ab4d19079f1554bb65cb4e9e145c2affdf4ac85a63f29503ae5bbd78eaa8` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-go-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-dispatch-table-positive.json` | `3ed72018001bdd2de7d08237b32099f6f02a419e9818affdad6139b7bb246c24` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-negative.json` | `f3258058db75ee9e6708644b6ed92b8270fb517cff692ae3a97779c427738f78` |
| `dfb-template-chal-element-object` | `dfb-taint-go-element-object-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-element-object-positive.json` | `ff2cc2d6fb5fc00d37164cf402ef15c5545ced836b2d3ff5caf487b0b7c183c9` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-negative.json` | `794eb5ef3b74edccc6675dd4af20d241ba269ec25ccca2dc9837d4f4e69910ff` |
| `dfb-template-chal-function-field` | `dfb-taint-go-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-function-field-positive.json` | `939e0b4181e48dbba231b89156f386cc204f569d56c5b763b1c166bae5d04c8a` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-negative.json` | `d2f9b549e9ce5af63db192c03eb9bd90005dbf93755b2b889df593e48745d59e` |
| `dfb-template-chal-map-iteration` | `dfb-taint-go-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-map-iteration-positive.json` | `ff1ae81d0392e4fe72a81cd38cb16c26c912eedd3e781ba2bc8ddd43027841e2` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-negative.json` | `2d8ab766fb253b8f360df06ed2042ed54529c7d0a9757d66b175f9b638294ec3` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-go-nested-access-path-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-nested-access-path-positive.json` | `2dbadbb6dec583e369b939ac43bd7c38b53707858c36ae427fb16284e2938913` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-negative.json` | `5c011523ce75b20c961625e6266fde8b3f38e98cfe44a6189cf2b7a5cf2b2156` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-go-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-recursive-carry-positive.json` | `3cd1bb5cc7e8785b91a86ac665ce85ca912904f673c5e47c173cbd1bbaeb8b47` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-negative.json` | `f1ec54b8da32a299541db9edb9b547d1674cccab4ecf516e202c141a09cbb5b9` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-go-reflective-invocation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-reflective-invocation-positive.json` | `60437fa1293db64f9ff27f6fbecb269aa08dfeece48620ca797c6ccdf19417c5` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-negative.json` | `538ea6994073a2a5efb2285e39ae0da5ebd8dc1a20aa3f0faad77c06a1a13a0e` |
| `dfb-template-direct-propagation` | `dfb-taint-go-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-direct-positive.json` | `4470ea080f6f763d6f27eb744bd0eaea181e2306c5eeb1e84460f5c0aaed55d0` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-negative.json` | `248f2a9d94a9257a3e7c14c39b96876f5bb3cbcfda522e204751b1902fc3abc5` |
| `dfb-template-exception-catch` | `dfb-taint-go-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-go-kernel/dfb-taint-go-exception-catch-positive.json` | `a433cf00ce037ece7ef95aa0a96b2d2b28db23b0dc4629aba0aa02a9cc215275` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-negative.json` | `ac688d20f071594ec855547008d56768f4471a9cb32257c2476ceaf91ac544d5` |
| `dfb-template-infeasible-branch` | `dfb-taint-go-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-infeasible-branch-positive.json` | `771f7ccc5bb97c6fc65dce8d4128ec85110f684869b0699a0e8a26967b7623f7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-negative.json` | `6d5a8ed372daab1ae69f3cdc324bca8c073162bd64eadbc3f18e0f69f49531f6` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-go-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-chain-positive.json` | `9d756fadf6e3aa32a7d720a3da316042ee9d3807b5950bbf35a9605a55c783d5` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-negative.json` | `91ba857d5d702099f9bf511da3261635b10fbf61559900c192920c5c8bb6a6b4` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-go-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-local-overwrite-positive.json` | `f5bbe20f20841b17d1a40ee7c8b1714a3249f9c38b1a297c0477f92c4a233279` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-negative.json` | `6e0757d8a6e36a069a6636bdbfa63adb1b1a053be927d4111dc333a0f86861cd` |
| `dfb-template-loop-carried-kill` | `dfb-taint-go-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-loop-carried-positive.json` | `26bcd77c9a7f5dca63813c298d2439267294e925709bde047d9430fd7008ea3b` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-negative.json` | `df203534fe645881e388353c1583d8e0fe3201809443880521719687f48d2073` |
| `dfb-template-object-separation` | `dfb-taint-go-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-object-separation-positive.json` | `978d2a324b8a568bd011775961f04cb44168ea7899b7cbb3b51ca4ac6ce5b50b` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-negative.json` | `07ba1cf88fcd6b28a1ea4d88131d576685dbd27bcf8837eb6f1ab9889cbfc0b0` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-go-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-one-hop-positive.json` | `e6917e70d8645baa9e34fab004172a17044764f4bf3d6050c1f8161dec7d8f32` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-negative.json` | `2d3f6485c032dbf6f2e687d44987fedc26976f4181c9990a01ea76779851554b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-go-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-return-relay-two-hop-positive.json` | `522f8c2bed2e689a99c57d58cace916bbadd5bdca1effb4e7d3ee694a363e813` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-negative.json` | `41a112d9b6594f53066c7ec3b6fa7f891d4bab11b781131d726f95e86b76449f` |
| `dfb-template-same-object-field-separation` | `dfb-taint-go-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-go-kernel/dfb-taint-go-same-object-field-positive.json` | `64fdf0c77d00655d14cf82df410df9c64911f2328732d4e3e9b1b5f1c4ea7d9a` |
