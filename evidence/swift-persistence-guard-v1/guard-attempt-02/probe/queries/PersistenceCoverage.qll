/** Fail-closed applicability evidence; no fixture-name or source-text matching. */
import FoundationSources
import codeql.swift.controlflow.ControlFlowGraph
import codeql.swift.dataflow.internal.DataFlowPrivate as Private

predicate persistenceOwner(Method method) {
  method.getModule().getName() = "Foundation" and
  method.getDeclaringDecl().asNominalTypeDecl().getModule().getName() = "Foundation" and
  method.getDeclaringDecl().asNominalTypeDecl().getName() = "UserDefaults"
}
predicate stringPayload(Expr value) {
  namedType(value.getType(), "Swift", "String")
  or
  exists(Expr inner |
    (value instanceof InjectIntoOptionalExpr or value instanceof ErasureExpr) and
    value.convertsFrom(inner) and stringPayload(inner)
  )
}
predicate coverageReason(CfgNode point, string reason) {
  exists(MethodCallExpr call, Method method |
    point.(ApplyExprCfgNode).getExpr() = call and method = call.getStaticTarget() and persistenceOwner(method) and
    (
      not method.getName() = ["init(suiteName:)", "set(_:forKey:)", "string(forKey:)"] and
      reason = "UnsupportedPreferenceOperation"
      or
      method.getName() = ["set(_:forKey:)", "string(forKey:)"] and
      not exists(call.getArgumentWithLabel("forKey").getExpr().(StringLiteralExpr)) and
      reason = "DynamicKey"
      or
      method.getName() = "set(_:forKey:)" and
      not stringPayload(call.getArgument(0).getExpr()) and reason = "UnqualifiedPayloadType"
      or
      method.getName() = ["set(_:forKey:)", "string(forKey:)"] and
      (not Private::userDefaultsReceiverProof(call, _, _, _) or
       Private::userDefaultsReceiverProof(call, _, _, false)) and
      reason = "IncompleteReceiverOrigin"
    )
  )
}

predicate relevantScope(CfgScope scope) {
  exists(ApplyExprCfgNode read, Method method |
    read.getScope()=scope and method=read.getStaticTarget() and persistenceOwner(method) and
    method.getName()="string(forKey:)"
  )
}
predicate beforeRead(CfgNode point, CfgScope scope) {
  point.getScope()=scope and
  exists(ApplyExprCfgNode read, Method method |
    read.getScope()=scope and method=read.getStaticTarget() and persistenceOwner(method) and
    method.getName()="string(forKey:)" and point.getASuccessor*()=read
  )
}
predicate incompleteEffect(CfgNode point, CfgScope scope, string reason) {
  beforeRead(point,scope) and
  (
    point instanceof ApplyExprCfgNode and
    not exists(Method method | method=point.(ApplyExprCfgNode).getStaticTarget() and persistenceOwner(method)) and
    reason="UnmodeledCallEffect"
    or
    point instanceof PropertySetterCfgNode and reason="UnmodeledPropertyMutation"
    or
    point instanceof PropertyObserverCfgNode and reason="UnmodeledPropertyObserver"
  )
}

predicate safeInputGetter(PropertyGetterCfgNode point) {
  exists(DataFlow::Node node | node.getCfgNode()=point and processInput(node,_))
  or
  exists(MemberRefExpr ref, FieldDecl field |
    ref=point.getRef() and field=ref.getMember() and
    ownedField(field,"Foundation","ProcessInfo","processInfo") and
    point.getAccessor()=field.getAnAccessor() and point.getAccessor().getModule().getName()="Foundation"
  )
  or
  exists(SubscriptExpr ref, SubscriptDecl member |
    ref=point.getRef() and member=ref.getMember() and
    member.getModule().getName()="Swift" and
    member.getDeclaringDecl().asNominalTypeDecl().getModule().getName()="Swift" and
    member.getDeclaringDecl().asNominalTypeDecl().getName()="Dictionary" and
    point.getAccessor()=member.getAnAccessor() and point.getAccessor().isGetter() and
    stringDictionary(ref.getBase().getType()) and
    ref.getNumberOfArguments()=1 and namedType(ref.getArgument(0).getExpr().getType(),"Swift","String")
  )
}
predicate scopeIncomplete(CfgScope scope, CfgNode point, string reason) {
  relevantScope(scope) and
  (
    point.getScope()=scope and coverageReason(point,reason)
    or
    incompleteEffect(point,scope,reason)
    or
    beforeRead(point,scope) and point instanceof PropertyGetterCfgNode and
    not safeInputGetter(point) and reason="UnmodeledGetterEffect"
  )
}


/** AST call enumeration is independent of CFG discovery. */
predicate missingCallCoverage(CfgScope scope, ApplyExpr call) {
  call.getEnclosingCallable()=scope and not exists(ApplyExprCfgNode point | point.getExpr()=call)
}
