/** @name Structural endpoint stages
 * @kind table
 * @id dfb/swift-endpoint-diagnostic-v1
 */
import swift
import codeql.swift.controlflow.CfgNodes
import codeql.swift.dataflow.DataFlow

predicate benchmarkInt(Type t) {
  t.(NominalType).getDeclaration().getModule().getName() = "Swift" and
  t.(NominalType).getDeclaration().getName() = "Int"
}

predicate exactTarget(CallExpr call, string role) {
  exists(FreeFunction f |
    f = call.getStaticTarget() and
    f.getModule().getName() = "DataFlowBenchTaintSwift" and
    (
      role = "source" and f.getName() = "dfb_source()" and
      f.getNumberOfParams() = 0 and
      benchmarkInt(f.getInterfaceType().(AnyFunctionType).getResult())
      or
      role = "sink" and f.getName() = "dfb_sink(_:)" and
      f.getNumberOfParams() = 1 and benchmarkInt(f.getParam(0).getType()) and
      f.getInterfaceType().(AnyFunctionType).getResult().(TupleType).getNumberOfTypes() = 0
    )
  )
}

Expr endpointExpr(CallExpr call, string role) {
  role = "source" and result = call
  or
  role = "sink" and result = call.getArgument(0).getExpr()
}

from CallExpr call, string role, int exact
where
  role = ["source", "sink"] and
  (if exactTarget(call, role) then exact = 1 else exact = 0) and
  call.getLocation().getFile().getBaseName() = "main.swift"
select call.getLocation().getFile().getBaseName(),
  call.getLocation().getStartLine(), call.getLocation().getStartColumn(), role,
  count(call.getStaticTarget()), exact,
  count(endpointExpr(call, role)),
  count(CfgNode n | n.getAst() = endpointExpr(call, role) | n),
  count(DataFlow::Node n | n.asExpr() = endpointExpr(call, role) | n),
  concat(Function f | f = call.getStaticTarget() | f.getModule().getName() + ":" + f.getName(), ",")
