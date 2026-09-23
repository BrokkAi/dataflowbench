/** @name Bounded local-body flow checkpoints
 * @kind table
 * @id dfb/swift-conversion-body-checkpoints
 */
import FoundationSources
module CheckpointConfig implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { processInput(n, _) }
 predicate isSink(DataFlow::Node n) { n.getLocation().getFile().getBaseName() = "main.swift" }
 predicate isBarrier(DataFlow::Node n) { CommandInjectionConfig::isBarrier(n) }
 predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) { CommandInjectionConfig::isAdditionalFlowStep(a,b) }
}
module CheckpointFlow = TaintTracking::Global<CheckpointConfig>;
from DataFlow::Node source, DataFlow::Node target
where CheckpointFlow::flow(source,target)
select target.getLocation().getStartLine(), target.getLocation().getStartColumn(),
 target.getLocation().getEndLine(), target.getLocation().getEndColumn(), target.toString()
