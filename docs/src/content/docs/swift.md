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
