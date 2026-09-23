/** @name Diagnose typed source and sink call declarations
 * @kind table
 * @id dfb/swift-opaque-endpoint-diagnosis
 */
import swift
from CallExpr call, Function target
where call.getLocation().getFile().getBaseName()="main.swift" and call.getStaticTarget()=target
select call.getLocation().getStartLine(),target.getModule().getName(),target.getName(),target.getAPrimaryQlClass(),target.getNumberOfParams(),target.getInterfaceType().toString(),target.getInterfaceType().getAPrimaryQlClass()
