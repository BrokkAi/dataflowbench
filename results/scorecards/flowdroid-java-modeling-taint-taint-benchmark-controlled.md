# Scorecard `flowdroid-java-modeling-taint-taint-benchmark-controlled`

Adapter `flowdroid-java-modeling`: `flowdroid` `2.15.1` (build `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218; android-34 platform android.jar sha256:6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad; dexed by D8 8.5.35 (build 2c176ec131a9edb97721fb8578b7fbb462376632 from go/r8bot (luci-r8-custom-ci-archive-0-gths)); r8 jar sha256:4733945987ee0a840fafc34080b135259e01678412e07212b23f706334290294`, adapter version `0.1.0`, configuration `1dfd4bebb5426ae7524ceae88e5f7b4588f807a48c83ca66bb24664f45b88377`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/releases/v0.9.2/publication-v1/normal/flowdroid-java-modeling.json` (`sha256:b34b2d00873ca84cd4f699fdbffca93472a990b9b00744d7ce4309c63bcad459`, normalized `sha256:b34b2d00873ca84cd4f699fdbffca93472a990b9b00744d7ce4309c63bcad459`). Generated from freeze manifest `reports/freeze.json` (`sha256:750e3b8c1275ee05b027017a1e993e84847e292344224976ca3447257ad15d69`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 7, `not-reached` 7, `inconclusive` 0, `unsupported` 10, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 2 | 0 | 0 | 2 | 0 | 4 | 0 | 100.0% | 0.0% |
| `heap-field-sensitivity` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |
| `interprocedural-flow` | 4 | 0 | 0 | 4 | 0 | 4 | 0 | 100.0% | 0.0% |
| `local-flow` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 1 | 0 | 0 | 1 | 0 | 2 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `ea26f78783f44cf8ef58cde344181580c6acc44ac7031d3a8bbcd5bec3a5d28e` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `35a845cbfaa3f0043d6592f4104009b4b743514812600ec9e70a81b9b28d66ff` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `55a63f200cddf238cfbea07fbc4725c812ea20b1b710189fa0379c36a4e03b48` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `5fa5c96f5fc487f6cab7439da9b1b944b497959aa6a7017b31365188b8dc7210` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative.json` | `2863ad6eaff0116f18166bf6ca56ff1ca76c024737e0e139a6eddb8cef6eb529` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive.json` | `92a733deb54a21250babd37a9f7d8b82fcfa3ba604d6345576632981a86d749a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative.json` | `f44355431f9e136062f29284c8052315f8e13649b823ec9f22aa9447e6af407a` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive.json` | `fafa0aa47432f43a201a67e08f0b6b8896dac6608553caf76f8f2b36e10539d4` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-negative.json` | `93a571a2e262bbf849a40ae1ffd9bbaa0315eabbe0584c7f8746351a5901d419` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-opaque-propagator-positive.json` | `0dc09ca75f3ad18415fff14dc480959743aab34060019160b222f500ebf32091` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-negative.json` | `4fe31e34fd59eedd427c8e6d58a16f17f11a1a4b1579586cbe908132bab3290a` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-propagator-position-positive.json` | `fe3d1079dfb507feef97784bd4a19141a1c290ffcd42b99f6cba8b94d12221eb` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `36c32c58baacf5f091878f545baf18fe0b1cdc93d6f01b0c474e0cfb63ba48bf` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `88f647338aec72a225f7655c8fe4ebfa3610e2a1dd11d7f9b025df9435c50868` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `53296be3130002c2aa4fda21e1c0578bbdb5f91cfa407416e1b833985ab448ed` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `fd286cb3d7ee0daa3b8b3b9afcc8a347b93bb0022b487f22e0636c5a77b0cbfc` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-negative.json` | `0f05b99a0ccc1ad6613a5d0ef432b05dfbb22105e9e686d5b4a18bcab4b3cfef` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-store-roundtrip-positive.json` | `a8d69db556f3dcc01ccc10643d020f077a234354fa64572944bb0cb6777b73c1` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-negative.json` | `d34b5ed1be84c5fb667b045b4fb0fdaec3e0f3beb1a05ad28d1fda5dcdffe33e` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-store-separation-positive.json` | `8ffd2bf727db5a970bf8c893083d5aeef389672de98ebebe82a862b9e4686d13` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-negative.json` | `82d293710e9599d1bcc67b2c15a5c36c347da40b1dadf1e7f922e91308707b4c` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-field-positive.json` | `435d7e516da7e6bcf0beef198b87e1cc0dc13569a667e64daaee6434fba0ffcc` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `not-reached` | true-negative | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-negative.json` | `6044cb7e2534dcbdfdbb93adfee9ea2817ba755da8f28f8a0df9cea6b77c4808` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `reached` | true-positive | `reports/releases/v0.9.2/publication-v1/capture/raw/flowdroid-java-modeling/dfb-taint-java-model-summary-through-positive.json` | `9d3c18be454c0409ffe3f321e3a9bc7a7c31b8f95de927a7fa8895551912f0f9` |
