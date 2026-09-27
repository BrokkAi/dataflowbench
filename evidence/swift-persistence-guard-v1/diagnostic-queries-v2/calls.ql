/** @name Resolved calls in persistence control
 * @kind table
 * @id dfb/swift-persistence-call-effects
 */
import FoundationSources
from ApplyExprCfgNode point, ApplyExpr call, string moduleName, string targetName
where point.getExpr()=call and call.getLocation().getFile().getBaseName()="main.swift" and
 (if exists(Function target | target=call.getStaticTarget()) then
   exists(Function target | target=call.getStaticTarget() and moduleName=target.getModule().getName() and targetName=target.getName())
  else moduleName="<unresolved>" and targetName="<unresolved>")
select call.getLocation().getStartLine(),call.getLocation().getStartColumn(),moduleName,targetName,
 point.getScope().getLocation().getStartLine()
