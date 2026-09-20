# Scorecard `bifrost-c-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-c-kernel`: `bifrost` `bifrost 0.11.4` (build `015ee1f76b049e1ebdbb2fe66fb0bcd01ba43b2f`, adapter version `0.1.0`, configuration `345ccbcc40bfb14d3e17c434a5fca2ad103661d4318079bf4639e8d23a922585`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-c-kernel.json` (`sha256:ae4c70293d2ebc7ae83bf42f489d62d651608505aad498e43945035674d8f45a`, normalized `sha256:ae4c70293d2ebc7ae83bf42f489d62d651608505aad498e43945035674d8f45a`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `c`, tier `core`

Outcome coverage: `reached` 21, `not-reached` 21, `inconclusive` 14, `unsupported` 0, `runner-error` 0, total 56. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 3 | 0 | 0 | 3 | 2 | 0 | 0 | 100.0% | 0.0% |
| `dynamic-dispatch` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 4 | 0 | 0 | 4 | 6 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 6 | 0 | 0 | 6 | 6 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 8 | 0 | 0 | 8 | 12 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 0 | 7 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 3 | 0 | 0 | 3 | 4 | 0 | 0 | 100.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 0 | 3 | 0 | 0 | 0 | 100.0% | 0.0% |
| `recursion` | 2 | 0 | 0 | 2 | 6 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 14 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-negative.json` | `f8c28cdebb33b2bedc837edc640c1ec595b8dd434a1bd7998803fe241cf2276d` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-alias-propagation-positive.json` | `211115a944dfa7d2a6760742eef83cd3662e021dfa8c908e82f4d5ff3e3a98aa` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-negative.json` | `7c5382c1a4b78ea80a5230aa168815eb6fb8759b899c2f6e72fb8d7a99f6fd3a` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-argument-position-positive.json` | `6b58e43f978c1bf63c25c868edbabd28cd536ce4aea5aa494215e83b5b9db5be` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-negative.json` | `9d1621b6bc562c1bffd7677b5d161c160e16f305624b217f3f6de10de0c7ae54` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-expression-positive.json` | `ceaef33e5e7e8197b38475cc3267bb152c61be503869724706e91612d7b35735` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-negative.json` | `e8f19402b65286dc57be3a79356f50eb6c88a2d2cf4df942e1aa422827097092` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-array-element-positive.json` | `1f5211a4e9578d741ac91b1d4d33b432df655650eb4c6544fe2171a736206f7d` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-negative.json` | `36ff6ee8a3dddedb28b07c2b4b2a8b97b5519e1a1a8695456927d5d8ceed865a` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-branch-join-positive.json` | `6c18f671b2f4552db6b1a9eb14c3ca04d70cb6c6f72f95e286ad6e1001209487` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-negative.json` | `9692958b52ec58e3253315b5b625e34c9de784b2f9c364ec6dbb3c9de72b56fe` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-call-context-positive.json` | `fe82833051b5d591a844b57791f5f24cfd3e065df281304f2d126ceef538162c` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-negative.json` | `f6ab2260f419952404cbd94a56408e37084b12f83300272804173952ebc2c0ed` |
| `dfb-template-chal-callback-registration` | `dfb-taint-c-callback-registration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-callback-registration-positive.json` | `a5cdda9f6a539b62d40271bf2a2dc9695b30e24a6111d8c9f6b65010599ba464` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-negative.json` | `a94a40527cf61d7f9fe3814fa78e5864a8eaf39d043a2483357e4b29e7e48ad7` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-c-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-context-pair-depth2-positive.json` | `ced9fd5fc7c47a401a9d2a53c964259e686094d12364ccde3269b632981363d3` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-negative.json` | `b3ac42bad6c1800f30fa20d92fe02fd71b736ce7c22db07adb5a7b6a96475e92` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-c-deep-relay-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-deep-relay-chain-positive.json` | `aea1fc0a2d9b8bc7ccdb2177c3cebd45b945dac94a99a3994fba43c74af61977` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-negative.json` | `1886b55b6020b76ab4d1e9f44b3f99b6f63a996e111e52c1bce3668fd7a9e8f1` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-c-dispatch-table-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-dispatch-table-positive.json` | `40dcbff9e2b9589bad1d030d9ef13e45b3c97ec2fe5142d52ac02b26ae8b3089` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-negative.json` | `2e0b9b3a5bc159bf968389d4f5ea721ce20507a5d935e5ba206b1286e23e4f70` |
| `dfb-template-chal-element-object` | `dfb-taint-c-element-object-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-element-object-positive.json` | `e3e21ccbba2e90c013602c4c4d318660af2cdd12fff34ce1552039ca658e8ca9` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-negative.json` | `ab715a5c581849d8e94c1d5b2240cf00566fda5707798355b1328a2b9ac2d71e` |
| `dfb-template-chal-function-field` | `dfb-taint-c-function-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-function-field-positive.json` | `e82ea1230f90ac3ec1acc2f8eb77ceaf89828f35af10ed68f3aa681f203210a8` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-negative.json` | `efc967b80a2790fa02815bd7dbd28e3271d3b6d83b22ad2dea0897ad9ee7ed9c` |
| `dfb-template-chal-map-iteration` | `dfb-taint-c-map-iteration-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-map-iteration-positive.json` | `db8f7edf6252b10a213b0d3b7830faaba90a272a7cae137c6d2ab71154ea56d8` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-mutual-recursive-transform-negative.json` | `d5bc2d32fb5b3b22b4641c438b9965816b10b49fe1e8d1d8043aae0bcd7dde54` |
| `dfb-template-chal-mutual-recursive-transform` | `dfb-taint-c-mutual-recursive-transform-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-mutual-recursive-transform-positive.json` | `9b01e0fb3201974cf2c20bced13e30a7515c7651daf014cf84999609a246a516` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-negative.json` | `d19b09b3daaf7c2f123dd36b1370ebf41558f890056f9781e6d3828645bb0fc8` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-c-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-nested-access-path-positive.json` | `9e4cc87aea3534498b00833b4d6dd79a3a56194cbbe9aeb6d6753e0ed68ce491` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-callback-transform-negative.json` | `384f96eabf2d039deaa9d978cce21cf628293deb1964537aa668e9194efbe087` |
| `dfb-template-chal-recursive-callback-transform` | `dfb-taint-c-recursive-callback-transform-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-callback-transform-positive.json` | `37857956373ad2a88468891f4b642cee76f70432ff10c4d9fd1af25e7e67496c` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-negative.json` | `55bae6c864ccb2d853441a2d44da65bb40749398225c91ca4035cb861468c9a8` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-c-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-carry-positive.json` | `1a69a58fddab86e27a98f8a32d4192fb360e14c75c29d0702f9f518fee1521c7` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-heap-unwind-negative.json` | `a8fd591a3785cb1e5a4db0b111863868238cab624b4bba2dca3e74d5c274641b` |
| `dfb-template-chal-recursive-heap-unwind` | `dfb-taint-c-recursive-heap-unwind-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-heap-unwind-positive.json` | `3ea05caf6c168a5b67393b18b2e78005f05c21fd9bbec4625bc1651de438d38e` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-payload-transform-negative.json` | `b63d97842abf0756a06db45551e8f3f4c63caaabb77a55022e7a35075f33c068` |
| `dfb-template-chal-recursive-payload-transform` | `dfb-taint-c-recursive-payload-transform-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-recursive-payload-transform-positive.json` | `d64a58707a59113c2dd7a7e1f269cae94c963708056c8446473bd894e8b71add` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-negative.json` | `ff81b6f8942918560ee9e41868f64be23c9a0e7e41d187139789d91e3cb3ed72` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-direct-positive.json` | `1c30b369b11c09007582bb028ea99da7c29930778b49038f6b7396677472f3c3` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-negative.json` | `d64e55d904ac27853fd2be1d6a994bce88f6fa7ffe8c3a305e9d0d6aacdba503` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-infeasible-branch-positive.json` | `1b62a3076458ced30aea0b75db693e8940753e79a4a8b082dfc279f3ae3d6d81` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-negative.json` | `561d0ad8ec92ebbc20b481b55719c1193ee89c51cab734b969d8490fb13c53e0` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-chain-positive.json` | `f9915b70ef6e6f7fefe7b47e186a5bb118a0d788af82358ec7889bd903cd2fef` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-negative.json` | `98b63e342cc3a53c7e3a5517b4d9e2acec0ddf82dda26af8a71d7b0d02445c26` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-local-overwrite-positive.json` | `969d29f858d80a8ede485387cde310209b41aa7d1e1fb9ebd785d60c7dc540cb` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-negative.json` | `0ad9a78cc8027d02c98521e1fb842703456ddc2ff2c018c731494de638293251` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-loop-carried-positive.json` | `2abfc405e81162088273465e90b346264e366e278d407af4eb78edf58e04a21f` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-negative.json` | `f6e0c6b55340d06d43f9ad010799a11df0a156d2028e8975436afcb50c7e8d4f` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-object-separation-positive.json` | `3b3c23451e6c7d25ff8212383ad927f1e7523367c7e2ce2a4fdc05f46d7acc3a` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-negative.json` | `9eaa7ad77de18e8d36303666edd76a81ebb85b0947d17aa1a2bcc19ecf722109` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-one-hop-positive.json` | `5721de3119b321a6327c8ca270f0ad1fb84b0eb629797ccdf896cd869e802a09` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-negative.json` | `aa12f76153dcbeff90e6e7514f7d834cac61ec56a9b96cc0c6ae62118fba87e0` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-return-relay-two-hop-positive.json` | `dde33fb1cd706954da7daa8c2de6e830f15928cacb89b6ec8ece4f9b7e61d6c3` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-negative.json` | `f6807d73ad8890ac88994fcae564367ba96d5323c860fe142579e99fab209e50` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-same-object-field-positive.json` | `994ef4ec6024b807b9c09ed08f2de1becb41bf5f5985ec784fc62ec1ab28c570` |

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
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-c-kernel/dfb-taint-c-error-code-return-positive.json` | `074947b2a33e6d77b798daa892e7337526cdd639b3db5821e161e11086357308` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-c-kernel/dfb-taint-c-goto-cleanup-positive.json` | `ad80d1c576d17050460e600b259e4a259bb6a7d73ed399fc9168a0ff63f1fd91` |
