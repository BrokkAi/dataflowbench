/** Versioned adapter experiment; preserves stock flow except unproved String data initializer heuristics. */
import FoundationSources
private import codeql.dataflow.TaintTracking as GenericTaint
private import codeql.swift.dataflow.internal.DataFlowImplSpecific
private import codeql.swift.dataflow.internal.TaintTrackingImplSpecific as Stock

/** Only the String data initializer heuristic is intercepted in this experiment. */
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
    not (model = "AdditionalTaintStep" and rejectedStringDataHeuristic(a, b))
  }
  bindingset[node]
  predicate defaultImplicitTaintRead(DataFlow::Node node, DataFlow::ContentSet content) {
    Stock::SwiftTaintTracking::defaultImplicitTaintRead(node, content)
  }
  predicate speculativeTaintStep(DataFlow::Node a, DataFlow::Node b) {
    Stock::SwiftTaintTracking::speculativeTaintStep(a, b)
  }
}
module ResolvedConversionEngine = GenericTaint::TaintFlowMake<Location, SwiftDataFlow, ResolvedSwiftTaint>;
