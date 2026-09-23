/** @name Diagnose typed source and sink call declarations
 * @kind table
 * @id dfb/swift-opaque-endpoint-diagnosis
 */
import swift
import codeql.swift.dataflow.DataFlow
from CallExpr call, Function target, boolean free, boolean callNode, boolean argumentNode
where call.getLocation().getFile().getBaseName()="main.swift" and call.getStaticTarget()=target and
 (if target instanceof FreeFunction then free=true else free=false) and
 (if exists(DataFlow::Node n | n.asExpr()=call) then callNode=true else callNode=false) and
 (if exists(DataFlow::Node n | n.asExpr()=call.getArgument(0).getExpr()) then argumentNode=true else argumentNode=false)
select call.getLocation().getStartLine(),target.getModule().getName(),target.getName(),target.getAPrimaryQlClass(),target.getNumberOfParams(),target.getInterfaceType().toString(),target.getInterfaceType().getAPrimaryQlClass(), free, callNode, argumentNode
