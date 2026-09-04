# Scorecard `joern-php-kernel-taint-taint-benchmark-controlled`

Adapter `joern-php-kernel`: `joern` `4.0.617` (build `joern-cli:4.0.617`, adapter version `0.1.0`, configuration `ab10e81860305e492a930e2c2691873b23be25e97e5b354ca785058e09a20025`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/joern-php-kernel.json` (`sha256:f0cbbcf1d95da15be5aed5a7dc802b038202fa0f6b470256762d04793f81e27e`, normalized `sha256:f0cbbcf1d95da15be5aed5a7dc802b038202fa0f6b470256762d04793f81e27e`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

## Language `php`, tier `core`

Outcome coverage: `reached` 25, `not-reached` 33, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 58. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 4 | 1 | 1 | 4 | 0 | 0 | 0 | 80.0% | 20.0% |
| `dynamic-dispatch` | 3 | 4 | 1 | 6 | 0 | 0 | 0 | 42.9% | 14.3% |
| `exceptional-flow` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 7 | 3 | 0 | 10 | 0 | 0 | 0 | 70.0% | 0.0% |
| `interprocedural-flow` | 8 | 5 | 1 | 12 | 0 | 0 | 0 | 61.5% | 7.7% |
| `local-flow` | 7 | 1 | 2 | 6 | 0 | 0 | 0 | 87.5% | 25.0% |
| `object-sensitivity` | 3 | 2 | 0 | 5 | 0 | 0 | 0 | 60.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 2 | 1 | 0 | 0 | 0 | 100.0% | 66.7% |
| `recursion` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 70.2%, FPR 16.7%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-php-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-alias-propagation-negative.json` | `b3c9555dd2347613b57ca43afaff462ea67fd37189e3e6ff3a67478de568e7ee` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-php-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-php-kernel/dfb-taint-php-alias-propagation-positive.json` | `bbb435e079e2d8380bd081d8f8aca0e1f714103998f5cf4672c97d15293f0a9b` |
| `dfb-template-argument-position-separation` | `dfb-taint-php-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-argument-position-negative.json` | `d7ac8568ebca6fb7f070c7099549ef52130429cfcf738a09264a29acfdfb40df` |
| `dfb-template-argument-position-separation` | `dfb-taint-php-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-argument-position-positive.json` | `4885ce82467cd96cb51badd36b39815953e7cd9c421ee65c6fbb402a6f97b249` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-php-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-expression-negative.json` | `a5aec2c66eb457006f40f17f826ac8697961514f3b04e0b723e72cc172e46307` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-php-expression-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-expression-positive.json` | `bf21d753408584a5a6fee9aa67180307886b07c1553205d94872827392f5fb1b` |
| `dfb-template-array-element-separation` | `dfb-taint-php-array-element-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-array-element-negative.json` | `b48c8b046792fe338dd57abb44cfb61f6c8a1afd4ec972f426ca69722538e6ea` |
| `dfb-template-array-element-separation` | `dfb-taint-php-array-element-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-array-element-positive.json` | `d44598b530e56e1ce1e08a5b4485c45807ed33aeb74c7f9958a3090304eed326` |
| `dfb-template-branch-join` | `dfb-taint-php-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-branch-join-negative.json` | `e130d167f51e6ed2c35609f7824f0383097e8832ea2cd727e27a5238c3604a71` |
| `dfb-template-branch-join` | `dfb-taint-php-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-branch-join-positive.json` | `d2e7fb1323dc61cbe6cf6b99342df323e59dcddb8c6af5aed4c98062bbc8e19b` |
| `dfb-template-call-context-separation` | `dfb-taint-php-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-call-context-negative.json` | `ef971612c093e116d3c39f95fb7d8f3593fe2a39d6b46aa3083e2e0fa17fa618` |
| `dfb-template-call-context-separation` | `dfb-taint-php-call-context-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-call-context-positive.json` | `862990282e9711d64348de2ae4c18fd28b522e577293aa6da3c9cdccd2c16404` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-php-anonymous-implementation-negative` | negative | `reached` | false-positive | `reports/raw/joern-php-kernel/dfb-taint-php-anonymous-implementation-negative.json` | `2fcccf4998002216414566e57355509860f914a069751434511ef6679ccec7c7` |
| `dfb-template-chal-anonymous-implementation` | `dfb-taint-php-anonymous-implementation-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-anonymous-implementation-positive.json` | `a4c88fccce959abbfa3d53bb17b8fef2635eae50d80003f47925aec977817c0a` |
| `dfb-template-chal-callback-registration` | `dfb-taint-php-callback-registration-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-callback-registration-negative.json` | `3e312b22312ef6c8173d70d3aed516996d50202e0c97a9f0196f39e22dff6105` |
| `dfb-template-chal-callback-registration` | `dfb-taint-php-callback-registration-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-php-kernel/dfb-taint-php-callback-registration-positive.json` | `8cab2b92a89d7e027fdb6bd9005d9a3bb407f649886fc8983f00b91edf711a2d` |
| `dfb-template-chal-closure-capture` | `dfb-taint-php-closure-capture-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-closure-capture-negative.json` | `196a5d1fc9e4972bebe64b5d8ac7fc6a4661ae8a1643e78d229ab9ca3ee7143f` |
| `dfb-template-chal-closure-capture` | `dfb-taint-php-closure-capture-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-closure-capture-positive.json` | `629046e12cfb07ab9765ec3828826f0d8674c7f14a954f5af77ec19764bdf75c` |
| `dfb-template-chal-computed-property` | `dfb-taint-php-computed-property-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-computed-property-negative.json` | `e12f342fcb153e271cb26f50c65ffcc9c52339fd713b38a719ebd3e63000d459` |
| `dfb-template-chal-computed-property` | `dfb-taint-php-computed-property-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-computed-property-positive.json` | `96933eecc92132a1bf4d7ba290171da067f7b17eb66af49b1925833566d47697` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-php-context-pair-depth2-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-context-pair-depth2-negative.json` | `029e57b49d4a1b56b6c082d4915a291f95ddf87f07a0ba07df2a750b997d9835` |
| `dfb-template-chal-context-pair-depth2` | `dfb-taint-php-context-pair-depth2-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-context-pair-depth2-positive.json` | `17080444d352300341072526303515358cd7564b4c1eda111a903bde5d5bf3c1` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-php-deep-relay-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-deep-relay-chain-negative.json` | `0a228a52b29afbdc3275e9aa24bdbf78bdf14d2719494852704f2b62e5727d82` |
| `dfb-template-chal-deep-relay-chain` | `dfb-taint-php-deep-relay-chain-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-php-kernel/dfb-taint-php-deep-relay-chain-positive.json` | `452083b47bb057500921f9adf83c3be6eaaa5afc1e776333e9656bcbca22a385` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-php-dispatch-table-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-dispatch-table-negative.json` | `9ecd8f26183eae352debad6aa21b5668fac2d6d657dbd990d52bd686ba3dd54f` |
| `dfb-template-chal-dispatch-table` | `dfb-taint-php-dispatch-table-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-php-kernel/dfb-taint-php-dispatch-table-positive.json` | `95f17b6e2cf639710dce14bf177b57ae9a1f2a54f48a09f70ab45bc5961500fa` |
| `dfb-template-chal-element-object` | `dfb-taint-php-element-object-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-element-object-negative.json` | `f046ea0b6bf28fff6b0d38afdc57ede82ca90e49ba303db6492922e10a44b6b6` |
| `dfb-template-chal-element-object` | `dfb-taint-php-element-object-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-element-object-positive.json` | `2d05354c014984bdc04bb5e650e6b8421719f5101ed7e0eb65a81b3eed2a1767` |
| `dfb-template-chal-function-field` | `dfb-taint-php-function-field-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-function-field-negative.json` | `1b4db3a0b5b4e45d93eb339197f0a87e69b91b86af6688083d42f3289e230f61` |
| `dfb-template-chal-function-field` | `dfb-taint-php-function-field-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-php-kernel/dfb-taint-php-function-field-positive.json` | `1353341be0e36c67b5176a18bb9a165c729cd7aaa3df9c3fd6bb128f3b099b28` |
| `dfb-template-chal-map-iteration` | `dfb-taint-php-map-iteration-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-map-iteration-negative.json` | `4e6bf2c7b874b16030020172987137b36ce2fe0074ccdeacc11bccfc39aaefa3` |
| `dfb-template-chal-map-iteration` | `dfb-taint-php-map-iteration-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-map-iteration-positive.json` | `db5f0cdee7efe61d2842c16f2282bf9fbbac177a527b5635a45063abdccd6149` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-php-nested-access-path-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-nested-access-path-negative.json` | `70735bceb62f9b96e9a9ca00bc0bc02516d940ce3768b93ace60296c724b3181` |
| `dfb-template-chal-nested-access-path` | `dfb-taint-php-nested-access-path-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-nested-access-path-positive.json` | `7250b87f5e1cff7742dfa9ac15e20ed8e3c92540ab8388104356d36584d2e894` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-php-recursive-carry-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-recursive-carry-negative.json` | `1988d4a58e46daded150556f5785e18dfb738334f456c2868586f56fb65ed381` |
| `dfb-template-chal-recursive-carry` | `dfb-taint-php-recursive-carry-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-recursive-carry-positive.json` | `bec9e0ae055a74e3ab1c061dc1a9f7613d93ac6def93b961de0606d0f150e32d` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-php-reflective-invocation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-reflective-invocation-negative.json` | `829e712005f2db00cd793a96b010d634cd06b0020c16785611074237dea28450` |
| `dfb-template-chal-reflective-invocation` | `dfb-taint-php-reflective-invocation-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-php-kernel/dfb-taint-php-reflective-invocation-positive.json` | `0f0bf3e9e93f1622db3c3bad881741f22313dbd7e43936a08bba5d1bbe953ef6` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-direct-negative.json` | `e36b4a7652dbd726f3ea62736604d72319fac0c6637d15a57de173e2c868d23e` |
| `dfb-template-direct-propagation` | `dfb-taint-php-direct-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-direct-positive.json` | `db1bda420992c4aef97f9fc54c33a7c912b0fa4b1c4c7cd3562ac938aa8681aa` |
| `dfb-template-exception-catch` | `dfb-taint-php-exception-catch-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-exception-catch-negative.json` | `1eb59acb997a97b49fd0d5988f759c548553ef7eae2b8a643d398c686848daaa` |
| `dfb-template-exception-catch` | `dfb-taint-php-exception-catch-positive` | positive | `not-reached` | false-negative | `reports/raw/joern-php-kernel/dfb-taint-php-exception-catch-positive.json` | `a13fc433aaa4e64eaa574d923f0320bb30a0a068f1ed080a7b40854805c9a975` |
| `dfb-template-infeasible-branch` | `dfb-taint-php-infeasible-branch-negative` | negative | `reached` | false-positive | `reports/raw/joern-php-kernel/dfb-taint-php-infeasible-branch-negative.json` | `6c5a13987674606724254bcba7bedff938680f50512171158e3ec091ee355d4e` |
| `dfb-template-infeasible-branch` | `dfb-taint-php-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-infeasible-branch-positive.json` | `1768825a614e714c8e06ff35680e32ac1e1f1fa52fa9aef0663e1b18e94d681b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-php-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-local-chain-negative.json` | `8cb00320c61fbe784cbf2afaa549f379fa6f60acf23bdacb424271d1c48d370b` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-php-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-local-chain-positive.json` | `47a22d5d05f2af766b6918b497fe83daf7ba167d10e8b0726fcae4cd9833312c` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-php-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-local-overwrite-negative.json` | `dac17660e6f362648dfa90b65628c93ef02b3d56e358a9575e3fb9e634899084` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-php-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-local-overwrite-positive.json` | `6667b48906e6b82d47974705d5484a8ef33b65e5e62868780c235b31bd5f0f8c` |
| `dfb-template-loop-carried-kill` | `dfb-taint-php-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/joern-php-kernel/dfb-taint-php-loop-carried-negative.json` | `c6e8c5563d3f28a60ef19dc8e41ec446bdfe831f6d048a8d3101b6bbaa376099` |
| `dfb-template-loop-carried-kill` | `dfb-taint-php-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-loop-carried-positive.json` | `5989ed4022f2d27ad7653123a06604076c49e0f604173998f2fe4266a230aa66` |
| `dfb-template-object-separation` | `dfb-taint-php-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-object-separation-negative.json` | `3133b2d36cda7b8b74da6ecef61e72b98e95d26f24c727f7286157647093db82` |
| `dfb-template-object-separation` | `dfb-taint-php-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-object-separation-positive.json` | `2924b8fa076a39f04b91f7426e725ce7537767980782793f49b99393cc9249a5` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-php-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-return-relay-one-hop-negative.json` | `cd446055e6512facfc799817f466395f3aac6aad23ebba9ed40665c1c2f25a05` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-php-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-return-relay-one-hop-positive.json` | `0337553694e98aa92c742075e286680f45fc658c12afb7f3750288269753667e` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-php-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-return-relay-two-hop-negative.json` | `4bd2211abbc57129a581ab02522a0319c9f463ec63fd483ecd3a73dcb6de14c8` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-php-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-return-relay-two-hop-positive.json` | `f41438039bf88bcd692c217f9229a24bb8ef01d097c4ca3d95b92113e29d1ce9` |
| `dfb-template-same-object-field-separation` | `dfb-taint-php-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/joern-php-kernel/dfb-taint-php-same-object-field-negative.json` | `0a9a2a65bb28474f49534782a004c1831c6c2ebaadf8337ce6f4e8c15bc0f4d6` |
| `dfb-template-same-object-field-separation` | `dfb-taint-php-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/joern-php-kernel/dfb-taint-php-same-object-field-positive.json` | `3cc41c9bcbb49233a13583ad4d97b33ab9bfd7444060c0f492ec88101d03a42a` |
