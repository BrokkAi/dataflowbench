import FoundationSources
import codeql.swift.dataflow.FlowSummary

predicate selectedPersistenceCall(MethodCallExpr call, Method target) {
  call.getLocation().getFile().getBaseName() = "main.swift" and target = call.getStaticTarget() and
  target.getName() = ["init(suiteName:)", "set(_:forKey:)", "string(forKey:)"] and
  target.getDeclaringDecl().asNominalTypeDecl().getName() = "UserDefaults"
}
