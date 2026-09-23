/** @name Instantiated shipped append summary transfer, independent of endpoint flow
 * @kind table
 * @id dfb/swift-propagator-transfer
 */
import AppendIdentity
private import codeql.swift.dataflow.internal.FlowSummaryImpl as SummaryImpl
from MethodCallExpr call, SummarizedCallable summary, DataFlow::Node input, DataFlow::Node output, string model
where call.getLocation().getFile().getBaseName() = "main.swift" and
 summary = call.getStaticTarget() and exactAppend(summary) and summary.hasManualModel() and
 summary.propagatesFlow("Argument[0]", "Argument[-1]", false, _, true, model) and
 SummaryImpl::Private::Steps::summaryThroughStepTaint(input, output, summary) and
 input.asExpr() = call.getArgument(0).getExpr() and
 output.(DataFlow::PostUpdateNode).getPreUpdateNode().asExpr() = call.getQualifier()
select call.getLocation().getStartLine(), input.getLocation().getStartLine(),
 input.getLocation().getStartColumn(), output.getLocation().getStartLine(),
 output.getLocation().getStartColumn(), model
