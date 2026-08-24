# Scorecard `bifrost-cpp-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-cpp-kernel`: `bifrost` `bifrost 0.10.5` (build `728ac69ab93224151c6c951b23d2f5bc681d8558`, adapter version `0.1.0`, configuration `b29775f28c44e0830155def3030cb36f7c7f8906c440dc18af2be6f7ddbdc22e`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-cpp-kernel.json` (`sha256:ab5d332588a9a3b7e5ab26ab09b87de2551f60fef164cc3b2c8f834845def169`, normalized `sha256:ab5d332588a9a3b7e5ab26ab09b87de2551f60fef164cc3b2c8f834845def169`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `cpp`, tier `core`

Outcome coverage: `reached` 1, `not-reached` 1, `inconclusive` 30, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 8 | 0 | 0 | n/a | n/a |
| `local-flow` | 1 | 0 | 0 | 1 | 14 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 0 | 0 | 0 | 0 | 6 | 0 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-negative.json` | `5e4468af74c6607f34c74be392542048df284d8326f7e33eb0b49e911e1b498e` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-cpp-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-alias-propagation-positive.json` | `e484c7b031d57c2345094d0a0f42abc854e54f7e019a0165b6a2f3534ff7f5c1` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-negative.json` | `e2bba7853ef471dc55bb88c90783630ad223008632af6acf3f9e40da867f23ec` |
| `dfb-template-argument-position-separation` | `dfb-taint-cpp-argument-position-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-argument-position-positive.json` | `b48f4c044eef0c3a14bcefb191503dda1952b1d40e876c5d3f4d63f7ee3943ca` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-negative.json` | `e6572788d7d4a373a1bc0ceb37d7464872df73f9bd05c4e9f0cd0f286a451531` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-cpp-expression-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-expression-positive.json` | `3f6d7adad22100cf4dbb3dcd70b36ea17ec9b4a1c0710df0d10becafac55cc6f` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-negative.json` | `071ab850f3fa35947c9558992857a2193f0f1cc598ab01e6d9dd80098cefa10c` |
| `dfb-template-array-element-separation` | `dfb-taint-cpp-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-array-element-positive.json` | `4c4379e0272c5ef73df3b160cd1cde22bb4f25832ce447f320e457f50310c7bb` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-negative.json` | `87f8270f8950598102907332c887d2029c73c7c5b74c6aa55a5415d18af61b50` |
| `dfb-template-branch-join` | `dfb-taint-cpp-branch-join-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-branch-join-positive.json` | `11b91e083de06fae48ab5e90a3e0e0c2a7938b08fabcafa96d9468dc9cec3a95` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-negative.json` | `b91cd044f047c872ef90567aa3e501e29e21cdf97a1d995d3b97f46d97e7cb53` |
| `dfb-template-call-context-separation` | `dfb-taint-cpp-call-context-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-call-context-positive.json` | `c27d41e616f3904e033312508c7ba48ee56e5743b3d115bd20691418222b0896` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-negative.json` | `6eee3b9fc16ca85ed84cfdb039f38054247333d14d805193e00cd79332f9213f` |
| `dfb-template-direct-propagation` | `dfb-taint-cpp-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-direct-positive.json` | `9d723530ba6963d9245ff1d701ba589975f1041e45ee306ee05549a3deb0bf99` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-negative.json` | `314353afcc74b6459e1c511392c55fba5d19ab899b828a5882049cf00169cd94` |
| `dfb-template-exception-catch` | `dfb-taint-cpp-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-exception-catch-positive.json` | `91f414f58b29125764ea78cf2c2a3431258acf6c23fa5833c1861e0775162bb9` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-negative.json` | `63b2ecb90f943cdd5c0859fa91cb5c1e225da28a8c15c6a3adf3aee27ddffe73` |
| `dfb-template-infeasible-branch` | `dfb-taint-cpp-infeasible-branch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-infeasible-branch-positive.json` | `fd2d470ba5bb2f9e5cb45d0823074970d7ac408ef2c0b68f0b01325393c72f88` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-negative.json` | `a90f3a353f11be1d8dd4409a24d817488f4d29022471d60e616c1ca12ab697e5` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-cpp-local-chain-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-chain-positive.json` | `2223bede910635198c36f8057bea10bbe8cee3b7a89573c2fc57bfcf5fa374da` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-negative.json` | `a42cd4a4d6427428ee9735d567d546ef51a9f0d86940af628781fcc919824d81` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-cpp-local-overwrite-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-local-overwrite-positive.json` | `611dca8e2841a2a2d65d29e75dab3932bf39cfcceac6eaa4d28d578b14557098` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-negative.json` | `27e113596e218f43c00b39b3e5377ae9cf6d4d7f16fdceda16aafcd5b0ac8f49` |
| `dfb-template-loop-carried-kill` | `dfb-taint-cpp-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-loop-carried-positive.json` | `7c0b4ebd95643b9060c66d6095149317d44c0078e2ed8d37451371d1b41b3f8b` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-negative.json` | `d011044bbc605fe4077284d81c0414369d596104adb54ff18645b010a6fbd117` |
| `dfb-template-object-separation` | `dfb-taint-cpp-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-object-separation-positive.json` | `38bf07b750cddc7b55c7ddce0e31515b6fb9ad6046ed2baeabb232df45bed1f8` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-negative.json` | `bb363df97a7cf36733726e5f17aa1ae21449380071f6886d1a65cf85f8f0f81d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-cpp-return-relay-one-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-one-hop-positive.json` | `f6021a41c127a5a87053aaac18339ac0d036698ebac56b08906190f42b1e3f09` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-negative.json` | `fa1a4993ffa8714eeeb000ac10bae2b9398d7699473f2d086a87235fe903cad3` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-cpp-return-relay-two-hop-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-return-relay-two-hop-positive.json` | `d0b881d9d3faeaad6afe74aeac070edd340a26201e6b5cab11995e27d28b4b69` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-negative.json` | `c4808792d30c2328ca029b206358f011944c870d258d865f5d746e6bffc1f248` |
| `dfb-template-same-object-field-separation` | `dfb-taint-cpp-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-cpp-kernel/dfb-taint-cpp-same-object-field-positive.json` | `225780e8b63c9953c1cc2a73121898241e2b829c96fb75af9b5007211dd780b9` |
