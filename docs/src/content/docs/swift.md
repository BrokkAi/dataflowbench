---
title: Swift implementation status
description: Swift examples, independent analyzer execution, and remaining publication gates.
---

Swift examples and independent CodeQL and Joern execution evidence are available
in the repository. They have not yet entered a published release freeze.
The current snapshot remains authoritative for published benchmark participation.

Analyzer language breadth, implemented fixtures, completed native queries and
qualified benchmark outcomes are separate claims. In particular, Bifrost Swift
support remains **unsupported**. Native path observations do not establish
qualified correctness or semantic completeness.

- [Browse the Swift examples](https://github.com/BrokkAi/dataflowbench/tree/main/cases/taint/swift).
- [Inspect the historical v1 registry reconciliation](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-coverage-audit.md), including the original unresolved families and links to retained evidence.
- [Inspect the v2 fixture additions](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-v2-coverage.md), with separate native and Result validation boundaries.
- [Read the Swift applicability contract](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-kernel.md).
- [CodeQL activation and execution](https://github.com/BrokkAi/dataflowbench/blob/main/docs/codeql-swift.md).
- [Joern activation and execution](https://github.com/BrokkAi/dataflowbench/blob/main/docs/joern-swift.md).

The v2 population adds 12 platform-native examples and two Result extension
examples to the original 90. Native examples are compile-only; the Result pair
has bounded source-dependence controls. Independent analyzer qualification and
execution for these additions remain pending. Two opaque modeling identities
remain unresolved, with no accepted exclusion or completion of the Swift epic. Real-project work requires its own selection
and review; reserved tracks remain inactive.

A future snapshot must follow the normal pin review, evidence, immutable freeze
and result-generation process. Inconclusive, unsupported and runner-error
outcomes remain separate from clean negatives. A partition with no definitive
outcomes has no correctness rate; publishing honest coverage does not require
inventing one.

The [prospective native integration plan](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-native-integration-plan.md) tracks the next CodeQL qualification dependencies with separate vendor-native and adapter-assisted lanes. The candidate configuration remains pending, and Joern's external-property binding gap remains blocked. These diagnostics add no published results.

The [canonical source–sink qualification](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-canonical-qualification.md) retains a separating positive/negative observation for the adapter-assisted CodeQL lane. It remains non-scored; vendor-native observations and the pending activation state are reported separately.

The [canonical entrypoint qualification](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-entrypoint-qualification.md) treats the command-line count guard and indexed source separately, retaining vendor-native and adapter-assisted observations without scored promotion.

The [independent append control](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-propagator-qualification.md) is blocked by a retained false flow through a constant-body lookalike. Native path and shipped heuristic evidence explain the precision gap; the canonical propagator pair remains unrun.

The [independent integer sanitizer control](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-sanitizer-qualification.md) is also blocked: a string-holding local numeric lookalike is admitted as a barrier, and both local wrapper flow controls are missing. These observations remain separate; the canonical sanitizer pair has not run.

The [independent Data roundtrip control](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-summary-qualification.md) is blocked by a false flow through constant-body local lookalikes. Resolved identities, attached ports, simple transfer edges and OptionalSome stores are retained separately; the canonical summary pair remains unrun.
