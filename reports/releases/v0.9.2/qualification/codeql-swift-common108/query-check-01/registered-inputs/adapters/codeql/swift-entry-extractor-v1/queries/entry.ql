/** @name Compiler script entry sequence
 * @kind table
 * @id dfb/swift-entry-sequence
 */
import swift
import codeql.swift.controlflow.CfgNodes
from TopLevelEntryPoint entry, int i, TopLevelCodeDecl decl
where decl = entry.getDeclaration(i)
select entry.getSourceFile().getAbsolutePath(), entry.getModule().getName(), i,
  decl.getLocation().getStartLine(), count(entry.getDeclaration(i)),
  count(CfgNode n | n.getScope() = entry | n)
