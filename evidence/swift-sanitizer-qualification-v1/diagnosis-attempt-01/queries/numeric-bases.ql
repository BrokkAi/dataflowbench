/** @name Resolved base declarations used by the shipped numeric barrier
 * @kind table
 * @id dfb/swift-sanitizer-numeric-bases
 */
import FoundationSources
from DataFlow::Node node, NominalOrBoundGenericNominalType type,
 NominalOrBoundGenericNominalType base
where node.getLocation().getFile().getBaseName() = "main.swift" and
 type = node.asExpr().getType().getUnderlyingType() and
 base = type.getABaseType*() and base.getName() = ["Numeric", "SignedInteger", "UnsignedInteger"]
select node.getLocation().getStartLine(), node.getLocation().getStartColumn(),
 type.getDeclaration().getModule().getName(), type.getDeclaration().getName(),
 base.getDeclaration().getModule().getName(), base.getDeclaration().getName()
