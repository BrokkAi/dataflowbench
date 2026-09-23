/** @name Adapter-patched conversion source and sink roles
 * @kind table
 * @id dfb/swift-patched-conversion-roles
 */
import FoundationSources
from DataFlow::Node node, string role
where node.getLocation().getFile().getBaseName() = "main.swift" and
 (processInput(node, role) or correctedSink(node) and role = "sink")
select node.getLocation().getStartLine(), node.getLocation().getStartColumn(), "adapter-patched-conversion", role
