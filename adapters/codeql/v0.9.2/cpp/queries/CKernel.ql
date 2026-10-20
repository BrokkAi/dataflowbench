/**
 * @name DataFlowBench C propagation kernel
 * @description Finds benchmark-controlled taint flow between the C kernel's source and sink functions.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/c-propagation-kernel
 * @tags security
 */

import cpp
import semmle.code.cpp.dataflow.new.DataFlow
import semmle.code.cpp.dataflow.new.TaintTracking

/**
 * CodeQL extracts C and C++ with one `cpp` extractor, and DataFlowBench keeps
 * the two languages as separate populations. The C kernel is therefore
 * restricted to `.c` fixtures; the C++ kernel query is its `.cpp` counterpart.
 */
predicate isCFixture(DataFlow::Node node) { node.getLocation().getFile().getExtension() = "c" }

module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(FunctionCall call |
      call.getTarget().getName() = "dfb_source" and
      source.asExpr() = call and
      isCFixture(source)
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(FunctionCall call |
      call.getTarget().getName() = "dfb_sink" and
      sink.asExpr() = call.getArgument(0) and
      isCFixture(sink)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
