/**
 * @name Non-scored Swift reflection off control
 * @description Exact resolved identity reflection model control.
 * @kind problem
 * @problem.severity warning
 * @id dfb/swift-reflection-off
 */
import ReflectionModels
import codeql.swift.dataflow.TaintTracking
module Config implements DataFlow::ConfigSig {
 predicate isSource(DataFlow::Node n) { stringSource(n) }
 predicate isSink(DataFlow::Node n) { stringSink(n) }

}
module Flow = TaintTracking::Global<Config>;
from DataFlow::Node source, DataFlow::Node sink
where Flow::flow(source,sink)
select sink.getLocation(), "Native reflection flow, off."
