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
- [Inspect the complete registry reconciliation](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-coverage-audit.md), including every unresolved family and links to retained evidence.
- [Read the Swift applicability contract](https://github.com/BrokkAi/dataflowbench/blob/main/docs/swift-kernel.md).
- [CodeQL activation and execution](https://github.com/BrokkAi/dataflowbench/blob/main/docs/codeql-swift.md).
- [Joern activation and execution](https://github.com/BrokkAi/dataflowbench/blob/main/docs/joern-swift.md).

Opaque modeling, platform-native families and the Result extension remain
unresolved scope. Their documentation does not constitute accepted exclusions
or completion of the Swift epic. Real-project work requires its own selection
and review; reserved tracks remain inactive.

A future snapshot must follow the normal pin review, evidence, immutable freeze
and result-generation process. Inconclusive, unsupported and runner-error
outcomes remain separate from clean negatives. A partition with no definitive
outcomes has no correctness rate; publishing honest coverage does not require
inventing one.
