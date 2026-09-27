/** @name Canonical resolved calls and CFG membership
 * @kind table
 * @id dfb/swift-persistence-call-effects
 */
import FoundationSources
from ApplyExpr call, Callable target, boolean hasCfg
where call.getLocation().getFile().getBaseName()="main.swift" and target=call.getStaticTarget() and
 (if exists(ApplyExprCfgNode point | point.getExpr()=call) then hasCfg=true else hasCfg=false)
select call.getLocation().getStartLine(),call.getLocation().getStartColumn(),
 target.getName(),target.(Decl).getModule().getName(),hasCfg
