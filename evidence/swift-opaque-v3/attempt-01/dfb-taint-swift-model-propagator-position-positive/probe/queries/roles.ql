/** @name Objective-C control endpoint roles
 * @kind table
 * @id dfb/swift-opaque-objc-roles
 */
import OpaqueIdentity
from DataFlow::Node node, string profile, string role
where profile=["adapter-controlled-model-off","adapter-controlled-model-on"] and
 (stringSource(node) and role="source" or stringSink(node) and role="sink")
select node.getLocation().getStartLine(),node.getLocation().getStartColumn(),profile,role
