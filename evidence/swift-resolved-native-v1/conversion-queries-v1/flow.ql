/** @name Vendor and corrected process input flow
 * @kind table
 * @id dfb/swift-foundation-sources-flow
 */
import FoundationSources
module CorrectedConfig implements DataFlow::ConfigSig {
  predicate isSource(DataFlow::Node node) {
    CommandInjectionConfig::isSource(node) or processInput(node, _)
  }
  predicate isSink(DataFlow::Node node) { correctedSink(node) }
  predicate isBarrier(DataFlow::Node node) { CommandInjectionConfig::isBarrier(node) }
  predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) {
    CommandInjectionConfig::isAdditionalFlowStep(a, b)
  }
}
module CorrectedFlow = TaintTracking::Global<CorrectedConfig>;
from DataFlow::Node source, DataFlow::Node sink, string profile
where source.getLocation().getFile().getBaseName() = "main.swift" and
 sink.getLocation().getFile().getBaseName() = "main.swift" and
 (CorrectedFlow::flow(source, sink) and profile = "adapter-patched-conversion")
select source.getLocation().getStartLine(), sink.getLocation().getStartLine(),
 sink.getLocation().getStartColumn(), profile
