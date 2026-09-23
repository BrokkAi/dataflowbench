/** @name Native assignment AST shapes
 * @kind table
 * @id dfb/swift-assignment-shapes
 */
import swift
from AssignExpr a
where a.getLocation().getFile().getBaseName()="main.swift"
select a.getLocation().getStartLine(), a.getDest().getAPrimaryQlClass(), a.getDest().toString(), a.getSource().getAPrimaryQlClass(), a.getSource().toString()
