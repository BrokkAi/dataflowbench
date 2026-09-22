import swift
import codeql.swift.dataflow.DataFlow
import codeql.swift.dataflow.TaintTracking
module ActivationConfig implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node source) {
  exists(CallExpr call, FreeFunction f | f = call.getStaticTarget() and
   f.getModule().getName() = "DFBActivation" and f.getName() = "activationSource()" and
   f.getNumberOfParams() = 0 and source.asExpr() = call)
 }
 predicate isSink(DataFlow::Node sink) {
  exists(CallExpr call, FreeFunction f | f = call.getStaticTarget() and
   f.getModule().getName() = "DFBActivation" and f.getName() = "activationSink(_:)" and
   f.getNumberOfParams() = 1 and sink.asExpr() = call.getArgument(0).getExpr())
 }
}
module Flow = TaintTracking::Global<ActivationConfig>;
from DataFlow::Node source, DataFlow::Node sink
where Flow::flow(source,sink)
select source.getLocation(), sink.getLocation()
