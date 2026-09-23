/** @name Diagnose suite constructor and receiver CFG identities
 * @kind table
 * @id dfb/swift-suite-origins
 */
import FoundationSources
from MethodCallExpr call, Method target, boolean initializerCall
where call.getLocation().getFile().getBaseName()="main.swift" and call.getStaticTarget()=target and
 target.getDeclaringDecl().asNominalTypeDecl().getName()="UserDefaults" and
 (if call instanceof InitializerCallExpr then initializerCall=true else initializerCall=false)
select call.getLocation().getStartLine(),target.getModule().getName(),target.getName(),target.getAPrimaryQlClass(),initializerCall,call.getFunction().getAPrimaryQlClass(),call.getArgument(0).getExpr().getAPrimaryQlClass()
