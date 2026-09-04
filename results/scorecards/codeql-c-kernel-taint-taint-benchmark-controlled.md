# Scorecard `codeql-c-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-c-kernel`: `codeql` `2.26.4` (build `codeql-cli:6b1e4dee94adb20f90a671f3fc9e04be32eecf65`, adapter version `0.1.0`, configuration `e1262d0ea438d0336325c8dc3e7a11ed656c44085442d916cee0d264871d5355`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-c-kernel.json` (`sha256:c09c75740d6590c727c813a6a551fa2058582fb913d47389e022eaadc42a6409`, normalized `sha256:c09c75740d6590c727c813a6a551fa2058582fb913d47389e022eaadc42a6409`). Generated from freeze manifest `reports/freeze.json` (`sha256:c92efa03098fd8b51e820ff66b942099c4b972d2fec19a90bd65424b5e01fa1e`).

## Language `c`, tier `core`

Outcome coverage: `reached` 23, `not-reached` 24, `inconclusive` 1, `unsupported` 0, `runner-error` 0, total 48. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 1 | 0 | 4 | 0 | 0 | 0 | 75.0% | 0.0% |
| `dynamic-dispatch` | 0 | 3 | 0 | 3 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 6 | 2 | 2 | 6 | 0 | 0 | 0 | 75.0% | 25.0% |
| `interprocedural-flow` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 5 | 1 | 0 | 0 | 100.0% | 16.7% |
| `object-sensitivity` | 3 | 2 | 1 | 4 | 0 | 0 | 0 | 60.0% | 20.0% |
| `path-sensitivity` | 3 | 0 | 1 | 1 | 1 | 0 | 0 | 100.0% | 50.0% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 75.6%, FPR 16.1%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `codeql`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-negative.sarif.json` | `075c15aeeb478be6319c5acb734a6dffa9cc755391807ddb5da693c472f46b35` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-positive.sarif.json` | `e26aa12b4c11ea045a158d563424859c0894fefca338682acce2505678a5390c` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-negative.sarif.json` | `c2648382b8263b1eb5005a32162677297815f712e6303b03dfc490af93b95cac` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-positive.sarif.json` | `47dfead9beb4440e5d74fcb0505ed11b23c639e2c977421d7a5d1884f532f988` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-negative.sarif.json` | `6256309944fec11a32fe984faaf784902b09bcf81ef650ffdf7589d59ea63442` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-positive.sarif.json` | `c9d00d52c31811f1375bab56fab31ec32d96cc040f7b98cba3170aae9a4363f7` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-negative.sarif.json` | `6592db6484b9f0ee15a37ec87a0d8e7da999fd75892889b2646dd152e0116744` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-positive.sarif.json` | `ee8b842e0ea45c39770a307207fdc4eb9b4c7776793a57b952a9a9737d3918d6` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-negative.sarif.json` | `352cd79d83d56d4826bb185a8fcd0eece7e4fd434523d985c29a3bef80d55cd7` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-positive.sarif.json` | `12133b13546909d79ec34130432f96ad7d955f17973a66cf11506d836525265c` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-negative.sarif.json` | `c4276490070370b3e6aa1e0c66916db024f879627e5f510d8cc8890a9bc2faed` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-positive.sarif.json` | `a9aa4ae45f41a3d6ec3e80008e8cc8d59c6ef7a4b14e7c922a62bbe1340c1fea` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-negative.sarif.json` | `420527ea957c5e1aaf1de602e3436bb20ce7e486b3240ccb4b167a792696b2f9` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-callback-registration-positive.sarif.json` | `dc6245f6a17f85bb1fb91466fcc7a359e2823374f12cd885320866b449b5a177` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-negative.sarif.json` | `56ea8da2c54b4170aa291f9ea9b6fafc75b8702330b861250615a7650dc3721c` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-context-pair-depth2-positive.sarif.json` | `2825e77577256713a2968e7403ab6bbfb9d15ca32196ccf027f966236fb395ef` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-negative.sarif.json` | `8b631140f8b78e2dd71befbac8725f9c58addde2f5dd08feb08e60bf0ce84309` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-deep-relay-chain-positive.sarif.json` | `fcfb217cccaf0de572aa1ddc8cca4fbcc40119094a316d3d5c094e30ca52d560` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-negative.sarif.json` | `88b927c84fdb219c0adb37503d7618a0fa27088ed8f717e435e90c69578d0c14` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-dispatch-table-positive.sarif.json` | `902361790ef44f7abf56e375c8c9a6226272a1d9f4595623c8410c1134cd7a6a` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-negative.sarif.json` | `a5287524643a0317514c65419432558d78b20c348f40bcbd202009adc5229c09` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-element-object-positive.sarif.json` | `c0e60e25c25cbabdcc2cb925fda0d1aeabe96c3f68b8a084500f3a47d0bd7a3e` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-negative.sarif.json` | `8fd1c6ef7220b758c1fd66bf11763f1dcca0321678fe10133dfd7e1da1fc92cb` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-function-field-positive.sarif.json` | `5a3524a6fcded17d9fe4e999b79a9dfb385e426bf3edda922609539225f929e2` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-negative.sarif.json` | `e5a0557c25ef20c6bf832cfd817bc4e270e1d34dbff827f318fef658f7dec21a` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-map-iteration-positive.sarif.json` | `c11d28f1861e281ca49ab0d0fa82a6e55332075b5efc6be6925201d37724b125` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-negative.sarif.json` | `3bd42ebd2d9a09875ab22480878cfb795d77bc9060c2e96d323641dd42670e81` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-nested-access-path-positive.sarif.json` | `fd453c719ec78d4f91c53655cfe940abd39b077ea28203d610c83003cea547c2` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-negative.sarif.json` | `34f1b2d2341967b9a2a3b9168948d2526b112b0f82cf238d5068b709b1bfee74` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-recursive-carry-positive.sarif.json` | `bfd04d46cf03067c1fa40b93a27ee265c7fea4c5f2765726dbe1d37fc76125bc` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-negative.sarif.json` | `e7f5792e9f4357ef13bc6df193f8f0873072260966a23e8746dc347168a100cf` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-positive.sarif.json` | `ffcc13f593b6deb00c73bdd55ec31dd8d2b45139481dde7e92542135b77b7e70` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-negative.sarif.json` | `d3e0cd6730efcfb16c8f233b3411a67654083e00be7aaa93c97b2ae5f40dbd9d` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-positive.sarif.json` | `f4e25da2273189be58174a354d684071e2484315d87c3b4295b4fb801f4f550f` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-negative.sarif.json` | `b1b7a327852273819513c95d21df0b9b6fc0b7b6f55ad238859d173e6ae0e4c4` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-positive.sarif.json` | `39b2d313555572285a28f62460af51d577beb63f5e910bdccf707a699cab67b3` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-negative.sarif.json` | `c1c9b8f5a1afb7fe7a13f5bd2360afee3f508788df1de914c6224c645e018195` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-positive.sarif.json` | `7434aa1c12fb0e81f5f2b24b74c861c02a11be270d3c58389ceac75d1f1bee7a` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-negative.sarif.json` | `b6000181b009c083531c5cc11d2c79e47d69d0cb0dc6df9f01c6decc3481bd4d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-positive.sarif.json` | `aa753e81aea070f7d28396020ae35e2ceedd80f89a8b7c0a74d095b40d06da13` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-negative.sarif.json` | `ea298125bd166ef72d73ae2e2b292781640ea52ca50610382aeee1909d5c140f` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-positive.sarif.json` | `103924c1bad0e957c5cd9e48ced0ee7b777999e5bb11fdcb1108fa22106d244a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-negative.sarif.json` | `3542bbe50245ab77908448a9ea1e6e6d5c73433969efb5c6db456111fbe7b565` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-positive.sarif.json` | `b8e398b8dc8fb04d24c7f7b7c82440db33ac0c1b92ebe2d750c757b427814095` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-negative.sarif.json` | `84a81cda36092666cb6982879011ca55053ae8ae43ea032688063a6a8d09cb77` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-positive.sarif.json` | `01e12cfd7b27553cf1bc4cd3b072a81162055ca57e0108b1c81cf1b2fb4abf1d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-negative.sarif.json` | `1a3c1b540b7b41af5fed6bf2df92eb89dfff633fcd515a8864c25764e8dc18bd` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-positive.sarif.json` | `63c9f7dff16114cbb46d6691833800d6bd52d9deca64861f832bc72086fc397e` |

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-error-code-return-positive.sarif.json` | `ed25a09c7b45b15e4eee8c6623ffad58960dafafdb57202ac0b68b8d95381489` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-goto-cleanup-positive.sarif.json` | `9e29381724bdea14b6c2e4e7c2ddf38ded545fc6e6de46fdc94090c3806192f9` |
