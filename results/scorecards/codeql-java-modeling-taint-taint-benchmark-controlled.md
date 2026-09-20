# Scorecard `codeql-java-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-java-modeling`: `codeql` `2.27.0` (build `codeql-cli:b47b3e59262c95aff4eeb84ac72d09e25a9c37e9`, adapter version `0.1.0`, configuration `38acb5de67ed39a244c7eb8a9db755ddbcf197488051a5f1ec0d35b65fa30aee`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/codeql-java-modeling.json` (`sha256:666e913802d2ff4402917337b48427089970f87ef61c6e6f2745b75456dfc1b9`, normalized `sha256:666e913802d2ff4402917337b48427089970f87ef61c6e6f2745b75456dfc1b9`). Generated from freeze manifest `reports/freeze.json` (`sha256:582b2589648772926bc7da0a83844eed0450f015c3593fa5f2937c10669f4259`).

## Language `java`, tier `modeling`

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-negative.sarif.json` | `48113e07bc4d2dbe66b8593789300310bb02d57555838126ba80c209b0f71100` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-positive.sarif.json` | `cab6249c10fdae2b10fe49cadc731c8e145a04b4c98bdb2af500805269d897a2` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-negative.sarif.json` | `c49d856f6de03f464003eb4b9aaf323a19e916b8fae20785659b936b4a0c2d2f` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-positive.sarif.json` | `aafa8bcea685b89a3fd6593d0a456ddf1753ab58fcf1e95d74dd11491b1ed06d` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.sarif.json` | `53d526af0612b84034abdac4b7e2964885e06952209d2f5f8b947a8085e5f1bb` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.sarif.json` | `8e558a8d63bd936e900c92f25cc1650fde8e4d9ce826d6c20b04a414b2deb56c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.sarif.json` | `9bfe2097f6492df9673de06e667b887d591613abc118e91f2d687a0a85ae1562` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.sarif.json` | `db5e1849b03f41dadd7bb71114e848f704af2d808e87c09cdbbac263f1b72b7f` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-negative.sarif.json` | `8b08af5ccd8cc0e8833e39ae78464c75ae317d23f9335aaadacbe5ea62f61fff` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-positive.sarif.json` | `9186ed9cc92f0cb88a29ab5d82d71aef5c21fd37d521b50ee011bf3b3021c6ec` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-negative.sarif.json` | `03472fb07df37f3b96a437c3dd63bc79a59d0deae00aabbfe235df7ce970bf44` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-positive.sarif.json` | `ab5c7f1650be4141fd8bfee8d355883d8a0519c4208708ce42dcdf3f78ff300c` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.sarif.json` | `f0af794784ae044c05f8e600cadd03630b2587362d88cb247fc1846c92cdd18e` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.sarif.json` | `486d6f80d2137c26da00329a53bf69ae97caaf6fa7724bbf23e1350474ec9730` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.sarif.json` | `071358f436a695ca1d5ac33ba23303040c4a944dc50c6e68751f4957ece8f866` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.sarif.json` | `a8f9b510d49dfbb039a053ee74bd81932f8a04ee1707889e887120bc60900ebb` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-negative.sarif.json` | `28a5a7f856a08a4b9cd39da639952a59f6a088fda994919a2077c44b7ab3e01e` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-positive.sarif.json` | `69f6c7f1aa53a6a3af4dfbf49bc73ea2b057fd22872025776375ba15f429aa01` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-negative.sarif.json` | `52e2418bda36a097b49a5b3506ab978c5c98e0ebf2ea6e52f7c23e5b35eaea39` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-positive.sarif.json` | `639ec4d6b10da88825218f03915e1e18c1cb9b64700bbc76bd3079d72a22f007` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-negative.sarif.json` | `7e956c8e03295dc6cee3f18a0ac29fc9093f486868641a4431f09620bb021e5c` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-positive.sarif.json` | `b2f65abaf8e52847229dd7d645514f0664a85b75a065684d0c23680e622347fd` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-negative.sarif.json` | `96622253bff0546a14b0a04f77f28c8580d20515ea85746f5b3d11743acb2a80` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-positive.sarif.json` | `e49a499e49cd0b6996ae3b0298e65da1eaa24218730c7d7377123b1c9b65c4c3` |
