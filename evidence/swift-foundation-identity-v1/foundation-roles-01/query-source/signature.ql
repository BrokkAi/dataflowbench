/** @name Resolved signature diagnostics
 * @kind table
 * @id dfb/swift-foundation-signature
 */
import FoundationIdentity
from CallExpr call, Method m, string category, string value
where call.getLocation().getFile().getBaseName()="main.swift" and m=call.getStaticTarget() and
(
 category="method" and value=m.getModule().getName()+":"+m.getName()+":"+m.getNumberOfParams().toString()
 or category="owner" and exists(Decl d|d.getAMember()=m|value=d.asNominalTypeDecl().getModule().getName()+":"+d.asNominalTypeDecl().getName())
 or category="parameter" and exists(int i,Type t|t=m.getParam(i).getType()|value=i.toString()+":"+t.toString()+":"+t.getAPrimaryQlClass())
 or category="static" and m.isStaticOrClassMethod() and value="yes"
 or category="parameter-type-decl" and exists(int i,Type t|t=m.getParam(i).getType().getUnderlyingType()|value=i.toString()+":"+t.(NominalOrBoundGenericNominalType).getDeclaration().getModule().getName()+":"+t.(NominalOrBoundGenericNominalType).getDeclaration().getName())
 or category="qualified" and processMember(m) and value="yes"
)
select call.getLocation().getStartLine(),category,value
