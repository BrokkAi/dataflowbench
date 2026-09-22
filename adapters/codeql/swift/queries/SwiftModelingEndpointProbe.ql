/**
 * @name Swift controlled-model endpoint identity observation
 * @description Observe exact declared and undeclared sibling identities, independently of model activation.
 * @kind problem
 * @problem.severity warning
 * @id dfb/swift-modeling-endpoint-probe
 */
import SwiftModelIdentity
predicate sourceCandidate(DataFlow::Node n) {
 stringSource(n) or declaredSource(n)
 or exists(CallExpr c, Method f | c.getStaticTarget() = f and
  modelMethod(f,"Config","fetchLocal()",0) and f.isStaticOrClassMethod() and n.asExpr() = c)
 or exists(Method f | (modelMethod(f,"Handler","onIgnored(_:)",1) or
  modelMethod(f,"Handler","onUndeclared(_:)",1)) and f.isInstanceMethod() and n.asParameter() = f.getParam(0))
}
predicate sinkCandidate(DataFlow::Node n) {
 stringSink(n) or declaredSink(n)
 or exists(CallExpr c, Method f | c.getStaticTarget() = f and modelMethod(f,"Audit","discard(_:)",1)
  and f.isStaticOrClassMethod() and n.asExpr() = c.getArgument(0).getExpr())
}
from Location location, string role
where
 exists(DataFlow::Node endpoint | sourceCandidate(endpoint) and location = endpoint.getLocation() and role = "source")
 or exists(DataFlow::Node endpoint | sinkCandidate(endpoint) and location = modeledSinkLocation(endpoint) and role = "sink")
 or exists(Method f | modelMethod(f,"Config","fetchRemote()",0) and f.isStaticOrClassMethod() and
   f.hasBody() and location = f.getLocation() and role = "source")
 or exists(Method f | modelMethod(f,"Audit","record(_:)",1) and f.isStaticOrClassMethod() and
   f.hasBody() and location = f.getLocation() and role = "sink")
select location, "Benchmark " + role + " endpoint observed."
