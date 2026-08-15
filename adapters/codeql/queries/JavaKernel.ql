/**
 * @name DataFlowBench Java propagation kernel
 * @description Finds benchmark-controlled taint flow between the Java kernel's source and sink methods.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/java-propagation-kernel
 * @tags security
 */

import java
import semmle.code.java.dataflow.DataFlow
import semmle.code.java.dataflow.TaintTracking

module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(MethodCall call |
      call.getMethod().getName() = ["dfb_source", "directUntrustedInput", "explicitNegativeUntrustedInput"] and
      source.asExpr() = call
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(MethodCall call |
      call.getMethod().getName() = ["dfb_sink", "recordDirect", "recordExplicitNegative"] and
      sink.asExpr() = call.getArgument(0)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
