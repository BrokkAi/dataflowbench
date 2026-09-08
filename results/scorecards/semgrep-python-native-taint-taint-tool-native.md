# Scorecard `semgrep-python-native-taint-taint-tool-native`

Adapter `semgrep-python-native`: `semgrep` `1.176.0` (build `semgrep-oss:1.176.0 — 1.176.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/python`, adapter version `0.1.0`, configuration `d392dc858c5fa5494c9a03e2c5f3136f06ea81bbb635573acea69bd082a74117`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-native.json` (`sha256:ad9dc1a0ab69667d908df04e21a9d40494904ea3bc07b09184b7c9ae7d883d28`, normalized `sha256:ad9dc1a0ab69667d908df04e21a9d40494904ea3bc07b09184b7c9ae7d883d28`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

## Language `python`, tier `modeling`

Outcome coverage: `reached` 10, `not-reached` 2, `inconclusive` 0, `unsupported` 0, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 2 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `heap-field-sensitivity` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |
| `local-flow` | 6 | 0 | 4 | 2 | 0 | 0 | 0 | 100.0% | 66.7% |
| `sanitizer` | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 100.0% | 100.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 91.7%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-negative.json` | `cb2218870b56331a8d078bca144e8439451fc38de0186520ef1f91cca97e28ed` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-positive.json` | `be8b7a381846f9f503c3d1ccb1989b36a6f0ebecf6ac8aae66e115146d2c2340` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-negative.json` | `462cfbdfdb7421b55921467356ecf83bdf7432b8f5800c7e65068c44293bc82c` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-positive.json` | `66f05a8b74004a1c6b8688195647e18b7c7a239735e022a83fc3e8357e2422d2` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-negative.json` | `7e46a3db36819ff61c3e8c260980cf87f28199dee540966378697090143a485f` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-positive.json` | `3b049c3f652fddf7b83995ad9687e8fcebbacb8c1c708de4ee89f61ff142e4c9` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-negative.json` | `c24b4d708ebeac09d5b741fe2cb900e6065e5b56f672349eb4815ab4f37f21b4` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-positive.json` | `d5c038b98692f73d5b7cd7b07a34745c765ff40ae541ebab77dccd02e271c2f7` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-negative.json` | `3974bb228d0777b26baa50a19af0f70e399095d5df2dea356b18c66f3cb2d826` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-positive.json` | `163183210700f334fbf67b6a14cb6594c1679eb73487ee859d1f2fe7fc129364` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-negative.json` | `533c4b64f7af6902fa179f60f15d153862053fededf29282d69a345c8dbf202b` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-positive.json` | `2d1df2ddf9e0f4a19c922e38171a626ef29ba0e1225e4ded375e2fb9af7a4705` |
