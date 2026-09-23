/** @name Instantiated persistence simple/read/store model observations
 * @kind table
 * @id dfb/swift-persistence-edges
 */
import PersistenceIdentity
private import codeql.swift.dataflow.internal.FlowSummaryImpl as SummaryImpl
from MethodCallExpr call, SummarizedCallable summary, DataFlow::Node input, DataFlow::Node output, string kind
where selectedPersistenceCall(call, summary) and summary.hasManualModel() and
 (input.asExpr() = call.getAnArgument().getExpr() or input.asExpr() = call.getQualifier()) and
 (output.asExpr() = call or output.(DataFlow::PostUpdateNode).getPreUpdateNode().asExpr() = call.getQualifier()) and
 (SummaryImpl::Private::Steps::summaryThroughStepTaint(input, output, summary) and kind = "taint"
  or SummaryImpl::Private::Steps::summaryThroughStepValue(input, output, summary) and kind = "value"
  or SummaryImpl::Private::Steps::summarySetterStep(input, _, output, summary) and kind = "store"
  or SummaryImpl::Private::Steps::summaryGetterStep(input, _, output, summary) and kind = "read")
select call.getLocation().getStartLine(), input.getLocation().getStartLine(), input.getLocation().getStartColumn(),
 output.getLocation().getStartLine(), output.getLocation().getStartColumn(), kind
