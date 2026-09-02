# Scorecard `codeql-c-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-c-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `719415b9134dfd43390ffdb76eef45f7ed022f907f22913226c22f93277b62f8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-c-kernel.json` (`sha256:0bbf4766f6a5fe4a60cbc1fdf6667b942a01456df9c0828485db8d43b201fd4d`, normalized `sha256:0bbf4766f6a5fe4a60cbc1fdf6667b942a01456df9c0828485db8d43b201fd4d`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

## Language `c`, tier `core`

Outcome coverage: `reached` 23, `not-reached` 25, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 75.0% | 0.0% |
| `dynamic-dispatch` | 0 | 3 | 0 | 3 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 6 | 2 | 2 | 6 | 0 | 0 | 0 | 75.0% | 25.0% |
| `interprocedural-flow` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 6 | 0 | 0 | 0 | 100.0% | 14.3% |
| `object-sensitivity` | 3 | 2 | 1 | 4 | 0 | 0 | 0 | 60.0% | 20.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 75.6%, FPR 14.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-negative.sarif.json` | `8e04e92b140e7d532cce7b794f3284481824054a75a35c90a55d588a9d2fb967` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-positive.sarif.json` | `2d88dfc4952a056d4d88b8e3965d4aff6559e7a20f20edaa12538390f58b07f0` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-negative.sarif.json` | `cec887fe3e92ccb531d16a023cc9fc3749cdfaf2f38c6ccfd0cb7c70559651bc` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-positive.sarif.json` | `421333db41abe52de8a05fe586bc476787f0c0dee67adb857d6ce63fd015a845` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-negative.sarif.json` | `8014136f934a7bfbc09eeae8a426babe06f1e07131e9db4e80bd2956510abe30` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-positive.sarif.json` | `bb8a3c38c4c4040e085548a1e62dc4dd7c881b04f19291e15defce6b4fe452f1` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-negative.sarif.json` | `c0db763da81dd2919f5d2b27c8461dfb0b3e8777b8b2fa88bb15dc5372504684` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-positive.sarif.json` | `f43dd3ba3cce0310fca3ddacbd2406ba154219bd22ae84c33e15e0d298b1ae1f` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-negative.sarif.json` | `93af2bad7c20cfcd80ce499ed92661b0826f2f999dcfdfe295ff21dc6706bdfb` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-positive.sarif.json` | `34bdb803eca252ecbfcc9d84278d4f6b016c70d1debd159250cb2ae9fbc0cb5e` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-negative.sarif.json` | `0e7162d9b8d6743150d5f25dc7d27c61901397081a871b6e07de7250ac4bff14` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-positive.sarif.json` | `30b645eb2f5e610c9f986d0a56888b3e174b52a0ea426847dd0b91e26991b832` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-negative.sarif.json` | `c2633cf8e053bf7c9ec316edd80431eebef51ea913a13f9d0637b7118d7d8b3c` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-positive.sarif.json` | `05c71e1dffdb447393b1663cd7570a7a461636a5ba31905ddc5f399fd9fc15df` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-negative.sarif.json` | `0bc4a3c58720d5aa29f3b8e12c2eca9e1be26000ad7138ee1307547507f627b4` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-positive.sarif.json` | `ab1f3b3ebbf47d4aac12f430784813c26c3e74d00224be44ba63ba5d57163054` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-negative.sarif.json` | `b55c5def11c568c91b2d1be67f56aa8895b0e31211e9051e463662af5b32cfbf` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-positive.sarif.json` | `e8bfc0eeab31fe55eefb29695679021acffae793091c7f396775a3fd690f513d` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-negative.sarif.json` | `a15e7d75a166267ddb7fde43113eef5878c5710b7a6a9bfdf66c9d6633895797` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-positive.sarif.json` | `1bebf0f21e14b906343913abb6f6ce71666bf5288d27106647fb70e8aa51c545` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-negative.sarif.json` | `823cfc13ff97e9b21cf04000d4c9602776cb801e7c0fecdf53477e069ffa9762` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-positive.sarif.json` | `10298fcb1598e3741067f045cc7a0c3dd21bc2080505f75362e3ee11677bcdb8` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-negative.sarif.json` | `498dbe3742156e260b22d0a86041b0ba81b36008674c0a6cda609a7ef3675267` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-positive.sarif.json` | `c6db7f48bbc1947c222484c18be2a6c1a15a16e2be549e500e5d78e2990a03f7` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-negative.sarif.json` | `4dafa1041608e0d0af147b2253cfa9e605710129581777ac19ced24b09b78bbb` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-positive.sarif.json` | `3a10dda35f2e24254a9b4efec7e176447c89439876b60d4333d61ad66246e92b` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-negative.sarif.json` | `61a700432db52b007f51f2b5cbbcdf8a6918e4455281bae1e1751ce4210bcbfe` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-positive.sarif.json` | `69a59e00e18380971ef95250443bc8e9f76af66b64e2f59fb34a72c344975eed` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-negative.sarif.json` | `5f8bf16a589bfab353655e9d39eaa64a11da8c19acacfdde109d3d3b6f761a22` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-positive.sarif.json` | `fcdc665386b2665f21d0a8c9601844319dab8b8531ac529c4023f52b624a4bc1` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-negative.sarif.json` | `0e0a404d79ac2beb9a7f47617d85345de6058e2af2ebcf9970313bd90a94bffa` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-positive.sarif.json` | `a3776e998b5e564fdf964c642c7ef13797d28ababb604dd489033afd63d395bd` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-negative.sarif.json` | `326ece73209a7913d425f760a6da823db5b24873083ce7949cb5db1abb24f0bd` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-positive.sarif.json` | `4442d6b9f11503ddc635c1937c86f959f23308772c633126609ec6c51f2c3f79` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-negative.sarif.json` | `15e652880fba10b3a56e45d182ac0afbbbad8a4ff46363401db9629d6234be28` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-positive.sarif.json` | `fbcf3f2cdfe6201945894a7c26aead25720471dd297e7f53b618606f7a7734b4` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-negative.sarif.json` | `eeccd5af6eed25fd2bf0267de4a35c0abd91cff34b6b2f0674a0971837fe8f1e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-positive.sarif.json` | `2df7f840a38249d1061b4acdd4185930f867b14188ae870a5d913845df77efb5` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-negative.sarif.json` | `d842075721b7c23c5e4d1c5fa10b13db7d4f7398a9fdea48f3c4473442fafdad` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-positive.sarif.json` | `329158f58243c2536cc008583336c9a039c00569f944233ad5d6c8a8f29180d7` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-negative.sarif.json` | `8e0c5977b03a2be63595529ca5cf06dc3b3e127b5ed979ba3c06e965016135da` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-positive.sarif.json` | `2820e017b261bd987a275a93408a5a5c6746cd5c073f6c1c6760f35386dbbe7c` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-negative.sarif.json` | `b3d3db847a6402aadb8f0bfd920a4f94acd9d571f4b22d488b6697f0733e4897` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-positive.sarif.json` | `6bac471937d52afa636aff1d61372fc49746c3010806cb867f9250fb94edf380` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-negative.sarif.json` | `382069678a0cdafcc53823d123ebeed95eb2ed99c57ce4b579abd8b4132392fa` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-positive.sarif.json` | `0a41f3bf479c2183a5e5b86dff6e5acf6e40d04b91deac150489ea63fd831a10` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-negative.sarif.json` | `ced63af0815d70b5364e369ba67a7822a537963ed4550daf6b41b171909ad9a7` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-positive.sarif.json` | `6d0a66f7fb8c5bf58aff88a2e62ae0df087df93a6fd972f3637b08cbad03e71a` |

## Language `c`, tier `language-extension`

Outcome coverage: `reached` 2, `not-reached` 0, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 2. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `flow-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `heap-field-sensitivity` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `interprocedural-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |
| `local-flow` | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-error-code-return-positive.sarif.json` | `16e4061277b3d4934aedd55290d196476c0ee62522aed302eabba52887d258f8` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-goto-cleanup-positive.sarif.json` | `b9a2dd6425f692b182dcdf54bc7d4296b88d480cf999cc26a5869f2cfab50e60` |
