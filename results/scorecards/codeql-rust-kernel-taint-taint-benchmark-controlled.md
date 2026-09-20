# Scorecard `codeql-rust-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-rust-kernel`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9`, adapter version `0.1.0`, configuration `ab464a094e47ef2f07c708c42de0c7f2dfe7b920f7e4385e08e38f43c98f3312`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-rust-kernel.json` (`sha256:da6772c638a45210d1e1f5e1a7734d7d9b46f1d44752506092dd8c7b21e0ecda`, normalized `sha256:da6772c638a45210d1e1f5e1a7734d7d9b46f1d44752506092dd8c7b21e0ecda`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `rust`, tier `core`

Outcome coverage: `reached` 24, `not-reached` 38, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 62. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 2 | 0 | 5 | 0 | 0 | 0 | 60.0% | 0.0% |
| `dynamic-dispatch` | 0 | 5 | 0 | 5 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 6 | 1 | 1 | 6 | 0 | 0 | 0 | 85.7% | 14.3% |
| `heap-field-sensitivity` | 5 | 4 | 1 | 8 | 0 | 0 | 0 | 55.6% | 11.1% |
| `interprocedural-flow` | 10 | 4 | 0 | 14 | 0 | 0 | 0 | 71.4% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 6 | 0 | 0 | 0 | 100.0% | 14.3% |
| `object-sensitivity` | 3 | 3 | 0 | 6 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 4 | 1 | 0 | 5 | 0 | 0 | 0 | 80.0% | 0.0% |

