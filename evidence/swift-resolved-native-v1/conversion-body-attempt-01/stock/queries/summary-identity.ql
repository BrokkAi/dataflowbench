/** @name Resolved Data roundtrip call identities
 * @kind table
 * @id dfb/swift-summary-identity
 */
import SummaryIdentity
from MethodCallExpr call, Method target, Decl owner, boolean modeled
where selectedSummaryCall(call, target) and owner.getAMember() = target and
 (if exists(SummarizedCallable summary | summary = target and summary.hasManualModel())
  then modeled = true else modeled = false)
select call.getLocation().getStartLine(), call.getLocation().getStartColumn(),
 target.getModule().getName(), owner.asNominalTypeDecl().getModule().getName(),
 owner.asNominalTypeDecl().getName(), target.getName(), target.getNumberOfParams(), modeled
