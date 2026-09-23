/** @name Shipped native role nodes including non-expression nodes
 * @description Enumerate existing shipped role classes without endpoint rules.
 * @kind table
 * @id dfb/swift-candidate-native-role-nodes
 */
import swift
import codeql.swift.dataflow.DataFlow
import codeql.swift.dataflow.FlowSources
import codeql.swift.security.CommandInjectionQuery
from DataFlow::Node node, string role, string identity
where node.getLocation().getFile().getBaseName() = "main.swift" and
(
  node instanceof FlowSource and role = "shipped-source" and identity = node.(FlowSource).getSourceType()
  or node instanceof CommandInjectionSink and role = "shipped-sink" and identity = node.toString()
)
select node.getLocation().getStartLine(), node.getLocation().getStartColumn(), role, identity
