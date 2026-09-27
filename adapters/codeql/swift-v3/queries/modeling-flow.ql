/** @name V3 modeling flow
 * @kind table
 * @id dfb/swift-v3-modeling-flow
 */
import SwiftModelSteps
import codeql.swift.dataflow.TaintTracking
module Config implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { stringSource(n) or declaredSource(n) }
 predicate isSink(DataFlow::Node n) { stringSink(n) or declaredSink(n) }
 predicate isBarrier(DataFlow::Node n) { sanitizer(n) or summaryBarrier(n) }
 predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) { declaredStep(a,b) }
}
module Flow = TaintTracking::Global<Config>;
Location sourceLocation(DataFlow::Node n) {
    exists(CallExpr c, Method f | n.asExpr()=c and c.getStaticTarget()=f and modelMethod(f,"Config","fetchRemote()",0) and result=f.getLocation())
    or not exists(CallExpr c, Method f | n.asExpr()=c and c.getStaticTarget()=f and modelMethod(f,"Config","fetchRemote()",0)) and result=n.getLocation()
}
from DataFlow::Node source, DataFlow::Node sink, Location a, Location b
where Flow::flow(source,sink) and a=sourceLocation(source) and b=modeledSinkLocation(sink)
select a.getFile().getBaseName(),a.getStartLine(),b.getFile().getBaseName(),b.getStartLine(),b.getStartColumn()
