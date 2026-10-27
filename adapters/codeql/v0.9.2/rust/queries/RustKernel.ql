/**
 * @name DataFlowBench Rust propagation kernel
 * @description Finds benchmark-controlled taint flow between the Rust kernel's source and sink functions.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/rust-propagation-kernel
 * @tags security
 */

import rust
import codeql.rust.dataflow.DataFlow
import codeql.rust.dataflow.TaintTracking

/**
 * The Rust fixtures expose the same language-neutral benchmark contract as
 * every other DataFlowBench kernel: `dfb_source()` produces controlled input
 * and `dfb_sink(value)` observes its first argument. Matching those calls keeps
 * the query independent of fixture and template names, and selects only the
 * benchmark-controlled assertions of the Rust population.
 */
module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(Call call | call.getTargetName() = "dfb_source" and source.asExpr() = call)
  }

  predicate isSink(DataFlow::Node sink) {
    exists(Call call |
      call.getTargetName() = "dfb_sink" and
      sink.asExpr() = call.getPositionalArgument(0)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
