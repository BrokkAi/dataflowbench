/** @name Patched SSA adapter source and sink roles
 * @kind table
 * @id dfb/swift-patched-conversion-roles
 */
import FoundationSources
from DataFlow::Node node, string role, string profile
where node.getLocation().getFile().getBaseName() = "main.swift" and
 (processInput(node, role) or correctedSink(node) and role = "sink") and
 profile = ["adapter-patched-ssa", "adapter-patched-ssa-resolved"]
select node.getLocation().getStartLine(), node.getLocation().getStartColumn(), profile, role
