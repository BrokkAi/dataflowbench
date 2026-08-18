# Scorecard `bifrost-python-kernel-taint-taint-benchmark-controlled`

Adapter `bifrost-python-kernel`: `bifrost` `bifrost 0.10.2` (build `c2116609f5fc1be318c8fb76fb83763cf326bab6`, adapter version `0.1.0`, configuration `8ffa260f17d570afc01df63034130d26f19afe260949b2fadee3f27af6f26a98`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-python-kernel.json` (`sha256:1d86fd4c245c4f86c6d75f3f1a7847532b521e258a81c560d163fafd152d2d55`, normalized `sha256:1d86fd4c245c4f86c6d75f3f1a7847532b521e258a81c560d163fafd152d2d55`). Generated from freeze manifest `reports/freeze.json` (`sha256:c8ba343f2db9a8c1cac5570a414bf497c85bbe11d29730639575c9ba3bb70912`).

## Language `python`, tier `core`

Outcome coverage: `reached` 12, `not-reached` 8, `inconclusive` 12, `unsupported` 0, `runner-error` 0, total 32. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `exceptional-flow` | 0 | 0 | 0 | 0 | 2 | 0 | 0 | n/a | n/a |
| `flow-sensitivity` | 2 | 0 | 2 | 0 | 2 | 0 | 0 | 100.0% | 100.0% |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 10 | 0 | 0 | n/a | n/a |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 5 | 1 | 3 | 3 | 4 | 0 | 0 | 83.3% | 50.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 4 | 0 | 0 | n/a | n/a |
| `path-sensitivity` | 2 | 0 | 2 | 0 | 2 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 96.7%, FPR 50.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-alias-propagation-negative.json` | `d90226375a17fd01647811acd7b9d9417d6409fbd6cb2248ff21a95a0519dc05` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-python-alias-propagation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-alias-propagation-positive.json` | `a057e168f4480377aa483516aaf547dacfb1d554cac09a290e69710b602c7031` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-argument-position-negative.json` | `052b5304c6745b113abf0a8f075b285746a646a8c1d1ad659ed0220f4108576e` |
| `dfb-template-argument-position-separation` | `dfb-taint-python-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-argument-position-positive.json` | `01206377029072f8ac1b5d66093e8253c392163d7acabc294c5993e9c85034bb` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-arithmetic-expression-negative.json` | `7383c7125a347772ea86062c7f6f43475159f1fa402518af7adeb58bcc07c157` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-python-arithmetic-expression-positive` | positive | `not-reached` | false-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-arithmetic-expression-positive.json` | `594837ba6b0035b36c8cfce9cfcbd0d51bc192d5d5523c1c5761bddec1adc7b2` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-array-element-negative.json` | `cbfbdd064b3793838ad30afff79c6637bd847eee916133a46581150ec4805513` |
| `dfb-template-array-element-separation` | `dfb-taint-python-array-element-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-array-element-positive.json` | `cbfbdd064b3793838ad30afff79c6637bd847eee916133a46581150ec4805513` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-negative` | negative | `reached` | false-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-branch-join-negative.json` | `2e9527bd6a69c257079d1c596cfa31d47b2c891b66a51c86b13d00e679aedcec` |
| `dfb-template-branch-join` | `dfb-taint-python-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-branch-join-positive.json` | `6fe8d582f69901a825a1b9ebb4ddcd85274a3e2d553f6e455543a13f164ac17e` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-call-context-negative.json` | `c1b45142583effc7f910c987a234cc189bd680a282286ed21c60c76762fb43cc` |
| `dfb-template-call-context-separation` | `dfb-taint-python-call-context-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-call-context-positive.json` | `6400757e544e6f12cf34baef7b7a0a5a5e0f81e0e1515600dac0d7bd6c0a9553` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-direct-negative.json` | `70a7b78d8ad4a1f11788d680c4d35abd28091ab4220004bcc9c3643a595cd196` |
| `dfb-template-direct-propagation` | `dfb-taint-python-direct-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-direct-positive.json` | `a3647ed1074deba833fe38d289fc320bd22277e18280584b1647a85819d6cf32` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-exception-catch-negative.json` | `b282fb595820ecb9470b3d8beac2c961685fc49799d3d33e08fee2bbf6fe472c` |
| `dfb-template-exception-catch` | `dfb-taint-python-exception-catch-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-exception-catch-positive.json` | `1b564092afb543c1c40a8c1f406977fbc8dd2b1c8bb25ee4c4edeb3dc9685072` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-infeasible-branch-negative.json` | `62c76b450925b9968a99fb74a8ed7993dcc6a0d212f9bf3a9619d62534611ae9` |
| `dfb-template-infeasible-branch` | `dfb-taint-python-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-infeasible-branch-positive.json` | `9b34f8c804845e3f83b84dd64b6b51e59e745eb866d90665403ba04a3e990a72` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-chain-negative.json` | `6dbeea9a8fbbd6d106f0b12c883b784979a322d5ecefa1be1396b1afe61c7ff7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-python-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-chain-positive.json` | `ac2655fdd5777591cd2a8f734cb8dba9acc0bcab19a70a930300607d560faa71` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-negative` | negative | `reached` | false-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-overwrite-negative.json` | `550f11f167a4ce5c7257f560f8132980a1a488865ea939e817745ce1854b40b4` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-python-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-local-overwrite-positive.json` | `d2242223446db4f3c4f8f2c3a6b0781bbf5bf55bcff66cfe68bf4f0507cbd1d7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-loop-carried-negative.json` | `ec776385a6fef024b49d48bd3b8c5f59a112cdc69cb9ef2612cd9274c98ff76c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-python-loop-carried-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-loop-carried-positive.json` | `a80ae6520d6c84335d4902fc94c0ecc98bf00da98b5d84bc6edf88541b911c1d` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-object-separation-negative.json` | `f3e3d5641b6a1581d6f4f2b741fbb8d410e985ec5f0ec0c346e657162c258689` |
| `dfb-template-object-separation` | `dfb-taint-python-object-separation-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-object-separation-positive.json` | `eb0d22e3f1b44d809b98d1534fd362457204eda3530fb5866db1ecaef69e48e9` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-one-hop-negative.json` | `55a47bebec3438d775576c298a5ff02e125f561a9bb90ea8890a10beb02a3076` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-python-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-one-hop-positive.json` | `2cf3ee39b212e2357b436195d21e367a5e7484b8ac2caee048294ffad74bb49b` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-two-hop-negative.json` | `f3aa91484b3ea0fe1b958528a472484fe834dfd665089261f2291c6154b33a53` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-python-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-python-kernel/dfb-taint-python-return-relay-two-hop-positive.json` | `e5be9d1ab62747e00dd40cac3d4434624ebf72c877d837ac2c7c39ce29b7dfbd` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-same-object-field-negative.json` | `5bff7c7d8452c45bbaf6938b2b63791a3b4d751b814896919577d3fef6f0650d` |
| `dfb-template-same-object-field-separation` | `dfb-taint-python-same-object-field-positive` | positive | `inconclusive` | inconclusive | `reports/raw/bifrost-python-kernel/dfb-taint-python-same-object-field-positive.json` | `81d76dab61f37f0ee416d26ddaeff4352f376fc4c4f1f29ca6ba03a7f2de6886` |
