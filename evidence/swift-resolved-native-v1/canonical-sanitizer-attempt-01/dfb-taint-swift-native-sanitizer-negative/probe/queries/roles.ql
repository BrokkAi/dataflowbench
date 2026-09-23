/** @name Resolved sanitizer adapter roles
 * @kind table
 * @id dfb/swift-resolved-sanitizer-roles
 */
import FoundationSources
from DataFlow::Node node, string role
where node.getLocation().getFile().getBaseName()="main.swift" and
 (processInput(node,role) or correctedSink(node) and role="sink")
select node.getLocation().getStartLine(),node.getLocation().getStartColumn(),"adapter-patched-resolved-sanitizer",role
