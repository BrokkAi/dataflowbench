# Scorecard `semgrep-python-native-taint-taint-tool-native`

Adapter `semgrep-python-native`: `semgrep` `1.175.0` (build `semgrep-oss:1.175.0 — 1.175.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/python`, adapter version `0.1.0`, configuration `08316baa11a9cab8899e96bd48943f529c9c8e770b551faafa686dde2f76c084`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-python-native.json` (`sha256:a0187f8a2fb1212c516ddf3095ee347f47e82eeaeb9c9a98dad1c58e513c8216`, normalized `sha256:a0187f8a2fb1212c516ddf3095ee347f47e82eeaeb9c9a98dad1c58e513c8216`). Generated from freeze manifest `reports/freeze.json` (`sha256:e3fbcae1eaf3f49192f7156616c4b2149893a8470e03ff445fcd1d5f984f9e5c`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-negative.json` | `713f939bd23a34eb60f837ddfc110a5220ff97cf77c6e164b74cc698e2daf1e7` |
| `dfb-template-native-entrypoint` | `dfb-taint-python-native-entrypoint-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-entrypoint-positive.json` | `ecf08744a60456036ec4f1f725c011d22a9989cee4c4478aa25ee9f88e42abf0` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-negative.json` | `6d25a1228fceca5a67243c837ad6e1382b3a7e3afc2d45a9ea640cde2e6a3286` |
| `dfb-template-native-persistence` | `dfb-taint-python-native-persistence-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-persistence-positive.json` | `62998beecabdb6dba0f22a735d6ccd2432738c29377abc624ecea49f0d23e789` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-negative.json` | `4651596848f1f2cf59df71e958e53c009d7eadbafa309f18129b46956b682394` |
| `dfb-template-native-propagator` | `dfb-taint-python-native-propagator-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-propagator-positive.json` | `378c03518d7fa1e121feeb278f4e43515f5edfffdbada586becd8c1884e9d8f1` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-negative.json` | `27006befabba2d41553fc60cd6d0b4808b99c6f157612f3b7e0b62da443b0784` |
| `dfb-template-native-sanitizer` | `dfb-taint-python-native-sanitizer-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-sanitizer-positive.json` | `c79436e7e6339ba314325c7a9b7cd7515de4f97f3cf3deceb23564aca2ff3f84` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-negative` | negative | `not-reached` | true-negative | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-negative.json` | `e316eb5db8156bfeb4dd47f170780e6750f025df4d515fb5e317e58c1e61c80d` |
| `dfb-template-native-source-sink` | `dfb-taint-python-native-source-sink-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-source-sink-positive.json` | `3b78db94317426bce43a13524aad6a0962faa76928ba6823df4b6ea075219f74` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-negative` | negative | `reached` | false-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-negative.json` | `840c7e53e127ba6847bd56d0d1f272834c12d55a221f4532f976dc5830ee6595` |
| `dfb-template-native-summary` | `dfb-taint-python-native-summary-positive` | positive | `reached` | true-positive | `reports/raw/semgrep-python-native/dfb-taint-python-native-summary-positive.json` | `2b11fafb002999d3d7cd632704ffbdab699cc9b0dc4ce5775c6f0d35f3408917` |
