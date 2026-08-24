/**
 * @name DataFlowBench Go propagation kernel
 * @description Finds benchmark-controlled taint flow between the Go kernel's source and sink functions.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/go-propagation-kernel
 * @tags security
 */

import go

/**
 * The Go fixtures expose the same language-neutral benchmark contract as every
 * other DataFlowBench kernel: `dfb_source()` produces controlled input and
 * `dfb_sink(value)` observes its first argument. Matching those calls keeps the
 * query independent of fixture and template names, and selects only the 32 core
 * assertions of the 16 balanced Go templates.
 */
module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(DataFlow::CallNode call |
      call.getTarget().getName() = "dfb_source" and
      source = call.getResult()
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::CallNode call |
      call.getTarget().getName() = "dfb_sink" and
      sink = call.getArgument(0)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
