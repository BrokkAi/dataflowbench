/** @name Typed persistence applicability including missing CFG coverage
 * @kind table
 * @id dfb/swift-persistence-coverage
 */
import PersistenceCoverage
from int scopeLine, string status, string reason, int line
where
 exists(CfgScope scope |
  scope.getLocation().getFile().getBaseName()="main.swift" and relevantScope(scope) and
  scopeLine=scope.getLocation().getStartLine() and
  (
   exists(CfgNode point | scopeIncomplete(scope,point,reason) and line=point.getLocation().getStartLine()) and status="Incomplete"
   or
   exists(ApplyExpr call | missingCallCoverage(scope,call) and line=call.getLocation().getStartLine()) and status="Incomplete" and reason="MissingCfgCallCoverage"
   or
   not scopeIncomplete(scope,_,_) and not missingCallCoverage(scope,_) and
   status="Complete" and reason="AdmittedClosedScope" and line=scopeLine
  )
 )
 or
 exists(MethodCallExpr call, Method method |
  call.getLocation().getFile().getBaseName()="main.swift" and method=call.getStaticTarget() and persistenceOwner(method) and
  method.getName()=["set(_:forKey:)","string(forKey:)"] and
  not exists(ApplyExprCfgNode point, CfgScope scope | point.getExpr()=call and point.getScope()=scope) and
  scopeLine=0 and status="Incomplete" and reason="MissingCfgCoverage" and line=call.getLocation().getStartLine()
 )
select scopeLine,status,reason,line
