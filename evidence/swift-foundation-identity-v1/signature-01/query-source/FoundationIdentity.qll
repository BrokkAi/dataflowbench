/** Adapter-corrected profile: resolver-backed Foundation Process sinks. */
import swift
import codeql.swift.dataflow.DataFlow
import codeql.swift.security.CommandInjectionQuery

predicate namedType(Type t, string moduleName, string name) {
  t.getUnderlyingType().(NominalOrBoundGenericNominalType).getDeclaration().getModule().getName() = moduleName and
  t.getUnderlyingType().(NominalOrBoundGenericNominalType).getDeclaration().getName() = name
}
predicate stringArray(Type t) {
  namedType(t, "Swift", "Array") and
  namedType(t.getUnderlyingType().(BoundGenericType).getArgType(0), "Swift", "String")
}
predicate processMember(Decl member) {
  member.getModule().getName() = "Foundation" and
  exists(Decl owner |
    owner.getAMember() = member and
    owner.asNominalTypeDecl().getModule().getName() = "Foundation" and
    owner.asNominalTypeDecl().getName() = "Process"
  )
}
predicate exactStaticRun(Method method) {
  processMember(method) and method.getName() = "run(_:arguments:terminationHandler:)" and
  method.isStaticOrClassMethod() and method.getNumberOfParams() = 3 and
  namedType(method.getParam(0).getType(), "Foundation", "URL") and
  stringArray(method.getParam(1).getType())
}
predicate correctedSink(DataFlow::Node node) {
  node instanceof CommandInjectionSink and
  (
    exists(CallExpr call, Method method |
      method = call.getStaticTarget() and exactStaticRun(method) and
      node.asExpr() = call.getArgument([0, 1]).getExpr()
    )
    or
    exists(MemberRefExpr access, FieldDecl field |
      field = access.getMember() and processMember(field) and field.getName() = "arguments" and
      namedType(access.getBase().getType(), "Foundation", "Process") and
      node.(DataFlow::PostUpdateNode).getPreUpdateNode().asExpr() = access.getBase()
    )
  )
}
