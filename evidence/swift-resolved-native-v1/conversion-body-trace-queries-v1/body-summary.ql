/** @name All summary attachment kinds on conversion calls
 * @kind table
 * @id dfb/swift-conversion-body-summary
 */
import SummaryIdentity
from MethodCallExpr call, Method target, boolean summarized, boolean manual
where selectedSummaryCall(call,target) and
 (if target instanceof SummarizedCallable then summarized = true else summarized = false) and
 (if exists(SummarizedCallable c | c=target and c.hasManualModel()) then manual = true else manual = false)
select call.getLocation().getStartLine(), target.getModule().getName(), target.getName(), summarized, manual
