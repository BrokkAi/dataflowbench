import FoundationSources
import codeql.swift.dataflow.FlowSummary

predicate exactAppend(Method method) {
  method.getModule().getName() = "Swift" and method.getName() = "append(_:)" and
  method.isInstanceMethod() and method.getSelfParam().isInout() and
  method.getNumberOfParams() = 1 and namedType(method.getParam(0).getType(), "Swift", "String") and
  namedType(method.getSelfParam().getType(), "Swift", "String") and
  exists(Decl owner |
    owner.getAMember() = method and
    owner.asNominalTypeDecl().getModule().getName() = "Swift" and
    owner.asNominalTypeDecl().getName() = "String"
  )
}
