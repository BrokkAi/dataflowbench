/** @name Script structural facts
 * @kind table
 * @id dfb/swift-entry-structural-facts-v1
 */
import swift
import codeql.swift.controlflow.ControlFlowGraph
import codeql.swift.controlflow.CfgNodes
import codeql.swift.controlflow.internal.ControlFlowGraphImpl as Impl
import codeql.swift.controlflow.internal.Completion
import codeql.swift.controlflow.internal.Scope

predicate local(AstNode n) {
  n.getLocation().getFile().getBaseName() = ["main.swift", "Library.swift"]
}
predicate fact(string key, int value) {
  key = "entries" and value = count(TopLevelEntryPoint e)
  or
  key = "wrong-entry-file" and value = count(TopLevelEntryPoint e | e.getSourceFile().getBaseName() != "main.swift" | e)
  or
  key = "wrong-entry-module" and value = count(TopLevelEntryPoint e | e.getModule().getName() != "DataFlowBenchTaintSwift" | e)
  or
  key = "declarations" and value = count(TopLevelCodeDecl d | local(d) | d)
  or
  key = "unowned-declarations" and value = count(TopLevelCodeDecl d | local(d) and not exists(TopLevelEntryPoint e | e.getADeclaration() = d) | d)
  or
  key = "wrong-declaration-owner" and value = count(TopLevelEntryPoint e, TopLevelCodeDecl d | d = e.getADeclaration() and (d.getLocation().getFile() != e.getSourceFile() or d.getModule() != e.getModule()) | d)
  or
  key = "duplicate-declaration" and value = count(TopLevelCodeDecl d | exists(TopLevelEntryPoint a, TopLevelEntryPoint b, int i, int j | a.getDeclaration(i) = d and b.getDeclaration(j) = d and (a != b or i != j)) | d)
  or
  key = "duplicate-indices" and value = count(TopLevelEntryPoint e | exists(int i | exists(e.getDeclaration(i)) and count(e.getDeclaration(i)) > 1) | e)
  or
  key = "non-dense-indices" and value = count(TopLevelEntryPoint e, int i | exists(e.getDeclaration(i)) and (i < 0 or i >= count(e.getADeclaration())) | e)
  or
  key = "nested-return-leak" and value = count(ReturnStmt r | local(r) and scopeOfAst(r) instanceof TopLevelEntryPoint | r)
  or
  key = "nested-return-scopes" and value = count(ReturnStmt r | local(r) and scopeOfAst(r) instanceof CfgScope | r)
  or
  key = "closure-scopes" and value = count(ClosureExpr c | local(c) and c instanceof CfgScope | c)
  or
  key = "script-conditions" and value = count(ControlFlowNode n | n.getScope() instanceof TopLevelEntryPoint and n.isCondition() | n)
  or
  key = "throw-statements" and value = count(ThrowStmt t | local(t) | t)
  or
  key = "throw-cfg" and value = count(ControlFlowNode n | n.getScope() instanceof TopLevelEntryPoint and n.getNode().asAstNode() instanceof ThrowStmt | n)
  or
  key = "throw-exits" and value = count(TopLevelEntryPoint e | Impl::succExit(e, _, any(ThrowCompletion c)) | e)
  or
  key = "normal-exits" and value = count(TopLevelEntryPoint e | Impl::succExit(e, _, any(NormalCompletion c)) | e)
  or
  key = "throw-to-sink" and value = count(ControlFlowNode a, ControlFlowNode b | a.getNode().asAstNode() instanceof ThrowStmt and a.getScope() instanceof TopLevelEntryPoint and b = a.getASuccessor+() and b.getNode().asAstNode().(CallExpr).getStaticTarget().getName() = "dfb_sink(_:)" | a)
}
from string key, int value where fact(key, value) select key, value
