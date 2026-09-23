/** @name Vendor and adapter-corrected Foundation sink roles
 * @kind table
 * @id dfb/swift-foundation-identity-roles
 */
import FoundationIdentity
from DataFlow::Node node, string profile
where node.getLocation().getFile().getBaseName() = "main.swift" and
 (node instanceof CommandInjectionSink and profile = "vendor-native" or
  correctedSink(node) and profile = "adapter-corrected")
select node.getLocation().getStartLine(), node.getLocation().getStartColumn(), profile, node.toString()
