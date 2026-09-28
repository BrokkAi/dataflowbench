/** Composed adapter experiment: resolved append and String/Data heuristic guards. */
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
private predicate rejectedStringDataHeuristic(DataFlow::Node input, DataFlow::Node output) {
 exists(InitializerCallExpr call, Initializer target, NominalTypeDecl owner, Argument argument |
  target = call.getStaticTarget() and owner = target.getDeclaringDecl().asNominalTypeDecl() and
  owner.getModule().getName() = "Swift" and owner.getName() = "String" and
  argument = call.getAnArgument() and argument.getLabel() = "data" and
  input.asExpr() = argument.getExpr() and output.asExpr() = call and
  not (target.getModule().getName() = "Foundation" and target.getName() = "init(data:encoding:)" and
       target.getNumberOfParams() = 2 and namedType(target.getParam(0).getType(), "Foundation", "Data"))
 )
}
module ResolvedSwiftTaint implements GenericTaint::InputSig<Location, SwiftDataFlow> {
  predicate defaultTaintSanitizer(DataFlow::Node node) {
    Stock::SwiftTaintTracking::defaultTaintSanitizer(node)
  }
  predicate defaultAdditionalTaintStep(DataFlow::Node a, DataFlow::Node b, string model) {
    Stock::SwiftTaintTracking::defaultAdditionalTaintStep(a, b, model) and
    not (model = "AdditionalTaintStep" and (rejectedAppendHeuristic(a, b) or rejectedStringDataHeuristic(a, b)))
  }
  bindingset[node]
  predicate defaultImplicitTaintRead(DataFlow::Node node, DataFlow::ContentSet content) {
    Stock::SwiftTaintTracking::defaultImplicitTaintRead(node, content)
  }
  predicate speculativeTaintStep(DataFlow::Node a, DataFlow::Node b) {
    Stock::SwiftTaintTracking::speculativeTaintStep(a, b)
  }
}
module ResolvedTaintEngine = GenericTaint::TaintFlowMake<Location, SwiftDataFlow, ResolvedSwiftTaint>;
