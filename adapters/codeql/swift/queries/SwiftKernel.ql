/**
 * @name DataFlowBench Swift propagation kernel
 * @description Global taint between exact benchmark declarations.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dfb/swift-kernel
 */
import SwiftEndpoints
import codeql.swift.dataflow.TaintTracking
module Config implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node n) { benchmarkSource(n) }
  predicate isSink(DataFlow::Node n) { benchmarkSink(n) }
}
module Flow = TaintTracking::Global<Config>;
from DataFlow::Node source, DataFlow::Node sink
where Flow::flow(source, sink)
select sink.getLocation(), "Controlled input reaches the benchmark sink."
