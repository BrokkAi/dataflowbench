# Swift v2 fixture participation

This is an unfrozen fixture inventory under A38/A39, not analyzer support or a scored result. The immutable `swift-synthetic-v2` input population contains the original 90 v1 assertions plus 12 native assertions and two Result extension assertions. The original reports still bind v1 and do not acquire rows for these additions.

The [v1 outcome reconciliation](swift-coverage-audit.md) retains all prior results. Seven formerly deferred families now have canonical pairs, with independent analyzer qualification and execution still pending. The two opaque modeling identities remain unresolved. No absent execution is labeled unsupported, inconclusive, runner-error, or not-reached. Bifrost Swift remains unsupported; no Bifrost result rows are invented.

| Template | Polarity | Example | Profile | Validation policy | Analyzer results |
| --- | --- | --- | --- | --- | --- |
| `dfb-template-native-entrypoint` | negative | [dfb-taint-swift-native-entrypoint-negative](../cases/taint/swift/native-entrypoint-negative/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-entrypoint` | positive | [dfb-taint-swift-native-entrypoint-positive](../cases/taint/swift/native-entrypoint-positive/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-persistence` | negative | [dfb-taint-swift-native-persistence-negative](../cases/taint/swift/native-persistence-negative/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-persistence` | positive | [dfb-taint-swift-native-persistence-positive](../cases/taint/swift/native-persistence-positive/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-propagator` | negative | [dfb-taint-swift-native-propagator-negative](../cases/taint/swift/native-propagator-negative/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-propagator` | positive | [dfb-taint-swift-native-propagator-positive](../cases/taint/swift/native-propagator-positive/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-sanitizer` | negative | [dfb-taint-swift-native-sanitizer-negative](../cases/taint/swift/native-sanitizer-negative/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-sanitizer` | positive | [dfb-taint-swift-native-sanitizer-positive](../cases/taint/swift/native-sanitizer-positive/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-source-sink` | negative | [dfb-taint-swift-native-source-sink-negative](../cases/taint/swift/native-source-sink-negative/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-source-sink` | positive | [dfb-taint-swift-native-source-sink-positive](../cases/taint/swift/native-source-sink-positive/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-summary` | negative | [dfb-taint-swift-native-summary-negative](../cases/taint/swift/native-summary-negative/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-native-summary` | positive | [dfb-taint-swift-native-summary-positive](../cases/taint/swift/native-summary-positive/case.json) | tool-native | Compile only; never execute | Pending qualification and execution |
| `dfb-template-result-error-propagation` | negative | [dfb-taint-swift-result-error-propagation-negative](../cases/taint/swift/result-error-propagation-negative/case.json) | benchmark-controlled | Compile and bounded source-dependence controls | Pending qualification and execution |
| `dfb-template-result-error-propagation` | positive | [dfb-taint-swift-result-error-propagation-positive](../cases/taint/swift/result-error-propagation-positive/case.json) | benchmark-controlled | Compile and bounded source-dependence controls | Pending qualification and execution |

The new population preserves core (66), calibration (4), controlled modeling (20), native modeling (12), and language extension (2) as separate partitions. No rate or score denominator pools them. All analyzer budgets remain 512 MiB / 60 seconds. Real-project work stays separate and reserved tracks remain inactive.

Reproduce input integrity with `python3 scripts/audit-swift-v2.py --check`; compile/control the new tranche with `python3 scripts/validate-swift-v2.py --output <fresh-directory>`. The existing Swift fixture validator continues to validate v1 independently. Prospective independent native API/model qualification and extension partitions must precede fresh analyzer execution; neither existing adapter configuration is modified here.
