# Scorecard `semgrep-java-native-taint-taint-tool-native`

Adapter `semgrep-java-native`: `semgrep` `1.175.0` (build `semgrep-oss:1.175.0 — 1.175.0 over the pinned snapshot vendored from https://github.com/semgrep/semgrep-rules into adapters/semgrep/native/java`, adapter version `0.1.0`, configuration `445cee9f6886885c22f5081d6dc391849210a2787a4a0d505dfeca788c337f49`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/semgrep-java-native.json` (`sha256:f20ab62be7d8d3e4a6678ac07041d691b36d53ea66d8bb1c44fce4182dbb71d0`, normalized `sha256:f20ab62be7d8d3e4a6678ac07041d691b36d53ea66d8bb1c44fce4182dbb71d0`). Generated from freeze manifest `reports/freeze.json` (`sha256:3228af686d09f8666989368483bef375bb28b94025b55e31eaa7a0bdd29506ee`).

## Language `java`, tier `modeling`

Outcome coverage: `reached` 0, `not-reached` 0, `inconclusive` 0, `unsupported` 12, `runner-error` 0, total 12. `inconclusive`, `unsupported`, and `runner-error` are capability and execution coverage; they are never counted as clean negatives.

### Semantic dimension rates

| Semantic dimension | TP | FN | FP | TN | Inconclusive | Unsupported | Runner error | TPR (template macro) | FPR (template macro) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `external-summary` | 0 | 0 | 0 | 0 | 0 | 4 | 0 | n/a | n/a |
| `heap-field-sensitivity` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |
| `local-flow` | 0 | 0 | 0 | 0 | 0 | 12 | 0 | n/a | n/a |
| `sanitizer` | 0 | 0 | 0 | 0 | 0 | 2 | 0 | n/a | n/a |

Macro-average over semantic dimensions: TPR n/a, FPR n/a. Macro-averages pool templates first, then semantic dimensions; raw case counts are shown for audit only.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `b393207e116c1775b02120e1cbc86492401ef561d52397ba5bb90f42d43a9f08` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `abcd74a9c28d97f3077a9dc99e2d1174e4edf2783e0c94f42e3b27f5952db11e` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `e794a3a40cd8f805ca70c38a646a6b1886236278dcbbb11bd6b14d8e95a8ebfc` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `58a5bdaf3088eb4ec2e31fa62d6987b7825ef15aefdc599b8fc946812bbc72f6` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `87173c67d89061d7c127ed752480fff3f81770129150ed88f466c2776540b8d6` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `cb3f4bee42412e04c690ef351e8976dcd24f1ea44ae391b2caa8ead19b590863` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `8cebef2198df2810fa47a16a532ba3da507bf6324dbdb2cc1561c46d30f767e6` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `e6e755667f592700aae3960fc5a6e9f9957bf2350f4263b2e190216e6b933331` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `3f5f1458c0a12b3ba8d4ddfc25138d4e4b5adb4f9839bcd6f4a72e934326f671` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `6bdeb20011acb3d571d78be35fdd31dcb8a44c85e76b66d1788b5e7cbebaa46d` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `50546b088878a23d57f9930e8f2bffab08737cacd575416c94f58e2e232a81dd` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/semgrep-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `82124f5e7f44617b69da17897eb2782fcf2f1252c4d570e6d86ca16c08cf1001` |
