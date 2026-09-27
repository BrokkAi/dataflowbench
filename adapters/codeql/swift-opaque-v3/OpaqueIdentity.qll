/** Exact controlled-model declarations; never match bare names or display signatures. */
import swift
import codeql.swift.dataflow.DataFlow

predicate swiftString(Type t) {
 t.(NominalType).getDeclaration().getModule().getName() = "Swift" and
 t.(NominalType).getDeclaration().getName() = "String"
}
predicate stringSource(DataFlow::Node n) {
 exists(CallExpr c, FreeFunction f | c.getStaticTarget() = f and
  f.getModule().getName() = "DataFlowBenchTaintSwift" and
  f.getName() = "dfb_source()" and f.getNumberOfParams() = 0 and
  swiftString(f.getInterfaceType().(AnyFunctionType).getResult()) and n.asExpr() = c)
}
predicate stringSink(DataFlow::Node n) {
 exists(CallExpr c, FreeFunction f | c.getStaticTarget() = f and
  f.getModule().getName() = "DataFlowBenchTaintSwift" and
  f.getName() = "dfb_sink(_:)" and f.getNumberOfParams() = 1 and
  swiftString(f.getParam(0).getType()) and
  f.getInterfaceType().(AnyFunctionType).getResult().(TupleType).getNumberOfTypes() = 0 and n.asExpr() = c.getArgument(0).getExpr())
}

predicate opaqueMethod(Method f, string member, int arity) {
 f.hasQualifiedName("DataFlowBenchTaintSwift", "Opaque", member) and
 f.isInstanceMethod() and f.getNumberOfParams() = arity and
 forall(ParamDecl p | p = f.getAParam() | swiftString(p.getType())) and
 swiftString(f.getInterfaceType().(AnyFunctionType).getResult().(AnyFunctionType).getResult())
}
predicate declaredStep(DataFlow::Node a, DataFlow::Node b) {
 exists(CallExpr call, Method target, int position |
  call.getStaticTarget() = target and
  (opaqueMethod(target,"carry(_:)",1) and position=0 or
   opaqueMethod(target,"select(_:_:)",2) and position=1) and
  a.asExpr() = call.getArgument(position).getExpr() and b.asExpr() = call)
}
