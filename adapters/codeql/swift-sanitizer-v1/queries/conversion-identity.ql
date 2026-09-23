/** @name Resolved radix conversion identities
 * @kind table
 * @id dfb/swift-sanitizer-conversion-identity
 */
import FoundationSources
predicate observedType(Type type, string moduleName, string name) {
  exists(Type scalar |
    (if type instanceof OptionalType then scalar = type.(OptionalType).getBaseType() else scalar = type) and
    moduleName = scalar.(NominalOrBoundGenericNominalType).getDeclaration().getModule().getName() and
    name = scalar.(NominalOrBoundGenericNominalType).getDeclaration().getName()
  )
  or
  not exists(Type scalar |
    (if type instanceof OptionalType then scalar = type.(OptionalType).getBaseType() else scalar = type) and
    scalar instanceof NominalOrBoundGenericNominalType
  ) and moduleName = "unresolved" and name = "unresolved"
}
from InitializerCallExpr call, Initializer target, Decl owner, Type type, string typeModule, string typeName
where call.getLocation().getFile().getBaseName() = "main.swift" and
 target = call.getStaticTarget() and owner.getAMember() = target and
 call.getArgument(1).getLabel() = "radix" and type = call.getType().getUnderlyingType() and observedType(type, typeModule, typeName)
select call.getLocation().getStartLine(), call.getLocation().getStartColumn(),
 target.getModule().getName(), owner.asNominalTypeDecl().getModule().getName(),
 owner.asNominalTypeDecl().getName(), target.getName(), target.getNumberOfParams(),
 target.getParam(0).getType().toString(), target.getParam(1).getType().toString(),
 typeModule, typeName
