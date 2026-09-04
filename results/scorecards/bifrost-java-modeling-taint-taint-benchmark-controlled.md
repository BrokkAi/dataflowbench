# Scorecard `bifrost-java-modeling-taint-taint-benchmark-controlled`

Adapter `bifrost-java-modeling`: `bifrost` `bifrost 0.10.9` (build `04775a7b38c9c025714168328ddb8b793a326461`, adapter version `0.1.0`, configuration `f84f51766cf26ce5665df0281d649df8fdb9ec64ab76cde675f790b8c0644ba8`).

Track `taint`, score dimension `taint`, model profile `benchmark-controlled`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/bifrost-java-modeling.json` (`sha256:282d0c4aa045356168de42ece3e04f7cdbe9daf17d7931aea9ab502a17ecdc87`, normalized `sha256:282d0c4aa045356168de42ece3e04f7cdbe9daf17d7931aea9ab502a17ecdc87`). Generated from freeze manifest `reports/freeze.json` (`sha256:95faa71908b637ba349c1890ce913abd865c670a9093e123a25d975430bfe52c`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 4, `not-reached` 3, `inconclusive` 1, `unsupported` 16, `runner-error` 0, total 24. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 8 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `interprocedural-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `local-flow` | 2 | 0 | 0 | 1 | 1 | 0 | 0 | 100.0% | 0.0% |
| `object-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `sanitizer` | 2 | 0 | 0 | 2 | 0 | 0 | 0 | 100.0% | 0.0% |

Macro-average over semantic dimensions: TPR 100.0%, FPR 0.0%. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 1 `inconclusive` outcome(s), produced by `bifrost`. Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-negative.json` | `34fdfed866b570ebd86b470137165b5a7247beac0c8d27d27df1cab4e8b064bf` |
| `dfb-template-model-declared-sink` | `dfb-taint-java-model-declared-sink-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-sink-positive.json` | `b9d9740396abe58eb3a5e0c81856c4d2c95098dd7cc959a288f8f951cd4ef54b` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-negative` | negative | `inconclusive` | inconclusive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-negative.json` | `d92b8f475f7d25f66ce167dfaa99ab4a2f042cb2e5efb7d7b6e8990effda0631` |
| `dfb-template-model-declared-source` | `dfb-taint-java-model-declared-source-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-declared-source-positive.json` | `dba3d12b26f4503ffcdcb66757c047cdaa02b7d9717233bb7e782f9ccbfee3d5` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-negative-unsupported.json` | `0e1f3b5a601e5081b8177a7dcddb83a4a363aab2ef887892ee1fa78881b75aa3` |
| `dfb-template-model-entrypoint-parameter` | `dfb-taint-java-model-entrypoint-parameter-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-parameter-positive-unsupported.json` | `19f5c738c363bd4a7ded23c083de83481831e6cde923966e1980e7d07527628f` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-negative-unsupported.json` | `f3c8e284a346e19345fc857c9dd6740098d4978c6e3d33f8548524a77b00f893` |
| `dfb-template-model-entrypoint-selectivity` | `dfb-taint-java-model-entrypoint-selectivity-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-entrypoint-selectivity-positive-unsupported.json` | `942726b9de3d285c89a61ef0793c82e3e411b03062ef43178a3e4f4a6e9b143a` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-negative-unsupported.json` | `2ee1abb578d54303e5cc0983204df1147020ca024957e938adb2dd77f0f15da9` |
| `dfb-template-model-opaque-propagator` | `dfb-taint-java-model-opaque-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-opaque-propagator-positive-unsupported.json` | `f10095ca7b1a6357d6bd7b6a9d7cb5ae01fe095bb24ce6e81300f273dd2f83a6` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-negative-unsupported.json` | `94a6fcbc47ef9f44b6e09626d769bd1f3e6dc3df68c49af8f56e77ddee39c76e` |
| `dfb-template-model-propagator-position` | `dfb-taint-java-model-propagator-position-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-propagator-position-positive-unsupported.json` | `1b618f4031dbd22aa1d33b3f8b8cfc62cdbaa868ec28d016c0fb188c497d57c8` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-negative.json` | `ab03eaee639c000d3e4c4a52b3191cea677e7155e379a6113533b79fe97d9d13` |
| `dfb-template-model-sanitizer-kill` | `dfb-taint-java-model-sanitizer-kill-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-kill-positive.json` | `758a36c42de8eea4ac6b31a5d9a8c507dc5a6bffb316e10fd5c81d5e77a588a0` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-negative` | negative | `not-reached` | true-negative | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-negative.json` | `90ee8c9ee868dfd386810da0fb2ba631d99403ac6c65eb91b462f905ebbf1bc1` |
| `dfb-template-model-sanitizer-selectivity` | `dfb-taint-java-model-sanitizer-selectivity-positive` | positive | `reached` | true-positive | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-sanitizer-selectivity-positive.json` | `4a2222c3ae97f620eda4e684e4f33a0d377bc6b36b2ddc7c99ebb47cae059c93` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-negative-unsupported.json` | `317b57e2ecdddb3bf1aea99256a689a9aeb4ef672061f4265053e11f7f14f1cf` |
| `dfb-template-model-store-roundtrip` | `dfb-taint-java-model-store-roundtrip-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-roundtrip-positive-unsupported.json` | `9abafb5b0ab6ac8ad4abebcfddd0fdf79290b83593114ae8425988ba1b9a3bf0` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-negative-unsupported.json` | `c2d8da544a31b925c6c8d4f189d7180e9b53aa939e43e2ad394f76e63184fb5f` |
| `dfb-template-model-store-separation` | `dfb-taint-java-model-store-separation-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-store-separation-positive-unsupported.json` | `2e021b9f82a5ba22e35a71b5622fe275bddd991f04605716a4fc154731da971b` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-negative-unsupported.json` | `3a4d6837791533096c771f160fed89ad313aaf6ff55b107567aa18f033ad4a9a` |
| `dfb-template-model-summary-field` | `dfb-taint-java-model-summary-field-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-field-positive-unsupported.json` | `18ab8befb12d44dccc7493c1d62d746e1e99ff59812a11d7bfb4e898a82749a1` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-negative` | negative | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-negative-unsupported.json` | `6db8b2f2bf50e4723985c00e389d4d67a2b77d8551831a09d10a58106002dd71` |
| `dfb-template-model-summary-through` | `dfb-taint-java-model-summary-through-positive` | positive | `unsupported` | unsupported | `reports/raw/bifrost-java-modeling/dfb-taint-java-model-summary-through-positive-unsupported.json` | `cc8db1bf5876d7e585a32d35d1d8838df3fcd5b57eb9e72757867672f9a9d1e7` |
