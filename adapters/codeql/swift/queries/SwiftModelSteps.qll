/** Declaration-driven summaries and keyed persistence, with resolved object provenance. */
import SwiftModelIdentity

predicate fixtureType(Type t, string name) {
 t.(NominalType).getDeclaration().getModule().getName() = "DataFlowBenchTaintSwift" and
 t.(NominalType).getDeclaration().getName() = name
}

module StoreObjectConfig implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) {
  exists(CallExpr c | n.asExpr() = c and fixtureType(c.getType(), "Store") and
   c.getStaticTarget() instanceof Initializer)
 }
 predicate isSink(DataFlow::Node n) {
  exists(CallExpr c, Method f | c.getStaticTarget() = f and
   (modelMethod(f,"Store","put(_:_:)",2) or modelMethod(f,"Store","get(_:)",1)) and
   f.isInstanceMethod() and n.asExpr() = c.getQualifier())
 }
}
module StoreObjects = DataFlow::Global<StoreObjectConfig>;

predicate storeKey(CallExpr call, string key) {
 call.getArgument(0).getExpr().(StringLiteralExpr).getValue() = key
}
predicate sameStore(CallExpr put, CallExpr get) {
 put.getStaticTarget().(Method).isStaticOrClassMethod() and
 get.getStaticTarget().(Method).isStaticOrClassMethod()
 or
 exists(DataFlow::Node allocation, DataFlow::Node writeReceiver, DataFlow::Node readReceiver |
  writeReceiver.asExpr() = put.getQualifier() and readReceiver.asExpr() = get.getQualifier() and
  StoreObjects::flow(allocation,writeReceiver) and StoreObjects::flow(allocation,readReceiver))
}
predicate summaryBarrier(DataFlow::Node n) {
 exists(CallExpr c, Method f | c.getStaticTarget() = f and
  modelMethod(f,"Bridge","hold(_:)",1) and f.isStaticOrClassMethod() and
  n.asExpr() = c.getArgument(0).getExpr())
}
predicate declaredStep(DataFlow::Node predecessor, DataFlow::Node to) {
 exists(CallExpr c, Method f | c.getStaticTarget() = f and
  modelMethod(f,"Bridge","pass(_:)",1) and f.isStaticOrClassMethod() and
  predecessor.asExpr() = c.getArgument(0).getExpr() and to.asExpr() = c)
 or
 exists(CallExpr c, Method f, MemberRefExpr read, DataFlow::Node object |
  c.getStaticTarget() = f and f.hasQualifiedName("DataFlowBenchTaintSwift","Bridge","deposit(_:_:)") and
  f.isStaticOrClassMethod() and f.getNumberOfParams() = 2 and
  f.getInterfaceType().(AnyFunctionType).getResult().(AnyFunctionType).getResult().(TupleType).getNumberOfTypes() = 0 and
  swiftString(f.getParam(0).getType()) and fixtureType(f.getParam(1).getType(),"Box") and
  read.getMember().(FieldDecl).hasQualifiedName("DataFlowBenchTaintSwift","Box","payload") and
  fixtureType(object.asExpr().getType(),"Box") and
  DataFlow::localFlow(object,DataFlow::exprNode(c.getArgument(1).getExpr())) and
  DataFlow::localFlow(object,DataFlow::exprNode(read.getBase())) and
  predecessor.asExpr() = c.getArgument(0).getExpr() and to.asExpr() = read)
 or
 exists(CallExpr put, CallExpr get, Method write, Method read, string key |
  put.getStaticTarget() = write and get.getStaticTarget() = read and
  modelMethod(write,"Store","put(_:_:)",2) and modelMethod(read,"Store","get(_:)",1) and
  storeKey(put,key) and storeKey(get,key) and sameStore(put,get) and
  predecessor.asExpr() = put.getArgument(1).getExpr() and to.asExpr() = get)
}
