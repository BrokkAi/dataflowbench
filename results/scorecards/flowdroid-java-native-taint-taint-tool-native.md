# Scorecard `flowdroid-java-native-taint-taint-tool-native`

Adapter `flowdroid-java-native`: `flowdroid` `2.15.1` (build `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218; android-34 platform android.jar sha256:6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad — FlowDroid 2.15.1 shipped SourcesAndSinks.txt catalog (extracted verbatim from the pinned soot-infoflow-cmd jar) and default summariesManual taint wrapper`, adapter version `0.1.0`, configuration `297ad249b96b70b527d5717be3fd23c85cf47063d280fd76d177a415a22b7ecf`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/flowdroid-java-native.json` (`sha256:27678765cf4a5abbdf31db07bc8918fe995fe3a878dc10dd22d3f4cb745b5c2e`, normalized `sha256:27678765cf4a5abbdf31db07bc8918fe995fe3a878dc10dd22d3f4cb745b5c2e`). Generated from freeze manifest `reports/freeze.json` (`sha256:f5416cded5891c92418d23ec5e2c638eb73f86695255cd5ea5f818b10f6c9e1d`).

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

Caveat: `inconclusive` outcomes are excluded from every TPR and FPR denominator above, so the rates cover only the conclusive subset of this population. This population records 0 `inconclusive` outcome(s). Compare rate columns across adapters with that exclusion in mind: an adapter that self-reports uncertainty is not penalized in its rates for the cases it declined to decide.

### Cases

| Template | Case | Polarity | Outcome | Classification | Raw evidence | Raw SHA-256 |
| --- | --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `a278aeecd648c8d367676c6571aa44fdc0fb5fb9acbe5a33e2b507b996d08862` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `d34a224dd7c755703755064da7a6bc081b46b72af130173fa8060618e7d29475` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `2b1f3e463994824eafd61673013f45444c87640d373d7bccfe073a881397610b` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `d9f057c463348a6d0c173e0c96f87505f24c05ca54cd4ae20d6f0abd66b4991b` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `e88ecb3ab0aa9d601a217e9dd204240720fd3a8ab68a28710930b3e668b18fae` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `c2989cf26e1504c101850fc5b7f1cbf26ba0ba7c5bc603a6c1a3afea0121b5c8` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `4e08f8029c3b4c4a66453cbd2fe053b4606aa0028f69c3ce10d14d802c114197` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `0010ebf8b120486591969369486de74aa0fd4f4502f44f61f482411dfb4b9398` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `8b854d884e3926a47fbb8785cfa44191988af3a72f344b6c6cc1599632f8c206` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `586f02938c0919be7aed8a656f735160bcbab78d909952cb5dc4ffa51ee09284` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `3707880163495c9b40ea8f5672032686f80cf4bc9e52f5b268d35bfc3492669e` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `b29f31ec476b2274c67fc5c1e43a37039b498953d796dd048f2aeaf70a70b1e9` |
