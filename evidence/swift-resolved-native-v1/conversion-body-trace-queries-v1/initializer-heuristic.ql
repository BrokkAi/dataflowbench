/** @name Native additional initializer steps and resolved targets
 * @kind table
 * @id dfb/swift-conversion-initializer-heuristic
 */
import SummaryIdentity
import codeql.swift.dataflow.FlowSteps
from InitializerCallExpr call, Initializer target, Argument arg, DataFlow::Node input, DataFlow::Node output
where call.getLocation().getFile().getBaseName() = "main.swift" and
 target=call.getStaticTarget() and arg=call.getAnArgument() and arg.getLabel()="data" and
 input.asExpr()=arg.getExpr() and output.asExpr()=call and
 any(AdditionalTaintStep step).step(input,output)
select call.getLocation().getStartLine(), target.getModule().getName(), target.getName(), target.getNumberOfParams(),
 input.getLocation().getStartLine(), input.getLocation().getStartColumn(), output.getLocation().getStartLine(), output.getLocation().getStartColumn()
