# Scorecard `codeql-javascript-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-javascript-modeling`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9`, adapter version `0.1.0`, configuration `50f4a31741fd93420f8bdad4cbdea9f07dacda897641e12fdcdcdc8d7810e910`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-javascript-modeling.json` (`sha256:8a2e516b91eb6b9753d970b60cbfdb75e3894822358a6e7da6b8524baf27c5d6`, normalized `sha256:8a2e516b91eb6b9753d970b60cbfdb75e3894822358a6e7da6b8524baf27c5d6`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `javascript`, tier `modeling`

Outcome coverage: `reached` 12, `not-reached` 12, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 4 | 0 | 0 | 4 | 0 | 0 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 6 | 0 | 0 | 6 | 0 | 0 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 100.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-negative.sarif.json` | `061e323bb265b4d509f077c60cf329f292775efab2b59b0a595ff1f77650c109` |
| `dfb-template-model-declared-sink` | `dfb-taint-javascript-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-sink-positive.sarif.json` | `6c73fb70c31012c2ad324b887135211105e439d76564e68dd3cf9e35fe206d6a` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-negative.sarif.json` | `b8372ca0fc27f3b04e1851b0c9bf2b29948d78023e9db1958b918c531cdbaeef` |
| `dfb-template-model-declared-source` | `dfb-taint-javascript-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-declared-source-positive.sarif.json` | `52203d1bbb682244a00f84f3cfa2ecb76f423965d8f2eeb6c76a1185d5a0defc` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-negative.sarif.json` | `e6eb4120459dc514a1da3ea5a6797e4cf71b59b22244b1b547aa1999bb66a7f3` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-javascript-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-parameter-positive.sarif.json` | `5ab93cc8fbdb9768e595a8babfb6162b09f684d14fc2b76b2134aff28271c1aa` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-negative.sarif.json` | `72efb1178dceb7d870e6182d999ed9ff6c7172864e4b2449afbc8747f9ad50a8` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-javascript-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-entrypoint-selectivity-positive.sarif.json` | `0d033cf7d07ff08a4e9d21af15a1f14fa50b3dd68cba12957156a26d57e87b49` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-negative.sarif.json` | `113ac10c9b5655cdde5582fd13b0e10c6b507f5c4fe390007839b03b5fa64a29` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-javascript-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-opaque-propagator-positive.sarif.json` | `da77fb031545ba1f2707bf9a04ed42a290638d9af9a9eda3ba4175c615468c0e` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-negative.sarif.json` | `df55cd050eb6f353dca3c93d1a9a0f20449dc5efc90cbe8ef81df8a69fbbb681` |
| `dfb-template-model-propagator-position` | `dfb-taint-javascript-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-propagator-position-positive.sarif.json` | `99314c083b95d8ad59195b2b34334b7fa60181fcc10075b4d8326ef62c592cf3` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-negative.sarif.json` | `7fae78509324f7865640b988f1eb42cd3988c96695b3f3468a870fd2c6271669` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-javascript-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-kill-positive.sarif.json` | `6101ef98d456bc6f71d73980843df78a0ec6f3bb3045bb2e6d847b52ae6bf8a4` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-negative.sarif.json` | `72491795c6f5cfc06864e049eb0d35aa667f063186999ecddc2453bed0949f22` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-javascript-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-sanitizer-selectivity-positive.sarif.json` | `1916b034920b906701d99e4f86ea4720f6201e16e6896e8de0529f35dd6e8a86` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-negative.sarif.json` | `3e188043ba04c77e6944b194097a9ef9f29f01137ce1b474080cdf5b7d9ede5d` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-javascript-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-roundtrip-positive.sarif.json` | `a0bc7f0fdedffa2b839c128daaebe165bb915b5eb520ef02c64c9fb159bdfe80` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-negative.sarif.json` | `304b3f5a57c2e1af84c13e291721067183159aac41b2cf1d4e7bd73ac24eacbb` |
| `dfb-template-model-store-separation` | `dfb-taint-javascript-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-store-separation-positive.sarif.json` | `1d18a77081029fa361762c41c6e1b899160a35dedf094c22ebc5eda2a3da7ace` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-negative.sarif.json` | `4c810e78912cac5fe700943d5713c684c9397954968e1fb7d15d4882fcb36efe` |
| `dfb-template-model-summary-field` | `dfb-taint-javascript-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-field-positive.sarif.json` | `639f232755a0f9b7f83b2a0d735ea82317509ae0878c05ebb6edcd13fdd57b42` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-negative.sarif.json` | `b1b485379d43005ec1d523ec297e3ec6d0da67b68fe3eafdf63b38e5a8eda885` |
| `dfb-template-model-summary-through` | `dfb-taint-javascript-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-javascript-modeling/dfb-taint-javascript-model-summary-through-positive.sarif.json` | `3f68aa208971801bb693e59cc597a23093fc801e93eb22e36ad70e27d0fbc7fd` |
