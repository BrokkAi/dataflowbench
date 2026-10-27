/**
 * @name DataFlowBench Ruby propagation kernel
 * @description Finds benchmark-controlled taint flow between the Ruby kernel's source and sink calls.
 * @kind problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/ruby-propagation-kernel
 * @tags security
 */

private import codeql.ruby.AST
import codeql.ruby.DataFlow
import codeql.ruby.TaintTracking

/**
 * The Ruby fixtures expose the same small, language-neutral benchmark contract
 * as every other kernel: `dfb_source` produces controlled input and
 * `dfb_sink(value)` observes its first positional argument. Matching those
 * calls keeps the query independent of fixture, template, and polarity names
 * while selecting only the benchmark's 32 core assertions (the 16 balanced
 * templates). Ruby's parenless call surface is irrelevant here — a receiverless
 * `dfb_source` is the same `MethodCall` node as `dfb_source()`.
 */
module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(DataFlow::CallNode call |
      call.getMethodName() = "dfb_source" and
      source = call
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(DataFlow::CallNode call |
      call.getMethodName() = "dfb_sink" and
      sink = call.getArgument(0)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

from DataFlow::Node source, DataFlow::Node sink
where DataFlowBenchFlow::flow(source, sink)
select sink.getLocation(), "Controlled input reaches the benchmark sink."
