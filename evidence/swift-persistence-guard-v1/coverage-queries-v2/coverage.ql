/** @name Typed persistence applicability
 * @kind table
 * @id dfb/swift-persistence-coverage
 */
import PersistenceCoverage
from CfgScope scope, string status, string reason, int line
where scope.getLocation().getFile().getBaseName()="main.swift" and relevantScope(scope) and
 (exists(CfgNode point | scopeIncomplete(scope,point,reason) and line=point.getLocation().getStartLine()) and status="Incomplete"
  or
  not scopeIncomplete(scope,_,_) and status="Complete" and reason="AdmittedClosedScope" and line=scope.getLocation().getStartLine())
select scope.getLocation().getStartLine(),status,reason,line
