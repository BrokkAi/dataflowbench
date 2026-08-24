/**
 * @name DataFlowBench TypeScript propagation kernel
 * @description Finds benchmark-controlled taint flow between the TypeScript kernel's source and sink calls.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/typescript-propagation-kernel
 * @tags security
 */

import javascript

/**
 * The TypeScript kernel is intentionally restricted to `.ts` fixtures.  The
 * CodeQL JavaScript library extracts JavaScript and TypeScript with the same
 * extractor, so the extension check keeps this query's result set disjoint
 * from the JavaScript kernel's, exactly as `JavaScriptKernel.ql` keeps itself
 * disjoint from TypeScript.
 */
predicate isTypeScriptFixture(DataFlow::Node node) { node.getFile().getExtension() = "ts" }

module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "dfb_source" and
      source = call and
      isTypeScriptFixture(source)
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::CallNode call |
      call.getCalleeName() = "dfb_sink" and
      sink = call.getArgument(0) and
      isTypeScriptFixture(sink)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
