/**
 * @name DataFlowBench C++ propagation kernel
 * @description Finds benchmark-controlled taint flow between the C++ kernel's source and sink functions.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/cpp-propagation-kernel
 * @tags security
 */

import cpp
import semmle.code.cpp.dataflow.new.DataFlow
import semmle.code.cpp.dataflow.new.TaintTracking

/**
 * CodeQL extracts C and C++ with one `cpp` extractor, and DataFlowBench keeps
 * the two languages as separate populations. The C++ kernel is therefore
 * restricted to `.cpp` fixtures, exactly as the Kotlin kernel is restricted to
 * `.kt` fixtures inside the shared `java` extractor.
 */
predicate isCppFixture(DataFlow::Node node) {
  node.getLocation().getFile().getExtension() = "cpp"
}

module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(FunctionCall call |
      call.getTarget().getName() = "dfb_source" and
      source.asExpr() = call and
      isCppFixture(source)
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(FunctionCall call |
      call.getTarget().getName() = "dfb_sink" and
      sink.asExpr() = call.getArgument(0) and
      isCppFixture(sink)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
