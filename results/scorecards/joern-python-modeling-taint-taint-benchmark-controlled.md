# Scorecard `joern-python-modeling-taint-taint-benchmark-controlled`

Adapter `joern-python-modeling`: `joern` `4.0.660` (build `joern-cli:4.0.660`, adapter version `0.1.0`, configuration `f7f9d9d53572b098556aa86d16b3e9a0b3e9c7a4226526090bb03fd61bbf1eb8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/joern-python-modeling.json` (`sha256:97c240aa2b3d5cb5cff6056db69e3a632c6e6f41fb57d3cb38c224d31739ab51`, normalized `sha256:97c240aa2b3d5cb5cff6056db69e3a632c6e6f41fb57d3cb38c224d31739ab51`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 6, `not-reached` 10, `inconclusive` 0, `unsupported` 8, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 0 | 1 | 0 | 1 | 0 | 2 | 0 | 0.0% | 0.0% |
| `interprocedural-flow` | 0 | 2 | 0 | 2 | 0 | 8 | 0 | 0.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0.0% | 0.0% |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 50.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-negative.json` | `0046499099821708b049cb94eb53bc92040c6a624b52a747a3d896d0886ad4fd` |
| `dfb-template-model-declared-sink` | `dfb-taint-python-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-declared-sink-positive.json` | `b698a51775265c50d9c6c11f5797399940f029ce576179cc02127248d289fec2` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-declared-source-negative.json` | `e0ff61479ae09c6bb073e322c304ffcfc0051fe6cc27677480aca6292a213f15` |
| `dfb-template-model-declared-source` | `dfb-taint-python-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-declared-source-positive.json` | `1b3637fb72c368c2a49d333aa50214034297c1d189a2951b9aa1ed81686c13d0` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-negative.json` | `5938dad9159dc53fe46ce3eee67f4e6be477ec1714a3cc34ba79e81cc7ed0676` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-python-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-parameter-positive.json` | `12c5bf02e3867e880c1fbc3008d960bb73c5c65b28a745c9506566d72df999a0` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-negative.json` | `d6febf52f233b2e347b0fae01e0edd5dbc7f83733898a2eb294a89cf602a8758` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-python-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-entrypoint-selectivity-positive.json` | `7f6a3bf5042fe9e3bf48f0a432727d9b7afeea26c228ad3aab23535b50687d50` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-negative.json` | `ed885316649eb0944799c73b70df6127b1f9fdbe871d1cc4e5ca4c6f701b699b` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-python-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-opaque-propagator-positive.json` | `51241feaee2a787f02a0fb8d358dea7f302eefd58023b10334016bf78a2e480f` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-negative.json` | `7665ddcc72737f44cc149c423dae84d8fddba96c32082505fe10e7efce2f2bb3` |
| `dfb-template-model-propagator-position` | `dfb-taint-python-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-propagator-position-positive.json` | `7054291750b49f7de5536e289aef0bcf21eb2eb17aaa975ec37ee5f0208d75fb` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-negative.json` | `9d3db776b26404a0de00b7e4f565260644d99da632c7d1504bc66aa6b51a3d8f` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-python-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-kill-positive.json` | `5eef77f3f4c88a5242f88f3be157bdb3ed4dde2d06f3039b577c7176103f44ef` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-negative.json` | `5e28ef6ef616f0e5033cec319681c6b4afcc5a55f0b8d33a561c50abc30f4d74` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-python-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-sanitizer-selectivity-positive.json` | `cb91783d9d9ce40e20a109866089850e234c3af317e0f7e28edb827e42ed6181` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-negative.json` | `8a98b77ad2524796a51015502ec766b66096421124e26c568f4eb81bcd13f82f` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-python-model-store-roundtrip-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-store-roundtrip-positive.json` | `a51ee83c595a5295803f3236772fec08c9c90fac1ee44b107599f83eca1078a0` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-store-separation-negative.json` | `9264b5ba02ea17ee64b053c97e2172c9ab784287d0c9e4e9720b72b769a9c857` |
| `dfb-template-model-store-separation` | `dfb-taint-python-model-store-separation-positive` | positive | `not-reached` | false-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-store-separation-positive.json` | `8b9072e2a5b992796792a768c74757b6b4abb12b479577180ce2628384ddb19f` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-summary-field-negative.json` | `bce35f680b8e05e381e7aeecec2b52bf91230c356ff094dccc7b2c9e86184718` |
| `dfb-template-model-summary-field` | `dfb-taint-python-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-summary-field-positive.json` | `121552f66c0a651617dcc2893c6e1b575ebe410fc90be4529d9562c346a59288` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-summary-through-negative.json` | `9ddfb885ea695a8f3c1d59ff13f66c29ff128da474e5364df341eaf205f36f0a` |
| `dfb-template-model-summary-through` | `dfb-taint-python-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/joern-python-modeling/dfb-taint-python-model-summary-through-positive.json` | `f37cbc05f8491fca31005396de546c7596a8d1aac049015582034c9ccc1310bc` |
