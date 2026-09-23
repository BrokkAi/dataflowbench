/** @name Instantiated shipped summary taint edges at Data roundtrip calls
 * @kind table
 * @id dfb/swift-summary-transfer
 */
import SummaryIdentity
private import codeql.swift.dataflow.internal.FlowSummaryImpl as SummaryImpl
from MethodCallExpr call, SummarizedCallable summary, DataFlow::Node input, DataFlow::Node output
where selectedSummaryCall(call, summary) and summary.hasManualModel() and
 SummaryImpl::Private::Steps::summaryThroughStepTaint(input, output, summary) and
 (input.asExpr() = call.getAnArgument().getExpr() or input.asExpr() = call.getQualifier()) and
 output.asExpr() = call
select call.getLocation().getStartLine(), input.getLocation().getStartLine(),
 input.getLocation().getStartColumn(), output.getLocation().getStartLine(),
 output.getLocation().getStartColumn()
