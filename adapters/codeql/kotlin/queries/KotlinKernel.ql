/**
 * @name DataFlowBench Kotlin propagation kernel
 * @description Finds benchmark-controlled taint flow between the Kotlin kernel's source and sink functions.
 * @kind path-problem
 * @problem.severity warning
 * @precision high
 * @id dataflowbench/kotlin-propagation-kernel
 * @tags security
 */

import java
import semmle.code.java.dataflow.DataFlow
import semmle.code.java.dataflow.TaintTracking

/**
 * The Kotlin kernel is intentionally restricted to `.kt` fixtures. CodeQL
 * extracts Kotlin through the shared `java` extractor and standard library, so
 * keeping the extension check here prevents the Java kernel and the Kotlin
 * kernel from ever sharing a result set.
 */
predicate isKotlinFixture(DataFlow::Node node) {
  node.getLocation().getFile().getExtension() = "kt"
}

module DataFlowBenchConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node source) {
    exists(MethodCall call |
      call.getMethod().getName() = "dfb_source" and
      source.asExpr() = call and
      isKotlinFixture(source)
    )
  }

  predicate isSink(DataFlow::Node sink) {
    exists(MethodCall call |
      call.getMethod().getName() = "dfb_sink" and
      sink.asExpr() = call.getArgument(0) and
      isKotlinFixture(sink)
    )
  }
}

module DataFlowBenchFlow = TaintTracking::Global<DataFlowBenchConfig>;

import DataFlowBenchFlow::PathGraph

from DataFlowBenchFlow::PathNode source, DataFlowBenchFlow::PathNode sink
where DataFlowBenchFlow::flowPath(source, sink)
select sink.getNode(), source, sink, "Controlled input reaches the benchmark sink."
