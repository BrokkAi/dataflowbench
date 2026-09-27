/** @name Resolved property accessor effects
 * @kind table
 * @id dfb/swift-getter-effects
 */
import FoundationSources
from PropertyGetterCfgNode point, Accessor target
where point.getLocation().getFile().getBaseName()="main.swift" and target=point.getAccessor()
select point.getLocation().getStartLine(),target.getModule().getName(),target.getName(),point.getScope().getLocation().getStartLine()
