/**
 * @name DataFlowBench Java vertical slice
 * @description Finds benchmark-controlled taint flow from dfb_source return values to dfb_sink argument zero.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/java-vertical-slice
 * @tags security
 */

import java
import semmle.code.java.dataflow.DataFlow
import semmle.code.java.dataflow.TaintTracking

module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(MethodCall call |
      call.getMethod().hasName("dfb_source") and
      source.asExpr() = call
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(MethodCall call |
      call.getMethod().hasName("dfb_sink") and
      sink.asExpr() = call.getArgument(0)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
