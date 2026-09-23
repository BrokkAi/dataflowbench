/** Versioned adapter experiment; preserves stock flow except unproved append heuristics. */
import AppendIdentity
private import codeql.dataflow.TaintTracking as GenericTaint
private import codeql.swift.dataflow.internal.DataFlowImplSpecific
private import codeql.swift.dataflow.internal.TaintTrackingImplSpecific as Stock

private predicate rejectedAppendHeuristic(DataFlow::Node input, DataFlow::Node output) {
  exists(CallExpr call, Method target, Argument argument |
    target = call.getStaticTarget() and target.getShortName() = "append" and
    argument = call.getAnArgument() and argument.getLabel() = ["", "contentsOf"] and
    input.asExpr() = argument.getExpr() and
    output.(DataFlow::PostUpdateNode).getPreUpdateNode().asExpr() = call.getQualifier() and
    not exactAppend(target)
  )
}
module ResolvedSwiftTaint implements GenericTaint::InputSig<Location, SwiftDataFlow> {
  predicate defaultTaintSanitizer(DataFlow::Node node) {
    Stock::SwiftTaintTracking::defaultTaintSanitizer(node)
  }
  predicate defaultAdditionalTaintStep(DataFlow::Node a, DataFlow::Node b, string model) {
    Stock::SwiftTaintTracking::defaultAdditionalTaintStep(a, b, model) and
    not (model = "AdditionalTaintStep" and rejectedAppendHeuristic(a, b))
  }
  bindingset[node]
  predicate defaultImplicitTaintRead(DataFlow::Node node, DataFlow::ContentSet content) {
    Stock::SwiftTaintTracking::defaultImplicitTaintRead(node, content)
  }
  predicate speculativeTaintStep(DataFlow::Node a, DataFlow::Node b) {
    Stock::SwiftTaintTracking::speculativeTaintStep(a, b)
  }
}
module ResolvedTaint = GenericTaint::TaintFlowMake<Location, SwiftDataFlow, ResolvedSwiftTaint>;
