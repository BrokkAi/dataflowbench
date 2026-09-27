/** @name CFG apply node shape
 * @kind table
 * @id dfb/swift-cfg-call-shapes
 */
import FoundationSources
from ApplyExprCfgNode point
where point.getLocation().getFile().getBaseName()="main.swift"
select point.getLocation().getStartLine(),point.getExpr().getAPrimaryQlClass(),point.getScope().getLocation().getStartLine()
