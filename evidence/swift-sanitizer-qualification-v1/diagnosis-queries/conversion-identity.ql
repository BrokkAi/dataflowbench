/** @name Resolved radix conversion identities
 * @kind table
 * @id dfb/swift-sanitizer-conversion-identity
 */
import FoundationSources
from InitializerCallExpr call, Initializer target, Decl owner, Type type
where call.getLocation().getFile().getBaseName() = "main.swift" and
 target = call.getStaticTarget() and owner.getAMember() = target and
 call.getArgument(1).getLabel() = "radix" and type = call.getType().getUnderlyingType()
select call.getLocation().getStartLine(), call.getLocation().getStartColumn(),
 target.getModule().getName(), owner.asNominalTypeDecl().getModule().getName(),
 owner.asNominalTypeDecl().getName(), target.getName(), target.getNumberOfParams(),
 target.getParam(0).getType().toString(), target.getParam(1).getType().toString(),
 type.toString(), type.getAPrimaryQlClass()
