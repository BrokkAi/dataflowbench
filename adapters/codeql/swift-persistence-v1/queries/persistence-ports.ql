/** @name Attached persistence manual-summary ports
 * @kind table
 * @id dfb/swift-persistence-ports
 */
import PersistenceIdentity
from MethodCallExpr call, SummarizedCallable summary, string input, string output, string origin, boolean value
where selectedPersistenceCall(call, summary) and summary.hasManualModel() and
 summary.propagatesFlow(input, output, value, _, true, origin)
select call.getLocation().getStartLine(), input, output, value, origin
