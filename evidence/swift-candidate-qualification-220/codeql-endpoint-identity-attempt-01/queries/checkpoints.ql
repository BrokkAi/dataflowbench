/**
 * @name Result failure-path diagnostic checkpoints
 * @description Non-scored observations of existing flow at compiler-selected source lines.
 * @kind table
 * @id dfb/swift-result-v2-checkpoints
 */
import SwiftEndpoints
import codeql.swift.dataflow.TaintTracking
module Config implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node node) { benchmarkSource(node) }
  predicate isSink(DataFlow::Node node) {
    node.getLocation().getFile().getBaseName() = "main.swift" and
    node.getLocation().getStartLine() = [9, 15, 26, 27]
  }
}
module Flow = TaintTracking::Global<Config>;
from DataFlow::Node source, DataFlow::Node checkpoint
where Flow::flow(source, checkpoint)
select checkpoint.getLocation(), checkpoint.toString()
