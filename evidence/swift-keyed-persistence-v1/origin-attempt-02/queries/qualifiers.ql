/** @name Resolved receiver CFG qualifiers
 * @kind table
 * @id dfb/swift-suite-qualifier-diagnosis
 */
import FoundationSources
import codeql.swift.controlflow.CfgNodes
from ApplyExprCfgNode point, MethodCallExpr call, Method target
where point.getExpr()=call and call.getLocation().getFile().getBaseName()="main.swift" and
 call.getStaticTarget()=target and target.getDeclaringDecl().asNominalTypeDecl().getName()="UserDefaults"
select call.getLocation().getStartLine(),target.getName(),point.getQualifier().getLocation().getStartLine(),point.getQualifier().getLocation().getStartColumn(),point.getQualifier().getAst().getAPrimaryQlClass()
