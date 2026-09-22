/** Exact controlled-model declarations; never match bare names or display signatures. */
import swift
import codeql.swift.dataflow.DataFlow

predicate swiftString(Type t) {
 t.(NominalType).getDeclaration().getModule().getName() = "Swift" and
 t.(NominalType).getDeclaration().getName() = "String"
}
predicate modelMethod(Method f, string owner, string member, int arity) {
 f.hasQualifiedName("DataFlowBenchTaintSwift", owner, member) and
 f.getNumberOfParams() = arity and
 forall(ParamDecl p | p = f.getAParam() | swiftString(p.getType())) and
 (if member = ["fetchRemote()", "fetchLocal()", "scrub(_:)", "sanitize(_:)", "pass(_:)", "hold(_:)", "get(_:)"]
  then swiftString(f.getInterfaceType().(AnyFunctionType).getResult())
  else f.getInterfaceType().(AnyFunctionType).getResult().(TupleType).getNumberOfTypes() = 0)
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
  swiftString(f.getParam(0).getType()) and n.asExpr() = c.getArgument(0).getExpr())
}
predicate declaredSource(DataFlow::Node n) {
 exists(CallExpr c, Method f | c.getStaticTarget() = f and
  modelMethod(f,"Config","fetchRemote()",0) and f.isStaticOrClassMethod() and
  n.asExpr() = c)
 or
 exists(Method f | (modelMethod(f,"Handler","onRequest(_:)",1) or
  modelMethod(f,"Handler","onDeclared(_:)",1)) and f.isInstanceMethod() and
  n.asParameter() = f.getParam(0))
}
predicate declaredSink(DataFlow::Node n) {
 exists(CallExpr c, Method f | c.getStaticTarget() = f and
  modelMethod(f,"Audit","record(_:)",1) and f.isStaticOrClassMethod() and
  n.asExpr() = c.getArgument(0).getExpr())
}
predicate sanitizer(DataFlow::Node n) {
 exists(CallExpr c, Method f | c.getStaticTarget() = f and
  modelMethod(f,"Clean","scrub(_:)",1) and f.isStaticOrClassMethod() and
  n.asExpr() = c)
}
