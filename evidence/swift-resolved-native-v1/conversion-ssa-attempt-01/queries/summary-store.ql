/** @name Instantiated summary stores into returned content
 * @kind table
 * @id dfb/swift-summary-store
 */
import SummaryIdentity
private import codeql.swift.dataflow.internal.FlowSummaryImpl as SummaryImpl
from MethodCallExpr call, SummarizedCallable summary, DataFlow::Node input,
 DataFlow::Node output, DataFlow::ContentSet content, string encoded
where selectedSummaryCall(call, summary) and summary.hasManualModel() and
 SummaryImpl::Private::Steps::summarySetterStep(input, content, output, summary) and
 (input.asExpr() = call.getAnArgument().getExpr() or input.asExpr() = call.getQualifier()) and
 output.asExpr() = call and encoded = SummaryImpl::Input::encodeContent(content, "")
select call.getLocation().getStartLine(), input.getLocation().getStartLine(),
 input.getLocation().getStartColumn(), output.getLocation().getStartLine(),
 output.getLocation().getStartColumn(), encoded
