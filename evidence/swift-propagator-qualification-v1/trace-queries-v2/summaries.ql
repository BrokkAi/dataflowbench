/** @name Attached summaries on the failed near-miss
 * @kind table
 * @id dfb/swift-propagator-near-miss-summaries
 */
import FoundationSources
import codeql.swift.dataflow.FlowSummary
from MethodCallExpr call, SummarizedCallable summary, string input, string output,
 boolean preservesValue, string provenance, boolean exact, string model
where call.getLocation().getFile().getBaseName() = "main.swift" and
 call.getLocation().getStartLine() = 22 and summary = call.getStaticTarget() and
 summary.propagatesFlow(input, output, preservesValue, provenance, exact, model)
select call.getLocation().getStartLine(), summary.getName(), input, output,
 preservesValue, provenance, exact, model
