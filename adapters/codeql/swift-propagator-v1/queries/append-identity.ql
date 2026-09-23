/** @name Resolved append declarations and attached summaries
 * @kind table
 * @id dfb/swift-propagator-identity
 */
import AppendIdentity
from MethodCallExpr call, Method method, Decl owner, boolean exact, boolean inoutSelf, boolean modeled
where call.getLocation().getFile().getBaseName() = "main.swift" and
 method = call.getStaticTarget() and owner.getAMember() = method and
 method.getName() = ["append(_:)", "append(_:ignored:)"] and
 ((exact = true and exactAppend(method)) or (exact = false and not exactAppend(method))) and
 ((inoutSelf = true and method.getSelfParam().isInout()) or (inoutSelf = false and not method.getSelfParam().isInout())) and
 ((modeled = true and exists(SummarizedCallable summary |
    summary = method and summary.hasManualModel() and
    summary.propagatesFlow("Argument[0]", "Argument[-1]", false, _, true, _))) or
  (modeled = false and not exists(SummarizedCallable summary |
    summary = method and summary.hasManualModel() and
    summary.propagatesFlow("Argument[0]", "Argument[-1]", false, _, true, _))))
select call.getLocation().getStartLine(), method.getModule().getName(),
 owner.asNominalTypeDecl().getModule().getName(), owner.asNominalTypeDecl().getName(),
 method.getName(), method.getNumberOfParams(), method.getParam(0).getType().toString(),
 inoutSelf, exact, modeled
