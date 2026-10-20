/** @name V3 calibration flow
 * @kind table
 * @id dfb/swift-v3-calibration-flow
 */
import SwiftEndpoints
import codeql.swift.dataflow.TaintTracking
predicate summary(CallExpr c, string member) {
 exists(Method f | c.getStaticTarget() = f and
  f.hasQualifiedName("DataFlowBenchTaintSwift","ThirdPartyBridge",member) and
  f.isStaticOrClassMethod() and f.getNumberOfParams() = 1 and benchmarkInt(f.getParam(0).getType()) and
  benchmarkInt(f.getInterfaceType().(AnyFunctionType).getResult().(AnyFunctionType).getResult()))
}
module Config implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { benchmarkSource(n) }
 predicate isSink(DataFlow::Node n) { benchmarkSink(n) }
 predicate isBarrier(DataFlow::Node n) { exists(CallExpr c | summary(c,"hold(_:)" ) and n.asExpr() = c.getArgument(0).getExpr()) }
 predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) {
  exists(CallExpr c | summary(c,"passThrough(_:)") and a.asExpr() = c.getArgument(0).getExpr() and b.asExpr() = c)
 }
}
module Flow = TaintTracking::Global<Config>;
from DataFlow::Node source, DataFlow::Node sink, Location a, Location b
where Flow::flow(source,sink) and a=source.getLocation() and b=sink.getLocation()
select a.getFile().getBaseName(),a.getStartLine(),b.getFile().getBaseName(),b.getStartLine(),b.getStartColumn()
