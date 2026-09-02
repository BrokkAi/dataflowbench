# Scorecard `flowdroid-java-native-taint-taint-tool-native`

Adapter `flowdroid-java-native`: `flowdroid` `2.15.1` (build `soot-infoflow-cmd-2.15.1-jar-with-dependencies.jar sha256:51dadead47a173c494c2fa4855b1e8bd3b54e702a2c4b5ed58e60153009ae218; android-34 platform android.jar sha256:6cea1df3efb77103ac3e2beb9bf4718964b0e0869ab16d39d29d5cbae1c147ad — FlowDroid 2.15.1 shipped SourcesAndSinks.txt catalog (extracted verbatim from the pinned soot-infoflow-cmd jar) and default summariesManual taint wrapper`, adapter version `0.1.0`, configuration `297ad249b96b70b527d5717be3fd23c85cf47063d280fd76d177a415a22b7ecf`).

Track `taint`, score dimension `taint`, model profile `tool-native`. This scorecard is a single result population; it is never pooled with other tracks, dimensions, or model profiles.

Normalized report: `reports/flowdroid-java-native.json` (`sha256:6671f301cdcf1a28f4b5c125d9088b2ca8a056c1eeb4a4a52ca1f28366192f99`, normalized `sha256:6671f301cdcf1a28f4b5c125d9088b2ca8a056c1eeb4a4a52ca1f28366192f99`). Generated from freeze manifest `reports/freeze.json` (`sha256:65638eafb36478120d268290479815114f244baa57994c47e19fac6b759e50ae`).

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
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-entrypoint-negative-unsupported.json` | `07bc5c0e6863daf34151e11f0b47dcd998e29fce01752acb7c5fcc87b76c7cf3` |
| `dfb-template-native-entrypoint` | `dfb-taint-java-native-entrypoint-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-entrypoint-positive-unsupported.json` | `e102a1e411c2745e45f229ad841be76a5e65213012a8ae975544b687e2a5ae02` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-persistence-negative-unsupported.json` | `57b9be6ce1c0d0aab7fecc0f6defb555e97e2708e28a66d6511ebd6a14affa0b` |
| `dfb-template-native-persistence` | `dfb-taint-java-native-persistence-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-persistence-positive-unsupported.json` | `6c0db12d450980524d3fe7b9f62060412c2a1c5459ad6eb973ecfbd16236c1d9` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-propagator-negative-unsupported.json` | `cc88f82d23c135b8e2af548999ab6ee28476a260c143c0b1dec7bb0ff8ef6963` |
| `dfb-template-native-propagator` | `dfb-taint-java-native-propagator-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-propagator-positive-unsupported.json` | `510ae7ac7e7c36fc3c07db10fdc49a1064e60c13b53b80228c5f56b012377294` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-sanitizer-negative-unsupported.json` | `15b2bbc0ba1f0512b695658b297528945ebe1b40086a2d4c29e0e759f50aaa43` |
| `dfb-template-native-sanitizer` | `dfb-taint-java-native-sanitizer-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-sanitizer-positive-unsupported.json` | `cf7aecf9edc0dd8e36f725fd8fc30e28bab95424e86ddef04743859f027debfb` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-source-sink-negative-unsupported.json` | `b323db32c877a9acbf354c527353080c587229ded8dc1f62040dedeeccdfa00d` |
| `dfb-template-native-source-sink` | `dfb-taint-java-native-source-sink-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-source-sink-positive-unsupported.json` | `96fea20b0d89eb5e701acdfd690f4376fd0f9f70edcbcc6dd41a76c870bed5bc` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-negative` | negative | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-summary-negative-unsupported.json` | `b44bc8330180a50a345249c6a8ba0e1b5d1611adebf438ed1c0f610a638b634c` |
| `dfb-template-native-summary` | `dfb-taint-java-native-summary-positive` | positive | `unsupported` | unsupported | `reports/raw/flowdroid-java-native/dfb-taint-java-native-summary-positive-unsupported.json` | `b22745d715f633e6a609a378bd72d70c269de43f39d92a161d407536726e9712` |
