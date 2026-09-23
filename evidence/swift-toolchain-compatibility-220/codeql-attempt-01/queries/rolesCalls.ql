/** @name Resolved native declarations and shipped roles
 * @kind table
 * @id dfb/swift-v2-native-roles
 */
import swift
import codeql.swift.dataflow.FlowSources
import codeql.swift.security.CommandInjectionQuery
from Expr e, string role, string identity
where e.getLocation().getFile().getBaseName() = "main.swift" and
(
 exists(Decl d | d = e.(DeclRefExpr).getDecl() or d = e.(LookupExpr).getMember() or d = e.(CallExpr).getStaticTarget() |
 role = "declaration" and identity = d.getModule().getFullName() + ":" + d.toString() + ":" + d.(ValueDecl).getInterfaceType().toString())
 or exists(FlowSource n | n.asExpr() = e | role = "shipped-source" and identity = n.getSourceType())
 or exists(CommandInjectionSink n | n.asExpr() = e | role = "shipped-sink" and identity = n.toString())
)
select e.getLocation().getStartLine(), e.getLocation().getStartColumn(), role, identity
