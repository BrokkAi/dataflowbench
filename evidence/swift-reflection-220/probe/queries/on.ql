/**
 * @name Non-scored Swift reflection on control
 * @description Exact resolved identity reflection model control.
 * @kind problem
 * @problem.severity warning
 * @id dfb/swift-reflection-on
 */
import ReflectionModels
import codeql.swift.dataflow.TaintTracking
module Config implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { stringSource(n) }
 predicate isSink(DataFlow::Node n) { stringSink(n) }
 predicate isBarrier(DataFlow::Node n) { barrier(n) }
 predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) { step(a,b) }
}
module Flow = TaintTracking::Global<Config>;
from DataFlow::Node source, DataFlow::Node sink
where Flow::flow(source,sink)
select sink.getLocation(), "Native reflection flow, on."
