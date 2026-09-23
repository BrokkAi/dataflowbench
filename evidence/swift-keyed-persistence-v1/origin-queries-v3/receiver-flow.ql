/** @name Native reference value flow to persistence receivers
 * @kind table
 * @id dfb/swift-suite-receiver-flow
 */
import FoundationSources
from InitializerCallExpr init, MethodCallExpr call, DataFlow::Node origin, DataFlow::Node receiver
where init.getLocation().getFile().getBaseName()="main.swift" and call.getLocation().getFile().getBaseName()="main.swift" and
 init.getStaticTarget().getName()="init(suiteName:)" and origin.asExpr()=init and receiver.asExpr()=call.getQualifier() and
 DataFlow::localFlow(origin,receiver)
select init.getLocation().getStartLine(),call.getLocation().getStartLine(),call.getStaticTarget().getName()
