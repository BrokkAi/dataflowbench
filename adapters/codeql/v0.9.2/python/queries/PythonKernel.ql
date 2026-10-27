/**
 * @name DataFlowBench Python propagation kernel
 * @description Finds benchmark-controlled taint flow between the Python kernel's source and sink calls.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/python-propagation-kernel
 * @tags security
 */

private import python
import semmle.python.dataflow.new.DataFlow
import semmle.python.dataflow.new.TaintTracking

/**
 * The Python fixtures deliberately expose a small, language-neutral benchmark
 * contract: `dfb_source()` produces controlled input and `dfb_sink(value)`
 * observes its first positional argument. Matching those calls keeps the
 * query independent of fixture/template names while selecting only the
 * benchmark's 32 core assertions (the 16 balanced templates).
 */
module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(DataFlow::CallCfgNode call |
      call.getFunction().asCfgNode().(NameNode).getId() = "dfb_source" and
      source = call
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::CallCfgNode call |
      call.getFunction().asCfgNode().(NameNode).getId() = "dfb_sink" and
      sink = call.getArg(0)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

from DataFlow::Node source, DataFlow::Node sink
where DataFlowBenchFlow::flow(source, sink)
select sink.getLocation(), "Controlled input reaches the benchmark sink."