Macro-average over semantic dimensions: TPR 67.0%, FPR 8.1%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-negative.sarif.json` | `ca9fbbd63e163b1cb3b260e9d853dfb6a9b61088116e46e752ee603d29e40b62` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-rust-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-alias-propagation-positive.sarif.json` | `72e8405fb05e6870cea7b581ebf1bf7f3bdd52c39cb65044712e129b90ecf9e8` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-negative.sarif.json` | `4732c87a64fea5d89e16787399d7cc2c059f7ac3adf70e8a610383908b919873` |
| `dfb-template-argument-position-separation` | `dfb-taint-rust-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-argument-position-positive.sarif.json` | `cec99286167113e8ed118acbb0d725a892d42975d9f12e7b76ed9fa5f68608f6` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-negative.sarif.json` | `bd04ee19fa1370e8fccaa443b16435132a1243982e05066e305368a06990c290` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-rust-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-expression-positive.sarif.json` | `a854cbb90830cde0eec48e8f4700c2f2170ecec6f68fbaa819af4b707758fffc` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-negative.sarif.json` | `3bf7c2f6806ea851c26faba218c3abcc32b0cf5c81e82f97873ed325cd958d00` |
| `dfb-template-array-element-separation` | `dfb-taint-rust-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-array-element-positive.sarif.json` | `55461cca3b9de6c7682c50d9c91d7105fd3ba1b8980177c905c671e51ef210e2` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-negative.sarif.json` | `825992e846eb66327db96f9c9ceba45ba4996912e2ec82b6ca98a74870d3b950` |
| `dfb-template-branch-join` | `dfb-taint-rust-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-branch-join-positive.sarif.json` | `f5f17fede5ce0ab070936e52127b83cc163356030d4b19e7c405f076894c001e` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-negative.sarif.json` | `7c19f2bbe2d16c4c65390d4192d1cbfd40ab18567937d68747e9e4ea85ef824e` |
| `dfb-template-call-context-separation` | `dfb-taint-rust-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-call-context-positive.sarif.json` | `25b6ff4dda9751424b78e7ed1ec27ea8d0985376af790fd08328ab930329d117` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-negative.sarif.json` | `c7d14c483852641e47ed269944c7ed12a8ea8be01dbf005f71d3306699848072` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-rust-anonymous-implementation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-anonymous-implementation-positive.sarif.json` | `3f8528a0eb67d5e4e4a182050bc749b0bcd9114092cf4894ac01325102cb7d6f` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-negative.sarif.json` | `b21b6859fa46a152bb570ca7dad29902d99f3b04c944fce1b6a13123579ebf07` |
| `dfb-template-chal-callback-registration` | `dfb-taint-rust-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-callback-registration-positive.sarif.json` | `ff5b8abef236c8afd7790b3e7171a84e745dd23b060ebf781c6c42af7df07165` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-negative.sarif.json` | `e149f5afda933819f66c860cb5f9eb938bb7c8f524fa11f361505525f4214e08` |
| `dfb-template-chal-closure-capture` | `dfb-taint-rust-closure-capture-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-closure-capture-positive.sarif.json` | `ab54c413cfae697ca87dc2bce6f3f0dfcb05230d4d09c579851416f1032b49ef` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-negative.sarif.json` | `25dd25e99ede86b5533418b8e9d4bece20dee60d6636a9627763c7a7341ee62c` |
| `dfb-template-chal-computed-property` | `dfb-taint-rust-computed-property-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-computed-property-positive.sarif.json` | `71a1f4b06bbe62f7dcff99a20a435fb4a1e5182c5c8b86124eb34d96aebfb4de` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-negative.sarif.json` | `d4c5cc57431f948be5e27b423defa3dd025ad18cfbd7e11a4533e7c1533ec3e2` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-rust-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-context-pair-depth2-positive.sarif.json` | `5de2d924ccb2fe772dfc28687b7c356d56162c51c64ee93d62d9e3a8c9f18b75` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-negative.sarif.json` | `4feceb15c76f5f6977ca6d3333700a91018af799e8849293eb75613c8c1c82e0` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-rust-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-deep-relay-chain-positive.sarif.json` | `41b383977c3b7b75673396229adf2d1c3e1252131e0b849f6fd1e50d50d0d9c8` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-negative.sarif.json` | `983d2ec7167cb8ee93efcc033f61c8d94b9b7292f18c5f326e92be0c3df3eb7b` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-rust-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-dispatch-table-positive.sarif.json` | `7593f85528b1a6f2a865739af1459e2ca0f8e4e120bbe70597280c6e7a9afee3` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-negative.sarif.json` | `4f2b38d1d736dced104deaacf67b582e094b92003ab36fa68a224b352d58ea21` |
| `dfb-template-chal-element-object` | `dfb-taint-rust-element-object-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-element-object-positive.sarif.json` | `e933a60aa2906ecb8add15727fea9847a19da77dbff66b37fadcf48d481212c9` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-negative.sarif.json` | `fc89992f0513416126908e1c15301a9e4d32c307326d04e9080f7aa748e5b31d` |
| `dfb-template-chal-function-field` | `dfb-taint-rust-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-function-field-positive.sarif.json` | `239310f6341a5128f4632217e497ef32b8afc1a7a40117adf896e8f45552eef4` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-negative.sarif.json` | `519ef55c6a681f91b002289a0cc2e6aec656462336190e5239692bebf9583542` |
| `dfb-template-chal-map-iteration` | `dfb-taint-rust-map-iteration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-map-iteration-positive.sarif.json` | `dfa6a9991a105057001a152b6cffcbb142f4dde409df27731efd304dfde25682` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-rust-mutual-recursive-transform-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-mutual-recursive-transform-negative.sarif.json` | `de914707ed60faa5edb24aefca22bd3bc8a94a32aadcf4c955210442814cbdbb` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-rust-mutual-recursive-transform-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-mutual-recursive-transform-positive.sarif.json` | `89cb9899db08238fcb0f994286aa29f38968d733618b2c3f11c160a5c886203b` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-negative.sarif.json` | `ac4bb302121326930e6e96dc54c30f010f92e5ca5c8f265aa984eebfe6386010` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-rust-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-nested-access-path-positive.sarif.json` | `830542cef4bd042fae58deda76e956d3cc2bda72a2d45b908560a7a5d1a698b7` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-rust-recursive-callback-transform-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-callback-transform-negative.sarif.json` | `5ca208c15260d57e1fc94a5190445a6ea988c35c4e3d9f0a010d87194f4a58b7` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-rust-recursive-callback-transform-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-callback-transform-positive.sarif.json` | `c772a9e6a1c4598a0e9c1645cc91ba826cafcf861da8b3fcaf88da7c0ad70784` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-negative.sarif.json` | `cc76039aa2656d8e7948a311b6e178b02b0601d7a56010e1653d865e65353d8d` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-rust-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-carry-positive.sarif.json` | `e55006c6487a39e50bfde63b5a89c0c15f90db94fd32b831f4abe51368c674fc` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-rust-recursive-heap-unwind-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-heap-unwind-negative.sarif.json` | `31d2d767292e06857443bbea5d39b5be9892fa91a2aa3831df6077ee1d9cf506` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-rust-recursive-heap-unwind-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-heap-unwind-positive.sarif.json` | `58cc4a7ae904f576412a8baa0a06aa639f5afd5c6f452e5415dac1579af2005f` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-rust-recursive-payload-transform-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-payload-transform-negative.sarif.json` | `bd9a8c2e9b5a476e2feaced7a020c80b199e8f9d6b879a795c66ef960dfebaba` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-rust-recursive-payload-transform-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-recursive-payload-transform-positive.sarif.json` | `00cf9f5f609822ef8d3c188b454891651b91107c74698ee53299d0e7900fd64c` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-negative.sarif.json` | `b3bd2d4a26d430e85059a9b4b90a6a613b5bc51a50c6fc38ea99efceb71c7115` |
| `dfb-template-direct-propagation` | `dfb-taint-rust-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-direct-positive.sarif.json` | `1d6f36670e323d3624aaff54c14ce90bf87236ae38d2cc6bffde9052c23f8b59` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-negative.sarif.json` | `4ac07aa4ab6f08c57dbc7c02b365d812cbd269836b2460dc1db3626f76455141` |
| `dfb-template-infeasible-branch` | `dfb-taint-rust-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-infeasible-branch-positive.sarif.json` | `16162c924b91c87f79b7dd96d5c630fe48252c065f2c9fae1f7a23f9bc8f46c7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-negative.sarif.json` | `739b57c5839ca717a16541295c4b2f2360c2b008d0b7a618bf0fbc38296daa73` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-rust-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-chain-positive.sarif.json` | `043fbf9bdc312c1a9430cd10dee984449d35580c72eaac4b14668e5e673f0668` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-negative.sarif.json` | `99088f858fae3bc56a12f7c547d857d8cf4514f7034c0b2de0be88582c772463` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-rust-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-local-overwrite-positive.sarif.json` | `aa571466fd782473116deb9501117c1c8363f71efa61e94dec903b800587fd3c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-negative.sarif.json` | `3a1c07697628cd4c1518b4ae671cc1736532c6d9bc15d0022f59a7f55fc8ec5a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-rust-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-loop-carried-positive.sarif.json` | `1202153f5e6c1d6c33715b6febb8d7f688ff6d3abb6487b7c846b2373b0d5152` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-negative.sarif.json` | `2ff2dd5227b714d07a04ffd998c793493b62ebe19008bab40554dc6ea4c4df0b` |
| `dfb-template-object-separation` | `dfb-taint-rust-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-object-separation-positive.sarif.json` | `2c776ef81608c36a916ec6fa8cee6cd4e5be2fe573c8c0ec4777caca8fa1b3b5` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-negative.sarif.json` | `12f109ddd0594972a9efe9925576f19f197c76028929dd7ea08674ed762e0e4e` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-rust-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-one-hop-positive.sarif.json` | `fcb7d131fbe04e93376c998fd8d7af20e3fe29ccddeaf62698e4828df98c2b78` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-negative.sarif.json` | `274cd7768ffa125241c28dd17bd5943cebb3cf1dfc8ff5107e4b031ee0eb8ace` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-rust-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-return-relay-two-hop-positive.sarif.json` | `cd9c241cb71d4c4b2e45d36644cbb7b813c2464fa0c12a7d32ce54a540d24edf` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-negative.sarif.json` | `ad38b0be2a8965f341b1e64ea14404c4dfc1d4969fc025ba5ee84b3357c5286b` |
| `dfb-template-same-object-field-separation` | `dfb-taint-rust-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-rust-kernel/dfb-taint-rust-same-object-field-positive.sarif.json` | `63abe34c892c8ac232f364e3a12fdaf063e04ace5c659ac0e23ad16476ef6a12` |

## Language `rust`, tier `language-extension`

Outcome coverage: `reached` 0, `not-reached` 2, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |

Macro-average over semantic dimensions: TPR 0.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-negative.sarif.json` | `404c6da26f104304c5ed9f64b82e734fb16602a6a89c15f4e6c542191e314d7f` |
| `dfb-template-result-error-propagation` | `dfb-taint-rust-result-error-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-rust-kernel/dfb-taint-rust-result-error-propagation-positive.sarif.json` | `7f9aa64da89b8c5ac75604fe92ee69df8253354e7bfbffdeddc5bfb884477efa` |
