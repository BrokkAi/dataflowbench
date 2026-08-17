/**
 * @name DataFlowBench JavaScript propagation kernel
 * @description Finds benchmark-controlled taint flow between the JavaScript kernel's source and sink calls.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/javascript-propagation-kernel
 * @tags security
 */

import javascript

/**
 * The JavaScript kernel is intentionally restricted to `.js` fixtures.  The
 * CodeQL JavaScript library also extracts TypeScript, so keeping the extension
 * check here prevents a future TypeScript adapter from silently sharing this
 * query's result set.
 */
predicate isJavaScriptFixture(DataFlow::Node node) { node.getFile().getExtension() = "js" }

module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "dfb_source" and
      source = call and
      isJavaScriptFixture(source)
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "dfb_sink" and
      sink = call.getArgument(0) and
      isJavaScriptFixture(sink)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
