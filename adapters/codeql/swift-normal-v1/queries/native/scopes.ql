/** @name Persistence scope inventory
 * @kind table
 * @id dfb/swift-composed-scopes
 */
import PersistenceCoverage
from CfgScope scope
where scope.getLocation().getFile().getBaseName()="main.swift" and relevantScope(scope)
select scope.getLocation().getStartLine()
