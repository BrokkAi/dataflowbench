import FoundationSources
import codeql.swift.dataflow.FlowSummary

predicate selectedSummaryCall(MethodCallExpr call, Method target) {
  call.getLocation().getFile().getBaseName() = "main.swift" and
  target = call.getStaticTarget() and
  exists(Decl owner |
    owner.getAMember() = target and
    (owner.asNominalTypeDecl().getName() = "Data" and
      target.getName() = ["init(_:)", "base64EncodedString(options:)", "init(base64Encoded:options:)"]
     or owner.asNominalTypeDecl().getName() = "String" and target.getName() = "init(data:encoding:)")
  )
}
