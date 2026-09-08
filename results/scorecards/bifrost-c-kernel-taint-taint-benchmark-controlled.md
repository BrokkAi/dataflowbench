# Scorecard `bifrost-c-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-c-kernel`: `bifrost` `bifrost 0.11.0` (build `bd77fd7e47c1d683231a9a2f552c997fd13634e2`, adapter version `0.1.0`, configuration `345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-c-kernel.json` (`sha256:41713490c40230560c5c9235eb4a2153d7a2d8cea90e8cc407f00abd63f4aef6`, normalized `sha256:41713490c40230560c5c9235eb4a2153d7a2d8cea90e8cc407f00abd63f4aef6`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `780ce321f7fda9fe2cef2e8739ef68e6c134b6d653c6925b0127499b726ccc3c` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `6a9b1c02868163576b9cf71ec539e92bd770be686fc29e95dee98f8cc4f01d3f` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-negative.json` | `52f3cab712c931a14baddf21d8d7a82c1b3880aa10e1b3a04ff80a5486c029cf` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-positive.json` | `2b75b2503209a456885ae1c2009346c108b9b5f90759bf35647ab8cf8672ac9d` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-negative.json` | `c61c4025d3a3006598d93dae52ce9b3896418dce66e92975091fb4b928c4f18a` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-positive.json` | `f417a29bcdb2c4a3a7dff0f9979021f8f569ce210e03b3fad8c06afe9cf0e6f0` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-negative.json` | `ede48da8e254aeec39fc559b1fb229e3590211348bb503865200b35595381b73` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-positive.json` | `c06d9e718f1641ea08ebe9bf33c47dd54e5eb7b5677120ad36d28e31b3e24a27` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-negative.json` | `4e362563a9251237f57a798fe2bb7550a9cd3afdce5c2315b9571ae2b9ffb41e` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-positive.json` | `34f2f73275bbdb92aacf06ca50938c71aeda9ea523de0c44d19727703505a27b` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-negative.json` | `cd2dc38d4afdb5313604b3756f60fd1b127d1050eb04de2138d05ccc6b514f7b` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-positive.json` | `888ad0ebe5265a40a8de111eaa4c461dfc9696eac508e820b5bd1b6fe258fc53` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-negative.json` | `ec94dc71ca59a3161280c8f9eb3375e5181a59a988555b3471f43ba23bd7507e` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-positive.json` | `559466fb3d2f24b3d4df3876c21e1c379e220751614b1cbac5a862b48c3c1b3f` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-negative.json` | `5975ece7d6478cebfc71d0d789567ebd067737cdbab28d38425ba04c4fcd16b7` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-positive.json` | `3a41d6a6d5c13e43136a9231bc79c7d4e890e58fa2c5213aed7a2fc322e55d7c` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-negative.json` | `c63e33dbc194a7ea803e3cbfd7d047286e3ea7805ebe0f411a4ddceaebc89433` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-positive.json` | `d15258986c72c2e0c08e929067aaf4767547ed68abeb84b3f134474ee9d1a095` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-negative.json` | `d453d9a62f684aa2c6c6f454d8d5882d60338b373c2187b8a99a854c9a66fcff` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-positive.json` | `66befdbfd5b992964ed1ee3729b486d18ffe5b4b4c39663b77e4bb866dd784ff` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-negative.json` | `e14b3e903762e5fbcb53f6972b1562c96825a9922e9762f026390f348fcc7e1b` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-positive.json` | `7adb8c7591c6fcd9de97556b6cb1d5134c64d2b411a85dd18afeb42122e65027` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-negative.json` | `1489359333f08833bcf0276c50f09dabab68662db2fa82c492a3c29ca016d36d` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-positive.json` | `8ff3e57ed42c5907e3e6a6a945a6dd646ae87ebf7910afcc157cfbbda1d45132` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-negative.json` | `a19057a17951980a51dc7733d54a7273c8d1bc590bad401b8cb874f62a60918e` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-positive.json` | `6ce8a810b3d8dd8913a346a14b5ff9e54543a505227855282721c80585af2bfe` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-negative.json` | `9b4389e027ba7b7d6f48bdcd1e6e57a7e03bcf078a895343f823a499a20f77ce` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-positive.json` | `9f3f3106ee88f7cc8829c742fec08d2f7713d0957babe37d51d51609f938d36e` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-negative.json` | `5ea600a60f3db905984f5cc5a04b916c049e893c10da1f17e9519da2bd238b09` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-positive.json` | `f8265c828d74c10115c1154ca88215e3942070dfd08d3c485458aba0853b1203` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-negative.json` | `41e4429cc9dbf74a5528e90db6b87a1c5ef7d8cd1ab553507e54062ecb37043a` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-positive.json` | `a4ddaeef10a7129a03ede4ee83e2b1f645ee8cbd01f6c65bdb351d283a9b2e2f` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `ee8b33256994cbec156b261dc07aa43479c98e86c2071a49e0622b6e82be322d` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `95bb1c67b299b7e47d535275620c2cdb5b89ede4c321ed30ad4bd144b17682f2` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-negative.json` | `d0f828667c86fdb8177599c790b66626020bc4060c5db19fa565442de4ed4aae` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-positive.json` | `b8a0852b9fc80edc31cea668f90adcad94f6df7267c99b383f9fb46a11ebce49` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `a9e51e1d73888c5adb0fa5a44567a793f7e13433c5c03bdf7c7658b805524fbe` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `38fd129025ab578053e30fcad5a738caea5eef30e013968869555a6045bfce4b` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-negative.json` | `3270b956edd99a7e09ad5c73076d87639f744c5a02c1b7fc556a480017c79758` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-positive.json` | `b7cf441b8a011f4cf0759e48ab12a00f6557a7e882a1f22a32a44d6b5b027aec` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-negative.json` | `4476aca330d7640b8657c71e1191c937156c5f16e906b4533261763f63174f95` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-positive.json` | `027673502eccb6e5cc2c907df086b735413f278a32d5248068c644ac206f3479` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `1686c25ea26604149d0af638ad690d6d60ac9c8d19ac2acc2594635a471d5de3` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `1550b8234eafd468a05b660e49e7b637becd6664736523ed0266c9389d264006` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `68c2fa2832dc267a7f9f17a0a7f0c78b16c066bf6db9e12a19038813819738a8` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `57a7bdeb6d41d064491dab10c2f6955928eb5812f40ab4c2bb8bede167a99808` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-negative.json` | `7f5472d84280377655a1cc730bba1f83259650468b6922efbc8634f8c253c02a` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-positive.json` | `943d73446e4d23318ed93e048d60a739e713810dbbc6946ad2609eb9e0e81d0d` |

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
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-error-code-return-positive.json` | `57c293ab38822bc0453332a08fc57a1b2e101dddf02b815de35552b69e02e6bd` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-goto-cleanup-positive.json` | `e4f55aecb3a343e3d174ccfcb836c94c73ebf147ed01a92752dc7dce9ca53428` |
