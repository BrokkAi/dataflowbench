# Scorecard `codeql-c-kernel-taint-taint-benchmark-controlled`

Adapter `codeql-c-kernel`: `codeql` `2.26.3` (build `codeql-cli:7d097a43199effe04ecd9c6bd3ad9bb02a45b3d7`, adapter version `0.1.0`, configuration `719415b9134dfd43390ffdb76eef45f7ed022f907f22913226c22f93277b62f8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-c-kernel.json` (`sha256:5d4d3f23c90402e214dd9a71ffebbb3ca49190b97a47202d41dce4d6358be6c6`, normalized `sha256:5d4d3f23c90402e214dd9a71ffebbb3ca49190b97a47202d41dce4d6358be6c6`). Generated from freeze manifest `reports/freeze.json` (`sha256:61d0025957ba5f8a8d3ffa6cd2b46ba058bd67fcf2128568a96ff0eb5a1546e4`).

## Language `c`, tier `core`

Outcome coverage: `reached` 16, `not-reached` 14, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 30. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `context-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `flow-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |
| `heap-field-sensitivity` | 3 | 1 | 1 | 3 | 0 | 0 | 0 | 75.0% | 25.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 7 | 0 | 1 | 6 | 0 | 0 | 0 | 100.0% | 14.3% |
| `object-sensitivity` | 1 | 1 | 0 | 2 | 0 | 0 | 0 | 50.0% | 0.0% |
| `path-sensitivity` | 3 | 0 | 1 | 2 | 0 | 0 | 0 | 100.0% | 33.3% |

Macro-average over semantic dimensions: TPR 89.3%, FPR 15.1%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-negative.sarif.json` | `4ef0923534db56a520895f57b55ac63f5040a73815466d589a296c96fa88a847` |
| `dfb-template-alias-propagation-separation` | `dfb-taint-c-alias-propagation-positive` | positive | `not-reached` | false-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-alias-propagation-positive.sarif.json` | `9c18ea00d31eb9f3510ceb8ee62e2d91b85febaf8d11bb56f39e34dc871c7695` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-negative.sarif.json` | `39d115d74a5616478f613c6060a836d68f6abe1d3aa632ad8f3d577e4ad849d0` |
| `dfb-template-argument-position-separation` | `dfb-taint-c-argument-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-argument-position-positive.sarif.json` | `21ff40e6b3f57597f323509add7b77ae5e4f676ded1c002de7fc59e53127d7e9` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-negative.sarif.json` | `b9e11aba583ea7275f17dde3c20593edc1341395b43696dc8cd7292dc44a9cf6` |
| `dfb-template-arithmetic-expression-propagation` | `dfb-taint-c-expression-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-expression-positive.sarif.json` | `f04aa6429074e65113c0aff9b9826c98ae2b46d839a90f26e5e67c52eba8c389` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-negative.sarif.json` | `10586a2e98af1249b3099092cd86420e4faed2171f522aed985ac2d3c21ac0c8` |
| `dfb-template-array-element-separation` | `dfb-taint-c-array-element-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-array-element-positive.sarif.json` | `7b05c88d956cfb8665fd06cea3e47f796d612da3713fe08ed4e3fffa3e7471f9` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-negative.sarif.json` | `62a6ed515084b4fd25d67fbef4f2dc3ff2c392989dbccde98d2a2c56ed1936ef` |
| `dfb-template-branch-join` | `dfb-taint-c-branch-join-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-branch-join-positive.sarif.json` | `94aa05c96e3690370dc60f1f59687ffb9db024b8ea7f6e63afc01c66c8e13577` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-negative.sarif.json` | `7a0408a8a477efaa9d7cf2c55eda0b26b64a8722b60cda8b1eb1abd65bd1e288` |
| `dfb-template-call-context-separation` | `dfb-taint-c-call-context-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-call-context-positive.sarif.json` | `1b549cbcacae8a97b001ad96deac20d7ae023c6f8800a19c4ed7b01eac8e8115` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-negative.sarif.json` | `baef9960a7faed01f4a7f57801a4c2ba3230ba154e960e63f2452639dd048cf1` |
| `dfb-template-direct-propagation` | `dfb-taint-c-direct-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-direct-positive.sarif.json` | `630618bd498df67001f7106f353c79f7fe7bf6d5aee6c6e968cfe30a164fd720` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-negative.sarif.json` | `c06beeb9c44ee3f60671ea4304dd6ee787b7c4d87f560cba8383c68496738091` |
| `dfb-template-infeasible-branch` | `dfb-taint-c-infeasible-branch-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-infeasible-branch-positive.sarif.json` | `6cbf4fdd7b3baf1c3c1317b10a5e100516fd810108488b77839d76bbb62922d7` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-negative.sarif.json` | `6b50f04bce7528d94daa7d40ead35ba84a0815c0300f42d80a78768253ebdd5e` |
| `dfb-template-local-multi-step-chain` | `dfb-taint-c-local-chain-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-chain-positive.sarif.json` | `55516ecc94f5b9b8aa4ae4a90f41d08b97d23b197627abca898b884d94d48d9e` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-negative.sarif.json` | `c9e9202e8281ac2341b59e1912fdcc7bf50040ab46d2cc8675739ff92f8d2ca1` |
| `dfb-template-local-overwrite-kill` | `dfb-taint-c-local-overwrite-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-local-overwrite-positive.sarif.json` | `8a0a714c07834363d2a649e9f93d3d23790746b0de0be522f1a9aa18431c473d` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-negative` | negative | `reached` | false-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-negative.sarif.json` | `2c349f5cc49ddc71872e717c7e1ce3104810c3b3e83ea5cc91cfe53b6e000ab7` |
| `dfb-template-loop-carried-kill` | `dfb-taint-c-loop-carried-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-loop-carried-positive.sarif.json` | `d52b3b903800321d30a4120142a2d6bb6a0998f06bbde7310b72374f0418c974` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-negative.sarif.json` | `da237d6201656a45fae260bda3ec0959ce9728e4b4520dcddd0b6b071e0e1085` |
| `dfb-template-object-separation` | `dfb-taint-c-object-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-object-separation-positive.sarif.json` | `862789b6688ff81351221d31dd7798e269c004198f32a2c6f968122fc519370d` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-negative.sarif.json` | `116a127912df20e7b3cdca60e753a3d039ecb034652cb9e4f54e70405768c151` |
| `dfb-template-return-relay-one-hop` | `dfb-taint-c-return-relay-one-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-one-hop-positive.sarif.json` | `c80c489aabbb18010a3f7f2b349c40896b9d28c276373418f00b80b73d954b75` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-negative.sarif.json` | `7baf054977183e7674410e049c236e3387bc418814a7dbd90a2b22325853c4aa` |
| `dfb-template-return-relay-two-hop` | `dfb-taint-c-return-relay-two-hop-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-return-relay-two-hop-positive.sarif.json` | `6e9e5615a3161b784880a45bc6c324dc6e79463594bfe8c5f8a0662b5c1258b7` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-negative.sarif.json` | `853413d8b97820ee1ea2ae04f88a7eb51e9e1844b4a47e92ccd8a210a29bbe62` |
| `dfb-template-same-object-field-separation` | `dfb-taint-c-same-object-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-same-object-field-positive.sarif.json` | `9be0ec3c63000a2baa64a3e92fc0a82d0d36973274c469e09eac5b5ce7a841a5` |

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
| `dfb-template-c-error-code-return-path` | `dfb-taint-c-error-code-return-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-error-code-return-positive.sarif.json` | `cf80c40f54a31aad305ac138fc76558adf7c7eb4c688b6512a4424c4b59cfbec` |
| `dfb-template-c-goto-cleanup-carry` | `dfb-taint-c-goto-cleanup-positive` | positive | `reached` | true-positive | `reports/raw/codeql-c-kernel/dfb-taint-c-goto-cleanup-positive.sarif.json` | `400a87ebfd4138498fa3cf367faf5458acc37f764870865424a7887690bace8e` |
