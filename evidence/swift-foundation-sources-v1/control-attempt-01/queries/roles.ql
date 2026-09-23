/** @name Resolved source and sink roles
 * @kind table
 * @id dfb/swift-foundation-sources-roles
 */
import FoundationSources
from DataFlow::Node node, string profile, string role
where node.getLocation().getFile().getBaseName() = "main.swift" and
 (
  processInput(node, role) and profile = "adapter-corrected"
  or node instanceof FlowSource and role = "source" and profile = "vendor-native"
  or correctedSink(node) and role = "sink" and profile = "adapter-corrected"
  or node instanceof CommandInjectionSink and role = "sink" and profile = "vendor-native"
 )
select node.getLocation().getStartLine(), node.getLocation().getStartColumn(), profile, role
