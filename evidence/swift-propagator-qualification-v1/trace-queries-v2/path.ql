/** @name Native path edges for the failed wrong-arity control
 * @kind table
 * @id dfb/swift-propagator-near-miss-path
 */
import FoundationSources
module Config implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node node) { CommandInjectionConfig::isSource(node) or processInput(node, _) }
 predicate isSink(DataFlow::Node node) { correctedSink(node) }
 predicate isBarrier(DataFlow::Node node) { CommandInjectionConfig::isBarrier(node) }
 predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) { CommandInjectionConfig::isAdditionalFlowStep(a, b) }
}
module Flow = TaintTracking::Global<Config>;
import Flow::PathGraph
predicate step(Flow::PathNode a, Flow::PathNode b) { Flow::PathGraph::edges(a, b, _, _) }
from Flow::PathNode source, Flow::PathNode sink, Flow::PathNode a, Flow::PathNode b
where Flow::flowPath(source, sink) and source.getNode().getLocation().getStartLine() = 11 and
 sink.getNode().getLocation().getStartLine() = 23 and
 step*(source, a) and step(a, b) and step*(b, sink)
select a.getNode().getLocation().getStartLine(), a.getNode().getLocation().getStartColumn(),
 a.getNode().toString(), b.getNode().getLocation().getStartLine(), b.getNode().getLocation().getStartColumn(), b.getNode().toString()
