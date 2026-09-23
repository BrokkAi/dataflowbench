/** @name Resolved persistence methods and manual-model membership
 * @kind table
 * @id dfb/swift-persistence-identity
 */
import PersistenceIdentity
from MethodCallExpr call, Method target, Decl owner, boolean modeled
where selectedPersistenceCall(call, target) and owner.getAMember() = target and
 (if exists(SummarizedCallable s | s = target and s.hasManualModel()) then modeled = true else modeled = false)
select call.getLocation().getStartLine(), call.getLocation().getStartColumn(),
 target.getModule().getName(), owner.asNominalTypeDecl().getModule().getName(),
 owner.asNominalTypeDecl().getName(), target.getName(), target.getNumberOfParams(), modeled
