# Scorecard `codeql-java-modeling-taint-taint-benchmark-controlled`

Adapter `codeql-java-modeling`: `codeql` `2.27.2` (build `codeql-cli:d7b185e374bfe18c0484dac07a521a810eb9c4fb`, adapter version `0.1.0`, configuration `63e8a86fd492ffbf47b6c13be032edd6d3e345601464b82d2e908568f703872a`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/codeql-java-modeling.json` (`sha256:29ecad78b105c590825e12a35bdf0d1612f3644cd481666a80d04279f656fbd7`, normalized `sha256:29ecad78b105c590825e12a35bdf0d1612f3644cd481666a80d04279f656fbd7`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

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
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-negative.sarif.json` | `232713f5489532c8165192a9f9d770153fe1fcd0cbdb3380651b1b404684128b` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-declared-sink-positive.sarif.json` | `24e0b42d3cb03179eb236bc420dde6aabd4e10b5d5a1cbdfd34c4b69a994d2fe` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-negative.sarif.json` | `4ee573849e8801bf07da4214365f61f425e00d5e56282679e9f80df09c5edcac` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-declared-source-positive.sarif.json` | `d221c19610db1f3c16a5702448e4ac98b4d03695dd4a8f0f15d0e3f7e7f7974f` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.sarif.json` | `b48a150a713932e6f4ec41dfe374695a2b5ce4c3544022e330923b598b2b64ac` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.sarif.json` | `5d5da5a909e0e6b7a1e0da54752e5e1485c11b8fcf8ea467c8ba048f70a6d803` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.sarif.json` | `cc8424f3776094502acc8c24ce70da6fb82a2bd110043a28d92f8ee429cee41c` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.sarif.json` | `7f88e313b87b8e4b4cb7da2f7543e9dbde68a7e65d4bbdf176ccc22235dbcd00` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-negative.sarif.json` | `1884bcb29e49c65b226c32cf71f85d0f4ce952d30cb7b3b8aab969cdfc6684dd` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-opaque-propagator-positive.sarif.json` | `f40d604774735e28f51d74174690ce240161963f800d4885494de13a2b37313e` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-negative.sarif.json` | `ac20fc8c2b59a0f3f981370fc9a94ae9d30ea9d44e18d1aec02cacccef7b96cf` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-propagator-position-positive.sarif.json` | `c592a2c24ad7ce5614cd698b08ae1b3439662b4ba20dc42b41e181296b2716fa` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.sarif.json` | `1c1dd43d350398917a7e9c1cf1f54db4099b859f7804c86337cb769982b6df30` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.sarif.json` | `b1a4f2dd7d095ac92de65ea2bee60b777c44fff635cdaac2c488aac8f846afcf` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.sarif.json` | `68200764c94985466ff618f963dbbe48ea2d356acc30bcc682578ff657c7b8c3` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.sarif.json` | `ad1111fb048020ae1e8315b2a42f445373e0e48b2c429e66d97c62aa1b93f7fb` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-negative.sarif.json` | `321e92011aca61566d8f2fefcadd3bfe76f561456c6b5a09ecfbc2b27a7412d4` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-store-roundtrip-positive.sarif.json` | `8f8a89d34934dca76758a797a56779a7d4062acb64a8d45b0fb42aacbb0722e7` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-negative.sarif.json` | `9475b777edb8656cc71bdbea95bcc0cc80d9e6ce137276efadb90b414e52e4fb` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-store-separation-positive.sarif.json` | `e88ba6fb691ddf6cccc3431ddec9856935ef7c6bfa28afdf223e6cbb8aa64f22` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-negative.sarif.json` | `ac1d9da2194a8ebacaa497bb46bc9c757762fa50d2df5f4cdd3b2d9c60bb79c2` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-summary-field-positive.sarif.json` | `1821ba463015e4d11f7a5805b2fe106fc22112d0d57d709b7bf804a5b26efc8a` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-negative.sarif.json` | `ef62dbf5935ce1011566d508b69a73462c85157ee6fb6aed45cd8574023da16f` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/codeql-java-modeling/dfb-taint-java-model-summary-through-positive.sarif.json` | `f77383b87743b371f321a94a28fdaa36e15b00ebbb1f7a461dbf866164a5e9a8` |
