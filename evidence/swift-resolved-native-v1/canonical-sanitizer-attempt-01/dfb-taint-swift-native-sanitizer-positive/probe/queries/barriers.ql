/** @name Native command injection barrier and resolved type provenance
 * @kind table
 * @id dfb/swift-sanitizer-barriers
 */
import FoundationSources
from DataFlow::Node node, Type type, NominalTypeDecl declaration, boolean barrier
where node.getLocation().getFile().getBaseName() = "main.swift" and
 type = node.asExpr().getType().getUnderlyingType() and
 declaration = type.(NominalOrBoundGenericNominalType).getDeclaration() and
 (if node instanceof CommandInjectionBarrier then barrier = true else barrier = false)
select node.getLocation().getStartLine(), node.getLocation().getStartColumn(),
 declaration.getModule().getName(), declaration.getName(), barrier,
 node.asExpr().getAPrimaryQlClass()
