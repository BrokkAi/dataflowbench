/** @name Stock and resolved adapter append control flow
 * @kind table
 * @id dfb/swift-resolved-append-flow
 */
import ResolvedTaint
module ProcessConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node n) { CommandInjectionConfig::isSource(n) or processInput(n, _) }
  predicate isSink(DataFlow::Node n) { correctedSink(n) }
  predicate isBarrier(DataFlow::Node n) { CommandInjectionConfig::isBarrier(n) }
  predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) { CommandInjectionConfig::isAdditionalFlowStep(a, b) }
}
module StockFlow = TaintTracking::Global<ProcessConfig>;
module ResolvedFlow = ResolvedTaint::Global<ProcessConfig>;
from DataFlow::Node source, DataFlow::Node sink, string profile
where source.getLocation().getFile().getBaseName() = "main.swift" and
 sink.getLocation().getFile().getBaseName() = "main.swift" and
 (StockFlow::flow(source, sink) and profile = "adapter-corrected-stock" or
  ResolvedFlow::flow(source, sink) and profile = "adapter-resolved-experiment")
select source.getLocation().getStartLine(), sink.getLocation().getStartLine(), sink.getLocation().getStartColumn(), profile
