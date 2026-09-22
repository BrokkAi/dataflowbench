import SwiftModelIdentity
predicate exactOpaque(Method f, string member, int arity) {
 f.hasQualifiedName("DataFlowBenchTaintSwift", "Opaque", member) and
 f.isStaticOrClassMethod() and f.getNumberOfParams() = arity and
 forall(ParamDecl p | p = f.getAParam() | swiftString(p.getType())) and
 swiftString(f.getInterfaceType().(AnyFunctionType).getResult().(AnyFunctionType).getResult())
}
predicate barrier(DataFlow::Node n) {
 exists(CallExpr c, Method f | c.getStaticTarget() = f and exactOpaque(f,"block(_:)",1)
  and n.asExpr() = c.getArgument(0).getExpr())
}
predicate step(DataFlow::Node predecessor, DataFlow::Node to) {
 exists(CallExpr c, Method f, int position | c.getStaticTarget() = f and
  (exactOpaque(f,"carry(_:)",1) and position = 0 or exactOpaque(f,"select(_:_:)",2) and position = 1) and
  predecessor.asExpr() = c.getArgument(position).getExpr() and to.asExpr() = c)
}
