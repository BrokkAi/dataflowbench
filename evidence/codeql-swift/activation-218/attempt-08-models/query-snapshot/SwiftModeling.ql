/**
 * @name DataFlowBench Swift controlled modeling
 * @description Exact declared source, sink, entrypoint and sanitizer semantics.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dfb/swift-modeling
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
from DataFlow::Node source, DataFlow::Node sink
where Flow::flow(source,sink)
select sink.getLocation(), "Controlled modeled input reaches the benchmark sink."
