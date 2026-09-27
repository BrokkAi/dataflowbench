/** @name Typed erased setter payloads
 * @kind table
 * @id dfb/swift-setter-payloads
 */
import FoundationSources
from MethodCallExpr call, Expr value, Expr leaf
where call.getLocation().getFile().getBaseName()="main.swift" and
 call.getStaticTarget().hasQualifiedName("Foundation","UserDefaults","set(_:forKey:)") and
 value=call.getArgument(0).getExpr() and value.convertsFrom*(leaf)
select call.getLocation().getStartLine(),value.getAPrimaryQlClass(),leaf.getAPrimaryQlClass(),
 leaf.getType().getAPrimaryQlClass(),leaf.getType().toString()
