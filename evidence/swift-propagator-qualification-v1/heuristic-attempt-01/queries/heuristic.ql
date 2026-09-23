/** @name Instantiated additional taint step for resolved append calls
 * @kind table
 * @id dfb/swift-propagator-heuristic-step
 */
import FoundationSources
import codeql.swift.dataflow.FlowSteps
from MethodCallExpr call, DataFlow::Node input, DataFlow::Node output
where call.getLocation().getFile().getBaseName() = "main.swift" and
 call.getLocation().getStartLine() = [13, 16, 19, 22] and
 input.asExpr() = call.getArgument(0).getExpr() and
 output.(DataFlow::PostUpdateNode).getPreUpdateNode().asExpr() = call.getQualifier() and
 exists(AdditionalTaintStep step | step.step(input, output))
select call.getLocation().getStartLine(), call.getStaticTarget().getModule().getName(),
 call.getStaticTarget().getShortName(), call.getArgument(0).getLabel(),
 input.getLocation().getStartLine(), input.getLocation().getStartColumn(),
 output.getLocation().getStartLine(), output.getLocation().getStartColumn()
