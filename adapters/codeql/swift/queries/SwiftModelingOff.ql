/**
 * @name Swift modeling activation model-off control
 * @description Separate non-scored load-bearing control with no declared models.
 * @kind problem
 * @problem.severity warning
 * @id dfb/swift-modeling-off
 */
import SwiftModelIdentity
import codeql.swift.dataflow.TaintTracking
module Config implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { stringSource(n) }
 predicate isSink(DataFlow::Node n) { stringSink(n) }
}
module Flow = TaintTracking::Global<Config>;
from DataFlow::Node source, DataFlow::Node sink
where Flow::flow(source,sink)
select sink.getLocation(), "Model-off control flow."
