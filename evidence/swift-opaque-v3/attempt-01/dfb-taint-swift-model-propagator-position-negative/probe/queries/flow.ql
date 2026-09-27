/** @name Objective-C opaque model off and on controls
 * @kind table
 * @id dfb/swift-opaque-objc-flow
 */
import OpaqueIdentity
import codeql.swift.dataflow.TaintTracking
module OffConfig implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { stringSource(n) }
 predicate isSink(DataFlow::Node n) { stringSink(n) }
}
module OnConfig implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { stringSource(n) }
 predicate isSink(DataFlow::Node n) { stringSink(n) }
 predicate isAdditionalFlowStep(DataFlow::Node a, DataFlow::Node b) { declaredStep(a,b) }
}
module Off = TaintTracking::Global<OffConfig>;
module On = TaintTracking::Global<OnConfig>;
from DataFlow::Node source, DataFlow::Node sink, string profile
where Off::flow(source,sink) and profile="adapter-controlled-model-off"
 or On::flow(source,sink) and profile="adapter-controlled-model-on"
select source.getLocation().getStartLine(),sink.getLocation().getStartLine(),sink.getLocation().getStartColumn(),profile
