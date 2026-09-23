/** @name Attached manual summary ports, distinct from instantiated edges
 * @kind table
 * @id dfb/swift-summary-ports
 */
import SummaryIdentity
from MethodCallExpr call, SummarizedCallable summary, string input, string output, string origin
where selectedSummaryCall(call, summary) and summary.hasManualModel() and
 summary.propagatesFlow(input, output, false, _, true, origin)
select call.getLocation().getStartLine(), input, output, origin
