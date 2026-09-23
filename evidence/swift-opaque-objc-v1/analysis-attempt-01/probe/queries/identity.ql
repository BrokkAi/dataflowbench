/** @name Resolved opaque wrapper declarations and positional model bindings
 * @kind table
 * @id dfb/swift-opaque-objc-identity
 */
import OpaqueIdentity
from CallExpr call, Method method, Decl owner, ParamDecl parameter, int position, boolean modeled
where call.getLocation().getFile().getBaseName()="main.swift" and
 call.getStaticTarget()=method and owner.getAMember()=method and
 (opaqueMethod(method,"carry(_:)",1) or opaqueMethod(method,"block(_:)",1) or opaqueMethod(method,"select(_:_:)",2)) and
 parameter=method.getParam(position) and
 (if opaqueMethod(method,"carry(_:)",1) and position=0 or opaqueMethod(method,"select(_:_:)",2) and position=1 then modeled=true else modeled=false)
select call.getLocation().getStartLine(), method.getModule().getName(),
 owner.asNominalTypeDecl().getName(),method.getName(),method.getNumberOfParams(),position,
 parameter.getType().(NominalType).getDeclaration().getModule().getName(),parameter.getType().(NominalType).getDeclaration().getName(),
 method.getInterfaceType().(AnyFunctionType).getResult().(AnyFunctionType).getResult().(NominalType).getDeclaration().getModule().getName(),
 method.getInterfaceType().(AnyFunctionType).getResult().(AnyFunctionType).getResult().(NominalType).getDeclaration().getName(),modeled
