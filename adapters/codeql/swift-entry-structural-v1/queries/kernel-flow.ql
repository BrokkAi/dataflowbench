/** @name V3 kernel flow
 * @kind table
 * @id dfb/swift-v3-kernel-flow
 */
import SwiftEndpoints
import codeql.swift.dataflow.TaintTracking
module Config implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node n) { benchmarkSource(n) }
  predicate isSink(DataFlow::Node n) { benchmarkSink(n) }
}
module Flow = TaintTracking::Global<Config>;
from DataFlow::Node source, DataFlow::Node sink, Location a, Location b
where Flow::flow(source,sink) and a=source.getLocation() and b=sink.getLocation()
select a.getFile().getBaseName(),a.getStartLine(),b.getFile().getBaseName(),b.getStartLine(),b.getStartColumn()
